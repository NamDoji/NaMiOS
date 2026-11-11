"""Màu thương hiệu NaMiOS ("Sen Việt" v2.0) cho giao diện PySide6 của Cổng
Dịch vụ Việt. Đọc trực tiếp ``usr/share/namios-branding/logo/brand.json``
(đã cài sẵn trong ảnh qua hook ``0120-namios-branding.hook.chroot``) — KHÔNG
sửa/ghi file đó, chỉ ĐỌC màu. Cùng khuôn ``namios_assistant.branding``/
``namios_antoan.branding`` — tái dùng logic đọc file, KHÔNG tự chế cách đọc
brand.json thứ ba.

FAIL-SAFE: file thiếu/hỏng/đổi cấu trúc (vd chạy module này ngoài ảnh NaMiOS,
môi trường dev/test) -> dùng bộ màu dự phòng CỨNG (giá trị y hệt bản
``brand.json`` tại thời điểm viết module này, 11/11/2026) — app KHÔNG BAO GIỜ
crash vì thiếu file thương hiệu."""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["BrandColors", "load_brand_colors", "build_stylesheet"]

_BRAND_JSON_PATH = Path("/usr/share/namios-branding/logo/brand.json")

#: Dự phòng CỨNG — mapped sang bảng NaMiOS v3 "Đông Sơn" (navy/gold/vermilion,
#: xem ``branding/kit/NaMi_Brand_DongSon_v1``), cập nhật 11/11/2026; giữ
#: nguyên TÊN KHOÁ của bản ``brand.json`` v2.0 "Sen Việt" cũ, chỉ đổi mã màu.
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

_REQUIRED_KEYS = frozenset(_FALLBACK_COLORS)

#: Màu TRẠNG THÁI chức năng (KHÔNG nằm trong brand.json — ngữ nghĩa riêng
#: của realistic_status ở Cổng Dịch vụ Việt/Trung tâm Ký số, cùng quy ước
#: ``namios_antoan.branding.STATUS_*``): xanh=chạy được (web/native), vàng=
#: chưa kiểm/candidate, đỏ=bị chặn.
STATUS_WORKS_WEB = "#2E7D32"
STATUS_WORKS_NATIVE = "#1B5E8A"
STATUS_WINE_CANDIDATE = "#B8860B"
STATUS_BLOCKED = "#C62828"

STATUS_COLORS: dict[str, str] = {
    "works-web": STATUS_WORKS_WEB,
    "works-native": STATUS_WORKS_NATIVE,
    "wine-candidate": STATUS_WINE_CANDIDATE,
    "blocked": STATUS_BLOCKED,
}


