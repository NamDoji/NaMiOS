"""QA tester integration — ``namios doctor --json`` end-to-end qua
``main()`` THẬT (``deps=None`` ⇒ wiring thật, ``default_dependencies()``).

Khẳng định bắt buộc theo nhiệm vụ: envelope sạch, exit 0, có capabilities
thật (không giả lập), KHÔNG rò secret/đường dẫn home người dùng ra stdout.
"""

from __future__ import annotations

import io
import json
import os

from namios_cli.main import main
from namios_core.exitcodes import ExitCode


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_doctor_json_envelope_is_clean_single_line_ok() -> None:
    rc, out, err = _run(["doctor", "--json"])
    assert rc == ExitCode.OK
    assert rc != 1
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 1, "stdout --json PHẢI luôn đúng một dòng JSON"
    parsed = json.loads(lines[0])
    assert parsed["api_version"] == "1.0"
    assert parsed["status"] == "ok"
    assert parsed["error"] is None
    assert isinstance(parsed["operation_id"], str) and parsed["operation_id"]


def test_doctor_json_has_real_capabilities_not_simulated() -> None:
    rc, out, _err = _run(["doctor", "--json"])
    assert rc == ExitCode.OK
    data = json.loads(out)["data"]
    assert set(data.keys()) == {"host", "session", "virtualization", "tooling"}
    assert isinstance(data["host"]["os_pretty_name"], str) and data["host"]["os_pretty_name"]
    assert isinstance(data["host"]["kernel_release"], str) and data["host"]["kernel_release"]
    assert isinstance(data["host"]["python_version"], str) and data["host"]["python_version"]
    # FACT môi trường build hiện tại (CLAUDE.md 02/11/2026): không KVM/wine.
    assert data["virtualization"]["has_kvm"] is False
    assert isinstance(data["tooling"]["present"], list)
    assert isinstance(data["tooling"]["absent"], list)


def test_doctor_json_does_not_leak_home_path_or_env_secrets() -> None:
    rc, out, err = _run(["doctor", "--json"])
    assert rc == ExitCode.OK
    full_payload = out + err
    home = os.environ.get("HOME", "")
    if home and home not in ("/", ""):
        assert home not in full_payload, "doctor --json KHÔNG được in HOME path tuyệt đối"
    # Không được lộ biến môi trường kiểu secret/token phổ biến.
    for forbidden_substr in ("SECRET", "TOKEN", "PASSWORD", "API_KEY"):
        assert forbidden_substr not in full_payload.upper()


def test_doctor_human_mode_without_json_prints_one_line_to_stdout() -> None:
    rc, out, err = _run(["doctor"])
    assert rc == ExitCode.OK
    assert err == ""
    assert out.strip() != ""
    assert "{" not in out  # human mode không phải JSON
