"""Hợp đồng dữ liệu DÙNG CHUNG của SmartAI M0 (Phụ lục 04).

Đóng băng mọi enum + dataclass để các module con (intent, planner, tools,
policy, orchestrator, CLI) và test tham chiếu MỘT nguồn sự thật.

Nguyên tắc nền (SAI §1/§2/§8): LỜI AI ≠ SỰ THẬT. Trạng thái task chỉ được
cập nhật từ KẾT QUẢ TOOL (``ToolResult``), không từ văn bản mô hình. Policy/
consent/tool-contract là MÃ QUYẾT ĐỊNH ĐƯỢC (deterministic), không phụ thuộc
suy đoán mô hình. AI chỉ phát ra ACTION CÓ CẤU TRÚC (``ToolCall``) — không có
root shell, không chạy lệnh từ log/web/tài liệu.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "TaskStatus",
    "TERMINAL_STATUSES",
    "RiskTier",
    "RISK_ORDER",
    "ToolResultStatus",
    "PolicyEffect",
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
    # M1 — chẩn đoán (SAI-006/007/009)
    "ErrorCategory",
    "NodeStatus",
    "DepKind",
    "SystemInventory",
    "DepNode",
    "DependencyGraph",
    "TriageInput",
    "TriageResult",
    "Diagnosis",
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
]


class TaskStatus(str, Enum):
    """12 trạng thái task (SAI-003). Orchestrator cập nhật từ tool result,
    KHÔNG từ văn bản AI. Giá trị chuỗi là hợp đồng ổn định."""

    PROPOSED = "proposed"
    AWAITING_INPUT = "awaiting_input"
    AWAITING_CONSENT = "awaiting_consent"
    PREFLIGHTING = "preflighting"
    TESTING = "testing"
    APPLYING = "applying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


#: Trạng thái cuối — không chuyển tiếp (trừ mở task mới).
TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset(
    {
        TaskStatus.COMPLETED,
        TaskStatus.PARTIAL,
        TaskStatus.ROLLED_BACK,
        TaskStatus.FAILED,
    }
)


class RiskTier(str, Enum):
    """Bậc rủi ro hành động (SAI-017).

    - R0: phân tích metadata + tra catalog (không tác động).
    - R1: thử read-only / sandbox cô lập.
    - R2: ghi cấu hình capsule / cài app trong môi trường được cấp (cần consent phạm vi).
    - R3: đổi OS/quyền thiết bị/dữ liệu thật/chuyển remote (cần xác nhận cụ thể / admin).
    - R4: ký/nộp/phát hành hóa đơn/thanh toán/giao dịch KHÔNG HOÀN TÁC (cần xác
      nhận GIAO DỊCH với nội dung + chủ thể; "cứ làm đi" KHÔNG thay thế được).
    """

    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


#: Thứ hạng để so sánh mức rủi ro (R4 cao nhất).
RISK_ORDER: dict[RiskTier, int] = {
    RiskTier.R0: 0,
    RiskTier.R1: 1,
    RiskTier.R2: 2,
    RiskTier.R3: 3,
    RiskTier.R4: 4,
}


class ToolResultStatus(str, Enum):
    """Kết quả một tool (SAI-040). Đây là SỰ THẬT để orchestrator cập nhật
    trạng thái — không dùng text của tool làm lệnh điều khiển."""

    SUCCESS = "success"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class CapabilityToken:
    """Quyền theo tác vụ, có phạm vi (SAI-016). KHÔNG wildcard toàn ổ, KHÔNG
    token mặc định cho sudo. Có thể thu hồi / một-lần / hết hạn."""

    token_id: str
    subject: str  # app/capsule id token gắn vào
    paths: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()
    risk_tier: RiskTier = RiskTier.R0
    granted_by: str | None = None
    expires_at: str | None = None  # ISO-8601
    one_time: bool = False
    used: bool = False
    revoked: bool = False


@dataclass(frozen=True)
class ConsentRecord:
    """Sự chấp thuận người dùng cho một phạm vi (SAI-017). ``transaction_confirmed``
    = xác nhận GIAO DỊCH cụ thể cho R4. ``target_fingerprint`` buộc consent vào
    một mục tiêu — đổi mục tiêu làm consent cũ vô hiệu."""

    scope: tuple[str, ...] = ()
    granted_by: str | None = None
    expires_at: str | None = None
    transaction_confirmed: bool = False
    target_fingerprint: str = ""


@dataclass(frozen=True)
class ToolSpec:
    """Khai báo một tool có kiểu (SAI-015/040). Tool Broker chỉ gọi tool đã
    đăng ký, validate tham số + phạm vi, fail-closed."""

    name: str
    risk: RiskTier
    required_params: tuple[str, ...] = ()
    writes: bool = False
    network_scope: str = "none"  # none | official_only | lab
    filesystem_scope: str = "none"  # none | capsule | granted_paths
    device_scope: str = "none"
    retry_safe: bool = False
    rollback_class: str = "none"  # none | snapshot | reversible


@dataclass(frozen=True)
class ToolCall:
    """Action CÓ CẤU TRÚC do AI đề xuất (SAI-019: chỉ dạng này mới tới Broker)."""

    tool: str
    params: Mapping[str, Any] = field(default_factory=dict)
    target: str = ""
    risk: RiskTier = RiskTier.R0


@dataclass(frozen=True)
class ToolResult:
    """Kết quả tool — SỰ THẬT (SAI-030/040)."""

    status: ToolResultStatus
    message_vi: str = ""
    error_code: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)
    evidence_id: str | None = None


@dataclass(frozen=True)
class PlanStep:
    """Một bước trong Task Plan hữu hình (SAI-002)."""

    step_id: str
    tool: str
    risk: RiskTier
    expected_vi: str
    status: TaskStatus = TaskStatus.PROPOSED
    consent_required: bool = False


@dataclass(frozen=True)
class PolicyRule:
    """Luật allow/deny dạng DỮ LIỆU (SAI-039) — tách khỏi prompt, version hoá,
    test được. ``when`` là tiêu chí khớp (action/risk/stage/target_glob…)."""

    rule_id: str
    effect: PolicyEffect
    when: Mapping[str, Any] = field(default_factory=dict)
    reason_key: str = ""


@dataclass(frozen=True)
class PolicyContext:
    """Ngữ cảnh để policy engine quyết (SAI-039)."""

    action: str
    risk: RiskTier
    target: str = ""
    capability: CapabilityToken | None = None
    consent: ConsentRecord | None = None
    org_policy: str = "default"
    workflow_stage: str = "proposed"
    now: str | None = None


@dataclass(frozen=True)
class PolicyDecision:
    effect: PolicyEffect
    reason_vi: str
    rule_id: str


@dataclass(frozen=True)
class IntentResult:
    """Kết quả ánh xạ ý định tiếng Việt → cấu trúc (SAI-001). ``confidence``
    0..1; ``unknowns`` liệt kê thông tin còn thiếu (AI phải HỎI, không tự đoán
    người nộp/khoản tiền)."""

    intent: str
    target_app: str | None = None
    target_data: str | None = None
    required_outcome: str | None = None
    constraints: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True)
class Task:
    """Trạng thái task bền (SAI-038). Tách trạng thái AI-text với tool-state:
    ``status`` ở đây chỉ đổi qua orchestrator từ ToolResult."""

    task_id: str
    intent: str
    status: TaskStatus = TaskStatus.PROPOSED
    workflow_id: str | None = None
    app_id: str | None = None
    app_version: str | None = None
    steps: tuple[PlanStep, ...] = ()
    consent: ConsentRecord | None = None
    evidence_ids: tuple[str, ...] = ()
    route_mode: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None


# --- M1 — Chẩn đoán & tìm đường (SAI-006/007/008/009) ------------------------


class ErrorCategory(str, Enum):
    """Phân loại lỗi tất định (SAI-009). Nhãn từ DẤU HIỆU quan sát được, KHÔNG
    đoán; không chắc → ``unknown`` (không bịa nguyên nhân)."""

    MISSING_RUNTIME = "missing_runtime"
    UNSUPPORTED_API = "unsupported_api"
    DB_UNREACHABLE = "db_unreachable"
    DEVICE_MISSING = "device_missing"
    PORTAL_PLUGIN = "portal_plugin"
    LICENSE = "license"
    DATA_MISMATCH = "data_mismatch"
    UNKNOWN = "unknown"


class NodeStatus(str, Enum):
    """Mức quan sát của một node phụ thuộc (SAI-007)."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class DepKind(str, Enum):
    """Loại node trong dependency graph (SAI-007): installer → runtime →
    COM/service/DB/browser → thiết bị/token → tài liệu → portal."""

    INSTALLER = "installer"
    RUNTIME = "runtime"
    COM_SERVICE = "com_service"
    DATABASE = "database"
    BROWSER = "browser"
    DEVICE = "device"
    TOKEN = "token"
    DOCUMENT = "document"
    PORTAL = "portal"


