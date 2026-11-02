"""Integration — ``namios app inspect`` end-to-end với ``ManifestValidatorImpl``
thật (qua ``default_dependencies()`` khi ``main()`` không được truyền ``deps``)."""

from __future__ import annotations

import io
import json

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

from ._paths import manifest_fixture_path


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_app_inspect_real_manifest_returns_summary() -> None:
    path = manifest_fixture_path("valid-demo-app.json")
    rc, out, err = _run(["app", "inspect", path, "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["data"] == {
        "app_id": "demo-app",
        "name": "Demo App",
        "publisher": "Demo Publisher",
        "mode": "native",
        "compatibility_status": "untested",
    }


def test_app_inspect_nonexistent_path_is_input_error_not_crash() -> None:
    path = manifest_fixture_path("khong-ton-tai.json")
    rc, out, err = _run(["app", "inspect", path, "--json"])
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    # Không lộ đường dẫn tuyệt đối thật ra envelope.
    assert path not in json.dumps(parsed, ensure_ascii=False)
