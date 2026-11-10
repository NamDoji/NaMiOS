#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — các bước biến đổi (Transform steps).

Tương đương các bước M-step của Get & Transform: Filter / Select / Rename /
Merge (join) / Append (union) / Unpivot / Group-by. MỖI bước là:

  * MỘT dataclass bất biến (frozen) mô tả tham số của bước — tự
    serialize/deserialize JSON được (`to_dict`/`from_dict`), nên một DANH
    SÁCH bước (`Pipeline.steps`) ghi lại được, lưu ra đĩa, nạp lại, và
    "tái lập" (replay) ra đúng kết quả cũ. Đây là điểm cốt lõi của "Get &
    Transform tương đương" theo spec kit — KHÔNG phải branding "Power Query".
  * MỘT hàm `apply(table, aux_tables)` THUẦN: không sửa `table`/`aux_tables`
    đầu vào, luôn trả `Table` MỚI. Cùng input (table + aux_tables) + cùng
    tham số bước ⇒ LUÔN cùng output — đây là điều kiện để test replay
    (`tests/test_replay.py`) khẳng định "serialize → reload → replay →
    identical output".

`aux_tables` dùng cho Merge/Append: dict tên bảng phụ -> `Table`, do
`pipeline.Pipeline` nạp sẵn từ `aux_sources` trước khi chạy các bước.

Trạng thái triển khai: 7 loại bước trên đã có + test cho từng loại. KHÔNG có
"calculated column"/custom M-code tuỳ ý (Power Query cho viết công thức M bất
kỳ) — đây là giới hạn CÓ CHỦ Ý để giữ mọi bước thuần/an toàn/replay được mà
không cần một engine ngôn ngữ M đầy đủ.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from table import Table

_AGG_FUNCS = frozenset({"sum", "count", "avg", "min", "max"})
_FILTER_OPS = frozenset({"eq", "ne", "gt", "gte", "lt", "lte", "contains", "in"})


class StepError(ValueError):
    """Tham số bước không hợp lệ, hoặc không áp dụng được lên Table đưa vào."""


# --------------------------------------------------------------------------- #
# Filter
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FilterStep:
    KIND = "filter"
    column: str
    op: str
    value: Any = None

    def __post_init__(self) -> None:
        if self.op not in _FILTER_OPS:
            raise StepError(f"filter.op không hợp lệ: {self.op!r} (hợp lệ: {sorted(_FILTER_OPS)!r})")

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        if self.column not in table.columns:
            raise StepError(f"filter: không có cột {self.column!r}")
        kept = tuple(row for row in table.rows if self._matches(row[self.column]))
        return Table(columns=table.columns, dtypes=dict(table.dtypes), rows=kept)

    def _matches(self, v: Any) -> bool:
        if self.op in ("gt", "gte", "lt", "lte") and v is None:
            return False  # None không so sánh thứ tự được — loại khỏi kết quả
        if self.op == "eq":
            return v == self.value
        if self.op == "ne":
            return v != self.value
        if self.op == "gt":
            return v > self.value
        if self.op == "gte":
            return v >= self.value
        if self.op == "lt":
            return v < self.value
        if self.op == "lte":
            return v <= self.value
        if self.op == "contains":
            return v is not None and str(self.value) in str(v)
        if self.op == "in":
            return v in self.value
        raise StepError(f"filter.op không hỗ trợ: {self.op!r}")

    def to_dict(self) -> dict:
        return {"kind": self.KIND, "column": self.column, "op": self.op, "value": self.value}

    @classmethod
    def from_dict(cls, d: dict) -> "FilterStep":
        return cls(column=d["column"], op=d["op"], value=d.get("value"))


# --------------------------------------------------------------------------- #
# Select
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SelectStep:
    KIND = "select"
    columns: Tuple[str, ...]

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        missing = [c for c in self.columns if c not in table.columns]
        if missing:
            raise StepError(f"select: không có cột {missing!r}")
        new_dtypes = {c: table.dtypes[c] for c in self.columns}
        new_rows = tuple({c: row[c] for c in self.columns} for row in table.rows)
        return Table(columns=tuple(self.columns), dtypes=new_dtypes, rows=new_rows)

    def to_dict(self) -> dict:
        return {"kind": self.KIND, "columns": list(self.columns)}

    @classmethod
    def from_dict(cls, d: dict) -> "SelectStep":
        return cls(columns=tuple(d["columns"]))


