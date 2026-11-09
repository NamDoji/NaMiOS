#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bộ so sánh (comparator) cho vertical-slice NaMiOffice v2.

Hai chế độ:

  1. `selfcheck` (CHẠY ĐƯỢC ở máy này, không cần soffice): mở lại từng
     fixture bằng python-docx/openpyxl/python-pptx, đếm đối tượng (bảng,
     ảnh, chart, comment, named range, formula...), và — quan trọng nhất —
     TÍNH LẠI một lần nữa bằng Python, độc lập với lúc sinh file, các giá
     trị SUMIFS/COUNTIFS/AVERAGEIFS/IF/IFERROR/INDEX-MATCH/XLOOKUP/SUM từ
     DỮ LIỆU THÔ đọc trực tiếp trong WorkBook.xlsx, rồi so với sheet
     "KỳVọng" đã lưu trong file. Hai lần tính độc lập (lúc sinh file và lúc
     so sánh) phải khớp — đây KHÔNG phải so sánh "file tự khớp với chính nó"
     vì phép tính ở compare.py không import từ make_sheet.py, nó đọc lại
     dữ liệu thô từ file .xlsx đã lưu trên đĩa.

  2. `roundtrip` (CHẠY TRONG CI/QEMU, nơi có soffice): so sánh một fixture
     GỐC với một bản đã được LibreOffice/Microsoft Office mở-lưu lại — diff
     số đối tượng, công thức, giá trị cache. compare.py KHÔNG tự gọi
     soffice; việc convert là trách nhiệm của run_roundtrip.sh.

TRUNG THỰC: ở máy build hiện tại KHÔNG có soffice/LibreOffice/Microsoft
Office, nên compare.py không thể tự xác nhận dynamic-array có SPILL đúng
hay track-changes có round-trip đúng hay không — những phần đó chỉ có thể
đo khi `roundtrip` chạy trong CI/QEMU với soffice/Office thật. Script này
NÊU RÕ "SKIP (cần CI)" ở mọi mục chưa đo được, không tự nhận đạt.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FIXTURES_DIR = os.path.normpath(os.path.join(HERE, "..", "fixtures"))


# ---------------------------------------------------------------------------
@dataclass
class Report:
    ok: bool = True
    sections: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def section(self, name: str, data: dict) -> None:
        self.sections.append({"name": name, "data": data})

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_json(self) -> str:
        return json.dumps(
            {"ok": self.ok, "sections": self.sections, "errors": self.errors},
            ensure_ascii=False, indent=2,
        )

    def print_human(self) -> None:
        for sec in self.sections:
            print(f"\n== {sec['name']} ==")
            for k, v in sec["data"].items():
                print(f"  {k}: {v}")
        if self.errors:
            print("\n!! LỖI !!")
            for e in self.errors:
                print(f"  - {e}")
        print(f"\nKẾT QUẢ: {'PASS' if self.ok else 'FAIL'}")


