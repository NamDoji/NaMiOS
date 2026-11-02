"""Gate tầng 2 — ``compute_allowed_status`` (§11.2/§18.3, WP9).

Bất biến bắt buộc: KHÔNG cho đặt ``task_verified`` nếu thiếu evidence /
thiếu required tests pass / chưa QA-approved. ``sample-evidence-not-run.json``
PHẢI bị từ chối làm chứng nhận (yêu cầu tường minh của WP9)."""

from __future__ import annotations

from dataclasses import replace

from tests.unit.evidence._fixtures import contract_sample_path, fixture_path, load_raw

from namios_core.compat import CompatStatus
from namios_core.evidence_types import EvidenceReport, EvidenceTest
from namios_evidence.validator import EvidenceValidatorImpl, build_report


def _validator() -> EvidenceValidatorImpl:
    return EvidenceValidatorImpl()


def _load_report(filename: str) -> EvidenceReport:
    v = _validator()
    raw = load_raw(fixture_path(filename))
    assert v.validate_schema(raw).ok, "fixture phải schema-valid trước khi test gate"
    return build_report(raw)


def test_all_required_pass_with_qa_reviewer_is_task_verified() -> None:
    rep = _load_report("sample-task-verified.json")
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status == CompatStatus.TASK_VERIFIED
    assert gate.reasons_vi


def test_pass_without_qa_reviewer_never_task_verified() -> None:
    rep = _load_report("sample-missing-qa-reviewer.json")
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status != CompatStatus.TASK_VERIFIED
    assert gate.allowed_status == CompatStatus.EXPERIMENTAL
    assert any("qa_reviewer" in r for r in gate.reasons_vi)


def test_required_fail_is_blocked_not_task_verified() -> None:
    rep = _load_report("sample-required-fail.json")
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status != CompatStatus.TASK_VERIFIED
    assert gate.allowed_status == CompatStatus.BLOCKED


def test_official_sample_evidence_not_run_is_rejected_for_certification() -> None:
    """Yêu cầu tường minh WP9: sample-evidence-not-run.json PHẢI bị từ chối
    làm chứng nhận — không được là ``task_verified``."""

    v = _validator()
    raw = load_raw(contract_sample_path("sample-evidence-not-run.json"))
    assert v.validate_schema(raw).ok  # schema hợp lệ (tầng 1)
    rep = build_report(raw)
    gate = v.compute_allowed_status(rep)
    assert gate.allowed_status != CompatStatus.TASK_VERIFIED
    assert gate.allowed_status in (CompatStatus.BLOCKED, CompatStatus.UNTESTED)
    assert gate.reasons_vi


def test_skipped_required_test_is_never_treated_as_pass() -> None:
    rep = _load_report("sample-task-verified.json")
    tests = tuple(replace(t, result="skipped") if t.test_id == "MISA-02" else t for t in rep.tests)
    rep_with_skip = replace(rep, tests=tests)
    gate = _validator().compute_allowed_status(rep_with_skip)
    assert gate.allowed_status != CompatStatus.TASK_VERIFIED
    assert gate.allowed_status == CompatStatus.BLOCKED


def test_no_required_tests_declared_is_untested() -> None:
    rep = EvidenceReport(
        report_id="r1",
        manifest_id="app-x",
        tests=(EvidenceTest(test_id="OPTIONAL-1", required=False, result="pass"),),
        decision="experimental",
        qa_reviewer=None,
        environment={},
    )
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status == CompatStatus.UNTESTED


def test_revoked_decision_wins_even_if_tests_pass_and_qa_approved() -> None:
    rep = EvidenceReport(
        report_id="r2",
        manifest_id="app-x",
        tests=(EvidenceTest(test_id="T1", required=True, result="pass"),),
        decision="revoked",
        qa_reviewer="qa.someone",
        environment={},
    )
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status == CompatStatus.REVOKED


def test_blocked_external_dependency_required_blocks_certification() -> None:
    rep = EvidenceReport(
        report_id="r3",
        manifest_id="app-x",
        tests=(
            EvidenceTest(test_id="T1", required=True, result="pass"),
            EvidenceTest(test_id="T2", required=True, result="blocked_external_dependency"),
        ),
        decision="blocked",
        qa_reviewer="qa.someone",
        environment={},
    )
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status != CompatStatus.TASK_VERIFIED
    assert gate.allowed_status == CompatStatus.BLOCKED


def test_optional_test_failure_does_not_block_task_verified() -> None:
    rep = EvidenceReport(
        report_id="r4",
        manifest_id="app-x",
        tests=(
            EvidenceTest(test_id="T1", required=True, result="pass"),
            EvidenceTest(test_id="T2-optional", required=False, result="fail"),
        ),
        decision="task_verified",
        qa_reviewer="qa.someone",
        environment={},
    )
    gate = _validator().compute_allowed_status(rep)
    assert gate.allowed_status == CompatStatus.TASK_VERIFIED
