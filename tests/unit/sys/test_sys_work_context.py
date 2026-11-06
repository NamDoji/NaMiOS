"""SYS-029 — WorkContext: SmartAI chỉ đọc tài nguyên đã cấp (deny-by-default)."""

from __future__ import annotations

from namios_sys import ContextResource, ResourceKind, WorkContext


def _win(i: str) -> ContextResource:
    return ContextResource(ResourceKind.WINDOW, i)


def test_default_empty_denies_all() -> None:
    ctx = WorkContext()
    assert ctx.can_access(_win("A")) is False
    assert ctx.granted() == ()


def test_two_windows_only_granted_is_readable() -> None:
    # Nghiệm thu SYS-029: cấp cửa sổ A → đọc A được, cửa sổ B chưa cấp thì KHÔNG.
    ctx = WorkContext()
    ctx.grant(_win("A"))
    assert ctx.can_access(_win("A")) is True
    assert ctx.can_access(_win("B")) is False
    assert ctx.read(_win("B")) is None
    assert ctx.read(_win("A")) == _win("A")


def test_kind_scoped_not_crossing() -> None:
    # Cấp FILE 'x' không mở WINDOW 'x' (khác loại tài nguyên).
    ctx = WorkContext()
    ctx.grant(ContextResource(ResourceKind.FILE, "x"))
    assert ctx.can_access(ContextResource(ResourceKind.FILE, "x")) is True
    assert ctx.can_access(ContextResource(ResourceKind.WINDOW, "x")) is False


def test_revoke_closes_access() -> None:
    ctx = WorkContext()
    a = _win("A")
    ctx.grant(a)
    ctx.revoke(a)
    assert ctx.can_access(a) is False


def test_granted_is_transparent_and_stable() -> None:
    ctx = WorkContext()
    ctx.grant(_win("B"))
    ctx.grant(_win("A"))
    ctx.grant(ContextResource(ResourceKind.DEVICE, "printer0"))
    g = ctx.granted()
    assert len(g) == 3
    assert g == tuple(sorted(g, key=lambda r: (r.kind, r.resource_id)))
