"""SAI-034 — Observability: phân biệt nguồn lỗi + trace không lộ credential."""

from __future__ import annotations

from namios_smartai._types import TraceErrorClass as EC
from namios_smartai._types import TraceEvent
from namios_smartai.observability import Trace, classify_error_source


def test_classify_five_sources() -> None:
    assert classify_error_source("policy deny consent") == EC.POLICY
    assert classify_error_source("tool schema fail-closed") == EC.TOOL
    assert classify_error_source("vendor sdk driver missing") == EC.VENDOR
    assert classify_error_source("portal activex plugin") == EC.PORTAL
    assert classify_error_source("model returned bad json") == EC.MODEL


def test_classify_none_and_unknown() -> None:
    assert classify_error_source("") == EC.NONE
    assert classify_error_source("điều gì đó không rõ") == EC.UNKNOWN


def test_trace_record_redacts_note() -> None:
    tr = Trace()
    tr.record(
        TraceEvent(
            event_id="e1",
            plan_id="p1",
            action_id="submit",
            policy_decision="deny",
            tool="submit",
            result="blocked",
            error_class=EC.POLICY,
            note="password=TopSecret ghp_ABCDEF123456",
        )
    )
    blob = str(tr.events())
    assert "TopSecret" not in blob and "ghp_ABCDEF123456" not in blob


def test_reject_reasons_surfaced() -> None:
    tr = Trace()
    tr.record(TraceEvent("e1", "p1", "submit", "deny", "submit", "blocked", error_class=EC.POLICY))
    tr.record(TraceEvent("e2", "p1", "preflight", "allow", "preflight", "success"))
    rr = tr.reject_reasons()
    assert len(rr) == 1 and rr[0][0] == "submit" and rr[0][1] == "policy"
