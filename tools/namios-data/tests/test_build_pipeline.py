# -*- coding: utf-8 -*-
"""Dựng một pipeline trên một CSV mẫu (filter -> select -> rename), chạy, và
khẳng định kết quả — bullet đầu tiên trong yêu cầu task (M4)."""
import csv

from pipeline import Pipeline
from sources import SourceSpec
from steps import FilterStep, RenameStep, SelectStep


def _write_students_csv(path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["HoTen", "Lop", "Diem", "DaDuyet"])
        w.writerows(
            [
                ["Nguyen Van A", "6A1", "8.5", "true"],
                ["Tran Thi B", "6A1", "9.0", "true"],
                ["Le Van C", "6A2", "4.0", "false"],
                ["Pham Thi D", "6A2", "7.5", "true"],
            ]
        )


def test_build_pipeline_filter_select_rename(tmp_path):
    csv_path = tmp_path / "students.csv"
    _write_students_csv(str(csv_path))

    pipeline = Pipeline(name="hs_dat", source=SourceSpec(kind="csv", uri=str(csv_path)))
    pipeline.add_step(FilterStep(column="Diem", op="gte", value=7.0))
    pipeline.add_step(SelectStep(columns=("HoTen", "Lop", "Diem")))
    pipeline.add_step(RenameStep(mapping={"HoTen": "Họ tên", "Diem": "Điểm"}))

    result = pipeline.run()

    assert result.columns == ("Họ tên", "Lop", "Điểm")
    assert len(result) == 3  # Le Van C (4.0) bị loại
    names = [row["Họ tên"] for row in result.rows]
    assert names == ["Nguyen Van A", "Tran Thi B", "Pham Thi D"]
    # type inference: cột Diem phải được đoán là float (có giá trị thập phân)
    assert pipeline.source.kind == "csv"
    assert all(isinstance(row["Điểm"], float) for row in result.rows)
    assert result.column("Điểm") == [8.5, 9.0, 7.5]

    # run() ghi lại lịch sử chạy (ts + row_count + hash) — không rỗng sau khi chạy.
    assert len(pipeline.history) == 1
    assert pipeline.history[0]["row_count"] == 3


def test_type_inference_is_editable_via_override(tmp_path):
    """Cột "MaHS" trông như số ("001","002",...) nhưng người dùng muốn giữ
    là chuỗi (để không mất số 0 đứng đầu) — override phải thắng suy luận."""
    csv_path = tmp_path / "ma_hs.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["MaHS", "HoTen"])
        w.writerows([["001", "A"], ["002", "B"]])

    # Không override: suy luận ra int -> mất số 0 đứng đầu khi hiển thị lại.
    auto = Pipeline(name="auto", source=SourceSpec(kind="csv", uri=str(csv_path))).run()
    assert auto.dtypes["MaHS"] == "int"
    assert auto.column("MaHS") == [1, 2]

    # Có override: giữ "MaHS" là str -> giữ đúng "001"/"002".
    overridden = Pipeline(
        name="overridden",
        source=SourceSpec(kind="csv", uri=str(csv_path), type_overrides={"MaHS": "str"}),
    ).run()
    assert overridden.dtypes["MaHS"] == "str"
    assert overridden.column("MaHS") == ["001", "002"]
