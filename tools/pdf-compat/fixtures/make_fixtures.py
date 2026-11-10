#!/usr/bin/env python3
"""Sinh 13 fixture PDF (PDF-01..PDF-13) cho vertical-slice NaMiPDF.

Thực hiện bước "13 fixture và báo cáo" trong
docs/specs/namipdf-v18/05_PROMPT_CLAUDE_CODE.md, ánh xạ theo bảng "Test theo
công việc" ở docs/specs/namipdf-v18/04_KIEM_THU_PHAT_HANH.md (PDF-01..PDF-13).
Bảng kiểm thử gốc mô tả CÔNG VIỆC (vd "PDF-04 merge/split/reorder/rotate"),
không phải một corpus file cố định — file này sinh một CORPUS ĐẠI DIỆN tối
thiểu, mỗi fixture nhắm đúng một hàng trong bảng, để roundtrip/check_fixtures
có cái cụ thể mà chạy. Ánh xạ fixture -> hàng kiểm thử gốc được ghi trong
README.md cùng thư mục.

Dùng reportlab để dựng nội dung (text thật, không phải ảnh giả danh text) và
pikepdf để hậu xử lý cấu trúc PDF (mã hoá, AcroForm bổ sung, OutputIntent,
JavaScript/OpenAction, Sig dict, embedded file, corrupt). Mọi fixture TỰ SINH
tại chỗ, không chứa dữ liệu người dùng thật/định danh thật.

Chạy (idempotent, không cần mạng):
    python3 tools/pdf-compat/fixtures/make_fixtures.py
"""
from __future__ import annotations

import os
import sys

import pikepdf
from pikepdf import Array, Dictionary, Name, String
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "_assets")
os.makedirs(ASSETS, exist_ok=True)

