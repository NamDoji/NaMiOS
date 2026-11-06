"""Hợp đồng dữ liệu D0 — Phụ lục 06 (PRA-001..044).

Tầng hợp đồng + UX cho thiết bị đa chức năng, Office, .NET và theo-dõi-kết-quả.
TÁI DÙNG (không fork): ``namios_sys.DeviceFunctionStatus`` (mức hỗ trợ từng
chức năng), ``namios_eco.status.WindowsMode`` (chế độ chạy). Nguyên tắc trung
thực xuyên suốt: công bố theo (app + version + workflow + thiết bị + chế độ);
"mở được/launch được" ≠ "dùng được"; thiếu bằng chứng → ``unknown``/``untested``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from namios_sys import DeviceFunctionStatus

__all__ = [
    "PRA_SCHEMA_VERSION",
    # thiết bị đa chức năng (PRA-001)
    "DeviceFunction",
    "DeviceCapability",
    # Office route + fidelity (PRA-016/017)
    "OfficeNeed",
    "OfficeRoute",
    "OfficeRouteResult",
    "FidelitySeverity",
    "FidelityIssue",
    # .NET classifier (PRA-022)
    "DotnetKind",
    "DotnetRoute",
    "DotnetClassification",
    # theo dõi kết quả trung thực (PRA-032)
    "PrintStage",
    "SignSubmitStage",
    # Doctor-taxonomy (PRA-028..035)
    "ResolverRole",
    "DeviceFault",
    "DeviceSignals",
    "NetworkFault",
    "NetworkSignals",
    "Diagnosis",
    "OfficePreflight",
    "Hypothesis",
    "ChecklistStep",
    "Checklist",
    "PermissionScope",
    "PermissionDecision",
    "OfflineReport",
    # re-export
    "DeviceFunctionStatus",
]

PRA_SCHEMA_VERSION = "1"


class DeviceFunction(str, Enum):
    """Chức năng ĐỘC LẬP của máy đa chức năng (PRA-001). Mỗi chức năng có mức hỗ
    trợ + ngày test RIÊNG — in được + scan được KHÔNG tự suy ra copy được."""

    PRINT = "print"
    SCAN = "scan"
    COPY = "copy"
    FAX = "fax"


@dataclass(frozen=True)
class DeviceCapability:
    """Hồ sơ năng lực một thiết bị (PRA-001). ``functions`` = chức năng → mức hỗ
    trợ ĐO được; chức năng không khai = ``UNTESTED`` (không suy diễn)."""

    device_id: str
    model: str = "unknown"
    protocol: str = "unknown"
    functions: Mapping[DeviceFunction, DeviceFunctionStatus] = field(default_factory=dict)
    test_dates: Mapping[DeviceFunction, str] = field(default_factory=dict)


class OfficeNeed(str, Enum):
    """Nhu cầu khi mở tài liệu Office (PRA-016). Quyết định route."""

    READ = "read"
    PRINT = "print"
    EDIT = "edit"
    COLLABORATE = "collaborate"
    MACRO = "macro"
    ADDIN = "addin"
    SIGN = "sign"


class OfficeRoute(str, Enum):
    """Tuyến xử lý Office hợp lệ (PRA-016, §4.1). ``BLOCKED`` = chưa có tuyến đạt."""

    NATIVE_LINUX = "native_linux"
    MS365_WEB = "ms365_web"
    WINE = "wine"
    WINDOWS_VM = "windows_vm"
    REMOTE_WINDOWS = "remote_windows"
    VIEWER_READONLY = "viewer_readonly"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class OfficeRouteResult:
    """Kết quả chọn tuyến Office (PRA-016). ``reasons_vi`` giải thích vì sao."""

    route: OfficeRoute
    reasons_vi: tuple[str, ...] = ()
    windows_dependent: bool = False


class FidelitySeverity(str, Enum):
    """Mức khác biệt khi so tài liệu với bản gốc/Windows (PRA-017)."""

    INFO = "info"  # khác nhỏ (vd font thay thế) — báo, không chặn
    BLOCKING = "blocking"  # sai dữ liệu nghĩa (số tiền/trang/chữ ký) — PHẢI chặn


@dataclass(frozen=True)
class FidelityIssue:
    """Một khác biệt fidelity (PRA-017). ``BLOCKING`` chặn lưu/in."""

    field: str
    severity: FidelitySeverity
    detail_vi: str = ""


class DotnetKind(str, Enum):
    """Phân loại công nghệ .NET (PRA-022). ``UNKNOWN`` khi thiếu metadata."""

    FRAMEWORK_LEGACY = "framework_legacy"  # .NET Framework 2.x–4.x
    MODERN = "modern"  # .NET 5+ đa nền tảng
    ASPNET = "aspnet"
    CONSOLE = "console"
    WINFORMS = "winforms"
    WPF = "wpf"
    WINUI = "winui"
    UNKNOWN = "unknown"


class DotnetRoute(str, Enum):
    """Tuyến chạy .NET đã đo (PRA-023). Không nhận native Linux cho WPF/WinUI."""

    NATIVE_LINUX = "native_linux"
    WINE = "wine"
    WINDOWS_ONLY = "windows_only"  # cần Windows VM/remote (blocker native)
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DotnetClassification:
    """Kết quả phân loại .NET (PRA-022/023). ``traits`` = P/Invoke/COM/WebView2/
    VC++… (dấu hiệu quan sát được). ``route`` suy TẤT ĐỊNH từ kind+traits."""

    kind: DotnetKind
    route: DotnetRoute
    arch: str = "unknown"
    traits: frozenset[str] = frozenset()
    reason_vi: str = ""


class PrintStage(str, Enum):
    """Giai đoạn một job in — NGÔN NGỮ TRUNG THỰC (PRA-032). ``MACHINE_DONE`` =
    CUPS báo xử lý xong job, KHÔNG phải người dùng đã cầm bản in; chỉ
    ``USER_CONFIRMED`` mới là "đã nhận bản in"."""

    QUEUED = "queued"
    PRINTING = "printing"
    MACHINE_DONE = "machine_done"
    USER_CONFIRMED = "user_confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SignSubmitStage(str, Enum):
    """Giai đoạn ký/nộp — TÁCH RÕ (PRA-032): ký ≠ nộp ≠ cổng trả biên nhận."""

    PREPARED = "prepared"
    SIGNED = "signed"
    SUBMITTED = "submitted"
    RECEIPT_VERIFIED = "receipt_verified"
    FAILED = "failed"
    UNKNOWN = "unknown"


# --------------------------------------------------------------------------- #
# Doctor-taxonomy (PRA-028..035) — chẩn đoán có cấu trúc, trung thực, phân vai  #
# --------------------------------------------------------------------------- #


class ResolverRole(str, Enum):
    """Ai xử lý được lỗi (PRA-028/031/033). Phân vai để không đẩy mọi thứ cho
    người dùng, cũng không tự nhận việc vượt quyền."""

    USER = "user"  # người dùng tự làm được theo checklist
    IT = "it"  # cần IT/quản trị (VLAN/policy/profile/DNS)
    VENDOR = "vendor"  # cần vendor/CA (driver/SDK/plugin/token)


class DeviceFault(str, Enum):
    """Kết luận Device Doctor (PRA-028). 5 fixtures nghiệm thu = 5 fault KHÁC
    nhau. ``FUNCTION_ABSENT`` (máy không có chức năng, vd copy) ≠ "hỏng"."""

    HEALTHY = "healthy"
    OFFLINE = "offline"
    OUT_OF_PAPER = "out_of_paper"
    JOB_JAMMED = "job_jammed"
    MDNS_BLOCKED = "mdns_blocked"  # VLAN/firewall chặn mDNS → cấu hình site
    SCAN_BACKEND_MISSING = "scan_backend_missing"
    FUNCTION_ABSENT = "function_absent"  # chức năng chưa kiểm/không có — KHÔNG phải lỗi
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DeviceSignals:
    """Dấu hiệu QUAN SÁT được của thiết bị (PRA-028, data giả cho D0). Không đọc
    nội dung tài liệu — chỉ trạng thái thiết bị/hàng đợi theo quyền."""

    requested: DeviceFunction = DeviceFunction.PRINT
    reachable: bool = True  # máy phản hồi (online)
    paper_ok: bool = True
    media_jam: bool = False
    mdns_visible: bool = True  # thấy qua mDNS/DNS-SD
    on_same_subnet: bool = True
    scan_backend_present: bool = True


class NetworkFault(str, Enum):
    """Kết luận Network Doctor (PRA-029). Mỗi fault có việc-cần-làm RIÊNG —
    KHÔNG gom hết về 'khởi động lại router'."""

    HEALTHY = "healthy"
    SSID_NOT_FOUND = "ssid_not_found"
    WRONG_PASSWORD = "wrong_password"
    NO_IP = "no_ip"  # associated nhưng DHCP fail
    CAPTIVE_PORTAL = "captive_portal"
    DNS_ERROR = "dns_error"
    PROXY_VPN = "proxy_vpn"
    NO_INTERNET = "no_internet"
    PRINTER_OFF_NETWORK = "printer_off_network"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NetworkSignals:
    """Dấu hiệu QUAN SÁT được của mạng (PRA-029, data giả cho D0). Không đọc nội
    dung truy cập (PRA-029 giới hạn chẩn đoán)."""

    ssid_visible: bool = True
    auth_ok: bool = True
    has_ip: bool = True
    gateway_reachable: bool = True
    captive_portal: bool = False
    dns_ok: bool = True
    proxy_required: bool = False
    proxy_ok: bool = True
    internet_ok: bool = True
    printer_same_subnet: bool = True
    checking_printer: bool = False  # True = đang chẩn mạng cho máy in


@dataclass(frozen=True)
class Diagnosis:
    """Kết luận chẩn đoán có cấu trúc (PRA-028..031). ``is_blocker`` = không tự
    sửa tại chỗ (cần IT/vendor); ``is_terminal`` = dừng, không thử tiếp nữa."""

    domain: str  # "device" | "network" | "office" | "windows_app"
    fault: str
    cause_vi: str
    next_step_vi: str
    resolver: ResolverRole = ResolverRole.USER
    is_blocker: bool = False
    is_terminal: bool = False


@dataclass(frozen=True)
class OfficePreflight:
    """Kết quả Office Doctor (PRA-030): route + hậu quả + cờ an toàn dữ liệu.
    ``auto_upload`` LUÔN False (không tự đẩy file lên cloud)."""

    route: OfficeRoute
    windows_dependent: bool
    warnings_vi: tuple[str, ...]
    needs_explicit_consent: bool  # khi route web mà file có dữ liệu nhạy cảm
    auto_upload: bool = False


@dataclass(frozen=True)
class Hypothesis:
    """Một giả thuyết sửa lỗi Windows App (PRA-031). BẮT BUỘC có test + rollback;
    không có rollback → không được áp dụng."""

    summary_vi: str
    test_vi: str
    rollback_vi: str


@dataclass(frozen=True)
class ChecklistStep:
    """Một bước hướng dẫn (PRA-033)."""

    title_vi: str
    done: bool = False


@dataclass(frozen=True)
class Checklist:
    """Hướng dẫn đa bước có thể tiếp tục (PRA-033). ``visible`` ≤ 3 bước/màn hình;
    ``checkpoint`` = chỉ số bước đang làm (lưu để tiếp tục sau reboot)."""

    steps: tuple[ChecklistStep, ...]
    checkpoint: int = 0
    max_visible: int = 3


class PermissionScope(str, Enum):
    """Phạm vi quyền AI xin trước khi sửa (PRA-034). Việc GIAO DỊCH (ký/nộp/
    thanh toán) luôn cần xác nhận hành động cụ thể (SAI-017)."""

    READ = "read"
    WRITE = "write"
    TRANSACT = "transact"  # ký/nộp/thanh toán — luôn cần xác nhận riêng


@dataclass(frozen=True)
class PermissionDecision:
    """Kết quả xin quyền (PRA-034). Nguồn không tin cậy (log/web/tài liệu) KHÔNG
    BAO GIỜ cấp được quyền mới; giao dịch luôn cần xác nhận cụ thể."""

    granted: bool
    reason_vi: str
    requires_explicit_confirmation: bool = False
    error_code: str = ""


@dataclass(frozen=True)
class OfflineReport:
    """Khả năng khi model cloud không dùng được (PRA-035). Lõi desktop/thiết
    bị/Office native KHÔNG phụ thuộc AI cloud."""

    cloud_ai_available: bool
    available_vi: tuple[str, ...]
    degraded_vi: tuple[str, ...]
