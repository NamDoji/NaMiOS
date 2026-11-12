"""Cài đặt phần mềm/driver "1 chạm" cho App & Driver Concierge — hiện thực
DUY NHẤT trong ``namios_assistant`` được phép THAY ĐỔI hệ thống (mọi module
khác trong ``engine/`` chỉ ĐỌC/tra cứu, xem docstring ``engine/__init__.py``).

TÁI DÙNG đúng khuôn ``namios_antoan.actions._run_privileged`` (pkexec +
``namios_security.run_argv``, argv TĨNH, KHÔNG shell, dịch mã polkit
126/127 sang thông báo người dùng đọc được) — KHÔNG viết lại logic
pkexec/argv-safety ở module này, chỉ import ``run_argv`` từ
``namios_security`` (nền an toàn dùng chung của cả repo, xem
``namios_security/__init__.py``).

CHỈ BA lệnh TĨNH được phép chạy qua đây, KHÔNG có đường nào khác:
  - ``pkexec apt-get install -y <package_id>`` — ``package_id`` PHẢI đến từ
    ``InstallPlan.action_payload`` (catalog đã kiểm duyệt).
  - ``pkexec flatpak install -y flathub <package_id>`` — tương tự.
  - ``pkexec apt-get install -y <tệp .deb tạm>`` (thêm 12/11/2026, "Vendor
    .deb auto-install" — xem ``install_deb_from_url``) — phần DUY NHẤT của
    argv do NGƯỜI DÙNG ảnh hưởng gián tiếp là đường dẫn tệp tạm, nhưng
    đường dẫn đó do CHÍNH module này sinh ra (``tempfile``, tên ngẫu nhiên,
    quyền 0600) sau khi đã tải + kiểm chứng xong — văn bản người dùng gõ
    KHÔNG BAO GIỜ chảy trực tiếp vào argv ở nhánh này.

``package_id``/URL truyền vào các hàm dưới đây PHẢI đến từ
``InstallPlan.action_payload``/``InstallPlan.verify_domain`` (tức từ catalog
đã kiểm duyệt, xem ``engine/app_catalog.py``), KHÔNG BAO GIỜ từ văn bản
người dùng gõ trực tiếp. Module này không tự xác thực NGUỒN GỐC của chuỗi đó
(đó là việc của ``app_catalog``/``backend``) — nó chỉ đảm bảo: (1) argv chạy
ra luôn TĨNH, không shell, có timeout (cùng nguyên tắc
``namios_security.run_argv``), và (2) với nhánh tải ``.deb`` — domain được
pin CHẶT (``is_official_https_url``) + nội dung tải về được xác minh ĐÚNG là
một gói Debian thật (magic bytes) trước khi chạm vào ``apt-get`` — xem
docstring ``install_deb_from_url``."""

from __future__ import annotations

import shutil
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import IO
from urllib.parse import urlparse

from namios_security import ExecPolicyError, run_argv

__all__ = ["InstallResult", "install_package", "install_deb_from_url", "is_official_https_url"]

#: Cài qua mạng (tải gói/image Flatpak) có thể lâu hơn hành động antoan
#: thường (120s) — cho rộng hơn, đồng thời vẫn bao trùm thời gian người dùng
#: tự nhập mật khẩu trong hộp thoại polkit.
_INSTALL_TIMEOUT_SECONDS = 600.0

#: Giới hạn độ dài output hiển thị trong hộp thoại kết quả — cùng giá trị
#: ``namios_antoan.actions._OUTPUT_DISPLAY_LIMIT_CHARS``.
_OUTPUT_DISPLAY_LIMIT_CHARS = 4000


@dataclass(frozen=True)
class InstallResult:
    """Kết quả một lần cài — ``success=False`` có thể là: thiếu công cụ
    (apt-get/flatpak/pkexec), người dùng từ chối polkit, timeout, hoặc lệnh
    trả mã lỗi. ``message`` nêu rõ trường hợp nào, KHÔNG gộp chung thành một
    câu "thất bại" mơ hồ (cùng nguyên tắc ``namios_antoan.actions.ActionResult``)."""

    success: bool
    message: str


def _which(name: str) -> str | None:
    return shutil.which(name)


