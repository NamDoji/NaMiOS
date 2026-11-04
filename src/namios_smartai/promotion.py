"""Promotion Gate + Evidence/Trust (SAI-012/042).

Vòng ``draft/experimental → lab_passed → pilot_verified → published`` CHỈ nâng
qua ``promote()`` với evidence THẬT + người thẩm quyền — **AI sửa nhãn trong
output KHÔNG nâng được** (nghiệm thu SAI-012). Không evidence → không publish.
Tác vụ kế toán/thuế/BHXH cần xác nhận nghiệp vụ + end-to-end (ECO/COMP).
Evidence quá hạn / nguồn giả → ``needs_retest`` (SAI-042), KHÔNG tạo pass.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import CompatibilityRecipe, RecipeState, TrustEvidence
from namios_smartai.recipe import validate_recipe_publishable

__all__ = [
    "evidence_trusted",
    "evidence_expired",
    "promote",
    "is_legitimately_published",
]


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(value), datetime.min.time())
        except ValueError:
            return None


def evidence_expired(ev: TrustEvidence, now: str | None) -> bool:
    """``True`` nếu evidence KHÔNG xác nhận được còn hạn (fail-closed, SAI-042).

    - Không khai ``valid_until`` → không có mốc hết hạn → ``False``.
    - Có ``valid_until`` nhưng parse lỗi → coi là quá hạn (dữ liệu hỏng = không tin).
    - Có ``valid_until`` nhưng KHÔNG biết ``now`` → coi là QUÁ HẠN: bất biến
      "evidence quá hạn → không pass" phải TỰ-BẢO-VỆ, không phụ thuộc caller nhớ
      truyền đồng hồ (QA COMPAT/M2: quên ``now`` từng cho phép evidence năm 2000
      lên published).
    - Biết ``now`` → so NGÀY THẬT."""

    if not ev.valid_until:
        return False
    vu = _parse_iso(ev.valid_until)
    if vu is None:
        return True
    if not now:
        return True
    nw = _parse_iso(now)
    return nw is None or nw > vu


def evidence_trusted(ev: TrustEvidence, *, now: str | None = None) -> bool:
    """Evidence ĐỦ TIN để nâng trạng thái (SAI-042): nguồn ``tool`` (vendor/
    user chỉ là tham khảo), ``test_result == 'pass'``, chưa quá hạn."""

    return ev.origin == "tool" and ev.test_result == "pass" and not evidence_expired(ev, now)


def promote(
    recipe: CompatibilityRecipe,
    *,
    evidence: Sequence[TrustEvidence],
    approver: str | None = None,
    business_ok: bool = False,
    now: str | None = None,
) -> tuple[RecipeState, str]:
    """Trả (trạng thái HỢP LỆ cao nhất, lý do VI). Tất định — không phụ thuộc
    ``recipe.state`` do AI gán. Thứ tự an toàn: quá-hạn → needs_retest; không
    tool-pass → experimental; có tool-pass → lab_passed; + approver →
    pilot_verified; + reviewers + business_ok + đủ cấu trúc → published."""

    # Evidence quá hạn / nguồn hỏng → needs_retest (SAI-042), không pass.
    if any(evidence_expired(e, now) for e in evidence):
        return RecipeState.NEEDS_RETEST, t("sai.promotion.needs_retest", lang=Lang.VI)

    trusted = [e for e in evidence if evidence_trusted(e, now=now)]
    if not trusted:
        return RecipeState.EXPERIMENTAL, t("sai.promotion.denied.no_evidence", lang=Lang.VI)

    structural = validate_recipe_publishable(recipe)

    if approver is None:
        return RecipeState.LAB_PASSED, t("sai.promotion.denied.reviewer", lang=Lang.VI)

    if structural:
        return RecipeState.PILOT_VERIFIED, structural[0].message_vi
    if not recipe.reviewers:
        return RecipeState.PILOT_VERIFIED, t("sai.promotion.denied.reviewer", lang=Lang.VI)
    if not business_ok:
        return RecipeState.PILOT_VERIFIED, t("sai.promotion.denied.business", lang=Lang.VI)

    return RecipeState.PUBLISHED, t("sai.repair.stop.success", lang=Lang.VI)


def is_legitimately_published(
    recipe: CompatibilityRecipe,
    *,
    evidence: Sequence[TrustEvidence],
    approver: str | None = None,
    business_ok: bool = False,
    now: str | None = None,
) -> bool:
    """Chống "AI gán state=published": một recipe CHỈ thực sự published khi
    ``promote(...)`` cũng trả ``PUBLISHED`` từ evidence+approver thật — bất kể
    ``recipe.state`` ghi gì."""

    state, _ = promote(
        recipe, evidence=evidence, approver=approver, business_ok=business_ok, now=now
    )
    return state == RecipeState.PUBLISHED
