"""Trạng thái an toàn hệ thống — CHỈ ĐỌC, không bao giờ thay đổi cấu hình.

Mỗi hàm ``probe_*`` trả về một :class:`CardStatus` cho một "thẻ" trong Trung
tâm An toàn (SEC-1): Cập nhật, Tường lửa (UFW), AppArmor, Quét virus (ClamAV
on-demand), Sao lưu (Kup). Mọi lệnh con chạy qua
``namios_security.run_argv`` (argv tĩnh, KHÔNG shell, có timeout — WP8) hoặc
đọc file/``/proc`` trực tiếp bằng Python thuần; KHÔNG lệnh nào ở đây cần
quyền root/``pkexec`` — xem ``actions.py`` cho các hành động CÓ thay đổi hệ
thống hoặc cần quyền quản trị (luồng riêng, tách bạch theo đúng CLAUDE.md
"privileged actions go through pkexec, never silent sudo").

FAIL-SAFE tuyệt đối: thiếu công cụ (``ufw``/``aa-enabled``/``clamscan``/
``dpkg``/...) KHÔNG BAO GIỜ làm hàm raise — trả ``CardStatus(installed=False,
...)`` kèm hướng dẫn cài tiếng Việt rõ ràng (``docs/roadmap/
NEW-FUNCTIONS-DIRECTION.md`` khối SEC-1: "nếu không thì hiện 'chưa cài' +
hướng dẫn cài chính xác, không bao giờ một dấu tích xanh giả"). Timeout mọi
lệnh con để không treo giao diện khi gọi từ UI thread/worker.

TRUNG THỰC (VN09-030): ``ok=True`` CHỈ có nghĩa "lớp phòng thủ này đang BẬT
theo cấu hình đọc được lúc kiểm tra" — KHÔNG phải "máy an toàn tuyệt đối".
"""

from __future__ import annotations

import configparser
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from namios_core.security_types import CompletedProc
from namios_security import ExecPolicyError, run_argv

__all__ = [
    "CardStatus",
    "probe_update",
    "probe_firewall",
    "probe_apparmor",
    "probe_antivirus",
    "probe_backup",
]

#: Timeout mặc định cho các probe đọc trạng thái nhanh (systemctl/aa-enabled/
#: dpkg-query) — các lệnh này về bản chất chỉ đọc file/trạng thái cục bộ, nên
#: vài giây là quá đủ; timeout thấp để một máy có lệnh "treo" lạ không làm
#: toàn bộ cửa sổ chờ lâu.
_PROBE_TIMEOUT_SECONDS = 8.0

#: ``apt list --upgradable`` đọc cache cục bộ (KHÔNG gọi mạng/``apt update``)
#: nhưng trên máy yếu/cache lớn có thể chậm hơn các lệnh trên — timeout rộng
#: hơn một chút.
_APT_LIST_TIMEOUT_SECONDS = 20.0

#: Chữ ký ClamAV được coi là "còn mới" nếu cập nhật trong vòng N ngày gần
#: nhất — khớp đúng ngưỡng đã dùng ở ``namios-security-center``
#: (``hooks/normal/0630-security-default.hook.chroot`` phần (d)), KHÔNG tự
#: chọn một ngưỡng khác gây hai nguồn sự thật.
_CLAMAV_SIGNATURE_MAX_AGE_DAYS = 7


@dataclass(frozen=True)
class CardStatus:
    """Trạng thái hiệu lực của một thẻ trong Trung tâm An toàn.

    - ``installed``: công cụ nền (ufw/apparmor/clamav/kup-backup/apt) có mặt
      trên máy này không. ``False`` -> UI hiển thị "chưa cài" + ``install_hint``,
      KHÔNG BAO GIỜ một dấu tích xanh giả.
    - ``ok``: ``True`` = lớp phòng thủ đang bật/ổn theo cấu hình đọc được;
      ``False`` = tắt/cần chú ý; ``None`` = không xác định được (thiếu công cụ
      đọc trạng thái, hoặc lệnh đọc trạng thái lỗi) — KHÔNG đoán thành tốt.
    - ``headline``: một dòng ngắn tóm tắt (hiển thị cạnh chấm màu trạng thái).
    - ``detail``: nhiều dòng giải thích thêm (hiển thị dưới headline).
    - ``install_hint``: lệnh cài gói CHÍNH XÁC khi ``installed=False`` (vd
      ``"sudo apt install ufw"``) — ``None`` khi ``installed=True``.
    """

    installed: bool
    ok: bool | None
    headline: str
    detail: str
    install_hint: str | None = None


