#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh fixture LongDoc.docx cho vertical-slice NaMiWriter (NaMiOffice v2).

Mục tiêu (xem docs/specs/namioffice-v2/02_WRITER_SHEET_SLIDES.md mục A và
05_PROMPT_CLAUDE_CODE.md bước 3): một DOCX dài, nhiều heading (TOC-able),
bảng có gộp ô + dòng tiêu đề, ảnh chèn trong dòng, comment, footer số trang,
hyperlink — để làm input cho pipeline round-trip (mở → sửa nhỏ → lưu → so
sánh) chạy trong CI/QEMU có LibreOffice/Microsoft Office.

TRUNG THỰC về giới hạn của python-docx (không giả vờ đạt):
  - Track changes (w:ins/w:del, nhiều tác giả, accept/reject) KHÔNG có API
    ghi trong python-docx 1.2.0. File này KHÔNG chứa track changes thật.
    Xem README.md trong thư mục cha để biết chi tiết + hướng khắc phục.
  - python-docx 1.2.0 CÓ hỗ trợ comment thật (Document.add_comment gắn vào
    một vùng run) — khác với ghi chú ban đầu trong đặc tả rằng comment "rất
    hạn chế"; đã kiểm tra trực tiếp và dùng API thật thay vì giả bằng đoạn
    văn thường.
  - Footnote: python-docx 1.2.0 không có API bậc cao để thêm footnote mới;
    để trung thực, mục này dùng chú thích cuối trang kiểu thủ công (đánh số
    + đoạn văn ở cuối tài liệu) và NÊU RÕ đây không phải footnote OOXML thật
    (w:footnoteReference) — xem README.

Chạy:  python3 tools/office-compat/fixtures/make_doc.py
Đầu ra: tools/office-compat/fixtures/LongDoc.docx (+ _assets/logo.png tạm)
"""
from __future__ import annotations

import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DOCX = os.path.join(HERE, "LongDoc.docx")
ASSETS_DIR = os.path.join(HERE, "_assets")
LOGO_PNG = os.path.join(ASSETS_DIR, "logo.png")

SON = RGBColor(0xC9, 0x36, 0x43)   # đỏ son — thương hiệu NaMiOS
INK = RGBColor(0x18, 0x2E, 0x3B)


def make_logo_png(path: str) -> None:
    """Sinh một PNG nhỏ (không cần mạng) để làm ảnh chèn trong dòng."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (240, 120), (245, 242, 235))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 235, 115], outline=(201, 54, 67), width=4)
    d.ellipse([20, 20, 100, 100], fill=(201, 54, 67))
    d.text((112, 48), "NaMiOffice", fill=(24, 46, 59))
    img.save(path, format="PNG")


def add_hyperlink(paragraph, url: str, text: str):
    """Thêm hyperlink thật (w:hyperlink + r:id quan hệ) — python-docx không có
    helper bậc cao cho việc này nên thao tác trực tiếp trên XML part, đúng
    cách Word ghi hyperlink (để round-trip giữ được, không phải text giả)."""
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = paragraph._p.makeelement(qn("w:hyperlink"), {qn("r:id"): r_id})
    new_run = paragraph._p.makeelement(qn("w:r"), {})
    rpr = paragraph._p.makeelement(qn("w:rPr"), {})
    color = paragraph._p.makeelement(qn("w:color"), {qn("w:val"): "0563C1"})
    underline = paragraph._p.makeelement(qn("w:u"), {qn("w:val"): "single"})
    rpr.append(color)
    rpr.append(underline)
    new_run.append(rpr)
    t = paragraph._p.makeelement(qn("w:t"), {})
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink


def add_page_number_footer(section) -> None:
    """Footer có số trang dạng field PAGE / NUMPAGES — ghi XML field trực
    tiếp vì python-docx không có helper field bậc cao."""
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = ""
    run = p.add_run("Trang ")

    def _field(instr: str):
        fld_begin = p._p.makeelement(qn("w:r"), {})
        b = p._p.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
        fld_begin.append(b)

        fld_instr = p._p.makeelement(qn("w:r"), {})
        itext = p._p.makeelement(qn("w:instrText"), {qn("xml:space"): "preserve"})
        itext.text = instr
        fld_instr.append(itext)

        fld_sep = p._p.makeelement(qn("w:r"), {})
        s = p._p.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "separate"})
        fld_sep.append(s)

        fld_end = p._p.makeelement(qn("w:r"), {})
        e = p._p.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
        fld_end.append(e)

        for el in (fld_begin, fld_instr, fld_sep, fld_end):
            p._p.append(el)

    _field("PAGE")
    sep_run = p.add_run(" / ")
    _field("NUMPAGES")
    run.font.size = Pt(9)
    sep_run.font.size = Pt(9)


