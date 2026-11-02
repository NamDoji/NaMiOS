# NaMiOS branding — PLACEHOLDER (chưa có asset thật)

File này đánh dấu rằng thư mục `usr/share/namios-branding/` trong ảnh
Live **chưa có** asset branding nhị phân thật (logo, icon set ứng dụng,
splash screen SDDM/Plymouth). Đây là khung chỗ-để-đặt-file
(placeholder), không phải branding đã hoàn chỉnh.

## Điều kiện bắt buộc trước khi thêm asset thật vào đây

1. Asset do NaMiOS tự thiết kế, hoặc lấy từ nguồn có giấy phép cho phép
   phân phối lại rõ ràng (ghi nguồn + giấy phép cụ thể cạnh file asset).
2. **TUYỆT ĐỐI KHÔNG** sao chép icon, font hoặc âm thanh của Microsoft
   hay bất kỳ bên thứ ba không có quyền phân phối (theo yêu cầu nhiệm vụ
   và §5.1/LIC-006 của đặc tả).
3. Logo/icon không được gây nhầm lẫn là sản phẩm chính thức của Debian,
   KDE, hay bất kỳ nhãn hiệu bên thứ ba khác (OWN-001: NaMiOS không sở
   hữu các dự án đó).
4. Ghi rõ định dạng, độ phân giải, và vị trí cài đặt dự kiến (ví dụ
   `usr/share/namios-branding/logo.svg`, `usr/share/sddm/themes/namios/`)
   trong một README cập nhật thay thế file này.

## Danh sách asset còn thiếu (TBD)

- Logo NaMiOS (SVG, vector, nền trong suốt).
- Icon set ứng dụng namios-* (namios-welcome, namios-app-center, ...).
- Theme SDDM màn hình đăng nhập.
- Splash Plymouth lúc boot (nếu dùng).

Không tạo file nhị phân giả (ví dụ PNG trống/placeholder) thay cho asset
thật — giữ README này cho tới khi có asset thật kèm giấy phép rõ ràng.
