#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tạo BẢNG TÍNH TỰ KIỂM TRA tương thích hàm Office cho NaMiOS.

Mục tiêu (yêu cầu Cuong 09/11/2026): chứng minh — một cách TRUNG THỰC, ĐO ĐƯỢC —
rằng LibreOffice Calc trong NaMiOS chạy đúng các hàm quen thuộc của Microsoft
Excel. KHÔNG hứa 100%: file này ĐO độ tương thích thay vì tuyên bố.

Cách đo:
  - Mỗi hàm có 1 ô "Kết quả" là CÔNG THỨC THẬT (Calc sẽ tự tính khi mở file).
  - Ô "Kết quả đúng" là giá trị kỳ vọng được TÍNH ĐỘC LẬP bằng Python ngay trong
    script này (không nhờ Calc tính), nên nó đúng theo định nghĩa Excel.
  - Ô "Khớp?" so sánh hai ô trên:
        số   : =IF(ROUND(KếtQuả-KếtQuảĐúng,6)=0,"✅ OK","❌ SAI")
        chữ  : =IF(EXACT(KếtQuả,KếtQuảĐúng),"✅ OK","❌ SAI")
  => Mở file trong Calc trên ISO: hàm nào Calc tính đúng hiện ✅, lệch hiện ❌.

Số liệu là MINH HOẠ. Dùng openpyxl. Không cần mạng.

