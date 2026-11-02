# ADR 0005 — Tách chế độ ứng dụng

- **Trạng thái:** proposed
- **Ngày:** 02/11/2026
- **Liên quan:** §5.3, §6.1, §6.2; requirement APP-OFF-006, UX-002

## Bối cảnh

Cùng một "ứng dụng" (ví dụ Excel) có thể được đáp ứng qua nhiều cách: bản Linux native, dịch vụ web, chạy qua Wine, Windows trong VM, hoặc máy remote. Các cách này có phụ thuộc, giới hạn và ý nghĩa pháp lý khác nhau; trộn lẫn chúng sẽ tạo kết luận sai.

## Quyết định

Tách rõ 5 mode: **native / web / wine / vm / remote**, mỗi mode có ID hoặc instance riêng trong catalog. Nhánh **core không phụ thuộc Windows** (native/web/wine); **vm/remote là optional**, ghi rõ license và tài nguyên. Không tự đổi phần mềm của người dùng (ví dụ không âm thầm mở Microsoft Excel desktop bằng LibreOffice/web).

## Lý do

- Tính tương thích trên Wine ≠ vendor hỗ trợ chính thức; bản web là hồ sơ khác; LibreOffice là sản phẩm khác (APP-OFF-006).
- Người dùng phải thấy đúng mode đang dùng và tự xác nhận khi đổi.

## Hệ quả

- Mở XLSX trong LibreOffice KHÔNG cập nhật chứng nhận cho Excel desktop.
- Lựa chọn mode/app mặc định được lưu theo người dùng + loại tệp + mode; hệ thống chỉ gợi ý, không tự thay.
- vm/remote không được dùng để báo nhánh "miễn phụ thuộc Windows" đã đạt (APP-OFF-007).

## Bối cảnh môi trường hiện tại (từ inventory M0)

- Mô hình mode (ID/instance, nhãn, lưu lựa chọn) có thể **thiết kế + test logic ở M1** (dữ liệu/validator). 
- Kiểm chứng hành vi thực (file association, UI không âm thầm đổi mode) cần app-center + desktop → thuộc M3/M4, hiện **BLOCKED** tại host này.

## Spike cần làm + điều kiện chấp nhận

- **Spike:** UI và file association thể hiện đúng mode; thử mở app từ catalog + file association (OFF-01).
- **Điều kiện chấp nhận:** không có trường hợp âm thầm đổi Microsoft desktop sang web/LibreOffice; mỗi mode có hồ sơ + nhãn tách biệt; vm/remote hiển thị license/tài nguyên riêng.