# ---------------------------------------------------------------------------
# Font tiếng Việt: DejaVu Sans (qua matplotlib) phủ Latin Extended Additional
# (đủ các tổ hợp dấu tiếng Việt: ă â đ ê ô ơ ư + 5 thanh điệu). Không dùng
# font Helvetica/Times mặc định của reportlab vì không có glyph tiếng Việt
# -> sẽ in ra ô vuông/mất dấu, làm sai mục đích fixture #01/#12.
_DEJAVU_CANDIDATES = [
    "/home/node/.local/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_DEJAVU_BOLD_CANDIDATES = [
    "/home/node/.local/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _first_existing(paths):
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


VN_FONT_PATH = _first_existing(_DEJAVU_CANDIDATES)
VN_FONT_BOLD_PATH = _first_existing(_DEJAVU_BOLD_CANDIDATES)
if not VN_FONT_PATH:
    sys.exit(
        "KHONG TIM THAY font DejaVu Sans tren may nay (can glyph tieng Viet). "
        "Khong fallback sang Helvetica vi se sinh fixture SAI muc dich (mat dau)."
    )

pdfmetrics.registerFont(TTFont("VNFont", VN_FONT_PATH))
if VN_FONT_BOLD_PATH:
    pdfmetrics.registerFont(TTFont("VNFont-Bold", VN_FONT_BOLD_PATH))
else:
    pdfmetrics.registerFont(TTFont("VNFont-Bold", VN_FONT_PATH))

PAGE_W, PAGE_H = A4

# Câu tiếng Việt đủ dấu, dùng lặp lại trong nhiều fixture để check_fixtures.py
# có một "expected string" cố định đối chiếu (đủ 6 thanh điệu + ă â đ ê ô ơ ư).
VN_PANGRAM = "Chuyện kể rằng: đường phố Hà Nội mùa thu rất đẹp, gió nhẹ và se lạnh."
VN_DIACRITIC_SAMPLE = "ă â đ ê ô ơ ư — à á ả ã ạ — ầ ấ ẩ ẫ ậ — ẹ ẽ ẻ é è — ộ ồ ố ổ ỗ"


def _wrap_draw_text(c: canvas.Canvas, text: str, x: float, y: float, font: str,
                     size: float, max_width: float, leading: float) -> float:
    """Vẽ text có wrap đơn giản theo từ; trả về y sau khi vẽ xong dòng cuối."""
    words = text.split(" ")
    line = ""
    for w in words:
        trial = (line + " " + w).strip()
        if pdfmetrics.stringWidth(trial, font, size) > max_width and line:
            c.setFont(font, size)
            c.drawString(x, y, line)
            y -= leading
            line = w
        else:
            line = trial
    if line:
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= leading
    return y


# ---------------------------------------------------------------------------
# PDF-01: text PDF tiếng Việt, text thật chọn/copy được (không phải ảnh).
def make_01_text_vn(path: str) -> None:
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-01 Van ban tieng Viet")
    c.setFont("VNFont-Bold", 18)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-01 — Tài liệu văn bản tiếng Việt")
    y = PAGE_H - 40 * mm
    paragraphs = [
        VN_PANGRAM,
        VN_DIACRITIC_SAMPLE,
        "Đoạn thứ hai minh hoạ nguyên âm đôi: nước, người, muốn, được, tưởng, "
        "những, rượu, suối, chương, trường, thương, dương.",
        "Đoạn thứ ba kiểm tra phụ âm ghép: nghiêng, nghệ, ngoằn ngoèo, khuếch "
        "khoác, nghịch ngợm, quặn thắt, khuỷu tay.",
        "Văn bản này KHÔNG phải ảnh — toàn bộ nội dung là text layer thật, "
        "có thể bôi đen / sao chép / tìm kiếm bằng Ctrl+F trong viewer PDF.",
    ]
    for para in paragraphs:
        y = _wrap_draw_text(c, para, 20 * mm, y, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm)
        y -= 4 * mm
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-02: scanned-image-only (text rendered to raster, NO text layer) — cho OCR.
def make_02_scanned_image_only(path: str) -> None:
    img_w, img_h = 1240, 1754  # xấp xỉ A4 @ 150dpi
    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)
    font_big = ImageFont.truetype(VN_FONT_PATH, 34)
    font_small = ImageFont.truetype(VN_FONT_PATH, 24)
    draw.text((60, 60), "PDF-02 — Bản scan (ảnh) không có text layer", font=font_big, fill="black")
    lines = [
        VN_PANGRAM,
        VN_DIACRITIC_SAMPLE,
        "Đây là trang được RENDER RA ẢNH RASTER rồi nhúng vào PDF — không có",
        "text layer thật. Dùng để kiểm tra pipeline OCR (vd Tesseract vie)",
        "— pdftotext/Ctrl+F sẽ KHÔNG tìm thấy chữ nào trên trang này.",
    ]
    y = 160
    for ln in lines:
        draw.text((60, y), ln, font=font_small, fill="black")
        y += 44
    # Vẽ thêm vài đường kẻ/ô nhiễu để giống ảnh scan thật hơn (không ảnh hưởng OCR test).
    draw.rectangle([60, y + 20, img_w - 60, y + 24], fill="black")
    img_path = os.path.join(ASSETS, "scan_page.png")
    img.save(img_path)

    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-02 Scan anh khong co text layer")
    c.drawImage(img_path, 0, 0, width=PAGE_W, height=PAGE_H)
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-03: mixed text + image pages.
def make_03_mixed(path: str) -> None:
    # Ảnh minh hoạ nhỏ (biểu đồ cột giả lập), tái dùng cho trang ảnh.
    chart_path = os.path.join(ASSETS, "mixed_chart.png")
    if not os.path.isfile(chart_path):
        img = Image.new("RGB", (900, 600), "white")
        d = ImageDraw.Draw(img)
        bars = [(80, 420, 180, 560, "#2b6cb0"), (220, 300, 320, 560, "#2f855a"),
                (360, 180, 460, 560, "#c05621"), (500, 360, 600, 560, "#6b46c1")]
        for x0, y0, x1, y1, color in bars:
            d.rectangle([x0, y0, x1, y1], fill=color)
        font = ImageFont.truetype(VN_FONT_PATH, 26)
        d.text((80, 40), "Hình minh hoạ — biểu đồ giả lập (PDF-03)", font=font, fill="black")
        img.save(chart_path)

    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-03 Hon hop text va anh")
    # Trang 1: text thật.
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-03 — Trang 1: văn bản thuần")
    y = PAGE_H - 40 * mm
    y = _wrap_draw_text(c, VN_PANGRAM, 20 * mm, y, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm)
    y = _wrap_draw_text(c, "Trang kế tiếp chèn một ảnh raster, sau đó quay lại văn bản.",
                         20 * mm, y - 2 * mm, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm)
    c.showPage()
    # Trang 2: ảnh full trang.
    c.drawImage(chart_path, 20 * mm, PAGE_H - 160 * mm, width=PAGE_W - 40 * mm,
                height=(PAGE_W - 40 * mm) * 600 / 900, preserveAspectRatio=True)
    c.setFont("VNFont", 11)
    c.drawString(20 * mm, 30 * mm, "PDF-03 — Trang 2: ảnh raster (biểu đồ giả lập)")
    c.showPage()
    # Trang 3: text thật trở lại.
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-03 — Trang 3: văn bản thuần (tiếp)")
    y = PAGE_H - 40 * mm
    _wrap_draw_text(c, VN_DIACRITIC_SAMPLE, 20 * mm, y, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm)
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-04: multi-page (20+ trang) + bookmarks/outline.
def make_04_multipage_bookmarks(path: str) -> None:
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-04 Nhieu trang co bookmark")
    n_pages = 24
    # reportlab outline API: addOutlineEntry(title, key, level, closed)
    for i in range(1, n_pages + 1):
        key = f"page-{i}"
        c.bookmarkPage(key)
        level = 0 if i % 4 == 1 else 1
        if i % 4 == 1:
            c.addOutlineEntry(f"Chương {i // 4 + 1} — trang {i}", key, level=0, closed=False)
        else:
            c.addOutlineEntry(f"Mục {i}", key, level=1, closed=True)

        c.setFont("VNFont-Bold", 16)
        c.drawString(20 * mm, PAGE_H - 25 * mm, f"PDF-04 — Trang {i}/{n_pages}")
        c.setFont("VNFont", 12)
        _wrap_draw_text(
            c,
            f"Đây là trang số {i}. {VN_PANGRAM}",
            20 * mm, PAGE_H - 40 * mm, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm,
        )
        c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-05: AcroForm (text field + checkbox) — dùng reportlab acroform API.
