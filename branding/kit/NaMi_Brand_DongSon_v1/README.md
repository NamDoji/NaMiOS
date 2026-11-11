# Bộ nhận diện NaMi — Trống đồng hiện đại, bản 1.0

Bộ tài sản triển khai cho hệ điều hành dựa trên Linux. **NaMi** là tên hiển thị trong bộ này; việc dùng tên **NaMiOS** trên sản phẩm thương mại cần được quyết định riêng sau khi kiểm tra tên và nhãn hiệu. Đây là bộ thiết kế ứng dụng, chưa phải xác nhận quyền nhãn hiệu hay logo đã đăng ký.

## Mở nhanh

| Mục đích | Tệp nguồn | Tệp sử dụng |
|---|---|---|
| Logo chính | `01_logo_svg/nami-lockup-horizontal.svg` | `02_logo_png/nami-lockup-horizontal-1024.png` |
| Biểu tượng độc lập | `01_logo_svg/nami-symbol-color.svg` | `02_logo_png/nami-symbol-256.png` |
| Icon nhỏ 16–32 px | `01_logo_svg/nami-symbol-small.svg` | `02_logo_png/nami-symbol-16.png`, `-32.png` |
| Nền tối / đơn sắc | `01_logo_svg/nami-lockup-horizontal-dark.svg`, `nami-symbol-white.svg`, `nami-symbol-black.svg` | Xuất ở kích thước cần dùng |
| Trình duyệt do NaMi đóng gói | `03_app_icons/nami-browser.svg` | `nami-browser-32.png` đến `-512.png` |
| Cài đặt / khởi động / đăng nhập | `04_system_screens/*.svg` | `*-1920x1080.png` |
| Favicon / tệp ico | SVG chính | `02_logo_png/nami-favicon.ico` |

`07_reference/concept-approved-direction.png` chỉ là ảnh ý tưởng được duyệt làm định hướng. SVG trong thư mục 01 là bản dựng hình học để triển khai; rà soát đối chiếu trước khi công bố. Tên chữ trong SVG còn là text, chưa chuyển outline; khi gửi nhà in phải chuyển chữ thành path hoặc nhúng font theo giấy phép.

## Tư duy thiết kế

Mặt trời ở tâm gợi trống đồng Đông Sơn; vòng nhịp hình học tạo cấu trúc công nghệ; những cung màu bao quanh tạo chuyển động như sóng. Không ghép biểu tượng quốc kỳ, không sử dụng họa tiết hiện vật cụ thể dưới dạng sao chép trực tiếp. Ở icon nhỏ dùng hình giản lược để không bị nhòe.

## Quy tắc dùng

- Nền sáng: logo chính. Nền tối: bản dành cho nền tối hoặc biểu tượng trắng.
- Chừa khoảng trống ít nhất 15% đường kính biểu tượng ở mọi phía.
- Không kéo méo, thêm bóng/gradient, xoay riêng mặt trống, thay đổi số lượng màu tùy từng ứng dụng.
- Chỉ dùng bản đầy đủ từ 48 px trở lên. Dưới 48 px dùng bản giản lược. Ở 16 px có thể lược bỏ sắc đỏ/xanh nếu không rõ.
- Mỗi ứng dụng có icon riêng nhưng dùng chung nền, bán kính góc, nhịp màu. Icon trình duyệt được định danh là **NaMi Trình duyệt**, không đổi thương hiệu hay quyền tác giả của Firefox.

## Thành phần

- `01_logo_svg`: nguồn SVG có thể scale.
- `02_logo_png`: biểu tượng PNG nền trong, lockup PNG nền trong, favicon ICO.
- `03_app_icons`: icon cho trình duyệt, trợ lý AI, cửa hàng, cài đặt, cập nhật.
- `04_system_screens`: màn hình mẫu cho trình cài đặt, tiến trình, boot, đăng nhập, giới thiệu. Dữ liệu tiến trình trong hình chỉ là bố cục, ứng dụng thực phải lấy dữ liệu thật.
- `05_design_tokens`: mã màu và nguyên tắc chữ.
- `06_implementation`: bản đồ tích hợp, hướng dẫn và prompt cho Claude Code.

## Giới hạn quan trọng

Đây là tài sản giao diện và tài liệu tích hợp; chưa được áp dụng vào một bản phân phối NaMi đang chạy vì chưa có mã nguồn, tên desktop environment hay trình cài đặt cụ thể. Logo firmware/UEFI của nhà sản xuất phần cứng không được tự ý thay; bản splash này dành cho phần mềm điều khiển được như bootloader và Plymouth. Kiểm tra quyền sử dụng tên trước khi phát hành rộng.