def build() -> dict:
    make_logo_png(LOGO_PNG)
    doc = Document()

    # ---- Section/page setup cơ bản (A4) ----
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    add_page_number_footer(section)

    # ---- Trang 1: tiêu đề + heading styles (TOC-able) ----
    title = doc.add_heading("Tài liệu dài — NaMiWriter Vertical Slice", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub = doc.add_paragraph("Fixture kiểm thử round-trip DOCX — sinh bởi make_doc.py")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True
    sub.runs[0].font.color.rgb = INK

    doc.add_paragraph(
        "Tài liệu này mô phỏng một văn bản hành chính/báo cáo nhiều trang, dùng để "
        "đối chiếu nội dung và cấu trúc sau khi mở/sửa/lưu bằng LibreOffice Writer "
        "và Microsoft Word có giấy phép (xem docs/specs/namioffice-v2/04)."
    )

    # Nhiều heading cấp 1/2/3 để TOC có mục lục thật + đủ dài nhiều trang.
    sections_plan = [
        ("1. Giới thiệu", [
            "Mục tiêu vertical slice là chứng minh pipeline mở an toàn, nhận diện "
            "tính năng rủi ro, chỉnh sửa, lưu bản sao và so sánh kết quả.",
            "Dữ liệu trong tài liệu là dữ liệu thử, không chứa thông tin cá nhân thật.",
        ]),
        ("1.1. Phạm vi", [
            "Phạm vi F0 gồm: style đoạn/ký tự, bảng/ảnh, header/footer, số trang, "
            "hyperlink, PDF có bookmark.",
        ]),
        ("2. Nội dung mẫu", [
            "Đoạn văn này lặp lại nhiều lần để tài liệu đủ dài nhiều trang, kiểm "
            "tra ngắt trang tự động và tiêu đề lặp lại của bảng khi bảng tràn trang. "
            * 1,
        ] * 3),
        ("2.1. Bảng dữ liệu", [
            "Bảng dưới đây có dòng tiêu đề lặp lại và một ô gộp ngang để kiểm tra "
            "round-trip không rớt cấu trúc merge.",
        ]),
        ("2.2. Hình ảnh", [
            "Ảnh logo dưới đây được chèn trong dòng (inline) kèm alt text.",
        ]),
        ("3. Liên kết và chú thích", [
            "Phần này có một hyperlink ra ngoài và một comment gắn vào một vùng văn bản.",
        ]),
        ("4. Kết luận", [
            "Track changes KHÔNG được tạo trong fixture này vì python-docx không có "
            "API ghi w:ins/w:del — xem README.md để biết giới hạn và hướng khắc phục.",
        ]),
    ]

    for heading, paras in sections_plan:
        # heading dạng "1. ..." -> level1 (1 dấu chấm), "1.1. ..." -> level2 (2 dấu chấm).
        dots = heading.split(" ")[0].count(".")
        level = 1 if dots <= 1 else 2
        doc.add_heading(heading, level=level)
        for para_text in paras:
            doc.add_paragraph(para_text)
        if heading.startswith("2. Nội dung mẫu"):
            # Thêm vài đoạn + page break để chắc chắn tài liệu nhiều trang thật.
            for i in range(6):
                doc.add_paragraph(
                    f"Đoạn lấp đầy số {i + 1}: Lorem ipsum NaMiOffice dolor sit amet, "
                    "consectetur adipiscing elit. Nội dung tiếng Việt có dấu: "
                    "Đây là đoạn kiểm tra Unicode không mất dấu — ă â ê ô ơ ư đ."
                )
            doc.add_page_break()

    # ---- Bảng có merge + header lặp ----
    table = doc.add_table(rows=4, cols=3)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Đánh dấu dòng tiêu đề lặp lại khi bảng tràn trang (w:tblHeader).
    tr = table.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    tbl_header = trPr.makeelement(qn("w:tblHeader"), {qn("w:val"): "true"})
    trPr.append(tbl_header)

    hdr = table.rows[0].cells
    hdr[0].text = "Hạng mục"
    hdr[1].text = "Số lượng"
    hdr[2].text = "Ghi chú"

    data_rows = [
        ("Bản cài NaMiWriter", "1", "F0"),
        ("Bản cài NaMiSheet", "1", "F0"),
        ("Bản cài NaMiSlides", "1", "F0"),
    ]
    for i, (a, b, c) in enumerate(data_rows, start=1):
        row = table.rows[i].cells
        row[0].text = a
        row[1].text = b
        row[2].text = c

    # Gộp ô ngang ở dòng cuối để kiểm tra round-trip merge.
    merged = table.rows[3].cells[0].merge(table.rows[3].cells[2])
    merged.text = "Dòng gộp 3 cột — kiểm tra round-trip không rớt cấu trúc merge"

    doc.add_paragraph("")

    # ---- Ảnh inline + alt text ----
    pic_para = doc.add_paragraph()
    pic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = pic_para.add_run()
    run.add_picture(LOGO_PNG, width=Cm(5))
    # Alt text (docPr/@descr) — python-docx không có API bậc cao, set trực tiếp.
    inline_shape = doc.inline_shapes[-1]
    doc_pr = inline_shape._inline.find(qn("wp:docPr"))
    doc_pr.set("descr", "Logo NaMiOffice minh hoạ — ảnh chèn trong dòng (inline)")
    doc_pr.set("name", "LogoNaMiOffice")
    cap = doc.add_paragraph("Hình 1 — Logo minh hoạ (caption)")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.runs[0].italic = True
    cap.runs[0].font.size = Pt(9)

    # ---- Hyperlink ----
    link_para = doc.add_paragraph("Tham khảo đặc tả tại ")
    add_hyperlink(link_para, "https://www.libreoffice.org/licenses/", "LibreOffice licensing")
    link_para.add_run(" (mở trong trình duyệt khi click).")

    # ---- Comment thật (Document.add_comment) ----
    comment_target_para = doc.add_paragraph(
        "Đoạn này có một BÌNH LUẬN (comment) thật gắn vào cụm từ "
        "\"vertical slice\" để kiểm tra round-trip phần w:comments."
    )
    # Tìm run chứa cụm "vertical slice" bằng cách tách run riêng cho nó.
    comment_target_para.clear()
    r1 = comment_target_para.add_run("Đoạn này có một bình luận thật gắn vào cụm ")
    r_target = comment_target_para.add_run("\"vertical slice\"")
    r3 = comment_target_para.add_run(" để kiểm tra round-trip phần w:comments (comments.xml).")
    doc.add_comment(
        runs=r_target,
        text="Nhắc QA: kiểm tra comment này còn nguyên sau khi LibreOffice/Word lưu lại.",
        author="NaMiOS QA",
        initials="QA",
    )

    # ---- "Footnote" thủ công (giới hạn trung thực — xem docstring + README) ----
    fn_para = doc.add_paragraph()
    fn_para.add_run("Đây là câu có chú thích cuối trang kiểu thủ công").font.superscript = False
    fn_marker = fn_para.add_run("¹")
    fn_marker.font.superscript = True
    doc.add_paragraph("").paragraph_format.space_after = Pt(2)
    fn_body = doc.add_paragraph()
    fn_body.add_run("¹ ").font.superscript = True
    fn_body.add_run(
        "Đây KHÔNG phải footnote OOXML thật (không có w:footnoteReference/footnotes.xml) — "
        "python-docx 1.2.0 không có API bậc cao để thêm footnote thật. Ghi chú trung thực "
        "trong README.md."
    ).font.size = Pt(9)
    fn_body.runs[1].italic = True

    doc.save(OUT_DOCX)
    return {
        "path": OUT_DOCX,
        "paragraphs": len(doc.paragraphs),
        "tables": len(doc.tables),
        "inline_shapes": len(doc.inline_shapes),
    }


def verify(stats: dict) -> None:
    """Mở lại bằng python-docx để xác nhận các đối tượng chính còn nguyên."""
    doc = Document(stats["path"])
    assert len(doc.tables) == 1, "thiếu bảng"
    tbl = doc.tables[0]
    assert len(tbl.rows) == 4 and len(tbl.columns) == 3, "sai kích thước bảng"
    assert len(doc.inline_shapes) >= 1, "thiếu ảnh inline"
    assert len(doc.comments) >= 1, "thiếu comment"
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert len(headings) >= 5, "thiếu heading để TOC"
    has_hyperlink = len(doc.part._element.xpath("//w:hyperlink")) > 0
    assert has_hyperlink, "thiếu hyperlink"


if __name__ == "__main__":
    stats = build()
    verify(stats)
    size_kb = os.path.getsize(stats["path"]) // 1024
    print(f"wrote {stats['path']} ({size_kb} KB)")
    print(f"paragraphs={stats['paragraphs']} tables={stats['tables']} "
          f"inline_shapes={stats['inline_shapes']}")
