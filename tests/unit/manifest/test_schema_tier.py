"""MAN-01 — Tầng 1: JSON Schema structural (additionalProperties:false →
unknown key fail; type/enum/pattern/required đúng theo
contracts/app-manifest.schema.json)."""

from __future__ import annotations

import json
from pathlib import Path

from namios_core.errors import ErrorCode
from namios_manifest import ManifestValidatorImpl

from ._fixtures import deep_copy, valid_raw_manifest

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_minimal_valid_manifest_passes_schema() -> None:
    validator = ManifestValidatorImpl()
    result = validator.validate_schema(valid_raw_manifest())
    assert result.ok is True
    assert result.errors == ()


def test_sample_misa_passes_schema() -> None:
    validator = ManifestValidatorImpl()
    raw = json.loads((_REPO_ROOT / "contracts" / "sample-misa-sme-wine.json").read_text())
    result = validator.validate_schema(raw)
    assert result.ok is True, result.errors


def test_unknown_top_level_key_fails_with_unknown_key_code() -> None:
    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["unexpected_extra_field"] = "giá trị lạ"

    result = validator.validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_UNKNOWN_KEY.value for e in result.errors)
    assert any(e.path == "$.unexpected_extra_field" for e in result.errors)


def test_unknown_nested_key_fails_with_unknown_key_code() -> None:
    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["application"]["unexpected_nested"] = 1

    result = validator.validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_UNKNOWN_KEY.value for e in result.errors)


def test_missing_required_field_fails_schema() -> None:
    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    del raw["application"]["build"]

    result = validator.validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_invalid_enum_value_fails_schema() -> None:
    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["mode"] = "not-a-real-mode"

    result = validator.validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_recipe_action_outside_enum_fails_schema() -> None:
    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [{"action": "delete_everything", "params": {}}]

    result = validator.validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_bad_installer_sha256_pattern_fails_schema() -> None:
    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["application"]["installer_sha256"] = "not-a-hex-hash"

    result = validator.validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_recipe_params_with_shell_key_still_passes_schema_tier() -> None:
    """Quan trọng: schema (tầng 1) KHÔNG chặn khóa lạ bên trong
    ``recipe[].params`` (schema không đặt additionalProperties:false ở đó
    — chủ ý, để tầng 2/semantic của WP2 chặn 'shell' một cách tường minh).
    """

    validator = ManifestValidatorImpl()
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "installer.exe",
                "argv": ["installer.exe", "/S"],
                "shell": "rm -rf /",
            },
        }
    ]

    result = validator.validate_schema(raw)

    assert result.ok is True, result.errors