@dataclass(frozen=True)
class SystemInventory:
    """Inventory theo quyền (SAI-006): CHỈ metadata, KHÔNG đọc nội dung tài
    liệu/toàn bộ home. ``read_fields`` = danh sách trường ĐÃ đọc (xem được —
    minh bạch); ``out_of_scope`` = thứ bị từ chối đọc (vd thư mục cá nhân)."""

    os: str = "unknown"
    cpu_arch: str = "unknown"
    kernel: str | None = None
    browser: str | None = None
    app_id: str | None = None
    app_version: str | None = None
    runtime: str | None = None
    devices: tuple[str, ...] = ()
    printers: tuple[str, ...] = ()
    tokens: tuple[str, ...] = ()
    network_ports: tuple[str, ...] = ()
    read_fields: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()


@dataclass(frozen=True)
class DepNode:
    """Một node phụ thuộc (SAI-007). ``required`` + (``status`` chưa observed
    hoặc có ``blocker``) → chặn bước execute (không coi là hoàn thành)."""

    node_id: str
    kind: DepKind
    status: NodeStatus = NodeStatus.UNKNOWN
    source: str = ""
    blocker: str | None = None
    required: bool = False


@dataclass(frozen=True)
class DependencyGraph:
    workflow_id: str
    nodes: tuple[DepNode, ...] = ()


