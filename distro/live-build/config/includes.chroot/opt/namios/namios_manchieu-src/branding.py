"""Màu thương hiệu NaMiOS ("Sen Việt" v2.0) cho giao diện PySide6 của Máy
chiếu & Màn hình ngoài. Đọc trực tiếp
``usr/share/namios-branding/logo/brand.json`` (đã cài sẵn trong ảnh) —
KHÔNG sửa/ghi file đó, chỉ ĐỌC màu. Cùng khuôn ``namios_dichvu.branding``/
``namios_lich.ui._load_brand_colors`` — tái dùng logic đọc file.

FAIL-SAFE: file thiếu/hỏng/đổi cấu trúc (vd chạy module ngoài ảnh NaMiOS,
môi trường dev/test không có gói branding) -> dùng bộ màu dự phòng CỨNG
(giá trị y hệt ``brand.json`` tại 11/11/2026) — app KHÔNG BAO GIỜ crash vì
thiếu file thương hiệu."""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["BrandColors", "load_brand_colors", "build_stylesheet"]

_BRAND_JSON_PATH = Path("/usr/share/namios-branding/logo/brand.json")

# Màu NaMiOS v3 "Đông Sơn" (navy/gold/vermilion) — map từ fallback "Sen" v2.0
# cũ, cập nhật 11/11/2026. "canh*/son/dai" tô header + nút hành động → vai trò
# ACTION ⇒ vermilion; "vang_*" → gold; "muc_dem/chu_muc" → navy mới. Đọc
# brand.json trước; dict này chỉ là dự phòng khi thiếu gói branding.
_FALLBACK_COLORS: dict[str, str] = {
    "son": "#D64C3E",
    "canh_dark": "#D64C3E",
    "canh": "#D64C3E",
    "canh_light": "#D64C3E",
    "dai": "#D64C3E",
    "vang_tam": "#DEA93E",
    "vang_nuoc": "#DEA93E",
    "muc_dem": "#092D4F",
    "chu_muc": "#092D4F",
}


class BrandColors(dict[str, str]):
    """``dict[str, str]`` tên-màu -> mã hex, LUÔN có đủ khoá của
    ``_FALLBACK_COLORS``."""


def load_brand_colors(path: Path | None = None) -> BrandColors:
    brand_path = path if path is not None else _BRAND_JSON_PATH
    colors = dict(_FALLBACK_COLORS)
    try:
        raw = json.loads(brand_path.read_text(encoding="utf-8"))
        raw_colors = raw.get("colors") if isinstance(raw, dict) else None
        if isinstance(raw_colors, dict):
            for key, value in raw_colors.items():
                if isinstance(key, str) and isinstance(value, str) and value.startswith("#"):
                    colors[key] = value
    except (OSError, json.JSONDecodeError, AttributeError):
        pass  # noqa: S110 - fail-safe tuyệt đối, xem docstring module
    return BrandColors(colors)


def build_stylesheet(colors: BrandColors | None = None) -> str:
    """QSS cho cửa sổ 4-nút-to + dòng trạng thái — bố cục đơn giản hơn
    ``namios_antoan``/``namios_dichvu`` (không có thẻ cuộn, chỉ 1 màn hình
    chọn chế độ), nên stylesheet cũng gọn hơn, tập trung làm 4 nút thật TO
    + dễ bấm (người dùng ít rành công nghệ, đúng tinh thần đặc tả)."""

    c = colors if colors is not None else load_brand_colors()
    return f"""
    QMainWindow, QWidget#ManChieuRoot {{
        background-color: #F4F4F4;
    }}
    QFrame#Header {{
        background-color: {c["canh"]};
        border-bottom: 2px solid {c["dai"]};
    }}
    QLabel#HeaderTitle {{
        color: #FFFFFF;
        font-size: 16pt;
        font-weight: 600;
    }}
    QLabel#HeaderSubtitle {{
        color: #FDEAEA;
        font-size: 9pt;
    }}
    QFrame#StatusBar {{
        background-color: #FFFFFF;
        border: 1px solid #DDDDDD;
        border-radius: 8px;
    }}
    QLabel#StatusLabel {{
        color: {c["chu_muc"]};
        font-size: 10pt;
    }}
    QPushButton#RefreshButton {{
        background-color: #FFFFFF;
        border: 1px solid {c["canh"]};
        color: {c["canh"]};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
    }}
    QPushButton#RefreshButton:hover {{
        background-color: #FBEAEA;
    }}
    QPushButton#ModeButton {{
        background-color: {c["muc_dem"]};
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 18px;
        font-size: 13pt;
        font-weight: 700;
        text-align: center;
    }}
    QPushButton#ModeButton:hover {{
        background-color: {c["canh_dark"]};
    }}
    QPushButton#ModeButton:disabled {{
        background-color: #BBBBBB;
        color: #EEEEEE;
    }}
    QLabel#ModeHint {{
        color: #666666;
        font-size: 8pt;
    }}
    QLabel#FooterDisclaimer {{
        color: #666666;
        font-size: 8pt;
    }}
    """
