"""PRA-016/017 — Office route + fidelity gate."""

from __future__ import annotations

from namios_pra import (
    FidelityIssue,
    FidelitySeverity,
    OfficeNeed,
    OfficeRoute,
    fidelity_gate,
    is_fidelity_blocked,
    resolve_office_route,
)

N = OfficeNeed


def test_macro_never_routes_to_web() -> None:
    # Nghiệm thu PRA-016: .xlsm cần macro KHÔNG được gán Office web.
    r = resolve_office_route([N.EDIT, N.MACRO], has_native_support=True, web_available=True)
    assert r.route is OfficeRoute.WINDOWS_VM
    assert r.windows_dependent is True
    assert r.route is not OfficeRoute.MS365_WEB


def test_addin_also_windows() -> None:
    r = resolve_office_route([N.ADDIN], web_available=True)
    assert r.route is OfficeRoute.WINDOWS_VM


def test_sign_needs_windows() -> None:
    r = resolve_office_route([N.EDIT, N.SIGN])
    assert r.route is OfficeRoute.WINDOWS_VM and r.windows_dependent is True


def test_read_only_prefers_native_then_viewer() -> None:
    assert resolve_office_route([N.READ], has_native_support=True).route is OfficeRoute.NATIVE_LINUX
    assert (
        resolve_office_route([N.READ], has_native_support=False).route
        is OfficeRoute.VIEWER_READONLY
    )


def test_edit_native_then_web_then_blocked() -> None:
    assert resolve_office_route([N.EDIT], has_native_support=True).route is OfficeRoute.NATIVE_LINUX
    assert (
        resolve_office_route([N.EDIT], has_native_support=False, web_available=True).route
        is OfficeRoute.MS365_WEB
    )
    assert (
        resolve_office_route([N.EDIT], has_native_support=False, web_available=False).route
        is OfficeRoute.BLOCKED
    )


def test_fidelity_blocking_blocks_save_print() -> None:
    # Nghiệm thu PRA-017: sai tổng tiền → fail dù file mở được.
    issues = [FidelityIssue("tong_tien", FidelitySeverity.BLOCKING, "lệch 1000đ")]
    assert is_fidelity_blocked(issues) is True
    ok, reason = fidelity_gate(issues)
    assert ok is False and "tong_tien" in reason


def test_fidelity_info_only_passes() -> None:
    issues = [FidelityIssue("font", FidelitySeverity.INFO, "thay font")]
    assert is_fidelity_blocked(issues) is False
    ok, _ = fidelity_gate(issues)
    assert ok is True


def test_fidelity_empty_passes() -> None:
    assert fidelity_gate([])[0] is True
