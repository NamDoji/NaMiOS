"""SmartAI phân biệt loại ứng dụng/cập nhật (APP11-026).

Câu "cập nhật Zalo/Facebook" PHẢI được giải thích đúng: phần web do NHÀ CUNG CẤP
tự cập nhật trên server của họ; NaMiOS chỉ cập nhật browser/manifest/kiểm
tương thích phía mình. Nếu người dùng dùng Zalo PC trong Wine, chỉ cập nhật
SAU KHI đã chứng nhận bản mới (``wine_cert_ok``) — chưa chứng nhận →
``WINE_RECIPE_PENDING_CERT``, ``action_allowed=False``.

TÁI DÙNG ``namios_sys.data_authority.authorize`` (SourceTrust.WEBPAGE không
BAO GIỜ nằm trong ``TRUSTED_SOURCES``) để khẳng định: lệnh/chỉ-dẫn nằm TRONG
nội dung một trang web (vd banner "Nhấn vào đây để cập nhật ngay") KHÔNG tự
kích hoạt tool nào — KHÔNG dựng lại cơ chế authority thứ hai.
"""

from __future__ import annotations

from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._types import UpdateClassification, UpdateOrigin
from namios_i18n import Lang, t
from namios_sys import SourceTrust, authorize

__all__ = ["classify_update_question", "webpage_instruction_authorized"]

#: Từ khóa ứng dụng web do vendor tự cập nhật (Phụ lục 11 bảng danh mục §2).
_WEB_APP_KEYWORDS: tuple[str, ...] = (
    "zalo",
    "facebook",
    "tiktok",
    "youtube",
    "maps",
    "whatsapp",
    "google maps",
    "ban do",
    "bản đồ",
)

#: Từ khóa chỉ "browser"/"trình duyệt" — kênh NaMiOS THẬT SỰ cập nhật được.
_BROWSER_KEYWORDS: tuple[str, ...] = ("browser", "trinh duyet", "trình duyệt", "chrome", "firefox")


def classify_update_question(
    text: str,
    *,
    target_is_wine_app: bool = False,
    wine_cert_ok: bool = False,
) -> UpdateClassification:
    """Phân loại một câu hỏi cập nhật tự nhiên (APP11-026). Thứ tự xét:
    1) app Windows qua Wine → cần chứng nhận mới cho cập nhật, chưa có →
       ``WINE_RECIPE_PENDING_CERT`` (``action_allowed=False``, APP11-021).
    2) tên dịch vụ web phổ biến → ``VENDOR_WEB_SERVICE`` (``action_allowed=
       False`` — NaMiOS không "cập nhật" được server vendor).
    3) từ khóa browser → ``NAMIOS_BROWSER_MANIFEST`` (``action_allowed=True``).
    4) còn lại → coi là gói native NaMiOS/distro (``action_allowed=True``)."""

    folded = text.strip().lower()

    if target_is_wine_app:
        if not wine_cert_ok:
            return UpdateClassification(
                origin=UpdateOrigin.WINE_RECIPE_PENDING_CERT,
                action_allowed=False,
                explanation_vi=t("essentials.smartai.wine_pending_cert", lang=Lang.VI),
            )
        return UpdateClassification(
            origin=UpdateOrigin.NAMIOS_NATIVE_PACKAGE,
            action_allowed=True,
            explanation_vi=t("essentials.smartai.wine_certified_update", lang=Lang.VI),
        )

    if any(keyword in folded for keyword in _WEB_APP_KEYWORDS):
        return UpdateClassification(
            origin=UpdateOrigin.VENDOR_WEB_SERVICE,
            action_allowed=False,
            explanation_vi=t("essentials.smartai.vendor_web_service", lang=Lang.VI),
        )

    if any(keyword in folded for keyword in _BROWSER_KEYWORDS):
        return UpdateClassification(
            origin=UpdateOrigin.NAMIOS_BROWSER_MANIFEST,
            action_allowed=True,
            explanation_vi=t("essentials.smartai.browser_manifest", lang=Lang.VI),
        )

    return UpdateClassification(
        origin=UpdateOrigin.NAMIOS_NATIVE_PACKAGE,
        action_allowed=True,
        explanation_vi=t("essentials.smartai.native_package", lang=Lang.VI),
    )


def webpage_instruction_authorized(action: str, *, content: str = "") -> bool:
    """Chỉ-dẫn nằm TRONG nội dung một trang web có được biến thành hành động
    không (APP11-026). KHÔNG — ``SourceTrust.WEBPAGE`` không nằm trong
    ``TRUSTED_SOURCES`` của ``namios_sys.data_authority``, nên luôn bị từ
    chối, kể cả khi trang web không chứa marker injection rõ ràng."""

    decision = authorize(
        action, source=SourceTrust.WEBPAGE, org_policy_allows=True, content=content
    )
    return decision.allowed
