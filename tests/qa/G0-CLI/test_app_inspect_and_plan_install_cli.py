"""QA tester integration — ``namios app inspect`` / ``namios app
plan-install`` end-to-end THẬT (``deps=None`` ⇒ wiring thật: WP2 + WP6/WP10)."""

from __future__ import annotations

import io
import json
from pathlib import Path

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

# "G0-CLI" chứa dấu gạch ngang → không thể import tương đối; dùng path tuyệt
# đối trực tiếp (không chia sẻ module helper giữa các file trong thư mục này).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_INTEGRATION_MANIFEST_DIR = _REPO_ROOT / "tests" / "integration" / "fixtures" / "manifest"


def integration_manifest_fixture_path(name: str) -> str:
    return str(_INTEGRATION_MANIFEST_DIR / name)


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_app_inspect_valid_manifest_returns_summary_single_line_json() -> None:
    path = integration_manifest_fixture_path("valid-demo-app.json")
    rc, out, err = _run(["app", "inspect", path, "--json"])
    assert rc == ExitCode.OK
    assert rc != 1
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "ok"
    assert parsed["data"]["app_id"] == "demo-app"
    assert parsed["data"]["mode"] == "native"


def test_app_plan_install_valid_manifest_builds_plan_ok() -> None:
    path = integration_manifest_fixture_path("valid-demo-app.json")
    rc, out, err = _run(["app", "plan-install", path, "--json"])
    assert rc == ExitCode.OK
    assert rc != 1
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["data"]["app_id"] == "demo-app"
    assert parsed["data"]["plan_id"]


def test_app_plan_install_tbd_manifest_is_blocked_with_semantic_tbd() -> None:
    path = integration_manifest_fixture_path("not-ready-tbd-app.json")
    rc, out, _err = _run(["app", "plan-install", path, "--json"])
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["code"] == "E_SEMANTIC_TBD"


def test_app_install_is_always_blocked_at_this_host_m1_gate() -> None:
    """M1 gate cố ý (FACT CLAUDE.md): cài thật là M2, BLOCKED tại host này
    dù wiring đủ — ``app install`` KHÔNG BAO GIỜ trả ``ok`` giả."""

    rc, out, _err = _run(["app", "install", "some-plan-id", "--json"])
    assert rc != ExitCode.OK
    assert rc != 1
    assert 0 <= rc <= 9
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["details"]["blocked_external_dependency"] is True
