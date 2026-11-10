"""NaMiOS — SmartAI, trung tâm điều phối công việc & tương thích (Phụ lục 04).

M0 = KHUNG AN TOÀN tất định (build + test được ngay, fake model provider cho
determinism). Người dùng tả việc bằng tiếng Việt → intent có cấu trúc → plan
hữu hình → policy/consent gate → typed tool broker → trạng thái cập nhật TỪ
kết quả tool (không từ văn bản AI).

Bất biến: AI ĐỀ XUẤT/THỬ nhưng KHÔNG tự kết luận tương thích; policy-as-code +
evidence + người nghiệp vụ mới quyết. Không root shell cho AI; không chạy lệnh
từ log/web/tài liệu (SAI-019); không tự ký/nộp/thanh toán (R4 cần xác nhận
giao dịch). Pilot thật (vendor/thiết bị/portal) = Giai đoạn M3/M4 BLOCKED.

Package tự được ``[tool.setuptools.packages.find] where=["src"]`` nhận diện.
"""

from __future__ import annotations

from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import (
    RISK_ORDER,
    TERMINAL_STATUSES,
    CapabilityToken,
    Capsule,
    CompatibilityRecipe,
    ConsentRecord,
    DependencyGraph,
    DepKind,
    DepNode,
    Diagnosis,
    ErrorCategory,
    Feedback,
    FeedbackVerdict,
    IntentResult,
    KbAnswer,
    KbEntry,
    MemoryScope,
    NodeStatus,
    PlanStep,
    PolicyContext,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
    Principal,
    Provenance,
    RecipeState,
    RegressionKey,
    RepairBudget,
    RepairOutcome,
    ReporterRole,
    RiskTier,
    SubmissionRecord,
    SubmissionStatus,
    SwitchTarget,
    SystemInventory,
    Task,
    TaskStatus,
    TestCaseSuggestion,
    TestedLevel,
    ToolCall,
    ToolResult,
    ToolResultStatus,
    ToolSpec,
    TraceErrorClass,
    TraceEvent,
    TriageInput,
    TriageResult,
    Trial,
    TrialStopReason,
    TrustEvidence,
    UnitPolicy,
    VendorPack,
)
from namios_smartai.adapters import (
    ADAPTER_TOOLS,
    ADAPTERS_BY_NAME,
    READONLY_ADAPTERS,
    ReadOnlyAdapter,
    build_adapter_registry,
    parse_bluetoothctl_show,
    parse_lpstat,
    parse_nmcli_devices,
    parse_rfkill,
    run_adapter,
)
from namios_smartai.admin import can_approve_r3_r4, can_edit_policy, can_read_logs
from namios_smartai.cli import PRIVILEGED_TOOLS, handle_request
from namios_smartai.capsule import apply_change, check_supply_chain, make_capsule, rollback
from namios_smartai.depgraph import build_graph, execute_blockers, is_execute_blocked
from namios_smartai.diagnose import diagnose
from namios_smartai.human_feedback import FeedbackLedger, can_certify_from_feedback
from namios_smartai.idempotency import (
    begin_submission,
    confirm,
    is_complete,
    mark_ambiguous,
    should_auto_resend,
)
from namios_smartai.injection import guard_untrusted, is_injection, scan_untrusted
from namios_smartai.intent import FakeModelProvider, ModelProvider, parse_intent
from namios_smartai.inventory import collect_inventory, inventory_from_declared
from namios_smartai.kill_switch import WILDCARD, KillSwitch
from namios_smartai.knowledge_base import KnowledgeBase, trust_rank
from namios_smartai.memory_scope import MemoryStore
from namios_smartai.observability import Trace, classify_error_source
from namios_smartai.orchestrator import run_plan, task_from_dict, task_to_dict
from namios_smartai.planner import build_task
from namios_smartai.policy import DEFAULT_RULES, evaluate
from namios_smartai.promotion import (
    evidence_expired,
    evidence_trusted,
    is_legitimately_published,
    promote,
)
from namios_smartai.recipe import arch_applies, new_candidate, validate_recipe_publishable
from namios_smartai.redaction import (
    is_shareable,
    redact_bundle,
    redact_text_full,
    residual_findings,
    scrub_all,
)
from namios_smartai.regression import apply_regression, changed_components
from namios_smartai.repair import HARD_STOPS, TrialExecutor, bounded_repair
from namios_smartai.route import select_route
from namios_smartai.state_machine import (
    VALID_TRANSITIONS,
    apply_tool_result,
    is_terminal,
    validate_transition,
)
from namios_smartai.tools import DEFAULT_TOOLS, ToolRegistry
from namios_smartai.triage import triage_error
from namios_smartai.vendorpack import build_vendor_pack, is_safe_to_share

