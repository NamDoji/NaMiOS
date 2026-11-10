# 03. Giao diện và thói quen sử dụng của người Việt

## 1. Desktop quen thuộc, nhận diện riêng

Màn hình đăng nhập, desktop, taskbar/dock, launcher, tray, notification center, file manager, Settings và dialog cùng một họ thiết kế. Một cú nhấp mở app trên taskbar, nhấp đôi mở tệp/thư mục, Alt+Tab đổi cửa sổ, Ctrl+C/V/X/Z/A/F/S/P theo ngữ cảnh, Delete/Shift+Delete có xác nhận phù hợp, F2 đổi tên, Win/Super+E mở NaMiFiles, Win/Super+L khóa máy; phím tắt có trang trợ giúp và tùy chỉnh để không xung đột bộ gõ.

Thẩm mỹ lấy cảm hứng từ độ tinh gọn, khoảng trắng và chuyển động mượt của hệ điều hành hiện đại, nhưng dùng logo sen cân đối cuối cùng của NaMiOS, màu/navy/đỏ sen/vàng tiết chế, icon riêng và từ ngữ riêng. Bộ Brand UI/UX cũ có thể ghi logo sen phiên bản khác; **asset logo sen cân đối được chủ dự án duyệt gần nhất là nguồn ưu tiên**, cần đối chiếu vector và tokens trước khi đóng ISO. Không sao chép pixel, icon, tên control/trademark Apple/Microsoft. Hình nền Việt Nam có quyền và mô tả nguồn, không dùng bản đồ AI làm bản đồ thật.

Font có giấy phép, hỗ trợ đầy đủ dấu tiếng Việt, nội dung 15–17px ở 100%, tỉ lệ phóng 100–200%, control 40–44px trở lên cho thao tác thông thường, focus rõ, contrast theo WCAG 2.2 AA, reduced motion, screen reader. App mở dưới 3 giây trên máy baseline cho tác vụ đơn giản là mục tiêu đề xuất cần benchmark, không claim trước khi đo.

## 2. Lần dùng đầu tiên

Onboarding tối đa vài màn hình: chọn tiếng Việt/English; Telex/VNI; Wi-Fi; quyền riêng tư/AI cloud; cập nhật tự động; giới thiệu 3 thao tác “Mở tệp, Mở ứng dụng, Tìm trợ giúp”. Tự phát hiện máy in/scan/Bluetooth phù hợp nhưng không quét rộng mạng cơ quan ngoài quyền. Trang “Ứng dụng của tôi” ghim NaMiOffice/NaMiPDF/NaMiFiles/NaMiBrowser/NaMiType, còn web services chia nhóm với badge “Cần mạng”.

Tìm kiếm launcher hiểu “mở excel”, “đọc PDF”, “giải nén rar”, “xem video mp4”, “máy in không chạy”, tên không dấu; kết quả đầu chỉ app có thật hoặc giải pháp đã chứng nhận. “Mở Excel” có thể mở NaMiSheet, không ám chỉ Microsoft Excel native. Nếu cần phần mềm chưa có, App Center giải thích Linux/web/Wine/Windows có phép theo trạng thái kiểm thử.

## 3. Mẫu lỗi và hỗ trợ

Thông báo lỗi chuẩn: **việc gì thất bại + đối tượng + nguyên nhân đã biết + điều không bị thay đổi + hành động tiếp theo**. Ví dụ:

| Tình huống | Lời nhắn chính | Hành động |
|---|---|---|
| RAR mật khẩu | “Chưa giải nén được TAILIEU.rar vì mật khẩu không đúng. Tệp gốc còn nguyên.” | Nhập lại, xem chi tiết |
| MP4 codec lạ | “NaMiMedia mở được tệp nhưng chưa giải mã được luồng video này.” | Xem codec, gói hợp lệ nếu có |
| DWG xref thiếu | “Bản vẽ mở được một phần; còn thiếu 2 tệp tham chiếu.” | Xem tên, chỉ đường dẫn |
| PDF chữ ký | “Tệp đã ký; chỉnh sửa có thể ảnh hưởng hiệu lực chữ ký.” | Chỉ xem, lưu bản sao |
| USB rút giữa copy | “Sao chép chưa hoàn tất. Tệp đích chưa được xác nhận.” | Cắm lại, thử lại |
| Máy in offline | “NaMiDevice chưa liên lạc được với máy in tầng 2.” | Kiểm dây/mạng, xem hàng đợi |

SmartAI nhận mã lỗi từ ứng dụng và trạng thái hệ thống đã lọc, tối đa ba bước giải thích; không tự gỡ chương trình, tải codec/driver không tin cậy, đổi công thức, sửa CAD/PDF hoặc gửi file ra cloud. Mọi hành động ghi tài liệu cần preview, xác nhận và undo/Save As. Không có AI, mọi ứng dụng vẫn có lối xử lý lỗi cơ bản.

## 4. Kiểm thử cảm giác quen thuộc

Thử với ít nhất ba nhóm pilot: người dùng gia đình, giáo viên/văn phòng, IT/kế toán. Các tác vụ: tìm file tải về; tạo bảng có công thức; mở PDF và in; giải nén; xem ảnh và MP4; ghim Zalo Web; kết nối Wi-Fi và máy in. Đo tỉ lệ hoàn thành không cần hướng dẫn, số bước, thời gian, lỗi hiểu nhầm “web app là cài trên máy”, lỗi lưu bản gốc. Ngưỡng chốt theo baseline thử nghiệm, không bịa số “dễ dùng hơn Windows”.
