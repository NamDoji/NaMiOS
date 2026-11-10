#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — ghi kết quả Table ra .xlsx (openpyxl).

Đây CHỈ là bước xuất kết quả cuối (một bảng tĩnh — giá trị, không phải công
thức) ra một sheet .xlsx, để người dùng xem bằng NaMiSheet/Excel. KHÔNG tạo
Table object Excel có "Refresh" trong UI — refresh thật phải chạy lại
`pipeline.Pipeline.run()` bên Python (xem docs/office/NAMI-DATA-PIPELINE.md
mục "KHÔNG phải": chưa nối vào NaMiSheet/Calc UI).
"""
from __future__ import annotations

import datetime
import os

from openpyxl import Workbook

from table import Table


def write_table_xlsx(table: Table, path: str, *, sheet_name: str = "Data") -> str:
    """Ghi `table` ra MỘT sheet của file `path` (tạo thư mục cha nếu thiếu).
    Giữ nguyên kiểu Python thật cho ô (int/float/bool/`datetime.date`/str) —
    openpyxl tự áp number_format hợp lý cho ngày; không ép mọi thứ về chuỗi.
    Trả về `path` đã ghi."""
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]  # giới hạn tên sheet của Excel

    ws.append(list(table.columns))
    for row in table.rows:
        ws.append([_cell_value(row[c]) for c in table.columns])

    for col_idx, col_name in enumerate(table.columns, start=1):
        if table.dtypes.get(col_name) == "date":
            for r in range(2, len(table.rows) + 2):
                cell = ws.cell(row=r, column=col_idx)
                if isinstance(cell.value, datetime.date):
                    cell.number_format = "yyyy-mm-dd"

    wb.save(path)
    return path


def _cell_value(v):
    # openpyxl không nhận None trực tiếp làm vấn đề (ghi ô trống) — giữ
    # nguyên; mọi kiểu khác (int/float/bool/str/date) openpyxl tự xử lý.
    return v


__all__ = ["write_table_xlsx"]
