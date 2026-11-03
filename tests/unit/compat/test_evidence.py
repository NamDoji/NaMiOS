"""COMP-048/049 — provenance + GATE trạng thái tổng hợp.

Trọng tâm: metadata một mình KHÔNG tạo ra workflow_verified; gate chỉ HẠ,
không NÂNG (thu hồi / nghiệp vụ chưa duyệt / quá hạn tái kiểm)."""

from __future__ import annotations

from namios_compat._types import BusinessStatus, CompatEvidence, EvidenceEnvironment
from namios_compat.evidence import (
    compute_fixture_hash,
    evaluate_route_status,
    evidence_to_steps,
    validate_evidence,
)
from namios_eco.status import PublishedStatus
from namios_eco.workflow import WORKFLOW_STEP_ORDER, StepOutcome, WorkflowStep, WorkflowStepName


def _full_pass_steps() -> tuple[WorkflowStep, ...]:
    """7 nấc PASS, có evidence_ref ở submit + verify → đủ workflow_verified kỹ thuật."""
    steps = []
    for name in WORKFLOW_STEP_ORDER:
        ref = (
            "ev-1"
            if name
            in (
                WorkflowStepName.SUBMIT_OR_EXPORT,
                WorkflowStepName.VERIFY_RESULT,
            )
            else None
        )
        steps.append(WorkflowStep(name=name, outcome=StepOutcome.PASS, evidence_ref=ref))
    return tuple(steps)


def test_compute_fixture_hash_shape() -> None:
    h = compute_fixture_hash(b"hello")
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 64


def test_validate_evidence_missing_field() -> None:
    ev = CompatEvidence(
        evidence_id="",  # thiếu
        workflow_id="vn.tax.sample_submission",
        step=WorkflowStepName.VERIFY_RESULT,
        test_case_id="tc1",
        fixture_hash=compute_fixture_hash(b"x"),
        expected="100",
        actual="100",
        outcome=StepOutcome.PASS,
        timestamp="2026-11-03T10:00:00",
        environment=EvidenceEnvironment.SANDBOX,
        os_version="debian13",
        app_version="1.0",
        runner_version="r1",
    )
    errors = validate_evidence(ev)
    assert any(e.path == "evidence_id" for e in errors)


def test_validate_evidence_bad_hash() -> None:
    ev = CompatEvidence(
        evidence_id="e1",
        workflow_id="w",
        step=WorkflowStepName.EXECUTE,
        test_case_id="tc",
        fixture_hash="md5:zzz",
        expected="a",
        actual="a",
        outcome=StepOutcome.PASS,
        timestamp="t",
        environment=EvidenceEnvironment.SANDBOX,
        os_version="o",
        app_version="a",
        runner_version="r",
    )
    errors = validate_evidence(ev)
    assert any(e.path == "fixture_hash" for e in errors)


def test_validate_evidence_production_needs_reviewer() -> None:
    ev = CompatEvidence(
        evidence_id="e1",
        workflow_id="w",
        step=WorkflowStepName.VERIFY_RESULT,
        test_case_id="tc",
        fixture_hash=compute_fixture_hash(b"x"),
        expected="a",
        actual="a",
        outcome=StepOutcome.PASS,
        timestamp="t",
        environment=EvidenceEnvironment.PRODUCTION,
        os_version="o",
        app_version="a",
        runner_version="r",
        confirmed_by_role=None,  # production + verify PASS nhưng không ai duyệt
    )
    errors = validate_evidence(ev)
    assert any(e.path == "confirmed_by_role" for e in errors)


def test_evidence_to_steps_missing_is_not_run() -> None:
    steps = evidence_to_steps("w", [])
    assert len(steps) == 7
    assert all(s.outcome == StepOutcome.NOT_RUN for s in steps)


def test_evidence_to_steps_worst_wins() -> None:
    evs = [
        CompatEvidence(
            evidence_id="p",
            workflow_id="w",
            step=WorkflowStepName.EXECUTE,
            test_case_id="tc",
            fixture_hash=compute_fixture_hash(b"x"),
            expected="a",
            actual="a",
            outcome=StepOutcome.PASS,
            timestamp="t",
            environment=EvidenceEnvironment.SANDBOX,
            os_version="o",
            app_version="a",
            runner_version="r",
        ),
        CompatEvidence(
            evidence_id="f",
            workflow_id="w",
            step=WorkflowStepName.EXECUTE,
            test_case_id="tc2",
            fixture_hash=compute_fixture_hash(b"y"),
            expected="a",
            actual="b",
            outcome=StepOutcome.FAIL,
            timestamp="t",
            environment=EvidenceEnvironment.SANDBOX,
            os_version="o",
            app_version="a",
            runner_version="r",
        ),
    ]
    steps = {s.name: s for s in evidence_to_steps("w", evs)}
    assert steps[WorkflowStepName.EXECUTE].outcome == StepOutcome.FAIL  # xấu nhất thắng


def test_gate_revoked_beats_everything() -> None:
    res = evaluate_route_status(
        _full_pass_steps(), business_status=BusinessStatus.APPROVED, revoked=True
    )
    assert res.status == PublishedStatus.REVOKED


def test_gate_business_unreviewed_downgrades() -> None:
    res = evaluate_route_status(_full_pass_steps(), business_status=BusinessStatus.UNREVIEWED)
    assert res.status == PublishedStatus.PARTIAL_WORKFLOW


def test_gate_business_rejected_downgrades() -> None:
    res = evaluate_route_status(_full_pass_steps(), business_status=BusinessStatus.REJECTED)
    assert res.status == PublishedStatus.PARTIAL_WORKFLOW


def test_gate_expired_downgrades() -> None:
    res = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        recertify_by="2026-01-01",
        now="2026-11-03",
    )
    assert res.status == PublishedStatus.PARTIAL_WORKFLOW


def test_gate_approved_and_fresh_is_verified() -> None:
    res = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        recertify_by="2027-12-31",
        now="2026-11-03",
    )
    assert res.status == PublishedStatus.WORKFLOW_VERIFIED


def test_gate_cannot_elevate_incomplete_evidence() -> None:
    # Thiếu evidence_ref ở verify → gate kỹ thuật ECO-003 KHÔNG cho verified,
    # business approved cũng không nâng được (metadata không cứu được thiếu
    # bằng chứng).
    steps = []
    for name in WORKFLOW_STEP_ORDER:
        steps.append(WorkflowStep(name=name, outcome=StepOutcome.PASS, evidence_ref=None))
    res = evaluate_route_status(tuple(steps), business_status=BusinessStatus.APPROVED)
    assert res.status != PublishedStatus.WORKFLOW_VERIFIED
