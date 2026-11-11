# Yêu cầu triển khai cho Claude Code

## Lệnh giao việc nguyên văn

> Hãy giải nén `NaMiOS_Prototype_Luxury_v1.zip`, xem `index.html`, đọc `README.md`, `docs/DESIGN_SYSTEM.md` và `docs/SCREEN_FLOWS.md`. Đây là prototype NaMi Human Interface “Đồng Sơn Contemporary”, định hướng thương hiệu mới của NaMi. Hãy dùng nó làm chuẩn về cấu trúc, màu sắc, khoảng cách, vị trí điều khiển, thuật ngữ tiếng Việt và phản hồi người dùng. Không coi HTML là mã sản xuất, không copy nguyên mã HTML vào shell nếu toolkit hiện tại khác.
>
> Bước 1: khảo sát repo thực và báo cáo base Linux, desktop environment/compositor, toolkit, bootloader, installer, display manager, launcher, app catalog, file manager, update system, NetworkManager/BlueZ/CUPS, AI broker, cách đóng gói và thiết bị mục tiêu. Liệt kê tất cả branding cũ cần thay và các thành phần chưa có. Không phỏng đoán.
>
> Bước 2: xây gói `nami-branding` cùng design tokens semantic light/dark/high-contrast, typography tiếng Việt được cấp phép, icon theme SVG/PNG, wallpaper có quyền sử dụng, component library, localization, nội dung lỗi chuẩn. Giữ biểu tượng trống đồng từ gói thương hiệu; icon ứng dụng cần vẽ riêng và không dùng chữ W/X/P như biểu tượng Microsoft.
>
> Bước 3: triển khai theo thứ tự S01/S02 desktop & Start → S04 Tệp → S08 kết nối thiết bị → S09 cập nhật → S03 danh mục tương thích → S10 AI → S11 installer/S12 login → Office/Browser/About. Mỗi phần cần một patch tách biệt, ảnh chụp, test và hướng dẫn rollback. Nếu stack hiện tại không hỗ trợ cách mô phỏng của HTML, chọn control native tương đương và giải thích quyết định.
>
> Bước 4: nối trạng thái thật. Danh mục ứng dụng phải hiển thị kết quả từ ma trận thử nghiệm theo phiên bản/tác vụ, không nhận dữ liệu minh họa là sự thật. Wi‑Fi/Bluetooth/máy in phải gắn backend có cơ chế báo lỗi rõ. Cập nhật phải dùng repo có chữ ký và giao dịch/rollback được kiểm chứng. SmartAI chỉ đọc trạng thái sau khi được cấp quyền, hiển thị xem trước và xin xác nhận trước thao tác đặc quyền; không tự gửi log.
>
> Bước 5: chạy test trên VM và máy thật. Kiểm tra 1366×768, 1920×1080, 2560×1440; scaling 100/125/150/200%; light/dark/high-contrast/reduced-motion/low-GPU; bàn phím, screen reader; offline, mất mạng, lỗi driver, hết dung lượng, khôi phục sau update. Báo kết quả thực, lỗi còn mở và đường nâng cấp từ branding cũ mà không mất cài đặt người dùng.
>
> Không sửa icon/package Firefox, LibreOffice hay MISA để nhận là phần mềm NaMi. Có thể tạo launcher NaMi riêng nếu giữ attribution, giấy phép và kênh cập nhật gốc. Không đổi firmware logo, không tắt Secure Boot hoặc xác minh chữ ký vì mục đích thẩm mỹ. Không tuyên bố “chạy mọi phần mềm Windows” khi chưa kiểm tra.

## Bảng chuyển từ prototype sang OS

| HTML demo | Thành phần OS thực | Hợp đồng trạng thái cần khai báo |
|---|---|---|
| `state.start` | app launcher | open/close, query, results, launch failure |
| `state.screen` | shell/window manager | window open/close/minimize/maximize, focus |
| `state.wifi` | NetworkManager | radio state, AP scan, auth, IP/DNS, failure codes |
| `state.bt` | BlueZ | adapter, discovery, pairing, profile, failure |
| `test-print` | CUPS/IPP | printer, job ID, queue, device status, test page result |
| `state.updateProgress` | update agent | signed metadata, download, verify, install, reboot, rollback |
| `state.selectedApp` | compatibility DB | app version, test date, OS build, task matrix, evidence |
| `state.aiText` | SmartAI broker | prompt, allowed context, consent, tool call, audit, result |
| `state.installStep` | installer | hardware, partitions, backup, consent, install, recovery |
| `state.auth` | display manager | session login, keyboard layout, account, errors |

## Các đầu ra bắt buộc

1. Audit repo và bản đồ branding cũ → mới; đề xuất chính xác stack UI.
2. Tokens ở định dạng đọc được bởi toolkit và icon nguồn SVG có giấy phép rõ.
3. Component library và 12+ màn hình/states đã tích hợp thật.
4. Bảng thuật ngữ UI tiếng Việt và bản dịch tiếng Anh tối thiểu.
5. Test tự động cần thiết: component state/keyboard, updater rollback, compatibility evidence schema, device error code mapping; test thủ công với thiết bị thật.
6. Ảnh chụp và video ngắn các luồng F01–F07 trên bản chạy, không dùng ảnh prototype để báo hoàn thành.
7. PR/commit tách module, hướng dẫn build, triển khai, cập nhật và rollback.

## Điều kiện dừng phát hành

- Chưa rõ quyền dùng tên NaMi/NaMiOS hoặc quyền phân phối logo/font/hình nền.
- Luồng cài đặt có thể xóa dữ liệu nhưng chưa hiển thị phân vùng và xác nhận rõ.
- Cập nhật có thể phá boot hoặc mất dữ liệu mà chưa có recovery được thử.
- Các trạng thái tương thích công bố không có dữ liệu kiểm thử.
- Thành phần cốt lõi không dùng được bằng bàn phím hoặc thông báo lỗi không có cách xử lý.

## Nguồn nguyên tắc, không phải tài sản sao chép

Apple HIG: https://developer.apple.com/design/human-interface-guidelines/design-principles/  
Microsoft Fluent: https://learn.microsoft.com/en-us/windows/apps/design/  
GNOME HIG: https://developer.gnome.org/hig/  
KDE HIG: https://develop.kde.org/hig/  
WCAG 2.2: https://www.w3.org/TR/WCAG22/
