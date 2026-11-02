"""Integration — ``namios evidence validate`` end-to-end với implementation
THẬT (``EvidenceValidatorImpl`` của WP9, qua ``default_dependencies()`` khi
``main()`` không được truyền ``deps``). Dùng fixtures CHUNG đã có sẵn trong
repo ``fixtures/evidence/**`` (WP9) — KHÔNG tự chế fixture mới, KHÔNG fake.
"""

from __future__ import annotations

import io
import json

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

from ._paths import evidence_fixture_path


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_evidence_validate_task_verified_report_is_allowed_task_verified() -> None:
    """``sample-task-verified.json``: mọi test required pass + có
    qa_reviewer thật → gate thật (WP9) PHẢI trả ``task_verified``."""

    path = evidence_fixture_path("sample-task-verified.json")
    rc, out, err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["data"]["report_id"] == "run-2026-11-02-misa-sme-wine-01"
    assert parsed["data"]["manifest_id"] == "misa-sme-wine"
    assert parsed["data"]["allowed_status"] == "task_verified"
    assert parsed["data"]["reasons_vi"]


def test_evidence_validate_required_test_fail_is_rejected_from_task_verified() -> None:
    """``sample-required-fail.json``: một test required=true có result='fail'
    → gate thật PHẢI từ chối task_verified (tối đa 'blocked'), KHÔNG lỗi/crash
    (lệnh ``validate`` vẫn ``status=ok``, chỉ ``allowed_status`` thấp hơn)."""

    path = evidence_fixture_path("sample-required-fail.json")
    rc, out, err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["data"]["allowed_status"] == "blocked"
    assert parsed["data"]["allowed_status"] != "task_verified"
    assert parsed["data"]["reasons_vi"]


def test_evidence_validate_missing_qa_reviewer_is_rejected_from_task_verified() -> None:
    """``sample-missing-qa-reviewer.json``: test required pass nhưng
    ``qa_approval.reviewer`` null → gate thật PHẢI từ chối task_verified
    (tối đa 'experimental') dù mọi test đã pass — đúng bất biến §11.2
    "task_verified chỉ khi có QA phê duyệt độc lập"."""

    path = evidence_fixture_path("sample-missing-qa-reviewer.json")
    rc, out, err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["allowed_status"] == "experimental"
    assert parsed["data"]["allowed_status"] != "task_verified"


def test_evidence_validate_unknown_key_fails_schema_layer_exit_input() -> None:
    """``sample-unknown-key.json``: khóa lạ ``trusted_by_vendor`` KHÔNG được
    tầng 1 (schema) chấp nhận — load() thật phải raise, CLI chuẩn hoá về
    ``E_INPUT_SCHEMA``/exit 2, không crash."""

    path = evidence_fixture_path("sample-unknown-key.json")
    rc, out, err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
