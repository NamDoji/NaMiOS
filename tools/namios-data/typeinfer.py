#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — suy luận kiểu dữ liệu (type inference), có thể sửa.

Tương đương "type detection" của Get & Transform: đọc nguồn thô (CSV luôn ra
chuỗi; JSON đã có kiểu native) rồi ĐOÁN dtype hợp lý cho từng cột. Người dùng
có thể GHI ĐÈ bất kỳ cột nào qua `overrides` trước khi ép kiểu thật
(`cast_rows`) — đây là phần "có thể sửa" theo đúng yêu cầu ở
`docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md` §B.

Module THUẦN: không đọc file, không ném ngoại lệ vì dữ liệu "xấu" trong lúc
đoán kiểu (xấu thì rơi về "str") — chỉ `cast_rows` mới có thể ném lỗi ép kiểu
rõ ràng khi override SAI (ví dụ ép "abc" thành "int").
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, Optional, Sequence

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BOOL_TRUE = {"true", "yes", "1", "có", "x"}
_BOOL_FALSE = {"false", "no", "0", "không", ""}
_EMPTY = {None, ""}


def _is_blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def _try_int(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return False
        try:
            int(s)
            return True
        except ValueError:
            return False
    return False


def _try_float(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return False
        try:
            float(s)
            return True
        except ValueError:
            return False
    return False


def _try_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return True
    if isinstance(v, str):
        return v.strip().lower() in (_BOOL_TRUE | _BOOL_FALSE) - {""}
    return False


def _try_date(v: Any) -> bool:
    if isinstance(v, datetime.date):
        return True
    if isinstance(v, str):
        s = v.strip()
        if not _DATE_RE.match(s):
            return False
        try:
            datetime.date.fromisoformat(s)
            return True
        except ValueError:
            return False
    return False


def infer_column_dtype(values: Sequence[Any]) -> str:
    """Đoán dtype cho MỘT cột từ danh sách giá trị thô (đã bỏ hàng trống hay
    chưa đều được — hàm tự bỏ qua giá trị rỗng khi xét, trừ khi TOÀN BỘ rỗng).

    Thứ tự ưu tiên (giống trực giác người dùng bảng tính): bool > int > float
    > date > str. Một cột chỉ nhận dtype X nếu MỌI giá trị không-rỗng đều hợp
    X (an toàn — không đoán liều)."""
    non_blank = [v for v in values if not _is_blank(v)]
    if not non_blank:
        return "null"
    if all(_try_bool(v) for v in non_blank):
        # "1"/"0" cũng khớp bool VÀ int — ưu tiên int (phổ biến hơn trong dữ
        # liệu bảng tính thật) trừ khi giá trị là bool Python thật hoặc chữ.
        if all(isinstance(v, bool) for v in non_blank) or all(
            isinstance(v, str) and v.strip().lower() in (_BOOL_TRUE | _BOOL_FALSE) - {"0", "1", ""}
            for v in non_blank
        ):
            return "bool"
    if all(_try_int(v) for v in non_blank):
        return "int"
    if all(_try_float(v) for v in non_blank):
        return "float"
    if all(_try_date(v) for v in non_blank):
        return "date"
    return "str"


def infer_dtypes(
    rows: Sequence[Dict[str, Any]],
    columns: Sequence[str],
    *,
    overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Đoán dtype cho mọi cột trong `columns`, rồi áp `overrides` (nếu có) —
    đây là điểm "type inference có thể sửa". Không kiểm tra overrides khớp
    dữ liệu thật ở đây (việc đó để `cast_rows` làm, vì đó là lúc ép kiểu thật
    xảy ra và lỗi phải rõ ràng, trỏ đúng cột/dòng)."""
    from table import SUPPORTED_DTYPES  # import trễ, tránh vòng import lúc nạp module

    out: Dict[str, str] = {}
    for col in columns:
        values = [row.get(col) for row in rows]
        out[col] = infer_column_dtype(values)
    if overrides:
        unknown = set(overrides) - set(columns)
        if unknown:
            raise ValueError(f"overrides nhắc cột không tồn tại: {sorted(unknown)!r}")
        bad = {c: d for c, d in overrides.items() if d not in SUPPORTED_DTYPES}
        if bad:
            raise ValueError(f"override dtype không hợp lệ: {bad!r}")
        for col, dtype in overrides.items():
            out[col] = dtype
    return out


def cast_value(value: Any, dtype: str, *, column: str = "", row_index: int = -1) -> Any:
    """Ép MỘT giá trị thô sang `dtype`. Ném ValueError rõ ràng (cột + dòng)
    nếu override/ dtype không khớp dữ liệu thật — KHÔNG âm thầm trả None."""
    if _is_blank(value):
        return None
    try:
        if dtype == "null":
            return None
        if dtype == "str":
            return str(value)
        if dtype == "int":
            if isinstance(value, bool):
                raise ValueError("bool không ép thẳng sang int trong pipeline này")
            return int(str(value).strip()) if not isinstance(value, int) else value
        if dtype == "float":
            return float(str(value).strip()) if not isinstance(value, float) else value
        if dtype == "bool":
            if isinstance(value, bool):
                return value
            s = str(value).strip().lower()
            if s in _BOOL_TRUE:
                return True
            if s in _BOOL_FALSE - {""}:
                return False
            raise ValueError(f"giá trị {value!r} không phải bool hợp lệ")
        if dtype == "date":
            if isinstance(value, datetime.date):
                return value
            return datetime.date.fromisoformat(str(value).strip())
    except (ValueError, TypeError) as exc:
        where = f" (cột {column!r}, dòng {row_index})" if column else ""
        raise ValueError(f"Không ép được {value!r} sang dtype={dtype!r}{where}: {exc}") from exc
    raise ValueError(f"dtype không hỗ trợ: {dtype!r}")


def cast_rows(
    rows: Sequence[Dict[str, Any]],
    columns: Sequence[str],
    dtypes: Dict[str, str],
) -> list:
    """Ép toàn bộ `rows` sang kiểu trong `dtypes` (áp dụng sau khi đã có
    override). Trả list dict MỚI — không sửa `rows` đầu vào (pure)."""
    out = []
    for i, row in enumerate(rows):
        new_row = {}
        for col in columns:
            new_row[col] = cast_value(row.get(col), dtypes[col], column=col, row_index=i)
        out.append(new_row)
    return out


__all__ = ["infer_column_dtype", "infer_dtypes", "cast_value", "cast_rows"]
