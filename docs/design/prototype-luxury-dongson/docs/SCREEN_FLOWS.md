# Ma trận màn hình, trạng thái và luồng tương tác

## 1. Danh sách màn hình

| ID | Màn hình | Prototype thể hiện | Backend cần nối khi triển khai |
|---|---|---|---|
| S01 | Desktop | hình nền, icon, taskbar, cửa sổ Office | compositor/window manager, session |
| S02 | Bắt đầu & tìm | ứng dụng ghim, nhóm việc, tìm cục bộ | app index, file search, settings search |
| S03 | Danh mục ứng dụng | bộ lọc nhóm, 4 trạng thái, panel chi tiết | catalog, compatibility test data, install |
| S04 | Tệp | sidebar, thư mục, danh sách file, mở/in | filesystem, MIME, permission, trash |
| S05 | NaMi Office | trang soạn thảo và toolbar mẫu | LibreOffice/ứng dụng thực, attribution |
| S06 | Trình duyệt | launcher và trang bắt đầu | browser package, default browser, URL handler |
| S07 | Cài đặt nhanh | Wi‑Fi, Bluetooth, âm lượng | NetworkManager, BlueZ, PipeWire |
| S08 | Cài đặt thiết bị | trạng thái mạng, Bluetooth, máy in, USB | NetworkManager, BlueZ, CUPS/IPP, udev |
| S09 | Cập nhật | changelog, tự động, progress mô phỏng | ký số repo, updater, lịch và rollback |
| S10 | NaMi AI | hướng dẫn, xin quyền chẩn đoán | agent broker, audit, policy, model |
| S11 | Installer | ba bước, kiểm tra, cảnh báo dữ liệu | installer/phân vùng/backup/chữ ký |
| S12 | Login | chọn tài khoản, bàn phím, trạng thái | display manager, PAM, policy |
| S13 | About | phiên bản, người sáng lập, giấy phép | metadata bản dựng, SBOM, license |

## 2. Luồng bắt buộc khi xây bản thật

### F01 — Mở ứng dụng
`Desktop → Bắt đầu → tìm hoặc chọn ứng dụng → mở → taskbar cho biết đang chạy`. Không thêm pop-up chào mừng nếu người dùng đã dùng app. Khi lỗi phải nêu tên app, vị trí log và cách thử lại.

### F02 — Tìm và in tệp
`Tệp → chọn DOCX/PDF → mở đúng ứng dụng → In → chọn máy in → xem khổ giấy → in → hàng đợi → kết quả`. Nếu máy in mất kết nối, nêu cụ thể vị trí kiểm tra; không báo “đã in” khi chỉ đưa job vào hàng đợi.

### F03 — Tương thích phần mềm Windows
`Danh mục → tìm phần mềm → kết quả theo phiên bản & tác vụ → môi trường chạy → giới hạn → hướng dẫn cài/chạy → ghi nhận kết quả`. Bốn trạng thái: **Dùng được** (phải có bộ nghiệp vụ đã xác nhận), **Một phần**, **Chưa kiểm tra**, **Không mở được**. Bản phát hành chỉ hiển thị kết quả có bằng chứng; status trong HTML chỉ là demo.

### F04 — Kết nối Wi‑Fi/Bluetooth/máy in
`Phát hiện → chọn → xác thực/quyền → kết nối → kiểm tra chức năng → thành công hoặc lỗi cụ thể`. Với Wi‑Fi: phân biệt sai mật khẩu, không có mạng, driver chưa nhận, DNS lỗi. Với Bluetooth: trạng thái adapter/pairing/profile. Với máy in: IPP/USB, driver/filter, hàng đợi, giấy/mực, trang thử. SmartAI nhận chẩn đoán chỉ sau khi người dùng chủ động yêu cầu.

### F05 — Cập nhật
`Có bản mới → xem thay đổi/dung lượng/yêu cầu restart → chọn lịch hoặc cập nhật → xác minh nguồn/chữ ký → tải → cài → restart → tự kiểm tra → rollback nếu thất bại`. Các bước hiện thị trung thực. Không để chọn tự động cập nhật thay thế consent với thay đổi dữ liệu hoặc restart bất ngờ.