@dataclass(frozen=True)
class TriageInput:
    """Ngữ cảnh lỗi THÔ (có thể chứa PII/secret) — PHẢI redact TRƯỚC khi phân
    loại/đưa vào model (SAI-009/023)."""

    exit_code: int | None = None
    log_text: str = ""
    crash_signature: str = ""
    app_version: str = ""
    device: str = ""
    step: str = ""


@dataclass(frozen=True)
class TriageResult:
    """Kết quả phân loại lỗi (SAI-009). ``redacted_log`` đã lọc PII/secret —
    là bản DUY NHẤT được phép ghi log/đưa model."""

    category: ErrorCategory
    confidence: float
    evidence_vi: tuple[str, ...]
    redacted_log: str
    source: str = ""


@dataclass(frozen=True)
class Diagnosis:
    """Kết luận chẩn đoán tổng hợp (SAI-006/007/008/009). Trung thực: nêu
    blocker, không tự nhận 'đã sửa'/'tương thích'."""

    workflow_id: str
    triage: TriageResult | None = None
    execute_blocked: bool = False
    depgraph_blockers: tuple[str, ...] = ()
    route_recommended: str | None = None
    route_no_verified: bool = True
    inventory_read_fields: tuple[str, ...] = ()
    findings_vi: tuple[str, ...] = ()
    suggested_action_vi: str = ""
    blockers: tuple[str, ...] = ()


# --- M2 — Tự sửa có giới hạn (SAI-010/011/012/018/020/031/032/033/041/042) ---


class RecipeState(str, Enum):
    """Vòng đời công thức tương thích (SAI-012). AI đề xuất mặc định
    ``experimental``; chỉ validator + người thẩm quyền mới nâng; không có
    evidence → không thể ``published``; thu hồi/needs_retest là trạng thái an
    toàn khi thành phần đổi (SAI-033/035)."""

    DRAFT = "draft"
    EXPERIMENTAL = "experimental"
    LAB_PASSED = "lab_passed"
    PILOT_VERIFIED = "pilot_verified"
    PUBLISHED = "published"
    NEEDS_RETEST = "needs_retest"
    REVOKED = "revoked"


