"""ECO-007 — Tìm theo tên phổ thông ("khai thuế", "bảo hiểm", "học bạ",
"hóa đơn"...), có/không dấu, không phân biệt hoa thường.

Tự viết fold tiếng Việt riêng ở đây (KHÔNG import ``namios_catalog._fold`` —
module đó là PRIVATE của WP4; ``namios_eco`` không phải WP4, không import
chéo vào implementation private của module khác theo quy ước M1-INTERFACES
§0 "KHÔNG import chéo vào implementation của module khác"). Thuật toán fold
giống WP4 (đã kiểm chứng đúng cho tiếng Việt): xử lý "đ" tường minh, NFD bỏ
dấu tổ hợp, NFC + casefold lại.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from namios_eco.models import ServiceEntry

__all__ = ["fold_vn", "SearchHit", "search_services"]

_DJ_MAP = {"đ": "d", "Đ": "D"}
_WS_RE = re.compile(r"\s+")


def fold_vn(text: str) -> str:
    """Chuẩn hoá KHÔNG DẤU, không phân biệt hoa/thường — CHỈ dùng cho index
    tìm kiếm (bản sao trong bộ nhớ), KHÔNG dùng để đổi tên hiển thị thật."""

    translated = "".join(_DJ_MAP.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFD", translated)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    recomposed = unicodedata.normalize("NFC", stripped)
    return recomposed.casefold()


def _collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text)


@dataclass(frozen=True)
class SearchHit:
    """Kết quả tìm kiếm — hiển thị đủ thông tin trung thực (ECO-007 §4.1):
    nhà cung cấp, mode, khả năng hoàn thành quy trình, yêu cầu token/đăng
    nhập, ngày kiểm. KHÔNG tự gắn nhãn "ứng dụng chính thức của NaMiOS"."""

    entry: ServiceEntry
    requires_account_or_token: bool  # suy từ account_condition/dependencies không rỗng


def _requires_account_or_token(entry: ServiceEntry) -> bool:
    if entry.dependencies:
        return True
    condition = entry.account_condition.strip().casefold()
    if not condition:
        return False
    no_requirement_markers = ("không cần", "khong can", "không yêu cầu", "khong yeu cau")
    return not any(marker in condition for marker in no_requirement_markers)


def _haystack(entry: ServiceEntry) -> str:
    parts = [entry.id, entry.provider, entry.purpose]
    if entry.agency:
        parts.append(entry.agency)
    return " ".join(parts)


def search_services(
    entries: Sequence[ServiceEntry], query: str, *, limit: int = 50
) -> tuple[SearchHit, ...]:
    """Tìm theo tên phổ thông, accent-insensitive, không phân biệt hoa/thường.
    Khớp SUBSTRING trên ``id``/``provider``/``purpose``/``agency`` đã fold.
    Kết quả thứ tự xác định (theo ``purpose`` rồi ``id``) để ổn định test/UI."""

    if limit <= 0:
        return ()
    folded_query = _collapse_ws(fold_vn(query)).strip()
    if not folded_query:
        return ()

    hits: list[ServiceEntry] = []
    for entry in entries:
        haystack = _collapse_ws(fold_vn(_haystack(entry)))
        if folded_query in haystack:
            hits.append(entry)

    hits.sort(key=lambda e: (e.purpose, e.id))
    return tuple(
        SearchHit(entry=e, requires_account_or_token=_requires_account_or_token(e))
        for e in hits[:limit]
    )
