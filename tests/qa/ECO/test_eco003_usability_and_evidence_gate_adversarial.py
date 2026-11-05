"""ECO-003 — GATE đối kháng (bộ test độc lập của tester, KHÔNG tái dùng
``tests/unit/eco/_fixtures.py`` của dev):

  1. Không được gán ``published_status=workflow_verified`` cho một entry
     mà dữ liệu 7 nấc thật chỉ chứng minh được ``launches_only``/
     ``downloadable_only`` (thiếu evidence submit/verify thật).
  2. Chuyển trạng thái bất hợp lệ (nhảy tắt, thoát khỏi ``revoked``) phải bị
     chặn.
  3. ``downloadable_only``/``launches_only`` hiển thị "usable" phải bị chặn
     TUYỆT ĐỐI — thử nhiều cách gọi khác nhau để tìm đường vòng.
"""

from __future__ import annotations

import pytest
from tests.qa.ECO._qa_fixtures import steps_single_outcome

from namios_eco.status import (
    NEVER_USABLE_STATUSES,
    PublishedStatus,
    derive_published_status,
    is_usable,
)
from namios_eco.validator import (
    ALLOWED_STATUS_TRANSITIONS,
    validate_status_matches_workflow,
    validate_status_transition,
    validate_usability_claim,
)
from namios_eco.workflow import StepOutcome, WorkflowStepName

# -- (1) workflow_verified claim trên dữ liệu chỉ đạt launches_only/downloadable_only


def test_claiming_workflow_verified_on_downloadable_only_shaped_steps_is_rejected() -> None:
    """acquire pass, install_or_open chưa chạy gì (not_run) -> dữ liệu thật
    chỉ chứng minh downloadable_only. Thử claim workflow_verified PHẢI bị
    validator từ chối."""

    steps = steps_single_outcome(
        WorkflowStepName.ACQUIRE,
        StepOutcome.PASS,
        before=StepOutcome.PASS,
        after=StepOutcome.NOT_RUN,
    )
    derived = derive_published_status(steps)
    assert derived.status == PublishedStatus.DOWNLOADABLE_ONLY  # giả định đúng trước khi test gate

    errors = validate_status_matches_workflow(PublishedStatus.WORKFLOW_VERIFIED, steps)
    assert errors and errors[0].code == "E_EVIDENCE_MISSING"


def test_claiming_workflow_verified_on_launches_only_shaped_steps_is_rejected() -> None:
    """install_or_open pass, authenticate chưa chạy -> launches_only. Thử
    claim workflow_verified PHẢI bị từ chối."""

    steps = steps_single_outcome(
        WorkflowStepName.INSTALL_OR_OPEN,
        StepOutcome.PASS,
        before=StepOutcome.PASS,
        after=StepOutcome.NOT_RUN,
    )
    derived = derive_published_status(steps)
    assert derived.status == PublishedStatus.LAUNCHES_ONLY

    errors = validate_status_matches_workflow(PublishedStatus.WORKFLOW_VERIFIED, steps)
    assert errors and errors[0].code == "E_EVIDENCE_MISSING"


def test_claiming_workflow_verified_when_evidence_ref_is_empty_string_is_rejected() -> None:
    """submit/verify pass nhưng evidence_ref="" (chuỗi rỗng, không phải
    None) — vẫn phải coi là KHÔNG có bằng chứng, không lách qua kiểm tra
    "is not None"."""

    from namios_eco.workflow import WorkflowStep

    steps = tuple(
        WorkflowStep(
            name,
            StepOutcome.PASS,
            evidence_ref=(
                ""
                if name in (WorkflowStepName.SUBMIT_OR_EXPORT, WorkflowStepName.VERIFY_RESULT)
                else None
            ),
        )
        for name in (
            WorkflowStepName.DISCOVER,
            WorkflowStepName.ACQUIRE,
            WorkflowStepName.INSTALL_OR_OPEN,
            WorkflowStepName.AUTHENTICATE,
            WorkflowStepName.EXECUTE,
            WorkflowStepName.SUBMIT_OR_EXPORT,
            WorkflowStepName.VERIFY_RESULT,
        )
    )
    derived = derive_published_status(steps)
    assert derived.status != PublishedStatus.WORKFLOW_VERIFIED


# -- (2) chuyển trạng thái bất hợp lệ


@pytest.mark.parametrize(
    ("frm", "to"),
    [
        (PublishedStatus.NOT_INVENTORIED, PublishedStatus.WORKFLOW_VERIFIED),
        (PublishedStatus.DOWNLOADABLE_ONLY, PublishedStatus.WORKFLOW_VERIFIED),
        (PublishedStatus.LAUNCHES_ONLY, PublishedStatus.WORKFLOW_VERIFIED),
        (PublishedStatus.REVOKED, PublishedStatus.WORKFLOW_VERIFIED),
        (PublishedStatus.REVOKED, PublishedStatus.NOT_INVENTORIED),
    ],
)
def test_illegal_status_jump_rejected(frm: PublishedStatus, to: PublishedStatus) -> None:
    errors = validate_status_transition(frm, to)
    assert errors and errors[0].code == "E_STATE_CONFLICT", f"{frm} -> {to} phải bị chặn"


def test_every_published_status_has_an_explicit_transition_table_entry() -> None:
    """Không bỏ sót trạng thái nào trong bảng chuyển — một trạng thái vắng
    mặt khỏi ``ALLOWED_STATUS_TRANSITIONS`` sẽ bị coi là "không cho đi đâu
    cả" một cách NGẪU NHIÊN (do ``.get(frm, frozenset())``), không phải một
    quyết định rõ ràng."""

    for status in PublishedStatus:
        assert status in ALLOWED_STATUS_TRANSITIONS, (
            f"'{status.value}' thiếu trong ALLOWED_STATUS_TRANSITIONS — hành vi "
            "chuyển trạng thái từ đây sẽ ngầm định rơi về rỗng, không rõ ràng."
        )


# -- (3) downloadable_only/launches_only "usable" bị chặn tuyệt đối, nhiều đường gọi


@pytest.mark.parametrize("status", sorted(NEVER_USABLE_STATUSES, key=lambda s: s.value))
def test_is_usable_never_true_for_never_usable_statuses(status: PublishedStatus) -> None:
    assert is_usable(status) is False


@pytest.mark.parametrize("status", sorted(NEVER_USABLE_STATUSES, key=lambda s: s.value))
def test_validator_rejects_explicit_usable_claim_for_never_usable_statuses(
    status: PublishedStatus,
) -> None:
    errors = validate_usability_claim(status, claimed_usable=True)
    assert errors and errors[0].code == "E_ECO_USABILITY_CLAIM"


def test_never_usable_statuses_constant_is_exactly_downloadable_and_launches() -> None:
    """Khoá cứng danh sách — nếu ai đó vô tình thêm/bớt một trạng thái vào
    ``NEVER_USABLE_STATUSES`` sau này, test này nổ ra ngay (bảo vệ bất biến
    cấp cao nhất của ECO-003, không chỉ hành vi hàm)."""

    assert NEVER_USABLE_STATUSES == frozenset(
        {PublishedStatus.DOWNLOADABLE_ONLY, PublishedStatus.LAUNCHES_ONLY}
    )
