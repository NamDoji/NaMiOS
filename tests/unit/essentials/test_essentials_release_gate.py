"""APP11-036 — cổng phát hành. Không phát hành nếu IME/Office/browser/Security
Center/rollback P0 lỗi; không ghi "đã cài app Linux" cho shortcut web; 6 dịch
vụ web phải kiểm trên browser ship + máy pilot."""

from __future__ import annotations

from namios_essentials import DeliveryType, EssentialsManifest, Provenance
from namios_essentials.release_gate import (
    P0_GATE_KEYS,
    REQUIRED_WEB_SERVICES,
    evaluate_release_gate,
)

DT = DeliveryType


def _all_p0_pass() -> dict[str, bool]:
    return dict.fromkeys(P0_GATE_KEYS, True)


def _all_web_pass() -> dict[str, bool]:
    return dict.fromkeys(REQUIRED_WEB_SERVICES, True)


def _good_native_manifest() -> EssentialsManifest:
    return EssentialsManifest(
        id="namios-office",
        title="NaMi Office",
        publisher="NaMiOS",
        category="lam_viec",
        delivery_type=DT.INSTALLED_NATIVE,
        package_source=Provenance(official=True, sha256="abc", signature_ok=True),
        license="MPL-2.0",
        owner="team",
        last_verified="2026-11-06",
    )


def _good_web_manifest() -> EssentialsManifest:
    return EssentialsManifest(
        id="zalo.web",
        title="Zalo Web",
        publisher="Zalo",
        category="lien_lac",
        delivery_type=DT.OFFICIAL_WEB,
        official_url="https://id.zalo.me/",
        owner="team",
        last_verified="2026-11-06",
    )


def test_fully_passing_release_is_shippable() -> None:
    result = evaluate_release_gate(
        [_good_native_manifest(), _good_web_manifest()], _all_p0_pass(), _all_web_pass()
    )
    assert result.shippable is True
    assert result.blockers == ()


def test_ime_failure_blocks_release() -> None:
    p0 = _all_p0_pass()
    p0["ime"] = False
    result = evaluate_release_gate([_good_native_manifest()], p0, _all_web_pass())
    assert result.shippable is False
    assert any("ime" in b for b in result.blockers)


def test_each_p0_key_individually_blocks() -> None:
    for key in P0_GATE_KEYS:
        p0 = _all_p0_pass()
        p0[key] = False
        result = evaluate_release_gate([], p0, _all_web_pass())
        assert result.shippable is False, key


def test_missing_web_smoke_test_blocks_release() -> None:
    web = _all_web_pass()
    web["zalo_web"] = False
    result = evaluate_release_gate([], _all_p0_pass(), web)
    assert result.shippable is False
    assert any("zalo_web" in b for b in result.blockers)


def test_unshippable_manifest_blocks_release() -> None:
    bad = EssentialsManifest(
        id="bad-app",
        title="Bad",
        publisher="X",
        category="c",
        delivery_type=DT.INSTALLED_NATIVE,
        package_source=None,  # thiếu nguồn
    )
    result = evaluate_release_gate([bad], _all_p0_pass(), _all_web_pass())
    assert result.shippable is False
    assert any("bad-app" in b for b in result.blockers)


def test_misleading_web_display_text_blocks_release() -> None:
    web_manifest = _good_web_manifest()
    result = evaluate_release_gate(
        [web_manifest],
        _all_p0_pass(),
        _all_web_pass(),
        web_display_texts={"zalo.web": "Zalo đã cài trên máy"},
    )
    assert result.shippable is False
    assert any("zalo.web" in b for b in result.blockers)


def test_honest_web_display_text_does_not_block() -> None:
    web_manifest = _good_web_manifest()
    result = evaluate_release_gate(
        [web_manifest],
        _all_p0_pass(),
        _all_web_pass(),
        web_display_texts={"zalo.web": "Zalo Web"},
    )
    assert result.shippable is True