__all__ = [
    # types / enums
    "TaskStatus",
    "TERMINAL_STATUSES",
    "RiskTier",
    "RISK_ORDER",
    "ToolResultStatus",
    "PolicyEffect",
    "SaiErrorCode",
    "CapabilityToken",
    "ConsentRecord",
    "ToolSpec",
    "ToolCall",
    "ToolResult",
    "PlanStep",
    "PolicyRule",
    "PolicyContext",
    "PolicyDecision",
    "IntentResult",
    "Task",
    # intent (SAI-001)
    "ModelProvider",
    "FakeModelProvider",
    "parse_intent",
    # planner (SAI-002)
    "build_task",
    # policy (SAI-039)
    "DEFAULT_RULES",
    "evaluate",
    # state machine (SAI-003/038)
    "VALID_TRANSITIONS",
    "validate_transition",
    "apply_tool_result",
    "is_terminal",
    # tools + injection (SAI-015/016/019/040)
    "DEFAULT_TOOLS",
    "ToolRegistry",
    "scan_untrusted",
    "is_injection",
    "guard_untrusted",
    # read-only OS adapters + thin broker CLI (ADR-0021, M4 backbone)
    "ReadOnlyAdapter",
    "READONLY_ADAPTERS",
    "ADAPTER_TOOLS",
    "ADAPTERS_BY_NAME",
    "build_adapter_registry",
    "run_adapter",
    "parse_nmcli_devices",
    "parse_lpstat",
    "parse_rfkill",
    "parse_bluetoothctl_show",
    "PRIVILEGED_TOOLS",
    "handle_request",
    # orchestrator (SAI-003/038)
    "run_plan",
    "task_to_dict",
    "task_from_dict",
    # M1 — chẩn đoán (SAI-006/007/008/009)
    "ErrorCategory",
    "NodeStatus",
    "DepKind",
    "SystemInventory",
    "DepNode",
    "DependencyGraph",
    "TriageInput",
    "TriageResult",
    "Diagnosis",
    "collect_inventory",
    "inventory_from_declared",
    "triage_error",
    "build_graph",
    "execute_blockers",
    "is_execute_blocked",
    "select_route",
    "diagnose",
    # M2 — tự sửa có giới hạn (SAI-010/011/012/018/033/041/042)
    "RecipeState",
    "TrialStopReason",
    "Capsule",
    "Trial",
    "RepairBudget",
    "RepairOutcome",
    "CompatibilityRecipe",
    "TrustEvidence",
    "RegressionKey",
    "make_capsule",
    "apply_change",
    "rollback",
    "check_supply_chain",
    "validate_recipe_publishable",
    "arch_applies",
    "new_candidate",
    "promote",
    "is_legitimately_published",
    "evidence_trusted",
    "evidence_expired",
    "bounded_repair",
    "TrialExecutor",
    "HARD_STOPS",
    "changed_components",
    "apply_regression",
    # M3/M4 — quản trị & kiểm soát an toàn (SAI-014/022/035/037)
    "SwitchTarget",
    "SubmissionStatus",
    "UnitPolicy",
    "Principal",
    "SubmissionRecord",
    "VendorPack",
    "KillSwitch",
    "WILDCARD",
    "can_edit_policy",
    "can_approve_r3_r4",
    "can_read_logs",
    "build_vendor_pack",
    "is_safe_to_share",
    "begin_submission",
    "mark_ambiguous",
    "confirm",
    "should_auto_resend",
    "is_complete",
    # Cross-cutting — an toàn dữ liệu / quan sát / cách ly (SAI-024/026/034)
    "MemoryScope",
    "TraceErrorClass",
    "TraceEvent",
    "redact_text_full",
    "scrub_all",
    "redact_bundle",
    "residual_findings",
    "is_shareable",
    "Trace",
    "classify_error_source",
    "MemoryStore",
    # Knowledge Base có nguồn (SAI-025)
    "Provenance",
    "TestedLevel",
    "KbEntry",
    "KbAnswer",
    "KnowledgeBase",
    "trust_rank",
    # Human Feedback (SAI-029)
    "FeedbackVerdict",
    "ReporterRole",
    "Feedback",
    "TestCaseSuggestion",
    "FeedbackLedger",
    "can_certify_from_feedback",
]
