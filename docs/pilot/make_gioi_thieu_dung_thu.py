#!/usr/bin/env python3
"""Sinh tài liệu DOCX "NaMi — Giới thiệu cho đợt dùng thật" (2–3 trang) để Cuong
viết 20 user-story. Nhấn mạnh Trợ lý AI + Wine; TRUNG THỰC (bản alpha, Wine tuỳ
app). Đối tượng pilot: ~10 nhân viên = văn phòng + dev (mô hình công ty IT).
Tái lập: python3 docs/pilot/make_gioi_thieu_dung_thu.py
"""
from __future__ import annotations

import os

from docx import Document
from docx.shared import Pt, RGBColor

NAVY = RGBColor(0x09, 0x2D, 0x4F)
GOLD = RGBColor(0xB5, 0x80, 0x2E)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10.5)


def h(text, level=1, color=NAVY):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.color.rgb = color
    return p


def b(text):
    doc.add_paragraph(text, style="List Bullet")


def story(text):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run("User-story: ")
    r.italic = True
    r.font.color.rgb = GOLD
    r2 = p.add_run(text)
    r2.italic = True


# ---- Tiêu đề ----
t = doc.add_heading("NaMi — Giới thiệu nhanh cho đợt dùng thật", level=0)
for r in t.runs:
    r.font.color.rgb = NAVY
sub = doc.add_paragraph()
r = sub.add_run("Bản alpha · 20/11/2026 · Tài liệu để viết 20 user-story · "
                "Pilot ~10 nhân viên (văn phòng + lập trình viên)")
r.italic = True
r.font.size = Pt(9.5)

doc.add_paragraph(
    "Mục đích tài liệu: giúp anh nắm NaMi làm được gì để viết user-story sát "
    "thực tế. Hai phần KHÁC BIỆT NHẤT của NaMi là Trợ lý AI và Wine (chạy phần "
    "mềm Windows) — được nói kỹ ở mục 3 và 4. Tài liệu viết trung thực: ghi đúng "
    "cái chạy được và cái còn giới hạn, để đợt dùng thật đặt kỳ vọng đúng."
)

# ---- 1 ----
h("1. NaMi là gì — cho ai", 1)
b("Hệ điều hành MIỄN PHÍ cho người Việt, nền Debian 13 + KDE Plasma 6; giao "
  "diện và thao tác làm theo kiểu Windows để người quen Windows dùng được ngay.")
b("Mặc định tiếng Việt, giờ Việt Nam, gõ tiếng Việt sẵn; có sẵn bộ Office, "
  "trình duyệt, app đọc PDF, nhạc/phim, nén/giải nén…")
b("Đợt này: cho ~10 nhân viên (cả văn phòng lẫn dev) dùng THẬT hằng ngày để tìm "
  "ra chỗ được và chưa được.")

# ---- 2 ----
h("2. Trải nghiệm hằng ngày (giống Windows)", 1)
b("Màn hình nền có nút Start góc trái dưới, thanh tác vụ, các icon quen thuộc "
  "(Máy tính của tôi / Tài liệu / Thùng rác); F5 làm mới desktop.")
b("Quản lý tệp theo ổ đĩa (C/D…), kéo-thả, copy/paste như Windows.")
b("Mở ứng dụng từ menu Start hoặc thanh tác vụ; tắt máy/khởi động lại/đăng xuất "
  "ở màn Rời phiên tiếng Việt.")
story("Là nhân viên văn phòng chưa từng dùng Linux, tôi muốn mở máy lên làm việc "
      "được ngay mà không phải học lại thao tác.")

# ---- 3: TRỢ LÝ AI ----
h("3. ⭐ Trợ lý AI — điểm khác biệt lớn nhất", 1)
doc.add_paragraph(
    "Hỏi bằng tiếng Việt, Trợ lý trả lời VÀ đưa ra NÚT BẤM để làm luôn — không "
    "phải lên Google mò. Ba nhóm việc:"
)
b("CÀI PHẦN MỀM: gõ “cài giúp tôi Zoom / Chrome / VS Code / bộ công cụ lập "
  "trình” → Trợ lý cài 1 chạm từ nguồn chính chủ đã kiểm duyệt (không tự bịa "
  "link). Phần mềm không có bản Linux → nói thật + gợi bản thay thế/web.")
b("SỬA LỖI & THIẾT BỊ: “máy in Canon G2010 không nhận driver”, “wifi không vào "
  "được” → Trợ lý chỉ đúng driver/công cụ để xử lý.")
b("HƯỚNG DẪN CLICK-ĐƯỢC: “tôi muốn đổi giao diện màn hình / độ phân giải / mật "
  "khẩu / ngôn ngữ / âm thanh…” → Trợ lý đưa hướng dẫn ngắn + 1 NÚT, bấm vào mở "
  "thẳng đúng trang Cài đặt để làm ngay (phủ ~28 việc hay dùng).")
b("Nguyên tắc an toàn: Trợ lý CHỈ dùng kho lệnh/link đã kiểm duyệt, tuyệt đối "
  "không tự nghĩ ra link lạ/lệnh lạ → không dẫn người dùng tải nhầm phần mềm độc.")
story("Là nhân viên văn phòng, tôi muốn gõ “đổi hình nền” và bấm 1 nút là mở "
      "đúng chỗ đổi, không phải đi tìm trong menu.")
story("Là dev, tôi muốn gõ “bộ công cụ lập trình” để cài VS Code + Node + "
      "Python + Docker trong một lần.")