def make_05_acroform(path: str) -> None:
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-05 AcroForm text field va checkbox")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-05 — Biểu mẫu AcroForm")
    c.setFont("VNFont", 12)
    c.drawString(20 * mm, PAGE_H - 45 * mm, "Họ và tên:")
    c.drawString(20 * mm, PAGE_H - 65 * mm, "Đồng ý nhận thông báo qua email:")

    form = c.acroForm
    form.textfield(
        name="ho_ten",
        tooltip="Họ và tên",
        x=60 * mm, y=PAGE_H - 50 * mm, width=90 * mm, height=8 * mm,
        borderStyle="inset", forceBorder=True, value="",
    )
    form.checkbox(
        name="dong_y_nhan_email",
        tooltip="Đồng ý nhận email",
        x=100 * mm, y=PAGE_H - 69 * mm, size=6 * mm,
        checked=False, borderStyle="solid",
    )
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-06: encrypted / password-protected (built via pikepdf on top of a base PDF).
def make_06_encrypted(path: str, tmp_plain: str) -> None:
    c = canvas.Canvas(tmp_plain, pagesize=A4)
    c.setTitle("PDF-06 File ma hoa (truoc khi encrypt)")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-06 — Nội dung được bảo vệ bằng mật khẩu")
    c.setFont("VNFont", 12)
    _wrap_draw_text(
        c,
        "Mở file này cần mật khẩu người dùng 'user-pass'. " + VN_PANGRAM,
        20 * mm, PAGE_H - 45 * mm, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm,
    )
    c.showPage()
    c.save()

    with pikepdf.open(tmp_plain) as pdf:
        pdf.save(
            path,
            encryption=pikepdf.Encryption(
                user="user-pass",
                owner="owner-pass",
                R=6,  # AES-256, PDF 2.0 / 1.7 ExtensionLevel 8
            ),
        )
    os.remove(tmp_plain)


