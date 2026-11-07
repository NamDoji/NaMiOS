"""Hợp đồng hình nền "Việt Nam qua từng vùng đất" (Phụ lục 12, §3.6 —
UX12-025..032/046).

Honest-core: đây KHÔNG phải pipeline tải/xử lý ảnh thật, chỉ là hợp đồng dữ
liệu + gate fail-closed để một ảnh ĐƯỢC PHÉP đóng gói hay không. KHÔNG đoán
quyền sử dụng: thiếu license/bằng chứng quyền/hash → luôn coi là CHƯA đủ điều
kiện, không bao giờ suy diễn "chắc là có quyền" từ các trường khác.
"""

from __future__ import annotations

from dataclasses import dataclass

from namios_core.validation import ValidationError
from namios_i18n import Lang, t
from namios_ux import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_ux._errors import UxErrorCode

__all__ = [
    "WallpaperEntry",
    "HARD_GATE_CODES",
    "validate_wallpaper",
    "wallpaper_is_shippable",
]

#: Dấu hiệu (lowercase, trong ``credit``/``source``) coi là ĐÃ khai rõ ảnh có
#: liên quan tới AI (UX12-031: "ảnh được tạo/sửa bằng AI phải ghi rõ bản chất
#: và quyền sử dụng nếu phát hành"). Không đoán — chỉ chuỗi tường minh.
_AI_DISCLOSURE_MARKERS: tuple[str, ...] = (
    "ai",
    "trí tuệ nhân tạo",
    "tạo bởi ai",
    "generative",
    "midjourney",
    "stable diffusion",
    "dall-e",
    "dalle",
)


@dataclass(frozen=True)
class WallpaperEntry:
    """Một ảnh trong bộ sưu tập hình nền (UX12-025..032/046).

    ``variants`` = danh sách biến thể xuất bản đã có (vd ``("16:9", "16:10")``
    — xem UX12-027); ``credit`` là chuỗi ghi công hiển thị trong hộp thoại
    "Thông tin hình nền" (UX12-026, §3.6)."""

    id: str
    title: str = ""
    location: str = ""
    author: str = ""
    source: str = ""
    license: str = ""
    rights_evidence: str = ""
    sha256: str = ""
    variants: tuple[str, ...] = ()
    credit: str = ""
    ai_generated: bool = False


#: Mã lỗi coi là CỨNG — thiếu MỘT trong các mã này = KHÔNG được đóng gói
#: (UX12-026/031/046). ``validate_wallpaper`` còn trả thêm các vấn đề "mềm"
#: (thiếu title/location/author/variants — chất lượng biên tập, không tự nó
#: chặn phát hành ở gate quyền/nguồn gốc này).
HARD_GATE_CODES: frozenset[str] = frozenset(
    {
        UxErrorCode.E_UX_WALLPAPER_MISSING_LICENSE.value,
        UxErrorCode.E_UX_WALLPAPER_MISSING_RIGHTS_EVIDENCE.value,
        UxErrorCode.E_UX_WALLPAPER_MISSING_SHA256.value,
        UxErrorCode.E_UX_WALLPAPER_AI_UNDISCLOSED.value,
    }
)


def _ai_disclosed(entry: WallpaperEntry) -> bool:
    haystack = f"{entry.credit} {entry.source}".lower()
    return any(marker in haystack for marker in _AI_DISCLOSURE_MARKERS)


def validate_wallpaper(entry: WallpaperEntry) -> list[ValidationError]:
    """Mọi vấn đề metadata của một ảnh (cứng + mềm). Rỗng = đủ metadata.

    KHÔNG đoán quyền: field rỗng/toàn khoảng trắng luôn tính là THIẾU, không
    bao giờ coi "chắc đã có nhưng quên điền" là hợp lệ."""

    errors: list[ValidationError] = []

    def _add(cond: bool, code: UxErrorCode, path: str, msg_key: str) -> None:
        if cond:
            errors.append(
                ValidationError(
                    code=code.value,
                    path=path,
                    message_vi=t(msg_key, lang=Lang.VI, title=entry.title or entry.id),
                )
            )

    _add(
        not entry.title.strip(),
        UxErrorCode.E_UX_WALLPAPER_MISSING_TITLE,
        "title",
        "ux.wallpaper.missing_title",
    )
    _add(
        not entry.location.strip(),
        UxErrorCode.E_UX_WALLPAPER_MISSING_LOCATION,
        "location",
        "ux.wallpaper.missing_location",
    )
    _add(
        not entry.author.strip(),
        UxErrorCode.E_UX_WALLPAPER_MISSING_AUTHOR,
        "author",
        "ux.wallpaper.missing_author",
    )
    _add(
        not entry.license.strip(),
        UxErrorCode.E_UX_WALLPAPER_MISSING_LICENSE,
        "license",
        "ux.wallpaper.missing_license",
    )
    _add(
        not entry.rights_evidence.strip(),
        UxErrorCode.E_UX_WALLPAPER_MISSING_RIGHTS_EVIDENCE,
        "rights_evidence",
        "ux.wallpaper.missing_rights_evidence",
    )
    _add(
        not entry.sha256.strip(),
        UxErrorCode.E_UX_WALLPAPER_MISSING_SHA256,
        "sha256",
        "ux.wallpaper.missing_sha256",
    )
    _add(
        not entry.variants,
        UxErrorCode.E_UX_WALLPAPER_MISSING_VARIANTS,
        "variants",
        "ux.wallpaper.missing_variants",
    )
    _add(
        entry.ai_generated and not _ai_disclosed(entry),
        UxErrorCode.E_UX_WALLPAPER_AI_UNDISCLOSED,
        "credit",
        "ux.wallpaper.ai_undisclosed",
    )

    return errors


def wallpaper_is_shippable(entry: WallpaperEntry) -> bool:
    """FAIL-CLOSED (UX12-026/031/046): một ảnh chỉ được đóng gói khi KHÔNG có
    vấn đề nào trong ``HARD_GATE_CODES`` — thiếu license HOẶC thiếu
    rights_evidence HOẶC thiếu sha256 HOẶC (``ai_generated`` mà chưa khai rõ)
    → luôn ``False``, bất kể các trường khác (title/author/...) đẹp đến đâu."""

    return not any(err.code in HARD_GATE_CODES for err in validate_wallpaper(entry))
