"""ECO-001 — GATE đối kháng 7 nấc:
1. Web app bị gán ``acquire.method=downloaded_binary`` -> phải bị chặn.
2. "Bước ký" (ở đây đại diện bằng nấc ``authenticate`` — nấc gần nhất với
   hành vi "ký/xác thực" trong mô hình 7 nấc hiện tại, vì model KHÔNG có
   tên nấc "ký" riêng) bị XOÁ khỏi danh sách (thay vì ghi
   ``not_applicable``) -> phải bị chặn cấu trúc, không có cách nào tạo
   được ``WorkflowResult`` thiếu nấc.
3. Không chỉ 1 nấc bị xoá — thử xoá TỪNG nấc một trong 7 nấc để xác nhận
   bất biến giữ đủ không phụ thuộc vị trí.
"""

from __future__ import annotations

import pytest

from namios_eco.workflow import (
    METHOD_DOWNLOADED_BINARY,
    StepOutcome,
    WorkflowStep,
    WorkflowStepName,
    validate_workflow_rules,
    validate_workflow_structure,
)

_ALL_SEVEN: tuple[WorkflowStepName, ...] = (
    WorkflowStepName.DISCOVER,
    WorkflowStepName.ACQUIRE,
    WorkflowStepName.INSTALL_OR_OPEN,
    WorkflowStepName.AUTHENTICATE,
    WorkflowStepName.EXECUTE,
    WorkflowStepName.SUBMIT_OR_EXPORT,
    WorkflowStepName.VERIFY_RESULT,
)


def _full_pass_steps() -> tuple[WorkflowStep, ...]:
    return tuple(WorkflowStep(name, StepOutcome.PASS) for name in _ALL_SEVEN)


def test_web_app_cannot_claim_acquire_is_a_downloaded_binary() -> None:
    steps = tuple(
        (
            WorkflowStep(name, StepOutcome.PASS, method=METHOD_DOWNLOADED_BINARY)
            if name == WorkflowStepName.ACQUIRE
            else WorkflowStep(name, StepOutcome.PASS)
        )
        for name in _ALL_SEVEN
    )
    errors = validate_workflow_rules(steps, is_web_without_binary=True)
    assert any(e.code == "E_ECO_ACQUIRE_METHOD_INVALID" for e in errors)


@pytest.mark.parametrize("removed_step", _ALL_SEVEN, ids=lambda s: s.value)
def test_removing_any_single_step_instead_of_not_applicable_is_rejected(
    removed_step: WorkflowStepName,
) -> None:
    """Thử "xoá bước" (vd ký/xác thực) khỏi danh sách thay vì ghi
    ``not_applicable`` — PHẢI bị chặn bởi bất biến kết cấu, với TỪNG nấc
    trong 7 nấc (không chỉ nấc dev đã test là ``verify_result``)."""

    steps = tuple(s for s in _full_pass_steps() if s.name != removed_step)
    errors = validate_workflow_structure(steps)
    assert any(e.code == "E_ECO_STEP_MISSING" for e in errors), (
        f"Xoá nấc '{removed_step.value}' khỏi danh sách PHẢI bị chặn "
        "E_ECO_STEP_MISSING — không có cách hợp lệ nào thiếu bất kỳ nấc nào."
    )


def test_authenticate_step_marked_not_applicable_instead_of_removed_is_the_correct_path() -> None:
    """Đối chứng dương: cách ĐÚNG để biểu diễn "thủ tục không cần ký/xác
    thực riêng" là giữ nấc, ghi ``not_applicable`` — không xoá. Phải pass
    cấu trúc."""

    steps = tuple(
        (
            WorkflowStep(
                name, StepOutcome.NOT_APPLICABLE, note_vi="Thủ tục không yêu cầu ký riêng."
            )
            if name == WorkflowStepName.AUTHENTICATE
            else WorkflowStep(name, StepOutcome.PASS)
        )
        for name in _ALL_SEVEN
    )
    assert validate_workflow_structure(steps) == []
    by_name = {s.name: s for s in steps}
    assert by_name[WorkflowStepName.AUTHENTICATE].outcome == StepOutcome.NOT_APPLICABLE


def test_removing_two_steps_at_once_reports_both_missing() -> None:
    """Xoá đồng thời 2 nấc (vd authenticate + submit_or_export) phải báo
    ĐỦ cả hai lỗi thiếu nấc, không chỉ nấc đầu tiên phát hiện được."""

    steps = tuple(
        s
        for s in _full_pass_steps()
        if s.name not in (WorkflowStepName.AUTHENTICATE, WorkflowStepName.SUBMIT_OR_EXPORT)
    )
    errors = validate_workflow_structure(steps)
    missing_paths = {e.message_vi for e in errors if e.code == "E_ECO_STEP_MISSING"}
    assert any("authenticate" in m for m in missing_paths)
    assert any("submit_or_export" in m for m in missing_paths)


def test_duplicating_a_step_to_disguise_a_missing_one_is_rejected() -> None:
    """Tấn công tinh vi hơn: thay nấc bị xoá bằng một BẢN SAO của nấc khác
    (để giữ đúng SỐ LƯỢNG 7 phần tử, đánh lừa một kiểm tra chỉ đếm
    ``len(steps) == 7``) — vẫn phải bị chặn vì thiếu TÊN nấc bắt buộc."""

    steps = tuple(
        (
            WorkflowStep(
                WorkflowStepName.DISCOVER, StepOutcome.PASS
            )  # trùng, thế chỗ verify_result
            if s.name == WorkflowStepName.VERIFY_RESULT
            else s
        )
        for s in _full_pass_steps()
    )
    assert len(steps) == 7  # vẫn đủ SỐ LƯỢNG — tấn công nhằm đánh lừa kiểm tra đếm thô
    errors = validate_workflow_structure(steps)
    assert any(e.code == "E_ECO_STEP_MISSING" for e in errors)
    assert any(e.code == "E_ECO_STEP_UNKNOWN_OR_DUPLICATE" for e in errors)
