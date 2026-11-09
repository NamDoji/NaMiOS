# Lệnh giao Claude Code triển khai NaMiOS Brand/UI/UX

Sao chép nguyên phần dưới đây cho Claude Code trong repository NaMiOS. Bàn giao kèm gói này; **không yêu cầu Claude tuyên bố tính năng đã có nếu chưa chạy và kiểm thử**.

---

Bạn là kiến trúc sư Linux desktop, kỹ sư UI/UX và kỹ sư tích hợp NaMiOS. Đọc toàn bộ `03_NaMiOS_Brand_UIUX_Design_System.md`, manifest hình nền, 24 icon SVG và các phụ lục NaMiOS trước. Chủ dự án: Đỗ Chí Cường và Đỗ Bảo Nam. Mục tiêu: bản desktop Việt Nam dễ dùng, quen với người dùng Windows, đẹp, ổn định, lỗi có hướng xử lý, SmartAI hữu ích nhưng an toàn.

## Bước 0: kiểm kê thực tế

- In ra cây repo gọn, xác định distro, desktop shell/toolkit, service mạng, in/scan, Bluetooth, trình cập nhật, bộ gõ, logger, AI đã có hay chưa. Với mỗi hạng mục ghi `implemented/tested/partial/absent` và bằng chứng file/command/test. Không tự tạo module giả hoặc UI tĩnh rồi gọi là hoàn thành.
- Viết ADR chọn cách tích hợp assets và component vào stack hiện tại. Nếu không có repo hay ISO, tạo skeleton có thể chạy trong môi trường dev và ghi rõ những bước chưa thể test trên máy thật.
- Kiểm tra giấy phép font/logo/ảnh/app. 20 wallpaper là ảnh AI **minh họa**, ảnh 3840×2160 nội suy từ bản gốc 1672×941. Chưa có bản đồ được duyệt, tuyệt đối không phát hành một bản đồ tự vẽ. Ảnh 20 chỉ là cảnh biển đảo chung.

## Đầu ra theo 4 nhánh, đi theo thứ tự

**A. Design system:** tạo tokens dạng JSON và binding cho toolkit thực tế; Noto Sans + fallback có dấu; Button, Field, Select, Checkbox, Dialog, Toast, Progress, DeviceCard, ConnectionStepper, ErrorCard, AIPlanCard. Bản sáng/tối, focus, zoom 200%, reduced motion, màn hình 1366×768 trở lên. Tạo trang Storybook/preview nội bộ hoặc demo tương đương. Không sao chép asset giao diện Windows/Apple.

**B. Desktop assets:** nhập 20 JPG offline theo `wallpapers_manifest.json`, verify SHA-256 khi đóng gói, tạo thumbnail bằng build step, đặt ảnh 01 mặc định, chooser có tên tiếng Việt và preview crop. Nhập 24 SVG `currentColor`, ánh xạ tên icon theo Freedesktop; không thay logo ứng dụng bên thứ ba. Thử icon ở 16/24/32 px. Nếu phải đơn giản hóa kích thước nhỏ, tạo symbolic variant riêng và cập nhật manifest.

**C. Feedback & errors:** xây event contract và catalog lỗi có `correlation_id`, `phase`, `cause_code`, `evidence`, `safe_actions`, `result_after_action`; localization tiếng Việt. Luồng mạng phân biệt radio/SSID/auth/IP/DNS/portal; máy in phân biệt discovery/backend/queue/device/scan; Bluetooth phân biệt discover/pair/profile/service. UI phải nói rõ kết nối thành công hay thất bại và lỗi xác định tại bước nào; lỗi chưa đủ bằng chứng phải nói “chưa xác định”, không bịa nguyên nhân. Dùng thông báo chuẩn desktop, error panel có “Thử lại”, “Chi tiết kỹ thuật”, “Nhờ SmartAI giải thích” và lịch sử. Che bí mật trong log.

**D. SmartAI trợ giúp:** adapter chỉ đọc diagnostics trước, tạo kế hoạch tối đa 3 bước có bằng chứng/mức chắc chắn. Hành động thay cấu hình, cài backend, reset dịch vụ, xóa queue hoặc cấp quyền phải qua policy và xác nhận cụ thể; kiểm kết quả, audit, undo nếu có. Không dùng lệnh shell do AI sinh không kiểm soát; không tải driver từ nguồn không tin cậy. Nếu AI lỗi/offline, rule-based diagnostics vẫn dùng được.

## Cổng riêng cho bản đồ

Tạo issue `MAP-01` và placeholder **không đóng vào ISO**. Yêu cầu nguồn bản đồ được phép sử dụng, bản cập nhật hành chính, Hoàng Sa, Trường Sa, Phú Quốc, Côn Đảo và các đảo liên quan, ô phụ nếu cần, chuyên gia rà soát độc lập, bằng chứng duyệt, hash và giấy phép. Chỉ bật asset đó sau khi chủ dự án có nguồn hợp lệ và người có chuyên môn ký duyệt. Không nhờ AI sinh đường biên/đảo.

## Kiểm thử và báo cáo

- Test visual ở 1366×768, 1920×1080, 2560×1440 và scaling 100/150/200%; test bàn phím, screen reader và giảm chuyển động.
- Unit/contract tests cho error events, mã thông báo, localization; integration tests dùng event mô phỏng cho Wi‑Fi/auth/DNS, in/scan, Bluetooth pair/profile và AI offline.
- Máy thật: ít nhất 3 adapter Wi‑Fi, 3 model máy in/MFP và 2 tai nghe/chuột Bluetooth trong lab được chọn từ khảo sát; kết quả từng model/phiên bản, ảnh hoặc log đã che. Nếu không có máy, ghi `not tested`, không suy diễn.
- Người dùng Việt Nam làm 8 tác vụ trong đặc tả. Báo cáo phần trăm hoàn thành, lỗi hiểu nhầm, thời gian và việc phải sửa.
- Bàn giao commit, build commands, demo chạy được, ảnh chụp giao diện, test result, danh sách blocker. Dừng ở từng nhánh khi cổng chất lượng không đạt; mô tả rõ bước tiếp theo. Mọi thay đổi vào repo theo kiểu reviewable, không tự phát hành ISO công khai.

Khi bắt đầu, hãy trả về **kiểm kê hiện trạng và thứ tự file sẽ sửa**, rồi thực hiện nhánh A và B trước. Sau đó triển khai C và D với dữ liệu mô phỏng, kiểm thử, cuối cùng báo cáo bằng chứng tính năng nào đã chạy trên máy thật.
