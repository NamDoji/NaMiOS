"""Màu thương hiệu NaMiOS ("Sen Việt" v2.0) cho giao diện PySide6 của
NaMiOS Assistant. Đọc trực tiếp ``usr/share/namios-branding/logo/brand.json``
(đã cài sẵn trong ảnh qua hook ``0120-namios-branding.hook.chroot``) — KHÔNG
sửa/ghi file đó (sở hữu bởi wave branding khác), chỉ ĐỌC màu.

FAIL-SAFE: file thiếu/hỏng/đổi cấu trúc (vd chạy module này ngoài ảnh NaMiOS,
môi trường dev/test) -> dùng bộ màu dự phòng CỨNG (giá trị y hệt bản
``brand.json`` tại thời điểm viết module này, 09/11/2026) — app KHÔNG BAO GIỜ
crash vì thiếu file thương hiệu, chỉ mất khả năng tự cập nhật màu nếu
``brand.json`` đổi sau này mà không đồng bộ lại hằng số dự phòng ở đây."""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["BrandColors", "load_brand_colors", "build_stylesheet"]

_BRAND_JSON_PATH = Path("/usr/share/namios-branding/logo/brand.json")

#: Dự phòng CỨNG — khớp ``colors`` trong ``brand.json`` v2.0 (09/11/2026).
_FALLBACK_COLORS: dict[str, str] = {
    "son": "#C93643",
    "canh_dark": "#AB2430",
    "canh": "#CF3540",
    "canh_light": "#E56365",
    "dai": "#92212E",
    "vang_tam": "#F2C66D",
    "vang_nuoc": "#BC8A43",
    "muc_dem": "#122A3A",
    "chu_muc": "#182E3B",
}

_REQUIRED_KEYS = frozenset(_FALLBACK_COLORS)


class BrandColors(dict[str, str]):
    """``dict[str, str]`` tên-màu -> mã hex, LUÔN có đủ ``_REQUIRED_KEYS``
    (dùng fallback bù cho key thiếu trong file thật, không chỉ fallback toàn
    bộ khi file có mặt nhưng thiếu một vài khoá)."""


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
    """Dựng một QSS (Qt Style Sheet) brand-styled cho cửa sổ chat. Tách
    riêng khỏi ``ui.py`` để test được việc build chuỗi QSS không cần import
    PySide6 (``python3 -m py_compile``/unit test chạy headless)."""

    c = colors if colors is not None else load_brand_colors()
    return f"""
    QMainWindow, QWidget#AssistantRoot {{
        background-color: #FFFFFF;
    }}
    QFrame#Header {{
        background-color: {c['canh']};
        border-bottom: 2px solid {c['dai']};
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
    QLabel#StatusBanner {{
        background-color: {c['muc_dem']};
        color: {c['vang_tam']};
        padding: 4px 10px;
        font-size: 9pt;
    }}
    QListWidget#Transcript {{
        background-color: #FAFAFA;
        border: none;
    }}
    QFrame#BubbleYou {{
        background-color: {c['muc_dem']};
        border-radius: 10px;
    }}
    QFrame#BubbleYou QLabel {{
        color: #FFFFFF;
    }}
    QFrame#BubbleAssistant {{
        background-color: #F1F1F1;
        border-radius: 10px;
        border: 1px solid #DDDDDD;
    }}
    QFrame#BubbleAssistant QLabel {{
        color: {c['chu_muc']};
    }}
    QLabel#BubbleNote {{
        color: #777777;
        font-size: 8pt;
        font-style: italic;
    }}
    QFrame#BubbleSystem {{
        background-color: #FFF7E6;
        border-radius: 8px;
        border: 1px solid {c['vang_tam']};
    }}
    QFrame#BubbleSystem QLabel {{
        color: {c['chu_muc']};
    }}
    QPlainTextEdit#InputBox {{
        border: 1px solid #CCCCCC;
        border-radius: 8px;
        padding: 6px;
        font-size: 10pt;
    }}
    QPushButton {{
        background-color: #FFFFFF;
        border: 1px solid {c['canh']};
        color: {c['canh']};
        border-radius: 6px;
        padding: 6px 14px;
    }}
    QPushButton:hover {{
        background-color: #FBEAEA;
    }}
    QPushButton#SendButton {{
        background-color: {c['canh']};
        color: #FFFFFF;
        border: none;
        font-weight: 600;
    }}
    QPushButton#SendButton:hover {{
        background-color: {c['canh_dark']};
    }}
    QPushButton#SendButton:disabled {{
        background-color: #CCCCCC;
        color: #888888;
    }}
    QLabel#FooterDisclaimer {{
        color: #999999;
        font-size: 8pt;
    }}
    """
