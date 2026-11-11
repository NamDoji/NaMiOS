# NaMi Human Interface · Đồng Sơn Contemporary

## 1. Ý đồ

Sự sang trọng đến từ nhịp bố cục, chất liệu vừa đủ, sắc màu có kiểm soát và những trạng thái đáng tin. Logo trống đồng là dấu nhận diện duy nhất của hệ điều hành; các ứng dụng có icon riêng. Desktop gợi cảm giác quen của máy tính Windows nhưng có bề mặt và kiểu chữ riêng của NaMi. Vẻ đẹp không che giấu nút bấm, trạng thái hoặc lỗi.

Định hướng từ ba ảnh mẫu: giữ nền navy sâu, bố cục desktop và thanh tác vụ đáy của mẫu 1–2; giảm nền tím/hồng, bỏ icon bóng nổi nặng của mẫu 3; tránh title “mockup” trong sản phẩm và tránh vùng trống thừa ở danh mục ứng dụng. Mẫu 2 dùng thuật ngữ kỹ thuật và trạng thái quá ngắn; prototype dùng trạng thái theo nhiệm vụ và panel giải thích.

## 2. Màu chủ đạo

| Token | Hex | Ý nghĩa |
|---|---|---|
| `night-950` | `#081B2D` | nền desktop sâu |
| `navy-900` | `#0B2238` | bề mặt hệ thống tối |
| `ink-800` | `#172C3E` | chữ chính trên nền sáng |
| `warm-50` | `#FCFBF8` | cửa sổ, nội dung |
| `warm-100` | `#F4F4F1` | vùng phụ |
| `champagne-500` | `#D6AB66` | hành động/nhận diện cao cấp |
| `teal-600` | `#297F82` | điều khiển kết nối, tiến trình |
| `coral-600` | `#BB5E55` | cảnh báo/nguy hiểm có tiết chế |
| `border-200` | `#DEE3E4` | đường phân cách nhẹ |
| `success-700` | `#287B62` | thành công |
| `warning-700` | `#9A6A21` | một phần/cần lưu ý |

Các màu trên là nhận diện, không phải mọi cặp chữ/nền đều tự động đạt tương phản. Tạo semantic tokens theo trạng thái và đo WCAG 2.2 AA trên light/dark/high-contrast. Bản tương phản cao dùng bề mặt đặc, viền rõ; không phụ thuộc blur hay màu đơn lẻ.

## 3. Chữ và khoảng cách

- Font UI: Inter/Noto Sans/Segoe UI trong prototype với fallback hệ thống; bản OS chọn font có quyền phân phối, hiển thị dấu tiếng Việt đúng. Không đưa font thương mại vào gói mà chưa có giấy phép.
- Cấp chữ: display 28–32; tiêu đề 24–26; mục 18–20; nội dung 14–16; metadata 12–13 px tương đương tại 100%. Kiểm tra với 125/150/200% scale; không ép chữ nhỏ vì muốn nhìn “luxury”.
- Spacing thang 4/8/12/16/24/32/48. Cửa sổ nội dung có lề 22–30. Grid 2 hoặc 3 cột theo chiều rộng, co thành 1 cột. Sidebar chuyển sang tab ngang khi hẹp.
- Border radius 8–12 control, 15 card, 18–24 cửa sổ/panel. Shadow mềm một lớp, tránh bevel/3D bóng nhựa.
- Chuyển động 120–220ms cho phản hồi nhẹ, có `prefers-reduced-motion`. Không dùng animation dài ở boot hoặc modal lỗi.

## 4. Hệ icon và logo

Biểu tượng trống đồng dùng ở Start, About, cài đặt và đăng nhập. Icon ứng dụng có nền nhẹ, hình đơn sắc hoặc hai màu, cùng bán kính, cùng độ đậm, biểu thị tác vụ: tệp, soạn thảo, bảng tính, trình duyệt, thiết bị, AI, cập nhật. Icon prototype là glyph tạm dùng để thể hiện cấu trúc; Claude phải thay bằng SVG nguyên gốc có lưới 24/32/48 px và thử ở 16 px. Không dùng chữ W/X/P hoặc icon gần giống logo Microsoft Office cho ứng dụng NaMi.

Logo trình duyệt NaMi là icon launcher do NaMi sở hữu. Nếu chạy Firefox, trong About/chi tiết ứng dụng phải ghi nguồn gốc, giấy phép và bản cập nhật của Firefox; không ghi đè trực tiếp nhận diện trong package Firefox.

## 5. Thành phần

| Component | Chỉ dẫn |
|---|---|
| Window chrome | nút thu nhỏ, phóng to, đóng bên phải; một titlebar 50px, tên tệp được rút gọn nếu dài |
| Button | chính navy, hành động mang thương hiệu champagne, nguy hiểm coral; có hover/focus/disabled/loading |
| Form | nhãn ở gần trường, lỗi chỉ rõ cách sửa, vùng bấm >=32px desktop; không dùng placeholder làm nhãn duy nhất |
| Cards | nhóm một mục đích; metadata không được chìm; bấm vào thấy chi tiết |
| Notification | xác nhận thành công ngắn; lỗi cần xử lý giữ trong lịch sử; trạng thái có chữ + biểu tượng |
| Dialog | nêu tác động, cách quay lại, nhãn nút cụ thể; hành động nguy hiểm không là default |
| Progress | phải lấy phần trăm thật khi kết nối backend; nút hủy/tạm dừng khi hỗ trợ |
| Search | kết quả chia ứng dụng/tệp/cài đặt; chỉ tìm cục bộ theo quyền đã cấp; AI có vùng riêng |

## 6. Trạng thái & vật liệu

- Nội dung chính nền đặc ivory; chỉ thanh tác vụ và các panel hệ thống có thể mờ nhẹ khi GPU hỗ trợ. Tắt blur trong chế độ máy yếu hoặc tăng tương phản.
- Focus ring luôn nhìn thấy bằng bàn phím. Tương phản chữ tối thiểu 4.5:1, UI quan trọng 3:1 khi áp dụng WCAG phù hợp.
- Thành công, cảnh báo, chưa kiểm tra, bị chặn có nhãn chữ và màu riêng. Không gọi “đạt” nếu chỉ mở được giao diện mà chưa hoàn tất nghiệp vụ.
- Hình nền mặc định nên là nền navy trừu tượng. Wallpaper Việt Nam có thể chọn trong cài đặt sau khi xác minh bản quyền và chính xác địa danh.
