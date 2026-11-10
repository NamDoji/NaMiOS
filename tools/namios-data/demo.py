#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMi Data Pipeline — demo end-to-end (chạy tay, không phải test).

Sinh 3 nguồn cục bộ mẫu (2 CSV đơn hàng theo tháng + 1 JSON tra cứu ngành
hàng), dựng MỘT pipeline: filter -> append (gộp 2 tháng) -> merge (ghép
ngành hàng) -> group_by (tổng theo ngành hàng), chạy, in kết quả, ghi .xlsx,
rồi serialize pipeline ra JSON -> nạp lại -> chạy lại -> so hash để tự chứng
minh "replay cho ra đúng kết quả cũ" ngay trên dữ liệu thật (không chỉ trong
pytest).

Chạy: `python3 tools/namios-data/demo.py` (từ repo root hoặc bất kỳ đâu).
"""
from __future__ import annotations

import csv
import json
import os

from pipeline import Pipeline
from sources import SourceSpec
from steps import AppendStep, FilterStep, GroupByStep, MergeStep, UnpivotStep
from table import tables_equal
from xlsx_writer import write_table_xlsx

_HERE = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_DIR = os.path.join(_HERE, "sample_data")
_OUT_DIR = os.path.join(_HERE, "out")


def _write_sample_sources() -> None:
    os.makedirs(_SAMPLE_DIR, exist_ok=True)

    orders_jan = os.path.join(_SAMPLE_DIR, "orders_jan.csv")
    with open(orders_jan, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["OrderId", "ProductCode", "Qty", "Amount"])
        w.writerows(
            [
                ["J001", "SP01", "3", "900000"],
                ["J002", "SP02", "1", "450000"],
                ["J003", "SP01", "0", "0"],  # Qty=0 -> bị filter loại
                ["J004", "SP03", "2", "260000"],
            ]
        )

    orders_feb = os.path.join(_SAMPLE_DIR, "orders_feb.csv")
    with open(orders_feb, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["OrderId", "ProductCode", "Qty", "Amount"])
        w.writerows(
            [
                ["F001", "SP02", "2", "900000"],
                ["F002", "SP03", "1", "130000"],
            ]
        )

    products = os.path.join(_SAMPLE_DIR, "products.json")
    with open(products, "w", encoding="utf-8") as fh:
        json.dump(
            [
                {"ProductCode": "SP01", "Category": "Văn phòng"},
                {"ProductCode": "SP02", "Category": "Điện tử"},
                {"ProductCode": "SP03", "Category": "Văn phòng"},
            ],
            fh,
            ensure_ascii=False,
        )

    quarterly = os.path.join(_SAMPLE_DIR, "sales_wide.csv")
    with open(quarterly, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Region", "Q1", "Q2", "Q3", "Q4"])
        w.writerows(
            [
                ["Bắc", "100", "120", "90", "140"],
                ["Nam", "80", "95", "100", "110"],
            ]
        )


def build_sales_by_category_pipeline() -> Pipeline:
    p = Pipeline(
        name="sales_by_category",
        source=SourceSpec(kind="csv", uri=os.path.join(_SAMPLE_DIR, "orders_jan.csv")),
    )
    p.add_aux_source(
        "orders_feb", SourceSpec(kind="csv", uri=os.path.join(_SAMPLE_DIR, "orders_feb.csv"))
    )
    p.add_aux_source(
        "products", SourceSpec(kind="json", uri=os.path.join(_SAMPLE_DIR, "products.json"))
    )
    p.add_step(FilterStep(column="Qty", op="gt", value=0))
    p.add_step(AppendStep(other_table="orders_feb"))
    p.add_step(MergeStep(right_table="products", left_on="ProductCode", right_on="ProductCode", how="inner"))
    p.add_step(
        GroupByStep(
            by=("Category",),
            aggregations={"TotalAmount": ("sum", "Amount"), "OrderCount": ("count", "OrderId")},
        )
    )
    return p


def build_unpivot_pipeline() -> Pipeline:
    p = Pipeline(
        name="sales_unpivoted",
        source=SourceSpec(kind="csv", uri=os.path.join(_SAMPLE_DIR, "sales_wide.csv")),
    )
    p.add_step(
        UnpivotStep(
            id_columns=("Region",),
            value_columns=("Q1", "Q2", "Q3", "Q4"),
            name_col="Quarter",
            value_col="Sales",
        )
    )
    return p


def main() -> None:
    _write_sample_sources()
    os.makedirs(_OUT_DIR, exist_ok=True)

    p1 = build_sales_by_category_pipeline()
    result1 = p1.run()
    print("=== sales_by_category ===")
    print(result1.to_preview())
    out1 = write_table_xlsx(result1, os.path.join(_OUT_DIR, "sales_by_category.xlsx"))
    print(f"-> wrote {out1}")

    # Chứng minh replay: serialize -> JSON -> nạp lại thành Pipeline MỚI -> chạy lại.
    json_str = p1.to_json()
    p1_reloaded = Pipeline.from_json(json_str)
    result1_replay = p1_reloaded.run()
    assert tables_equal(result1, result1_replay), "REPLAY KHÔNG KHỚP — lỗi nghiêm trọng"
    print(f"replay hash khớp: {result1.content_hash()[:16]}...")

    p2 = build_unpivot_pipeline()
    result2 = p2.run()
    print("\n=== sales_unpivoted ===")
    print(result2.to_preview())
    out2 = write_table_xlsx(result2, os.path.join(_OUT_DIR, "sales_unpivoted.xlsx"))
    print(f"-> wrote {out2}")

    print("\nhistory (sales_by_category):", p1.history)


if __name__ == "__main__":
    main()