# ---------------------------------------------------------------------------
# ---- selfcheck: LongDoc.docx ----
def check_docx(report: Report, path: str) -> None:
    if not os.path.exists(path):
        report.fail(f"docx: không thấy file {path}")
        return
    doc = Document(path)
    n_tables = len(doc.tables)
    n_images = len(doc.inline_shapes)
    n_comments = len(doc.comments) if hasattr(doc, "comments") else 0
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    n_hyperlinks = len(doc.part._element.xpath("//w:hyperlink"))
    footer_xml_has_page_field = False
    for section in doc.sections:
        footer = section.footer
        xml = footer._element.xml if footer._element is not None else ""
        if "PAGE" in xml:
            footer_xml_has_page_field = True
    n_paragraphs = len(doc.paragraphs)

    data = {
        "file": os.path.basename(path),
        "size_kb": os.path.getsize(path) // 1024,
        "paragraphs": n_paragraphs,
        "tables": n_tables,
        "inline_images": n_images,
        "comments": n_comments,
        "headings(TOC-able)": len(headings),
        "hyperlinks": n_hyperlinks,
        "footer_has_PAGE_field": footer_xml_has_page_field,
        "track_changes_authored": "KHÔNG (python-docx không có API ghi w:ins/w:del — xem README)",
    }
    report.section("LongDoc.docx — selfcheck", data)

    if n_tables < 1:
        report.fail("docx: thiếu bảng")
    if n_images < 1:
        report.fail("docx: thiếu ảnh inline")
    if n_comments < 1:
        report.fail("docx: thiếu comment")
    if len(headings) < 5:
        report.fail("docx: thiếu heading để TOC")
    if n_hyperlinks < 1:
        report.fail("docx: thiếu hyperlink")
    if not footer_xml_has_page_field:
        report.fail("docx: thiếu field số trang ở footer")

    # Kiểm tra merge cell trong bảng (ô gộp phải trỏ cùng <w:tc> cho nhiều cột).
    if n_tables >= 1:
        tbl = doc.tables[0]
        last_row_cells = tbl.rows[-1].cells
        merged = len({id(c._tc) for c in last_row_cells}) < len(last_row_cells)
        data["last_row_has_merged_cell"] = merged
        if not merged:
            report.fail("docx: dòng cuối bảng không có ô gộp như kỳ vọng")


# ---------------------------------------------------------------------------
# ---- selfcheck: WorkBook.xlsx ----
def _read_duLieu_raw(ws) -> list[tuple]:
    """Đọc dữ liệu thô từ sheet DuLieu — KHÔNG đụng tới cột ThànhTiền (vì đó
    là công thức, không có giá trị cache do openpyxl không tính công thức).
    Trả về list (stt, ngay, khuvuc, khachhang, sanpham, soluong, dongia)."""
    rows = []
    r = 2
    while True:
        stt = ws.cell(row=r, column=1).value
        if stt is None:
            break
        khuvuc = ws.cell(row=r, column=3).value
        khachhang = ws.cell(row=r, column=4).value
        sanpham = ws.cell(row=r, column=5).value
        soluong = ws.cell(row=r, column=6).value
        dongia = ws.cell(row=r, column=7).value
        rows.append((stt, khuvuc, khachhang, sanpham, soluong, dongia))
        r += 1
    return rows


def _read_bangGia_raw(ws) -> list[tuple]:
    rows = []
    r = 2
    while True:
        code = ws.cell(row=r, column=1).value
        if code is None:
            break
        name = ws.cell(row=r, column=2).value
        price = ws.cell(row=r, column=3).value
        cat = ws.cell(row=r, column=4).value
        rows.append((code, name, price, cat))
        r += 1
    return rows


def _recompute_expected(dl_rows, bg_rows) -> dict:
    """TÍNH LẠI độc lập từ dữ liệu thô đọc trực tiếp từ file .xlsx đã lưu —
    không import hằng số từ make_sheet.py."""
    thanhtien = [sl * dg for (_stt, _kv, _kh, _sp, sl, dg) in dl_rows]

    sumifs = sum(
        tt for (_stt, kv, _kh, _sp, sl, _dg), tt in zip(dl_rows, thanhtien)
        if kv == "Bắc" and sl >= 5
    )
    countifs = sum(1 for (_stt, kv, _kh, sp, _sl, _dg) in dl_rows if kv == "Nam" and sp == "Ghế")
    trung_vals = [tt for (_stt, kv, _kh, _sp, _sl, _dg), tt in zip(dl_rows, thanhtien) if kv == "Trung"]
    averageifs = sum(trung_vals) / len(trung_vals) if trung_vals else None
    if_label = None
    if averageifs is not None:
        if_label = "Cao" if averageifs > 1_000_000 else "Thấp"
    sum_table = sum(thanhtien)

    bg_by_code = {code: price for (code, _name, price, _cat) in bg_rows}
    index_match_sp03 = bg_by_code.get("SP03")
    xlookup_sp05 = bg_by_code.get("SP05")

    return {
        "SUMIFS": sumifs,
        "COUNTIFS": countifs,
        "AVERAGEIFS": averageifs,
        "IF": if_label,
        "IFERROR": "Lỗi chia 0",  # 1/0 luôn lỗi — hằng số, không phụ thuộc dữ liệu
        "INDEX/MATCH": index_match_sp03,
        "XLOOKUP": xlookup_sp05,
        "SUM_TABLE": sum_table,
    }


