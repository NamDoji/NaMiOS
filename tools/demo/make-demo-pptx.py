#!/usr/bin/env python3
"""Tạo file demo TRÌNH CHIẾU tiếng Việt (PowerPoint .pptx) để NaMiOS mở sẵn
trong LibreOffice Impress làm ảnh minh hoạ "PowerPoint chạy thật, tiếng Việt"
(yêu cầu Cuong 10/11/2026: "*.ppt và những phần của bộ office Microsoft thì
NaMiOffice đều có và hoạt động xuất sắc" — mảnh còn thiếu chính là Impress).

4 slide:
  1) Tiêu đề — "NaMiOffice — Trình chiếu" + phụ đề.
  2) Danh sách gạch đầu dòng — NaMiOffice có đủ Writer/Calc/Impress/Draw/Base/Math.
  3) Biểu đồ cột NGUYÊN SINH (native chart, không phải ảnh dán) — "Doanh thu theo
     quý"; LibreOffice Impress đọc + render được biểu đồ OOXML này trực tiếp.
  4) Bảng — ánh xạ Microsoft Office -> NaMiOffice.

Số liệu là MINH HOẠ (không phải số kinh doanh thật). Dùng python-pptx (đã cài,
bản 1.0.2); LibreOffice Impress mở .pptx này sẽ render chữ + biểu đồ + bảng.

Chạy: python3 tools/demo/make-demo-pptx.py
Đầu ra: distro/.../usr/share/namios/demo/GioiThieu_NaMiOffice.pptx

verified_on_host: NO — máy soạn gói không có LibreOffice Impress cài để mở lại
và soi bằng mắt; script tự kiểm bằng cách python-pptx MỞ LẠI file vừa ghi (xem
cuối file) để bắt lỗi cấu trúc OOXML sớm, nhưng không thay được việc nhìn trên
ISO thật trong QEMU.
"""
from __future__ import annotations

import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/namios/demo/GioiThieu_NaMiOffice.pptx",
)

# Màu thương hiệu Sen Việt.
NGA = RGBColor(0xFB, 0xF8, 0xF2)         # ngà — nền sáng, KHÔNG dùng nền đen
NGA_DAM = RGBColor(0xEF, 0xE3, 0xD1)     # ngà đậm — dải/khối phụ
SON = RGBColor(0xC9, 0x36, 0x43)         # đỏ son — tiêu đề/nhấn chính
DAI = RGBColor(0x92, 0x21, 0x2E)         # đỏ đài — nhấn đậm/viền
VANG = RGBColor(0xF2, 0xC6, 0x6D)        # vàng tâm — điểm nhấn/nền header phụ
MUC = RGBColor(0x18, 0x2E, 0x3B)         # mực — chữ chính
TRANG = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Arial"  # font phổ biến sẵn trên mọi bản dựng, kể cả thiếu font Office


def set_background(slide, color: RGBColor) -> None:
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def add_brand_footer(slide, prs, label: str) -> None:
    """Dải màu đáy slide + chữ nhỏ 'NaMiOS · Sen Việt' — nhận diện thương hiệu
    nhất quán trên mọi slide, không che nội dung chính."""
    bar = slide.shapes.add_shape(1, Emu(0), prs.slide_height - Inches(0.28), prs.slide_width, Inches(0.28))
    bar.fill.solid()
    bar.fill.fore_color.rgb = SON
    bar.line.fill.background()
    bar.shadow.inherit = False
    tf = bar.text_frame
    tf.margin_left = Inches(0.25)
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = f"NaMiOS · Sen Việt — {label}"
    p.font.size = Pt(10)
    p.font.color.rgb = TRANG
    p.font.name = FONT


