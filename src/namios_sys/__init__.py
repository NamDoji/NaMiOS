"""NaMiOS — tầng hệ điều hành "máy làm việc hằng ngày" (Phụ lục 05, SYS-001..042).

K0 = HỢP ĐỒNG DÙNG CHUNG + ACTION BROKER: Desktop (chuột/menu/tìm kiếm), CLI và
SmartAI gọi CÙNG một action broker và đọc CÙNG hồ sơ (``device_profile``/
``app_route``/``workflow_run``) → cùng trạng thái cho cùng việc.

Bất biến (trùng ECO/COMP/SAI): GUI mở / tệp tải / app cài đều KHÔNG đủ để
"workflow_verified" (SYS-013 tái dùng gate ECO-003); thiếu handler thật →
``BLOCKED`` trung thực (không bịa thành công); nạp từ dict KHÔNG tin nhãn trạng
thái. Phần cần ISO/máy/thiết bị/pilot/vendor (K1–K4, H01–H10) = BLOCKED.

Package tự được ``[tool.setuptools.packages.find] where=["src"]`` nhận diện.
"""

from __future__ import annotations

from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_sys._errors import SysErrorCode
from namios_sys._types import (
    SYS_SCHEMA_VERSION,
    ActionKind,
    ActionRequest,
    ActionResult,
    ActionStatus,
    AppRoute,
    CapabilityRow,
    DeviceFunctionStatus,
    DeviceProfile,
    LicenseStatus,
    PublishedStatus,
    RunState,
    WindowsMode,
    WorkflowRun,
    WorkflowStepRun,
)
from namios_sys.action_broker import (
    EXECUTABLE_SUFFIXES,
    ActionBroker,
    ActionHandler,
    PolicyCheck,
)
from namios_sys.capability_catalog import CapabilityCatalog, validate_capability_row
from namios_sys.certification import end_to_end_status, is_overclaim
from namios_sys.schema import (
    app_route_from_dict,
    validate_app_route,
    validate_workflow_run,
    workflow_run_from_dict,
)

__all__ = [
    # contracts / enums (SYS-037)
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
    "PublishedStatus",
    "WindowsMode",
    "SysErrorCode",
    # action broker (SYS-001/002)
    "ActionBroker",
    "ActionHandler",
    "PolicyCheck",
    "EXECUTABLE_SUFFIXES",
    # schema (SYS-037)
    "validate_app_route",
    "validate_workflow_run",
    "app_route_from_dict",
    "workflow_run_from_dict",
    # certification (SYS-013)
    "end_to_end_status",
    "is_overclaim",
    # capability catalog (SYS-038)
    "CapabilityCatalog",
    "validate_capability_row",
]