# ---------------------------------------------------------------------------
# PDF-07: digitally-signed STUB — structural /Sig dict placeholder only.
# KHÔNG phải chữ ký số hợp lệ về mặt mật mã học (không có CMS/PKCS7 thật,
# không chứng thư, không hash nội dung). Xem README.md mục giới hạn.
def make_07_signature_stub(path: str, tmp_plain: str) -> None:
    c = canvas.Canvas(tmp_plain, pagesize=A4)
    c.setTitle("PDF-07 Chu ky so STUB (khong hop le ve mat ma)")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-07 — Có trường chữ ký (STUB cấu trúc)")
    c.setFont("VNFont", 12)
    _wrap_draw_text(
        c,
        "Fixture này chỉ có /Sig dict placeholder trong AcroForm để kiểm tra "
        "viewer NHẬN DIỆN được 'tài liệu có chữ ký' — KHÔNG phải chữ ký số "
        "hợp lệ (không PKCS7/CMS, không chứng thư X.509 thật). " + VN_PANGRAM,
        20 * mm, PAGE_H - 45 * mm, "VNFont", 11, PAGE_W - 40 * mm, 6 * mm,
    )
    c.showPage()
    c.save()

    with pikepdf.open(tmp_plain) as pdf:
        page = pdf.pages[0]
        # Sig dict tối giản — Contents rỗng (hex <>), SubFilter giả lập
        # adbe.pkcs7.detached nhưng KHÔNG chứa chữ ký mật mã thật.
        sig_dict = pdf.make_indirect(
            Dictionary(
                Type=Name("/Sig"),
                Filter=Name("/Adobe.PPKLite"),
                SubFilter=Name("/adbe.pkcs7.detached"),
                Name=String("NaMiPDF Fixture Stub — KHONG PHAI CHU KY HOP LE"),
                Reason=String("Cau truc stub cho vertical-slice QA, khong phai PAdES that"),
                M=String("D:20261110000000+07'00"),
                ByteRange=Array([0, 0, 0, 0]),  # placeholder — không khớp offset thật
                Contents=pikepdf.String(b""),
            )
        )
        widget = pdf.make_indirect(
            Dictionary(
                Type=Name("/Annot"),
                Subtype=Name("/Widget"),
                FT=Name("/Sig"),
                Rect=Array([20 * mm, 20 * mm, 90 * mm, 35 * mm]),
                V=sig_dict,
                T=String("ChuKyStub1"),
                P=page.obj,
                F=4,  # Print flag
            )
        )
        if "/Annots" in page.obj:
            page.obj.Annots.append(widget)
        else:
            page.obj.Annots = Array([widget])

        acroform = Dictionary(
            Fields=Array([widget]),
            SigFlags=3,  # SignaturesExist | AppendOnly
        )
        pdf.Root.AcroForm = acroform
        pdf.save(path)
    os.remove(tmp_plain)


# ---------------------------------------------------------------------------
# PDF-08: embedded file attachment.
def make_08_attachment(path: str, tmp_plain: str) -> None:
    c = canvas.Canvas(tmp_plain, pagesize=A4)
    c.setTitle("PDF-08 File co dinh kem")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-08 — Tài liệu có tệp đính kèm")
    c.setFont("VNFont", 12)
    _wrap_draw_text(
        c, "File .txt nhỏ được nhúng (embedded file attachment) trong PDF này. " + VN_PANGRAM,
        20 * mm, PAGE_H - 45 * mm, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm,
    )
    c.showPage()
    c.save()

    attachment_bytes = (
        "Đây là tệp đính kèm (ghi-chu.txt) nhúng trong PDF-08.\n"
        "Dùng để kiểm tra pipeline trích xuất/duyệt embedded file an toàn "
        "(không tự thực thi).\n" + VN_DIACRITIC_SAMPLE + "\n"
    ).encode("utf-8")

    with pikepdf.open(tmp_plain) as pdf:
        # pikepdf API thực tế: pdf.attachments là mapping-like (pikepdf >=2.9),
        # nhận một AttachedFileSpec dựng từ bytes.
        fs = pikepdf.AttachedFileSpec(
            pdf, attachment_bytes,
            description="Ghi chú đính kèm — fixture PDF-08",
            filename="ghi-chu.txt",
            mime_type="text/plain",
        )
        pdf.attachments["ghi-chu.txt"] = fs
        pdf.save(path)
    os.remove(tmp_plain)


