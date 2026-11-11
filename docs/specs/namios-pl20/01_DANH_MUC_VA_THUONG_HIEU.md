# 01. Bộ ứng dụng NaMi và dịch vụ thường dùng

## 1. Nhóm cài trên máy, ưu tiên ngoại tuyến

| Tên hiển thị | Việc người dùng làm | Pha và điều kiện trước khi ghi “có sẵn” |
|---|---|---|
| NaMiFiles | Xem thư mục, nhấp đôi tệp, copy/move, tìm, ổ USB, ổ mạng, preview, thuộc tính | P0; file safety, recovery, quyền và test |
| nOffice: nWord/nExcel/nPowerPoint (đổi từ "NaMiOffice: Writer/Sheet/Slides" 11/11/2026 — xem `docs/branding/NAMIOFFICE-APPS.md`) | DOCX/XLSX/PPTX/ODF, bảng, công thức, chart, trình chiếu | P0; theo ma trận v1/v2, không hứa VBA/Power Query |
| NaMiPDF | Xem/chú thích/sắp trang, OCR/sửa/ký/redact theo mốc | P0 viewer; tính năng nâng cao theo Phụ lục 18 |
| NaMiArchive | Xem/nén/giải nén ZIP, 7z, tar.gz; đọc RAR nếu giấy phép/engine cho phép | P0; chống zip bomb/path traversal |
| NaMiImages | Xem/rotate/crop/resize/chỉnh màu cơ bản, slideshow, metadata | P0; editor layer chuyên sâu là tùy chọn |
| NaMiMedia | Phát nhạc/video, playlist, subtitle, điều khiển tốc độ, thiết bị âm thanh | P0; test codec theo gói phát hành |
| NaMiBrowser | Trình duyệt và web apps chính thức | P0; engine upstream cập nhật bảo mật, không “tự viết browser từ đầu” |
| NaMiType | Telex/VNI/Unicode, chuyển chế độ rõ, từ điển, test mọi ô nhập | P0; không can thiệp mật khẩu |
| NaMiSecurity | Tình trạng cập nhật, firewall, quét tệp, backup, quyền | P0; không cam kết chặn mọi mã độc |
| NaMiDevice | Máy in/scan, Wi-Fi/Bluetooth/USB/âm thanh, chẩn đoán theo model | P0; khả năng riêng từng thiết bị |
| NaMiUpdates | Hệ điều hành, app, AI, driver; lịch/rollback | P0; theo Phụ lục 15/19 |
| NaMiHelp/NaMiAI | Trợ giúp offline và AI giải thích lỗi/theo quyền | P0 trợ giúp; AI theo khả năng máy/chính sách |

NaMiCAD Viewer P1 có thể cài sẵn nếu dung lượng ISO, license và corpus DWG/DXF đạt; nếu chưa, App Center hiển thị tùy chọn chính thức, không quảng cáo CAD đã cài. NaMiDraw P1 cho ODG/SVG và sơ đồ phổ thông; ứng dụng chỉnh thiết kế vector chuyên nghiệp là phạm vi khác.

## 2. Lối mở dịch vụ chính thức

Launcher có thể ghim **Zalo Web, YouTube, Google Maps hoặc dịch vụ bản đồ được chọn, Facebook, TikTok, WhatsApp Web**. Nhãn dưới icon: “Dịch vụ web · Cần mạng · Đăng nhập bên cung cấp”; mở domain chính thức qua NaMiBrowser, không tự đăng nhập và không phân phối logo/binary khi chưa có quyền. Người dùng có thể bỏ ghim. Bản PC qua Wine của Zalo/MISA/phần mềm ngành được liệt kê riêng theo version, không trộn với shortcut web. Cập nhật website của họ thuộc nhà cung cấp; NaMiOS cập nhật browser và manifest tích hợp.

Profile mặc định: Cá nhân (giao tiếp/giải trí dễ thấy), Giáo viên/Học sinh (Office/PDF/trình chiếu), Văn phòng (Office/PDF/in), Kế toán (Sheet/PDF/đối soát). Profile chỉ thay thứ tự/ghim và gói tùy chọn có nguồn; không tự cài ứng dụng giải trí trên máy trường học/cơ quan hoặc tự gửi dữ liệu.

## 3. Cổng dùng thương hiệu NaMi

Mỗi app có hồ sơ: nguồn upstream, commit/version, cách phát triển, giấy phép từng thành phần, nghĩa vụ công bố source/notice, quyền icon/font/dịch thuật, đơn vị chịu trách nhiệm vá lỗi, kênh cập nhật, hỗ trợ và khả năng gỡ. Nếu chỉ là shortcut/link đến app thương mại, phải giữ tên nhà cung cấp và không ghép NaMi vào tên sản phẩm của họ. Nếu fork/rebrand LibreOffice hay player, audit tên/nhãn hiệu upstream và nghĩa vụ giấy phép trước khi đưa vào ISO. SBOM và màn hình “Giới thiệu” nêu nguồn chính xác.

Không ghi “tích hợp sẵn” khi app chỉ có ý tưởng hoặc đường dẫn tải; UI và website có trạng thái “Cài trên máy”, “Lối mở web”, “Có thể cài thêm”, “Đang phát triển”, ngày kiểm và phiên bản NaMiOS. Quyết định gói nào vào ISO phải qua bảng dung lượng, hiệu năng máy yếu, bảo mật cập nhật và nhu cầu người dùng Việt pilot.
