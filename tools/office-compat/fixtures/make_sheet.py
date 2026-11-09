#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh fixture WorkBook.xlsx cho vertical-slice NaMiSheet (NaMiOffice v2).

Xem docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md mục B và
05_PROMPT_CLAUDE_CODE.md bước 3: một XLSX có SUMIFS/COUNTIFS/AVERAGEIFS,
IF/IFERROR, INDEX/MATCH, XLOOKUP, dynamic array (FILTER/SORT/UNIQUE),
Table object, chart, named range, Pivot (cố gắng), format tiền/ngày
kiểu vi-VN, và sheet "KỳVọng" chứa giá trị kỳ vọng TÍNH ĐỘC LẬP bằng Python
cho các công thức KHÔNG phải mảng động (SUMIFS/COUNTIFS/AVERAGEIFS/IF/
IFERROR/INDEX-MATCH/XLOOKUP/structured-reference).

TRUNG THỰC về giới hạn:
  - openpyxl GHI công thức dưới dạng CHUỖI, không tự tính (không có engine
    công thức). "fullCalcOnLoad=True" chỉ bắt LibreOffice/Excel tính lại khi
    MỞ file — ở máy này không có soffice nên các ô công thức sẽ hiện giá
    trị rỗng/0 cho tới khi mở trong LibreOffice Calc/Excel thật.
  - Dynamic array (FILTER/SORT/UNIQUE) ghi với tiền tố "_xlfn." / "_xlfn._xlws."
    theo quy ước lưu "future functions" của Microsoft (Phụ lục định dạng
    OOXML). Tiền tố đúng hay không CHỈ xác nhận được khi mở bằng LibreOffice
    Calc (đủ mới) hoặc Excel thật — máy này không có soffice nên KHÔNG xác
    nhận được việc render/spill ở bước này; việc đó thuộc CI/QEMU.
  - PivotTable: openpyxl có các class mức thấp để ĐỌC/giữ nguyên pivot đã
    tồn tại trong file nguồn (openpyxl.pivot.*), nhưng KHÔNG có API mức cao
    để TẠO MỚI một PivotTable kèm đủ pivotCacheDefinition + pivotCacheRecords
    + quan hệ phần (.rels) + Content_Types một cách an toàn. Tự ghép các
    phần XML đó bằng tay có rủi ro cao tạo ra file hỏng mà không có soffice
    ở đây để kiểm tra ngay. Theo đúng hướng dẫn của nhiệm vụ này, mục này
    được đánh dấu KHÔNG KHẢ THI ở local và thay bằng sheet "PivotTable_GhiChu"
    nêu rõ giới hạn + một bảng tổng hợp làm bằng SUMIFS (không phải Pivot
    object thật) để người dùng vẫn có số liệu tổng hợp tương đương.

