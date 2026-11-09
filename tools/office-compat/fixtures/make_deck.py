#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh fixture Deck.pptx cho vertical-slice NaMiSlides (NaMiOffice v2).

Xem docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md mục C và
05_PROMPT_CLAUDE_CODE.md bước 3: một PPTX có master/layout, chart gốc
(native, có data binding — không phải ảnh chụp), bảng, ảnh, speaker notes
trên mỗi slide, và dùng ít nhất một layout không mặc định.

Chạy:  python3 tools/office-compat/fixtures/make_deck.py
Đầu ra: tools/office-compat/fixtures/Deck.pptx (+ _assets/logo.png tạm, tái
dùng từ make_doc.py nếu đã sinh trước đó)
"""
from __future__ import annotations

import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Cm, Inches, Pt
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PPTX = os.path.join(HERE, "Deck.pptx")
ASSETS_DIR = os.path.join(HERE, "_assets")
LOGO_PNG = os.path.join(ASSETS_DIR, "logo.png")

SON_RGB = (0xC9, 0x36, 0x43)
INK_RGB = (0x18, 0x2E, 0x3B)


def ensure_logo_png(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (240, 120), (245, 242, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 235, 115], outline=SON_RGB, width=4)
    d.ellipse([20, 20, 100, 100], fill=SON_RGB)
    d.text((112, 48), "NaMiOffice", fill=INK_RGB)
    img.save(path, format="PNG")


def layout_by_name(prs: Presentation, name: str):
    for layout in prs.slide_layouts:
        if layout.name == name:
            return layout
    raise KeyError(f"không tìm thấy layout '{name}'")


def set_notes(slide, text: str) -> None:
    notes_slide = slide.notes_slide  # tạo notes page nếu chưa có
    notes_slide.notes_text_frame.text = text


def build() -> dict:
    ensure_logo_png(LOGO_PNG)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)  # 16:9

    # ---- Slide 1: Title slide (layout mặc định "Title Slide") ----
    title_layout = layout_by_name(prs, "Title Slide")
    s1 = prs.slides.add_slide(title_layout)
    s1.shapes.title.text = "NaMiSlides — Vertical Slice"
    sub = s1.placeholders[1]
    sub.text = "Bài trình chiếu kiểm thử round-trip PPTX (sinh bởi make_deck.py)"
    set_notes(
        s1,
        "Slide tiêu đề. Ghi chú diễn giả: giới thiệu mục tiêu vertical slice — "
        "mở, sửa một slide, lưu bản sao, so sánh với PowerPoint có giấy phép "
        "và NaMiSlides (xem docs/specs/namioffice-v2/02 mục C).",
    )

    # ---- Slide 2: Chart gốc (layout "Title and Content") ----
    content_layout = layout_by_name(prs, "Title and Content")
    s2 = prs.slides.add_slide(content_layout)
    s2.shapes.title.text = "Doanh thu theo khu vực (chart gốc, có data binding)"
    # Xoá placeholder nội dung trống (content) để không đè lên chart.
    for shp in list(s2.placeholders):
        if shp.placeholder_format.idx != 0:
            shp._element.getparent().remove(shp._element)

    chart_data = CategoryChartData()
    chart_data.categories = ["Bắc", "Trung", "Nam"]
    chart_data.add_series("Doanh thu (triệu đ)", (420, 310, 505))
    x, y, cx, cy = Cm(2), Cm(4), Cm(20), Cm(11)
    gframe = s2.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data)
    chart = gframe.chart
    chart.has_legend = False
    chart.chart_title.text_frame.text = "Doanh thu theo khu vực — số liệu minh hoạ"
    set_notes(
        s2,
        "Chart native (GraphicFrame có chart XML + embedded workbook dữ liệu), "
        "không phải ảnh chụp. Khi mở trong PowerPoint/Impress có giấy phép phải "
        "còn sửa được số liệu và style.",
    )

    # ---- Slide 3: Bảng (layout "Title Only") ----
    title_only_layout = layout_by_name(prs, "Title Only")
    s3 = prs.slides.add_slide(title_only_layout)
    s3.shapes.title.text = "Bảng tổng hợp hạng mục"
    rows, cols = 4, 3
    left, top, width, height = Cm(2), Cm(4), Cm(20), Cm(8)
    table_shape = s3.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    headers = ["Hạng mục", "Mức", "Trạng thái"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.text_frame.paragraphs[0].runs[0].font.bold = True
    data = [
        ("NaMiWriter F0", "Cơ bản", "Đang làm"),
        ("NaMiSheet F0", "Cơ bản", "Đang làm"),
        ("NaMiSlides F0", "Cơ bản", "Đang làm"),
    ]
    for r, row_vals in enumerate(data, start=1):
        for c, val in enumerate(row_vals):
            table.cell(r, c).text = val
    set_notes(
        s3,
        "Bảng native (graphicFrame/a:tbl), không phải ảnh chụp. Kiểm tra sau "
        "round-trip: số dòng/cột, nội dung, style bảng còn giữ nguyên.",
    )

    # ---- Slide 4: Ảnh + layout không mặc định "Picture with Caption" ----
    pic_layout = layout_by_name(prs, "Picture with Caption")
    s4 = prs.slides.add_slide(pic_layout)
    s4.shapes.title.text = "Logo minh hoạ (layout Picture with Caption)"
    # Tìm placeholder kiểu PICTURE (idx thường khác 0/1) để chèn ảnh đúng vùng.
    pic_placeholder = None
    for shp in s4.placeholders:
        if shp.placeholder_format.type is not None and "PICTURE" in str(shp.placeholder_format.type):
            pic_placeholder = shp
            break
    if pic_placeholder is not None:
        pic_placeholder.insert_picture(LOGO_PNG)
    else:
        s4.shapes.add_picture(LOGO_PNG, Cm(3), Cm(3), height=Cm(8))
    # Caption text placeholder (nếu có) — điền caption mô tả.
    for shp in s4.placeholders:
        if shp.has_text_frame and shp.placeholder_format.idx not in (0,) and shp is not pic_placeholder:
            if not shp.text_frame.text:
                shp.text_frame.text = "Logo NaMiOffice — ảnh minh hoạ chèn trong layout có caption."
    set_notes(
        s4,
        "Slide dùng layout KHÔNG mặc định (Picture with Caption) để kiểm tra "
        "round-trip giữ đúng master/layout, không bị rơi về Title and Content.",
    )

    os.makedirs(os.path.dirname(OUT_PPTX), exist_ok=True)
    prs.save(OUT_PPTX)
    return {"path": OUT_PPTX, "n_slides": len(list(prs.slides))}


def verify(stats: dict) -> None:
    prs = Presentation(stats["path"])
    slides = list(prs.slides)
    assert len(slides) == 4, f"số slide sai: {len(slides)}"
    layouts_used = {s.slide_layout.name for s in slides}
    assert "Title Slide" in layouts_used
    assert "Picture with Caption" in layouts_used, "thiếu slide layout không mặc định"
    n_charts = sum(1 for s in slides for shp in s.shapes if shp.has_chart)
    assert n_charts == 1, "thiếu chart native"
    n_tables = sum(1 for s in slides for shp in s.shapes if shp.has_table)
    assert n_tables == 1, "thiếu bảng"
    n_notes = sum(1 for s in slides if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())
    assert n_notes == 4, "thiếu speaker notes trên một số slide"
    def _is_picture(shp) -> bool:
        if "PICTURE" in str(shp.shape_type):
            return True
        if getattr(shp, "is_placeholder", False):
            pf = shp.placeholder_format
            return pf.type is not None and "PICTURE" in str(pf.type)
        return False

    n_pics = sum(1 for s in slides for shp in s.shapes if _is_picture(shp))
    assert n_pics >= 1, "thiếu ảnh"


if __name__ == "__main__":
    stats = build()
    verify(stats)
    size_kb = os.path.getsize(stats["path"]) // 1024
    print(f"wrote {stats['path']} ({size_kb} KB)")
    prs = Presentation(stats["path"])
    print(f"slides={len(list(prs.slides))}")
