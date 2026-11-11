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
    app tự quyết bố cục của mình, cùng dùng chung bảng màu thương hiệu).

    UI polish 12/11/2026 (consistency — cùng chuẩn hoá với
    ``namios_dichvu.branding``, xem ghi chú đầy đủ ở đó): NÚT = --r-md
    (12px) + ``:focus`` viền 2px #8B6518 (gold-deep); CARD = --r-lg (16px).
    Trước bản này StatusCard=10px, nút=6px, KHÔNG có state ``:focus`` nào —
    cùng lỗ hổng đã vá ở namios_dichvu/namios_manchieu/namios_assistant."""

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
        border-radius: 16px;
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
    QPushButton#RefreshAllButton {{
        background-color: {c['muc_dem']};
        color: {c['vang_tam']};
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 5px 12px;
        font-weight: 600;
    }}
    QPushButton#RefreshAllButton:focus {{
        border: 2px solid {c['vang_tam']};
    }}
    QLabel#FooterDisclaimer {{
        color: #555555;
        font-size: 8pt;
    }}
    """