Chạy:  python3 tools/office-compat/fixtures/make_sheet.py
Đầu ra: tools/office-compat/fixtures/WorkBook.xlsx
"""
from __future__ import annotations

import os
import random
import statistics
from datetime import date, timedelta

from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_XLSX = os.path.join(HERE, "WorkBook.xlsx")

SON = "C93643"
INK = "182E3B"
GOLD = "F2C66D"
IVORY = "F5F2EB"

random.seed(20261110)  # cố định để fixture tái lập được

REGIONS = ["Bắc", "Trung", "Nam"]
PRODUCTS = ["Bàn", "Ghế", "Tủ", "Đèn"]
CUSTOMERS = ["Công ty An Phát", "Cửa hàng Minh Tâm", "Xí nghiệp Hồng Hà",
             "Công ty Việt Á", "Cửa hàng Bình Minh", "Công ty Sao Mai"]

N_ROWS = 20
RAW_ROWS = []  # (stt, ngay, khuvuc, khachhang, sanpham, soluong, dongia)
start = date(2026, 1, 5)
for i in range(N_ROWS):
    ngay = start + timedelta(days=random.randint(0, 150))
    khuvuc = REGIONS[i % 3] if i % 7 != 0 else random.choice(REGIONS)
    khachhang = random.choice(CUSTOMERS)
    sanpham = PRODUCTS[i % 4]
    soluong = random.randint(1, 12)
    dongia = random.choice([350000, 520000, 980000, 1250000, 2100000, 780000])
    RAW_ROWS.append((i + 1, ngay, khuvuc, khachhang, sanpham, soluong, dongia))

# Đảm bảo luôn có ít nhất một dòng "Trung" để AVERAGEIFS không chia 0.
if not any(r[2] == "Trung" for r in RAW_ROWS):
    RAW_ROWS[0] = (RAW_ROWS[0][0], RAW_ROWS[0][1], "Trung", *RAW_ROWS[0][3:])

THANHTIEN = [r[5] * r[6] for r in RAW_ROWS]  # soluong * dongia, tính sẵn để so sánh

# Bảng giá tra cứu (cho INDEX/MATCH, XLOOKUP).
PRICE_CODES = ["SP01", "SP02", "SP03", "SP04", "SP05", "SP06"]
PRICE_NAMES = ["Bàn gỗ sồi", "Ghế xoay", "Tủ hồ sơ", "Đèn bàn LED", "Bàn họp", "Ghế giám đốc"]
PRICE_VALUES = [2850000, 650000, 3200000, 320000, 5400000, 1850000]
PRICE_CATS = ["Bàn", "Ghế", "Tủ", "Đèn", "Bàn", "Ghế"]


# ---------------------------------------------------------------------------
# Giá trị kỳ vọng TÍNH ĐỘC LẬP bằng Python (dùng ở generation-time; compare.py
# sẽ tính lại một lần nữa từ dữ liệu đã LƯU trong file để đối chiếu hai chiều).
def expected_sumifs_bac_soluong5():
    return sum(tt for (_, _, kv, _, _, sl, _), tt in zip(RAW_ROWS, THANHTIEN)
               if kv == "Bắc" and sl >= 5)


def expected_countifs_nam_ghe():
    return sum(1 for (_, _, kv, _, sp, _, _) in RAW_ROWS if kv == "Nam" and sp == "Ghế")


def expected_averageifs_trung():
    vals = [tt for (_, _, kv, _, _, _, _), tt in zip(RAW_ROWS, THANHTIEN) if kv == "Trung"]
    return statistics.mean(vals)


def expected_index_match(code: str) -> int:
    return PRICE_VALUES[PRICE_CODES.index(code)]


def expected_xlookup(code: str) -> int:
    return PRICE_VALUES[PRICE_CODES.index(code)]


def expected_sum_table() -> int:
    return sum(THANHTIEN)


EXP_SUMIFS = expected_sumifs_bac_soluong5()
EXP_COUNTIFS = expected_countifs_nam_ghe()
EXP_AVERAGEIFS = expected_averageifs_trung()
EXP_INDEXMATCH = expected_index_match("SP03")
EXP_XLOOKUP = expected_xlookup("SP05")
EXP_SUMTABLE = expected_sum_table()
EXP_IF_LABEL = "Cao" if EXP_AVERAGEIFS > 1_000_000 else "Thấp"
EXP_IFERROR_LABEL = "Lỗi chia 0"

KYVONG_ROWS = [
    # (hạng mục, công thức hiển thị, giá trị kỳ vọng, loại "num"/"text")
    ("SUMIFS — tổng Thành tiền khu vực Bắc, số lượng ≥5",
     '=SUMIFS(DuLieu!G2:G{n},DuLieu!C2:C{n},"Bắc",DuLieu!F2:F{n},">=5")',
     EXP_SUMIFS, "num"),
    ("COUNTIFS — số hoá đơn khu vực Nam, sản phẩm Ghế",
     '=COUNTIFS(DuLieu!C2:C{n},"Nam",DuLieu!E2:E{n},"Ghế")',
     EXP_COUNTIFS, "num"),
    ("AVERAGEIFS — trung bình Thành tiền khu vực Trung",
     '=AVERAGEIFS(DuLieu!G2:G{n},DuLieu!C2:C{n},"Trung")',
     EXP_AVERAGEIFS, "num"),
    ("IF — xếp loại trung bình khu vực Trung",
     '=IF(AVERAGEIFS(DuLieu!G2:G{n},DuLieu!C2:C{n},"Trung")>1000000,"Cao","Thấp")',
     EXP_IF_LABEL, "text"),
    ("IFERROR — bắt lỗi chia 0",
     '=IFERROR(1/0,"Lỗi chia 0")',
     EXP_IFERROR_LABEL, "text"),
    ("INDEX/MATCH — đơn giá mã SP03",
     '=INDEX(BangGia!C2:C7,MATCH("SP03",BangGia!A2:A7,0))',
     EXP_INDEXMATCH, "num"),
    ("XLOOKUP — đơn giá mã SP05",
     '=_xlfn.XLOOKUP("SP05",BangGia!A2:A7,BangGia!C2:C7)',
     EXP_XLOOKUP, "num"),
    ("SUM structured reference — tổng Table[ThànhTiền]",
     "=SUM(BangHoaDon[ThànhTiền])",
     EXP_SUMTABLE, "num"),
]


def build() -> dict:
    wb = Workbook()
    n_data = N_ROWS + 1  # dòng cuối (1-based, có header ở dòng 1)

    thin_hdr_font = Font(bold=True, color="FFFFFF")
    thin_hdr_fill = PatternFill("solid", fgColor=INK)

    # ---------------- Sheet DuLieu ----------------
    dl = wb.active
    dl.title = "DuLieu"
    headers = ["STT", "NgàyHĐ", "KhuVực", "KháchHàng", "SảnPhẩm", "SốLượng",
               "ThànhTiền"]
    # Cột ĐơnGiá chèn giữa SốLượng và ThànhTiền để ThànhTiền = SốLượng*ĐơnGiá
    headers = ["STT", "NgàyHĐ", "KhuVực", "KháchHàng", "SảnPhẩm", "SốLượng",
               "ĐơnGiá", "ThànhTiền"]
    for c, h in enumerate(headers, start=1):
        cell = dl.cell(row=1, column=c, value=h)
        cell.font = thin_hdr_font
        cell.fill = thin_hdr_fill
        cell.alignment = Alignment(horizontal="center")

    for i, (stt, ngay, khuvuc, khachhang, sanpham, soluong, dongia) in enumerate(RAW_ROWS):
        r = i + 2
        dl.cell(row=r, column=1, value=stt)
        dcell = dl.cell(row=r, column=2, value=ngay)
        dcell.number_format = "dd/mm/yyyy"  # định dạng ngày kiểu vi-VN
        dl.cell(row=r, column=3, value=khuvuc)
        dl.cell(row=r, column=4, value=khachhang)
        dl.cell(row=r, column=5, value=sanpham)
        dl.cell(row=r, column=6, value=soluong)
        gcell = dl.cell(row=r, column=7, value=dongia)
        gcell.number_format = '#,##0" ₫"'  # tiền VND kiểu vi-VN
        # ThànhTiền là công thức = SốLượng * ĐơnGiá (cột tính toán trong Table).
        tcell = dl.cell(row=r, column=8, value=f"=F{r}*G{r}")
        tcell.number_format = '#,##0" ₫"'

    for col, w in {"A": 6, "B": 12, "C": 10, "D": 22, "E": 10, "F": 10,
                   "G": 13, "H": 14}.items():
        dl.column_dimensions[col].width = w

    # Excel Table object trên vùng DuLieu (structured references).
    table_ref = f"A1:H{n_data}"
    excel_table = Table(displayName="BangHoaDon", ref=table_ref)
    excel_table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True, showColumnStripes=False,
    )
    dl.add_table(excel_table)

    # ---------------- Sheet BangGia (tra cứu) ----------------
    bg = wb.create_sheet("BangGia")
    bg_headers = ["MãSP", "TênSP", "ĐơnGiá", "DanhMục"]
    for c, h in enumerate(bg_headers, start=1):
        cell = bg.cell(row=1, column=c, value=h)
        cell.font = thin_hdr_font
        cell.fill = thin_hdr_fill
    for i, (code, name, price, cat) in enumerate(
        zip(PRICE_CODES, PRICE_NAMES, PRICE_VALUES, PRICE_CATS)
    ):
        r = i + 2
        bg.cell(row=r, column=1, value=code)
        bg.cell(row=r, column=2, value=name)
        pcell = bg.cell(row=r, column=3, value=price)
        pcell.number_format = '#,##0" ₫"'
        bg.cell(row=r, column=4, value=cat)
    for col, w in {"A": 8, "B": 20, "C": 13, "D": 10}.items():
        bg.column_dimensions[col].width = w

    # ---------------- Named ranges (tên vùng) ----------------
    wb.defined_names["ThanhTien_Rng"] = DefinedName(
        "ThanhTien_Rng", attr_text=f"DuLieu!$H$2:$H${n_data}"
    )
    wb.defined_names["KhuVuc_Rng"] = DefinedName(
        "KhuVuc_Rng", attr_text=f"DuLieu!$C$2:$C${n_data}"
    )
    wb.defined_names["SoLuong_Rng"] = DefinedName(
        "SoLuong_Rng", attr_text=f"DuLieu!$F$2:$F${n_data}"
    )
    wb.defined_names["BangGia_Rng"] = DefinedName(
        "BangGia_Rng", attr_text="BangGia!$A$2:$D$7"
    )

    # ---------------- Sheet TongHop (dữ liệu cho chart) ----------------
    th = wb.create_sheet("TongHop")
    th["A1"] = "KhuVực"
    th["B1"] = "TổngThànhTiền"
    for c in ("A1", "B1"):
        th[c].font = thin_hdr_font
        th[c].fill = thin_hdr_fill
    for i, region in enumerate(REGIONS):
        r = i + 2
        th.cell(row=r, column=1, value=region)
        # SUMIF dùng NAMED RANGE thay vì địa chỉ trực tiếp.
        th.cell(row=r, column=2,
                value=f'=SUMIF(KhuVuc_Rng,A{r},ThanhTien_Rng)')
        th.cell(row=r, column=2).number_format = '#,##0" ₫"'
    th.column_dimensions["A"].width = 12
    th.column_dimensions["B"].width = 16

    chart = BarChart()
    chart.type = "col"
    chart.title = "Tổng Thành tiền theo Khu vực"
    chart.y_axis.title = "Thành tiền (₫)"
    chart.x_axis.title = "Khu vực"
    data_ref = Reference(th, min_col=2, min_row=1, max_row=1 + len(REGIONS))
    cats_ref = Reference(th, min_col=1, min_row=2, max_row=1 + len(REGIONS))
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.width, chart.height = 14, 8
    th.add_chart(chart, "D2")

    # ---------------- Sheet CongThuc (công thức trình diễn) ----------------
    cf = wb.create_sheet("CongThuc")
    cf.sheet_view.showGridLines = False
    cf.merge_cells("A1:C1")
    cf["A1"] = "CÔNG THỨC TRÌNH DIỄN — WorkBook.xlsx (vertical slice NaMiSheet)"
    cf["A1"].font = Font(size=13, bold=True, color="FFFFFF")
    cf["A1"].fill = PatternFill("solid", fgColor=SON)
    cf["A1"].alignment = Alignment(horizontal="center", vertical="center")
    cf.row_dimensions[1].height = 26

    demo_rows = [
        ("SUMIFS (≥5, Bắc)", f'=SUMIFS(DuLieu!H2:H{n_data},DuLieu!C2:C{n_data},"Bắc",DuLieu!F2:F{n_data},">=5")'),
        ("COUNTIFS (Nam, Ghế)", f'=COUNTIFS(DuLieu!C2:C{n_data},"Nam",DuLieu!E2:E{n_data},"Ghế")'),
        ("AVERAGEIFS (Trung)", f'=AVERAGEIFS(DuLieu!H2:H{n_data},DuLieu!C2:C{n_data},"Trung")'),
        ("IF xếp loại", f'=IF(AVERAGEIFS(DuLieu!H2:H{n_data},DuLieu!C2:C{n_data},"Trung")>1000000,"Cao","Thấp")'),
        ("IFERROR", "=IFERROR(1/0,\"Lỗi chia 0\")"),
        ("INDEX/MATCH (SP03)", '=INDEX(BangGia!C2:C7,MATCH("SP03",BangGia!A2:A7,0))'),
        ("XLOOKUP (SP05)", '=_xlfn.XLOOKUP("SP05",BangGia!A2:A7,BangGia!C2:C7)'),
        ("SUM structured ref", "=SUM(BangHoaDon[ThànhTiền])"),
        ("UNIQUE khách hàng (dynamic array)", f"=_xlfn._xlws.UNIQUE(DuLieu!D2:D{n_data})"),
        ("SORT đơn giá giảm dần (dynamic array)", "=_xlfn._xlws.SORT(BangGia!C2:C7,1,-1)"),
        ("FILTER khu vực Bắc (dynamic array)",
         f'=_xlfn._xlws.FILTER(DuLieu!D2:H{n_data},DuLieu!C2:C{n_data}="Bắc")'),
    ]
    row = 3
    for label, formula in demo_rows:
        cf.cell(row=row, column=1, value=label).font = Font(bold=True, color=INK)
        fcell = cf.cell(row=row, column=2, value=formula)
        fcell.font = Font(name="Consolas", size=9)
        row += 1
    cf.column_dimensions["A"].width = 34
    cf.column_dimensions["B"].width = 70
    note = cf.cell(row=row + 1, column=1,
                    value=("Ghi chú: các công thức mảng động (UNIQUE/SORT/FILTER) chỉ "
                           "TÍNH và SPILL khi mở bằng LibreOffice Calc/Excel thật; "
                           "openpyxl chỉ ghi công thức dưới dạng chuỗi."))
    note.font = Font(size=9, italic=True, color="7A7366")
    cf.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=2)

    # ---------------- Sheet KỳVọng ----------------
    kv = wb.create_sheet("KỳVọng")
    kv.sheet_view.showGridLines = False
    kv_headers = ["#", "Hạng mục", "Công thức", "Giá trị kỳ vọng (Python)", "Loại"]
    for c, h in enumerate(kv_headers, start=1):
        cell = kv.cell(row=1, column=c, value=h)
        cell.font = thin_hdr_font
        cell.fill = thin_hdr_fill
    for i, (label, formula_tpl, expected, kind) in enumerate(KYVONG_ROWS):
        r = i + 2
        kv.cell(row=r, column=1, value=i + 1)
        kv.cell(row=r, column=2, value=label)
        f_cell = kv.cell(row=r, column=3, value=formula_tpl.format(n=n_data))
        f_cell.data_type = "s"  # lưu là CHỮ (literal), không phải công thức sống
        f_cell.font = Font(name="Consolas", size=9)
        e_cell = kv.cell(row=r, column=4, value=expected)
        if kind == "num" and isinstance(expected, float):
            e_cell.number_format = "#,##0.00"
        kv.cell(row=r, column=5, value=kind)
    kv.column_dimensions["A"].width = 4
    kv.column_dimensions["B"].width = 42
    kv.column_dimensions["C"].width = 60
    kv.column_dimensions["D"].width = 22
    kv.column_dimensions["E"].width = 8
    note_row = len(KYVONG_ROWS) + 3
    kv.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=5)
    kv.cell(row=note_row, column=1, value=(
        "Giá trị ở cột D được TÍNH ĐỘC LẬP bằng Python khi sinh file này. "
        "tools/office-compat/roundtrip/compare.py tính LẠI một lần nữa từ dữ liệu "
        "đã lưu trong sheet DuLieu/BangGia và so khớp với cột này — hai lần tính "
        "độc lập phải khớp thì mới coi là đúng; KHÔNG dùng giá trị cache của Calc/Excel."
    )).font = Font(size=9, italic=True, color="7A7366")
    kv.row_dimensions[note_row].height = 28

    # ---------------- PivotTable (không khả thi local) ----------------
    pv = wb.create_sheet("PivotTable_GhiChu")
    pv.sheet_view.showGridLines = False
    pv.merge_cells("A1:D1")
    pv["A1"] = "GHI CHÚ: PivotTable KHÔNG được tạo trong fixture này"
    pv["A1"].font = Font(size=12, bold=True, color="FFFFFF")
    pv["A1"].fill = PatternFill("solid", fgColor=SON)
    pv.merge_cells("A2:D5")
    pv["A2"] = (
        "openpyxl có class mức thấp để ĐỌC pivot đã có sẵn trong file nguồn "
        "(openpyxl.pivot.table/cache/record), nhưng KHÔNG có API mức cao để TẠO "
        "MỚI một PivotTable kèm đủ pivotCacheDefinition + pivotCacheRecords + "
        "quan hệ phần (.rels) + mục Content_Types một cách an toàn và có kiểm "
        "chứng. Ở máy này KHÔNG có soffice để xác nhận ngay một PivotTable viết "
        "tay bằng XML có mở được hay không, nên việc này được đánh dấu KHÔNG "
        "KHẢ THI ở bước local — xem README.md mục giới hạn."
    )
    pv["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    pv["A2"].font = Font(size=10, color=INK)
    pv.row_dimensions[2].height = 80

    pv["A7"] = "Bảng tổng hợp TƯƠNG ĐƯƠNG (SUMIFS thủ công — KHÔNG phải PivotTable object thật):"
    pv["A7"].font = Font(bold=True, italic=True, size=10, color="7A7366")
    pv.merge_cells("A7:D7")
    pv["A9"] = "KhuVực"
    pv["B9"] = "SảnPhẩm"
    pv["C9"] = "TổngThànhTiền"
    for c in ("A9", "B9", "C9"):
        pv[c].font = thin_hdr_font
        pv[c].fill = thin_hdr_fill
    r = 10
    for region in REGIONS:
        for prod in PRODUCTS:
            pv.cell(row=r, column=1, value=region)
            pv.cell(row=r, column=2, value=prod)
            cell = pv.cell(
                row=r, column=3,
                value=(f'=SUMIFS(DuLieu!H2:H{n_data},DuLieu!C2:C{n_data},A{r},'
                        f'DuLieu!E2:E{n_data},B{r})'),
            )
            cell.number_format = '#,##0" ₫"'
            r += 1
    for col, w in {"A": 10, "B": 10, "C": 16}.items():
        pv.column_dimensions[col].width = w

    # Thứ tự sheet gọn gàng: DuLieu, BangGia, TongHop, CongThuc, KỳVọng, PivotNote.
    wb._sheets = [wb["DuLieu"], wb["BangGia"], wb["TongHop"], wb["CongThuc"],
                  wb["KỳVọng"], wb["PivotTable_GhiChu"]]

    # Buộc Calc/Excel tính lại công thức khi mở (openpyxl không cache giá trị).
    wb.calculation.fullCalcOnLoad = True

    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    wb.save(OUT_XLSX)
    return {"path": OUT_XLSX, "n_data": n_data}


def verify(stats: dict) -> None:
    wb = load_workbook(stats["path"])
    expected_sheets = {"DuLieu", "BangGia", "TongHop", "CongThuc", "KỳVọng",
                       "PivotTable_GhiChu"}
    assert expected_sheets.issubset(set(wb.sheetnames)), "thiếu sheet"
    dl = wb["DuLieu"]
    assert len(dl.tables) == 1 and "BangHoaDon" in dl.tables, "thiếu Table object"
    assert "ThanhTien_Rng" in wb.defined_names, "thiếu named range"
    th = wb["TongHop"]
    assert len(th._charts) == 1, "thiếu chart"
    kv = wb["KỳVọng"]
    assert kv.cell(row=2, column=4).value == EXP_SUMIFS, "KỳVọng SUMIFS sai"


if __name__ == "__main__":
    stats = build()
    verify(stats)
    size_kb = os.path.getsize(stats["path"]) // 1024
    print(f"wrote {stats['path']} ({size_kb} KB)")
    print(f"rows={N_ROWS} expected SUMIFS={EXP_SUMIFS} COUNTIFS={EXP_COUNTIFS} "
          f"AVERAGEIFS={EXP_AVERAGEIFS:.2f} INDEX/MATCH(SP03)={EXP_INDEXMATCH} "
          f"XLOOKUP(SP05)={EXP_XLOOKUP} SUM(table)={EXP_SUMTABLE}")
