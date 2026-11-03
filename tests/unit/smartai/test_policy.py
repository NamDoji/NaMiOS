"""SAI-039/017 — policy-as-code: deny ưu tiên, R4 cần xác nhận giao dịch,
leo thang rủi ro cần consent+capability, đổi mục tiêu vô hiệu consent."""

from __future__ import annotations

from namios_smartai._types import (
    CapabilityToken,
    ConsentRecord,
    PolicyContext,
    PolicyEffect,
    PolicyRule,
    RiskTier,
)
from namios_smartai.policy import evaluate


def _ctx(**kw: object) -> PolicyContext:
    base: dict[str, object] = {"action": "do", "risk": RiskTier.R0, "target": "app"}
    base.update(kw)
    return PolicyContext(**base)  # type: ignore[arg-type]


def test_r0_r1_allow_without_consent() -> None:
    assert evaluate(_ctx(action="inspect_app", risk=RiskTier.R0)).effect == PolicyEffect.ALLOW
    assert evaluate(_ctx(action="run_test", risk=RiskTier.R1)).effect == PolicyEffect.ALLOW


def test_r2_needs_consent_and_capability() -> None:
    assert evaluate(_ctx(action="install_test", risk=RiskTier.R2)).effect == PolicyEffect.DENY
    cons = ConsentRecord(scope=("app",), target_fingerprint="app")
    # consent nhưng thiếu capability
    assert evaluate(_ctx(risk=RiskTier.R2, consent=cons)).effect == PolicyEffect.DENY
    cap = CapabilityToken(token_id="t", subject="app", risk_tier=RiskTier.R2)
    assert (
        evaluate(_ctx(risk=RiskTier.R2, consent=cons, capability=cap)).effect == PolicyEffect.ALLOW
    )


def test_r4_requires_transaction_confirmation() -> None:
    blanket = ConsentRecord(scope=("all",), target_fingerprint="app")  # "cứ làm đi"
    assert (
        evaluate(_ctx(action="submit", risk=RiskTier.R4, consent=blanket)).effect
        == PolicyEffect.DENY
    )
    confirmed = ConsentRecord(
        scope=("submit",), transaction_confirmed=True, target_fingerprint="app"
    )
    assert (
        evaluate(_ctx(action="submit", risk=RiskTier.R4, consent=confirmed)).effect
        == PolicyEffect.ALLOW
    )


def test_r4_no_consent_denied() -> None:
    assert evaluate(_ctx(action="submit", risk=RiskTier.R4)).effect == PolicyEffect.DENY


def test_target_change_voids_consent() -> None:
    stale = ConsentRecord(scope=("all",), transaction_confirmed=True, target_fingerprint="old")
    d = evaluate(_ctx(action="install", risk=RiskTier.R2, target="new", consent=stale))
    assert d.effect == PolicyEffect.DENY
    assert d.rule_id == "consent.target_changed"


def test_deny_rule_priority() -> None:
    rules = (
        PolicyRule(
            rule_id="org.block_inspect", effect=PolicyEffect.DENY, when={"action": "inspect_app"}
        ),
    )
    assert evaluate(_ctx(action="inspect_app", risk=RiskTier.R0), rules).effect == PolicyEffect.DENY


def test_expired_consent_denied_for_r2() -> None:
    expired = ConsentRecord(scope=("app",), target_fingerprint="app", expires_at="2020-01-01")
    cap = CapabilityToken(token_id="t", subject="app", risk_tier=RiskTier.R2)
    d = evaluate(_ctx(risk=RiskTier.R2, consent=expired, capability=cap, now="2026-11-04"))
    assert d.effect == PolicyEffect.DENY


def test_capability_risk_ceiling() -> None:
    cons = ConsentRecord(scope=("app",), target_fingerprint="app")
    weak = CapabilityToken(token_id="t", subject="app", risk_tier=RiskTier.R1)  # < R2
    d = evaluate(_ctx(risk=RiskTier.R2, consent=cons, capability=weak))
    assert d.effect == PolicyEffect.DENY


def test_revoked_and_onetime_capability() -> None:
    cons = ConsentRecord(scope=("app",), target_fingerprint="app")
    revoked = CapabilityToken(token_id="t", subject="app", risk_tier=RiskTier.R2, revoked=True)
    assert (
        evaluate(_ctx(risk=RiskTier.R2, consent=cons, capability=revoked)).effect
        == PolicyEffect.DENY
    )
    used = CapabilityToken(
        token_id="t", subject="app", risk_tier=RiskTier.R2, one_time=True, used=True
    )
    assert (
        evaluate(_ctx(risk=RiskTier.R2, consent=cons, capability=used)).effect == PolicyEffect.DENY
    )
