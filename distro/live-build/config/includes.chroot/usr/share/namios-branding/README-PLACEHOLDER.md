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
- Icon set ứng dụng namios-* (namios-welcome, namios-app-center, ...) — các
  file cấu hình skel hiện tham chiếu tên icon đặt trước (`namios-welcome`,
  `start-here-namios`) nhưng CHƯA có file icon thật tương ứng; Plasma sẽ rơi
  về icon fallback chung khi thiếu, không crash.
- Theme SDDM màn hình đăng nhập.
- Splash Plymouth lúc boot (nếu dùng).

**Cập nhật (việc desktop "giống Windows", 02/11/2026):** hình nền desktop mặc
định tạm (vector, tự soạn) đã có tại
`usr/share/backgrounds/namios/namios-default.svg` — xem README-PLACEHOLDER.md
cạnh file đó để biết phần còn thiếu (bản raster, xác nhận hiển thị thật).
Mục này KHÔNG tính là đã xong toàn bộ branding — chỉ 1/5 hạng mục TBD.

Không tạo file nhị phân giả (ví dụ PNG trống/placeholder) thay cho asset
thật — giữ README này cho tới khi có asset thật kèm giấy phép rõ ràng.