# --------------------------------------------------------------------------- #
# Rename
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RenameStep:
    KIND = "rename"
    mapping: Dict[str, str]

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        missing = [c for c in self.mapping if c not in table.columns]
        if missing:
            raise StepError(f"rename: không có cột nguồn {missing!r}")
        new_columns = tuple(self.mapping.get(c, c) for c in table.columns)
        if len(set(new_columns)) != len(new_columns):
            raise StepError(f"rename: tên cột trùng sau khi đổi: {new_columns!r}")
        new_dtypes = {self.mapping.get(c, c): dtype for c, dtype in table.dtypes.items()}
        new_rows = tuple(
            {self.mapping.get(c, c): row[c] for c in table.columns} for row in table.rows
        )
        return Table(columns=new_columns, dtypes=new_dtypes, rows=new_rows)

    def to_dict(self) -> dict:
        return {"kind": self.KIND, "mapping": dict(self.mapping)}

    @classmethod
    def from_dict(cls, d: dict) -> "RenameStep":
        return cls(mapping=dict(d["mapping"]))


# --------------------------------------------------------------------------- #
# Merge (join)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MergeStep:
    KIND = "merge"
    right_table: str  # tên bảng phụ trong aux_tables
    left_on: str
    right_on: str
    how: str = "inner"  # "inner" | "left"

    def __post_init__(self) -> None:
        if self.how not in ("inner", "left"):
            raise StepError(f"merge.how không hợp lệ: {self.how!r} (chỉ 'inner'/'left')")

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        if self.right_table not in aux_tables:
            raise StepError(
                f"merge: không có bảng phụ {self.right_table!r} "
                f"(đã nạp: {sorted(aux_tables)!r})"
            )
        right = aux_tables[self.right_table]
        if self.left_on not in table.columns:
            raise StepError(f"merge: left_on {self.left_on!r} không có trong bảng trái")
        if self.right_on not in right.columns:
            raise StepError(f"merge: right_on {self.right_on!r} không có trong bảng phải")

        # Cột bảng phải được thêm vào, trừ cột khóa phải nếu nó TRÙNG TÊN với
        # khóa trái (tránh 2 cột cùng tên lặp giá trị join). Nếu left_on và
        # right_on khác tên, cả hai được giữ. Các cột trùng tên KHÁC khóa
        # không được hỗ trợ (phải rename trước khi merge) — hành vi đơn
        # giản/đoán được, tránh phải bịa quy tắc tự thêm hậu tố "_x"/"_y".
        if self.right_on == self.left_on:
            right_extra_cols = [c for c in right.columns if c != self.right_on]
        else:
            right_extra_cols = list(right.columns)
        clash = (set(table.columns) & set(right_extra_cols)) - {self.left_on}
        if clash:
            raise StepError(
                f"merge: cột trùng tên giữa hai bảng (ngoài khóa join): {sorted(clash)!r} "
                "— hãy rename trước khi merge"
            )

        index: Dict[Any, List[Dict[str, Any]]] = {}
        for rrow in right.rows:
            index.setdefault(rrow[self.right_on], []).append(rrow)

        out_columns = tuple(list(table.columns) + right_extra_cols)
        out_dtypes = dict(table.dtypes)
        for c in right_extra_cols:
            out_dtypes[c] = right.dtypes[c]

        out_rows: List[Dict[str, Any]] = []
        for lrow in table.rows:
            matches = index.get(lrow[self.left_on], [])
            if matches:
                for rrow in matches:
                    new_row = dict(lrow)
                    for c in right_extra_cols:
                        new_row[c] = rrow[c]
                    out_rows.append(new_row)
            elif self.how == "left":
                new_row = dict(lrow)
                for c in right_extra_cols:
                    new_row[c] = None
                out_rows.append(new_row)
            # how == "inner" và không khớp -> bỏ dòng, không thêm gì

        return Table(columns=out_columns, dtypes=out_dtypes, rows=tuple(out_rows))

    def to_dict(self) -> dict:
        return {
            "kind": self.KIND,
            "right_table": self.right_table,
            "left_on": self.left_on,
            "right_on": self.right_on,
            "how": self.how,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MergeStep":
        return cls(
            right_table=d["right_table"],
            left_on=d["left_on"],
            right_on=d["right_on"],
            how=d.get("how", "inner"),
        )


# --------------------------------------------------------------------------- #
# Append (union)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AppendStep:
    KIND = "append"
    other_table: str  # tên bảng phụ trong aux_tables

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        if self.other_table not in aux_tables:
            raise StepError(
                f"append: không có bảng phụ {self.other_table!r} "
                f"(đã nạp: {sorted(aux_tables)!r})"
            )
        other = aux_tables[self.other_table]
        if set(table.columns) != set(other.columns):
            raise StepError(
                "append: hai bảng phải có CÙNG bộ cột trong prototype này "
                f"(trái={sorted(table.columns)!r}, phải={sorted(other.columns)!r}). "
                "Dùng select/rename để khớp schema trước khi append."
            )
        merged_dtypes = dict(table.dtypes)
        for c, dtype in other.dtypes.items():
            if merged_dtypes.get(c, dtype) != dtype:
                # Kiểu khác nhau giữa 2 nguồn cho cùng cột -> hạ an toàn về "str"
                merged_dtypes[c] = "str"
        new_rows = tuple(list(table.rows) + [dict({c: row[c] for c in table.columns}) for row in other.rows])
        return Table(columns=table.columns, dtypes=merged_dtypes, rows=new_rows)

    def to_dict(self) -> dict:
        return {"kind": self.KIND, "other_table": self.other_table}

    @classmethod
    def from_dict(cls, d: dict) -> "AppendStep":
        return cls(other_table=d["other_table"])


# --------------------------------------------------------------------------- #
# Unpivot
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class UnpivotStep:
    KIND = "unpivot"
    id_columns: Tuple[str, ...]
    value_columns: Tuple[str, ...]
    name_col: str = "Attribute"
    value_col: str = "Value"

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        missing = [c for c in list(self.id_columns) + list(self.value_columns) if c not in table.columns]
        if missing:
            raise StepError(f"unpivot: không có cột {missing!r}")
        out_columns = tuple(list(self.id_columns) + [self.name_col, self.value_col])
        if len(set(out_columns)) != len(out_columns):
            raise StepError(f"unpivot: tên cột đầu ra trùng nhau: {out_columns!r}")

        value_dtypes = {table.dtypes[c] for c in self.value_columns}
        value_dtype = next(iter(value_dtypes)) if len(value_dtypes) == 1 else "str"

        out_dtypes = {c: table.dtypes[c] for c in self.id_columns}
        out_dtypes[self.name_col] = "str"
        out_dtypes[self.value_col] = value_dtype

        out_rows: List[Dict[str, Any]] = []
        for row in table.rows:
            base = {c: row[c] for c in self.id_columns}
            for vc in self.value_columns:
                new_row = dict(base)
                new_row[self.name_col] = vc
                new_row[self.value_col] = row[vc]
                out_rows.append(new_row)
        return Table(columns=out_columns, dtypes=out_dtypes, rows=tuple(out_rows))

    def to_dict(self) -> dict:
        return {
            "kind": self.KIND,
            "id_columns": list(self.id_columns),
            "value_columns": list(self.value_columns),
            "name_col": self.name_col,
            "value_col": self.value_col,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UnpivotStep":
        return cls(
            id_columns=tuple(d["id_columns"]),
            value_columns=tuple(d["value_columns"]),
            name_col=d.get("name_col", "Attribute"),
            value_col=d.get("value_col", "Value"),
        )


# --------------------------------------------------------------------------- #
# Group by
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GroupByStep:
    KIND = "group_by"
    by: Tuple[str, ...]
    #: tên_cột_ra -> (hàm, cột_nguồn). hàm trong {"sum","count","avg","min","max"}.
    #: cột_nguồn == "*" chỉ hợp lệ với "count" (đếm toàn bộ dòng trong nhóm).
    aggregations: Dict[str, Tuple[str, str]]

    def __post_init__(self) -> None:
        for out_col, (func, src) in self.aggregations.items():
            if func not in _AGG_FUNCS:
                raise StepError(f"group_by: hàm tổng hợp không hợp lệ: {func!r}")
            if src == "*" and func != "count":
                raise StepError("group_by: cột nguồn '*' chỉ dùng với hàm 'count'")

    def apply(self, table: Table, aux_tables: Dict[str, Table]) -> Table:
        missing_by = [c for c in self.by if c not in table.columns]
        if missing_by:
            raise StepError(f"group_by: không có cột nhóm {missing_by!r}")
        for out_col, (func, src) in self.aggregations.items():
            if src != "*" and src not in table.columns:
                raise StepError(f"group_by: không có cột nguồn tổng hợp {src!r}")

        groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
        order: List[Tuple[Any, ...]] = []
        for row in table.rows:
            key = tuple(row[c] for c in self.by)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(row)

        out_columns = tuple(list(self.by) + list(self.aggregations.keys()))
        out_rows: List[Dict[str, Any]] = []
        for key in order:
            rows_in_group = groups[key]
            new_row = dict(zip(self.by, key))
            for out_col, (func, src) in self.aggregations.items():
                new_row[out_col] = self._aggregate(func, src, rows_in_group)
            out_rows.append(new_row)

        out_dtypes = {c: table.dtypes[c] for c in self.by}
        for out_col, (func, src) in self.aggregations.items():
            if func == "count":
                out_dtypes[out_col] = "int"
            else:
                sample_vals = [r[out_col] for r in out_rows if r[out_col] is not None]
                if sample_vals and all(isinstance(v, int) and not isinstance(v, bool) for v in sample_vals):
                    out_dtypes[out_col] = "int"
                else:
                    out_dtypes[out_col] = "float"

        return Table(columns=out_columns, dtypes=out_dtypes, rows=tuple(out_rows))

    @staticmethod
    def _aggregate(func: str, src: str, rows: Sequence[Dict[str, Any]]) -> Any:
        if func == "count":
            if src == "*":
                return len(rows)
            return sum(1 for r in rows if r[src] is not None)
        values = [r[src] for r in rows if r[src] is not None]
        if func == "sum":
            return sum(values) if values else 0
        if func == "avg":
            return (sum(values) / len(values)) if values else None
        if func == "min":
            return min(values) if values else None
        if func == "max":
            return max(values) if values else None
        raise StepError(f"group_by: hàm không hỗ trợ: {func!r}")

    def to_dict(self) -> dict:
        return {
            "kind": self.KIND,
            "by": list(self.by),
            "aggregations": {k: list(v) for k, v in self.aggregations.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GroupByStep":
        return cls(
            by=tuple(d["by"]),
            aggregations={k: tuple(v) for k, v in d["aggregations"].items()},
        )


STEP_REGISTRY = {
    FilterStep.KIND: FilterStep,
    SelectStep.KIND: SelectStep,
    RenameStep.KIND: RenameStep,
    MergeStep.KIND: MergeStep,
    AppendStep.KIND: AppendStep,
    UnpivotStep.KIND: UnpivotStep,
    GroupByStep.KIND: GroupByStep,
}


def step_from_dict(d: dict):
    kind = d.get("kind")
    cls = STEP_REGISTRY.get(kind)
    if cls is None:
        raise StepError(f"Không rõ loại bước: {kind!r} (hợp lệ: {sorted(STEP_REGISTRY)!r})")
    return cls.from_dict(d)


__all__ = [
    "StepError",
    "FilterStep",
    "SelectStep",
    "RenameStep",
    "MergeStep",
    "AppendStep",
    "UnpivotStep",
    "GroupByStep",
    "STEP_REGISTRY",
    "step_from_dict",
]
