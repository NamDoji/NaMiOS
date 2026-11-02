"""Test ``namios_cli.main`` — dispatch end-to-end, envelope đúng chuẩn,
exit code đúng bảng CLI-003, KHÔNG trộn log vào stdout JSON, wiring qua
Protocol (dependency injection), negative cases cho mọi subcommand."""

from __future__ import annotations

import io
import json

import pytest

from namios_cli.deps import CliDependencies
from namios_cli.main import main
from namios_core.compat import CompatStatus
from namios_core.exitcodes import ExitCode

from .fakes import FakeEvidenceValidator, FakeInstallPlanner, FakeManifestValidator


def _run(argv: list[str], deps: CliDependencies | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err, deps=deps)
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# doctor — WP3 hiện thực đầy đủ, không cần wiring
# ---------------------------------------------------------------------------


def test_doctor_json_exit_zero_and_valid_envelope() -> None:
    rc, out, err = _run(["doctor", "--json"])
    assert rc == ExitCode.OK
    assert err == ""  # không log lẫn vào — doctor không ghi gì ra stderr khi ok
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["error"] is None
    assert parsed["data"]["virtualization"]["has_kvm"] is False


def test_doctor_without_json_prints_human_text_not_json() -> None:
    rc, out, _err = _run(["doctor"])
    assert rc == ExitCode.OK
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)
    assert "OK" in out


# ---------------------------------------------------------------------------
# argument errors (CLI-003 exit 2) — không mix stdout log vào JSON
# ---------------------------------------------------------------------------


def test_unknown_subcommand_with_json_emits_single_error_envelope_exit_2() -> None:
    rc, out, err = _run(["khong-ton-tai", "--json"])
    assert rc == ExitCode.INPUT
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"


def test_unknown_subcommand_without_json_writes_message_to_stderr_only() -> None:
    rc, out, err = _run(["khong-ton-tai"])
    assert rc == 2
    assert out == ""  # stdout sạch, KHÔNG có gì khi không --json và lỗi parse
    assert err != ""


def test_missing_required_arg_without_json_does_not_crash() -> None:
    rc, out, err = _run(["app", "inspect"])
    assert rc == 2
    assert out == ""


# ---------------------------------------------------------------------------
# subcommand chưa wiring (deps rỗng) → E_INTERNAL rõ ràng, KHÔNG giả "ok"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["catalog", "validate", "fixture.json", "--json"],
        ["app", "inspect", "fixture.json", "--json"],
        ["app", "plan-install", "fixture.json", "--json"],
        ["evidence", "validate", "fixture.json", "--json"],
    ],
)
def test_subcommands_without_wiring_return_internal_error_not_fake_ok(argv: list[str]) -> None:
    rc, out, _err = _run(argv, deps=CliDependencies())
    assert rc == ExitCode.INTERNAL
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["code"] == "E_INTERNAL"
    assert parsed["error"]["details"]["wired"] is False


def test_app_install_always_blocked_in_m1_even_with_full_wiring() -> None:
    # M1 gate: KHÔNG cài thật dù đã có đủ manifest_validator/install_planner.
    deps = CliDependencies(
        manifest_validator=FakeManifestValidator(), install_planner=FakeInstallPlanner()
    )
    rc, out, _err = _run(["app", "install", "plan-xyz", "--json"], deps=deps)
    assert rc == ExitCode.INTERNAL
    parsed = json.loads(out)
    assert parsed["error"]["details"]["blocked_external_dependency"] is True


# ---------------------------------------------------------------------------
# wiring thật (qua fake Protocol) — happy path
# ---------------------------------------------------------------------------


def test_app_inspect_with_wired_manifest_validator_returns_summary() -> None:
    deps = CliDependencies(manifest_validator=FakeManifestValidator())
    rc, out, _err = _run(["app", "inspect", "fixture.json", "--json"], deps=deps)
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["app_id"] == "app.test"
    assert parsed["data"]["mode"] == "native"


def test_app_inspect_propagates_loader_failure_as_input_schema_error() -> None:
    deps = CliDependencies(manifest_validator=FakeManifestValidator())
    rc, out, _err = _run(["app", "inspect", "__raise__", "--json"], deps=deps)
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"


def test_catalog_validate_install_not_ready_returns_error_envelope() -> None:
    deps = CliDependencies(
        manifest_validator=FakeManifestValidator(install_ready=False),
    )
    rc, out, _err = _run(["catalog", "validate", "fixture.json", "--json"], deps=deps)
    # fake: validate_semantic.ok == install_ready == False, errors=() (không
    # đồng nghĩa "giả danh ok") => dispatch PHẢI trả envelope lỗi, không ok giả.
    assert rc != ExitCode.OK
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["data"] is None


def test_catalog_validate_install_ready_true_returns_ok() -> None:
    deps = CliDependencies(manifest_validator=FakeManifestValidator(install_ready=True))
    rc, out, _err = _run(["catalog", "validate", "fixture.json", "--json"], deps=deps)
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["install_ready"] is True


def test_app_plan_install_happy_path_with_full_wiring() -> None:
    deps = CliDependencies(
        manifest_validator=FakeManifestValidator(install_ready=True),
        install_planner=FakeInstallPlanner(),
    )
    rc, out, _err = _run(["app", "plan-install", "fixture.json", "--json"], deps=deps)
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["plan_id"] == "plan-app.test"
    assert "tao-prefix" in parsed["data"]["changes"]


def test_app_plan_install_rejects_when_not_install_ready() -> None:
    deps = CliDependencies(
        manifest_validator=FakeManifestValidator(install_ready=False),
        install_planner=FakeInstallPlanner(),
    )
    rc, out, _err = _run(["app", "plan-install", "fixture.json", "--json"], deps=deps)
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["error"]["code"] == "E_SEMANTIC_TBD"


def test_evidence_validate_happy_path_returns_allowed_status() -> None:
    deps = CliDependencies(
        evidence_validator=FakeEvidenceValidator(allowed_status=CompatStatus.BLOCKED)
    )
    rc, out, _err = _run(["evidence", "validate", "fixture.json", "--json"], deps=deps)
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["allowed_status"] == "blocked"
    assert parsed["data"]["reasons_vi"]


def test_evidence_validate_never_task_verified_without_reviewer_in_fake_gate() -> None:
    deps = CliDependencies(
        evidence_validator=FakeEvidenceValidator(allowed_status=CompatStatus.EXPERIMENTAL)
    )
    rc, out, _err = _run(["evidence", "validate", "fixture.json", "--json"], deps=deps)
    parsed = json.loads(out)
    assert parsed["data"]["allowed_status"] != "task_verified"


def test_evidence_validate_loader_failure_is_input_schema_error() -> None:
    deps = CliDependencies(evidence_validator=FakeEvidenceValidator())
    rc, out, _err = _run(["evidence", "validate", "__raise__", "--json"], deps=deps)
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"


# ---------------------------------------------------------------------------
# envelope invariants chung — mọi nhánh
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["doctor", "--json"],
        ["khong-ton-tai", "--json"],
        ["catalog", "validate", "x.json", "--json"],
    ],
)
def test_every_json_branch_emits_exactly_one_parseable_json_line(argv: list[str]) -> None:
    rc, out, _err = _run(argv)
    assert out.count("\n") == 1
    parsed = json.loads(out)
    assert set(parsed.keys()) == {
        "api_version",
        "operation_id",
        "status",
        "data",
        "warnings",
        "error",
    }
    assert isinstance(rc, int)
    assert 0 <= rc <= 9
    assert rc != 1
