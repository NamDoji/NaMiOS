#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — cấu trúc bảng (Table) thuần Python.

Module THUẦN (không I/O), biểu diễn một bảng dữ liệu trong-tiến-trình: danh
sách cột theo thứ tự + kiểu dữ liệu từng cột (dtype) + các dòng (mỗi dòng là
một dict cột->giá trị).

Mọi hàm ở đây là HÀM THUẦN (pure): không hàm nào sửa Table đầu vào — luôn trả
về Table MỚI (dict/tuple mới). Đây là điều kiện để các bước biến đổi
(`steps.py`) tái lập được (replay cho ra đúng kết quả cũ).

Trạng thái triển khai: prototype — đủ cho CSV/JSON cục bộ + các bước biến đổi
trong `steps.py`. KHÔNG phải một DataFrame engine đầy đủ (không index, không
kiểu categorical, không lazy evaluation).
"""
from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: Các dtype được hỗ trợ. "null" dành cho cột toàn giá trị rỗng (không đoán
#: được kiểu gì khác). Danh sách này PHẢI khớp `typeinfer.py`.
SUPPORTED_DTYPES = frozenset({"int", "float", "bool", "date", "str", "null"})


def _json_default(value: Any) -> Any:
    """Chuyển các kiểu Python không tự serialize JSON được (date) thành chuỗi.

    Dùng cho hash + to_dict — KHÔNG dùng cho ghi xlsx (xlsx_writer.py giữ
    nguyên kiểu Python thật, ví dụ `datetime.date`, để openpyxl định dạng ô
    đúng là ngày)."""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(f"Không serialize được giá trị kiểu {type(value)!r}: {value!r}")


@dataclass(frozen=True)
class Table:
    """Bảng dữ liệu bất biến theo quy ước: không có hàm nào trong pipeline này
    được sửa `.rows`/`.columns`/`.dtypes` sau khi tạo — luôn tạo bản mới.

    `columns` giữ THỨ TỰ cột hiển thị. `dtypes` là dict cột->tên kiểu
    (SUPPORTED_DTYPES). `rows` là tuple các dict {cột: giá_trị}; giá trị đã
    được ép kiểu theo `dtypes` (int/float/bool/str/`datetime.date`/None).
    """

    columns: Tuple[str, ...]
    dtypes: Dict[str, str]
    rows: Tuple[Dict[str, Any], ...]

    def __post_init__(self) -> None:
        if len(set(self.columns)) != len(self.columns):
            raise ValueError(f"Table có cột trùng tên: {self.columns!r}")
        missing_dtype = [c for c in self.columns if c not in self.dtypes]
        if missing_dtype:
            raise ValueError(f"Thiếu dtype cho cột: {missing_dtype!r}")
        bad_dtype = {c: t for c, t in self.dtypes.items() if t not in SUPPORTED_DTYPES}
        if bad_dtype:
            raise ValueError(f"dtype không hợp lệ: {bad_dtype!r}")
        col_set = set(self.columns)
        for i, row in enumerate(self.rows):
            if set(row.keys()) != col_set:
                raise ValueError(
                    f"Dòng {i} có cột khác với Table.columns: "
                    f"{sorted(row.keys())!r} != {sorted(col_set)!r}"
                )

    # ------------------------------------------------------------------ #
    # Dựng từ dữ liệu thô
    # ------------------------------------------------------------------ #
    @classmethod
    def from_rows(
        cls,
        rows: Sequence[Dict[str, Any]],
        *,
        columns: Optional[Sequence[str]] = None,
        dtypes: Optional[Dict[str, str]] = None,
    ) -> "Table":
        """Dựng Table từ danh sách dict thô. Nếu không cho `columns`, lấy
        theo thứ tự xuất hiện lần đầu trên toàn bộ `rows` (hợp union, giữ thứ
        tự). Nếu không cho `dtypes`, mọi cột tạm gán "str" (gọi
        `typeinfer.infer_dtypes` + `cast_rows` riêng để có suy luận thật)."""
        if columns is None:
            seen: List[str] = []
            seen_set = set()
            for row in rows:
                for k in row.keys():
                    if k not in seen_set:
                        seen.append(k)
                        seen_set.add(k)
            columns = tuple(seen)
        else:
            columns = tuple(columns)
        if dtypes is None:
            dtypes = {c: "str" for c in columns}
        norm_rows = tuple(
            {c: row.get(c) for c in columns} for row in rows
        )
        return cls(columns=columns, dtypes=dict(dtypes), rows=norm_rows)

    # ------------------------------------------------------------------ #
    # Serialize / hash (để test replay + lưu history)
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        """Dạng dict JSON-hoá được (date -> isoformat). Dùng cho hash + debug,
        KHÔNG dùng để ghi xlsx (xem `xlsx_writer.py`)."""
        return {
            "columns": list(self.columns),
            "dtypes": dict(self.dtypes),
            "rows": [
                {c: _json_default(v) if isinstance(v, (datetime.date, datetime.datetime)) else v
                 for c, v in row.items()}
                for row in self.rows
            ],
        }

    def content_hash(self) -> str:
        """SHA-256 của nội dung bảng (cột + dtype + từng dòng, THEO ĐÚNG THỨ
        TỰ). Hai Table có cùng hash này được xem là 'identical output' —
        dùng trong test replay (chạy lại pipeline phải ra cùng hash)."""
        payload = json.dumps(self.to_dict(), sort_keys=False, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def __len__(self) -> int:
        return len(self.rows)

    def column(self, name: str) -> List[Any]:
        if name not in self.columns:
            raise KeyError(f"Không có cột {name!r} (có: {list(self.columns)!r})")
        return [row[name] for row in self.rows]

    def to_preview(self, limit: int = 10) -> str:
        """Bản xem nhanh dạng text (debug), KHÔNG dùng để so sánh kết quả."""
        lines = [" | ".join(self.columns)]
        for row in self.rows[:limit]:
            lines.append(" | ".join(str(row[c]) for c in self.columns))
        more = len(self.rows) - limit
        if more > 0:
            lines.append(f"... (+{more} dòng nữa)")
        return "\n".join(lines)


def tables_equal(a: Table, b: Table) -> bool:
    """So sánh nội dung hai Table (dùng trong test thay cho `==` dataclass để
    rõ ràng ý định: so sánh KẾT QUẢ, không so sánh identity object)."""
    return a.content_hash() == b.content_hash()


__all__ = ["SUPPORTED_DTYPES", "Table", "tables_equal"]
