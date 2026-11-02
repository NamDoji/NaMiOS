"""ECO-003 — GATE: downloadable_only/launches_only KHÔNG BAO GIỜ usable;
workflow_verified CHỈ khi có evidence nộp/nhận. ECO-015 — WindowsMode."""

from __future__ import annotations

import pytest
from tests.unit.eco._fixtures import ALL_PASS_STEPS, not_run_steps, steps_with

from namios_eco.status import (
    NEVER_USABLE_STATUSES,
    USABLE_STATUSES,
    PublishedStatus,
    WindowsMode,
    derive_published_status,
    is_usable,
    is_windows_free,
)
from namios_eco.workflow import StepOutcome, WorkflowStep, WorkflowStepName

# -- GATE "never usable" tuyệt đối -------------------------------------------


@pytest.mark.parametrize("status", sorted(NEVER_USABLE_STATUSES, key=lambda s: s.value))
def test_never_usable_statuses_always_false(status: PublishedStatus) -> None:
    assert is_usable(status) is False


@pytest.mark.parametrize("status", sorted(USABLE_STATUSES, key=lambda s: s.value))
def test_usable_statuses_true(status: PublishedStatus) -> None:
    assert is_usable(status) is True


@pytest.mark.parametrize(
    "status",
    sorted(set(PublishedStatus) - NEVER_USABLE_STATUSES - USABLE_STATUSES, key=lambda s: s.value),
)
def test_other_statuses_not_usable(status: PublishedStatus) -> None:
    assert is_usable(status) is False


# -- derive_published_status: các nấc rỗng/full ------------------------------


def test_all_not_run_is_not_inventoried() -> None:
    result = derive_published_status(not_run_steps())
    assert result.status == PublishedStatus.NOT_INVENTORIED


def test_full_pass_with_evidence_is_workflow_verified() -> None:
    result = derive_published_status(ALL_PASS_STEPS)
    assert result.status == PublishedStatus.WORKFLOW_VERIFIED


def test_discover_fail_is_unsupported() -> None:
    steps = steps_with(
        {WorkflowStepName.DISCOVER: WorkflowStep(WorkflowStepName.DISCOVER, StepOutcome.FAIL)}
    )
    assert derive_published_status(steps).status == PublishedStatus.UNSUPPORTED


def test_acquire_pass_install_not_run_is_downloadable_only() -> None:
    steps = steps_with(
        {
            WorkflowStepName.INSTALL_OR_OPEN: WorkflowStep(
                WorkflowStepName.INSTALL_OR_OPEN, StepOutcome.NOT_RUN
            ),
            WorkflowStepName.AUTHENTICATE: WorkflowStep(
                WorkflowStepName.AUTHENTICATE, StepOutcome.NOT_RUN
            ),
            WorkflowStepName.EXECUTE: WorkflowStep(WorkflowStepName.EXECUTE, StepOutcome.NOT_RUN),
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.NOT_RUN
            ),
            WorkflowStepName.VERIFY_RESULT: WorkflowStep(
                WorkflowStepName.VERIFY_RESULT, StepOutcome.NOT_RUN
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.DOWNLOADABLE_ONLY
    assert is_usable(result.status) is False


def test_install_pass_authenticate_not_run_is_launches_only() -> None:
    steps = steps_with(
        {
            WorkflowStepName.AUTHENTICATE: WorkflowStep(
                WorkflowStepName.AUTHENTICATE, StepOutcome.NOT_RUN
            ),
            WorkflowStepName.EXECUTE: WorkflowStep(WorkflowStepName.EXECUTE, StepOutcome.NOT_RUN),
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.NOT_RUN
            ),
            WorkflowStepName.VERIFY_RESULT: WorkflowStep(
                WorkflowStepName.VERIFY_RESULT, StepOutcome.NOT_RUN
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.LAUNCHES_ONLY
    assert is_usable(result.status) is False


def test_progressed_but_submit_not_run_is_partial_workflow() -> None:
    steps = steps_with(
        {
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.NOT_RUN
            ),
            WorkflowStepName.VERIFY_RESULT: WorkflowStep(
                WorkflowStepName.VERIFY_RESULT, StepOutcome.NOT_RUN
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.PARTIAL_WORKFLOW


def test_submit_verify_pass_without_evidence_is_partial_not_verified() -> None:
    """GATE trung tâm: pass kỹ thuật KHÔNG đủ — thiếu evidence_ref thì
    KHÔNG BAO GIỜ được workflow_verified."""

    steps = steps_with(
        {
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.PASS, evidence_ref=None
            ),
            WorkflowStepName.VERIFY_RESULT: WorkflowStep(
                WorkflowStepName.VERIFY_RESULT, StepOutcome.PASS, evidence_ref=None
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.PARTIAL_WORKFLOW
    assert "evidence" in " ".join(result.reasons_vi).lower() or "bằng chứng" in " ".join(
        result.reasons_vi
    )


def test_submit_verify_pass_with_whitespace_only_evidence_rejected() -> None:
    """evidence_ref chỉ chứa khoảng trắng coi như KHÔNG có bằng chứng."""

    steps = steps_with(
        {
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.PASS, evidence_ref="   "
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED


def test_blocked_external_dependency_from_submit_step() -> None:
    """ECO-016: không có sandbox → dừng trước nộp, ghi blocked_external_dependency."""

    steps = steps_with(
        {
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT,
                StepOutcome.BLOCKED,
                note_vi="Không có sandbox/môi trường thử chính thức.",
            ),
            WorkflowStepName.VERIFY_RESULT: WorkflowStep(
                WorkflowStepName.VERIFY_RESULT, StepOutcome.NOT_RUN
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY
    assert is_usable(result.status) is False


def test_real_failure_after_install_is_unsupported_not_blocked() -> None:
    steps = steps_with(
        {
            WorkflowStepName.EXECUTE: WorkflowStep(WorkflowStepName.EXECUTE, StepOutcome.FAIL),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.UNSUPPORTED


def test_not_applicable_submit_with_verified_result_can_be_workflow_verified() -> None:
    """Thủ tục không có bước nộp/xuất (vd tra cứu) nhưng verify_result pass
    + có evidence vẫn đủ điều kiện workflow_verified."""

    steps = steps_with(
        {
            WorkflowStepName.SUBMIT_OR_EXPORT: WorkflowStep(
                WorkflowStepName.SUBMIT_OR_EXPORT, StepOutcome.NOT_APPLICABLE
            ),
        }
    )
    result = derive_published_status(steps)
    assert result.status == PublishedStatus.WORKFLOW_VERIFIED


# -- WindowsMode (ECO-015) ---------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "expected_free"),
    [
        (WindowsMode.NATIVE_LINUX, True),
        (WindowsMode.WEB_LINUX, True),
        (WindowsMode.WINE, False),
        (WindowsMode.REMOTE_WINDOWS, False),
        (WindowsMode.WINDOWS_VM, False),
    ],
)
def test_is_windows_free(mode: WindowsMode, expected_free: bool) -> None:
    assert is_windows_free(mode) is expected_free