def _trim_output(text: str) -> str:
    text = text.strip()
    if len(text) <= _OUTPUT_DISPLAY_LIMIT_CHARS:
        return text
    return text[-_OUTPUT_DISPLAY_LIMIT_CHARS:] + "\n\n[... đã cắt phần đầu, nội dung quá dài ...]"


def _run_privileged(argv: list[str], *, timeout: float) -> InstallResult:
    """Chạy ``argv`` qua ``pkexec`` — y hệt
    ``namios_antoan.actions._run_privileged`` (xem docstring module cho lý
    do không viết lại logic này lần thứ hai, chỉ import ``run_argv``)."""

    pkexec = _which("pkexec")
    if pkexec is None:
        return InstallResult(
            success=False,
            message=(
                "Không tìm thấy pkexec (gói policykit-1) trên máy này — không "
                "thể xin quyền quản trị một cách an toàn để cài đặt."
            ),
        )
    try:
        result = run_argv([pkexec, *argv], timeout=timeout)
    except ExecPolicyError as exc:
        return InstallResult(success=False, message=f"Không thực hiện được: {exc.reason_vi}")

    stdout_text = result.stdout.decode("utf-8", "replace")
    stderr_text = result.stderr.decode("utf-8", "replace")
    combined = (stdout_text + ("\n" + stderr_text if stderr_text.strip() else "")).strip()

    if result.returncode == 126:
        return InstallResult(
            success=False,
            message="Bạn đã từ chối cấp quyền quản trị (hộp thoại polkit) — chưa cài gì.",
        )
    if result.returncode == 127:
        return InstallResult(
            success=False,
            message=(
                "Sai mật khẩu hoặc tài khoản không có quyền quản trị — chưa cài gì. "
                "Hãy thử lại và nhập đúng mật khẩu."
            ),
        )
    if result.returncode != 0:
        return InstallResult(
            success=False,
            message=(
                f"Cài đặt không thành công (mã lỗi {result.returncode})."
                f"\n\n{_trim_output(combined) or '(không có kết quả trả về)'}"
            ),
        )
    return InstallResult(
        success=True, message=_trim_output(combined) or "Cài đặt hoàn tất, không có kết quả trả về."
    )


def install_package(*, method: str, package_id: str) -> InstallResult:
    """Cài ``package_id`` qua ``method`` ("apt" hoặc "flatpak") — CHỈ hai giá
    trị này được chấp nhận; giá trị khác -> lỗi rõ ràng, KHÔNG đoán cách chạy
    khác. ``package_id`` PHẢI lấy từ ``InstallPlan.action_payload`` (catalog
    đã kiểm duyệt) — hàm này không validate nguồn gốc chuỗi, chỉ đảm bảo
    argv chạy ra luôn TĨNH/KHÔNG shell (xem docstring module)."""

    if not package_id or not package_id.strip():
        return InstallResult(success=False, message="Thiếu tên gói cần cài — không có gì để làm.")

    if method == "apt":
        apt_get = _which("apt-get")
        if apt_get is None:
            return InstallResult(success=False, message="Không tìm thấy apt-get trên máy này.")
        return _run_privileged(
            [apt_get, "install", "-y", package_id], timeout=_INSTALL_TIMEOUT_SECONDS
        )

    if method == "flatpak":
        flatpak = _which("flatpak")
        if flatpak is None:
            return InstallResult(
                success=False,
                message="Chưa cài Flatpak trên máy này — cần Flatpak để cài qua Flathub.",
            )
        return _run_privileged(
            [flatpak, "install", "-y", "flathub", package_id], timeout=_INSTALL_TIMEOUT_SECONDS
        )

    return InstallResult(success=False, message=f"Phương thức cài đặt không được hỗ trợ: {method}")


# ---------------------------------------------------------------------------
# Vendor .deb auto-install (thêm 12/11/2026) — tải MỘT gói ``.deb`` từ domain
# chính chủ đã kiểm duyệt rồi ``pkexec apt-get install`` (apt tự giải quyết
# dependency cho một .deb local, giống hệt việc người dùng tự tải rồi
# double-click cài bằng tay — xem docstring ``install_deb_from_url``).
# ---------------------------------------------------------------------------

#: Kích thước tối đa một tệp ``.deb`` được phép tải — chặn một "trang chính
#: chủ" (hoặc domain bị compromise) trả về nội dung khổng lồ bất thường
#: (tràn đĩa/DoS). 500MB rộng rãi hơn mọi .deb desktop app thực tế.
_DEB_MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024