# Thứ tự PHẢI đi từ cụ thể → chung (ví dụ "IFERROR"/"SUMIFS" chứa substring
# "IF", nên khớp generic "IF" phải xét SAU CÙNG). Dùng được cho CẢ nhãn ở
# sheet "KỳVọng" (vd "AVERAGEIFS — trung bình...") LẪN nhãn ở sheet
# "CongThuc" (vd "AVERAGEIFS (Trung)") vì cùng chứa từ khoá tên hàm.
_LABEL_TO_KEY = [
    ("IFERROR", "IFERROR"),
    ("AVERAGEIFS", "AVERAGEIFS"),
    ("SUMIFS", "SUMIFS"),
    ("COUNTIFS", "COUNTIFS"),
    ("XLOOKUP", "XLOOKUP"),
    ("INDEX/MATCH", "INDEX/MATCH"),
    ("SUM structured", "SUM_TABLE"),
    ("IF", "IF"),
]


def _match_label_to_key(label: str) -> str | None:
    for substr, key in _LABEL_TO_KEY:
        if substr in label:
            return key
    return None


def _read_kyvong_expected(wb) -> dict[str, Any]:
    kv = wb["KỳVọng"]
    out: dict[str, Any] = {}
    r = 2
    while True:
        label = kv.cell(row=r, column=2).value
        if label is None:
            break
        key = _match_label_to_key(label)
        if key is not None:
            out[key] = kv.cell(row=r, column=4).value
        r += 1
    return out


def check_xlsx(report: Report, path: str) -> None:
    if not os.path.exists(path):
        report.fail(f"xlsx: không thấy file {path}")
        return
    wb = load_workbook(path)

    n_sheets = len(wb.sheetnames)
    dl = wb["DuLieu"]
    n_tables = len(dl.tables)
    n_named_ranges = len(wb.defined_names)
    th = wb["TongHop"]
    n_charts = len(th._charts)

    n_formula_cells = 0
    n_dynamic_array_formulas = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.data_type == "f" and isinstance(cell.value, str):
                    n_formula_cells += 1
                    if "_xlfn" in cell.value:
                        n_dynamic_array_formulas += 1

    has_real_pivot = bool(getattr(wb, "_pivots", None)) or any(
        "pivotTable" in name for name in getattr(wb, "sheetnames", [])
    )

    data = {
        "file": os.path.basename(path),
        "size_kb": os.path.getsize(path) // 1024,
        "sheets": n_sheets,
        "table_objects": n_tables,
        "named_ranges": n_named_ranges,
        "charts(TongHop)": n_charts,
        "formula_cells_total": n_formula_cells,
        "future_function_formulas(_xlfn)": n_dynamic_array_formulas,
        "real_pivot_table_object": f"{has_real_pivot} (kỳ vọng False — xem PivotTable_GhiChu + README)",
        "fullCalcOnLoad": bool(wb.calculation.fullCalcOnLoad) if wb.calculation else None,
    }
    report.section("WorkBook.xlsx — selfcheck (cấu trúc)", data)

    if n_tables < 1:
        report.fail("xlsx: thiếu Table object")
    if n_named_ranges < 1:
        report.fail("xlsx: thiếu named range")
    if n_charts < 1:
        report.fail("xlsx: thiếu chart")
    if n_dynamic_array_formulas < 1:
        report.fail("xlsx: thiếu công thức mảng động (_xlfn)")

    # ---- Đối chiếu KỳVọng: TÍNH LẠI độc lập từ dữ liệu thô trong file ----
    dl_rows = _read_duLieu_raw(dl)
    bg_rows = _read_bangGia_raw(wb["BangGia"])
    recomputed = _recompute_expected(dl_rows, bg_rows)

    kv = wb["KỳVọng"]
    kv_check = {}
    mismatches = []
    r = 2
    while True:
        label = kv.cell(row=r, column=2).value
        if label is None:
            break
        stored = kv.cell(row=r, column=4).value
        key = _match_label_to_key(label)
        if key is None:
            kv_check[label] = "KHÔNG NHẬN DIỆN ĐƯỢC NHÃN (bỏ qua)"
        else:
            recomputed_val = recomputed.get(key)
            match = (
                recomputed_val == stored
                if not isinstance(stored, float)
                else abs((recomputed_val or 0) - stored) < 1e-6
            )
            kv_check[label] = f"lưu={stored!r} tính_lại={recomputed_val!r} khớp={match}"
            if not match:
                mismatches.append(label)
        r += 1
    report.section("WorkBook.xlsx — đối chiếu KỳVọng (tính lại độc lập)", kv_check)
    if mismatches:
        report.fail(f"xlsx: KỳVọng lệch so với tính lại độc lập: {mismatches}")

    report.section(
        "WorkBook.xlsx — chưa đo được ở local (cần CI/QEMU có soffice)",
        {
            "dynamic_array_spill(FILTER/SORT/UNIQUE)": "SKIP — cần LibreOffice Calc/Excel tính thật",
            "pivot_equivalent_sumifs_block": "đã ghi trong PivotTable_GhiChu, chưa kiểm chứng render",
        },
    )


