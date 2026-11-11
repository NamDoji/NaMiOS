# Kiểm tra bàn giao và giới hạn bản mẫu

- Đã kiểm tra: HTML parse, cú pháp JavaScript bằng `node --check`, tồn tại các handler cho Start, danh mục, thiết bị, cập nhật, AI và cài đặt; toàn bộ tài sản cục bộ, không gọi CDN hay API mạng.
- Chưa xác nhận bằng ảnh chụp trình duyệt ở môi trường tạo gói: cơ chế trình duyệt tại đây không cho mở tệp `file://` cục bộ. Claude Code phải mở prototype, chụp và kiểm tra ở 1366×768, 1920×1080, 2560×1440 và viewport hẹp trước khi chuyển thành UI sản xuất.
- Không dùng hình ảnh ba tham chiếu như tài sản giao diện để phân phối. Bộ icon glyph trong HTML là tạm; thay bằng SVG riêng trước phát hành.
- Các thao tác mô phỏng không thay đổi Wi‑Fi, Bluetooth, in, ổ đĩa, tài khoản hoặc cập nhật thật. Số liệu tương thích phần mềm là ví dụ, không là cam kết.
- Browser có thể chiếm phím tắt `Alt+Tab`, `Ctrl+E`, `Super+D`; bản OS phải triển khai ở cấp shell. Phím tắt của bản demo không phải chứng minh OS đã hỗ trợ.
- Quyền dùng tên NaMi/NaMiOS, giấy phép font/hình nền và attribution của phần mềm nền cần được rà soát trước công bố.
