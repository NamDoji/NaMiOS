# NaMiOS — Phụ lục 19: Nâng cấp hệ điều hành cho người dùng

**Ngày:** 10/11/2026 · **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam · **Trạng thái:** yêu cầu triển khai, chưa phải báo cáo chức năng đã chạy.

Phụ lục mới này **bổ sung cho Phụ lục 15 — Update Center và bảo mật chuỗi cập nhật**. Chỉ tập trung vào đường đi từ thông báo có phiên bản NaMiOS mới đến cài đặt, khởi động, kiểm tra và khôi phục. Không thay thế tiêu chuẩn bảo mật, ký gói, khóa, firmware và quản trị tập trung của Phụ lục 15.

## Quyết định sản phẩm

- Mọi máy đang dùng bản được hỗ trợ đều có màn hình **Cài đặt → Cập nhật & bảo mật → NaMiOS** và thông báo khi có bản mới phù hợp.
- Người dùng xem được phiên bản, dung lượng, thay đổi, thời gian dự kiến và yêu cầu khởi động lại; chọn cài ngay, cài tối nay hoặc để sau theo chính sách.
- Mặc định cho giai đoạn pilot: **tự kiểm tra và tự tải khi điều kiện phù hợp, hỏi trước khi cài**. Có chế độ tự động theo lịch do người dùng chọn. Không khởi động lại khi còn công việc chưa lưu.
- OS dùng staged deployment có thể quay về bản boot trước hoặc cơ chế transactional tương đương, sau khi đã đánh giá nền Linux/repo thực. Rollback OS không đồng nghĩa khôi phục dữ liệu ứng dụng; migration phải có phương án riêng.
- NaMiOffice, NaMiPDF, browser, SmartAI, driver và firmware có vòng đời cập nhật riêng, nhưng hiển thị trong cùng Update Center; firmware không tự cài theo nút tự động của OS.

## Tập tin

1. 01_LUONG_NGUOI_DUNG.md — giao diện, lựa chọn và câu chữ thông báo.
2. 02_HOP_DONG_KY_THUAT.md — state machine, preflight, boot health, rollback và dữ liệu.
3. 03_KIEM_THU_CLAUDE_CODE.md — test, release gate và prompt triển khai.

Mục tiêu là tạo một trải nghiệm mà người dùng phổ thông hiểu và tin cậy: máy cho biết đang làm gì, khi nào cần khởi động lại, có thể quay về đâu và lỗi nào cần xử lý.