Chạy:  python3 tools/demo/make-office-compat-test.py
Đầu ra: distro/.../usr/share/namios/demo/KiemTra_Ham_Office.xlsx
"""
from __future__ import annotations

import os
import statistics
from datetime import date, timedelta

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/namios/demo/KiemTra_Ham_Office.xlsx",
)

# ---------------------------------------------------------------------------
# Màu thương hiệu (đồng bộ với demo báo cáo kinh doanh).
SON = "C93643"    # đỏ son
INK = "182E3B"    # mực
GOLD = "F2C66D"   # vàng tâm
IVORY = "F5F2EB"
GREENBG = "E4F3E4"
GREYTX = "7A7366"

# ---------------------------------------------------------------------------
# DỮ LIỆU NGUỒN (giống hệt sẽ ghi vào sheet "DuLieu"; expected tính từ đây).
NUMS = [5, 12, 8, 20, 3, 15, 9, 7, 18, 11]            # DuLieu!B2:B11
CATS = ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"]  # DuLieu!C2:C11
NUMS2 = [100, 250, 80, 300, 60, 180, 90, 70, 220, 130]    # DuLieu!D2:D11

CODES = ["SP01", "SP02", "SP03", "SP04", "SP05"]          # DuLieu!F2:F6
NAMES = ["Bút", "Vở", "Thước", "Tẩy", "Bảng"]            # DuLieu!G2:G6
PRICES = [5000, 12000, 8000, 3000, 45000]                # DuLieu!H2:H6
QTYS = [10, 20, 15, 25, 5]                               # DuLieu!I2:I6

HMONTHS = ["T1", "T2", "T3", "T4", "T5"]                  # DuLieu!F9:J9
HVALS = [100, 200, 150, 300, 250]                        # DuLieu!F10:J10

CASHFLOWS = [-1000, 300, 400, 500, 600]                  # DuLieu!K2:K6


# ---------------------------------------------------------------------------
# Hàm tính độc lập bằng Python (mô phỏng đúng ngữ nghĩa Excel).
def excel_substitute(text, old, new, instance):
    out, count, i = [], 0, 0
    while i < len(text):
        if text[i:i + len(old)] == old:
            count += 1
            if count == instance:
                out.append(new)
                i += len(old)
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def excel_replace(text, start, length, new):  # start 1-based
    return text[: start - 1] + new + text[start - 1 + length:]


def networkdays(a, b):
    sign = 1
    if a > b:
        a, b, sign = b, a, -1
    n, cur = 0, a
    while cur <= b:
        if cur.weekday() < 5:  # Mon..Fri
            n += 1
        cur += timedelta(days=1)
    return sign * n


def pmt(rate, nper, pv, fv=0.0, when=0):
    if rate == 0:
        return -(pv + fv) / nper
    return -(rate * (pv * (1 + rate) ** nper + fv)) / (((1 + rate) ** nper - 1) * (1 + rate * when))


def fv(rate, nper, pmt_, pv=0.0, when=0):
    if rate == 0:
        return -(pv + pmt_ * nper)
    return -(pv * (1 + rate) ** nper + pmt_ * (1 + rate * when) * (((1 + rate) ** nper - 1) / rate))


def pv(rate, nper, pmt_, fv_=0.0, when=0):
    if rate == 0:
        return -(fv_ + pmt_ * nper)
    return -(fv_ + pmt_ * (1 + rate * when) * (((1 + rate) ** nper - 1) / rate)) / ((1 + rate) ** nper)


def npv(rate, flows):
    return sum(cf / (1 + rate) ** (i + 1) for i, cf in enumerate(flows))


def irr(flows, guess=0.1):
    # Newton-Raphson trên NPV(rate)=0.
    r = guess
    for _ in range(200):
        f = sum(cf / (1 + r) ** t for t, cf in enumerate(flows))
        df = sum(-t * cf / (1 + r) ** (t + 1) for t, cf in enumerate(flows))
        if df == 0:
            break
        r_new = r - f / df
        if abs(r_new - r) < 1e-12:
            return r_new
        r = r_new
    return r


def rate_solve(nper, pmt_, pv_, fv_=0.0, when=0, guess=0.1):
    # Giải r từ: pv*(1+r)^n + pmt*(1+r*when)*((1+r)^n-1)/r + fv = 0
    def f(r):
        if r == 0:
            return pv_ + pmt_ * nper + fv_
        return pv_ * (1 + r) ** nper + pmt_ * (1 + r * when) * (((1 + r) ** nper - 1) / r) + fv_

    r = guess
    for _ in range(200):
        h = 1e-7
        f0 = f(r)
        df = (f(r + h) - f(r - h)) / (2 * h)
        if df == 0:
            break
        r_new = r - f0 / df
        if abs(r_new - r) < 1e-12:
            return r_new
        r = r_new
    return r


REF_DATE = date(2026, 3, 15)

# ---------------------------------------------------------------------------
# BẢNG HÀM: (Nhóm, Tên, công_thức_hiển_thị, công_thức_sống, kỳ_vọng, kind)
# kind: "num" | "text" | "bool"  (bool so sánh bằng số, giá trị kỳ vọng là TRUE/FALSE)
ROWS = []


def add(group, name, formula, expected, kind="num"):
    # công thức hiển thị == công thức sống (đều cú pháp Excel A1 với dấu !).
    ROWS.append((group, name, formula, formula, expected, kind))


# --- Toán ---
G = "Toán"
add(G, "SUM", "=SUM(DuLieu!B2:B11)", sum(NUMS))
add(G, "SUMIF", '=SUMIF(DuLieu!C2:C11,"A",DuLieu!B2:B11)',
    sum(n for n, c in zip(NUMS, CATS) if c == "A"))
add(G, "SUMIFS", '=SUMIFS(DuLieu!D2:D11,DuLieu!C2:C11,"B",DuLieu!B2:B11,">8")',
    sum(d for d, c, n in zip(NUMS2, CATS, NUMS) if c == "B" and n > 8))
add(G, "SUMPRODUCT", "=SUMPRODUCT(DuLieu!B2:B11,DuLieu!D2:D11)",
    sum(a * b for a, b in zip(NUMS, NUMS2)))
add(G, "ROUND", "=ROUND(3.14159,2)", round(3.14159, 2))
add(G, "ROUNDUP", "=ROUNDUP(3.14159,2)", 3.15)
add(G, "ROUNDDOWN", "=ROUNDDOWN(3.148,2)", 3.14)
add(G, "MOD", "=MOD(17,5)", 17 % 5)
add(G, "POWER", "=POWER(2,10)", 2 ** 10)
add(G, "SQRT", "=SQRT(144)", 12)
add(G, "ABS", "=ABS(-25.5)", abs(-25.5))
add(G, "INT", "=INT(-3.2)", -4)            # Excel INT làm tròn xuống (−∞)
add(G, "CEILING", "=CEILING(23,5)", 25)
add(G, "FLOOR", "=FLOOR(23,5)", 20)
add(G, "PRODUCT", "=PRODUCT(2,3,4)", 2 * 3 * 4)

# --- Thống kê ---
G = "Thống kê"
add(G, "AVERAGE", "=AVERAGE(DuLieu!B2:B11)", statistics.mean(NUMS))
add(G, "AVERAGEIF", '=AVERAGEIF(DuLieu!C2:C11,"A",DuLieu!B2:B11)',
    statistics.mean([n for n, c in zip(NUMS, CATS) if c == "A"]))
add(G, "COUNT", "=COUNT(DuLieu!B2:B11)", len(NUMS))
add(G, "COUNTA", "=COUNTA(DuLieu!C2:C11)", len(CATS))
add(G, "COUNTIF", '=COUNTIF(DuLieu!C2:C11,"C")', CATS.count("C"))
add(G, "COUNTIFS", '=COUNTIFS(DuLieu!C2:C11,"A",DuLieu!B2:B11,">7")',
    sum(1 for n, c in zip(NUMS, CATS) if c == "A" and n > 7))
add(G, "MAX", "=MAX(DuLieu!B2:B11)", max(NUMS))
add(G, "MIN", "=MIN(DuLieu!B2:B11)", min(NUMS))
add(G, "MEDIAN", "=MEDIAN(DuLieu!B2:B11)", statistics.median(NUMS))
add(G, "STDEV", "=STDEV(DuLieu!B2:B11)", statistics.stdev(NUMS))
add(G, "VAR", "=VAR(DuLieu!B2:B11)", statistics.variance(NUMS))
add(G, "RANK", "=RANK(12,DuLieu!B2:B11)", sorted(NUMS, reverse=True).index(12) + 1)
add(G, "LARGE", "=LARGE(DuLieu!B2:B11,2)", sorted(NUMS, reverse=True)[1])
add(G, "SMALL", "=SMALL(DuLieu!B2:B11,2)", sorted(NUMS)[1])
add(G, "PERCENTILE", "=PERCENTILE(DuLieu!B2:B11,0.25)",
    statistics.quantiles(NUMS, n=4, method="inclusive")[0])  # = 7.25

# --- Logic ---
G = "Logic"
add(G, "IF", '=IF(10>5,"Đúng","Sai")', "Đúng", "text")
add(G, "IFS", '=IFS(5>10,"A",8>3,"B",TRUE,"C")', "B", "text")
add(G, "AND", "=AND(1=1,2=2,3=3)", True, "bool")
add(G, "OR", "=OR(1=5,2=2,3=9)", True, "bool")
add(G, "NOT", "=NOT(1=2)", True, "bool")
add(G, "IFERROR", '=IFERROR(1/0,"Lỗi")', "Lỗi", "text")
add(G, "IFNA", '=IFNA(NA(),"Không có")', "Không có", "text")
add(G, "SWITCH", '=SWITCH(3,1,"Một",2,"Hai",3,"Ba","Khác")', "Ba", "text")
add(G, "XOR", "=XOR(TRUE,FALSE,TRUE)", False, "bool")

# --- Tra cứu ---
G = "Tra cứu"
add(G, "VLOOKUP", '=VLOOKUP("SP03",DuLieu!F2:I6,3,FALSE)', PRICES[CODES.index("SP03")])
add(G, "HLOOKUP", '=HLOOKUP("T4",DuLieu!F9:J10,2,FALSE)', HVALS[HMONTHS.index("T4")])
add(G, "INDEX", "=INDEX(DuLieu!G2:G6,4)", NAMES[3], "text")
add(G, "MATCH", '=MATCH("SP04",DuLieu!F2:F6,0)', CODES.index("SP04") + 1)
add(G, "XLOOKUP", '=XLOOKUP("SP05",DuLieu!F2:F6,DuLieu!H2:H6)', PRICES[CODES.index("SP05")])
add(G, "CHOOSE", '=CHOOSE(2,"Đỏ","Xanh","Vàng")', "Xanh", "text")
add(G, "OFFSET", "=OFFSET(DuLieu!B2,3,0)", NUMS[3])
add(G, "INDIRECT", '=INDIRECT("H1")', 777)  # H1 nằm cùng sheet KiemTra = 777

# --- Văn bản ---
G = "Văn bản"
add(G, "LEFT", '=LEFT("NaMiOS",2)', "Na", "text")
add(G, "RIGHT", '=RIGHT("NaMiOS",2)', "OS", "text")
add(G, "MID", '=MID("NaMiOS",3,2)', "Mi", "text")
add(G, "LEN", '=LEN("NaMiOS")', 6)
add(G, "TRIM", '=TRIM("  xin  chào  ")', " ".join("  xin  chào  ".split()), "text")
add(G, "UPPER", '=UPPER("namios")', "NAMIOS", "text")
add(G, "LOWER", '=LOWER("NaMiOS")', "namios", "text")
add(G, "PROPER", '=PROPER("xin chào bạn")', "xin chào bạn".title(), "text")
add(G, "CONCAT", '=CONCAT("Na","Mi","OS")', "NaMiOS", "text")
add(G, "TEXTJOIN", '=TEXTJOIN("-",TRUE,"a","b","c")', "a-b-c", "text")
add(G, "SUBSTITUTE", '=SUBSTITUTE("2024-2024","2024","2026",1)',
    excel_substitute("2024-2024", "2024", "2026", 1), "text")
add(G, "REPLACE", '=REPLACE("ABCDEF",2,3,"xyz")', excel_replace("ABCDEF", 2, 3, "xyz"), "text")
add(G, "FIND", '=FIND("Mi","NaMiOS")', "NaMiOS".find("Mi") + 1)
add(G, "SEARCH", '=SEARCH("mi","NaMiOS")', "NaMiOS".lower().find("mi") + 1)
add(G, "TEXT", '=TEXT(5,"000")', "005", "text")   # format số-thuần, không phụ thuộc locale
add(G, "VALUE", '=VALUE("1234")', 1234)
add(G, "REPT", '=REPT("*",5)', "*" * 5, "text")

# --- Ngày-giờ ---
G = "Ngày-giờ"
add(G, "DATE", "=DATE(2026,3,15)", REF_DATE, "num")
add(G, "YEAR", "=YEAR(DATE(2026,3,15))", REF_DATE.year)
add(G, "MONTH", "=MONTH(DATE(2026,3,15))", REF_DATE.month)
add(G, "DAY", "=DAY(DATE(2026,3,15))", REF_DATE.day)
add(G, "TODAY", '=IF(TODAY()>DATE(2000,1,1),"OK","SAI")', "OK", "text")  # động → kiểm bằng logic
add(G, "EOMONTH", "=DAY(EOMONTH(DATE(2026,3,15),1))", 30)   # cuối tháng 4/2026
add(G, "DATEDIF", '=DATEDIF(DATE(2026,1,1),DATE(2026,3,15),"d")',
    (date(2026, 3, 15) - date(2026, 1, 1)).days)
add(G, "WEEKDAY", "=WEEKDAY(DATE(2026,3,15),2)", REF_DATE.isoweekday())  # 7 = Chủ nhật
add(G, "NETWORKDAYS", "=NETWORKDAYS(DATE(2026,3,2),DATE(2026,3,6))",
    networkdays(date(2026, 3, 2), date(2026, 3, 6)))

# --- Tài chính ---
G = "Tài chính"
add(G, "PMT", "=PMT(0.01,12,-1000)", pmt(0.01, 12, -1000))
add(G, "FV", "=FV(0.01,12,-100)", fv(0.01, 12, -100))
add(G, "PV", "=PV(0.01,12,-100)", pv(0.01, 12, -100))
add(G, "NPV", "=NPV(0.1,300,400,500,600)-1000", npv(0.1, [300, 400, 500, 600]) - 1000)
add(G, "IRR", "=IRR(DuLieu!K2:K6)", irr(CASHFLOWS))
add(G, "RATE", "=RATE(12,-100,1000)", rate_solve(12, -100, 1000))


# ---------------------------------------------------------------------------
def build():
    thin = Side(style="thin", color="D8CFBE")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    wb = Workbook()

    # ---- Sheet DỮ LIỆU ----
    dl = wb.active
    dl.title = "DuLieu"
    dl["A1"] = "STT"; dl["B1"] = "SoLieu"; dl["C1"] = "Nhom"; dl["D1"] = "SoLieu2"
    for i in range(10):
        r = 2 + i
        dl.cell(row=r, column=1, value=i + 1)
        dl.cell(row=r, column=2, value=NUMS[i])
        dl.cell(row=r, column=3, value=CATS[i])
        dl.cell(row=r, column=4, value=NUMS2[i])
    # Bảng tra dọc (Ma|Ten|Gia|SoLuong) ở F..I
    dl["F1"] = "Ma"; dl["G1"] = "Ten"; dl["H1"] = "Gia"; dl["I1"] = "SoLuong"
    for i in range(5):
        r = 2 + i
        dl.cell(row=r, column=6, value=CODES[i])
        dl.cell(row=r, column=7, value=NAMES[i])
        dl.cell(row=r, column=8, value=PRICES[i])
        dl.cell(row=r, column=9, value=QTYS[i])
    # Bảng tra ngang (cho HLOOKUP) ở F9:J10
    for i in range(5):
        dl.cell(row=9, column=6 + i, value=HMONTHS[i])
        dl.cell(row=10, column=6 + i, value=HVALS[i])
    # Dòng tiền cho IRR ở K2:K6
    dl["K1"] = "DongTien"
    for i in range(5):
        dl.cell(row=2 + i, column=11, value=CASHFLOWS[i])
    for col, w in {"A": 6, "B": 8, "C": 7, "D": 9, "F": 8, "G": 9,
                   "H": 9, "I": 9, "J": 7, "K": 10}.items():
        dl.column_dimensions[col].width = w
    for c in range(1, 12):
        cell = dl.cell(row=1, column=c)
        if cell.value is not None:
            cell.font = Font(bold=True, color=INK)

    # ---- Sheet KIỂM TRA ----
    ws = wb.create_sheet("KiemTra", 0)
    ws.sheet_view.showGridLines = False

    # Ô phụ cho INDIRECT (cùng sheet, không cần tên sheet → mọi cú pháp đều hiểu).
    ws["H1"] = 777
    ws["I1"] = "← ô phụ cho INDIRECT(\"H1\")"
    ws["I1"].font = Font(size=8, italic=True, color=GREYTX)

    # Tiêu đề lớn.
    ws.merge_cells("A1:F1")
    t = ws["A1"]
    t.value = "KIỂM TRA TƯƠNG THÍCH HÀM OFFICE"
    t.font = Font(name="Arial", size=17, bold=True, color="FFFFFF")
    t.fill = PatternFill("solid", fgColor=SON)
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 34

    ws.merge_cells("A2:F2")
    ws["A2"].value = ("NaMiOS · LibreOffice Calc ↔ Microsoft Excel — tự chấm bằng công thức sống. "
                      "Mở trên ISO để xác nhận: hàm đúng hiện ✅, hàm lệch hiện ❌.")
    ws["A2"].font = Font(name="Arial", size=9, italic=True, color=GREYTX)
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    header_row = 5
    first = header_row + 1
    last = first + len(ROWS) - 1

    # Ô tổng kết (đếm OK/total động bằng công thức).
    ws.merge_cells("A3:F3")
    s = ws["A3"]
    s.value = (f'="TỔNG KẾT:  KHỚP "&COUNTIF(F{first}:F{last},"✅ OK")&" / "&'
               f'{len(ROWS)}&" hàm      —      LỆCH "&COUNTIF(F{first}:F{last},"❌ SAI")&" hàm"')
    s.font = Font(name="Arial", size=12, bold=True, color=INK)
    s.fill = PatternFill("solid", fgColor=GOLD)
    s.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 26

    # Tiêu đề cột.
    headers = ["Nhóm", "Tên hàm", "Công thức", "Kết quả", "Kết quả đúng", "Khớp?"]
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=c, value=h)
        cell.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=INK)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    ws.row_dimensions[header_row].height = 22

    # Các dòng hàm.
    for idx, (group, name, disp, live, expected, kind) in enumerate(ROWS):
        r = first + idx

        gcell = ws.cell(row=r, column=1, value=group)
        gcell.font = Font(size=9, color=GREYTX)

        ncell = ws.cell(row=r, column=2, value=name)
        ncell.font = Font(bold=True, color=INK)

        # Cột "Công thức": lưu CHỮ (data_type='s') để hiện công thức literal, không tự tính.
        dcell = ws.cell(row=r, column=3)
        dcell.value = disp
        dcell.data_type = "s"
        dcell.font = Font(name="Consolas", size=9, color="40484F")

        # Cột "Kết quả": CÔNG THỨC SỐNG (Calc tự tính).
        rcell = ws.cell(row=r, column=4, value=live)

        # Cột "Kết quả đúng": kỳ vọng tính độc lập bằng Python.
        ecell = ws.cell(row=r, column=5, value=expected)
        ecell.font = Font(bold=True)

        # Cột "Khớp?".
        if kind == "text":
            kc = ws.cell(row=r, column=6, value=f'=IF(EXACT(D{r},E{r}),"✅ OK","❌ SAI")')
        else:  # num hoặc bool → so sánh số (TRUE/FALSE tự ép về 1/0)
            kc = ws.cell(row=r, column=6, value=f'=IF(ROUND(D{r}-E{r},6)=0,"✅ OK","❌ SAI")')
        kc.alignment = Alignment(horizontal="center")
        kc.font = Font(bold=True)

        # Định dạng ngày cho dòng DATE.
        if name == "DATE":
            rcell.number_format = "YYYY-MM-DD"
            ecell.number_format = "YYYY-MM-DD"

        for c in range(1, 7):
            ws.cell(row=r, column=c).border = border
        if idx % 2 == 0:
            for c in range(1, 7):
                if ws.cell(row=r, column=c).fill.fgColor.rgb in (None, "00000000"):
                    ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=IVORY)

    # Ghi chú hàm động.
    note_row = last + 2
    ws.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=6)
    nc = ws.cell(row=note_row, column=1)
    nc.value = ("Ghi chú: TODAY()/NOW() là hàm ĐỘNG (đổi theo thời điểm mở) nên được kiểm bằng điều "
                "kiện logic (TODAY()>DATE(2000,1,1)) thay vì so với một giá trị cố định.")
    nc.font = Font(size=9, italic=True, color=GREYTX)
    nc.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[note_row].height = 30

    note_row2 = note_row + 1
    ws.merge_cells(start_row=note_row2, start_column=1, end_row=note_row2, end_column=6)
    nc2 = ws.cell(row=note_row2, column=1)
    nc2.value = ("Giá trị cột “Kết quả đúng” được TÍNH ĐỘC LẬP bằng Python (không nhờ Calc), "
                 "nên là chuẩn đối chiếu. Dữ liệu nguồn ở sheet “DuLieu”.")
    nc2.font = Font(size=9, italic=True, color=GREYTX)
    nc2.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[note_row2].height = 24

    # Độ rộng cột + đóng băng.
    for col, w in zip("ABCDEF", [11, 13, 40, 18, 18, 10]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A6"

    # Buộc Calc/Excel tính lại toàn bộ khi mở (file openpyxl không có giá trị cache).
    wb.calculation.fullCalcOnLoad = True

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    return first, last


def verify(first, last):
    """Mở lại bằng openpyxl để chắc chắn có đủ công thức + cột kỳ vọng."""
    wb = load_workbook(OUT)                  # formula mode
    wbv = load_workbook(OUT, data_only=True)  # (không có cache → None, chỉ kiểm cấu trúc)
    ws = wb["KiemTra"]
    assert "DuLieu" in wb.sheetnames, "thiếu sheet DuLieu"
    live_ok = 0
    expected_ok = 0
    for idx in range(len(ROWS)):
        r = first + idx
        live = ws.cell(row=r, column=4).value
        disp = ws.cell(row=r, column=3).value
        exp = ws.cell(row=r, column=5).value
        khop = ws.cell(row=r, column=6).value
        assert isinstance(live, str) and live.startswith("="), f"dòng {r}: Kết quả không phải công thức"
        assert ws.cell(row=r, column=4).data_type == "f", f"dòng {r}: cột Kết quả chưa phải formula"
        assert isinstance(disp, str) and disp.startswith("="), f"dòng {r}: Công thức hiển thị sai"
        assert ws.cell(row=r, column=3).data_type == "s", f"dòng {r}: Công thức phải là CHỮ"
        assert exp is not None, f"dòng {r}: thiếu Kết quả đúng"
        assert isinstance(khop, str) and khop.startswith("=IF("), f"dòng {r}: thiếu công thức Khớp?"
        live_ok += 1
        expected_ok += 1
    return live_ok, expected_ok


if __name__ == "__main__":
    first, last = build()
    lo, eo = verify(first, last)
    print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")
    print(f"functions covered: {len(ROWS)}  | live formulas verified: {lo}  | expected values: {eo}")
    # In vài giá trị kỳ vọng tài chính/thống kê để kiểm bằng mắt.
    sample = {name: exp for (_g, name, _d, _l, exp, _k) in ROWS
              if name in ("PMT", "FV", "PV", "NPV", "IRR", "RATE", "STDEV", "VAR", "PERCENTILE")}
    for k, v in sample.items():
        print(f"   expected[{k}] = {v}")
