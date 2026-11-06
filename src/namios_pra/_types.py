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
