"""Tự kiểm môi trường TRƯỚC KHI bắt đầu dùng dịch vụ (VN-2 acceptance
criteria, ECO-008): trình duyệt/PDF-ký-số/LibreOffice/giờ hệ thống — CHỈ kết
luận phần QUAN SÁT ĐƯỢC từ Python thuần (``shutil.which``/``datetime``,
không exec gì), KHÔNG thu PIN/khoá, KHÔNG bịa kết quả cho thứ không tự kiểm
được (popup/font rendering) — những mục đó trả về như một NHẮC NHỞ tự kiểm
tay, không giả vờ đã kiểm (ECO-008: "chỉ kết luận phần quan sát được").

Cùng nguyên tắc với ``namios_doctor.capabilities.collect_capabilities``:
"Chỉ đọc: platform/os.environ/PATH qua shutil.which — KHÔNG thực thi gì" —
NGOẠI LỆ DUY NHẤT là ``probe_pkcs11_slots`` (dò token USB qua
``pkcs11-tool --list-slots``), vì VN-3 acceptance criteria yêu cầu rõ hành vi
này ("thử phát hiện pkcs11-tool --list-slots và công bố trung thực
blocked/unknown"). Lệnh đó liệt kê slot, KHÔNG cần/KHÔNG hỏi PIN — tách riêng
khỏi ``run_env_check`` (không tự động chạy mỗi lần mở app, CHỈ chạy khi người
dùng bấm nút rõ ràng trong Trung tâm Ký số)."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime

__all__ = [
    "BrowserCheck",
    "SigningToolCheck",
    "SystemClockCheck",
    "EnvCheckReport",
    "run_env_check",
    "Pkcs11ProbeResult",
    "probe_pkcs11_slots",
]

_PKCS11_PROBE_TIMEOUT_SECONDS = 6.0


@dataclass(frozen=True)
class BrowserCheck:
    xdg_open_present: bool
    known_browser_present: tuple[str, ...]  # tên trình duyệt tìm thấy qua PATH


@dataclass(frozen=True)
class SigningToolCheck:
    okular_present: bool
    libreoffice_present: bool
    opensc_pkcs11_tool_present: bool


@dataclass(frozen=True)
class SystemClockCheck:
    local_time_iso: str
    timezone_name: str | None


@dataclass(frozen=True)
class EnvCheckReport:
    browser: BrowserCheck
    signing_tools: SigningToolCheck
    clock: SystemClockCheck
    #: Mục KHÔNG tự kiểm được bằng Python thuần (ECO-008: không bịa kết
    #: luận cho phần không quan sát được) — hiển thị như nhắc nhở tự kiểm tay.
    manual_check_reminders_vi: tuple[str, ...]
    manual_check_reminders_en: tuple[str, ...]


#: Tên trình duyệt phổ biến dò qua PATH — KHÔNG suy ra "trình duyệt mặc định
#: là cái nào" (việc đó cần đọc xdg mimeapps.list, dễ sai trên nhiều desktop
#: environment khác nhau) — chỉ báo "có mặt trên PATH hay không", trung thực
#: ở đúng mức dữ liệu quan sát được.
_KNOWN_BROWSER_COMMANDS: tuple[str, ...] = (
    "firefox-esr",
    "firefox",
    "chromium",
)

_MANUAL_REMINDERS_VI: tuple[str, ...] = (
    "Popup bị chặn hay không: tự mở một trang có popup đăng nhập thử (vd trang ký số từ "
    "xa) rồi xem có hộp thoại bị chặn không — NaMi không tự kiểm được việc này từ mã.",
    "Font/dấu tiếng Việt hiển thị đúng không: tự nhìn vào trang/tài liệu có dấu tiếng Việt "
    "(ă, â, ê, ô, ơ, ư, đ) xem có vuông/mất chữ không.",
    "Chứng thư số (.p12) của bạn còn hạn hay không: tự kiểm với nhà cung cấp chữ ký số, "
    "NaMi không đọc nội dung file chứng thư của bạn.",
)
_MANUAL_REMINDERS_EN: tuple[str, ...] = (
    "Whether popups are blocked: open a page with a login popup yourself (e.g. a remote "
    "signing page) and see if a dialog gets blocked — NaMi cannot check this from code.",
    "Whether Vietnamese diacritics render correctly: look at a page/document with Vietnamese "
    "accented letters (ă, â, ê, ô, ơ, ư, đ) and check for missing/boxed glyphs.",
    "Whether your .p12 certificate is still valid: check with your signing provider yourself; "
    "NaMi does not read the contents of your certificate file.",
)


def _local_time_iso() -> str:
    try:
        return datetime.now().astimezone().isoformat(timespec="seconds")
    except (OverflowError, OSError):
        return datetime.now().isoformat(timespec="seconds")


def _timezone_name() -> str | None:
    try:
        tzinfo = datetime.now().astimezone().tzinfo
    except (OverflowError, OSError):
        return None
    return str(tzinfo) if tzinfo is not None else None


def run_env_check() -> EnvCheckReport:
    """Thu thập báo cáo tự kiểm môi trường THẬT của máy hiện tại — chỉ
    ``shutil.which``/``datetime``, KHÔNG spawn process con, KHÔNG shell."""

    browser = BrowserCheck(
        xdg_open_present=shutil.which("xdg-open") is not None,
        known_browser_present=tuple(
            name for name in _KNOWN_BROWSER_COMMANDS if shutil.which(name) is not None
        ),
    )
    signing_tools = SigningToolCheck(
        okular_present=shutil.which("okular") is not None,
        libreoffice_present=shutil.which("soffice") is not None,
        opensc_pkcs11_tool_present=shutil.which("pkcs11-tool") is not None,
    )
    clock = SystemClockCheck(
        local_time_iso=_local_time_iso(),
        timezone_name=_timezone_name(),
    )
    return EnvCheckReport(
        browser=browser,
        signing_tools=signing_tools,
        clock=clock,
        manual_check_reminders_vi=_MANUAL_REMINDERS_VI,
        manual_check_reminders_en=_MANUAL_REMINDERS_EN,
    )


@dataclass(frozen=True)
class Pkcs11ProbeResult:
    tool_present: bool
    ran_successfully: bool
    raw_output: str | None
    note_vi: str
    note_en: str
    error: str | None


def probe_pkcs11_slots(*, timeout: float = _PKCS11_PROBE_TIMEOUT_SECONDS) -> Pkcs11ProbeResult:
    """Dò token USB chữ ký số qua ``pkcs11-tool --list-slots`` (VN-3
    acceptance criteria, tuyến 3). CHỈ ĐỌC — lệnh này liệt kê slot PKCS#11,
    KHÔNG yêu cầu PIN, KHÔNG ghi/sửa gì trên token. Argv cố định (không nội
    suy input người dùng nào vào argv) + ``shell=False`` + timeout — không
    có đường injection, không treo UI nếu công cụ phản hồi chậm/không phản
    hồi. Thiếu công cụ hoặc lỗi bất kỳ -> kết luận trung thực "unknown",
    KHÔNG BAO GIỜ suy diễn thành "works"."""

    tool_path = shutil.which("pkcs11-tool")
    if tool_path is None:
        return Pkcs11ProbeResult(
            tool_present=False,
            ran_successfully=False,
            raw_output=None,
            note_vi=(
                "Chưa có công cụ pkcs11-tool trên máy này (gói opensc) — KHÔNG thể tự dò "
                "token USB. Đây là 'unknown' (chưa biết), KHÔNG phải xác nhận token không "
                "hoạt động. Cài gói 'opensc' rồi thử lại nếu muốn tự kiểm."
            ),
            note_en=(
                "pkcs11-tool is not installed on this machine (opensc package) — cannot "
                "probe a USB token. This is 'unknown', NOT a confirmation the token fails. "
                "Install the 'opensc' package and retry if you want to check yourself."
            ),
            error=None,
        )

    try:
        completed = subprocess.run(  # noqa: S603 - argv cố định, shell=False, có timeout
            [tool_path, "--list-slots"],
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return Pkcs11ProbeResult(
            tool_present=True,
            ran_successfully=False,
            raw_output=None,
            note_vi="pkcs11-tool không phản hồi trong thời gian cho phép — kết luận 'unknown'.",
            note_en="pkcs11-tool did not respond in time — conclusion is 'unknown'.",
            error="timeout",
        )
    except OSError as exc:
        return Pkcs11ProbeResult(
            tool_present=True,
            ran_successfully=False,
            raw_output=None,
            note_vi=f"Không chạy được pkcs11-tool: {exc}. Kết luận 'unknown'.",
            note_en=f"Could not run pkcs11-tool: {exc}. Conclusion is 'unknown'.",
            error=str(exc),
        )

    combined_output = (completed.stdout or "") + (("\n" + completed.stderr) if completed.stderr else "")
    output_text = combined_output.strip()
    slot_found = completed.returncode == 0 and bool(output_text) and "no slots" not in output_text.lower()

    if slot_found:
        note_vi = "Đã thấy ít nhất một slot PKCS#11 — xem chi tiết dưới đây. Chưa chắc token đã ký được (cần thử ký thật mới biết chắc)."
        note_en = "At least one PKCS#11 slot was found — see details below. This does not guarantee the token can sign (a real sign attempt is needed to be sure)."
    else:
        note_vi = (
            "KHÔNG thấy slot PKCS#11 nào — kết luận trung thực: token này chưa dùng được "
            "qua PKCS#11 trên máy này (đúng với khảo sát docs/wine/KY-SO-PKCS11-RESEARCH.md: "
            "3 hãng CA lớn chưa có middleware Linux chính hãng công khai)."
        )
        note_en = (
            "NO PKCS#11 slot was found — honest conclusion: this token does not yet work "
            "via PKCS#11 on this machine (consistent with docs/wine/KY-SO-PKCS11-RESEARCH.md: "
            "the three major CAs have no publicly known official Linux middleware)."
        )

    return Pkcs11ProbeResult(
        tool_present=True,
        ran_successfully=True,
        raw_output=output_text or None,
        note_vi=note_vi,
        note_en=note_en,
        error=None,
    )