class TrialStopReason(str, Enum):
    """Lý do DỪNG tìm-kiếm-sửa có giới hạn (SAI-010). Dừng cứng khi: dữ liệu
    sai, thiếu license, lỗi bảo mật, cần vendor; hoặc hết ngân sách; hoặc mọi
    ứng viên fail. KHÔNG retry vô hạn."""

    NONE = "none"
    SUCCESS = "success"
    DATA_WRONG = "data_wrong"
    MISSING_LICENSE = "missing_license"
    SECURITY = "security"
    NEEDS_VENDOR = "needs_vendor"
    BUDGET_EXCEEDED = "budget_exceeded"
    ALL_CANDIDATES_FAILED = "all_candidates_failed"


@dataclass(frozen=True)
class Capsule:
    """Bản sao capsule để THỬ (SAI-018). Mọi thay đổi runtime/registry/prefix
    diễn ra trên BẢN SAO có snapshot — KHÔNG đụng bản gốc, KHÔNG mount home/DB
    thật. ``mutations`` ghi lại thay đổi (đo được); ``rolled_back`` cho biết đã
    hoàn nguyên. Frozen: thao tác trả Capsule MỚI, bản gốc bất biến."""

    capsule_id: str
    base_id: str
    snapshot_id: str
    mutations: tuple[str, ...] = ()
    rolled_back: bool = False


@dataclass(frozen=True)
class Trial:
    """Một phép thử sửa (SAI-010): ĐÚNG MỘT thay đổi đo được + điều kiện trước
    + kỳ vọng + đo + rollback. ``outcome`` từ bộ thực thi (mock/sandbox), KHÔNG
    từ lời AI."""

    trial_id: str
    hypothesis: str
    precondition: str
    change: str
    expected: str
    measured: str
    outcome: ToolResultStatus
    rolled_back: bool = True


@dataclass(frozen=True)
class RepairBudget:
    """Giới hạn tìm-kiếm-sửa (SAI-010/028): số phép thử + bước (đại diện thời
    gian/tài nguyên, tất định để test)."""

    max_trials: int = 3
    max_steps: int = 50


@dataclass(frozen=True)
class RepairOutcome:
    """Kết quả bounded repair (SAI-010). ``recipe_candidate`` chỉ có khi một
    phép thử THÀNH CÔNG — mặc định trạng thái ``experimental``, chưa published."""

    status: ToolResultStatus
    stop_reason: TrialStopReason
    trials: tuple[Trial, ...]
    recipe_candidate: CompatibilityRecipe | None = None
    reason_vi: str = ""


@dataclass(frozen=True)
class CompatibilityRecipe:
    """Công thức tương thích (SAI-041). ``rollback`` BẮT BUỘC cho recipe đổi hệ
    thống; ``source_url``+``app_hash`` bắt buộc để publish; recipe x86 KHÔNG tự
    áp cho x64. ``state`` do promotion gate quản (mặc định experimental)."""

    recipe_id: str
    publisher: str
    source_url: str
    app_id: str
    app_version: str
    app_hash: str
    architecture: str
    runner: str
    runtime: str
    preconditions: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    expected_outputs: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    license_notes: str = ""
    reviewers: tuple[str, ...] = ()
    verified_scope: str = ""
    retest_on: tuple[str, ...] = ()
    rollback: str | None = None
    signature: str | None = None
    changes_system: bool = True
    state: RecipeState = RecipeState.EXPERIMENTAL


@dataclass(frozen=True)
class TrustEvidence:
    """Evidence có provenance (SAI-042). Nguồn ngoài chỉ là tham khảo; badge
    KHÔNG chấp nhận AI tự đánh giá. Ngày quá hạn / nguồn giả → needs_retest,
    không tạo pass."""

    origin: str  # tool | vendor | user
    timestamp: str
    version: str
    fixture_hash: str
    test_result: str  # pass | fail | not_run
    reviewer: str | None = None
    valid_until: str | None = None


@dataclass(frozen=True)
class RegressionKey:
    """Khóa ma trận hồi quy (SAI-033). Đổi BẤT KỲ thành phần nào → workflow
    liên quan chuyển ``needs_retest`` trước khi stable."""

    os_build: str = "unresolved"
    model_version: str = "unresolved"
    planner_version: str = "unresolved"
    tool_schema: str = "unresolved"
    recipe_id: str = "unresolved"
    wine_runtime: str = "unresolved"
    app_version: str = "unresolved"
    device: str = "unresolved"
    workflow_id: str = "unresolved"