# ---------------------------------------------------------------------------
# PDF-09: /JavaScript + /OpenAction — malicious-pattern STUB, INERT content.
# JS payload chỉ là chuỗi vô hại (không network/exec thật) — dùng để kiểm tra
# parser/viewer có CHẶN auto-run JS hay không (theo yêu cầu bảo mật ở
# 05_PROMPT_CLAUDE_CODE.md: "cấm auto JavaScript, attachment execution").
def make_09_js_openaction(path: str, tmp_plain: str) -> None:
    c = canvas.Canvas(tmp_plain, pagesize=A4)
    c.setTitle("PDF-09 JavaScript OpenAction STUB (inert)")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-09 — /OpenAction + /JavaScript (vô hại, chỉ để test chặn)")
    c.setFont("VNFont", 12)
    _wrap_draw_text(
        c,
        "Fixture này có /OpenAction trỏ tới một action /JavaScript VÔ HẠI "
        "(chỉ là chuỗi app.alert giả lập, không mạng, không thực thi lệnh hệ "
        "thống). Mục đích: xác nhận NaMiPDF/viewer KHÔNG tự chạy JS khi mở "
        "file. " + VN_PANGRAM,
        20 * mm, PAGE_H - 45 * mm, "VNFont", 11, PAGE_W - 40 * mm, 6 * mm,
    )
    c.showPage()
    c.save()

    with pikepdf.open(tmp_plain) as pdf:
        # Payload JS vô hại — chỉ gọi app.alert với chuỗi tĩnh, không I/O,
        # không eval động, không fetch mạng (PDF JS không có network API
        # chuẩn, nhưng vẫn giữ payload tối giản nhất có thể để tránh hiểu lầm).
        js_code = (
            "// STUB VO HAI - chi danh dau fixture, khong thuc thi gi nguy hiem\n"
            "if (typeof app !== 'undefined' && app.alert) { "
            "app.alert('NaMiPDF fixture PDF-09: JS stub, khong duoc tu dong chay.'); }"
        )
        js_action = pdf.make_indirect(
            Dictionary(S=Name("/JavaScript"), JS=String(js_code))
        )
        pdf.Root.OpenAction = js_action
        # Cũng khai báo trong /Names /JavaScript (vị trí JS "thường trú" khác
        # nhau theo spec PDF — khai cả hai để test coverage rộng hơn).
        names_tree = Dictionary(
            Names=Array([String("StubScript"), pdf.make_indirect(
                Dictionary(S=Name("/JavaScript"), JS=String(js_code))
            )])
        )
        if "/Names" in pdf.Root:
            pdf.Root.Names.JavaScript = names_tree
        else:
            pdf.Root.Names = Dictionary(JavaScript=names_tree)
        pdf.save(path)
    os.remove(tmp_plain)


# ---------------------------------------------------------------------------
# PDF-10: PDF/A-ish — OutputIntent (sRGB ICC) + XMP metadata declaring PDF/A.
# Lưu ý trung thực: đây là PDF/A-DẠNG (mang OutputIntent+XMP conformance tag)
# chứ KHÔNG qua veraPDF validation thật — xem README.md.
def make_10_pdfa_ish(path: str, tmp_plain: str) -> None:
    c = canvas.Canvas(tmp_plain, pagesize=A4)
    c.setTitle("PDF-10 PDF-A-ish voi OutputIntent va XMP")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-10 — PDF/A-ish (OutputIntent + XMP, chưa qua veraPDF)")
    c.setFont("VNFont", 12)
    _wrap_draw_text(
        c, "Fixture khai báo OutputIntent sRGB và XMP conformance PDF/A-1b, "
           "nhưng CHƯA được xác nhận bằng validator veraPDF thật — chỉ là "
           "cấu trúc 'giống PDF/A' để tập dượt pipeline. " + VN_PANGRAM,
        20 * mm, PAGE_H - 45 * mm, "VNFont", 11, PAGE_W - 40 * mm, 6 * mm,
    )
    c.showPage()
    c.save()

    xmp = """<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
   <pdfaid:part>1</pdfaid:part>
   <pdfaid:conformance>B</pdfaid:conformance>
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">PDF-10 PDF/A-ish fixture</rdf:li></rdf:Alt></dc:title>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>""".encode()

    # ICC profile sRGB tối giản: dùng profile nhúng sẵn trong Pillow nếu có,
    # nếu không thì ghi một blob giả lập có header ICC hợp lệ tối thiểu để
    # OutputIntent có N (số kênh màu) đúng — KHÔNG claim đây là ICC chuẩn đủ
    # để in màu chính xác, chỉ đủ cấu trúc để validator cấu trúc không văng lỗi.
    icc_path = os.path.join(ASSETS, "srgb_stub.icc")
    if not os.path.isfile(icc_path):
        try:
            from PIL import ImageCms
            srgb = ImageCms.createProfile("sRGB")
            ImageCms.ImageCmsProfile(srgb).tobytes()
            with open(icc_path, "wb") as f:
                f.write(ImageCms.ImageCmsProfile(srgb).tobytes())
        except Exception:
            # Fallback tối giản: không có ImageCms -> ghi placeholder có đánh
            # dấu rõ "KHONG PHAI ICC CHUAN".
            with open(icc_path, "wb") as f:
                f.write(b"NAMIPDF-FIXTURE-NOT-A-REAL-ICC-PROFILE-PLACEHOLDER")

    with pikepdf.open(tmp_plain) as pdf:
        icc_stream = pikepdf.Stream(pdf, open(icc_path, "rb").read())
        icc_stream.N = 3
        output_intent = Dictionary(
            Type=Name("/OutputIntent"),
            S=Name("/GTS_PDFA1"),
            OutputConditionIdentifier=String("sRGB IEC61966-2.1"),
            Info=String("sRGB IEC61966-2.1 (stub, chua qua veraPDF)"),
            DestOutputProfile=icc_stream,
        )
        pdf.Root.OutputIntents = Array([output_intent])
        metadata_stream = pikepdf.Stream(pdf, xmp)
        metadata_stream.Type = Name("/Metadata")
        metadata_stream.Subtype = Name("/XML")
        pdf.Root.Metadata = metadata_stream
        pdf.save(path)
    os.remove(tmp_plain)


