"""NaMiOS — Phụ lục 10 (N10-001..060): lõi honest-core chương trình chuyển
đổi Windows → NaMiOS.

M0 = HỢP ĐỒNG trung thực + logic LÀM-ĐƯỢC-TẠI-CHỖ (dữ liệu/logic thuần, KHÔNG
cần thiết bị/pilot thật), TÁI DÙNG tầng dưới (``namios_odc``/``namios_pra``/
``namios_e08``/``namios_sys``), KHÔNG dựng hệ trạng thái thứ hai:

- Hợp đồng dữ liệu (``_types``/``schema``): ``AppManifest``/``DeviceManifest``/
  ``CompatibilityRecipe``/``WorkflowTest``/``EvidenceRecord``/
  ``MigrationInventory`` — recipe đổi hash/version tự ``needs_retest``
  (N10-026), vòng đời chứng nhận TÁI DÙNG ``namios_odc.device_cert``.
- Migration Assessor (``assessor``, N10-007): chỉ kiểm kê/preview; loại + đánh
  dấu mọi trường nhạy cảm (mật khẩu/cookie/khóa riêng); usage 30-ngày CHỈ giữ
  khi opt-in; nội dung thu thập được KHÔNG BAO GIỜ thành hành động (TÁI DÙNG
  ``namios_sys.data_authority``).
- Readiness score (``readiness``, N10-009): ``ready``/``ready_with_limits``/
  ``pilot_only``/``blocked``/``unknown`` — một công việc thiết yếu bị chặn →
  CẢ MÁY blocked.
- Compatibility Broker (``compat_broker``, N10-017): chọn tuyến THEO TÁC VỤ
  từ dependency graph (TÁI DÙNG ``namios_e08.depgraph``); "mở GUI được" ≠
  "tác vụ (vd ký số) đạt"; driver/token-chỉ-Windows KHÔNG BAO GIỜ route Wine.
- PE analyzer an toàn (``pe_analyzer``, N10-018): phân loại METADATA (struct
  input), KHÔNG chạy file; driver ``.sys`` KHÔNG BAO GIỜ bị gán app user-mode;
  thiếu bằng chứng → ``unknown``.
- Workflow verdict + evidence (``workflow_verdict``, N10-043): "đã xong" chỉ
  khi có bằng chứng ĐỘC LẬP hợp lệ; exit-code/spool một mình KHÔNG đủ.

Phần cần thiết bị/pilot/vendor THẬT (khảo sát 30-50 máy thật, ADR nền tảng,
Wine prefix thật, 20 fixture PE từ binary thật, pilot 3 nhóm người dùng…) =
BLOCKED — xem ``docs/specs/PHU-LUC-10-N10-MAPPING.md``.
"""

from __future__ import annotations

from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_mig._errors import MigErrorCode
from namios_mig._types import (
    MIG_SCHEMA_VERSION,
    AppManifest,
    CertState,
    CompatibilityRecipe,
    CompatRoute,
    DeviceFunction,
    DeviceManifest,
    DotnetKind,
    EvidenceRecord,
    MigrationInventory,
    PeripheralKind,
    PrintStage,
    SignSubmitStage,
    WorkflowTest,
    WorkflowTestStatus,
)
from namios_mig.assessor import (
    SECRET_FIELD_MARKERS,
    AssessmentResult,
    assess_machine,
    assessment_instruction_authorized,
    migrate_app_data,
)
from namios_mig.compat_broker import (
    DepKind,
    DepNode,
    DepState,
    TaskRouteResult,
    WorkflowVerdict,
    assess_dependency_verdict,
    office_document_route,
    office_task_route,
    proposed_action_is_safe,
    resolve_task_route,
)
from namios_mig.pe_analyzer import (
    PeAnalysisResult,
    PeClassification,
    PeMetadataInput,
    PeSubsystem,
    classify_pe,
)
from namios_mig.readiness import (
    AppReadinessInput,
    MachineReadiness,
    ReadinessLevel,
    compute_machine_readiness,
    is_device_requirement_met,
)
from namios_mig.schema import (
    promote_recipe,
    publish_recipe,
    recipe_needs_retest,
    validate_app_manifest,
    validate_device_manifest,
    validate_evidence_record,
    validate_inventory,
    validate_recipe,
    validate_workflow_test,
)
from namios_mig.workflow_verdict import (
    EvidenceOutcome,
    assess_workflow,
    evaluate_workflow,
    evidence_outcome,
    terminal_diagnosis_if_exhausted,
)
from namios_odc import EvidenceKind

__all__ = [
    "MIG_SCHEMA_VERSION",
    "MigErrorCode",
    # contracts (_types.py)
    "AppManifest",
    "DeviceManifest",
    "PeripheralKind",
    "CompatibilityRecipe",
    "CompatRoute",
    "WorkflowTest",
    "WorkflowTestStatus",
    "EvidenceRecord",
    "MigrationInventory",
    "CertState",
    "EvidenceKind",
    "DeviceFunction",
    "DotnetKind",
    "PrintStage",
    "SignSubmitStage",
    # schema.py — validator + recipe lifecycle (N10-007/012/019/026/043)
    "validate_app_manifest",
    "validate_device_manifest",
    "validate_recipe",
    "validate_workflow_test",
    "validate_evidence_record",
    "validate_inventory",
    "recipe_needs_retest",
    "promote_recipe",
    "publish_recipe",
    # assessor.py (N10-007/012/014)
    "SECRET_FIELD_MARKERS",
    "AssessmentResult",
    "assess_machine",
    "assessment_instruction_authorized",
    "migrate_app_data",
    # readiness.py (N10-009)
    "ReadinessLevel",
    "AppReadinessInput",
    "MachineReadiness",
    "is_device_requirement_met",
    "compute_machine_readiness",
    # compat_broker.py (N10-017/023/027)
    "TaskRouteResult",
    "resolve_task_route",
    "office_task_route",
    "office_document_route",
    "proposed_action_is_safe",
    "assess_dependency_verdict",
    "WorkflowVerdict",
    "DepKind",
    "DepNode",
    "DepState",
    # pe_analyzer.py (N10-018)
    "PeSubsystem",
    "PeClassification",
    "PeMetadataInput",
    "PeAnalysisResult",
    "classify_pe",
    # workflow_verdict.py (N10-043/060)
    "EvidenceOutcome",
    "evidence_outcome",
    "evaluate_workflow",
    "assess_workflow",
    "terminal_diagnosis_if_exhausted",
]
