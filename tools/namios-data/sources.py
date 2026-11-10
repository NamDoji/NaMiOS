#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — kết nối nguồn (CSV/JSON cục bộ; SQL/web bị chặn).

Tương đương bước "Get" của Get & Transform: đọc một nguồn thô thành
`table.Table`. Chỉ hai loại nguồn THỰC SỰ hoạt động trong prototype này: CSV
và JSON cục bộ (đọc từ đĩa, không ra mạng bao giờ). Nguồn SQL/web được khai
báo trong `SourceSpec` để phục vụ test consent-gate (`consent.py`) và để tài
liệu hoá rõ đường hướng mở rộng, nhưng **chưa có client mạng/SQL thật nào**
được nối — xem `read_source()` dưới.

Trạng thái triển khai: `partial` — csv/json ĐỦ DÙNG + có test; sql/web chỉ có
cổng consent, ném `NotImplementedError` tường minh nếu đi qua cổng. Không
tuyên bố "đã hỗ trợ kết nối SQL/web".
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict

from consent import ConsentRequiredError, check_consent
from table import Table
from typeinfer import cast_rows, infer_dtypes


@dataclass(frozen=True)
class SourceSpec:
    """Khai báo MỘT nguồn dữ liệu — tự serialize được (dùng trong
    `pipeline.Pipeline.to_json`), KHÔNG lưu secret dạng rõ (xem `options`
    dùng cho đường dẫn/encoding/delimiter, không phải mật khẩu)."""

    kind: str  # "csv" | "json" | "sql" | "web"
    uri: str
    options: Dict[str, Any] = field(default_factory=dict)
    type_overrides: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "uri": self.uri,
            "options": dict(self.options),
            "type_overrides": dict(self.type_overrides),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SourceSpec":
        return cls(
            kind=d["kind"],
            uri=d["uri"],
            options=dict(d.get("options", {})),
            type_overrides=dict(d.get("type_overrides", {})),
        )


def _read_csv_rows(path: str, options: Dict[str, Any]) -> tuple:
    delimiter = options.get("delimiter", ",")
    encoding = options.get("encoding", "utf-8-sig")  # -sig: tự bỏ BOM nếu có
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Không tìm thấy file CSV: {path!r}")
    with open(path, "r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        rows = [dict(r) for r in reader]
        columns = tuple(reader.fieldnames or [])
    return rows, columns


def _read_json_rows(path: str, options: Dict[str, Any]) -> tuple:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Không tìm thấy file JSON: {path!r}")
    encoding = options.get("encoding", "utf-8")
    with open(path, "r", encoding=encoding) as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "rows" in data:
        data = data["rows"]
    if not isinstance(data, list):
        raise ValueError(
            f"JSON nguồn phải là một LIST object phẳng (hoặc {{'rows': [...]}}); "
            f"nhận kiểu {type(data).__name__}"
        )
    if data and not all(isinstance(r, dict) for r in data):
        raise ValueError("Mọi phần tử trong JSON nguồn phải là object (dict) phẳng")
    seen: list = []
    seen_set: set = set()
    for row in data:
        for k in row.keys():
            if k not in seen_set:
                seen.append(k)
                seen_set.add(k)
    return data, tuple(seen)


def read_source(spec: SourceSpec, *, consent: bool = False) -> Table:
    """Đọc một `SourceSpec` thành `Table` ĐÃ ép kiểu (type inference +
    override áp ngay ở bước đọc — khớp "type inference có thể sửa" trong
    spec kit).

    Nguồn mạng (sql/web) đi qua `consent.check_consent` TRƯỚC — nếu thiếu
    `consent=True`, ném `ConsentRequiredError` và KHÔNG thử mở bất kỳ kết nối
    nào (không có side-effect một phần)."""
    query = spec.options.get("query", "") if spec.kind in ("sql", "web") else ""
    check_consent(spec.kind, spec.uri, consent=consent, query=query)

    if spec.kind == "csv":
        raw_rows, columns = _read_csv_rows(spec.uri, spec.options)
    elif spec.kind == "json":
        raw_rows, columns = _read_json_rows(spec.uri, spec.options)
    elif spec.kind in ("sql", "web"):
        # Đã qua cổng consent (người dùng đồng ý tường minh) — nhưng
        # prototype này CHƯA nối client HTTP/SQL thật phía sau cổng. Thà báo
        # rõ "chưa làm" còn hơn giả vờ đọc được dữ liệu không tồn tại.
        raise NotImplementedError(
            f"Nguồn '{spec.kind}' đã qua cổng đồng ý, nhưng NaMi Data Pipeline "
            "prototype CHƯA có client mạng/SQL thật nối sau cổng này. "
            "Xem docs/office/NAMI-DATA-PIPELINE.md mục 'KHÔNG phải'."
        )
    else:
        raise ValueError(f"source kind không hỗ trợ: {spec.kind!r}")

    dtypes = infer_dtypes(raw_rows, columns, overrides=spec.type_overrides)
    typed_rows = cast_rows(raw_rows, columns, dtypes)
    return Table(columns=columns, dtypes=dtypes, rows=tuple(typed_rows))


__all__ = ["SourceSpec", "read_source", "ConsentRequiredError"]