class BrandColors(dict[str, str]):
    """``dict[str, str]`` tên-màu -> mã hex, LUÔN có đủ ``_REQUIRED_KEYS``."""


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
    """Dựng QSS cho bố cục danh sách/thẻ (khác bố cục bong bóng chat của
    ``namios_assistant.branding.build_stylesheet``) — tách riêng theo app,
    cùng dùng chung bảng màu thương hiệu.

    UI polish 12/11/2026 (consistency, tham chiếu branding/design-system/
    components.css §1 "BUTTON"/§3 "FIELD" + docs/design/nami-tokens.json
    "radius"/"focus"): trước bản này mọi nút bấm dùng border-radius 6px còn
    card/input dùng 8/10px — một thang bo góc KHÔNG chủ đích, không khớp
    token nào. Chuẩn hoá: NÚT/Ô-NHẬP = --r-md (12px, khớp .nm-btn/.nm-field),
    CARD/BANNER = --r-lg (16px, khớp .nm-devicecard/.nm-errorcard), BADGE =
    pill (999px, khớp .nm-badge). Thêm ``:focus`` cho QPushButton/QLineEdit
    (trước đây KHÔNG có state nào — chỉ default/hover/disabled, thiếu đúng
    "focus" mà mọi control tương tác phải có) — viền 2px màu gold-deep
    #8B6518 (focus-ring token light-mode, nami-tokens.json color.light.
    focus-ring; KHÔNG dùng gold gốc #DEA93E vì chỉ ~2:1 trên nền sáng)."""

    c = colors if colors is not None else load_brand_colors()
    return f"""
    QMainWindow, QWidget#DichVuRoot {{
        background-color: #F4F4F4;
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
    QPushButton#EnvCheckButton {{
        background-color: {c['muc_dem']};
        color: {c['vang_tam']};
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 5px 12px;
        font-weight: 600;
    }}
    QPushButton#EnvCheckButton:focus {{
        border: 2px solid #8B6518;
    }}
    QLineEdit#SearchBox {{
        border: 1px solid #CCCCCC;
        border-radius: 12px;
        padding: 6px 10px;
        font-size: 10pt;
    }}
    QLineEdit#SearchBox:focus {{
        border: 2px solid #8B6518;
    }}
    QListWidget#CategoryList {{
        background-color: #FFFFFF;
        border: 1px solid #DDDDDD;
        border-radius: 16px;
    }}
    QListWidget#CategoryList:focus {{
        border: 2px solid #8B6518;
    }}
    QListWidget#CategoryList::item:selected {{
        background-color: {c['canh_light']};
        color: #FFFFFF;
    }}
    QScrollArea#CardScroll {{
        background-color: transparent;
        border: none;
    }}
    QWidget#CardScrollContent {{
        background-color: transparent;
    }}
    QFrame#KysoBanner {{
        background-color: {c['muc_dem']};
        border-radius: 16px;
    }}
    QLabel#KysoBannerTitle {{
        color: {c['vang_tam']};
        font-size: 11pt;
        font-weight: 600;
    }}
    QLabel#KysoBannerBody {{
        color: #FFFFFF;
        font-size: 9pt;
    }}
    QFrame#ServiceCard {{
        background-color: #FFFFFF;
        border: 1px solid #DDDDDD;
        border-radius: 16px;
    }}
    QLabel#CardTitle {{
        color: {c['chu_muc']};
        font-size: 12pt;
        font-weight: 600;
    }}
    QLabel#CardProvider {{
        color: #666666;
        font-size: 9pt;
        font-style: italic;
    }}
    QLabel#CardPurpose {{
        color: {c['chu_muc']};
        font-size: 9pt;
    }}
    QLabel#CardReason {{
        color: #555555;
        font-size: 8pt;
    }}
    QLabel#CardMeta {{
        color: #888888;
        font-size: 8pt;
    }}
    QLabel#StatusBadge {{
        color: #FFFFFF;
        font-size: 8pt;
        font-weight: 600;
        border-radius: 999px;
        padding: 2px 8px;
    }}
    QLabel#RecommendedBadge {{
        background-color: {c['vang_tam']};
        color: {c['muc_dem']};
        font-size: 8pt;
        font-weight: 600;
        border-radius: 999px;
        padding: 2px 8px;
    }}
    QPushButton {{
        background-color: #FFFFFF;
        border: 2px solid {c['canh']};
        color: {c['canh']};
        border-radius: 12px;
        padding: 5px 12px;
    }}
    QPushButton:hover {{
        background-color: #FBEAEA;
    }}
    QPushButton:focus {{
        border: 2px solid #8B6518;
    }}
    QPushButton:disabled {{
        border: 2px solid #CCCCCC;
        color: #AAAAAA;
    }}
    QPushButton#PrimaryButton {{
        background-color: {c['canh']};
        color: #FFFFFF;
        border: 2px solid transparent;
        border-radius: 12px;
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {c['canh_dark']};
    }}
    QPushButton#PrimaryButton:focus {{
        border: 2px solid #8B6518;
    }}
    QLabel#FooterDisclaimer {{
        color: #666666;
        font-size: 8pt;
    }}
    """