def _which(name: str) -> str | None:
    return shutil.which(name)


def _run(argv: list[str], *, timeout: float = _PROBE_TIMEOUT_SECONDS) -> CompletedProc | None:
    """Chạy ``argv`` qua ``run_argv``; trả ``None`` (KHÔNG raise) khi vi phạm
    chính sách exec/timeout/OSError — caller tự coi ``None`` là "không xác
    định được", không phải "lỗi hệ thống của người dùng"."""

    try:
        return run_argv(argv, timeout=timeout)
    except ExecPolicyError:
        return None


def _stdout_text(result: CompletedProc | None) -> str:
    if result is None:
        return ""
    return result.stdout.decode("utf-8", "replace").strip()


def _systemctl_is_active(unit: str) -> str:
    """``active``/``inactive``/``failed``/``unknown`` — không cần quyền root
    để đọc trạng thái một unit systemd đã biết tên."""

    systemctl = _which("systemctl")
    if systemctl is None:
        return "khong-xac-dinh"
    result = _run([systemctl, "is-active", unit])
    text = _stdout_text(result)
    return text or "khong-xac-dinh"


def _xdg_config_home() -> Path:
    """``$XDG_CONFIG_HOME`` hoặc ``~/.config`` — ĐÂY LÀ config generic của
    user hiện tại (nơi Kup/nhiều app KDE khác ghi), KHÔNG phải
    ``namios_core.paths.config_dir()`` (thư mục con RIÊNG của NaMiOS, dùng
    cho cấu hình của chính các app NaMiOS như ``namios_assistant``)."""

    value = os.environ.get("XDG_CONFIG_HOME")
    if value:
        return Path(value)
    return Path.home() / ".config"


def _process_running(comm_name: str) -> bool:
    """Dò một tiến trình đang chạy bằng tên ``comm`` qua ``/proc`` thuần
    Python (KHÔNG cần ``pgrep`` cài sẵn) — đọc-chỉ, bỏ qua PID không đọc được
    (tiến trình của user khác/đã kết thúc giữa lúc quét)."""

    proc_dir = Path("/proc")
    try:
        entries = list(proc_dir.iterdir())
    except OSError:
        return False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            comm = (entry / "comm").read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if comm == comm_name:
            return True
    return False


# ---------------------------------------------------------------------------
# 1) Cập nhật — apt (gói chờ cập nhật, qua cache cục bộ, KHÔNG gọi mạng) +
#    cấu hình unattended-upgrades (đọc file tĩnh, giống
#    ``namios-security-center`` AUTOUPDATE_STATUS).
# ---------------------------------------------------------------------------
def probe_update() -> CardStatus:
    apt_bin = _which("apt")

    auto_security_on = False
    unattended_conf = Path("/etc/apt/apt.conf.d/51namios-unattended")
    if unattended_conf.is_file():
        try:
            content = unattended_conf.read_text(encoding="utf-8", errors="replace")
            auto_security_on = 'APT::Periodic::Unattended-Upgrade "1"' in content
        except OSError:
            auto_security_on = False

    if apt_bin is None:
        return CardStatus(
            installed=False,
            ok=None,
            headline="Không tìm thấy lệnh apt",
            detail="Không đọc được trạng thái cập nhật vì thiếu lệnh apt trên máy này.",
            install_hint="apt là một phần của hệ thống cơ sở Debian — nếu thiếu, máy này có thể đã bị gỡ bỏ các gói nền tảng.",
        )

    upgradable_count: int | None = None
    result = _run([apt_bin, "list", "--upgradable"], timeout=_APT_LIST_TIMEOUT_SECONDS)
    if result is not None and result.returncode == 0:
        lines = result.stdout.decode("utf-8", "replace").splitlines()
        # Mỗi dòng gói hợp lệ có dạng "ten-goi/suite version arch [...]" — lọc
        # bằng việc có ký tự "/" ngay phần đầu, bỏ dòng tiêu đề/cảnh báo
        # (không phụ thuộc chuỗi "Listing..." theo locale cụ thể).
        upgradable_count = sum(
            1 for line in lines if "/" in line.split(" ", 1)[0] and line.strip()
        )

    if upgradable_count is None:
        headline = "Không đọc được số gói chờ cập nhật"
        ok: bool | None = None
    elif upgradable_count == 0:
        headline = "Không có gói nào chờ cập nhật (theo lần đồng bộ apt gần nhất)"
        ok = True
    else:
        plural = "gói" if upgradable_count == 1 else "gói"
        headline = f"{upgradable_count} {plural} đang chờ cập nhật"
        ok = False

    detail_lines = [
        "Cập nhật bảo mật tự động (unattended-upgrades, chỉ áp dụng gói trong "
        "nhóm bảo mật -security, KHÔNG tự khởi động lại máy): "
        + ("BẬT" if auto_security_on else "TẮT"),
        "Số gói chờ cập nhật được tính theo dữ liệu apt đã lưu sẵn trên máy — "
        "có thể chưa mới nhất nếu đã lâu bạn chưa bấm 'Kiểm tra cập nhật'.",
    ]
    return CardStatus(
        installed=True,
        ok=ok,
        headline=headline,
        detail="\n".join(detail_lines),
    )


