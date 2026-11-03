"""COMP-025 — Compatibility Resolver: 20 profile Gate A.

Bao mọi nhánh (feasibility theo license/mạng/chính sách, thứ tự điều tra,
never-usable) + hai bất biến nghiệm thu:
- Không mode verified cho tác vụ bắt buộc → ``no_verified_route=True``.
- Đổi app_version / token_model → chứng nhận mất hiệu lực (route rời khỏi
  verified) → không giữ "chạy được" bằng metadata cũ.
"""

from __future__ import annotations

import pytest

from namios_compat._types import (
    AppRef,
    Certification,
    ResolveInput,
    Route,
    Sector,
    WorkflowEntry,
)
from namios_compat.resolver import resolve_routes
from namios_eco.status import PublishedStatus as PS
from namios_eco.status import WindowsMode as WM
from namios_eco.workflow import WORKFLOW_STEP_ORDER


def _entry(
    routes: list[tuple[WM, PS]],
    *,
    app_version: str = "1.0",
    requires: tuple[str, ...] = (),
    device_models: tuple[str, ...] = (),
) -> WorkflowEntry:
    return WorkflowEntry(
        schema_version="1.0",
        workflow_id="w",
        sector=Sector.TAX,
        provider_id="p",
        region_scope="r",
        app=AppRef(id="a", version=app_version, architecture="x86_64"),
        required_steps=tuple(WORKFLOW_STEP_ORDER),
        requires=requires,
        routes=tuple(Route(mode=m, status=s.value) for m, s in routes),
        certification=Certification(device_models=device_models),
        last_updated="2026-11-03",
    )


def _inp(**kw: object) -> ResolveInput:
    base: dict[str, object] = {"workflow_id": "w", "app_id": "a", "app_version": "1.0"}
    base.update(kw)
    return ResolveInput(**base)  # type: ignore[arg-type]


