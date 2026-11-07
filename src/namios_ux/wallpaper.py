"""Hợp đồng hình nền "Việt Nam qua từng vùng đất" (Phụ lục 12, §3.6 —
UX12-025..032/046).

Honest-core: đây KHÔNG phải pipeline tải/xử lý ảnh thật, chỉ là hợp đồng dữ
liệu + gate fail-closed để một ảnh ĐƯỢC PHÉP đóng gói hay không. KHÔNG đoán
quyền sử dụng: thiếu license/bằng chứng quyền/hash → luôn coi là CHƯA đủ điều
kiện, không bao giờ suy diễn "chắc là có quyền" từ các trường khác.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from namios_core.validation import ValidationError
from namios_i18n import Lang, t
from namios_ux import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_ux._errors import UxErrorCode
from namios_ux._text import means_absent, normalize_text

__all__ = [
    "WallpaperEntry",
    "HARD_GATE_CODES",
    "validate_wallpaper",
    "wallpaper_is_shippable",
]

#: Dấu hiệu (lowercase, trong ``credit``/``source``) coi là ĐÃ khai rõ ảnh có
#: liên quan tới AI (UX12-031: "ảnh được tạo/sửa bằng AI phải ghi rõ bản chất
#: và quyền sử dụng nếu phát hành"). Không đoán — chỉ chuỗi tường minh.
#: Cụm từ khai báo AI (so khớp chuỗi con trên văn bản đã chuẩn hoá). KHÔNG đưa
#: chuỗi ``"ai"`` trần vào đây: nó là chuỗi con của RẤT NHIỀU từ tiếng Việt vô
#: can ("Mai", "Hai", "Lào Cai"...) → sẽ coi nhầm là "đã khai báo AI" (fail-
#: open). Token ``"ai"`` đứng một mình được xử lý riêng bằng ranh giới từ.
_AI_DISCLOSURE_PHRASES: tuple[str, ...] = (
    "trí tuệ nhân tạo",
    "tri tue nhan tao",
    "tạo bởi ai",
    "generative",
    "generativ",
    "midjourney",
    "stable diffusion",
    "dall-e",
    "dall·e",
    "dalle",
    "a.i.",
    "artificial intelligence",
)

#: ``"ai"`` CHỈ tính là khai báo khi đứng như một TỪ riêng (ranh giới không
#: phải chữ-số ascii) — "ai"/"AI" độc lập, không phải phần của "mai"/"cai".
_AI_WORD_RE = re.compile(r"(?<![a-z0-9])ai(?![a-z0-9])")

#: sha256 hợp lệ = đúng 64 ký tự hex (không phân biệt hoa thường).
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


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
        UxErrorCode.E_UX_WALLPAPER_INVALID_SHA256.value,
        UxErrorCode.E_UX_WALLPAPER_AI_UNDISCLOSED.value,
    }
)


def _ai_disclosed(entry: WallpaperEntry) -> bool:
    """Ảnh AI đã khai rõ trong ``credit``/``source`` chưa (UX12-031). FAIL-
    CLOSED: dùng chuẩn hoá Unicode (chặn fullwidth/zero-width/hoa-thường) và
    ranh giới từ cho token ``"ai"`` — tránh coi nhầm "Mai"/"Lào Cai" là đã khai
    báo (đó là lỗ hổng fail-open của bản substring ``"ai"`` thô)."""

    haystack = normalize_text(f"{entry.credit} {entry.source}")
    if any(phrase in haystack for phrase in _AI_DISCLOSURE_PHRASES):
        return True
    return _AI_WORD_RE.search(haystack) is not None


def _sha256_is_valid(raw: str) -> bool:
    """Đúng 64 ký tự hex, không gì khác. KHÔNG bỏ ký tự vô hình/fullwidth ở đây
    (fail-closed: hash thật là ascii thuần — mọi ký tự lạ → sai định dạng)."""

    return _SHA256_RE.fullmatch(raw.strip().lower()) is not None


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
    # License/bằng-chứng-quyền: ``means_absent`` chặn cả giá trị KHÔNG rỗng
    # nhưng nghĩa là CHƯA có quyền ("chưa có — cần cấp phép", "pending", "TODO",
    # "placeholder", "unknown"...). Không đoán "chắc quên điền" là hợp lệ.
    _add(
        means_absent(entry.license),
        UxErrorCode.E_UX_WALLPAPER_MISSING_LICENSE,
        "license",
        "ux.wallpaper.missing_license",
    )
    _add(
        means_absent(entry.rights_evidence),
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
    # sha256 có nội dung nhưng SAI định dạng (không phải 64 hex) → chặn riêng
    # (không âm thầm chấp nhận một hash giả/cắt ngắn).
    _add(
        bool(entry.sha256.strip()) and not _sha256_is_valid(entry.sha256),
        UxErrorCode.E_UX_WALLPAPER_INVALID_SHA256,
        "sha256",
        "ux.wallpaper.invalid_sha256",
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
