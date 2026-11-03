"""COMP-050 — CLI ``namios compat`` chạy thật qua ``main()`` (không fake).

Dùng chung đầu ra JSON envelope với các subcommand khác; trạng thái shipped
phải TRUNG THỰC (no_verified_route cho catalog chưa test)."""

from __future__ import annotations

import io
import json

from namios_cli.main import main


def _run(*argv: str) -> dict:
    # ``--json`` là cờ của leaf (đặt SAU subcommand), không phải cờ toàn cục.
    out, err = io.StringIO(), io.StringIO()
    code = main([*argv, "--json"], stdout=out, stderr=err)
    payload = json.loads(out.getvalue())
    payload["_exit"] = code
    return payload


def test_workflows_lists_honest_catalog() -> None:
    env = _run("compat", "workflows")
    assert env["status"] == "ok"
    assert env["_exit"] == 0
    assert env["data"]["count"] >= 6
    # Trung thực: catalog shipped chưa có workflow nào kiểm chứng end-to-end.
    assert env["data"]["end_to_end_verified"] == 0
    assert env["warnings"]


def test_route_honest_no_verified() -> None:
    env = _run("compat", "route", "vn.tax.sample_submission")
    assert env["status"] == "ok"
    assert env["data"]["no_verified_route"] is True
    assert env["data"]["recommended"] is None
    assert len(env["data"]["candidates"]) == 5
    assert env["warnings"]  # cảnh báo không kết luận chạy được


def test_route_not_found_exit_2() -> None:
    env = _run("compat", "route", "vn.nope.missing")
    assert env["status"] == "error"
    assert env["error"]["code"] == "E_INPUT_SCHEMA"
    assert env["_exit"] == 2


def test_preflight_lists_requires() -> None:
    env = _run("compat", "preflight", "vn.bhxh.monthly_filing")
    assert env["status"] == "ok"
    assert "signing_method" in env["data"]["requires"]
    assert env["data"]["modes"]


def test_evidence_honest_empty() -> None:
    env = _run("compat", "evidence", "vn.tax.sample_submission")
    assert env["status"] == "ok"
    assert env["data"]["evidence_ids"] == []
    assert env["data"]["technical_status"] == "not_inventoried"


def test_blocker_has_note() -> None:
    env = _run("compat", "blocker", "vn.vertical.sample_lob")
    assert env["status"] == "ok"
    assert env["data"]["note_vi"]
