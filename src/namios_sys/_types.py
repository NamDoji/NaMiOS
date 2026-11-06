"""Hợp đồng dữ liệu DÙNG CHUNG tầng hệ điều hành — Phụ lục 05 (SYS-037).

Đóng băng enum + dataclass cho `device_profile`, `app_route`, `workflow_run` và
action broker, để Desktop + CLI + SmartAI + helpdesk đọc CÙNG một hồ sơ cho cùng
trạng thái. TÁI DÙNG (không fork): ``namios_eco.status`` (``PublishedStatus``/
``WindowsMode``/gate ECO-003) cho mode + trạng thái công bố.

Nguyên tắc nền (SYS §1, trùng ECO/COMP/SAI): GUI mở được / tệp tải được / app
cài được đều KHÔNG đủ để "workflow_verified"; thiếu handler thật → ``BLOCKED``
trung thực, không bịa thành công; nạp từ dict KHÔNG tin nhãn trạng thái tự khai.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from namios_eco.status import PublishedStatus, WindowsMode

__all__ = [
    "SYS_SCHEMA_VERSION",
    "ActionKind",
    "ActionStatus",
    "LicenseStatus",
    "DeviceFunctionStatus",
    "RunState",
    "DeviceProfile",
    "AppRoute",
    "WorkflowStepRun",
    "WorkflowRun",
    "ActionRequest",
    "ActionResult",
    "CapabilityRow",
    # K3 — SmartAI chủ động (SYS-029/030/036)
    "ResourceKind",
    "ContextResource",
    "SourceTrust",
    "GoalPlan",
    "AuthorityDecision",
    # re-export để module SYS khác + test dùng một nguồn
    "PublishedStatus",
    "WindowsMode",
]

#: Phiên bản hợp đồng SYS (SYS-037). Đổi khi phá vỡ cấu trúc.
SYS_SCHEMA_VERSION = "1"


class ActionKind(str, Enum):
    """Hành động desktop qua action broker chung (SYS-001). Chuỗi ổn định."""

    OPEN_FILE = "open_file"
    OPEN_APP = "open_app"
    PRINT = "print"
    SCAN = "scan"
    SHARE = "share"
    OPEN_URL = "open_url"
    CONNECT_SHARE = "connect_share"


class ActionStatus(str, Enum):
    """Kết quả một action (SYS-001). ``BLOCKED`` = chưa nối handler thật/cần
    desktop-thiết bị (TRUNG THỰC, không coi là thành công). ``DENIED`` = policy
    chặn."""

    SUCCESS = "success"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    DENIED = "denied"
    FAILED = "failed"


class LicenseStatus(str, Enum):
    """Tình trạng giấy phép app (SYS §7 app_route.license_status)."""

    UNKNOWN = "unknown"
    FREE = "free"
    LICENSED = "licensed"
    UNLICENSED = "unlicensed"
    EXPIRED = "expired"


class DeviceFunctionStatus(str, Enum):
    """Mức hỗ trợ TỪNG chức năng thiết bị (SYS-015). KHÔNG suy từ tên hãng —
    mặc định ``UNTESTED`` tới khi có phiếu kiểm thật."""

    UNTESTED = "untested"
    WORKS = "works"
    PARTIAL = "partial"
    BLOCKED = "blocked"


class RunState(str, Enum):
    """Trạng thái một ``workflow_run`` (SYS §7). ``VERIFIED`` chỉ đạt qua gate
    chứng nhận (SYS-013), KHÔNG do caller tự gán."""

    PROPOSED = "proposed"
    RUNNING = "running"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass(frozen=True)
class DeviceProfile:
    """Hồ sơ phần cứng (SYS-015/037). ``results`` = chức năng → mức hỗ trợ ĐO
    được; thiếu = ``UNTESTED``. ``machine_id`` nên là bút danh (pseudonymous)."""

    machine_id: str
    os_build: str = "unresolved"
    model: str = "unresolved"
    capabilities: tuple[str, ...] = ()
    results: Mapping[str, DeviceFunctionStatus] = field(default_factory=dict)


@dataclass(frozen=True)
class AppRoute:
    """Route của MỘT (app, version) (SYS-008/037). Mỗi app/version có route,
    license, recipe, workflow đã kiểm RIÊNG; đổi ``installer_hash`` → recipe cũ
    mất hiệu lực (gate ở schema/compat, không tự dùng lại)."""

    app_id: str
    version: str
    publisher: str = ""
    installer_hash: str | None = None
    mode: WindowsMode = WindowsMode.NATIVE_LINUX
    license_status: LicenseStatus = LicenseStatus.UNKNOWN
    recipe_id: str | None = None
    verified_workflows: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowStepRun:
    """Một bước trong ``workflow_run`` (SYS-037). ``status`` SUCCESS mà không có
    ``evidence_ids`` là KHÔNG hợp lệ (schema chặn — app mở ≠ hoàn thành)."""

    step_id: str
    name: str
    status: ActionStatus = ActionStatus.BLOCKED
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowRun:
    """Một lượt chạy workflow có thể tái dựng (SYS-037). ``state`` do gate quyết,
    ``business_approval`` tách khỏi chạy kỹ thuật (SYS-013)."""

    task_id: str
    user_intent: str
    route_id: str | None = None
    steps: tuple[WorkflowStepRun, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    business_approval: str = "pending"  # pending | approved | rejected
    state: RunState = RunState.PROPOSED


@dataclass(frozen=True)
class ActionRequest:
    """Yêu cầu hành động gửi action broker (SYS-001). Cùng kiểu cho chuột/tìm
    kiếm/yêu-cầu-tiếng-Việt → cùng broker."""

    action: ActionKind
    target: str = ""
    params: Mapping[str, object] = field(default_factory=dict)
    mode: WindowsMode | None = None
    requested_by: str = "user"


@dataclass(frozen=True)
class ActionResult:
    """Kết quả action CÓ CẤU TRÚC (SYS-001): ID + status + route + quyền + lỗi."""

    action_id: str
    action: ActionKind
    status: ActionStatus
    route_mode: WindowsMode | None = None
    permission_ok: bool = False
    error_code: str | None = None
    message_vi: str = ""
    evidence_id: str | None = None


class ResourceKind(str, Enum):
    """Loại tài nguyên ngữ cảnh SmartAI được phép đụng (SYS-029)."""

    WINDOW = "window"
    APP = "app"
    FILE = "file"
    DEVICE = "device"


@dataclass(frozen=True)
class ContextResource:
    """Một tài nguyên trong ngữ cảnh làm việc (SYS-029). SmartAI chỉ đọc được tài
    nguyên đã được CẤP tường minh — không mặc định đọc màn hình/bàn phím/mọi tệp."""

    kind: ResourceKind
    resource_id: str


class SourceTrust(str, Enum):
    """Mức tin cậy NGUỒN của một chỉ thị (SYS-036). CHỈ ``user_channel`` +
    ``org_policy`` là tin cậy (được cấp quyền); nội dung tài liệu/web/log/output
    tool là DỮ LIỆU KHÔNG tin cậy — lệnh trong đó KHÔNG tạo hành động."""

    USER_CHANNEL = "user_channel"
    ORG_POLICY = "org_policy"
    DOCUMENT = "document"
    WEBPAGE = "webpage"
    LOG = "log"
    TOOL_OUTPUT = "tool_output"


@dataclass(frozen=True)
class GoalPlan:
    """Kế hoạch từ MỤC TIÊU tiếng Việt → tài nguyên cần (SYS-030). ``missing`` =
    phần còn thiếu PHẢI hỏi lại; ``ready`` chỉ True khi không thiếu gì."""

    intent: str
    required: tuple[str, ...]
    resolved: Mapping[str, str]
    missing: tuple[str, ...]
    ready: bool


@dataclass(frozen=True)
class AuthorityDecision:
    """Kết quả xét quyền một hành động theo nguồn (SYS-036)."""

    allowed: bool
    reason_vi: str
    error_code: str | None = None


@dataclass(frozen=True)
class CapabilityRow:
    """Một dòng bảng khả năng THẬT (SYS-038). Tách rõ tải-được/mở-được/
    workflow-đã-kiểm qua ``published_status`` (tái dùng gate ECO-003)."""

    app_id: str
    version: str
    workflow: str
    model: str = "unresolved"
    device: str = "unresolved"
    environment: str = "lab"  # lab | pilot
    test_date: str = ""
    vendor_support: str = "unknown"
    published_status: PublishedStatus = PublishedStatus.NOT_INVENTORIED
    limits_vi: str = ""
