"""Nhãn phân phối ĐÚNG cho Launcher/App Center (APP11-001/013).

Bốn nhãn phụ: "Cài trên máy" / "Dịch vụ web" / "Qua Wine (đã kiểm thử)" / "Cần
kết nối". Bất biến (APP11-001 nghiệm thu, Phụ lục 11 §1 bảng hình thức tích
hợp): ``official_web`` KHÔNG BAO GIỜ hiển thị "bản Linux"/"đã cài" — hàm
``delivery_label`` chọn nhãn bằng ``match`` đủ ba ``DeliveryType``, không có
nhánh ngầm nào gán ``INSTALLED`` cho web. ``offline=True`` chỉ khi khai THẬT:
``EssentialsManifest.offline`` mặc định ``False`` (xem ``_types.py``) — web app
chỉ ``offline=True`` khi caller tự xác nhận tường minh tại nguồn khai (vd PWA có
service worker đã kiểm), không có đường "ngầm" bật lên.
"""

from __future__ import annotations

import unicodedata

from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._types import DeliveryLabel, DeliveryType, EssentialsManifest
from namios_i18n import Lang, t

__all__ = ["delivery_label", "label_text", "needs_connection", "web_label_is_honest"]

#: STEM (gốc từ đã BỎ DẤU) KHÔNG BAO GIỜ được xuất hiện trong nhãn của một
#: ``official_web`` shortcut (APP11-001/036: "không ghi 'đã cài app Linux' cho
#: shortcut web"). Dò trên chuỗi đã ``_fold`` (bỏ dấu + hạ chữ) nên bắt được
#: mọi cách viết/đồng nghĩa paraphrase của "cài đặt trên máy"/"bản Linux" mà
#: KHÔNG phá tên brand hợp lệ như "Zalo Web".
_WEB_DISHONEST_STEMS: tuple[str, ...] = (
    "cai",
    "tren may",
    "ban linux",
    "linux app",
    "ung dung linux",
    "phan mem linux",
    "native",
    "installed",
    "desktop app",
)


def _fold(s: str) -> str:
    """Hạ chữ + bỏ dấu tiếng Việt (đ→d, tước dấu kết hợp) để so khớp STEM bền
    với mọi casing/khoảng-trắng/đồng-nghĩa có dấu."""

    s = s.strip().lower().replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def delivery_label(m: EssentialsManifest) -> DeliveryLabel:
    """Chọn nhãn phụ ĐÚNG theo ``delivery_type`` (APP11-001/013). Cấu trúc
    (xét đủ 3 ``DeliveryType``) chặn lỗi gọi nhầm ngay từ kiểu — không có
    nhánh nào gán ``INSTALLED``/``WINE_TESTED`` cho ``OFFICIAL_WEB``."""

    if m.delivery_type is DeliveryType.INSTALLED_NATIVE:
        return DeliveryLabel.INSTALLED
    if m.delivery_type is DeliveryType.WINE_OPTIONAL:
        return DeliveryLabel.WINE_TESTED
    # OFFICIAL_WEB: cần mạng trừ khi khai rõ offline=True (hiếm — PWA offline thật).
    if not m.offline:
        return DeliveryLabel.NEEDS_CONNECTION
    return DeliveryLabel.WEB_SERVICE


def label_text(label: DeliveryLabel, *, lang: Lang = Lang.VI) -> str:
    """Chuỗi hiển thị song ngữ cho một nhãn phụ."""

    return t(f"essentials.label.{label.value}", lang=lang)


def needs_connection(m: EssentialsManifest) -> bool:
    """App có cần mạng mới mở được không (APP11-001/007). Chỉ web app KHÔNG
    khai offline mới cần — installed_native/wine_optional coi là chạy cục bộ
    (mức offline thật của TỪNG chức năng do support_matrix mô tả riêng)."""

    return m.delivery_type is DeliveryType.OFFICIAL_WEB and not m.offline


def web_label_is_honest(m: EssentialsManifest, display_text: str) -> bool:
    """APP11-001/036: ``display_text`` dành cho một ``official_web`` shortcut có
    chứa cụm từ gây hiểu lầm "đã cài"/"bản Linux" không. Non-web delivery type
    luôn ``True`` (không áp dụng)."""

    if m.delivery_type is not DeliveryType.OFFICIAL_WEB:
        return True
    folded = _fold(display_text)
    return not any(stem in folded for stem in _WEB_DISHONEST_STEMS)
