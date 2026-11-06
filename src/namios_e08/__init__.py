"""NaMiOS — Phụ lục 08 (E08-001..040): quản trị driver + .NET + SmartAI vận hành.

I0 = HỢP ĐỒNG trung thực trên nền cơ chế Linux (udev/kernel/CUPS/SANE/NM/BlueZ),
TÁI DÙNG ``namios_pra``/``namios_sys``/``namios_smartai``/``namios_odc`` (KHÔNG dựng
hệ trạng thái thứ hai — §8): event bus debounce (1 thiết bị = 1 incident) + driver
match theo hardware-ID + provenance (không tên gần giống, nguồn fail-closed) + trạng
thái thiết bị theo-chức-năng + cài driver có giao dịch (hỏng→rollback) + Windows
dependency graph (mở GUI ≠ dùng được) + outcome validator (tool-ok ≠ workflow-ok) +
bounded actuator (log không thành lệnh; thay-đổi cần rollback; không root/binary/flash/ký).

Thiết bị/.NET/pilot THẬT (I1–I4, bài D/N/A) = BLOCKED. .NET fingerprint tái dùng
``namios_pra.classify_dotnet``; offline/manual reuse ``namios_pra.support``.
"""

from __future__ import annotations

from namios_e08 import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_e08._errors import E08ErrorCode
from namios_e08._types import (
    DRIVER_TIER_ORDER,
    E08_SCHEMA_VERSION,
    AiAction,
    AppRuntimeProfile,
    Bus,
    DepKind,
    DepNode,
    DepState,
    DeviceAction,
    DeviceFunction,
    DeviceIncident,
    DeviceState,
    DotnetKind,
    DotnetRoute,
    DriverCandidate,
    DriverMatch,
    DriverTier,
    InstallResult,
    InstallStage,
    Observation,
    Provenance,
    RawDeviceEvent,
    WorkflowVerdict,
)
from namios_e08.actuator import (
    FORBIDDEN_TOOL_MARKERS,
    action_is_safe,
    log_instruction_authorized,
)
from namios_e08.depgraph import (
    is_workflow_complete,
    tool_success_is_workflow_success,
    workflow_verdict,
)
from namios_e08.driver_match import match_driver, provenance_ok
from namios_e08.event_bus import coalesce_events, should_invoke_ai
from namios_e08.install_txn import run_install_transaction

__all__ = [
    "E08_SCHEMA_VERSION",
    "E08ErrorCode",
    # types
    "Bus",
    "DeviceAction",
    "RawDeviceEvent",
    "DriverTier",
    "DRIVER_TIER_ORDER",
    "Provenance",
    "DriverCandidate",
    "DriverMatch",
    "DeviceFunction",
    "DeviceState",
    "DeviceIncident",
    "InstallStage",
    "InstallResult",
    "DepKind",
    "DepState",
    "DepNode",
    "WorkflowVerdict",
    "Observation",
    "AppRuntimeProfile",
    "AiAction",
    "DotnetKind",
    "DotnetRoute",
    # event bus (E08-001/027)
    "coalesce_events",
    "should_invoke_ai",
    # driver match (E08-002/003)
    "match_driver",
    "provenance_ok",
    # install txn (E08-005)
    "run_install_transaction",
    # dep graph + outcome (E08-020/031)
    "workflow_verdict",
    "is_workflow_complete",
    "tool_success_is_workflow_success",
    # bounded actuator (E08-030)
    "log_instruction_authorized",
    "action_is_safe",
    "FORBIDDEN_TOOL_MARKERS",
]
