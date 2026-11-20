#!/usr/bin/env python3
"""Sinh tài liệu PDF "NaMi — Giới thiệu cho đợt dùng thật" (2–3 trang) để Cuong
viết 20 user-story. Cùng nội dung với bản DOCX (make_gioi_thieu_dung_thu.py),
chỉ khác định dạng đầu ra là PDF (reportlab + font Việt DejaVu).

Nhấn mạnh Trợ lý AI + Wine; TRUNG THỰC (bản alpha, Wine tuỳ app). Đối tượng
pilot: ~10 nhân viên = văn phòng + dev (mô hình công ty IT).
Tái lập: python3 docs/pilot/make_gioi_thieu_dung_thu_pdf.py
"""
from __future__ import annotations

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_REG = os.path.join(ROOT, "branding/fonts/DejaVuSans.ttf")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")

NAVY = HexColor("#092D4F")
GOLD = HexColor("#B5802E")
INK = HexColor("#1A1A1A")

pdfmetrics.registerFont(TTFont("DejaVu", FONT_REG))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", FONT_BOLD))
pdfmetrics.registerFontFamily(
    "DejaVu", normal="DejaVu", bold="DejaVu-Bold",
    italic="DejaVu", boldItalic="DejaVu-Bold",
)

ss = getSampleStyleSheet()
BODY = ParagraphStyle(
    "body", parent=ss["Normal"], fontName="DejaVu", fontSize=10,
    leading=13.5, textColor=INK, alignment=TA_LEFT, spaceAfter=3,
)
TITLE = ParagraphStyle(
    "title", parent=BODY, fontName="DejaVu-Bold", fontSize=18,
    leading=22, textColor=NAVY, spaceAfter=2,
)
SUBTITLE = ParagraphStyle(
    "subtitle", parent=BODY, fontSize=9, textColor=GOLD, spaceAfter=8,
)
H1 = ParagraphStyle(
    "h1", parent=BODY, fontName="DejaVu-Bold", fontSize=12.5,
    leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=3,
)
BULLET = ParagraphStyle(
    "bullet", parent=BODY, leftIndent=0, spaceAfter=2,
)

story = []


def P(text, style=BODY):
    story.append(Paragraph(text, style))


def H(text):
    story.append(Paragraph(text, H1))


def bullets(items):
    li = []
    for it in items:
        li.append(ListItem(Paragraph(it, BULLET), leftIndent=12,
                            value="•", bulletColor=NAVY))
    story.append(ListFlowable(li, bulletType="bullet", start="•",
                              leftIndent=12, bulletFontName="DejaVu",
                              bulletFontSize=9, spaceAfter=3))


def us(text):
    """Một user-story gợi ý: nhãn vàng + nội dung."""
    return ('<font name="DejaVu-Bold" color="#B5802E">User-story: </font>'
            '<i>' + text + '</i>')


# ---- Tiêu đề ----
P("NaMi — Giới thiệu nhanh cho đợt dùng thật", TITLE)
P("Bản alpha · 20/11/2026 · Tài liệu để viết 20 user-story · "
  "Pilot ~10 nhân viên (văn phòng + lập trình viên)", SUBTITLE)
P("Mục đích tài liệu: giúp anh nắm NaMi làm được gì để viết user-story sát "
  "thực tế. Hai phần KHÁC BIỆT NHẤT của NaMi là Trợ lý AI và Wine (chạy phần "
  "mềm Windows) — được nói kỹ ở mục 3 và 4. Tài liệu viết trung thực: ghi đúng "
  "cái chạy được và cái còn giới hạn, để đợt dùng thật đặt kỳ vọng đúng.")

# ---- 1 ----
H("1. NaMi là gì — cho ai")
bullets([
    "Hệ điều hành MIỄN PHÍ cho người Việt, nền Debian 13 + KDE Plasma 6; giao "
    "diện và thao tác làm theo kiểu Windows để người quen Windows dùng được ngay.",
    "Mặc định tiếng Việt, giờ Việt Nam, gõ tiếng Việt sẵn; có sẵn bộ Office, "
    "trình duyệt, app đọc PDF, nhạc/phim, nén/giải nén…",
    "Đợt này: cho ~10 nhân viên (cả văn phòng lẫn dev) dùng THẬT hằng ngày để "
    "tìm ra chỗ được và chưa được.",
])