### F06 — AI hỗ trợ
`Người dùng gọi → AI giải thích vấn đề → xin quyền đọc trạng thái tối thiểu → hiển thị dữ kiện và mức chắc chắn → đề xuất → xem trước thao tác → xác nhận → chạy → báo kết quả và cách hoàn tác`. Không tự chẩn đoán/đọc nội dung tệp nhạy cảm hoặc tải log lên mạng.

### F07 — Cài đặt
`Chọn tiếng Việt → kiểm tra điều kiện → chọn ổ và sao lưu → tổng kết chính xác thay đổi phân vùng → xác nhận riêng thao tác xóa → cài → lỗi có đường cứu → lần đầu đăng nhập`. Ba màn HTML chỉ là mô phỏng hình thức; không thực hiện partition.

## 3. Lỗi mẫu & microcopy

| Sự kiện | Thông báo người dùng | Hành động |
|---|---|---|
| Wi‑Fi sai mật khẩu | “Không kết nối được Mạng Nhà. Mật khẩu có thể chưa đúng.” | Nhập lại · Chẩn đoán |
| Máy in chờ giấy | “Lệnh in đã vào hàng đợi. Máy in đang báo hết giấy.” | Mở hàng đợi · Xem máy in |
| Bluetooth không có adapter | “Máy này chưa nhận bộ Bluetooth.” | Kiểm tra thiết bị · Xem driver |
| Update thiếu dung lượng | “Cần thêm 1,2 GB để tải bản cập nhật.” | Dọn dung lượng · Để sau |
| App chưa kiểm | “Chưa có kết quả thử với phiên bản này.” | Xem yêu cầu · Đề xuất kiểm thử |
| AI thiếu quyền | “Để xem lỗi máy in, NaMi AI cần đọc trạng thái hàng đợi in.” | Cho phép một lần · Hủy |

Mỗi thông báo lỗi cần mã lỗi sao chép, liên kết tới chi tiết nếu có, và không suy đoán nguyên nhân thành sự thật.

## 4. Tương tác đã có trong HTML

- Menu Bắt đầu mở/đóng; tìm lọc ứng dụng; bấm app mở cửa sổ.
- Danh mục lọc nhóm và mở panel trạng thái chi tiết.
- Tệp mở tài liệu; nút In cho phản hồi mô phỏng.
- Cài đặt nhanh và thiết bị bật tắt trạng thái demo.
- Cập nhật chạy thanh tiến trình demo, tự động cập nhật đổi trạng thái demo.
- NaMi AI nhận câu hỏi, hiển thị bước xin quyền minh họa.
- Installer ba bước, login đi vào desktop demo.
- `Esc`, `Tab`, `Enter`, `Ctrl/Super+E/D`; chế độ tương phản cao và máy cấu hình thấp.

## 5. Nghiệm thu sản phẩm thật

- Thử tại 1366×768, 1920×1080, 2560×1440; 100/125/150/200% scale; cửa sổ hẹp. Không cắt tiêu đề, nút và thẻ. Tại 1024×600 phải hoàn thành tác vụ thiết yếu hoặc có bố cục compact đã mô tả.
- Toàn bộ luồng chính dùng được bằng bàn phím và có accessible name; focus rõ, screen reader thông báo kết quả. Đo tương phản theo WCAG 2.2 AA ở light/dark/high contrast.
- Có chế độ giảm chuyển động, tắt blur và không phụ thuộc GPU mạnh. Đo độ trễ shell trên máy tham chiếu do nhóm phát triển công bố.
- Thử 5 người mới dùng Linux, 5 người quen Windows, ít nhất 2 người cần phóng chữ hoặc công cụ trợ năng. Ghi tỷ lệ hoàn thành và lỗi nhầm. Không dùng hình đẹp làm bằng chứng UX đạt.
- Tích hợp và test backend trên VM rồi thiết bị thật; đường rollback khi update branding lỗi; không thay đổi cấu hình hoặc phần mềm bên thứ ba ngoài phạm vi.