# ---------------------------------------------------------------------------
# PDF-11: external /URI link.
def make_11_uri_link(path: str) -> None:
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-11 Lien ket URI ra ngoai")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-11 — Liên kết ra ngoài (/URI)")
    c.setFont("VNFont", 12)
    link_text = "Xem tài liệu PDF Association tại pdfa.org (nhấn vào đây)"
    y = PAGE_H - 45 * mm
    c.drawString(20 * mm, y, link_text)
    text_width = pdfmetrics.stringWidth(link_text, "VNFont", 12)
    c.linkURL(
        "https://pdfa.org/pdf-standards/",
        (20 * mm, y - 2 * mm, 20 * mm + text_width, y + 10),
        relative=0,
        thickness=0,
    )
    c.setFillColorRGB(0.1, 0.1, 0.6)
    c.drawString(20 * mm, y, link_text)
    c.setFillColorRGB(0, 0, 0)
    _wrap_draw_text(
        c, "Dùng để kiểm tra viewer xử lý link ngoài an toàn (cảnh báo trước "
           "khi mở trình duyệt, không tự fetch mạng khi chỉ mở file). " + VN_PANGRAM,
        20 * mm, y - 15 * mm, "VNFont", 11, PAGE_W - 40 * mm, 6 * mm,
    )
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-12: Vietnamese-heavy, dense diacritics — copy/search test.
def make_12_vn_heavy(path: str) -> None:
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("PDF-12 Tieng Viet day du dau")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-12 — Văn bản tiếng Việt dày đặc dấu")
    y = PAGE_H - 40 * mm
    dense_lines = [
        "Nguyễn Thị Thanh Hường sinh ngày 05 tháng 09 năm 2008 tại Thừa Thiên Huế.",
        "Các nguyên âm có dấu: à ầ ấ ẩ ẫ ậ ă ằ ắ ẳ ẵ ặ â ầ ấ ẩ ẫ ậ.",
        "Các nguyên âm có dấu: è ề ế ể ễ ệ ê ề ế ể ễ ệ.",
        "Các nguyên âm có dấu: ì í ỉ ĩ ị.",
        "Các nguyên âm có dấu: ò ồ ố ổ ỗ ộ ô ồ ố ổ ỗ ộ ơ ờ ớ ở ỡ ợ.",
        "Các nguyên âm có dấu: ù ù ú ủ ũ ụ ư ừ ứ ử ữ ự.",
        "Phụ âm đặc trưng: đ, nh, ng, ngh, ph, th, tr, ch, kh, gi, qu.",
        "Câu đủ nghĩa: Khi sương sớm phủ kín cánh đồng, lũ trẻ rủ nhau ra "
        "ruộng bắt châu chấu, tiếng cười giòn tan vang khắp xóm làng.",
        "Thành ngữ: Ăn quả nhớ kẻ trồng cây; Uống nước nhớ nguồn; Có công "
        "mài sắt, có ngày nên kim.",
    ]
    for line in dense_lines:
        y = _wrap_draw_text(c, line, 20 * mm, y, "VNFont", 12, PAGE_W - 40 * mm, 6.5 * mm)
        y -= 3 * mm
    c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# PDF-13: intentionally corrupt / truncated — for parser-robustness testing.
