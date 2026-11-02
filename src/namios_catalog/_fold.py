"""Chuẩn hóa chuỗi tiếng Việt cho mục đích TÌM KIẾM (UX-006).

Chỉ dùng cho INDEX tìm kiếm (bản sao trong bộ nhớ) — KHÔNG được dùng để đổi
tên hiển thị hoặc tên file thật của entry (FACT M1-INTERFACES §7.2: "Chuẩn
hóa chỉ áp cho index tìm kiếm (fold dấu + casefold trên bản sao), giữ nguyên
tên hiển thị").

Thuật toán:
1. Thay "đ"/"Đ" tường minh (KHÔNG decompose qua NFD vì chữ "đ" không phải
   ký tự có dấu kết hợp — là chữ cái riêng "d có gạch ngang").
2. NFD để tách dấu thanh/dấu phụ ra khỏi ký tự gốc.
3. Bỏ mọi ký tự thuộc category Unicode "Mn" (combining mark) — tức bỏ dấu.
4. NFC lại rồi casefold (không phân biệt hoa/thường, kể cả non-ASCII).
"""

from __future__ import annotations

import unicodedata

__all__ = ["fold_vn"]

_DJ_MAP = {
    "đ": "d",
    "Đ": "D",
}


def fold_vn(text: str) -> str:
    """Trả bản chuẩn hóa KHÔNG DẤU, không phân biệt hoa/thường của ``text``.

    Dùng để so khớp trong index tìm kiếm; KHÔNG dùng để hiển thị hay đổi tên
    file thật.
    """

    translated = "".join(_DJ_MAP.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFD", translated)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    recomposed = unicodedata.normalize("NFC", stripped)
    return recomposed.casefold()