# ---------------------------------------------------------------------------
# ---- selfcheck: Deck.pptx ----
def check_pptx(report: Report, path: str) -> None:
    if not os.path.exists(path):
        report.fail(f"pptx: không thấy file {path}")
        return
    prs = Presentation(path)
    slides = list(prs.slides)
    n_slides = len(slides)
    layouts_used = sorted({s.slide_layout.name for s in slides})
    n_charts = sum(1 for s in slides for shp in s.shapes if shp.has_chart)
    n_tables = sum(1 for s in slides for shp in s.shapes if shp.has_table)
    n_notes = sum(
        1 for s in slides if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip()
    )

    def _is_picture(shp) -> bool:
        if "PICTURE" in str(shp.shape_type):
            return True
        if getattr(shp, "is_placeholder", False):
            pf = shp.placeholder_format
            return pf.type is not None and "PICTURE" in str(pf.type)
        return False

    n_pics = sum(1 for s in slides for shp in s.shapes if _is_picture(shp))

    data = {
        "file": os.path.basename(path),
        "size_kb": os.path.getsize(path) // 1024,
        "slides": n_slides,
        "layouts_used": layouts_used,
        "non_default_layout_used": any(l not in ("Title Slide", "Title and Content") for l in layouts_used),
        "native_charts": n_charts,
        "tables": n_tables,
        "slides_with_notes": n_notes,
        "images": n_pics,
    }
    report.section("Deck.pptx — selfcheck", data)

    if n_slides < 3:
        report.fail("pptx: quá ít slide")
    if n_charts < 1:
        report.fail("pptx: thiếu chart gốc (native)")
    if n_tables < 1:
        report.fail("pptx: thiếu bảng")
    if n_notes != n_slides:
        report.fail(f"pptx: không phải mọi slide đều có speaker notes ({n_notes}/{n_slides})")
    if n_pics < 1:
        report.fail("pptx: thiếu ảnh")
    if not data["non_default_layout_used"]:
        report.fail("pptx: chưa dùng layout không mặc định")


