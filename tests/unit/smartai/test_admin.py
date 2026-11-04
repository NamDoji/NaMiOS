"""SAI-037 — Multiuser Administration: phân quyền theo đơn vị."""

from __future__ import annotations

from namios_smartai._types import Principal, UnitPolicy
from namios_smartai.admin import can_approve_r3_r4, can_edit_policy, can_read_logs

_ACCT = UnitPolicy(
    unit_id="ketoan",
    admin_users=("ke_toan_truong",),
    approve_r3_r4_users=("ke_toan_truong",),
    log_collection=True,
)


def test_cross_unit_cannot_edit_policy() -> None:
    # Giáo viên đơn vị 'truong' KHÔNG sửa được chính sách kế toán.
    teacher = Principal(user_id="gv1", unit_id="truong", roles=("admin",))
    assert can_edit_policy(teacher, _ACCT) is False


def test_same_unit_admin_can_edit_and_approve() -> None:
    admin = Principal(user_id="ke_toan_truong", unit_id="ketoan", roles=("admin",))
    assert can_edit_policy(admin, _ACCT)
    assert can_approve_r3_r4(admin, _ACCT)


def test_non_admin_same_unit_cannot_edit() -> None:
    staff = Principal(user_id="nv1", unit_id="ketoan", roles=("user",))
    assert can_edit_policy(staff, _ACCT) is False


def test_helpdesk_reads_logs_only_when_permitted_and_same_unit() -> None:
    hd = Principal(user_id="hd", unit_id="ketoan", roles=("helpdesk",))
    assert can_read_logs(hd, _ACCT)  # cùng đơn vị + log_collection bật
    no_log = UnitPolicy(unit_id="ketoan", log_collection=False)
    assert can_read_logs(hd, no_log) is False  # đơn vị tắt thu-log
    cross = Principal(user_id="hd2", unit_id="truong", roles=("helpdesk",))
    assert can_read_logs(cross, _ACCT) is False  # khác đơn vị
