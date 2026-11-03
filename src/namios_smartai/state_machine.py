"""Máy trạng thái task SmartAI (SAI-003/038).

Bất biến trung thực: trạng thái chỉ đổi qua ``apply_tool_result`` (từ
``ToolResult`` — SỰ THẬT) hoặc các chuyển hợp lệ do orchestrator điều khiển.
Mô hình viết "đã xong" khi tool FAILED vẫn ra ``FAILED`` — văn bản AI KHÔNG
nâng được trạng thái (SAI-003 nghiệm thu)."""

from __future__ import annotations

from namios_core.validation import ValidationError
from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import TERMINAL_STATUSES, TaskStatus, ToolResult, ToolResultStatus

__all__ = [
    "VALID_TRANSITIONS",
    "is_terminal",
    "validate_transition",
    "apply_tool_result",
]

S = TaskStatus

#: Chuyển trạng thái hợp lệ (SAI-003).
#:
#: Bất biến an toàn (thứ tự PHA hoạt động KHÔNG phải bất biến — quy trình cài
#: có thể preflight→apply(cài)→test→verify, khác workflow khác):
#:  - Trạng thái CUỐI (COMPLETED/PARTIAL/ROLLED_BACK/FAILED) không có lối ra.
#:  - ``COMPLETED`` CHỈ tới được từ ``VERIFYING`` (không tự nhảy hoàn tất).
#:  - Các pha hoạt động (preflighting/testing/applying/verifying) chuyển linh
#:    hoạt qua nhau + tới chờ-consent/terminal.
_ACTIVE_FORWARD = frozenset(
    {
        S.TESTING,
        S.APPLYING,
        S.VERIFYING,
        S.AWAITING_CONSENT,
        S.PARTIAL,
        S.BLOCKED,
        S.FAILED,
        S.ROLLED_BACK,
    }
)
VALID_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    S.PROPOSED: frozenset(
        {S.AWAITING_INPUT, S.AWAITING_CONSENT, S.PREFLIGHTING, S.TESTING, S.BLOCKED, S.FAILED}
    ),
    S.AWAITING_INPUT: frozenset(
        {S.PROPOSED, S.AWAITING_CONSENT, S.PREFLIGHTING, S.BLOCKED, S.FAILED}
    ),
    S.AWAITING_CONSENT: frozenset(
        {S.PREFLIGHTING, S.TESTING, S.APPLYING, S.VERIFYING, S.BLOCKED, S.FAILED}
    ),
    S.PREFLIGHTING: _ACTIVE_FORWARD,
    S.TESTING: _ACTIVE_FORWARD,
    S.APPLYING: _ACTIVE_FORWARD,
    S.VERIFYING: _ACTIVE_FORWARD | frozenset({S.COMPLETED}),
    S.COMPLETED: frozenset(),
    S.PARTIAL: frozenset(),
    S.ROLLED_BACK: frozenset(),
    S.FAILED: frozenset(),
}


def is_terminal(status: TaskStatus) -> bool:
    return status in TERMINAL_STATUSES


def validate_transition(frm: TaskStatus, to: TaskStatus) -> list[ValidationError]:
    """Trả danh sách lỗi nếu chuyển ``frm → to`` không hợp lệ (rỗng = hợp lệ).
    ``frm == to`` luôn hợp lệ (no-op)."""

    if frm == to:
        return []
    if is_terminal(frm):
        return [
            ValidationError(
                code=SaiErrorCode.E_SAI_STATE_TRANSITION.value,
                path="status",
                message_vi=t("sai.state.error.from_terminal", lang=Lang.VI, frm=frm.value),
            )
        ]
    if to not in VALID_TRANSITIONS.get(frm, frozenset()):
        return [
            ValidationError(
                code=SaiErrorCode.E_SAI_STATE_TRANSITION.value,
                path="status",
                message_vi=t(
                    "sai.state.error.invalid_transition",
                    lang=Lang.VI,
                    frm=frm.value,
                    to=to.value,
                ),
            )
        ]
    return []


def apply_tool_result(
    current: TaskStatus, on_success: TaskStatus, result: ToolResult
) -> TaskStatus:
    """Cập nhật trạng thái TỪ KẾT QUẢ TOOL (SAI-003 — không từ văn bản AI).

    - ``FAILED``  → ``FAILED``
    - ``BLOCKED`` → ``BLOCKED``
    - ``PARTIAL`` → ``PARTIAL``
    - ``SUCCESS`` → ``on_success`` (phải là chuyển hợp lệ từ ``current``; nếu
      không hợp lệ, giữ an toàn ở ``PARTIAL`` thay vì tự nhảy bừa).

    Không bao giờ trả ``COMPLETED`` khi tool không ``SUCCESS``."""

    if result.status == ToolResultStatus.FAILED:
        return TaskStatus.FAILED
    if result.status == ToolResultStatus.BLOCKED:
        return TaskStatus.BLOCKED
    if result.status == ToolResultStatus.PARTIAL:
        return TaskStatus.PARTIAL
    # SUCCESS
    if validate_transition(current, on_success):
        return TaskStatus.PARTIAL
    return on_success