#: Timeout socket áp dụng cho CẢ kết nối lẫn mỗi lần đọc dữ liệu khi tải
#: ``.deb`` (``urllib`` dùng timeout này cho từng blocking call, không phải
#: tổng thời gian tải — đủ để chặn một kết nối treo vô hạn).
_DEB_DOWNLOAD_TIMEOUT_SECONDS = 120.0

#: User-Agent THẬT (không giả làm trình duyệt để lừa WAF/bot-detection) —
#: một số CDN chặn thẳng User-Agent mặc định của ``urllib``
#: (``Python-urllib/x.y``) nên cần khai báo rõ danh tính ứng dụng.
_DEB_DOWNLOAD_USER_AGENT = "NaMiOS-Assistant/1.0 (nAssistant App Concierge; 1-click installer)"

#: Magic bytes mở đầu MỌI gói Debian hợp lệ — định dạng ``ar`` archive, hai
#: thành phần đầu tiên luôn là chữ ký ``!<arch>\n`` rồi tên thành viên đầu
#: ``debian-binary`` (xem ``man 5 deb``). Kiểm tra byte THẬT của tệp đã tải,
#: KHÔNG tin đuôi tên tệp/header ``Content-Type`` do server khai báo (cả hai
#: đều có thể sai hoặc bị giả).
_DEB_MAGIC_PREFIX = b"!<arch>\ndebian-binary"
_DEB_MAGIC_READ_SIZE = 64

_DEB_DOWNLOAD_CHUNK_BYTES = 65536


def is_official_https_url(url: str, verify_domain: str) -> bool:
    """HÀM THUẦN (pure) — KHÔNG mạng, KHÔNG I/O, chỉ so khớp chuỗi. Đây là
    "cổng" an toàn DUY NHẤT quyết định một URL có được phép tải qua
    ``install_deb_from_url`` hay không — tách riêng khỏi phần tải mạng để
    TEST ĐƯỢC logic chặn (xem ``tests/test_app_catalog.py``) không cần
    mạng/không cần giả lập (mock) ``urllib``.

    Chấp nhận CHỈ khi CẢ HAI điều kiện đúng:

      1. ``url`` có scheme ``https`` — KHÔNG ``http``/bất kỳ scheme nào
         khác (chặn MITM đọc/sửa nội dung trên đường truyền; một kẻ tấn
         công ở giữa trên ``http`` có thể tráo hẳn nội dung tải về).
      2. hostname của ``url`` khớp ĐÚNG ``verify_domain`` HOẶC là một
         subdomain của nó (``hostname == verify_domain`` hoặc
         ``hostname.endswith("." + verify_domain)``). CHẶT hơn so khớp
         chuỗi con ngây thơ (``hostname.endswith(verify_domain)``) — tránh
         một domain đăng ký khác vô tình/cố ý có ĐUÔI trùng ký tự (vd
         ``"notzoom.us"`` kết thúc đúng bằng chuỗi ``"zoom.us"`` dù KHÔNG
         liên quan gì tới Zoom thật) bị chấp nhận nhầm.

    ``url``/``verify_domain`` rỗng, hoặc ``url`` không parse được -> LUÔN từ
    chối (an toàn mặc định — không có gì để pin domain vào thì không tải)."""

    if not url or not verify_domain:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme != "https":
        return False
    hostname = (parsed.hostname or "").lower()
    domain = verify_domain.strip().lower()
    if not hostname or not domain:
        return False
    return hostname == domain or hostname.endswith("." + domain)


def _looks_like_deb(path: Path) -> bool:
    """Đọc byte ĐẦU THẬT của tệp đã tải — KHÔNG tin đuôi tên tệp/khai báo
    của server (xem docstring ``_DEB_MAGIC_PREFIX``). Đọc/IO lỗi (tệp không
    tồn tại/không đọc được) -> ``False`` (an toàn mặc định, KHÔNG raise)."""

    try:
        with path.open("rb") as handle:
            header = handle.read(_DEB_MAGIC_READ_SIZE)
    except OSError:
        return False
    return header.startswith(_DEB_MAGIC_PREFIX)


