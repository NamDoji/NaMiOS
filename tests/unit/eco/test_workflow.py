"""ECO-001 — mô hình 7 nấc: cấu trúc bắt buộc + rule web-app-không-binary."""

from __future__ import annotations

from tests.unit.eco._fixtures import ALL_PASS_STEPS, not_run_steps, steps_with

from namios_eco.workflow import (
    METHOD_DOWNLOADED_BINARY,
    METHOD_OPEN_BROWSER,
    StepOutcome,
    WorkflowStep,
    WorkflowStepName,
    validate_workflow_rules,
    validate_workflow_structure,
)


def test_all_pass_steps_structurally_valid() -> None:
    assert validate_workflow_structure(ALL_PASS_STEPS) == []


def test_not_run_baseline_structurally_valid() -> None:
    assert validate_workflow_structure(not_run_steps()) == []


def test_missing_step_rejected() -> None:
    steps = tuple(s for s in ALL_PASS_STEPS if s.name != WorkflowStepName.VERIFY_RESULT)
    errors = validate_workflow_structure(steps)
    assert errors
    assert any("verify_result" in e.message_vi for e in errors)
    assert any(e.code == "E_ECO_STEP_MISSING" for e in errors)


def test_duplicate_step_rejected() -> None:
    steps = ALL_PASS_STEPS + (WorkflowStep(WorkflowStepName.DISCOVER, StepOutcome.PASS),)
    errors = validate_workflow_structure(steps)
    assert any(e.code == "E_ECO_STEP_UNKNOWN_OR_DUPLICATE" for e in errors)


def test_wrong_order_rejected() -> None:
    reordered = (ALL_PASS_STEPS[1], ALL_PASS_STEPS[0]) + ALL_PASS_STEPS[2:]
    errors = validate_workflow_structure(reordered)
    assert any(e.code == "E_ECO_STEP_ORDER" for e in errors)


def test_not_applicable_step_kept_not_removed() -> None:
    """Thủ tục không cần ký: nấc ghi not_applicable NHƯNG VẪN nằm trong 7 nấc
    — không có cách nào "xoá" nó khỏi WorkflowResult hợp lệ."""

    steps = steps_with(
        {
            WorkflowStepName.AUTHENTICATE: WorkflowStep(
                WorkflowStepName.AUTHENTICATE,
                StepOutcome.NOT_APPLICABLE,
                note_vi="Thủ tục không yêu cầu ký/xác thực riêng.",
            )
        }
    )
    assert validate_workflow_structure(steps) == []
    names = tuple(s.name for s in steps)
    assert WorkflowStepName.AUTHENTICATE in names
    by_name = {s.name: s for s in steps}
    assert by_name[WorkflowStepName.AUTHENTICATE].outcome == StepOutcome.NOT_APPLICABLE


def test_web_app_acquire_downloaded_binary_rejected() -> None:
    steps = steps_with(
        {
            WorkflowStepName.ACQUIRE: WorkflowStep(
                WorkflowStepName.ACQUIRE, StepOutcome.PASS, method=METHOD_DOWNLOADED_BINARY
            )
        }
    )
    errors = validate_workflow_rules(steps, is_web_without_binary=True)
    assert any(e.code == "E_ECO_ACQUIRE_METHOD_INVALID" for e in errors)


def test_web_app_install_or_open_must_be_open_browser() -> None:
    steps = steps_with(
        {
            WorkflowStepName.ACQUIRE: WorkflowStep(
                WorkflowStepName.ACQUIRE, StepOutcome.NOT_APPLICABLE
            ),
            WorkflowStepName.INSTALL_OR_OPEN: WorkflowStep(
                WorkflowStepName.INSTALL_OR_OPEN, StepOutcome.PASS, method="some_other_method"
            ),
        }
    )
    errors = validate_workflow_rules(steps, is_web_without_binary=True)
    assert any(e.code == "E_ECO_INSTALL_METHOD_INVALID" for e in errors)


def test_web_app_correct_open_browser_method_accepted() -> None:
    steps = steps_with(
        {
            WorkflowStepName.ACQUIRE: WorkflowStep(
                WorkflowStepName.ACQUIRE, StepOutcome.NOT_APPLICABLE
            ),
            WorkflowStepName.INSTALL_OR_OPEN: WorkflowStep(
                WorkflowStepName.INSTALL_OR_OPEN, StepOutcome.PASS, method=METHOD_OPEN_BROWSER
            ),
        }
    )
    errors = validate_workflow_rules(steps, is_web_without_binary=True)
    assert errors == []


def test_non_web_app_not_subject_to_web_rule() -> None:
    steps = steps_with(
        {
            WorkflowStepName.ACQUIRE: WorkflowStep(
                WorkflowStepName.ACQUIRE, StepOutcome.PASS, method=METHOD_DOWNLOADED_BINARY
            )
        }
    )
    assert validate_workflow_rules(steps, is_web_without_binary=False) == []
