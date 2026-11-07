"""Design token + kiểm tương phản màu WCAG thuần (Phụ lục 12, §3.2 [4]).

Công thức relative luminance / contrast ratio tự viết theo WCAG 2.2 (nguồn
[4] trong Phụ lục 12), KHÔNG phụ thuộc thư viện ngoài — honest-core pure-
stdlib. Dùng để GATE cặp màu ``text``/``surface`` trước khi đưa vào hệ token
chính thức, không phải để render UI thật.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from namios_i18n import Lang, t
from namios_ux import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_ux._errors import UxErrorCode

__all__ = [
    "TokenCategory",
    "DesignToken",
    "WCAG_NORMAL_TEXT_MIN_RATIO",
    "WCAG_LARGE_TEXT_MIN_RATIO",
    "contrast_ratio",
    "meets_wcag",
    "token_pair_meets_wcag",
    "CONTRAST_FAIL_CODE",
    "INVALID_HEX_CODE",
]

#: Ngưỡng WCAG 2.2 (UX12 §3.2 [4]): chữ thường tối thiểu 4.5:1.
WCAG_NORMAL_TEXT_MIN_RATIO = 4.5
#: Chữ LỚN (semibold cỡ lớn/hero) tối thiểu 3:1.
WCAG_LARGE_TEXT_MIN_RATIO = 3.0


class TokenCategory(str, Enum):
    """Nhóm token thiết kế (UX12 §3.1/§3.2) — đủ để phân loại, KHÔNG phải kho
    token đầy đủ (đó là việc của ``design/tokens.json`` do nhóm thiết kế giữ)."""

    COLOR = "color"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    RADIUS = "radius"
    SIZE = "size"
    MOTION = "motion"


@dataclass(frozen=True)
class DesignToken:
    """Một token thiết kế (tên ngữ nghĩa + giá trị, UX12 §3.1/§3.2).

    ``value`` với ``category=COLOR`` PHẢI là mã hex (``"#rrggbb"`` hoặc dạng
    rút gọn ``"#rgb"``) để ``token_pair_meets_wcag`` đọc được."""

    name: str
    value: str
    category: TokenCategory


def _hex_to_rgb01(hex_value: str) -> tuple[float, float, float]:
    """Parse mã hex màu (``"#rgb"``/``"#rrggbb"``, có hoặc không dấu ``#``)
    thành (r, g, b) chuẩn hoá [0, 1]. Giá trị không hợp lệ → ``ValueError``
    (fail LOUD — không âm thầm trả một màu mặc định làm sai kết quả gate)."""

    raw = hex_value.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        raise ValueError(
            t("ux.token.invalid_hex", lang=Lang.VI, value=hex_value),
        )
    try:
        r = int(raw[0:2], 16)
        g = int(raw[2:4], 16)
        b = int(raw[4:6], 16)
    except ValueError as exc:
        raise ValueError(t("ux.token.invalid_hex", lang=Lang.VI, value=hex_value)) from exc
    return (r / 255.0, g / 255.0, b / 255.0)


def _linearize(channel: float) -> float:
    """Tuyến tính hoá một kênh sRGB (WCAG 2.2, công thức relative luminance)."""

    if channel <= 0.03928:
        return channel / 12.92
    # ``float ** float`` được typeshed khai báo trả ``Any`` (vì trên lý thuyết
    # cơ số âm + số mũ lẻ có thể ra số phức) — ép lại ``float`` tường minh,
    # đúng với miền giá trị thật ở đây (channel luôn thuộc [0, 1]).
    return float(((channel + 0.055) / 1.055) ** 2.4)


def _relative_luminance(rgb01: tuple[float, float, float]) -> float:
    r, g, b = (_linearize(c) for c in rgb01)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Tỉ lệ tương phản WCAG giữa hai màu hex (UX12 §3.2 [4]).

    Công thức: ``(L1 + 0.05) / (L2 + 0.05)`` với ``L1`` là độ chói tương đối
    LỚN hơn trong hai màu (không phụ thuộc thứ tự tham số truyền vào — màu
    nào sáng hơn luôn là tử số). Kết quả trong khoảng ``[1.0, 21.0]``."""

    l_fg = _relative_luminance(_hex_to_rgb01(fg_hex))
    l_bg = _relative_luminance(_hex_to_rgb01(bg_hex))
    lighter, darker = (l_fg, l_bg) if l_fg >= l_bg else (l_bg, l_fg)
    return (lighter + 0.05) / (darker + 0.05)


def meets_wcag(ratio: float, *, large: bool = False) -> bool:
    """``ratio`` đạt ngưỡng WCAG 2.2 chưa — chữ lớn ``>= 3.0``, chữ thường
    ``>= 4.5`` (UX12 §3.2 [4])."""

    threshold = WCAG_LARGE_TEXT_MIN_RATIO if large else WCAG_NORMAL_TEXT_MIN_RATIO
    return ratio >= threshold


def token_pair_meets_wcag(
    text_token: DesignToken, surface_token: DesignToken, *, large: bool = False
) -> bool:
    """INVARIANT gate (UX12 §3.2 [4]): cặp token ``text``/``surface`` dưới
    ngưỡng WCAG → ``False``. Dùng để gate token màu trước khi công bố cặp
    sáng/tối chính thức — KHÔNG tự suy luận ngưỡng từ tên token, luôn tính
    thật bằng ``contrast_ratio``."""

    ratio = contrast_ratio(text_token.value, surface_token.value)
    return meets_wcag(ratio, large=large)


# Giữ mã lỗi sẵn trong namespace module (dùng ở call-site muốn báo cáo có cấu
# trúc thay vì chỉ bool — vd công cụ lint token hàng loạt).
CONTRAST_FAIL_CODE = UxErrorCode.E_UX_COLOR_CONTRAST_FAIL.value
INVALID_HEX_CODE = UxErrorCode.E_UX_COLOR_INVALID_HEX.value
