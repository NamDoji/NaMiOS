# Bắt đầu với bộ NaMiOS Brand & UI/UX

**Ngày:** 09/11/2026 · **Bản:** 1.0 · **Chủ dự án:** Đỗ Chí Cường, Đỗ Bảo Nam

## Xem trước

1. Mở `Wallpapers_Contact_Sheet.jpg` để xem đủ 20 ảnh nền trong một trang.
2. Mở `Icons_Contact_Sheet.png` để xem 24 icon chức năng.
3. Mở `UI_Mockup_Printer_SmartAI.jpg` để xem giao diện đề xuất khi máy in cần xử lý và SmartAI giải thích.

## Tệp nguồn

- `00_Brand_Logo/`: logo Sen Việt v2.0 dạng SVG và hướng dẫn.
- `01_Wallpapers_3840x2160/`: 20 ảnh nền JPG 3840×2160.
- `wallpapers_manifest.json`: tên tiếng Việt, kích thước nguồn, kích thước bàn giao, hash SHA-256, trạng thái.
- `02_Icon_System_SVG/`: 24 icon vector giao diện, mỗi icon 24×24.
- `03_NaMiOS_Brand_UIUX_Design_System.md`: quy chuẩn màu/chữ/bố cục, desktop, thiết bị, lỗi, SmartAI, kiểm thử và cổng bản đồ.
- `04_PROMPT_CLAUDE_CODE.md`: yêu cầu có thể dán vào Claude Code.
- `build_wallpapers.py`, `build_icons.py`, `build_ui_mockup.py`: mã dựng lại gói từ ảnh nguồn có sẵn trong phiên làm việc; bản đóng gói này đã chứa tệp bàn giao nên không cần chạy mã để xem.

## Ranh giới quan trọng

Đây là bộ **thiết kế và tài sản dùng thử**, không phải bằng chứng NaMiOS đã được lập trình. 20 hình nền là ảnh minh họa do AI tạo, không phải ảnh chụp tư liệu chính xác địa danh. JPG 3840×2160 là bản nội suy từ ảnh gốc 1672×941. **Không có bản đồ chủ quyền đã được duyệt trong gói**; ảnh 20 chỉ là cảnh biển đảo. Bản đồ có Hoàng Sa, Trường Sa, Phú Quốc và các đảo khác phải qua quy trình `MAP-01` trong đặc tả, nguồn/giấy phép và kiểm định trước khi cài sẵn. Không dùng ảnh trống đồng trong gói làm tư liệu khảo cổ gốc.

## Thứ tự làm với Claude Code

Kiểm kê repo và stack đang dùng → tích hợp tokens/icon/wallpaper → dựng component và desktop preview → catalog lỗi Wi‑Fi/máy in/Bluetooth → SmartAI trợ giúp có chính sách quyền → thử trên máy thật. Xem prompt riêng để biết tiêu chí nghiệm thu. Không đóng ISO hoặc công bố hỗ trợ thiết bị khi chưa có test thật.
