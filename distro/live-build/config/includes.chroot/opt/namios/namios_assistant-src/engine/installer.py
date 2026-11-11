"""Cài đặt phần mềm/driver "1 chạm" cho App & Driver Concierge — hiện thực
DUY NHẤT trong ``namios_assistant`` được phép THAY ĐỔI hệ thống (mọi module
khác trong ``engine/`` chỉ ĐỌC/tra cứu, xem docstring ``engine/__init__.py``).

TÁI DÙNG đúng khuôn ``namios_antoan.actions._run_privileged`` (pkexec +
``namios_security.run_argv``, argv TĨNH, KHÔNG shell, dịch mã polkit
126/127 sang thông báo người dùng đọc được) — KHÔNG viết lại logic
pkexec/argv-safety ở module này, chỉ import ``run_argv`` từ
``namios_security`` (nền an toàn dùng chung của cả repo, xem
``namios_security/__init__.py``).

CHỈ HAI lệnh TĨNH được phép chạy qua đây, KHÔNG có đường nào khác:
  - ``pkexec apt-get install -y <package_id>``
  - ``pkexec flatpak install -y flathub <package_id>``

``package_id`` là MỘT token duy nhất nội suy vào argv — PHẢI đến từ
``InstallPlan.action_payload`` (tức từ catalog đã kiểm duyệt, xem
``engine/app_catalog.py``), KHÔNG BAO GIỜ từ văn bản người dùng gõ trực
tiếp. Module này không tự xác thực nguồn gốc chuỗi (đó là việc của
``app_catalog``/``backend``) — nó chỉ đảm bảo argv luôn TĨNH, không shell,
có timeout (cùng nguyên tắc ``namios_security.run_argv``)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from namios_security import ExecPolicyError, run_argv

__all__ = ["InstallResult", "install_package"]

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