# ---------------------------------------------------------------------------
# ---- roundtrip mode: diff trước/sau khi soffice mở-lưu lại ----
def diff_docx(report: Report, orig: str, new: str) -> None:
    d0, d1 = Document(orig), Document(new)
    before = {
        "paragraphs": len(d0.paragraphs),
        "tables": len(d0.tables),
        "inline_images": len(d0.inline_shapes),
        "comments": len(d0.comments) if hasattr(d0, "comments") else 0,
        "hyperlinks": len(d0.part._element.xpath("//w:hyperlink")),
    }
    after = {
        "paragraphs": len(d1.paragraphs),
        "tables": len(d1.tables),
        "inline_images": len(d1.inline_shapes),
        "comments": len(d1.comments) if hasattr(d1, "comments") else 0,
        "hyperlinks": len(d1.part._element.xpath("//w:hyperlink")),
    }
    report.section("docx round-trip diff", {"before": before, "after": after})
    for k in before:
        if before[k] != after[k]:
            report.fail(f"docx round-trip: '{k}' đổi từ {before[k]} sang {after[k]}")


def diff_xlsx(report: Report, orig: str, new: str) -> None:
    w0, w1 = load_workbook(orig), load_workbook(new)
    common_sheets = [s for s in w0.sheetnames if s in w1.sheetnames]
    formula_diffs = []
    for sheet in common_sheets:
        s0, s1 = w0[sheet], w1[sheet]
        max_row = max(s0.max_row, s1.max_row)
        max_col = max(s0.max_column, s1.max_column)
        for r in range(1, max_row + 1):
            for c in range(1, max_col + 1):
                v0 = s0.cell(row=r, column=c).value
                v1 = s1.cell(row=r, column=c).value
                if v0 != v1 and (isinstance(v0, str) and v0.startswith("=") or
                                  isinstance(v1, str) and v1.startswith("=")):
                    formula_diffs.append((sheet, r, c, v0, v1))
    before = {
        "sheets": len(w0.sheetnames),
        "tables(DuLieu)": len(w0["DuLieu"].tables) if "DuLieu" in w0.sheetnames else None,
        "named_ranges": len(w0.defined_names),
    }
    after = {
        "sheets": len(w1.sheetnames),
        "tables(DuLieu)": len(w1["DuLieu"].tables) if "DuLieu" in w1.sheetnames else None,
        "named_ranges": len(w1.defined_names),
    }
    report.section("xlsx round-trip diff", {
        "before": before, "after": after,
        "formula_text_diffs": len(formula_diffs),
        "sample_formula_diffs": formula_diffs[:10],
    })
    if before["tables(DuLieu)"] != after["tables(DuLieu)"]:
        report.fail("xlsx round-trip: mất Table object")
    if before["named_ranges"] != after["named_ranges"]:
        report.fail("xlsx round-trip: mất named range")

    # Sau khi soffice/Excel mở-lưu bản "new", sheet CongThuc có CACHED VALUE
    # thật do engine tính (openpyxl không tính được điều này). Lấy cached
    # value đó và so với cột "Giá trị kỳ vọng" ở KỳVọng — đây là cách duy
    # nhất để biết LibreOffice/Excel tính formula ĐÚNG hay SAI so với Python.
    if "CongThuc" in w1.sheetnames and "KỳVọng" in w1.sheetnames:
        expected_by_key = _read_kyvong_expected(w1)
        w1_data = load_workbook(new, data_only=True)
        ct_text, ct_data = w1["CongThuc"], w1_data["CongThuc"]
        engine_vs_expected = {}
        mismatches = []
        r = 3
        while True:
            label = ct_text.cell(row=r, column=1).value
            if label is None:
                break
            formula = ct_text.cell(row=r, column=2).value
            cached = ct_data.cell(row=r, column=2).value
            key = _match_label_to_key(label) if isinstance(label, str) else None
            is_dynamic_array = isinstance(formula, str) and "_xlfn" in formula
            if key is not None and key in expected_by_key:
                expected = expected_by_key[key]
                ok = (cached == expected if not isinstance(expected, float)
                      else cached is not None and abs(cached - expected) < 1e-6)
                engine_vs_expected[label] = f"cached={cached!r} kỳ_vọng={expected!r} khớp={ok}"
                if not ok:
                    mismatches.append(label)
            elif is_dynamic_array:
                engine_vs_expected[label] = (
                    f"cached={cached!r} — mảng động, KHÔNG có giá trị Python đối chiếu "
                    "(chỉ kiểm định tính: có spill/tính ra gì đó hay không)"
                )
            r += 1
        report.section(
            "xlsx round-trip — CÔNG THỨC do engine (LibreOffice/Excel) tính vs KỳVọng (Python)",
            engine_vs_expected,
        )
        if mismatches:
            report.fail(f"xlsx round-trip: engine tính SAI so với Python cho: {mismatches}")


