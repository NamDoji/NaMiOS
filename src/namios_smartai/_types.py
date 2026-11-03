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