# ---- 2 ----
H("2. Trải nghiệm hằng ngày (giống Windows)")
bullets([
    "Màn hình nền có nút Start góc trái dưới, thanh tác vụ, các icon quen thuộc "
    "(Máy tính của tôi / Tài liệu / Thùng rác); F5 làm mới desktop.",
    "Quản lý tệp theo ổ đĩa (C/D…), kéo-thả, copy/paste như Windows.",
    "Mở ứng dụng từ menu Start hoặc thanh tác vụ; tắt máy/khởi động lại/đăng "
    "xuất ở màn Rời phiên tiếng Việt.",
])
bullets([us("Là nhân viên văn phòng chưa từng dùng Linux, tôi muốn mở máy lên "
            "làm việc được ngay mà không phải học lại thao tác.")])

# ---- 3: TRỢ LÝ AI ----
H("3. ★ Trợ lý AI — điểm khác biệt lớn nhất")
P("Hỏi bằng tiếng Việt, Trợ lý trả lời VÀ đưa ra NÚT BẤM để làm luôn — không "
  "phải lên Google mò. Ba nhóm việc:")
bullets([
    "CÀI PHẦN MỀM: gõ “cài giúp tôi Zoom / Chrome / VS Code / bộ công cụ lập "
    "trình” → Trợ lý cài 1 chạm từ nguồn chính chủ đã kiểm duyệt (không tự bịa "
    "link). Phần mềm không có bản Linux → nói thật + gợi bản thay thế/web.",
    "SỬA LỖI &amp; THIẾT BỊ: “máy in Canon G2010 không nhận driver”, “wifi không "
    "vào được” → Trợ lý chỉ đúng driver/công cụ để xử lý.",
    "HƯỚNG DẪN CLICK-ĐƯỢC: “tôi muốn đổi giao diện màn hình / độ phân giải / mật "
    "khẩu / ngôn ngữ / âm thanh…” → Trợ lý đưa hướng dẫn ngắn + 1 NÚT, bấm vào "
    "mở thẳng đúng trang Cài đặt để làm ngay (phủ ~28 việc hay dùng).",
    "Nguyên tắc an toàn: Trợ lý CHỈ dùng kho lệnh/link đã kiểm duyệt, tuyệt đối "
    "không tự nghĩ ra link lạ/lệnh lạ → không dẫn người dùng tải nhầm phần mềm "
    "độc.",
])
bullets([
    us("Là nhân viên văn phòng, tôi muốn gõ “đổi hình nền” và bấm 1 nút là mở "
       "đúng chỗ đổi, không phải đi tìm trong menu."),
    us("Là dev, tôi muốn gõ “bộ công cụ lập trình” để cài VS Code + Node + "
       "Python + Docker trong một lần."),
])

# ---- 4: WINE ----
H("4. ★ Wine — chạy phần mềm Windows (nói thật)")
P("NaMi có lớp Wine để mở phần mềm Windows (.exe) ngay trên hệ; app nền "
  "Microsoft .NET có sẵn Wine-Mono và tự chuẩn bị .NET khi cần.")
P('<font name="DejaVu-Bold" color="#B5802E">Sự thật quan trọng (đừng đặt kỳ '
  'vọng sai): </font>'
  "Wine chạy được RẤT NHIỀU phần mềm Windows nhưng TUỲ TỪNG APP — có app chạy "
  "mượt, có app chạy một phần, có app chưa chạy được. Ở bản alpha này phần lớn "
  "CHƯA kiểm chứng rộng, nên cách dùng đúng là: thử → nếu chạy tốt thì dùng; "
  "nếu không, Trợ lý gợi bản Linux/web thay thế. NaMi KHÔNG hứa “chạy mọi phần "
  "mềm Windows”.")
bullets([
    "Đợt dùng thật là lúc để biết CHÍNH XÁC app nào của công ty chạy được — "
    "nhân viên thử app Windows hay dùng rồi ghi lại “chạy/không chạy/lỗi gì”.",
])
bullets([
    us("Là dev, tôi muốn chạy một công cụ .NET/Windows quen thuộc để xem có "
       "dùng được trên NaMi không, và báo lại kết quả."),
    us("Là kế toán/văn phòng, tôi muốn thử mở một phần mềm Windows công ty hay "
       "dùng (vd phần mềm kế toán) để kiểm tra mức độ chạy được."),
])

