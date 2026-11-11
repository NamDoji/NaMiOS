"""Màu thương hiệu NaMiOS ("Sen Việt" v2.0) cho giao diện PySide6 của Trung
tâm An toàn. Đọc trực tiếp ``usr/share/namios-branding/logo/brand.json``
(đã cài sẵn trong ảnh qua hook ``0120-namios-branding.hook.chroot``) — KHÔNG
sửa/ghi file đó (sở hữu bởi wave branding khác), chỉ ĐỌC màu. Cùng khuôn
``namios_assistant.branding`` (module khác duy nhất đọc file này theo cách
này) — tái dùng logic, KHÔNG tự chế cách đọc brand.json thứ hai.

FAIL-SAFE: file thiếu/hỏng/đổi cấu trúc (vd chạy module này ngoài ảnh NaMiOS,
môi trường dev/test) -> dùng bộ màu dự phòng CỨNG (giá trị y hệt bản
``brand.json`` tại thời điểm viết module này, 11/11/2026) — app KHÔNG BAO
GIỜ crash vì thiếu file thương hiệu, chỉ mất khả năng tự cập nhật màu nếu
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

#: Màu trạng thái (KHÔNG nằm trong brand.json — đây là ngữ nghĩa riêng của
#: Trung tâm An toàn: xanh=đang bật/tốt, vàng=cần chú ý/không rõ,
#: đỏ=tắt/sự cố, xám=chưa cài. Cố định, không đọc từ brand.json vì đây không
#: phải màu thương hiệu mà là màu TRẠNG THÁI chức năng).
STATUS_OK = "#2E7D32"
STATUS_ATTENTION = "#B8860B"
STATUS_OFF = "#C62828"
STATUS_UNKNOWN = "#8A8A8A"


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
    """Dựng một QSS (Qt Style Sheet) brand-styled cho cửa sổ Trung tâm An
    toàn (bố cục thẻ/card, khác bố cục bong bóng chat của
    ``namios_assistant.branding.build_stylesheet`` — tách riêng hàm để mỗi
    app tự quyết bố cục của mình, cùng dùng chung bảng màu thương hiệu)."""

    c = colors if colors is not None else load_brand_colors()
    return f"""
    QMainWindow, QWidget#AntoanRoot {{
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
    QScrollArea#CardScroll {{
        background-color: transparent;
        border: none;
    }}
    QWidget#CardScrollContent {{
        background-color: transparent;
    }}
    QFrame#StatusCard {{
        background-color: #FFFFFF;
        border: 1px solid #DDDDDD;
        border-radius: 10px;
    }}
    QLabel#CardTitle {{
        color: {c['chu_muc']};
        font-size: 12pt;
        font-weight: 600;
    }}
    QLabel#CardHeadline {{
        color: {c['chu_muc']};
        font-size: 10pt;
        font-weight: 600;
    }}
    QLabel#CardDetail {{
        color: #444444;
        font-size: 9pt;
    }}
    QLabel#CardNotInstalled {{
        color: #777777;
        font-size: 9pt;
        font-style: italic;
    }}
    QPushButton {{
        background-color: #FFFFFF;
        border: 1px solid {c['canh']};
        color: {c['canh']};
        border-radius: 6px;
        padding: 5px 12px;
    }}
    QPushButton:hover {{
        background-color: #FBEAEA;
    }}
    QPushButton:disabled {{
        border: 1px solid #CCCCCC;
        color: #AAAAAA;
    }}
    QPushButton#PrimaryButton {{
        background-color: {c['canh']};
        color: #FFFFFF;
        border: none;
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {c['canh_dark']};
    }}
    QPushButton#RefreshAllButton {{
        background-color: {c['muc_dem']};
        color: {c['vang_tam']};
        border: none;
        font-weight: 600;
    }}
    QLabel#FooterDisclaimer {{
        color: #555555;
        font-size: 8pt;
    }}
    """