# ---- 4: WINE ----
h("4. ⭐ Wine — chạy phần mềm Windows (nói thật)", 1)
doc.add_paragraph(
    "NaMi có lớp Wine để mở phần mềm Windows (.exe) ngay trên hệ; app nền "
    "Microsoft .NET có sẵn Wine-Mono và tự chuẩn bị .NET khi cần."
)
p = doc.add_paragraph()
r = p.add_run("Sự thật quan trọng (đừng đặt kỳ vọng sai): ")
r.bold = True
r.font.color.rgb = GOLD
p.add_run(
    "Wine chạy được RẤT NHIỀU phần mềm Windows nhưng TUỲ TỪNG APP — có app chạy "
    "mượt, có app chạy một phần, có app chưa chạy được. Ở bản alpha này phần lớn "
    "CHƯA kiểm chứng rộng, nên cách dùng đúng là: thử → nếu chạy tốt thì dùng; "
    "nếu không, Trợ lý gợi bản Linux/web thay thế. NaMi KHÔNG hứa “chạy mọi phần "
    "mềm Windows”."
)
b("Đợt dùng thật là lúc để biết CHÍNH XÁC app nào của công ty chạy được — nhân "
  "viên thử app Windows hay dùng rồi ghi lại “chạy/không chạy/lỗi gì”.")
story("Là dev, tôi muốn chạy một công cụ .NET/Windows quen thuộc để xem có dùng "
      "được trên NaMi không, và báo lại kết quả.")
story("Là kế toán/văn phòng, tôi muốn thử mở một phần mềm Windows công ty hay "
      "dùng (vd phần mềm kế toán) để kiểm tra mức độ chạy được.")

# ---- 5 ----
h("5. Ứng dụng có sẵn", 1)
b("Bộ Office NaMi: Văn bản (nDoc) · Bảng tính (nSheet) · Trình chiếu (nSlide) — "
  "mở/sửa file .docx/.xlsx/.pptx của Microsoft Office.")
b("Dành cho công ty IT/dev: git, Python, Node.js, Docker, trình soạn thảo… cài "
  "nhanh qua “Bộ công cụ lập trình” của Trợ lý.")
b("Ứng dụng Việt: Lịch âm/lễ Việt, Cổng Dịch vụ (Thuế/BHXH/Dịch vụ công), ký số "
  "(mức hỗ trợ ghi đúng theo thực tế).")
b("Trình duyệt web, xem PDF, nghe nhạc/xem phim, quản lý máy in/thiết bị.")

# ---- 6 ----
h("6. Cài đặt · An toàn · Cập nhật", 1)
b("Cài từ USB như Windows (mặc định tiếng Việt). Chia ổ khi cài hiện có: Xoá cả "
  "ổ (máy trống) · Cài song song GIỮ NGUYÊN Windows + dữ liệu · Thủ công. "
  "(Tính năng “tự chia thành C/D/E đều nhau” đang hoàn thiện + test an toàn dữ "
  "liệu trước khi đưa vào.)")
b("Trung tâm Cài đặt, Trung tâm An toàn (tường lửa/cập nhật/quét), Cập nhật hệ "
  "thống — bố trí theo hướng quen thuộc với người dùng Windows.")

# ---- 7 ----
h("7. Giới hạn trung thực (bản ALPHA)", 1)
b("Đang là bản alpha: có thể còn lỗi giao diện/vặt, một số chỗ chưa “đã mắt” — "
  "rất cần nhân viên chụp màn hình + ghi lại để nhóm vá nhanh.")
b("Wine: tuỳ app (xem mục 4). Ký số qua USB-token còn hạn chế.")
b("Mong mỗi nhân viên ghi: việc đang làm → thao tác → kết quả mong đợi vs thực "
  "tế → ảnh chụp. Đây chính là nguyên liệu để hoàn thiện sản phẩm.")

# ---- Khung 20 user-story ----
h("Gợi ý khung 20 user-story (để anh viết nhanh)", 1)
doc.add_paragraph("Mẫu: “Là [vai trò], tôi muốn [làm gì] để [đạt điều gì].” "
                  "Gợi ý theo nhóm:")
for s in [
    "VĂN PHÒNG: mở máy dùng ngay; soạn/sửa file Word-Excel của đồng nghiệp; in "
    "tài liệu; đổi hình nền/độ phân giải qua Trợ lý; nộp hồ sơ ở Cổng Dịch vụ.",
    "TRỢ LÝ AI: cài 1 phần mềm bằng 1 câu; nhờ Trợ lý mở đúng trang Cài đặt; hỏi "
    "cách xử lý máy in/wifi; cài “bộ công cụ lập trình” 1 chạm.",
    "WINE: thử chạy 1 app Windows công ty hay dùng và báo kết quả; chạy app .NET; "
    "khi app không chạy, nhận gợi ý thay thế từ Trợ lý.",
    "DEV (công ty IT): dựng môi trường Python/Node/Docker; dùng VS Code + git; "
    "chạy dự án; đánh giá tốc độ/ổn định so với Windows.",
    "CÀI ĐẶT & AN TOÀN: cài NaMi song song giữ Windows; cập nhật hệ thống; dùng "
    "Trung tâm An toàn.",
]:
    b(s)
doc.add_paragraph(
    "Anh viết 20 user-story theo các nhóm trên là phủ đều cả văn phòng lẫn dev; "
    "mỗi story nên kèm “tiêu chí xong” để nhân viên test có cái đối chiếu."
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "NaMi-Gioi-thieu-dung-thu.docx")
doc.save(OUT)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
