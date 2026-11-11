# NaMiOS · Prototype giao diện “Đồng Sơn Contemporary”

**Bản 1.0 — 11/11/2026.** Một prototype có thể bấm thử, một bộ quy tắc thiết kế và lệnh triển khai cho Claude Code. Mở `index.html` bằng trình duyệt thông thường; toàn bộ giao diện dùng HTML/CSS/JS, không gọi mạng và không đọc dữ liệu máy. Các tệp SVG trong `assets/` là logo trống đồng của bộ nhận diện NaMi đã tạo trước đó; `assets/NaMi_Brand_DongSon_Full_Kit_v1.zip` chứa trọn bộ nhận diện để triển khai. Ba ảnh trong `references/` là ảnh mẫu người dùng cung cấp để so sánh, không phải tài sản sẽ cài vào hệ điều hành.

## Xem nhanh

1. Giải nén, mở `index.html`.
2. Dùng menu **Xem luồng** ở phía trên để chuyển giữa 10 màn hình chính.
3. Trên desktop, bấm **Bắt đầu**, tìm ứng dụng, mở Tệp, Cài đặt, Ứng dụng, Cập nhật, NaMi AI. Bấm biểu tượng mạng ở thanh tác vụ để mở cài đặt nhanh.
4. Dùng `Tab`, `Shift+Tab`, `Enter`, `Esc`. Prototype có xử lý thử `Ctrl/Super+E/D`, nhưng trình duyệt có thể giữ các phím tắt này; bản OS phải hỗ trợ ở cấp shell. Nút **Tương phản cao** và **Máy cấu hình thấp** là chế độ kiểm tra bố cục.

## Phạm vi thật của prototype

Đây là bản thiết kế tương tác của UI, không phải hệ điều hành hay bằng chứng tương thích phần mềm. Wi‑Fi, Bluetooth, máy in, cập nhật, AI, đăng nhập, trình duyệt và soạn thảo đều **mô phỏng**. Tài liệu `docs/CLAUDE_CODE_HANDOFF.md` yêu cầu tích hợp với dịch vụ thật và xác minh thiết bị/ứng dụng trước khi công bố.

## Tài liệu

- `docs/DESIGN_SYSTEM.md`: quyết định thẩm mỹ, token, component, kiểu icon và chuyển động.
- `docs/SCREEN_FLOWS.md`: màn hình, trạng thái, tương tác, thông báo và tiêu chí nghiệm thu.
- `docs/CLAUDE_CODE_HANDOFF.md`: lệnh triển khai và cách báo cáo kết quả thực tế.
- `docs/REVIEW_10_LENSES.md`: mười góc nhìn phản biện được mô phỏng bởi AI, không phải đánh giá của mười chuyên gia bên ngoài.

**Nguồn thiết kế:** ảnh người dùng gửi và bộ `NaMi_Brand_DongSon_Full_Kit_v1.zip`. Tên NaMi/NaMiOS còn phải rà soát nhãn hiệu trước phát hành thương mại. Không sao chép nhận diện, icon hoặc giao diện thương mại của Apple, Microsoft, Firefox, LibreOffice hay MISA.