# (name, entry, input, expected_recommended, expected_no_verified_route)
_PROFILES: list[tuple[str, WorkflowEntry, ResolveInput, WM | None, bool]] = [
    (
        "01-wine-verified-licensed",
        _entry([(WM.WINE, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=True),
        WM.WINE,
        False,
    ),
    (
        "02-native-verified",
        _entry([(WM.NATIVE_LINUX, PS.WORKFLOW_VERIFIED)]),
        _inp(),
        WM.NATIVE_LINUX,
        False,
    ),
    (
        "03-web-verified-offline",
        _entry([(WM.WEB_LINUX, PS.WORKFLOW_VERIFIED)]),
        _inp(network_online=False),
        None,
        False,
    ),
    (
        "04-wine-verified-no-license",
        _entry([(WM.WINE, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=False),
        None,
        False,
    ),
    (
        "05-remote-verified-no-policy",
        _entry([(WM.REMOTE_WINDOWS, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=True, network_online=True, org_policy_allows_remote=False),
        None,
        False,
    ),
    (
        "06-all-not-inventoried",
        _entry([(WM.WINE, PS.NOT_INVENTORIED), (WM.WEB_LINUX, PS.NOT_INVENTORIED)]),
        _inp(),
        None,
        True,
    ),
    (
        "07-partial-only",
        _entry([(WM.WINE, PS.PARTIAL_WORKFLOW)]),
        _inp(license_ok=True),
        None,
        True,
    ),
    ("08-blocked", _entry([(WM.WEB_LINUX, PS.BLOCKED_EXTERNAL_DEPENDENCY)]), _inp(), None, True),
    (
        "09-wine-verified-app-version-changed",
        _entry([(WM.WINE, PS.WORKFLOW_VERIFIED)], app_version="2.0"),
        _inp(app_version="2.1", license_ok=True),
        None,
        True,
    ),
    (
        "10-wine-verified-app-version-match",
        _entry([(WM.WINE, PS.WORKFLOW_VERIFIED)], app_version="2.0"),
        _inp(app_version="2.0", license_ok=True),
        WM.WINE,
        False,
    ),
    (
        "11-signing-token-changed",
        _entry(
            [(WM.WINE, PS.WORKFLOW_VERIFIED)],
            requires=("signing_method",),
            device_models=("TOK-A",),
        ),
        _inp(license_ok=True, token_model="TOK-B"),
        None,
        True,
    ),
    (
        "12-signing-token-match",
        _entry(
            [(WM.WINE, PS.WORKFLOW_VERIFIED)],
            requires=("signing_method",),
            device_models=("TOK-A",),
        ),
        _inp(license_ok=True, token_model="TOK-A"),
        WM.WINE,
        False,
    ),
    (
        "13-native-and-wine-verified-prefers-native",
        _entry([(WM.NATIVE_LINUX, PS.WORKFLOW_VERIFIED), (WM.WINE, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=True),
        WM.NATIVE_LINUX,
        False,
    ),
    (
        "14-downloadable-only",
        _entry([(WM.WINE, PS.DOWNLOADABLE_ONLY)]),
        _inp(license_ok=True),
        None,
        True,
    ),
    ("15-launches-only", _entry([(WM.WINE, PS.LAUNCHES_ONLY)]), _inp(license_ok=True), None, True),
    (
        "16-web-verified-online",
        _entry([(WM.WEB_LINUX, PS.WORKFLOW_VERIFIED)]),
        _inp(network_online=True),
        WM.WEB_LINUX,
        False,
    ),
    (
        "17-vm-verified",
        _entry([(WM.WINDOWS_VM, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=True, org_policy_allows_remote=True),
        WM.WINDOWS_VM,
        False,
    ),
    (
        "18-remote-verified",
        _entry([(WM.REMOTE_WINDOWS, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=True, network_online=True, org_policy_allows_remote=True),
        WM.REMOTE_WINDOWS,
        False,
    ),
    ("19-unsupported", _entry([(WM.WINE, PS.UNSUPPORTED)]), _inp(license_ok=True), None, True),
    (
        "20-web-partial-wine-verified",
        _entry([(WM.WEB_LINUX, PS.PARTIAL_WORKFLOW), (WM.WINE, PS.WORKFLOW_VERIFIED)]),
        _inp(license_ok=True),
        WM.WINE,
        False,
    ),
]


@pytest.mark.parametrize(
    ("name", "entry", "inp", "rec", "no_verified"),
    _PROFILES,
    ids=[p[0] for p in _PROFILES],
)
def test_gate_a_profiles(
    name: str, entry: WorkflowEntry, inp: ResolveInput, rec: WM | None, no_verified: bool
) -> None:
    res = resolve_routes(inp, entry)
    assert res.recommended == rec, f"{name}: recommended {res.recommended} != {rec}"
    assert res.no_verified_route == no_verified, f"{name}: no_verified {res.no_verified_route}"
    # Luôn có đủ 5 mode trong kết quả, đúng thứ tự điều tra.
    assert tuple(c.mode for c in res.candidates) == (
        WM.NATIVE_LINUX,
        WM.WEB_LINUX,
        WM.WINE,
        WM.REMOTE_WINDOWS,
        WM.WINDOWS_VM,
    )


def test_profiles_count_is_twenty() -> None:
    assert len(_PROFILES) == 20


def test_never_recommend_never_usable() -> None:
    # Bất biến ECO-003: downloadable/launches không bao giờ được đề xuất.
    for status in (PS.DOWNLOADABLE_ONLY, PS.LAUNCHES_ONLY):
        res = resolve_routes(_inp(license_ok=True), _entry([(WM.WINE, status)]))
        assert res.recommended is None
        assert res.no_verified_route is True


def test_reasons_present() -> None:
    res = resolve_routes(_inp(), _entry([(WM.WINE, PS.NOT_INVENTORIED)]))
    assert res.reasons_vi and all(isinstance(r, str) and r for r in res.reasons_vi)
