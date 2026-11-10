# -*- coding: utf-8 -*-
"""serialize steps -> reload -> replay -> identical output.

Đây là bullet "step history + re-run producing identical output" trong yêu
cầu task: một Pipeline với nhiều bước, serialize ra JSON, nạp lại thành một
Pipeline MỚI (object khác hẳn, không chia sẻ state Python nào), chạy lại, và
kết quả phải HOÀN TOÀN giống (so bằng content_hash, không phải identity)."""
import csv
import json

from pipeline import Pipeline
from sources import SourceSpec
from steps import FilterStep, GroupByStep, RenameStep, SelectStep
from table import tables_equal


def _write_sales_csv(path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Vung", "SanPham", "SoLuong", "DonGia"])
        w.writerows(
            [
                ["Bac", "Vo", "10", "50000"],
                ["Bac", "But", "20", "5000"],
                ["Nam", "Vo", "5", "50000"],
                ["Nam", "But", "0", "5000"],
            ]
        )


def _build_pipeline(csv_path: str) -> Pipeline:
    p = Pipeline(name="sales_demo", source=SourceSpec(kind="csv", uri=csv_path))
    p.add_step(FilterStep(column="SoLuong", op="gt", value=0))
    p.add_step(RenameStep(mapping={"Vung": "Region", "SanPham": "Product"}))
    p.add_step(SelectStep(columns=("Region", "Product", "SoLuong", "DonGia")))
    p.add_step(
        GroupByStep(
            by=("Region",),
            aggregations={"TotalQty": ("sum", "SoLuong"), "Items": ("count", "Product")},
        )
    )
    return p


def test_serialize_reload_replay_identical(tmp_path):
    csv_path = str(tmp_path / "sales.csv")
    _write_sales_csv(csv_path)

    original = _build_pipeline(csv_path)
    result_a = original.run()

    json_str = original.to_json()
    # Khẳng định JSON thật sự là dữ liệu thuần (round-trip qua json module),
    # không phải chỉ repr() — và chứa đủ 4 bước theo đúng thứ tự đã thêm.
    parsed = json.loads(json_str)
    assert [s["kind"] for s in parsed["steps"]] == ["filter", "rename", "select", "group_by"]

    reloaded = Pipeline.from_json(json_str)
    assert reloaded is not original  # object hoàn toàn mới
    assert reloaded.source.uri == original.source.uri

    result_b = reloaded.run()

    assert tables_equal(result_a, result_b)
    assert result_a.to_dict() == result_b.to_dict()  # so cả nội dung, không chỉ hash


def test_run_twice_same_pipeline_object_is_also_identical(tmp_path):
    """Gọi lại .run() nhiều lần trên CÙNG một Pipeline (không serialize) cũng
    phải cho ra cùng kết quả — 'refresh' đọc lại nguồn + replay bước, nguồn
    không đổi thì kết quả không đổi."""
    csv_path = str(tmp_path / "sales2.csv")
    _write_sales_csv(csv_path)
    p = _build_pipeline(csv_path)

    r1 = p.run()
    r2 = p.refresh()
    r3 = p.run()

    assert tables_equal(r1, r2)
    assert tables_equal(r2, r3)
    assert len(p.history) == 3


def test_refresh_picks_up_changed_source(tmp_path):
    """Khi nguồn trên đĩa THAY ĐỔI giữa hai lần chạy, refresh() phải đọc lại
    dữ liệu mới (không cache sai) — nhưng danh sách bước áp dụng vẫn như cũ,
    nên hai lần chạy ra hash KHÁC NHAU (đúng vì input khác), không phải lỗi."""
    csv_path = str(tmp_path / "sales3.csv")
    _write_sales_csv(csv_path)
    p = _build_pipeline(csv_path)
    r1 = p.run()

    # Thêm một dòng mới vào nguồn trên đĩa.
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Bac", "Vo", "100", "50000"])

    r2 = p.refresh()
    assert not tables_equal(r1, r2)
    bac_row = [row for row in r2.rows if row["Region"] == "Bac"][0]
    assert bac_row["TotalQty"] == 130  # 10 + 20 + 100