# ---------------------------------------------------------------------------
# 2) Tường lửa (UFW) — chỉ đọc trạng thái unit systemd (KHÔNG cần root).
#    ``ufw status`` chi tiết (luật deny/allow) cần quyền root -> xem
#    ``actions.view_firewall_detail`` (qua pkexec, CHỈ khi người dùng bấm).
# ---------------------------------------------------------------------------
def probe_firewall() -> CardStatus:
    ufw_bin = _which("ufw")
    if ufw_bin is None:
        return CardStatus(
            installed=False,
            ok=None,
            headline="Chưa cài UFW",
            detail="Tường lửa UFW chưa có trên máy này.",
            install_hint="sudo apt install ufw",
        )

    service_state = _systemctl_is_active("ufw.service")
    if service_state == "active":
        headline = "Tường lửa đang BẬT (mặc định chặn kết nối đến máy)"
        ok: bool | None = True
    elif service_state in ("inactive", "failed"):
        headline = "Tường lửa đang TẮT"
        ok = False
    else:
        headline = "Không xác định được trạng thái tường lửa"
        ok = None

    detail_lines = [
        "Mặc định NaMi: chặn kết nối đến máy, cho phép kết nối ra ngoài — "
        "KHÔNG chặn được mã độc đã chạy sẵn trên máy tự kết nối ra ngoài.",
    ]
    if ok is False:
        detail_lines.append(
            "Bấm 'Bật tường lửa' bên dưới nếu bạn muốn chặn kết nối lạ đến "
            "máy ngay."
        )
    detail_lines.append(
        "Xem đầy đủ các luật chi tiết (ufw status verbose) cần quyền quản trị "
        "— bấm 'Xem chi tiết luật'."
    )
    return CardStatus(installed=True, ok=ok, headline=headline, detail="\n".join(detail_lines))