def add_textbox(slide, left, top, width, height, text, size, color, bold=False, italic=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.italic = italic
    p.font.color.rgb = color
    p.font.name = FONT
    p.alignment = align
    return box


def slide_title(prs) -> None:
    """Slide 1 — Tiêu đề."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # layout trống (blank)
    set_background(slide, NGA)

    # Khối màu đỏ son bên trái toàn chiều cao — bố cục "bìa sách" kiểu Sen Việt.
    band = slide.shapes.add_shape(1, Emu(0), Emu(0), Inches(0.35), prs.slide_height)
    band.fill.solid()
    band.fill.fore_color.rgb = SON
    band.line.fill.background()
    band.shadow.inherit = False

    # Gạch vàng tâm ngang dưới tiêu đề.
    rule = slide.shapes.add_shape(1, Inches(0.9), Inches(3.55), Inches(2.4), Pt(5))
    rule.fill.solid()
    rule.fill.fore_color.rgb = VANG
    rule.line.fill.background()
    rule.shadow.inherit = False

    add_textbox(slide, Inches(0.85), Inches(2.55), Inches(11.5), Inches(1.2),
                "NaMiOffice — Trình chiếu", 44, MUC, bold=True)
    add_textbox(slide, Inches(0.9), Inches(3.75), Inches(11), Inches(0.8),
                "Bộ văn phòng của người Việt • dựa trên LibreOffice", 22, SON, italic=True)
    add_textbox(slide, Inches(0.9), Inches(6.4), Inches(11), Inches(0.5),
                "Demo tự mở trong NaMiOS — số liệu minh hoạ", 12, MUC, italic=True)
    add_brand_footer(slide, prs, "Trang bìa")


def slide_bullets(prs) -> None:
    """Slide 2 — NaMiOffice có đủ các ứng dụng tương đương Microsoft Office."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, NGA)

    add_textbox(slide, Inches(0.7), Inches(0.45), Inches(11.5), Inches(0.9),
                "NaMiOffice có đủ bộ ứng dụng văn phòng", 30, SON, bold=True)
    rule = slide.shapes.add_shape(1, Inches(0.75), Inches(1.25), Inches(3.2), Pt(4))
    rule.fill.solid(); rule.fill.fore_color.rgb = VANG; rule.line.fill.background(); rule.shadow.inherit = False

    items = [
        ("Writer", "tương đương Word — soạn thảo văn bản"),
        ("Calc", "tương đương Excel — bảng tính, công thức, biểu đồ"),
        ("Impress", "tương đương PowerPoint — trình chiếu (đang xem file này)"),
        ("Draw", "vẽ & sơ đồ — tương đương Publisher ở mức cơ bản"),
        ("Base", "tương đương Access — cơ sở dữ liệu"),
        ("Math", "soạn công thức toán học"),
    ]
    box = slide.shapes.add_textbox(Inches(0.9), Inches(1.65), Inches(11), Inches(5.3))
    tf = box.text_frame
    tf.word_wrap = True
    for i, (name, desc) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(14)
        run_dot = p.add_run(); run_dot.text = "● "
        run_dot.font.size = Pt(18); run_dot.font.color.rgb = VANG; run_dot.font.name = FONT
        run_name = p.add_run(); run_name.text = name + " "
        run_name.font.size = Pt(18); run_name.font.bold = True; run_name.font.color.rgb = DAI; run_name.font.name = FONT
        run_desc = p.add_run(); run_desc.text = "— " + desc
        run_desc.font.size = Pt(18); run_desc.font.color.rgb = MUC; run_desc.font.name = FONT
    add_brand_footer(slide, prs, "Các ứng dụng")


def slide_chart(prs) -> None:
    """Slide 3 — Biểu đồ cột NGUYÊN SINH (native OOXML chart)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, NGA)

    add_textbox(slide, Inches(0.7), Inches(0.4), Inches(11.5), Inches(0.9),
                "Doanh thu theo quý", 30, SON, bold=True)
    rule = slide.shapes.add_shape(1, Inches(0.75), Inches(1.2), Inches(2.2), Pt(4))
    rule.fill.solid(); rule.fill.fore_color.rgb = VANG; rule.line.fill.background(); rule.shadow.inherit = False
    add_textbox(slide, Inches(0.75), Inches(1.3), Inches(8), Inches(0.5),
                "Đơn vị: triệu đồng · Số liệu minh hoạ", 12, MUC, italic=True)

    chart_data = CategoryChartData()
    chart_data.categories = ["Quý 1", "Quý 2", "Quý 3", "Quý 4"]
    chart_data.add_series("Doanh thu (triệu đồng)", (1250, 1380, 1560, 1890))

    x, y, cx, cy = Inches(0.9), Inches(1.95), Inches(11.2), Inches(4.9)
    gframe = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data)
    chart = gframe.chart
    chart.has_legend = False
    chart.has_title = False
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.font.size = Pt(12)
    plot.data_labels.font.color.rgb = MUC
    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = SON
    cat_axis = chart.category_axis
    cat_axis.tick_labels.font.size = Pt(13)
    cat_axis.tick_labels.font.color.rgb = MUC
    val_axis = chart.value_axis
    val_axis.tick_labels.font.size = Pt(11)
    val_axis.tick_labels.font.color.rgb = MUC
    val_axis.has_major_gridlines = True

    add_brand_footer(slide, prs, "Biểu đồ")


def slide_table(prs) -> None:
    """Slide 4 — Bảng ánh xạ Microsoft Office -> NaMiOffice."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, NGA)

    add_textbox(slide, Inches(0.7), Inches(0.4), Inches(11.5), Inches(0.9),
                "Microsoft Office tương ứng NaMiOffice", 28, SON, bold=True)
    rule = slide.shapes.add_shape(1, Inches(0.75), Inches(1.15), Inches(3.4), Pt(4))
    rule.fill.solid(); rule.fill.fore_color.rgb = VANG; rule.line.fill.background(); rule.shadow.inherit = False

    rows_data = [
        ("Microsoft Office", "NaMiOffice"),
        ("Word (.doc/.docx)", "Writer"),
        ("Excel (.xls/.xlsx)", "Calc"),
        ("PowerPoint (.ppt/.pptx)", "Impress"),
        ("Access (.mdb/.accdb)", "Base"),
    ]
    n_rows, n_cols = len(rows_data), 2
    left, top, width, height = Inches(1.4), Inches(1.7), Inches(10.5), Inches(4.6)
    gframe = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = gframe.table
    table.columns[0].width = Inches(6.5)
    table.columns[1].width = Inches(4.0)

    for r, (a, b) in enumerate(rows_data):
        for c, val in enumerate((a, b)):
            cell = table.cell(r, c)
            cell.text = val
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = cell.text_frame.paragraphs[0]
            para.font.name = FONT
            para.font.size = Pt(18 if r == 0 else 16)
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = SON
                para.font.bold = True
                para.font.color.rgb = TRANG
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NGA_DAM if r % 2 == 0 else NGA
                para.font.color.rgb = MUC
                if c == 1:
                    para.font.bold = True
                    para.font.color.rgb = DAI

    add_brand_footer(slide, prs, "Bảng ứng dụng")


def main() -> None:
    prs = Presentation()
    # 16:9 widescreen — chuẩn trình chiếu hiện đại, không phải 4:3 cũ.
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide_title(prs)
    slide_bullets(prs)
    slide_chart(prs)
    slide_table(prs)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prs.save(OUT)
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB)")

    # Tự kiểm: mở lại ngay file vừa ghi để bắt lỗi cấu trúc OOXML sớm.
    reopened = Presentation(OUT)
    assert len(reopened.slides) == 4, f"expected 4 slides, got {len(reopened.slides)}"
    print(f"tu-kiem: mo lai OK, {len(reopened.slides)} slide")


if __name__ == "__main__":
    main()
