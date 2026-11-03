"""SAI-003/038 — máy trạng thái: trung thực, trạng thái từ KẾT QUẢ TOOL."""

from __future__ import annotations

from namios_smartai._types import TaskStatus as S
from namios_smartai._types import ToolResult, ToolResultStatus
from namios_smartai.state_machine import apply_tool_result, is_terminal, validate_transition


def test_valid_and_invalid_transitions() -> None:
    assert not validate_transition(S.PROPOSED, S.PREFLIGHTING)  # hợp lệ
    assert validate_transition(S.PROPOSED, S.COMPLETED)  # không được nhảy thẳng
    assert not validate_transition(S.VERIFYING, S.COMPLETED)  # completed chỉ từ verifying
    assert not validate_transition(S.PREFLIGHTING, S.APPLYING)  # pha linh hoạt
    assert validate_transition(S.PREFLIGHTING, S.COMPLETED)  # vẫn cấm nhảy hoàn tất


def test_terminal_has_no_exit() -> None:
    for term in (S.COMPLETED, S.PARTIAL, S.ROLLED_BACK, S.FAILED):
        assert is_terminal(term)
        assert validate_transition(term, S.TESTING)  # mọi lối ra đều lỗi
    assert validate_transition(S.COMPLETED, S.COMPLETED) == []  # no-op hợp lệ


def test_apply_tool_result_is_honest() -> None:
    # Tool FAILED → FAILED, bất kể "đích thành công" là COMPLETED.
    assert (
        apply_tool_result(S.VERIFYING, S.COMPLETED, ToolResult(ToolResultStatus.FAILED)) == S.FAILED
    )
    assert (
        apply_tool_result(S.APPLYING, S.VERIFYING, ToolResult(ToolResultStatus.BLOCKED))
        == S.BLOCKED
    )
    assert (
        apply_tool_result(S.TESTING, S.VERIFYING, ToolResult(ToolResultStatus.PARTIAL)) == S.PARTIAL
    )
    # SUCCESS → đích (chuyển hợp lệ).
    assert (
        apply_tool_result(S.VERIFYING, S.COMPLETED, ToolResult(ToolResultStatus.SUCCESS))
        == S.COMPLETED
    )


def test_apply_success_invalid_transition_stays_safe() -> None:
    # SUCCESS nhưng đích không phải chuyển hợp lệ (vd từ terminal) → PARTIAL an toàn,
    # KHÔNG tự nhảy bừa.
    assert (
        apply_tool_result(S.COMPLETED, S.TESTING, ToolResult(ToolResultStatus.SUCCESS)) == S.PARTIAL
    )
