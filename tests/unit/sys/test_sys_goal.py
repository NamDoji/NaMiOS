"""SYS-030 — mục tiêu → kết quả trung thực: máy in offline KHÔNG "đã in xong"."""

from __future__ import annotations

from namios_sys import ActionStatus, RunState, goal_outcome, plan_goal

AS = ActionStatus


def test_plan_missing_resources_asks() -> None:
    pg = plan_goal("in bảng lương", required=["app", "file", "printer"], provided={"app": "writer"})
    assert pg.ready is False
    assert set(pg.missing) == {"file", "printer"}
    assert pg.resolved == {"app": "writer"}


def test_plan_all_provided_ready() -> None:
    pg = plan_goal(
        "in bảng lương",
        required=["app", "file", "printer"],
        provided={"app": "writer", "file": "bl.xlsx", "printer": "HP-01"},
    )
    assert pg.ready is True and pg.missing == ()


def test_printer_offline_blocked_not_done() -> None:
    # Nghiệm thu SYS-030: máy in offline → BLOCKED (partial/blocked), KHÔNG "đã in xong".
    state, reason = goal_outcome("in bảng lương", [AS.SUCCESS, AS.BLOCKED], evidence_ids=("e1",))
    assert state is RunState.BLOCKED
    assert "xong" not in reason.lower() or "CHƯA" in reason


def test_failed_step_is_failed() -> None:
    state, _ = goal_outcome("in bảng lương", [AS.SUCCESS, AS.FAILED])
    assert state is RunState.FAILED


def test_success_without_evidence_is_partial() -> None:
    # "mở được"/chạy xong nhưng thiếu bằng chứng → chưa hoàn thành.
    state, _ = goal_outcome("in bảng lương", [AS.SUCCESS], evidence_ids=())
    assert state is RunState.PARTIAL


def test_business_requires_confirm_partial_until_confirmed() -> None:
    s1, _ = goal_outcome(
        "in bảng lương",
        [AS.SUCCESS],
        evidence_ids=("job1",),
        business_requires_confirm=True,
        user_confirmed=False,
    )
    assert s1 is RunState.PARTIAL
    s2, _ = goal_outcome(
        "in bảng lương",
        [AS.SUCCESS],
        evidence_ids=("job1",),
        business_requires_confirm=True,
        user_confirmed=True,
    )
    assert s2 is RunState.VERIFIED


def test_all_success_with_evidence_verified() -> None:
    state, reason = goal_outcome("in bảng lương", [AS.SUCCESS, AS.SUCCESS], evidence_ids=("job1",))
    assert state is RunState.VERIFIED and "hoàn thành" in reason


def test_no_steps_proposed() -> None:
    assert goal_outcome("x", [])[0] is RunState.PROPOSED
