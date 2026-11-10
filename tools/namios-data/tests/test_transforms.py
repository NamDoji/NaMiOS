# -*- coding: utf-8 -*-
"""unpivot + merge correctness (bullet riêng trong yêu cầu task), kèm thêm
append/group_by/select/rename/filter từng bước đơn lẻ để KHÔNG tuyên bố
"7 loại bước hoạt động" mà không có test cho từng loại."""
import csv
import json

from pipeline import Pipeline
from sources import SourceSpec
from steps import (
    AppendStep,
    FilterStep,
    GroupByStep,
    MergeStep,
    RenameStep,
    SelectStep,
    StepError,
    UnpivotStep,
)
from table import Table


def _wide_table() -> Table:
    return Table.from_rows(
        [
            {"Region": "Bac", "Q1": 100, "Q2": 120, "Q3": 90, "Q4": 140},
            {"Region": "Nam", "Q1": 80, "Q2": 95, "Q3": 100, "Q4": 110},
        ],
        dtypes={"Region": "str", "Q1": "int", "Q2": "int", "Q3": "int", "Q4": "int"},
    )


def test_unpivot_correctness():
    wide = _wide_table()
    step = UnpivotStep(id_columns=("Region",), value_columns=("Q1", "Q2", "Q3", "Q4"), name_col="Quarter", value_col="Sales")
    long = step.apply(wide, {})

    assert long.columns == ("Region", "Quarter", "Sales")
    assert len(long) == 8  # 2 vùng x 4 quý
    # Tổng Sales sau unpivot phải bằng tổng mọi giá trị Q1..Q4 ban đầu (bảo toàn dữ liệu).
    original_total = sum(wide.column("Q1")) + sum(wide.column("Q2")) + sum(wide.column("Q3")) + sum(wide.column("Q4"))
    assert sum(long.column("Sales")) == original_total == 835

    bac_rows = {row["Quarter"]: row["Sales"] for row in long.rows if row["Region"] == "Bac"}
    assert bac_rows == {"Q1": 100, "Q2": 120, "Q3": 90, "Q4": 140}


def test_unpivot_rejects_unknown_column():
    wide = _wide_table()
    step = UnpivotStep(id_columns=("Region",), value_columns=("Q1", "Q5"))
    try:
        step.apply(wide, {})
        assert False, "phải ném StepError vì Q5 không tồn tại"
    except StepError:
        pass


def test_merge_inner_correctness():
    orders = Table.from_rows(
        [
            {"OrderId": "O1", "ProductCode": "SP01", "Qty": 2},
            {"OrderId": "O2", "ProductCode": "SP02", "Qty": 1},
            {"OrderId": "O3", "ProductCode": "SP99", "Qty": 3},  # không có trong products
        ],
        dtypes={"OrderId": "str", "ProductCode": "str", "Qty": "int"},
    )
    products = Table.from_rows(
        [
            {"ProductCode": "SP01", "Category": "Văn phòng"},
            {"ProductCode": "SP02", "Category": "Điện tử"},
        ],
        dtypes={"ProductCode": "str", "Category": "str"},
    )

    inner = MergeStep(right_table="products", left_on="ProductCode", right_on="ProductCode", how="inner")
    result = inner.apply(orders, {"products": products})

    assert result.columns == ("OrderId", "ProductCode", "Qty", "Category")
    assert len(result) == 2  # SP99 bị loại (không khớp, inner join)
    cats = {row["OrderId"]: row["Category"] for row in result.rows}
    assert cats == {"O1": "Văn phòng", "O2": "Điện tử"}


def test_merge_left_keeps_unmatched_with_nulls():
    orders = Table.from_rows(
        [
            {"OrderId": "O1", "ProductCode": "SP01", "Qty": 2},
            {"OrderId": "O3", "ProductCode": "SP99", "Qty": 3},
        ],
        dtypes={"OrderId": "str", "ProductCode": "str", "Qty": "int"},
    )
    products = Table.from_rows(
        [{"ProductCode": "SP01", "Category": "Văn phòng"}],
        dtypes={"ProductCode": "str", "Category": "str"},
    )
    left = MergeStep(right_table="products", left_on="ProductCode", right_on="ProductCode", how="left")
    result = left.apply(orders, {"products": products})

    assert len(result) == 2  # left join giữ cả dòng không khớp
    by_id = {row["OrderId"]: row["Category"] for row in result.rows}
    assert by_id == {"O1": "Văn phòng", "O3": None}


def test_merge_rejects_unknown_aux_table():
    orders = Table.from_rows([{"A": 1}], dtypes={"A": "int"})
    step = MergeStep(right_table="ghost", left_on="A", right_on="A")
    try:
        step.apply(orders, {})
        assert False
    except StepError:
        pass


def test_merge_then_groupby_pipeline_end_to_end(tmp_path):
    """Kịch bản thực tế: đơn hàng (CSV) + ngành hàng (JSON, nguồn phụ) ->
    merge -> group_by theo ngành hàng. Khẳng định số tổng chính xác."""
    orders_csv = tmp_path / "orders.csv"
    with open(orders_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["OrderId", "ProductCode", "Amount"])
        w.writerows(
            [
                ["O1", "SP01", "900000"],
                ["O2", "SP02", "450000"],
                ["O3", "SP01", "260000"],
            ]
        )
    products_json = tmp_path / "products.json"
    with open(products_json, "w", encoding="utf-8") as fh:
        json.dump(
            [
                {"ProductCode": "SP01", "Category": "A"},
                {"ProductCode": "SP02", "Category": "B"},
            ],
            fh,
        )

    p = Pipeline(name="merge_groupby", source=SourceSpec(kind="csv", uri=str(orders_csv)))
    p.add_aux_source("products", SourceSpec(kind="json", uri=str(products_json)))
    p.add_step(MergeStep(right_table="products", left_on="ProductCode", right_on="ProductCode", how="inner"))
    p.add_step(GroupByStep(by=("Category",), aggregations={"Total": ("sum", "Amount")}))

    result = p.run()
    totals = {row["Category"]: row["Total"] for row in result.rows}
    assert totals == {"A": 1160000, "B": 450000}


def test_append_requires_matching_schema():
    left = Table.from_rows([{"A": 1, "B": "x"}], dtypes={"A": "int", "B": "str"})
    right_ok = Table.from_rows([{"A": 2, "B": "y"}], dtypes={"A": "int", "B": "str"})
    right_bad = Table.from_rows([{"A": 3, "C": "z"}], dtypes={"A": "int", "C": "str"})

    ok = AppendStep(other_table="r").apply(left, {"r": right_ok})
    assert len(ok) == 2
    assert ok.column("A") == [1, 2]

    try:
        AppendStep(other_table="r").apply(left, {"r": right_bad})
        assert False, "phải ném StepError vì schema không khớp"
    except StepError:
        pass


def test_filter_select_rename_pure_do_not_mutate_input():
    table = Table.from_rows(
        [{"X": 1, "Y": "a"}, {"X": 2, "Y": "b"}], dtypes={"X": "int", "Y": "str"}
    )
    before_rows = table.rows
    FilterStep(column="X", op="gt", value=1).apply(table, {})
    SelectStep(columns=("X",)).apply(table, {})
    RenameStep(mapping={"X": "Z"}).apply(table, {})
    # table gốc không bị đổi bởi bất kỳ bước nào ở trên (pure).
    assert table.rows == before_rows
    assert table.columns == ("X", "Y")