def _download_to_file(url: str, dest_file: IO[bytes], *, verify_domain: str) -> InstallResult | None:
    """Tải ``url`` (ĐÃ qua ``is_official_https_url`` ở caller) vào tệp đang
    mở ``dest_file`` (mở nhị phân, ghi được) — ghi theo khối, giới hạn tổng
    kích thước, kiểm tra lại domain SAU KHI theo redirect (xem bên dưới).

    Trả ``None`` nếu tải xong không có lỗi (bước kiểm tra magic bytes thuộc
    về caller, KHÔNG phải hàm này — tách riêng "tải được" khỏi "tải đúng
    định dạng .deb"); trả ``InstallResult(success=False, ...)`` nếu bất kỳ
    bước nào thất bại (redirect sang domain lạ, vượt kích thước, lỗi
    mạng/ghi tệp) — KHÔNG raise ra ngoài, caller (``install_deb_from_url``)
    chỉ cần kiểm tra giá trị trả về."""

    request = urllib.request.Request(url, headers={"User-Agent": _DEB_DOWNLOAD_USER_AGENT})
    try:
        with urllib.request.urlopen(  # noqa: S310 - scheme đã bị chặn chỉ https ở is_official_https_url
            request, timeout=_DEB_DOWNLOAD_TIMEOUT_SECONDS
        ) as response:
            final_url = response.geturl()
            # ``urllib`` TỰ ĐỘNG theo redirect (HTTPRedirectHandler mặc
            # định) — PHẢI tái kiểm tra domain CUỐI CÙNG sau khi theo
            # redirect, nếu không domain-pin ở is_official_https_url coi
            # như vô nghĩa (chỉ kiểm tra URL BAN ĐẦU, một trang chính chủ
            # hoàn toàn có thể redirect sang CDN/mirror ở domain khác).
            if not is_official_https_url(final_url, verify_domain):
                return InstallResult(
                    success=False,
                    message=(
                        "Đường dẫn chuyển hướng (redirect) sang domain KHÔNG khớp "
                        f"domain chính chủ đã kiểm duyệt ('{verify_domain}'): "
                        f"'{final_url}' — từ chối tải tiếp, chưa cài gì."
                    ),
                )
            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                try:
                    declared_size = int(content_length)
                except ValueError:
                    declared_size = -1
                if declared_size > _DEB_MAX_DOWNLOAD_BYTES:
                    return InstallResult(
                        success=False,
                        message=(
                            f"Tệp khai báo kích thước {declared_size} byte, vượt giới "
                            f"hạn {_DEB_MAX_DOWNLOAD_BYTES} byte — từ chối tải, chưa "
                            "cài gì."
                        ),
                    )
            written = 0
            while True:
                chunk = response.read(_DEB_DOWNLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                written += len(chunk)
                if written > _DEB_MAX_DOWNLOAD_BYTES:
                    return InstallResult(
                        success=False,
                        message=(
                            f"Tệp tải về vượt giới hạn {_DEB_MAX_DOWNLOAD_BYTES} byte "
                            "— đã huỷ tải, chưa cài gì."
                        ),
                    )
                dest_file.write(chunk)
    except urllib.error.HTTPError as exc:
        return InstallResult(
            success=False,
            message=f"Máy chủ '{verify_domain}' trả lỗi HTTP {exc.code} khi tải tệp.",
        )
    except urllib.error.URLError as exc:
        return InstallResult(success=False, message=f"Không tải được tệp: {exc.reason}")
    except OSError as exc:
        return InstallResult(success=False, message=f"Lỗi ghi tệp tạm khi tải: {exc}")
    return None


def install_deb_from_url(url: str, verify_domain: str) -> InstallResult:
    """Tải MỘT gói ``.deb`` từ ``url`` rồi cài qua ``pkexec apt-get install -y
    <tệp tạm>`` — hiện thực "Vendor .deb auto-install" cho catalog entry
    ``method == "deb_official"`` (xem ``engine/app_catalog.py``), để "cài
    giúp tôi Chrome/Zoom" THỰC SỰ cài thay vì chỉ mở một trang tải.

    ``url``/``verify_domain`` PHẢI lấy từ ``InstallPlan.action_payload``/
    ``InstallPlan.verify_domain`` (catalog đã kiểm duyệt) — hàm này KHÔNG
    tin bất kỳ nguồn nào khác (đặc biệt KHÔNG BAO GIỜ nhận URL do văn bản
    người dùng gõ trực tiếp sinh ra).

    RÀO CHẮN an toàn, fail-closed theo THỨ TỰ (dừng ở rào đầu tiên vi phạm —
    KHÔNG tải thêm/KHÔNG cài gì khi một rào thất bại):

      1. ``is_official_https_url(url, verify_domain)`` — CHỈ https:// VÀ
         domain khớp/subdomain của ``verify_domain``.
      2. Tải vào MỘT tệp tạm riêng (``tempfile.NamedTemporaryFile``, quyền
         0600, tên ngẫu nhiên — không đoán được, không ghi đè tệp người
         dùng khác), giới hạn kích thước + timeout + User-Agent thật; mọi
         redirect (nếu có) PHẢI vẫn khớp domain-pin (xem
         ``_download_to_file``).
      3. Đọc byte ĐẦU THẬT của tệp đã tải, xác nhận đúng magic bytes một
         gói Debian (``_looks_like_deb``) — KHÔNG tin đuôi tên tệp/
         Content-Type. Sai định dạng -> xoá tệp, trả lỗi trung thực, KHÔNG
         BAO GIỜ thực thi/mở tệp đã tải bằng cách nào khác (vd KHÔNG tự
         đoán đây là archive/script rồi giải nén/chạy).
      4. CHỈ khi cả ba rào trên pass: ``pkexec apt-get install -y <tệp
         tạm>`` (apt tự giải quyết dependency cho một ``.deb`` local — đây
         là cách CHÍNH THỐNG của Debian để cài ``.deb`` local, giống hệt
         việc người dùng tự tải rồi double-click cài bằng tay hôm nay).

    LƯU Ý THÀNH THẬT về giới hạn an toàn: maintainer script bên trong một
    gói ``.deb`` hợp lệ (``postinst``/``preinst``/...) VẪN chạy với quyền
    root như MỌI lần cài ``.deb`` khác trên Debian — đây là bản chất của
    định dạng ``.deb``, KHÔNG phải một lỗ hổng riêng của hàm này. Điều hàm
    này đảm bảo là: tệp được cài CHẮC CHẮN tải từ domain chính chủ đã người
    kiểm duyệt catalog xác nhận trước, và CHẮC CHẮN là một gói Debian thật
    (không phải HTML/script/thực thi giả danh .deb) — không hơn, không kém.

    Tệp tạm LUÔN bị xoá ở cuối (``finally``), bất kể thành công/thất bại."""

    if not is_official_https_url(url, verify_domain):
        return InstallResult(
            success=False,
            message=(
                f"Đường dẫn '{url}' KHÔNG phải https:// thuộc domain chính chủ đã "
                f"kiểm duyệt ('{verify_domain}') — từ chối tải, chưa cài gì."
            ),
        )

    apt_get = _which("apt-get")
    if apt_get is None:
        return InstallResult(success=False, message="Không tìm thấy apt-get trên máy này.")
    pkexec = _which("pkexec")
    if pkexec is None:
        return InstallResult(
            success=False,
            message=(
                "Không tìm thấy pkexec (gói policykit-1) trên máy này — không "
                "thể xin quyền quản trị một cách an toàn để cài đặt."
            ),
        )

    tmp_file = tempfile.NamedTemporaryFile(
        prefix="namios-assistant-deb-", suffix=".deb", delete=False
    )
    tmp_path = Path(tmp_file.name)
    try:
        with tmp_file:
            download_error = _download_to_file(url, tmp_file, verify_domain=verify_domain)
        if download_error is not None:
            return download_error

        if not _looks_like_deb(tmp_path):
            return InstallResult(
                success=False,
                message=(
                    "Tệp tải về KHÔNG phải gói Debian (.deb) hợp lệ (sai magic bytes "
                    "mở đầu) — từ chối cài, đã xoá tệp tạm. Trang chính chủ có thể "
                    "chưa trả về liên kết tải TRỰC TIẾP (vd trang hướng dẫn thay vì "
                    "tệp .deb) — hãy dùng \"Mở trang chính thức\" để tải/cài bằng tay."
                ),
            )

        return _run_privileged(
            [apt_get, "install", "-y", str(tmp_path)], timeout=_INSTALL_TIMEOUT_SECONDS
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
