"""Glossary tiếng Việt thống nhất toàn hệ thống (Phụ lục 12, UX12-037).

TÁI DÙNG ``namios_i18n`` làm kho thuật ngữ — glossary KHÔNG phải một
``dict``/file JSON song song mà chính là catalog VI đăng ký trong
``namios_ux._i18n`` dưới namespace ``ux.glossary.*``. Không có đường đọc file
``design/*.json`` nào ở đây: test tự chứa nạp glossary qua cùng cơ chế
``namios_i18n`` dùng cho toàn repo, hoặc (khi muốn cô lập hoàn toàn khỏi
catalog thật) truyền một ``Mapping`` tự dựng thẳng vào
``missing_required_terms``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from namios_i18n import Lang, has_key, t
from namios_ux import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_ux._text import is_blank

__all__ = [
    "GLOSSARY_NAMESPACE",
    "GLOSSARY_TERM_IDS",
    "REQUIRED_GLOSSARY_TERMS",
    "load_glossary",
    "missing_required_terms",
]

#: Tiền tố key trong catalog ``namios_i18n`` dành cho glossary (UX12-037).
GLOSSARY_NAMESPACE = "ux.glossary"

#: Toàn bộ term-id glossary UX hiện có (bắt buộc + mở rộng/giải thích thêm,
#: vd "driver" — UX12-037: "giải thích 'driver' trong trợ giúp").
GLOSSARY_TERM_IDS: tuple[str, ...] = (
    "tep",
    "thu_muc",
    "ung_dung",
    "may_in",
    "cap_nhat",
    "khoi_phuc",
    "bo_go",
    "trinh_dieu_khien",
)

#: Thuật ngữ BẮT BUỘC thống nhất theo UX12-037: "Tệp", "Thư mục", "Ứng dụng",
#: "Máy in", "Cập nhật", "Khôi phục", "Bộ gõ".
REQUIRED_GLOSSARY_TERMS: tuple[str, ...] = (
    "tep",
    "thu_muc",
    "ung_dung",
    "may_in",
    "cap_nhat",
    "khoi_phuc",
    "bo_go",
)


def load_glossary(
    *, lang: Lang = Lang.VI, term_ids: Sequence[str] = GLOSSARY_TERM_IDS
) -> dict[str, str]:
    """Nạp glossary bằng cách tra catalog i18n chung (``ux.glossary.<id>``).

    Term chưa đăng ký trong catalog (``has_key`` trả ``False``) bị LOẠI khỏi
    kết quả thay vì trả nhãn giả (vd dùng nguyên ``term_id`` làm giá trị) —
    tránh việc một glossary "có vẻ đầy đủ" nhưng thật ra chưa dịch."""

    result: dict[str, str] = {}
    for term_id in term_ids:
        key = f"{GLOSSARY_NAMESPACE}.{term_id}"
        if has_key(key, lang=lang):
            result[term_id] = t(key, lang=lang)
    return result


def missing_required_terms(
    glossary: Mapping[str, str], required: Sequence[str] = REQUIRED_GLOSSARY_TERMS
) -> tuple[str, ...]:
    """UX12-037: thuật ngữ BẮT BUỘC nào thiếu hoặc rỗng trong ``glossary`` đã
    nạp (nhận một ``Mapping`` bất kỳ — cho phép test tự dựng fixture glossary
    riêng, không phụ thuộc catalog thật hay file ngoài). Rỗng = đủ thuật ngữ
    thống nhất tối thiểu.

    FAIL-CLOSED: ``is_blank`` coi giá trị CHỈ gồm ký tự vô hình (zero-width
    space...) là RỖNG — một bản dịch "trống mà trông như có" KHÔNG được tính là
    đã dịch. Tra ``glossary.get(term)`` khớp CHÍNH XÁC key (khác hoa/thường/
    khoảng trắng ở key → coi là thiếu, không khớp lỏng để tránh báo đủ giả)."""

    return tuple(term for term in required if is_blank(glossary.get(term) or ""))
