"""QA tester integration — ``namios evidence validate`` end-to-end THẬT
(``deps=None`` ⇒ wiring thật: ``EvidenceValidatorImpl`` của WP9).

Khẳng định bắt buộc: fixture task-verified → ok, allowed_status=task_verified;
fixture not-run (``contracts/sample-evidence-not-run.json``) → TỪ CHỐI,
KHÔNG được cấp ``task_verified``.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

# "G0-CLI" chứa dấu gạch ngang → không thể import tương đối; dùng path tuyệt
# đối trực tiếp (không chia sẻ module helper giữa các file trong thư mục này).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVIDENCE_DIR = _REPO_ROOT / "fixtures" / "evidence"
_CONTRACTS_DIR = _REPO_ROOT / "contracts"


def evidence_fixture_path(name: str) -> str:
    return str(_EVIDENCE_DIR / name)


def contracts_fixture_path(name: str) -> str:
    return str(_CONTRACTS_DIR / name)


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_evidence_validate_task_verified_fixture_is_allowed_task_verified() -> None:
    path = evidence_fixture_path("sample-task-verified.json")
    rc, out, err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.OK
    assert rc != 1
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "ok"
    assert parsed["data"]["allowed_status"] == "task_verified"
    assert parsed["data"]["reasons_vi"]


def test_evidence_validate_not_run_template_fixture_is_rejected_from_task_verified() -> None:
    """``contracts/sample-evidence-not-run.json``: mẫu CHƯA chạy (mọi test
    ``result=not_run``, ``qa_approval.reviewer=null``) — gate thật (WP9)
    TUYỆT ĐỐI KHÔNG được cấp ``task_verified`` dù ``decision`` trong file
    ghi 'pending' (nguồn sự thật là gate tính toán lại, không tin trường
    ``decision`` tự khai của report)."""

    path = contracts_fixture_path("sample-evidence-not-run.json")
    rc, out, err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["data"]["allowed_status"] != "task_verified"
    assert parsed["data"]["reasons_vi"]


def test_evidence_validate_missing_qa_reviewer_never_reaches_task_verified() -> None:
    path = evidence_fixture_path("sample-missing-qa-reviewer.json")
    rc, out, _err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    assert parsed["data"]["allowed_status"] != "task_verified"


def test_evidence_validate_nonexistent_path_is_input_error_not_crash() -> None:
    path = evidence_fixture_path("khong-ton-tai.json")
    rc, out, _err = _run(["evidence", "validate", path, "--json"])
    assert rc == ExitCode.INPUT
    assert rc != 1
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    assert path not in json.dumps(parsed, ensure_ascii=False)
