"""Hợp đồng dữ liệu I0 — Phụ lục 08 (E08-001..040).

Quản trị driver kiểu Device Manager (trên nền udev/kernel/CUPS/SANE/NM/BlueZ, KHÔNG
dùng Windows driver/INF) + phòng .NET + SmartAI vận hành có ranh giới quyền. TÁI DÙNG
(không dựng hệ trạng thái thứ hai — §8): ``namios_pra`` (DotnetKind/route, device
per-function, progress), ``namios_sys`` (data_authority/action broker), ``namios_smartai``
(triage/repair/promotion), ``namios_odc`` (device cert). Bất biến: "nhận thiết bị" ≠
"chạy được" ≠ "hoàn thành việc"; ghép driver theo hardware-ID (KHÔNG theo tên gần giống);
nội dung log/tài liệu KHÔNG thành lệnh; AI không tự firmware-flash/ký/nộp.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from namios_pra import DotnetKind, DotnetRoute

__all__ = [
    "E08_SCHEMA_VERSION",
    # event bus (E08-001/027)
    "Bus",
    "DeviceAction",
    "RawDeviceEvent",
    # driver match + provenance (E08-002/003)
    "DriverTier",
    "DRIVER_TIER_ORDER",
    "Provenance",
    "DriverCandidate",
    "DriverMatch",
    # device states + incident (E08-004/037)
    "DeviceFunction",
    "DeviceState",
    "DeviceIncident",
    # install transaction (E08-005)
    "InstallStage",
    "InstallResult",
    # windows dependency graph + outcome (E08-020/031)
    "DepKind",
    "DepState",
    "DepNode",
    "WorkflowVerdict",
    # .NET runtime profile (E08-017)
    "Observation",
    "AppRuntimeProfile",
    # AI action (E08-030)
    "AiAction",
    # re-export
    "DotnetKind",
    "DotnetRoute",
]

E08_SCHEMA_VERSION = "1"


# --------------------------------------------------------------------------- #
# E08-001/027 — Device event bus                                               #
# --------------------------------------------------------------------------- #


class Bus(str, Enum):
    USB = "usb"
    PCIE = "pcie"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    SERIAL = "serial"
    OTHER = "other"


class DeviceAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    CHANGE = "change"


@dataclass(frozen=True)
class RawDeviceEvent:
    """Một sự kiện udev/subsystem THÔ (E08-001). ``device_instance_id`` ổn định
    trong máy; ``ts`` = mốc thời gian (giây, caller truyền vào — tất định)."""

    device_instance_id: str
    action: DeviceAction
    ts: int
    bus: Bus = Bus.OTHER
    hardware_id: str = ""  # VID:PID hoặc id lớp thiết bị


# --------------------------------------------------------------------------- #
# E08-002/003 — Driver match + provenance                                      #
# --------------------------------------------------------------------------- #


class DriverTier(str, Enum):
    """Thứ tự ứng viên driver (E08-002). Ưu tiên từ trên xuống."""

    KERNEL_DISTRO = "kernel_distro"  # đã có trong kernel/distro
    DEVICE_CLASS = "device_class"  # chuẩn lớp (HID/mass-storage/IPP/UVC)
    OSS_BACKEND = "oss_backend"  # backend mã nguồn mở được phân phối
    VENDOR_LINUX_PKG = "vendor_linux_pkg"  # gói Linux chính thức của vendor
    UNSUPPORTED = "unsupported"


#: Thứ tự ưu tiên ghép (E08-002).
DRIVER_TIER_ORDER: tuple[DriverTier, ...] = (
    DriverTier.KERNEL_DISTRO,
    DriverTier.DEVICE_CLASS,
    DriverTier.OSS_BACKEND,
    DriverTier.VENDOR_LINUX_PKG,
)


@dataclass(frozen=True)
class Provenance:
    """Nguồn gốc driver/backend/firmware (E08-003). Không có hash/chữ-ký/nguồn
    chính thức → KHÔNG tin (fail-closed); KHÔNG tải binary từ URL AI bịa."""

    source_url: str = ""
    package: str = ""
    version: str = ""
    sha256: str = ""
    signature_ok: bool = False
    license: str = ""
    official: bool = False  # từ repo/vendor chính thức


@dataclass(frozen=True)
class DriverCandidate:
    """Một ứng viên driver (E08-002). ``hardware_ids`` = tập VID:PID/id-lớp mà gói
    này THẬT SỰ khai hỗ trợ — ghép theo đây, KHÔNG theo tên thương mại gần giống."""

    tier: DriverTier
    package: str
    hardware_ids: frozenset[str] = frozenset()
    provenance: Provenance = field(default_factory=Provenance)


@dataclass(frozen=True)
class DriverMatch:
    """Kết quả ghép driver (E08-002/003)."""

    matched: bool
    tier: DriverTier
    package: str
    reason_vi: str = ""


# --------------------------------------------------------------------------- #
# E08-004/037 — Device states + incident                                       #
# --------------------------------------------------------------------------- #


class DeviceFunction(str, Enum):
    PRINT = "print"
    SCAN = "scan"
    COPY_VIA_PC = "copy_via_pc"
    COPY_ON_DEVICE = "copy_on_device"
    FAX = "fax"
    NETWORK = "network"
    BLUETOOTH_AUDIO = "bluetooth_audio"
    STORAGE = "storage"
    TOKEN = "token"


class DeviceState(str, Enum):
    """Trạng thái THEO CHỨC NĂNG của một thiết bị (E08-004). KHÔNG một boolean
    chung — in có thể ``function_verified`` còn scan ``firmware_missing``."""

    DETECTED = "detected"
    DRIVER_FOUND = "driver_found"
    FIRMWARE_MISSING = "firmware_missing"
    PERMISSION_REQUIRED = "permission_required"
    BACKEND_STARTING = "backend_starting"
    FUNCTION_TEST_PENDING = "function_test_pending"
    FUNCTION_VERIFIED = "function_verified"
    PARTIAL = "partial"
    BLOCKED_VENDOR = "blocked_vendor"
    FAILED = "failed"
    REMOVED = "removed"
    NEEDS_RETEST = "needs_retest"


#: Trạng thái coi là "dùng được chức năng" — CHỈ một giá trị (E08-004/031).
_FUNCTION_OK: frozenset[DeviceState] = frozenset({DeviceState.FUNCTION_VERIFIED})


@dataclass(frozen=True)
class DeviceIncident:
    """Hồ sơ một thiết bị (E08-001/037). Một ``device_instance_id`` = MỘT incident;
    chức năng → trạng thái RIÊNG; ``event_count`` = số event thô đã gộp (debounce)."""

    device_instance_id: str
    bus: Bus = Bus.OTHER
    hardware_id: str = ""
    present: bool = True
    functions: Mapping[DeviceFunction, DeviceState] = field(default_factory=dict)
    event_count: int = 0


# --------------------------------------------------------------------------- #
# E08-005 — Cài/đổi driver có giao dịch                                         #
# --------------------------------------------------------------------------- #


class InstallStage(str, Enum):
    STAGE = "stage"
    CHECK_SOURCE = "check_source"
    SNAPSHOT = "snapshot"
    APPLY = "apply"
    FUNCTION_TEST = "function_test"
    COMMIT = "commit"
    ROLLBACK = "rollback"
    FAILED = "failed"


@dataclass(frozen=True)
class InstallResult:
    """Kết quả cài/đổi driver có giao dịch (E08-005). Hỏng trước commit → rollback
    về trạng thái cũ; KHÔNG để nửa vời."""

    committed: bool
    rolled_back: bool
    final_stage: InstallStage
    reason_vi: str = ""


# --------------------------------------------------------------------------- #
# E08-020/031 — Windows dependency graph + outcome                              #
# --------------------------------------------------------------------------- #


class DepKind(str, Enum):
    INSTALLER = "installer"
    RUNTIME = "runtime"
    COM_SERVICE = "com_service"
    DATABASE = "database"
    PRINTER_TOKEN = "printer_token"
    PORTAL = "portal"
    EXPORT_SUBMIT = "export_submit"


class DepState(str, Enum):
    OK = "ok"
    DOWN = "down"  # vd DB timeout
    MISSING = "missing"  # vd thiếu plugin/runtime
    BLOCKED = "blocked"  # khóa-Windows, không có Linux API
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DepNode:
    """Một node phụ thuộc Windows (E08-020). ``required`` = bắt buộc cho workflow."""

    kind: DepKind
    state: DepState = DepState.UNKNOWN
    required: bool = True
    detail_vi: str = ""


class WorkflowVerdict(str, Enum):
    """Kết luận workflow app Windows (E08-020/031). "mở GUI" ≠ "dùng được"."""

    BLOCKED = "blocked"  # có node bắt buộc BLOCKED
    PARTIAL = "partial_workflow"  # node bắt buộc DOWN/MISSING (vd DB mất)
    TOOL_OK_PENDING_BUSINESS = "tool_ok_pending_business"  # kỹ thuật ổn, chờ nghiệp vụ
    UNKNOWN = "unknown"


# --------------------------------------------------------------------------- #
# E08-017 — .NET runtime fingerprint                                           #
# --------------------------------------------------------------------------- #


class Observation(str, Enum):
    """Độ chắc của một dấu hiệu (E08-017). KHÔNG suy chỉ từ đuôi .exe."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AppRuntimeProfile:
    """Hồ sơ runtime một app (E08-017/025). Tái dùng DotnetKind/route; mỗi dấu hiệu
    gắn observed/inferred/unknown + nguồn."""

    app_id: str
    version: str = "unresolved"
    binary_hash: str = ""
    kind: DotnetKind = DotnetKind.UNKNOWN
    kind_observation: Observation = Observation.UNKNOWN
    route: DotnetRoute = DotnetRoute.UNKNOWN
    windows_dependencies: tuple[str, ...] = ()
    status: str = "not_inventoried"


# --------------------------------------------------------------------------- #
# E08-030 — AI action (bounded actuator)                                       #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AiAction:
    """Một hành động AI đề xuất (E08-030). Chỉ typed-tool theo quyền; BẮT BUỘC có
    rollback cho bước thay đổi; không root shell, không tự tải binary."""

    incident_id: str
    tool_name: str
    permission_scope: tuple[str, ...] = ()
    hypothesis_id: str = ""
    rollback_id: str = ""
    outcome_evidence_id: str = ""
