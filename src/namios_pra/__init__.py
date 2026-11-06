"""NaMiOS — Phụ lục 06 (PRA-001..044): thiết bị đa chức năng, Office, .NET, UX.

D0 = HỢP ĐỒNG trung thực, TÁI DÙNG tầng dưới (namios_sys/eco/dotnet), không fork:
thiết bị khai năng-lực-từng-chức-năng (in≠scan≠copy), Office chọn tuyến theo nhu
cầu (macro/add-in không bao giờ web) + fidelity gate (sai số tiền/trang → chặn),
.NET phân loại có tuyến (WPF/WinUI không native Linux), và theo-dõi-kết-quả trung
thực (queued ≠ in xong ≠ đã nhận; ký ≠ nộp ≠ biên nhận).

Phần cần thiết bị/Office/.NET/pilot THẬT (D1–D4, bài P01–P13, §10) = BLOCKED.
"""

from __future__ import annotations

from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_pra._errors import PraErrorCode
from namios_pra._types import (
    PRA_SCHEMA_VERSION,
    Checklist,
    ChecklistStep,
    DeviceCapability,
    DeviceFault,
    DeviceFunction,
    DeviceFunctionStatus,
    DeviceSignals,
    Diagnosis,
    DotnetClassification,
    DotnetKind,
    DotnetRoute,
    FidelityIssue,
    FidelitySeverity,
    Hypothesis,
    NetworkFault,
    NetworkSignals,
    OfficeNeed,
    OfficePreflight,
    OfficeRoute,
    OfficeRouteResult,
    OfflineReport,
    PermissionDecision,
    PermissionScope,
    PrintStage,
    ResolverRole,
    SignSubmitStage,
)
from namios_pra.device_hub import can_copy, function_status, is_supported, untested_message
from namios_pra.doctor import (
    app_workflow_status,
    bounded_hypotheses,
    diagnose_device,
    diagnose_network,
    next_after_attempts,
    office_preflight,
)
from namios_pra.dotnet_classify import WINDOWS_ONLY_KINDS, classify_dotnet
from namios_pra.office_route import fidelity_gate, is_fidelity_blocked, resolve_office_route
from namios_pra.progress import (
    print_label,
    print_received,
    print_stage_from_cups,
    sign_label,
    sign_submitted_done,
)
from namios_pra.support import (
    advance,
    make_checklist,
    offline_capabilities,
    request_permission,
    visible_steps,
)

__all__ = [
    "PRA_SCHEMA_VERSION",
    "PraErrorCode",
    # types
    "DeviceFunction",
    "DeviceCapability",
    "DeviceFunctionStatus",
    "OfficeNeed",
    "OfficeRoute",
    "OfficeRouteResult",
    "FidelitySeverity",
    "FidelityIssue",
    "DotnetKind",
    "DotnetRoute",
    "DotnetClassification",
    "PrintStage",
    "SignSubmitStage",
    # Doctor-taxonomy types (PRA-028..035)
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
    # device hub (PRA-001)
    "function_status",
    "is_supported",
    "can_copy",
    "untested_message",
    # office (PRA-016/017)
    "resolve_office_route",
    "fidelity_gate",
    "is_fidelity_blocked",
    # dotnet (PRA-022/023)
    "classify_dotnet",
    "WINDOWS_ONLY_KINDS",
    # progress (PRA-032)
    "print_stage_from_cups",
    "print_label",
    "print_received",
    "sign_label",
    "sign_submitted_done",
    # Doctor (PRA-028..031)
    "diagnose_device",
    "diagnose_network",
    "office_preflight",
    "bounded_hypotheses",
    "app_workflow_status",
    "next_after_attempts",
    # support UX (PRA-033..035)
    "make_checklist",
    "visible_steps",
    "advance",
    "request_permission",
    "offline_capabilities",
]
