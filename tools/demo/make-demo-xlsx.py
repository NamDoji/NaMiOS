#!/usr/bin/env python3
"""Tạo file demo bảng tính tiếng Việt (BÁO CÁO KINH DOANH) có BẢNG + CÔNG THỨC
+ BIỂU ĐỒ để NaMiOS mở sẵn trong LibreOffice Calc làm ảnh minh hoạ "Excel chạy
thật, tiếng Việt" (yêu cầu Cuong 09/11/2026).

Số liệu là MINH HOẠ (không phải số kinh doanh thật). Dùng openpyxl; LibreOffice
Calc mở .xlsx này sẽ tự tính công thức + render biểu đồ cột.

Chạy: python3 tools/demo/make-demo-xlsx.py
Đầu ra: distro/.../usr/share/namios/demo/BaoCao_KinhDoanh_Q4_2026.xlsx
"""
from __future__ import annotations

import os
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/namios/demo/BaoCao_KinhDoanh_Q4_2026.xlsx",
)

# Màu thương hiệu Sen Việt.
SON = "C93643"       # đỏ son
INK = "182E3B"       # mực
GOLD = "F2C66D"      # vàng tâm
IVORY = "F5F2EB"

MONTHS = ["Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"]
DOANH_THU = [1250_000_000, 1380_000_000, 1210_000_000, 1560_000_000, 1720_000_000, 1890_000_000]
CHI_PHI = [920_000_000, 1010_000_000, 940_000_000, 1120_000_000, 1180_000_000, 1250_000_000]

thin = Side(style="thin", color="D8CFBE")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
money_fmt = '#,##0" ₫"'
pct_fmt = '0.0"%"'


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Báo cáo Quý 4"

    # Tiêu đề.
    ws.merge_cells("A1:E1")
    t = ws["A1"]
    t.value = "BÁO CÁO KINH DOANH — NỬA CUỐI NĂM 2026"
    t.font = Font(name="Arial", size=15, bold=True, color=INK)
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28
    ws.merge_cells("A2:E2")
    ws["A2"].value = "Đơn vị: đồng (₫) · Số liệu minh hoạ"
    ws["A2"].font = Font(name="Arial", size=9, italic=True, color="7A7366")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Tiêu đề cột.
    headers = ["Tháng", "Doanh thu", "Chi phí", "Lợi nhuận", "Tỷ suất LN"]
    hr = 4
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=hr, column=c, value=h)
        cell.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=SON)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    # Dữ liệu + CÔNG THỨC (Lợi nhuận, Tỷ suất).
    first = hr + 1
    for i, m in enumerate(MONTHS):
        r = first + i
        ws.cell(row=r, column=1, value=m).border = border
        dt = ws.cell(row=r, column=2, value=DOANH_THU[i]); dt.number_format = money_fmt; dt.border = border
        cp = ws.cell(row=r, column=3, value=CHI_PHI[i]); cp.number_format = money_fmt; cp.border = border
        ln = ws.cell(row=r, column=4, value=f"=B{r}-C{r}"); ln.number_format = money_fmt; ln.border = border
        ln.font = Font(color=SON, bold=True)
        ts = ws.cell(row=r, column=5, value=f"=(B{r}-C{r})/B{r}*100"); ts.number_format = pct_fmt; ts.border = border
        if i % 2 == 0:
            for c in range(1, 6):
                ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=IVORY)

    # Dòng TỔNG + TRUNG BÌNH.
    last = first + len(MONTHS) - 1
    tr = last + 1
    ws.cell(row=tr, column=1, value="TỔNG").font = Font(bold=True, color=INK)
    for c, col in [(2, "B"), (3, "C"), (4, "D")]:
        cell = ws.cell(row=tr, column=c, value=f"=SUM({col}{first}:{col}{last})")
        cell.number_format = money_fmt; cell.font = Font(bold=True, color=INK)
        cell.fill = PatternFill("solid", fgColor=GOLD); cell.border = border
    tbt = ws.cell(row=tr, column=5, value=f"=(B{tr}-C{tr})/B{tr}*100")
    tbt.number_format = pct_fmt; tbt.font = Font(bold=True, color=INK)
    tbt.fill = PatternFill("solid", fgColor=GOLD); tbt.border = border
    ws.cell(row=tr, column=1).fill = PatternFill("solid", fgColor=GOLD)
    ws.cell(row=tr, column=1).border = border

    ar = tr + 1
    ws.cell(row=ar, column=1, value="Trung bình/tháng").font = Font(italic=True, color=INK)
    ws.cell(row=ar, column=4, value=f"=AVERAGE(D{first}:D{last})").number_format = money_fmt

    # Độ rộng cột.
    for c, w in zip("ABCDE", [16, 18, 18, 18, 12]):
        ws.column_dimensions[c].width = w

    # BIỂU ĐỒ CỘT: Doanh thu vs Chi phí theo tháng.
    chart = BarChart()
    chart.type = "col"; chart.style = 10
    chart.title = "Doanh thu & Chi phí theo tháng"
    chart.y_axis.title = "Đồng (₫)"; chart.x_axis.title = "Tháng"
    data = Reference(ws, min_col=2, max_col=3, min_row=hr, max_row=last)
    cats = Reference(ws, min_col=1, min_row=first, max_row=last)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height = 8.5; chart.width = 17

    # Đường Lợi nhuận chồng lên.
    line = LineChart()
    ldata = Reference(ws, min_col=4, max_col=4, min_row=hr, max_row=last)
    line.add_data(ldata, titles_from_data=True)
    line.set_categories(cats)
    chart += line

    ws.add_chart(chart, "G4")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")


if __name__ == "__main__":
    main()
