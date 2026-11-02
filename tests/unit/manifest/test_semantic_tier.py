"""MAN-02 — Tầng 2: semantic validator. "Schema hợp lệ" ≠ "install-ready"."""

from __future__ import annotations

import json
from pathlib import Path

from namios_core.errors import ErrorCode
from namios_core.validation import SemanticContext
from namios_manifest import ManifestValidatorImpl

from ._fixtures import deep_copy, valid_raw_manifest

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _ctx(
    approved: frozenset[str] = frozenset(),
    pinned: frozenset[str] = frozenset(),
    revoked: frozenset[str] = frozenset(),
) -> SemanticContext:
    return SemanticContext(
        approved_dependency_ids=approved, pinned_runner_hashes=pinned, revoked_ids=revoked
    )


def test_minimal_valid_manifest_is_install_ready() -> None:
    validator = ManifestValidatorImpl()
    raw = valid_raw_manifest()
    schema_result = validator.validate_schema(raw)
    assert schema_result.ok

    from namios_manifest._builder import build_manifest

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.ok is True
    assert result.install_ready is True
    assert result.errors == ()


def test_sample_misa_schema_pass_but_not_install_ready() -> None:
    """Acceptance WP2: schema PASS nhưng install_ready=False (TBD)."""

    validator = ManifestValidatorImpl()
    raw = json.loads((_REPO_ROOT / "contracts" / "sample-misa-sme-wine.json").read_text())
    assert validator.validate_schema(raw).ok is True

    from namios_manifest._builder import build_manifest

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.install_ready is False
    assert any(e.code == ErrorCode.E_SEMANTIC_TBD.value for e in result.errors)
    assert {"application.build", "application.installer_sha256"} <= {e.path for e in result.errors}


def test_dependency_not_approved_fails_with_dependency_code() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["runtime"]["dependency_profile_ids"] = ["dotnet-48-x64"]

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(approved=frozenset({"other-dep"})))

    assert result.ok is False
    assert any(
        e.code == ErrorCode.E_SEMANTIC_DEPENDENCY.value
        and e.path == "runtime.dependency_profile_ids[0]"
        for e in result.errors
    )


def test_dependency_approved_passes() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["runtime"]["dependency_profile_ids"] = ["dotnet-48-x64"]

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(approved=frozenset({"dotnet-48-x64"})))

    assert result.ok is True


def test_wine_mode_requires_pinned_runner_hash() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["mode"] = "wine"
    raw["runtime"]["runner_id"] = "wine-staging-9"
    raw["runtime"]["runner_sha256"] = "b" * 64
    raw["runtime"]["prefix_architecture"] = "win64"
    raw["runtime"]["wow64_strategy"] = "new_wow64"

    m = build_manifest(raw)

    not_pinned = validator.validate_semantic(m, _ctx())
    assert not_pinned.ok is False
    assert any(
        e.code == ErrorCode.E_SEMANTIC_DEPENDENCY.value and e.path == "runtime.runner_sha256"
        for e in not_pinned.errors
    )

    pinned = validator.validate_semantic(m, _ctx(pinned=frozenset({"b" * 64})))
    assert pinned.ok is True


def test_wine_mode_with_null_runner_is_tbd() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["mode"] = "wine"
    raw["runtime"]["prefix_architecture"] = "win64"
    raw["runtime"]["wow64_strategy"] = "new_wow64"
    # runner_id/runner_sha256 giữ None (mặc định của fixture) → TBD.

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.install_ready is False
    assert {e.path for e in result.errors} >= {"runtime.runner_id", "runtime.runner_sha256"}


def test_revoked_id_is_blocked_regardless_of_other_fields() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx(revoked=frozenset({m.id})))

    assert result.ok is False
    assert any(e.code == ErrorCode.E_REVOKED.value for e in result.errors)


def test_compatibility_revoked_status_is_blocked() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["compatibility"]["status"] = "revoked"

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.ok is False
    assert any(e.code == ErrorCode.E_REVOKED.value for e in result.errors)


def test_task_verified_without_evidence_id_is_blocked() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["compatibility"]["status"] = "task_verified"
    raw["compatibility"]["evidence_id"] = None

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.ok is False
    assert any(
        e.code == ErrorCode.E_EVIDENCE_MISSING.value and e.path == "compatibility.evidence_id"
        for e in result.errors
    )


def test_task_verified_with_evidence_id_passes() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["compatibility"]["status"] = "task_verified"
    raw["compatibility"]["evidence_id"] = "evidence-report-001"

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.ok is True


def test_existing_environment_source_skips_local_install_tbd() -> None:
    """``source.acquisition == existing_environment`` nghĩa là app đã có sẵn
    trên hệ thống — không cần build/installer_sha256 để "cài" nữa."""

    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["source"]["acquisition"] = "existing_environment"
    raw["application"]["build"] = None
    raw["application"]["installer_sha256"] = None

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.ok is True


def test_web_mode_skips_local_install_tbd() -> None:
    from namios_manifest._builder import build_manifest

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["mode"] = "web"
    raw["application"]["build"] = None
    raw["application"]["installer_sha256"] = None

    m = build_manifest(raw)
    result = validator.validate_semantic(m, _ctx())

    assert result.ok is True
