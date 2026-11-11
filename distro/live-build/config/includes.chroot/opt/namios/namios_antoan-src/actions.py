"""Hành động của Trung tâm An toàn — hai loại, TÁCH BẠCH rõ:

1. **Hành động CẦN quyền quản trị** (``enable_firewall``,
   ``view_firewall_detail``, ``view_apparmor_detail``,
   ``update_clamav_signatures``): LUÔN đi qua ``pkexec`` (polkit hỏi mật
   khẩu người dùng) — KHÔNG BAO GIỜ ``sudo`` âm thầm, KHÔNG tự cấp quyền,
   KHÔNG lưu mật khẩu. Argv tĩnh, KHÔNG shell, có timeout (``run_argv``/WP8).

2. **Hành động KHÔNG cần quyền** (``run_clamav_scan`` — quét một thư mục
   NGƯỜI DÙNG đã có quyền đọc, chạy bằng chính quyền user hiện tại, KHÔNG
   qua pkexec vì không có lý do kỹ thuật/bảo mật nào để chạy clamscan bằng
   root; ``open_update_center``/``open_backup_settings`` — chỉ MỞ ứng dụng
   khác đã có sẵn trong ảnh, tiến trình con độc lập, không chờ/không capture
   output).

KHÔNG tự chế lại tường lửa/AppArmor/scanner/backup ở đây — mọi hàm chỉ
BẬT/MỞ công cụ thật đã có trong ảnh (đúng nguyên tắc trung thực của SEC-1:
"OPEN them, don't reimplement")."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from namios_security import ExecPolicyError, run_argv

__all__ = [
    "ActionResult",
    "enable_firewall",
    "view_firewall_detail",
    "view_apparmor_detail",
    "run_clamav_scan",
    "update_clamav_signatures",
    "open_update_center",
    "open_backup_settings",
]

_PRIVILEGED_ACTION_TIMEOUT_SECONDS = 25.0
_CLAMAV_SCAN_TIMEOUT_SECONDS = 1800.0  # 30 phút — quét thư mục lớn có thể lâu.
_FRESHCLAM_TIMEOUT_SECONDS = 180.0  # tải chữ ký mới cần mạng, cho nhiều thời gian hơn.

#: Giới hạn độ dài output hiển thị trong hộp thoại kết quả — tránh một lệnh
#: in ra hàng chục nghìn dòng (vd quét thư mục rất lớn) làm treo/khó đọc UI.
_OUTPUT_DISPLAY_LIMIT_CHARS = 6000


@dataclass(frozen=True)
class ActionResult:
    """Kết quả một hành động. ``success=False`` có thể là: thiếu công cụ,
    người dùng từ chối polkit, timeout, hoặc lệnh trả mã lỗi — ``message`` nêu
    rõ trường hợp nào, KHÔNG gộp chung thành một câu "thất bại" mơ hồ."""

    success: bool
    message: str


def _which(name: str) -> str | None:
    return shutil.which(name)


def _trim_output(text: str) -> str:
    text = text.strip()
    if len(text) <= _OUTPUT_DISPLAY_LIMIT_CHARS:
        return text
    return text[-_OUTPUT_DISPLAY_LIMIT_CHARS:] + "\n\n[... đã cắt phần đầu, output quá dài ...]"


def _pkexec_bin() -> str | None:
    return _which("pkexec")


def _run_privileged(argv: list[str], *, timeout: float) -> ActionResult:
    """Chạy ``argv`` qua ``pkexec`` (argv[0] của ``argv`` PHẢI đã là đường
    dẫn tuyệt đối thật của lệnh cần quyền — KHÔNG phải tên trần, để
    ``ArgvSafeExec`` xác nhận được file tồn tại/thực thi được trước khi
    giao cho pkexec)."""

    pkexec = _pkexec_bin()
    if pkexec is None:
        return ActionResult(
            success=False,
            message=(
                "Không tìm thấy pkexec (gói policykit-1) trên máy này — không "
                "thể xin quyền quản trị an toàn. Hãy báo IT/hỗ trợ."
            ),
        )
    try:
        result = run_argv([pkexec, *argv], timeout=timeout)
    except ExecPolicyError as exc:
        return ActionResult(success=False, message=f"Không thực hiện được: {exc.reason_vi}")

    stdout_text = result.stdout.decode("utf-8", "replace")
    stderr_text = result.stderr.decode("utf-8", "replace")
    combined = (stdout_text + ("\n" + stderr_text if stderr_text.strip() else "")).strip()

    if result.returncode == 126:
        return ActionResult(
            success=False,
            message="Bạn đã từ chối cấp quyền quản trị (hộp thoại polkit) — không có gì thay đổi.",
        )
    if result.returncode != 0:
        return ActionResult(
            success=False,
            message=f"Lệnh trả mã lỗi {result.returncode}.\n\n{_trim_output(combined) or '(không có output)'}",
        )
    return ActionResult(success=True, message=_trim_output(combined) or "Hoàn tất, không có output.")


def _launch_detached(argv: list[str]) -> bool:
    """Mở một ứng dụng GUI độc lập (KHÔNG chờ, KHÔNG capture output — giống
    ``launch_bg`` trong các script bash hiện có của repo, vd
    ``namios-control-panel``). ``argv[0]`` PHẢI là đường dẫn tuyệt đối đã xác
    nhận tồn tại; trả ``False`` nếu không khởi động được tiến trình (KHÔNG
    raise — caller tự hiển thị thông báo lỗi thân thiện)."""

    program = argv[0]
    if not os.path.isabs(program) or not os.path.exists(program):
        return False
    try:
        subprocess.Popen(  # noqa: S603 - argv-only, shell=False, đã kiểm argv[0] tồn tại tuyệt đối
            argv,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return False
    return True


# ---------------------------------------------------------------------------
# Tường lửa (UFW) — CẦN quyền quản trị.
# ---------------------------------------------------------------------------
def enable_firewall() -> ActionResult:
    ufw_bin = _which("ufw")
    if ufw_bin is None:
        return ActionResult(success=False, message="Chưa cài UFW — cài: sudo apt install ufw")
    # --force để bỏ qua câu hỏi tương tác "yes" của ufw (không có TTY tương
    # tác khi chạy từ GUI qua pkexec) — đây là cờ CHÍNH THỨC của ufw(8), không
    # phải bỏ qua bước xác nhận của NaMiOS (người dùng đã xác nhận ở hộp
    # thoại "Bật tường lửa" của chính app này TRƯỚC khi gọi hàm này).
    return _run_privileged([ufw_bin, "--force", "enable"], timeout=_PRIVILEGED_ACTION_TIMEOUT_SECONDS)


def view_firewall_detail() -> ActionResult:
    ufw_bin = _which("ufw")
    if ufw_bin is None:
        return ActionResult(success=False, message="Chưa cài UFW — cài: sudo apt install ufw")
    return _run_privileged([ufw_bin, "status", "verbose"], timeout=_PRIVILEGED_ACTION_TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# AppArmor — CHỈ xem chi tiết (CẦN quyền quản trị để đọc securityfs). KHÔNG
# có hành động "bật" ở đây: AppArmor LSM chỉ enforce thật khi kernel cmdline
# có 'apparmor=1 security=apparmor' (cấu hình bootloader, cần reboot) — một
# nút bấm trong app KHÔNG thể làm việc này một cách trung thực, xem
# docs/SECURITY-DEFAULTS.md §3.
# ---------------------------------------------------------------------------
def view_apparmor_detail() -> ActionResult:
    aa_status_bin = _which("aa-status")
    if aa_status_bin is None:
        return ActionResult(
            success=False,
            message="Chưa cài aa-status — cài: sudo apt install apparmor-utils",
        )
    return _run_privileged([aa_status_bin], timeout=_PRIVILEGED_ACTION_TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# ClamAV — quét KHÔNG cần quyền quản trị (chạy bằng quyền user hiện tại,
# chỉ đọc file người dùng đã có quyền đọc); cập nhật chữ ký (freshclam) CẦN
# quyền quản trị (freshclam cần ghi vào /var/lib/clamav).
# ---------------------------------------------------------------------------
def run_clamav_scan(folder: str) -> ActionResult:
    clamscan_bin = _which("clamscan")
    if clamscan_bin is None:
        return ActionResult(
            success=False,
            message="Chưa cài ClamAV — cài: sudo apt install clamav",
        )
    folder_path = Path(folder)
    if not folder_path.is_dir():
        return ActionResult(success=False, message=f"Không tìm thấy thư mục: {folder}")

    try:
        result = run_argv(
            [clamscan_bin, "-r", "--no-summary=no", str(folder_path)],
            timeout=_CLAMAV_SCAN_TIMEOUT_SECONDS,
        )
    except ExecPolicyError as exc:
        return ActionResult(
            success=False,
            message=(
                f"Quét vượt quá thời gian cho phép hoặc lỗi thực thi: {exc.reason_vi}. "
                "Thư mục có thể quá lớn — hãy thử quét một thư mục con nhỏ hơn."
            ),
        )

    stdout_text = result.stdout.decode("utf-8", "replace")
    # clamscan: 0 = không phát hiện, 1 = PHÁT HIỆN file nghi nhiễm, 2 = lỗi.
    marker = "----------- SCAN SUMMARY -----------"
    summary = stdout_text.split(marker, 1)
    display_text = (marker + summary[1]) if len(summary) == 2 else stdout_text

    if result.returncode == 0:
        return ActionResult(success=True, message=_trim_output(display_text) or "Quét xong, không phát hiện gì.")
    if result.returncode == 1:
        return ActionResult(
            success=False,
            message=(
                "PHÁT HIỆN file nghi nhiễm — xem chi tiết dưới đây. ClamAV KHÔNG tự "
                "xoá/cách ly gì; bạn tự quyết định xử lý file được báo.\n\n"
                + (_trim_output(display_text) or "(không có chi tiết)")
            ),
        )
    stderr_text = result.stderr.decode("utf-8", "replace")
    return ActionResult(
        success=False,
        message=f"clamscan trả mã lỗi {result.returncode}.\n\n{_trim_output(stderr_text or display_text)}",
    )


def update_clamav_signatures() -> ActionResult:
    freshclam_bin = _which("freshclam")
    if freshclam_bin is None:
        return ActionResult(
            success=False,
            message="Chưa cài freshclam — cài: sudo apt install clamav-freshclam",
        )
    return _run_privileged([freshclam_bin], timeout=_FRESHCLAM_TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# Mở công cụ thật đã có trong ảnh — KHÔNG cần quyền quản trị, chỉ khởi chạy
# tiến trình độc lập (GUI tự xin quyền riêng của nó nếu cần, vd Discover tự
# hỏi polkit khi người dùng bấm "Cập nhật" bên trong Discover).
# ---------------------------------------------------------------------------
def open_update_center() -> ActionResult:
    """Chuỗi fallback giống hệt ``namios-control-panel do_update`` (KHÔNG
    sửa/gọi lại chính script đó để tránh phụ thuộc chéo không cần thiết —
    chỉ mô phỏng đúng thứ tự ưu tiên: control panel có sẵn -> Discover
    trang Cập nhật -> Discover trần -> KCM cập nhật)."""

    control_panel = _which("namios-control-panel")
    if control_panel is not None and _launch_detached([control_panel, "--category", "update"]):
        return ActionResult(success=True, message="Đang mở Trung tâm cập nhật (Discover) qua Control Panel.")

    discover_update = _which("plasma-discover-update")
    if discover_update is not None and _launch_detached([discover_update]):
        return ActionResult(success=True, message="Đang mở Discover — trang Cập nhật.")

    discover = _which("plasma-discover")
    if discover is not None and _launch_detached([discover]):
        return ActionResult(success=True, message="Đang mở Trung tâm phần mềm Discover.")

    kcmshell6 = _which("kcmshell6")
    if kcmshell6 is not None and _launch_detached([kcmshell6, "kcm_updates"]):
        return ActionResult(success=True, message="Đang mở System Settings — Cập nhật.")

    return ActionResult(
        success=False,
        message="Không tìm thấy Discover/kcmshell6 để mở trang Cập nhật trên máy này.",
    )


def open_backup_settings() -> ActionResult:
    """Chuỗi fallback giống hệt wrapper có sẵn ``namios-mo-sao-luu`` (tạo bởi
    ``hooks/normal/0620-backup-config.hook.chroot``) — ưu tiên gọi chính
    wrapper đó (KHÔNG viết lại logic mở KCM Kup), dự phòng khi wrapper vắng."""

    wrapper = _which("namios-mo-sao-luu")
    if wrapper is not None and _launch_detached([wrapper]):
        return ActionResult(success=True, message="Đang mở cài đặt Sao lưu (Kup).")

    for kcmshell_name in ("kcmshell6", "kcmshell5"):
        kcmshell = _which(kcmshell_name)
        if kcmshell is not None and _launch_detached([kcmshell, "kcm_kup"]):
            return ActionResult(success=True, message="Đang mở System Settings — Sao lưu.")

    systemsettings = _which("systemsettings")
    if systemsettings is not None and _launch_detached([systemsettings]):
        return ActionResult(
            success=True,
            message="Đang mở System Settings — hãy tự tìm mục Sao lưu.",
        )

    return ActionResult(
        success=False,
        message="Không tìm thấy công cụ mở cài đặt Sao lưu (kcmshell6/systemsettings) trên máy này.",
    )
