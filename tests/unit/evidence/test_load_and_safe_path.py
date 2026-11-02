"""``EvidenceValidatorImpl.load`` — build report + an toàn đường dẫn (WP9)."""

from __future__ import annotations

import os

import pytest
from tests.unit.evidence._fixtures import fixture_path

from namios_core.evidence_types import EvidenceReport
from namios_evidence._errors import EvidenceLoadError
from namios_evidence._safe_io import PathUnsafeError
from namios_evidence.validator import EvidenceValidatorImpl


def _validator() -> EvidenceValidatorImpl:
    return EvidenceValidatorImpl()


def test_load_valid_report_builds_evidence_report() -> None:
    rep = _validator().load(fixture_path("sample-task-verified.json"))
    assert isinstance(rep, EvidenceReport)
    assert rep.report_id == "run-2026-11-02-misa-sme-wine-01"
    assert rep.manifest_id == "misa-sme-wine"
    assert rep.decision == "task_verified"
    assert rep.qa_reviewer == "qa.nguyen-van-a"
    assert len(rep.tests) == 3
    required = [t for t in rep.tests if t.required]
    assert len(required) == 2
    assert all(t.result == "pass" for t in required)


def test_load_unknown_key_report_raises_evidence_load_error() -> None:
    with pytest.raises(EvidenceLoadError) as exc_info:
        _validator().load(fixture_path("sample-unknown-key.json"))
    assert any(e.code == "E_INPUT_UNKNOWN_KEY" for e in exc_info.value.errors)


def test_load_malformed_json_raises_evidence_load_error(tmp_path: object) -> None:
    bad_path = os.path.join(str(tmp_path), "bad.json")  # type: ignore[arg-type]
    with open(bad_path, "w", encoding="utf-8") as fh:
        fh.write("{not valid json")
    with pytest.raises(EvidenceLoadError) as exc_info:
        _validator().load(bad_path)
    assert any(e.code == "E_INPUT_SCHEMA" for e in exc_info.value.errors)


def test_load_relative_path_rejected() -> None:
    with pytest.raises(PathUnsafeError):
        _validator().load("fixtures/evidence/sample-task-verified.json")


def test_load_symlink_traversal_outside_dir_rejected(tmp_path: object) -> None:
    tmp = str(tmp_path)  # type: ignore[arg-type]
    real_dir = os.path.join(tmp, "real")
    os.makedirs(real_dir)
    linked_dir = os.path.join(tmp, "linked")
    os.symlink(real_dir, linked_dir)
    target = os.path.join(real_dir, "report.json")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("{}")

    with pytest.raises(PathUnsafeError):
        # thư mục chứa file (``linked``) là symlink — phải bị chặn, dù file
        # đích tồn tại thật và nội dung vô hại.
        _validator().load(os.path.join(linked_dir, "report.json"))


def test_load_symlink_leaf_file_rejected(tmp_path: object) -> None:
    tmp = str(tmp_path)  # type: ignore[arg-type]
    target = os.path.join(tmp, "report.json")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("{}")
    link = os.path.join(tmp, "report-link.json")
    os.symlink(target, link)

    with pytest.raises(PathUnsafeError):
        _validator().load(link)
