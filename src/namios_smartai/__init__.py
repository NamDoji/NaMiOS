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
    ConsentRecord,
    IntentResult,
    PlanStep,
    PolicyContext,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
    RiskTier,
    Task,
    TaskStatus,
    ToolCall,
    ToolResult,
    ToolResultStatus,
    ToolSpec,
)
from namios_smartai.injection import guard_untrusted, is_injection, scan_untrusted
from namios_smartai.intent import FakeModelProvider, ModelProvider, parse_intent
from namios_smartai.orchestrator import run_plan, task_from_dict, task_to_dict
from namios_smartai.planner import build_task
from namios_smartai.policy import DEFAULT_RULES, evaluate
from namios_smartai.state_machine import (
    VALID_TRANSITIONS,
    apply_tool_result,
    is_terminal,
    validate_transition,
)
from namios_smartai.tools import DEFAULT_TOOLS, ToolRegistry

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
    # orchestrator (SAI-003/038)
    "run_plan",
    "task_to_dict",
    "task_from_dict",
]
