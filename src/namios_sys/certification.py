"""Chứng nhận đầu-cuối ba trục (SYS-013).

Ba trục RIÊNG: (1) chạy kỹ thuật, (2) đúng nghiệp vụ, (3) hoàn tất với bên
ngoài. GUI mở được / tệp tải được / app cài được đều KHÔNG đủ. TÁI DÙNG gate
ECO-003 (``derive_published_status``/``is_usable``) cho trục kỹ thuật — KHÔNG
dựng lại; trục nghiệp vụ + bên ngoài chồng lên trên, chỉ HẠ không NÂNG.

Tương thích ECO-003/COMP-048/SAI-012: badge ``workflow_verified`` chỉ đạt khi
cả ba trục đạt; mô phỏng sai tổng tiền / thiếu biên nhận → không thể publish.
"""

from __future__ import annotations

from namios_eco.status import (
    NEVER_USABLE_STATUSES,
    PublishedStatus,
    PublishedStatusResult,
    is_usable,
)
from namios_i18n import Lang, t
from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)

__all__ = ["end_to_end_status", "is_overclaim"]


def end_to_end_status(
    technical: PublishedStatus,
    *,
    business_approved: bool,
    external_complete: bool,
) -> PublishedStatusResult:
    """Chồng hai trục nghiệp vụ + bên ngoài lên trục kỹ thuật (SYS-013).

    - Kỹ thuật chưa tới mức dùng được (tải/mở/unsupported/blocked/revoked) → giữ
      NGUYÊN, không nâng (``is_usable`` False → không bao giờ verified).
    - Kỹ thuật ``workflow_verified`` nhưng thiếu nghiệp vụ → hạ ``partial_workflow``.
    - Đủ nghiệp vụ nhưng chưa hoàn tất bên ngoài → ``blocked_external_dependency``.
    - Đủ cả ba → ``workflow_verified``.
    - Kỹ thuật ``partial_workflow`` → giữ partial (không tự nâng khi chưa đủ kỹ thuật).
    """

    # Trục kỹ thuật chưa "dùng được" → trả thẳng (gate ECO-003 là tối thượng).
    if not is_usable(technical) or technical in NEVER_USABLE_STATUSES:
        return PublishedStatusResult(
            status=technical,
            reasons_vi=(t("sys.cert.not_usable", lang=Lang.VI),),
        )

    if technical == PublishedStatus.WORKFLOW_VERIFIED:
        if not business_approved:
            return PublishedStatusResult(
                status=PublishedStatus.PARTIAL_WORKFLOW,
                reasons_vi=(t("sys.cert.need_business", lang=Lang.VI),),
            )
        if not external_complete:
            return PublishedStatusResult(
                status=PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
                reasons_vi=(t("sys.cert.need_external", lang=Lang.VI),),
            )
        return PublishedStatusResult(
            status=PublishedStatus.WORKFLOW_VERIFIED,
            reasons_vi=(t("sys.cert.verified", lang=Lang.VI),),
        )

    # technical == PARTIAL_WORKFLOW: giữ nguyên, nêu lý do còn thiếu.
    reason = (
        t("sys.cert.need_business", lang=Lang.VI)
        if not business_approved
        else t("sys.cert.need_external", lang=Lang.VI)
    )
    return PublishedStatusResult(status=PublishedStatus.PARTIAL_WORKFLOW, reasons_vi=(reason,))


def is_overclaim(
    claimed: PublishedStatus,
    *,
    business_approved: bool,
    external_complete: bool,
) -> bool:
    """``True`` nếu ``claimed`` là ``workflow_verified`` nhưng thiếu nghiệp vụ
    hoặc hoàn tất bên ngoài (tức là tự nhận quá mức). Dùng để chặn publish."""

    if claimed != PublishedStatus.WORKFLOW_VERIFIED:
        return False
    return not (business_approved and external_complete)
