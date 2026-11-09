# NaMiOS — Logo “Sen Việt” v2.0

**Ngày thiết kế:** 09/11/2026  
**Dành cho:** dự án NaMiOS của Đỗ Chí Cường và Đỗ Bảo Nam  
**Trạng thái:** phương án nhận diện mới để xem xét, chưa công bố là nhãn hiệu đã đăng ký.

## Ý tưởng

Bông sen bảy cánh mở rộng và tâm vàng tạo dáng hoa dễ nhận ra ngay khi nhìn lướt. Đường cong dưới bông sen gợi mặt nước, đồng ruộng và nhịp sống gần với nhiều vùng đất Việt. Sắc đỏ son gợi đồ sơn truyền thống và sức sống; vàng ấm gợi ánh sáng, sự hiếu học và hy vọng. Mực đêm là nền trung tính cho một sản phẩm công nghệ. Đây là cách gợi Việt Nam bằng ngôn ngữ tạo hình và chất liệu văn hóa, không dùng hình bản đồ hay biểu trưng nhà nước.

Khẩu hiệu tùy chọn: **“Nét sen Việt, mở tương lai.”** Không đưa khẩu hiệu vào icon hệ điều hành.

## Hệ màu và quy tắc

| Thành phần | Hex | Dùng cho |
| --- | --- | --- |
| Đỏ son | `#C93643` | Chữ OS, điểm nhấn |
| Đỏ cánh | `#AB2430`, `#CF3540`, `#E56365` | Các lớp cánh sen |
| Đỏ đài | `#92212E` | Đài sen |
| Vàng tâm | `#F2C66D` | Cánh trung tâm |
| Vàng nước | `#BC8A43` | Nét nước |
| Mực đêm | `#122A3A` | Nền icon, nền tối |
| Chữ mực | `#182E3B` | Tên NaMi trên nền sáng |

- Dùng bản ngang trên màn hình chào, trang web và tài liệu. Dùng icon vuông cho launcher, cài đặt, màn hình đăng nhập. Dùng bản một màu cho dập nổi hoặc in đơn sắc.
- Chừa khoảng trống quanh logo ít nhất bằng **1/4 chiều cao biểu tượng**. Logo ngang nên rộng tối thiểu 160 px trên màn hình; biểu tượng có bản PNG 32/64/256/1024 px.
- Không đổi tỉ lệ, vẽ thêm ngôi sao/quốc kỳ, phủ hiệu ứng 3D hoặc dùng nền đỏ gần trùng màu cánh. Ở kích thước dưới 32 px nên dùng icon đơn giản hóa sau khi thử trên màn hình thật.
- Font mẫu hiện dùng DejaVu Sans Bold để tệp SVG hiển thị được rộng rãi. Trước khi đăng ký hoặc triển khai thương mại, chọn kiểu chữ có giấy phép phù hợp, điều chỉnh kerning thủ công và chuyển chữ thành outline trong file in cuối.

## Các tệp

- `NaMiOS_Sen_Viet_Symbol.svg`: biểu tượng vector nền trong suốt.
- `NaMiOS_Logo_Horizontal_Light.svg`, `NaMiOS_Logo_Horizontal_Dark.svg`: logo ngang nền sáng/tối.
- `NaMiOS_Symbol_One_Color.svg`: bản một màu.
- `NaMiOS_App_Icon.svg`, các PNG 32/64/256/1024: biểu tượng hệ điều hành.
- `NaMiOS_Logo_Preview.svg/.png`: trang xem nhanh.
- `build_assets.py`: tạo các biến thể SVG từ biểu tượng gốc; các PNG được raster hóa từ SVG.

## Kiểm tra trước khi chốt chính thức

Thử icon trên taskbar và màn hình boot ở 16–32 px, nền sáng/tối, trên màn hình độ tương phản thấp, bản in đơn sắc và với người dùng Việt Nam thuộc nhiều lứa tuổi. Hỏi người xem tự nhận ra “hoa sen” và mô tả cảm nhận trước khi được giải thích. Cần tra cứu nhãn hiệu và các logo tương tự trước khi đăng ký và dùng đại trà.
