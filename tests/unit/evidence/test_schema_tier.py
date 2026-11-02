"""Tầng 1 — schema cấu trúc evidence-report (WP9)."""

from __future__ import annotations

from tests.unit.evidence._fixtures import contract_sample_path, fixture_path, load_raw

from namios_evidence.validator import EvidenceValidatorImpl


def _validator() -> EvidenceValidatorImpl:
    return EvidenceValidatorImpl()


def test_valid_task_verified_report_passes_schema() -> None:
    raw = load_raw(fixture_path("sample-task-verified.json"))
    result = _validator().validate_schema(raw)
    assert result.ok is True
    assert result.errors == ()


def test_contract_sample_not_run_passes_schema_but_is_semantically_incomplete() -> None:
    # "Schema hợp lệ" ≠ "an toàn/đủ để chứng nhận" (FACT §11.1/§11.2) — mẫu
    # chính thức sample-evidence-not-run.json PHẢI hợp lệ ở tầng 1 (đúng
    # cấu trúc) nhưng sẽ bị gate tầng 2 từ chối (xem test_gate.py).
    raw = load_raw(contract_sample_path("sample-evidence-not-run.json"))
    result = _validator().validate_schema(raw)
    assert result.ok is True


def test_unknown_key_rejected_with_stable_error_code() -> None:
    raw = load_raw(fixture_path("sample-unknown-key.json"))
    result = _validator().validate_schema(raw)
    assert result.ok is False
    assert any(e.code == "E_INPUT_UNKNOWN_KEY" for e in result.errors)
    assert any("trusted_by_vendor" in e.path for e in result.errors)


def test_missing_required_top_level_key_rejected() -> None:
    raw = load_raw(fixture_path("sample-task-verified.json"))
    del raw["decision"]
    result = _validator().validate_schema(raw)
    assert result.ok is False
    assert any(e.path == "decision" for e in result.errors)


def test_bad_enum_result_rejected() -> None:
    raw = load_raw(fixture_path("sample-task-verified.json"))
    raw["tests"][0]["result"] = "maybe"
    result = _validator().validate_schema(raw)
    assert result.ok is False
    assert any("result" in e.path for e in result.errors)


def test_bad_sha256_shape_rejected() -> None:
    raw = load_raw(fixture_path("sample-task-verified.json"))
    raw["profile_sha256"] = "not-a-hash"
    result = _validator().validate_schema(raw)
    assert result.ok is False
    assert any(e.path == "profile_sha256" for e in result.errors)


def test_non_object_root_rejected() -> None:
    result = _validator().validate_schema([1, 2, 3])  # type: ignore[arg-type]
    assert result.ok is False
