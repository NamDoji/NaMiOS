"""NaMiOS — Phụ lục 07 (ODC-001..048): Office tích hợp sẵn + chứng nhận thiết bị.

O0 = HỢP ĐỒNG trung thực engine-agnostic, TÁI DÙNG tầng dưới (namios_pra/sys/smartai),
KHÔNG fork: Document Broker (mở≠sửa≠in≠macro; nội dung tài liệu không cấp quyền/không
tự upload) + Office Route Matrix 6-mode + tách vòng đời/recheck (đổi 1 thành phần chỉ
kiểm lại vùng ảnh hưởng) + chứng nhận thiết bị per-function (state machine; cộng đồng/
AI không nâng) + chỉ-số trung thực (catalog ≠ đã-hỗ-trợ).

Chọn engine thật (ODC-002, ADR 0013) + đo fidelity/thiết bị/pilot THẬT (O1–O4) = BLOCKED.
"""

from __future__ import annotations

from namios_odc import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_odc._errors import OdcErrorCode
from namios_odc._types import (
    ODC_SCHEMA_VERSION,
    CertFunction,
    CertState,
    Component,
    CoverageMetrics,
    DeviceCert,
    DocFormat,
    DocRouteResult,
    DocSensitivity,
    DocumentMetadata,
    EvidenceKind,
    LifecycleRing,
    OfficeMode,
    OfficeNeed,
    PackageRelease,
)
from namios_odc.device_cert import (
    PROMOTING_EVIDENCE,
    advance,
    can_publish,
    function_state,
    is_function_supported,
    publish,
    with_needs_retest,
)
from namios_odc.document_broker import (
    document_instruction_authorized,
    explain_routes,
    inspect_document,
    may_auto_upload,
    open_as_copy,
    verify_save,
)
from namios_odc.lifecycle import (
    RECHECK_MAP,
    WorkflowDomain,
    can_rollback,
    needs_retest_domains,
    office_failure_blocks_os,
)
from namios_odc.metrics import (
    build_coverage,
    published_model_count,
    safe_fraction,
    user_weighted_coverage,
)
from namios_odc.route_matrix import needs_macro, resolve_document_route

__all__ = [
    "ODC_SCHEMA_VERSION",
    "OdcErrorCode",
    # types
    "OfficeMode",
    "DocRouteResult",
    "DocFormat",
    "DocSensitivity",
    "DocumentMetadata",
    "Component",
    "LifecycleRing",
    "PackageRelease",
    "CertFunction",
    "CertState",
    "EvidenceKind",
    "DeviceCert",
    "CoverageMetrics",
    "OfficeNeed",
    "WorkflowDomain",
    # route matrix (ODC-008)
    "resolve_document_route",
    "needs_macro",
    # document broker (ODC-007)
    "inspect_document",
    "explain_routes",
    "open_as_copy",
    "may_auto_upload",
    "document_instruction_authorized",
    "verify_save",
    # lifecycle (ODC-001/020/033)
    "can_rollback",
    "office_failure_blocks_os",
    "needs_retest_domains",
    "RECHECK_MAP",
    # device cert (ODC-022/047)
    "function_state",
    "advance",
    "can_publish",
    "publish",
    "is_function_supported",
    "with_needs_retest",
    "PROMOTING_EVIDENCE",
    # metrics (ODC-048)
    "safe_fraction",
    "user_weighted_coverage",
    "published_model_count",
    "build_coverage",
]
