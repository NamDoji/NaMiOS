"""N10-043 — Workflow verdict + evidence: "đã xong" chỉ khi có bằng chứng hợp lệ.

Fixture nghiệm thu literal: "job spool thành công nhưng giấy trắng vẫn
failed/partial" — exit-code/CUPS 'completed' (``MACHINE_DONE``) MỘT MÌNH
không đủ để ``PASSED``.
"""

from __future__ import annotations

from namios_e08 import DepKind, DepNode, DepState
from namios_mig import EvidenceRecord, WorkflowTest, WorkflowTestStatus
from namios_mig.workflow_verdict import (
    assess_workflow,
    evaluate_workflow,
    evidence_outcome,
    terminal_diagnosis_if_exhausted,
)
from namios_pra import PrintStage, SignSubmitStage

WT = WorkflowTestStatus


def _test(workflow_id: str = "vn.print.flyer.test") -> WorkflowTest:
    return WorkflowTest(workflow_id=workflow_id, app_id="app1")


def test_exit_code_spool_alone_is_insufficient_not_passed() -> None:
    # N10-043: exit-code=0/CUPS "completed" một mình KHÔNG đủ.
    ev = EvidenceRecord(
        evidence_id="e1", workflow_id="vn.print.flyer.test", print_stage=PrintStage.MACHINE_DONE
    )
    assert evidence_outcome(ev) == "insufficient"

    result = evaluate_workflow(_test(), [ev])
    assert result.status is WT.PARTIAL  # KHÔNG được PASSED chỉ từ exit-code/spool


def test_spool_ok_but_blank_page_is_failed() -> None:
    # Fixture literal nghiệm thu: "job spool thành công nhưng giấy trắng vẫn
    # failed/partial".
    spool_ok = EvidenceRecord(
        evidence_id="e1", workflow_id="vn.print.flyer.test", print_stage=PrintStage.MACHINE_DONE
    )
    blank_page = EvidenceRecord(
        evidence_id="e2",
        workflow_id="vn.print.flyer.test",
        independent_check_ok=False,
        detail_vi="Người dùng xác nhận giấy trắng, không có nội dung.",
    )
    result = evaluate_workflow(_test(), [spool_ok, blank_page])
    assert result.status is WT.FAILED
    assert set(result.evidence_ids) == {"e1", "e2"}


def test_user_confirmed_print_is_passed() -> None:
    confirmed = EvidenceRecord(
        evidence_id="e1", workflow_id="vn.print.flyer.test", print_stage=PrintStage.USER_CONFIRMED
    )
    result = evaluate_workflow(_test(), [confirmed], tested_at="2026-11-07")
    assert result.status is WT.PASSED
    assert result.tested_at == "2026-11-07"


def test_sign_receipt_verified_is_passed_but_submitted_alone_is_not() -> None:
    receipt = EvidenceRecord(
        evidence_id="e1",
        workflow_id="vn.invoice.sign.test",
        sign_stage=SignSubmitStage.RECEIPT_VERIFIED,
    )
    assert evidence_outcome(receipt) == "positive"

    submitted_only = EvidenceRecord(
        evidence_id="e2", workflow_id="vn.invoice.sign.test", sign_stage=SignSubmitStage.SUBMITTED
    )
    assert evidence_outcome(submitted_only) == "insufficient"

    failed_sign = EvidenceRecord(
        evidence_id="e3", workflow_id="vn.invoice.sign.test", sign_stage=SignSubmitStage.FAILED
    )
    assert evidence_outcome(failed_sign) == "negative"


def test_no_matching_evidence_is_not_tested() -> None:
    other = EvidenceRecord(
        evidence_id="e1", workflow_id="some.other.workflow", independent_check_ok=True
    )
    result = evaluate_workflow(_test(), [other])
    assert result.status is WT.NOT_TESTED
    assert result.evidence_ids == ()


def test_independent_check_true_overrides_weak_pipeline_signal() -> None:
    weak_pipeline = EvidenceRecord(
        evidence_id="e1", workflow_id="w1", print_stage=PrintStage.QUEUED, independent_check_ok=True
    )
    result = evaluate_workflow(WorkflowTest(workflow_id="w1", app_id="a"), [weak_pipeline])
    assert result.status is WT.PASSED


def test_assess_workflow_dep_blocked_overrides_any_evidence() -> None:
    # Dù evidence trông có vẻ tốt, phụ thuộc kỹ thuật BLOCKED (portal khóa) →
    # vẫn FAILED — kỹ thuật thắng, không được evidence "cứu".
    nodes = [DepNode(DepKind.RUNTIME, DepState.OK), DepNode(DepKind.PORTAL, DepState.BLOCKED)]
    good_evidence = EvidenceRecord(evidence_id="e1", workflow_id="w1", independent_check_ok=True)
    result = assess_workflow(WorkflowTest(workflow_id="w1", app_id="a"), nodes, [good_evidence])
    assert result.status is WT.FAILED


def test_assess_workflow_dep_partial_downgrades_passed_evidence() -> None:
    # DB mất (N02) → PARTIAL kỹ thuật; evidence dương không được nâng vượt mức.
    nodes = [DepNode(DepKind.RUNTIME, DepState.OK), DepNode(DepKind.DATABASE, DepState.DOWN)]
    good_evidence = EvidenceRecord(evidence_id="e1", workflow_id="w1", independent_check_ok=True)
    result = assess_workflow(WorkflowTest(workflow_id="w1", app_id="a"), nodes, [good_evidence])
    assert result.status is WT.PARTIAL


def test_assess_workflow_all_ok_dep_lets_evidence_decide() -> None:
    nodes = [DepNode(DepKind.RUNTIME, DepState.OK)]
    good_evidence = EvidenceRecord(evidence_id="e1", workflow_id="w1", independent_check_ok=True)
    result = assess_workflow(
        WorkflowTest(workflow_id="w1", app_id="a"), nodes, [good_evidence], tested_at="2026-11-07"
    )
    assert result.status is WT.PASSED
    assert result.tested_at == "2026-11-07"


def test_terminal_diagnosis_reuses_pra_doctor_bound() -> None:
    # N10-060: dừng thử lại sau N lần fail — tái dùng namios_pra.doctor.
    assert terminal_diagnosis_if_exhausted(failed_attempts=1, max_attempts=3) is None
    terminal = terminal_diagnosis_if_exhausted(failed_attempts=3, max_attempts=3)
    assert terminal is not None
    assert terminal.is_terminal is True
    assert terminal.is_blocker is True