def diff_pptx(report: Report, orig: str, new: str) -> None:
    p0, p1 = Presentation(orig), Presentation(new)
    s0, s1 = list(p0.slides), list(p1.slides)
    before = {
        "slides": len(s0),
        "charts": sum(1 for s in s0 for shp in s.shapes if shp.has_chart),
        "tables": sum(1 for s in s0 for shp in s.shapes if shp.has_table),
        "notes": sum(1 for s in s0 if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip()),
    }
    after = {
        "slides": len(s1),
        "charts": sum(1 for s in s1 for shp in s.shapes if shp.has_chart),
        "tables": sum(1 for s in s1 for shp in s.shapes if shp.has_table),
        "notes": sum(1 for s in s1 if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip()),
    }
    report.section("pptx round-trip diff", {"before": before, "after": after})
    for k in before:
        if before[k] != after[k]:
            report.fail(f"pptx round-trip: '{k}' đổi từ {before[k]} sang {after[k]}")


DIFF_FN = {"docx": diff_docx, "xlsx": diff_xlsx, "pptx": diff_pptx}


# ---------------------------------------------------------------------------
def run_selfcheck(fixtures_dir: str) -> Report:
    report = Report()
    check_docx(report, os.path.join(fixtures_dir, "LongDoc.docx"))
    check_xlsx(report, os.path.join(fixtures_dir, "WorkBook.xlsx"))
    check_pptx(report, os.path.join(fixtures_dir, "Deck.pptx"))
    return report


def run_roundtrip(kind: str, orig: str, new: str) -> Report:
    report = Report()
    fn = DIFF_FN.get(kind)
    if fn is None:
        report.fail(f"kind không hợp lệ: {kind}")
        return report
    fn(report, orig, new)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Comparator cho vertical-slice NaMiOffice v2")
    sub = ap.add_subparsers(dest="mode", required=False)

    sc = sub.add_parser("selfcheck", help="kiểm tra tự thân, không cần soffice")
    sc.add_argument("--fixtures-dir", default=DEFAULT_FIXTURES_DIR)
    sc.add_argument("--report", default=None, help="đường dẫn ghi báo cáo JSON (tuỳ chọn)")

    rt = sub.add_parser("roundtrip", help="diff trước/sau round-trip (cần file đã convert ở CI)")
    rt.add_argument("--kind", required=True, choices=["docx", "xlsx", "pptx"])
    rt.add_argument("--orig", required=True)
    rt.add_argument("--new", required=True)
    rt.add_argument("--report", default=None)

    args = ap.parse_args()
    mode = args.mode or "selfcheck"

    if mode == "selfcheck":
        fixtures_dir = getattr(args, "fixtures_dir", DEFAULT_FIXTURES_DIR)
        report = run_selfcheck(fixtures_dir)
    else:
        report = run_roundtrip(args.kind, args.orig, args.new)

    report.print_human()
    report_path = getattr(args, "report", None)
    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report.to_json())
        print(f"\n(JSON report: {report_path})")

    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
