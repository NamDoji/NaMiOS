"""Chuẩn hoá văn bản FAIL-CLOSED dùng chung trong ``namios_ux`` (Phụ lục 12).

Gộp một chỗ các mẹo chống lách mà tầng bảo mật khác (``namios_e08.actuator``,
``namios_sys``) đã phải đối mặt: hoa/thường (kể cả Unicode như chữ ``ſ`` dài),
ký tự vô hình (zero-width/BOM/soft-hyphen/bidi-override), dạng toàn-rộng
(fullwidth) và dấu phân tách thay thế (khoảng trắng / gạch dưới / gạch nối).

Không hàm nào ``eval``/nội suy; chỉ chuẩn hoá chuỗi rồi so khớp văn bản thuần.
Mọi hàm fail-closed: khi nghi ngờ thì coi là "khớp dấu hiệu cấm" / "chưa điền",
KHÔNG bao giờ nới lỏng.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

__all__ = [
    "normalize_text",
    "compact",
    "visible",
    "is_blank",
    "contains_forbidden_marker",
    "means_absent",
]

#: Các dấu phân tách bị XOÁ khi "ép sát" chuỗi — chặn kiểu lách "root shell",
#: "root-shell", "send file" thay cho marker gạch-dưới "root_shell"/"send_file".
_SEPARATORS = re.compile(r"[\s_\-./\\|:+~]+")


def _strip_invisible(text: str) -> str:
    """Bỏ ký tự Unicode nhóm điều khiển (``Cc``) và định dạng (``Cf``) — gồm
    zero-width space/joiner, BOM, soft hyphen, các ký tự đảo chiều bidi — vì
    chúng có thể cắt vụn một marker cấm hoặc làm một giá trị RỖNG trông như đã
    điền."""

    return "".join(ch for ch in text if unicodedata.category(ch) not in ("Cc", "Cf"))


def normalize_text(text: str) -> str:
    """NFKC + bỏ ký tự vô hình + ``casefold``. Nền cho mọi so khớp fail-closed:
    gộp fullwidth về ascii, ``ſ``→``s``, xoá zero-width, không phân biệt hoa
    thường (mạnh hơn ``str.lower``)."""

    norm = unicodedata.normalize("NFKC", text)
    norm = _strip_invisible(norm)
    return norm.casefold()


def compact(text: str) -> str:
    """``normalize_text`` rồi XOÁ mọi dấu phân tách — hai chuỗi chỉ khác nhau ở
    khoảng trắng/gạch dưới/gạch nối trở thành MỘT. Dùng để so khớp marker cấm
    bất kể cách gõ."""

    return _SEPARATORS.sub("", normalize_text(text))


def visible(text: str) -> str:
    """Phần nhìn thấy được của chuỗi: NFKC + bỏ ký tự vô hình rồi ``strip``.
    Một giá trị chỉ gồm ký tự vô hình (zero-width...) → rỗng, KHÔNG được coi là
    đã điền."""

    norm = unicodedata.normalize("NFKC", text)
    norm = _strip_invisible(norm)
    return norm.strip()


def is_blank(text: str) -> bool:
    """``True`` nếu chuỗi không có nội dung nhìn thấy (rỗng / chỉ khoảng trắng /
    chỉ ký tự vô hình)."""

    return not visible(text)


def contains_forbidden_marker(text: str, markers: Iterable[str]) -> bool:
    """``True`` nếu BẤT KỲ marker nào (sau khi ``compact``) là chuỗi con của
    ``text`` đã ``compact`` — chặn mọi biến thể hoa/thường/vô hình/fullwidth/
    phân-tách của marker cấm."""

    haystack = compact(text)
    if not haystack:
        return False
    return any(needle in haystack for m in markers if (needle := compact(m)))


#: Giá trị (sau ``compact``) có NGHĨA là "chưa điền thật" dù chuỗi không rỗng —
#: placeholder/phủ định hay gặp. KHÔNG gồm ký tự đơn ("x") để tránh chặn nhầm
#: nội dung hợp lệ; giá trị chỉ gồm dấu phân tách/chấm ("-"/"..."/"/") có
#: ``compact() == ""`` nên bị ``means_absent`` bắt ở nhánh "rỗng sau khi ép sát".
_ABSENT_TOKENS: frozenset[str] = frozenset(
    {
        "na",
        "none",
        "null",
        "nil",
        "tbd",
        "tba",
        "todo",
        "fixme",
        "xxx",
        "wip",
        "pending",
        "placeholder",
        "unknown",
        "unspecified",
        "undefined",
        "notavailable",
        "notapplicable",
        "?",
        "??",
        "???",
    }
)

#: Cụm từ (kiểm trên ``normalize_text`` giữ khoảng trắng) mang nghĩa "chưa có
#: quyền / chờ cấp phép / chưa xác định" — placeholder phủ định tiếng Việt/Anh.
_ABSENT_PHRASES: tuple[str, ...] = (
    "chưa có",
    "chưa co",
    "chua co",
    "chưa rõ",
    "chua ro",
    "chưa xác định",
    "chua xac dinh",
    "không rõ",
    "khong ro",
    "cần cấp phép",
    "can cap phep",
    "cần xin",
    "can xin",
    "chờ cấp phép",
    "cho cap phep",
    "đang chờ",
    "dang cho",
    "đang cập nhật",
    "sẽ bổ sung",
    "sẽ cập nhật",
    "to do",
    "place holder",
    "not available",
    "no license",
    "no rights",
)


def means_absent(value: str) -> bool:
    """FAIL-CLOSED: ``True`` nếu ``value`` KHÔNG mang quyền/nội dung thật —
    rỗng, chỉ ký tự vô hình, một token placeholder (``TODO``/``pending``/
    ``unknown``/``n/a``...), hay một cụm phủ định (``"chưa có — cần cấp phép"``).
    Dùng để GATE license/bằng-chứng-quyền hình nền: ``rights_evidence`` không
    rỗng nhưng nghĩa là "chưa có quyền" PHẢI bị coi là THIẾU."""

    if is_blank(value):
        return True
    token = compact(value)
    if not token or token in _ABSENT_TOKENS:
        # ``not token``: giá trị chỉ gồm dấu phân tách/chấm ("-", "...", "/").
        return True
    phrase_hay = normalize_text(value)
    return any(phrase in phrase_hay for phrase in _ABSENT_PHRASES)