# ---- 5 ----
H("5. Ứng dụng có sẵn")
bullets([
    "Bộ Office NaMi: Văn bản (nDoc) · Bảng tính (nSheet) · Trình chiếu (nSlide) "
    "— mở/sửa file .docx/.xlsx/.pptx của Microsoft Office.",
    "Dành cho công ty IT/dev: git, Python, Node.js, Docker, trình soạn thảo… "
    "cài nhanh qua “Bộ công cụ lập trình” của Trợ lý.",
    "Ứng dụng Việt: Lịch âm/lễ Việt, Cổng Dịch vụ (Thuế/BHXH/Dịch vụ công), ký "
    "số (mức hỗ trợ ghi đúng theo thực tế).",
    "Trình duyệt web, xem PDF, nghe nhạc/xem phim, quản lý máy in/thiết bị.",
])

# ---- 6 ----
H("6. Cài đặt · An toàn · Cập nhật")
bullets([
    "Cài từ USB như Windows (mặc định tiếng Việt). Chia ổ khi cài hiện có: Xoá "
    "cả ổ (máy trống) · Cài song song GIỮ NGUYÊN Windows + dữ liệu · Thủ công. "
    "(Tính năng “tự chia thành C/D/E đều nhau” đang hoàn thiện + test an toàn "
    "dữ liệu trước khi đưa vào.)",
    "Trung tâm Cài đặt, Trung tâm An toàn (tường lửa/cập nhật/quét), Cập nhật "
    "hệ thống — bố trí theo hướng quen thuộc với người dùng Windows.",
])

# ---- 7 ----
H("7. Giới hạn trung thực (bản ALPHA)")
bullets([
    "Đang là bản alpha: có thể còn lỗi giao diện/vặt, một số chỗ chưa “đã mắt” "
    "— rất cần nhân viên chụp màn hình + ghi lại để nhóm vá nhanh.",
    "Wine: tuỳ app (xem mục 4). Ký số qua USB-token còn hạn chế.",
    "Mong mỗi nhân viên ghi: việc đang làm → thao tác → kết quả mong đợi vs "
    "thực tế → ảnh chụp. Đây chính là nguyên liệu để hoàn thiện sản phẩm.",
])

# ---- Khung 20 user-story ----
H("Gợi ý khung 20 user-story (để anh viết nhanh)")
P("Mẫu: “Là [vai trò], tôi muốn [làm gì] để [đạt điều gì].” Gợi ý theo nhóm:")
bullets([
    "VĂN PHÒNG: mở máy dùng ngay; soạn/sửa file Word-Excel của đồng nghiệp; in "
    "tài liệu; đổi hình nền/độ phân giải qua Trợ lý; nộp hồ sơ ở Cổng Dịch vụ.",
    "TRỢ LÝ AI: cài 1 phần mềm bằng 1 câu; nhờ Trợ lý mở đúng trang Cài đặt; "
    "hỏi cách xử lý máy in/wifi; cài “bộ công cụ lập trình” 1 chạm.",
    "WINE: thử chạy 1 app Windows công ty hay dùng và báo kết quả; chạy app "
    ".NET; khi app không chạy, nhận gợi ý thay thế từ Trợ lý.",
    "DEV (công ty IT): dựng môi trường Python/Node/Docker; dùng VS Code + git; "
    "chạy dự án; đánh giá tốc độ/ổn định so với Windows.",
    "CÀI ĐẶT &amp; AN TOÀN: cài NaMi song song giữ Windows; cập nhật hệ thống; "
    "dùng Trung tâm An toàn.",
])
P("Anh viết 20 user-story theo các nhóm trên là phủ đều cả văn phòng lẫn dev; "
  "mỗi story nên kèm “tiêu chí xong” để nhân viên test có cái đối chiếu.")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "NaMi-Gioi-thieu-dung-thu.pdf")
SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=18 * mm, rightMargin=18 * mm,
    topMargin=15 * mm, bottomMargin=15 * mm,
    title="NaMi — Giới thiệu cho đợt dùng thật",
).build(story)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
