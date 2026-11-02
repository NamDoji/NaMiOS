"""Integration — ``namios doctor`` end-to-end qua ``main()`` thật, KHÔNG
``deps`` (``deps=None`` ⇒ không áp dụng với doctor — doctor luôn hiện thực
đầy đủ ngay trong WP3, không đi qua ``CliDependencies``). Giữ ở đây để test
tích hợp bao trùm luôn case đơn giản nhất của "chạy lệnh thật end-to-end".
"""

from __future__ import annotations

import io
import json

from namios_cli.main import main
from namios_core.exitcodes import ExitCode


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None mặc định
    return rc, out.getvalue(), err.getvalue()


def test_doctor_json_end_to_end_single_envelope_exit_zero() -> None:
    rc, out, err = _run(["doctor", "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "ok"
    assert parsed["error"] is None
    assert set(parsed["data"].keys()) == {"host", "session", "virtualization", "tooling"}
    assert isinstance(parsed["data"]["virtualization"]["has_kvm"], bool)
    # FACT môi trường build hiện tại (CLAUDE.md 02/11/2026): /dev/kvm vắng.
    assert parsed["data"]["virtualization"]["has_kvm"] is False