def make_13_corrupt(path: str, tmp_plain: str) -> None:
    c = canvas.Canvas(tmp_plain, pagesize=A4)
    c.setTitle("PDF-13 File se bi lam hong truncate")
    c.setFont("VNFont-Bold", 16)
    c.drawString(20 * mm, PAGE_H - 25 * mm, "PDF-13 — (nội dung này sẽ bị cắt cụt)")
    c.setFont("VNFont", 12)
    _wrap_draw_text(c, VN_PANGRAM, 20 * mm, PAGE_H - 45 * mm, "VNFont", 12, PAGE_W - 40 * mm, 6 * mm)
    c.showPage()
    c.save()

    with open(tmp_plain, "rb") as f:
        data = f.read()
    # Cắt cụt ở ~55% độ dài -> mất xref/trailer, mô phỏng "mất điện khi save"
    # hoặc file tải dở (theo PDF-13 trong bảng kiểm thử gốc: "mất điện/hết
    # dung lượng/xung đột khi Save"). Đây là lỗi hỏng CÓ CHỦ Ý để kiểm tra
    # robustness của parser (không được crash, phải detect lỗi rõ ràng).
    cut_at = int(len(data) * 0.55)
    truncated = data[:cut_at]
    with open(path, "wb") as f:
        f.write(truncated)
    os.remove(tmp_plain)


# ---------------------------------------------------------------------------
def main() -> None:
    out = {}

    p01 = os.path.join(HERE, "01_text_vn.pdf")
    make_01_text_vn(p01)
    out["PDF-01"] = p01

    p02 = os.path.join(HERE, "02_scanned_image_only.pdf")
    make_02_scanned_image_only(p02)
    out["PDF-02"] = p02

    p03 = os.path.join(HERE, "03_mixed_text_image.pdf")
    make_03_mixed(p03)
    out["PDF-03"] = p03

    p04 = os.path.join(HERE, "04_multipage_bookmarks.pdf")
    make_04_multipage_bookmarks(p04)
    out["PDF-04"] = p04

    p05 = os.path.join(HERE, "05_acroform.pdf")
    make_05_acroform(p05)
    out["PDF-05"] = p05

    p06 = os.path.join(HERE, "06_encrypted.pdf")
    make_06_encrypted(p06, os.path.join(HERE, "_tmp_06_plain.pdf"))
    out["PDF-06"] = p06

    p07 = os.path.join(HERE, "07_signature_stub.pdf")
    make_07_signature_stub(p07, os.path.join(HERE, "_tmp_07_plain.pdf"))
    out["PDF-07"] = p07

    p08 = os.path.join(HERE, "08_attachment.pdf")
    make_08_attachment(p08, os.path.join(HERE, "_tmp_08_plain.pdf"))
    out["PDF-08"] = p08

    p09 = os.path.join(HERE, "09_js_openaction.pdf")
    make_09_js_openaction(p09, os.path.join(HERE, "_tmp_09_plain.pdf"))
    out["PDF-09"] = p09

    p10 = os.path.join(HERE, "10_pdfa_ish.pdf")
    make_10_pdfa_ish(p10, os.path.join(HERE, "_tmp_10_plain.pdf"))
    out["PDF-10"] = p10

    p11 = os.path.join(HERE, "11_uri_link.pdf")
    make_11_uri_link(p11)
    out["PDF-11"] = p11

    p12 = os.path.join(HERE, "12_vn_heavy_diacritics.pdf")
    make_12_vn_heavy(p12)
    out["PDF-12"] = p12

    p13 = os.path.join(HERE, "13_corrupt_truncated.pdf")
    make_13_corrupt(p13, os.path.join(HERE, "_tmp_13_plain.pdf"))
    out["PDF-13"] = p13

    print("Đã sinh 13 fixture PDF-01..PDF-13 tại", HERE)
    for key in sorted(out):
        fp = out[key]
        size = os.path.getsize(fp)
        print(f"  {key}: {os.path.basename(fp)} ({size:,} bytes)")


if __name__ == "__main__":
    main()