# ---------------------------------------------------------------------------
# 3) AppArmor — ``aa-enabled --quiet`` (không cần root) hoặc sysfs
#    ``/sys/module/apparmor/parameters/enabled`` khi thiếu ``aa-enabled``.
#    Danh sách hồ sơ đang nạp (``aa-status`` đầy đủ) cần quyền root -> xem
#    ``actions.view_apparmor_detail``.
# ---------------------------------------------------------------------------
def probe_apparmor() -> CardStatus:
    aa_enabled_bin = _which("aa-enabled")
    sysfs_path = Path("/sys/module/apparmor/parameters/enabled")

    if aa_enabled_bin is None and not sysfs_path.exists():
        return CardStatus(
            installed=False,
            ok=None,
            headline="Chưa cài AppArmor",
            detail="Không tìm thấy aa-enabled và không có module AppArmor trong kernel.",
            install_hint="sudo apt install apparmor apparmor-utils",
        )

    enabled: bool | None = None
    if aa_enabled_bin is not None:
        result = _run([aa_enabled_bin, "--quiet"])
        if result is not None:
            enabled = result.returncode == 0
    if enabled is None and sysfs_path.exists():
        try:
            raw = sysfs_path.read_text(encoding="utf-8", errors="replace").strip()
            enabled = raw.upper() in ("Y", "YES", "1")
        except OSError:
            enabled = None

    if enabled is True:
        headline = "AppArmor đang BẬT (giới hạn quyền ứng dụng theo hồ sơ)"
        ok: bool | None = True
        detail_extra = (
            "Chỉ các ứng dụng CÓ hồ sơ AppArmor mới bị giới hạn — app chưa có "
            "hồ sơ riêng vẫn chạy với quyền người dùng thông thường, không bị "
            "chặn thêm gì."
        )
    elif enabled is False:
        headline = "AppArmor đang TẮT"
        ok = False
        detail_extra = (
            "Có thể do thiếu tham số kernel 'apparmor=1 security=apparmor' lúc "
            "khởi động máy — đây là việc cấu hình bootloader nên KHÔNG thể bật "
            "chỉ bằng một nút bấm trong ứng dụng này; xem hướng dẫn tự cấu "
            "hình tại docs/SECURITY-DEFAULTS.md §3."
        )
    else:
        headline = "Không xác định được trạng thái AppArmor"
        ok = None
        detail_extra = "Không đọc được trạng thái enable/disable."

    detail_lines = [
        detail_extra,
        "Xem danh sách hồ sơ đang nạp (aa-status) cần quyền quản trị — bấm "
        "'Xem chi tiết hồ sơ'.",
    ]
    return CardStatus(installed=True, ok=ok, headline=headline, detail="\n".join(detail_lines))


