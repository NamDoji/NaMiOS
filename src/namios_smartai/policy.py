"""Policy-as-Code (SAI-039 / SAI-017).

Quy tắc allow/deny TÁCH KHỎI prompt, quyết định trên ``PolicyContext`` tất
định (action/risk/target/capability/consent/org/stage). **deny ưu tiên.** AI
KHÔNG sửa được policy từ câu chat (policy là dữ liệu + mã, không phải prompt).

Bất biến then chốt:
- R4 (ký/nộp/thanh toán/giao dịch không hoàn tác) PHẢI có xác nhận GIAO DỊCH
  cụ thể cho đúng mục tiêu; một câu "cứ làm đi" (dù scope rộng) KHÔNG qua được.
- R2+ cần consent phủ phạm vi; hành động ghi cần capability token hợp lệ.
- Đổi mục tiêu so với lúc cấp phép → consent cũ vô hiệu (cần xác nhận lại).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import (
    RISK_ORDER,
    CapabilityToken,
    ConsentRecord,
    PolicyContext,
    PolicyDecision,
    PolicyEffect,
    PolicyRule,
    RiskTier,
)

__all__ = ["DEFAULT_RULES", "evaluate"]

#: Luật mặc định rỗng — org tự thêm deny theo SAI-037. Gate cấu trúc dưới đây
#: mới là lớp an toàn chính (không phụ thuộc có luật hay không).
DEFAULT_RULES: tuple[PolicyRule, ...] = ()


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(value), time.min)
        except ValueError:
            return None


def _expired(expires_at: str | None, now: str | None) -> bool:
    """``True`` nếu đã quá hạn. Hạn không parse được = coi như hết hạn (bảo
    thủ). Không có ``now`` → không đánh giá được hạn → coi như còn (caller
    chủ động không truyền thời gian)."""

    if not expires_at or not now:
        return False
    exp = _parse_iso(expires_at)
    nw = _parse_iso(now)
    if exp is None:
        return True
    if nw is None:
        return True
    return nw > exp


def _deny(key: str, decision_rule_id: str, **params: object) -> PolicyDecision:
    return PolicyDecision(
        effect=PolicyEffect.DENY,
        reason_vi=t(key, lang=Lang.VI, **params),
        rule_id=decision_rule_id,
    )


def _allow(key: str, decision_rule_id: str, **params: object) -> PolicyDecision:
    return PolicyDecision(
        effect=PolicyEffect.ALLOW,
        reason_vi=t(key, lang=Lang.VI, **params),
        rule_id=decision_rule_id,
    )


def _rule_matches(when: Mapping[str, object], ctx: PolicyContext) -> bool:
    if "action" in when and when["action"] != ctx.action:
        return False
    if "risk" in when and when["risk"] != ctx.risk.value:
        return False
    if "stage" in when and when["stage"] != ctx.workflow_stage:
        return False
    if "org_policy" in when and when["org_policy"] != ctx.org_policy:
        return False
    if "target" in when and when["target"] != ctx.target:
        return False
    if "target_contains" in when and str(when["target_contains"]) not in ctx.target:
        return False
    return True


def _consent_covers(consent: ConsentRecord, ctx: PolicyContext) -> bool:
    if _expired(consent.expires_at, ctx.now):
        return False
    scope = consent.scope
    return bool(
        "all" in scope
        or ctx.action in scope
        or (ctx.target and ctx.target in scope)
        or f"risk:{ctx.risk.value}" in scope
    )


def _capability_valid(cap: CapabilityToken, ctx: PolicyContext) -> bool:
    if cap.revoked:
        return False
    if cap.one_time and cap.used:
        return False
    if _expired(cap.expires_at, ctx.now):
        return False
    if RISK_ORDER[cap.risk_tier] < RISK_ORDER[ctx.risk]:
        return False
    # Token phải gắn đúng chủ thể (app/capsule) = mục tiêu, nếu mục tiêu có nêu.
    return not (ctx.target and cap.subject and cap.subject != ctx.target)


def evaluate(ctx: PolicyContext, rules: Sequence[PolicyRule] = DEFAULT_RULES) -> PolicyDecision:
    """Quyết định allow/deny cho một hành động (SAI-039). deny ưu tiên."""

    # 1) Luật DENY tường minh (ưu tiên cao nhất).
    for rule in rules:
        if rule.effect == PolicyEffect.DENY and _rule_matches(rule.when, ctx):
            return _deny(
                rule.reason_key or "sai.policy.deny.rule",
                rule.rule_id,
                action=ctx.action,
                risk=ctx.risk.value,
                rule_id=rule.rule_id,
            )

    # 2) Consent gắn mục tiêu: đổi mục tiêu → consent cũ vô hiệu.
    if (
        ctx.consent is not None
        and ctx.target
        and ctx.consent.target_fingerprint
        and ctx.consent.target_fingerprint != ctx.target
    ):
        return _deny("sai.policy.deny.target_changed", "consent.target_changed")

    # 3) Gate cấu trúc theo bậc rủi ro (lớp an toàn chính).
    risk = ctx.risk
    if risk == RiskTier.R4:
        # R4 LUÔN cần xác nhận giao dịch cụ thể cho đúng mục tiêu — scope rộng
        # ("cứ làm đi") KHÔNG thay thế được.
        if not (
            ctx.consent is not None
            and ctx.consent.transaction_confirmed
            and ctx.consent.target_fingerprint == ctx.target
            and not _expired(ctx.consent.expires_at, ctx.now)
        ):
            return _deny("sai.policy.deny.r4_needs_transaction", "risk.r4")
        return _allow(
            "sai.policy.allow.default", "risk.r4.confirmed", action=ctx.action, risk=risk.value
        )

    if risk == RiskTier.R3:
        ok = (
            ctx.consent is not None
            and ctx.consent.target_fingerprint == ctx.target
            and (ctx.consent.transaction_confirmed or "r3" in ctx.consent.scope)
            and not _expired(ctx.consent.expires_at, ctx.now)
        )
        if not ok:
            return _deny("sai.policy.deny.risk_exceeds_consent", "risk.r3", risk=risk.value)

    if RISK_ORDER[risk] >= RISK_ORDER[RiskTier.R2]:
        if ctx.consent is None or not _consent_covers(ctx.consent, ctx):
            return _deny(
                "sai.policy.deny.consent_required",
                "risk.consent",
                action=ctx.action,
                risk=risk.value,
            )
        # Hành động ghi (R2+) cần capability token hợp lệ.
        if ctx.capability is None or not _capability_valid(ctx.capability, ctx):
            return _deny("sai.policy.deny.capability_missing", "risk.capability", action=ctx.action)

    # 4) Luật ALLOW tường minh.
    for rule in rules:
        if rule.effect == PolicyEffect.ALLOW and _rule_matches(rule.when, ctx):
            return _allow(
                rule.reason_key or "sai.policy.allow.default",
                rule.rule_id,
                action=ctx.action,
                risk=risk.value,
            )

    # 5) Tới đây: R0/R1 (đọc/sandbox) hoặc R2/R3 ĐÃ QUA gate cấu trúc (có đủ
    #    consent/capability) → cho phép. Org siết thêm bằng luật DENY ở (1).
    return _allow("sai.policy.allow.default", "default.allow", action=ctx.action, risk=risk.value)
