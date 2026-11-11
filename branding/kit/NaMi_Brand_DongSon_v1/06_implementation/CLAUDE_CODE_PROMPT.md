# Lệnh triển khai cho Claude Code

Hãy tích hợp gói tài sản NaMi_Brand_DongSon_v1 vào repo hệ điều hành hiện tại. Trước khi sửa, báo cáo: desktop environment, bootloader, installer, display manager, icon theme, cơ chế đóng gói và cập nhật; liệt kê vị trí branding cũ. Sau đó lập bảng mapping cũ → mới và triển khai theo `PLACEMENT_MAP.md`.

Yêu cầu bắt buộc:
- Giữ nguồn SVG làm chuẩn. Xuất PNG cho các kích thước cần thiết. Cài font hỗ trợ tiếng Việt theo giấy phép hợp lệ. Áp dụng logo ở website, cài đặt, splash phần mềm, màn hình đăng nhập, menu, About và ứng dụng do NaMi sở hữu.
- Icon dưới 48 px dùng `nami-symbol-small.svg`. Không chèn hình splash tĩnh như UI tương tác; tạo nút, text và progress thật, có screen reader và keyboard focus.
- Tạo gói `nami-branding` và cơ chế update/rollback. Không ghi đè trực tiếp tài sản của Firefox hoặc bên thứ ba. Tạo launcher riêng `NaMi Trình duyệt`, icon riêng; nếu chạy Firefox, giữ attribution, giấy phép, quyền thương hiệu và khả năng update trình duyệt độc lập.
- Không đổi logo firmware/UEFI, không vô hiệu Secure Boot, không tắt cơ chế xác minh chữ ký hoặc cập nhật chỉ để đổi hình.
- Viết tài liệu đường dẫn cụ thể đã sửa, cách build, cách test, cách hoàn nguyên. Chụp ảnh kiểm tra ở màn hình 1366×768, 1920×1080, 2560×1440; tỷ lệ 100%, 150%, 200%; nền sáng/tối, icon 16/24/32/48/64 px.
- Kiểm tra boot fallback text, installation offline, user upgrade từ branding cũ, xóa icon cache, trình duyệt mặc định và click HTTP/HTTPS; đảm bảo không mất thiết lập người dùng.
- Nếu repo thiếu thành phần, dừng ở module đó, ghi rõ thiếu gì và tiếp tục các module độc lập. Không báo cáo hoàn thành khi chưa chạy thử trên image/VM.

Đầu ra: commit patch/PR, gói cài branding, manifest tài sản, ảnh chứng minh, báo cáo test và danh sách vấn đề còn mở. Đây là bộ tài sản 1.0 concept; trước phát hành chính thức cần phê duyệt quyền tên/nhãn hiệu và soát lại vector master.
