# NaMiOS — logo trống Đông Sơn cách tân, bản thiết kế v2

**Ngày:** 12/11/2026  
**Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam  
**Trạng thái:** phương án thiết kế vector để duyệt và tích hợp thử; chưa khẳng định quyền nhãn hiệu, chưa thay logo trên bản NaMiOS đang chạy.

## Ý tưởng

Mặt trời **12 tia cách tân** làm tâm; nhịp chấm đồng gợi các vòng trang trí của mặt trống; vòng ngoài mở tạo chuyển động như sóng và hành trình liên tục. Vòng tròn cũng liên hệ với tính mở của hệ điều hành. Đây là biểu tượng mới **lấy cảm hứng** từ trống Đông Sơn, không sao chép một hiện vật cụ thể hoặc khẳng định phục dựng khảo cổ.

So với phiên bản cũ: bỏ nhiều vòng lồng nhau, bốn tam giác đỏ, nét trắng trang trí và những mảng màu chồng xéo. Giữ ba màu có vai trò: xanh navy là nền tảng và độ tin cậy, đồng vàng là di sản và năng lượng, teal là chuyển động hướng tới tương lai. Không dùng đỏ làm màu trang trí mặc định.

## Bộ tài sản

| Tệp | Cách dùng |
|---|---|
| `assets/namios-symbol.svg` | biểu tượng chính nền sáng, vector 256-grid |
| `assets/namios-symbol-dark.svg` | biến thể nền tối |
| `assets/namios-symbol-small.svg` | hình 8 tia giản lược cho 16/24/32 px |
| `assets/namios-symbol-mono.svg` | bản đơn sắc để triển khai tiếp theo nền thực tế |
| `assets/namios-lockup.svg` | logo ngang, chữ còn editable; cần font có phép |
| `assets/namios-app-icon.svg` | đế ứng dụng riêng, không áp đế lên logo mọi nơi |
| `assets/*.png` | các cỡ xuất; SVG là nguồn chuẩn |
| `assets/brand-preview.png` | bảng trình bày nền sáng/tối và kích thước |
| `build.py` | script tái tạo SVG/PNG và bảng preview |

## Quy định sử dụng

- Từ 48 px dùng biểu tượng chính; 16–32 px dùng bản giản lược đã xuất. Không thu nhỏ trực tiếp biểu tượng 12 tia để thay cho bản nhỏ.
- Nền sáng dùng bản màu; nền navy dùng bản dark. Bản mono cần kiểm tương phản với từng bề mặt. Vùng trống xung quanh biểu tượng ít nhất 15% đường kính ngoài.
- Không bóp méo vòng tròn, xoay ngẫu nhiên, đổi số tia hoặc từng màu theo hình nền. Tính thích ứng wallpaper của Phụ lục 23 áp dụng cho **lớp hiển thị và nhãn**; brand mark chính vẫn nhận diện ổn định.
- Logo trong `.svg` có chữ ở dạng text để chỉnh sửa; khi bàn giao sản xuất cần khóa font/kiểm giấy phép rồi xuất path hoặc nhúng theo quy trình. Tagline trong lockup là phương án truyền thông, có thể bỏ ở cỡ nhỏ; không nhét tagline vào app icon.
- Kiểm trực quan 16/24/32, 100–200% scaling, nền ảnh sáng/tối và màu xám. Kiểm phỏng vấn nhận diện với người dùng Việt trước khi thay toàn hệ thống.

## Công việc cho Claude Code

Đọc `CLAUDE_CODE_PROMPT.md`, Phụ lục 22 và 23. Thay thế asset theo mapping trong repo thật, giữ bản cũ để rollback. Đồng bộ cài đặt, boot splash, login, About, taskbar, menu, website và tài liệu sau khi phương án được duyệt; không sửa logo bên thứ ba. Công bố tác giả/giấy phép các thành phần nguồn nếu dùng. Đây là một **đề xuất thiết kế mới** chứ không phải xác nhận chất lượng sau thử nghiệm hay đăng ký nhãn hiệu.