# ---------------------------------------------------------------------------
# 4) Quét virus (ClamAV) — CHỈ on-demand theo thiết kế (VN09-029/030): không
#    có "always-on"/quét thường trú mặc định. Đọc: đã cài? tuổi chữ ký?
#    daemon on-access có đang chạy không (mong đợi KHÔNG, theo thiết kế).
# ---------------------------------------------------------------------------
def probe_antivirus() -> CardStatus:
    clamscan_bin = _which("clamscan")
    freshclam_bin = _which("freshclam")

    if clamscan_bin is None:
        return CardStatus(
            installed=False,
            ok=None,
            headline="Chưa cài ClamAV",
            detail=(
                "Chưa có công cụ quét ClamAV trên máy này. ClamAV ở NaMi CHỈ "
                "quét THEO YÊU CẦU — không chạy thường trú, không hứa chặn "
                "100% mã độc."
            ),
            install_hint="sudo apt install clamav clamav-freshclam",
        )

    signature_status: str | None = None
    signature_ok: bool | None = None
    sig_candidates = (
        "/var/lib/clamav/daily.cvd",
        "/var/lib/clamav/daily.cld",
        "/var/lib/clamav/main.cvd",
        "/var/lib/clamav/main.cld",
    )
    for sig_path_str in sig_candidates:
        sig_path = Path(sig_path_str)
        if not sig_path.is_file():
            continue
        try:
            mtime = sig_path.stat().st_mtime
        except OSError:
            continue
        age_days = int((datetime.now(timezone.utc).timestamp() - mtime) // 86400)
        if age_days <= _CLAMAV_SIGNATURE_MAX_AGE_DAYS:
            signature_status = f"Chữ ký đã cập nhật {age_days} ngày trước"
            signature_ok = True
        else:
            signature_status = (
                f"Chữ ký QUÁ HẠN {age_days} ngày chưa cập nhật — bấm "
                "'Cập nhật chữ ký' bên dưới."
            )
            signature_ok = False
        break

    if signature_status is None:
        signature_status = (
            "Chưa có dữ liệu chữ ký (freshclam chưa chạy lần nào) — bấm "
            "'Cập nhật chữ ký' bên dưới."
        )
        signature_ok = False

    onaccess_state = _systemctl_is_active("clamav-daemon.service")
    onaccess_running = onaccess_state == "active"

    ok: bool | None = signature_ok
    headline = "ClamAV đã cài, chỉ quét theo yêu cầu"

    detail_lines = [
        signature_status,
        (
            "Quét thường trú: "
            + ("ĐANG CHẠY" if onaccess_running else "TẮT theo thiết kế")
            + " — NaMi cố ý KHÔNG bật quét thường trú mặc định (tốn CPU/IO, "
            "có nguy cơ treo máy trên phần cứng chưa được kiểm thử hiệu năng "
            "kỹ, xem VN09-029)."
        ),
        "QUAN TRỌNG: 'quét sạch' KHÔNG phải bằng chứng máy không bị xâm nhập "
        "(VN09-030) — ClamAV chỉ giảm rủi ro, không hứa chặn 100% mã độc.",
        "" if freshclam_bin is not None else (
            "Thiếu lệnh freshclam (cập nhật chữ ký) — cài: sudo apt install "
            "clamav-freshclam."
        ),
    ]
    return CardStatus(
        installed=True,
        ok=ok,
        headline=headline,
        detail="\n".join(line for line in detail_lines if line),
    )


# ---------------------------------------------------------------------------
# 5) Sao lưu (Kup) — đã cài? đã cấu hình bật? đã chọn ổ đích chưa? daemon
#    đang chạy phiên này không. Đọc ``~/.config/kuprc`` (ghi mặc định bởi
#    ``hooks/normal/0620-backup-config.hook.chroot`` vào ``/etc/skel`` cho
#    user MỚI — ở đây đọc bản CỦA user hiện tại, có thể đã bị user tự sửa).
# ---------------------------------------------------------------------------
def probe_backup() -> CardStatus:
    dpkg_bin = _which("dpkg-query")
    installed = False
    if dpkg_bin is not None:
        result = _run([dpkg_bin, "-W", "-f=${Status}", "kup-backup"])
        text = _stdout_text(result)
        installed = result is not None and result.returncode == 0 and "install ok installed" in text

    if not installed:
        return CardStatus(
            installed=False,
            ok=None,
            headline="Chưa cài Kup (sao lưu cá nhân)",
            detail=(
                "Chưa tìm thấy gói kup-backup. NaMi dùng Kup (dựa trên bup) "
                "làm công cụ sao lưu cá nhân, lưu nhiều phiên bản theo thời "
                "gian."
            ),
            install_hint="sudo apt install kup-backup bup",
        )

    kuprc_path = _xdg_config_home() / "kuprc"
    backups_enabled: bool | None = None
    has_plan = False
    has_destination = False

    if kuprc_path.is_file():
        parser = configparser.ConfigParser()
        parser.optionxform = str  # type: ignore[assignment] - giữ nguyên hoa/thường của khoá kuprc
        try:
            parser.read(kuprc_path, encoding="utf-8")
        except (OSError, configparser.Error):
            parser = configparser.ConfigParser()
        if parser.has_section("Kup settings"):
            raw = parser.get("Kup settings", "Backups enabled", fallback="false")
            backups_enabled = raw.strip().lower() == "true"
        for section in parser.sections():
            if section.startswith("Plan/"):
                has_plan = True
                dest_uuid = parser.get(section, "Destination UUID", fallback="").strip()
                if dest_uuid:
                    has_destination = True

    daemon_running = _process_running("kupdaemon")

    if backups_enabled is None:
        headline = "Chưa có cấu hình sao lưu cho tài khoản này"
        ok: bool | None = None
    elif not backups_enabled:
        headline = "Sao lưu cá nhân đang TẮT"
        ok = False
    elif not has_plan:
        headline = "Sao lưu BẬT nhưng chưa có kế hoạch sao lưu nào"
        ok = False
    elif not has_destination:
        headline = "Sao lưu BẬT nhưng CHƯA chọn ổ đích"
        ok = False
    else:
        headline = "Sao lưu cá nhân đã cấu hình (có kế hoạch + ổ đích)"
        ok = True

    detail_lines = [
        "Tiến trình nền (kupdaemon) hiện tại: " + ("ĐANG CHẠY" if daemon_running else "KHÔNG chạy trong phiên này"),
        "Kup hỏi trước khi sao lưu/ghi đè (tuỳ chọn \"Hỏi trước\" mặc định "
        "BẬT) theo cấu hình mặc định của NaMi — KHÔNG tự chọn ổ/tự ghi đè "
        "âm thầm.",
        "Sao lưu KHÔNG tự động nếu bạn chưa từng mở Cài đặt > Sao lưu để chọn "
        "ổ ngoài lần đầu.",
    ]
    return CardStatus(installed=True, ok=ok, headline=headline, detail="\n".join(detail_lines))
