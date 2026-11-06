# NaMiOS — Mockup giao diện (bản thiết kế)

> **Trung thực:** đây là **bản thiết kế giao diện (mockup)** cho hướng "quen thuộc như
> Windows" của NaMiOS — **KHÔNG phải ảnh chụp hệ thống đang chạy**. Giao diện desktop
> thật dựng trên KDE Plasma; chỉ xác nhận được khi boot ISO trên VM/máy thật
> (`verified_on_boot: NO` tới lúc đó). Mockup dùng để chốt hướng nhìn/thao tác trước khi
> cấu hình KDE + theme thật, hoặc trước khi code hoá các luồng Phụ lục 10/11.

> **Hệ thiết kế (token màu/chữ/spacing/trạng thái/từ vựng):** [`../DESIGN-SYSTEM.md`](../DESIGN-SYSTEM.md)
> (PRA-036/037/039/040). Mọi màn hình dưới đây — PL06 (5 màn) lẫn PL10/PL11 (8 màn) —
> dùng CHUNG các token đó: khung cửa sổ/taskbar, 5 trạng thái (`Sẵn sàng` xanh ·
> `Có giới hạn`/`Một phần` vàng · `Pilot` kim cương ruby · `Bị chặn` đỏ · `Chưa kiểm` xám),
> và nhãn chữ luôn đi kèm icon (không truyền thông tin chỉ bằng màu).

## Tệp — 5 màn hình chính (PL06, PRA-036 §7)

| Tệp | Nội dung |
| --- | --- |
| `namios-login.svg` / `.png` | Màn hình **Đăng nhập**: avatar + tên người dùng, ô mật khẩu, đồng hồ góc dưới trái, khay (VN·Telex / wifi / trợ năng / nguồn). |
| `namios-desktop.svg` / `.png` | **Màn hình chính**: taskbar dưới (nút Bắt đầu + tìm kiếm + app ghim + khay VN/wifi/loa/pin/đồng hồ), menu Bắt đầu mở (app ghim + nhóm việc Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính), icon desktop (Tệp của tôi/Máy này/Thùng rác), cửa sổ Soạn thảo văn bản (LibreOffice Writer) mở một hợp đồng, bong bóng Hỏi SmartAI. |
| `namios-apps.svg` / `.png` | **Ứng dụng** (PRA-036): danh mục app theo nhóm việc + badge *chế độ chạy* (Máy Việt/Web/Thử-Wine/Máy ảo Windows) + chip trạng thái. Thể hiện **"mở được ≠ dùng được"**: MISA mở GUI nhưng DB lỗi = ▲ Một phần; app mới tải = ■ Chưa kiểm (KHÔNG xanh); app WPF = ✕ Bị chặn. |
| `namios-devices.svg` / `.png` | **Thiết bị** (PRA-001): máy đa chức năng liệt kê **in · scan · copy · fax RIÊNG**; in+scan = ● Đạt nhưng copy/fax = ■ Chưa kiểm — chứng minh in+scan được KHÔNG tự thành copy được. |
| `namios-network.svg` / `.png` | **Mạng** (PRA-029): mỗi lỗi (sai mật khẩu / cổng đăng nhập / DNS lỗi / mất Internet) có **việc-cần-làm RIÊNG** — không "khởi động router" chung. |
| `namios-smartai.svg` / `.png` | **SmartAI — Bảng tác vụ** (PRA-032/038): thang tiến độ *đã gửi hàng đợi → máy báo xong → **bạn** xác nhận đã nhận*; "nhấn nút ≠ xong"; ô Quyền đã cấp (hết hạn + Hoàn tác) + Nguồn kết quả + bước bị chặn + Chi tiết cho kỹ thuật viên. |

## Tệp — Phụ lục 10: Chuyển đổi từ Windows (6 màn, N10-xxx)

> Nguồn yêu cầu: `docs giao việc` Phụ lục 10 §1.2/1.3/1.5/1.6/4 (mã N10-007…N10-051).
> Máy mẫu xuyên suốt 6 màn: **KT-VP-014**, phòng Kế toán, Windows 10 Pro 22H2.

| Tệp | Nội dung | Nguyên tắc trung thực thể hiện |
| --- | --- | --- |
| `namios-migration-assessor.svg` | **NaMi Migration Assessor** (N10-007): quét máy Windows — 3 thẻ tổng quan (ứng dụng/thiết bị/tệp), bảng xem trước ứng dụng đã cài, danh sách thiết bị ngoại vi, nút xuất báo cáo. | Khối **"Những gì KHÔNG được thu thập"** nổi bật bằng dấu ✕ đỏ: mật khẩu, cookie, khóa riêng `.p12`, nội dung tệp — chỉ liệt kê những gì *tồn tại*, không lấy bí mật. |
| `namios-readiness-report.svg` | **Báo cáo sẵn sàng chuyển đổi** (N10-009): kết luận máy lớn ở đầu trang + bảng 12 hành trình (N10-031) với 5 trạng thái `Sẵn sàng/Có giới hạn/Pilot/Bị chặn/Chưa kiểm`. | 11/12 việc đạt/gần đạt nhưng **1 việc thiết yếu (ký số hóa đơn) bị chặn → kết luận máy vẫn là BỊ CHẶN** — banner "không quy đổi phần trăm trung bình". |
| `namios-compat-route.svg` | **Chọn tuyến ứng dụng** (N10-017): 4 thẻ tuyến (Máy Việt/Web/Thử-Wine/Windows có phép) cho MISA SME.VN + bảng **thao tác × tuyến tốt nhất**. | Banner "mở được KHÔNG đồng nghĩa ký được": mở GUI đạt qua Thử-Wine, nhưng ký số hóa đơn bị chặn ở Wine → phải dùng tuyến Windows có phép riêng cho đúng MỘT thao tác đó. |
| `namios-device-token-functions.svg` | **Thiết bị — Máy in & Token chữ ký số theo chức năng** (N10-047/024): 2 khối bảng — máy in (In/Scan/Copy/Fax) và USB Token (Nhận diện/Đọc chứng thư/Ký/Xác minh), mỗi dòng kiểm riêng. | "Nhận diện thiết bị (VID/PID)" = Đạt nhưng "Ký số tài liệu" = Bị chặn (thiếu middleware Linux) — nhận diện được KHÔNG đồng nghĩa dùng được. |
| `namios-ai-task-evidence.svg` | **SmartAI — Việc AI đang làm** (N10-040/041/043): 4 khối đánh số theo đúng thứ tự **Ý định → Bước → Bằng chứng → Nút quay lại**, ví dụ "Nộp tờ khai thuế thử (eTax)". | Khối 3 phân biệt bằng chứng ĐỦ (hash tệp) và CHƯA ĐỦ (ảnh chụp màn hình chưa có mã biên nhận); khối 4 nói rõ bước nào **không thể** thu hồi dù có nút "Hoàn tác". |
| `namios-recovery.svg` | **NaMi Recovery — Cứu hộ & khôi phục** (N10-051/016): banner kết quả rollback tự động, dòng thời gian 5 bước (bước 4 thất bại màu đỏ, bước 5 tự phục hồi màu xanh), khối "An toàn dữ liệu" + 4 lựa chọn tiếp theo. | Cập nhật lỗi → **tự rollback thành công, tệp cá nhân không đổi**; ghi rõ "không cần SmartAI hay mạng" để cứu hộ — đối lập với một màn hình chỉ báo lỗi chung chung. |

## Tệp — Phụ lục 11: Bộ ứng dụng tích hợp & cập nhật (2 màn, APP11-xxx)

> Nguồn yêu cầu: Phụ lục 11 §2/3.1/3.2/4 (mã APP11-001…APP11-036).

| Tệp | Nội dung | Nguyên tắc trung thực thể hiện |
| --- | --- | --- |
| `namios-my-apps-launcher.svg` | **"Ứng dụng của tôi"** (APP11-001): Launcher theo 5 nhóm — Làm việc / Liên lạc / Học tập & Giải trí / Thiết bị / An toàn, mỗi ô app có nhãn phụ `Cài trên máy` / `Dịch vụ web — Bên thứ ba` / `Qua Wine — đã kiểm`. | KHÔNG dùng logo Zalo/Facebook/YouTube — dịch vụ bên thứ ba hiện bằng icon tự vẽ trung tính + nhãn chữ "Dịch vụ web — Bên thứ ba" (SYS-006/APP11-033). |
| `namios-update-center.svg` | **NaMi Update Center** (APP11-013/019): bảng 7 hàng (Hệ điều hành/Bảo mật/Browser/Office/Bộ gõ/Wine recipe) + khối "Dịch vụ web" riêng cho Zalo Web/YouTube/Facebook. | Thành phần cài máy có số phiên bản thật; dịch vụ web ghi **"Được nhà cung cấp cập nhật trực tuyến"** và chỉ có kết quả *kiểm tra tự động* — không bịa số phiên bản cài trên máy cho web app. |

## Nguyên tắc thiết kế

- **Quen thuộc như Windows** về bố cục + thao tác (taskbar dưới, nút Bắt đầu trái, khay phải,
  nhấp đúp mở tệp) — NHƯNG **không sao chép biểu tượng/phông/thương hiệu Microsoft** (ràng buộc
  pháp lý, đúng SYS-006). Mọi icon là vector tự vẽ; phông là Noto Sans.
- **Tiếng Việt chỉnh chu** toàn bộ; bộ gõ Telex mặc định; định dạng ngày/giờ/tiền VN.
- **Phân nhóm theo việc** (Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính) — khớp
  `namios_eco` + menu Bắt đầu SYS-003.
- **SmartAI là trợ lý, không chiếm quyền**: bong bóng "Hỏi SmartAI" phụ trợ; desktop dùng được
  khi AI tắt (SYS-035).
- **Mỗi màn PL10/PL11 chỉ minh hoạ MỘT bất biến trung thực** (mở ≠ xong · web ≠ đã cài ·
  thiếu bằng chứng = chưa xác nhận) bằng ví dụ cụ thể có số liệu, không chỉ chữ "lưu ý" chung chung.
- **Không nhúng logo/biểu tượng thương mại** của bên thứ ba (Zalo/Facebook/YouTube…) — dịch vụ
  ngoài NaMiOS luôn hiện bằng icon tự vẽ trung tính + nhãn chữ rõ nguồn (APP11-033).

8 tệp `.svg` của Phụ lục 10/11 ở trên hiện **chưa có `.png` đi kèm** (khác với 5 màn PL06) — dùng
lệnh dưới để tự dựng ảnh khi cần xem nhanh hoặc đính kèm báo cáo.

## Dựng lại ảnh từ SVG

```bash
# Cách 1 — cần Node + @resvg/resvg-js + một phông có tiếng Việt (vd Noto Sans)
node render.js namios-login.svg namios-login.png 1920

# Cách 2 — không cần cài gì sẵn, dùng resvg-cli qua npx (đã dùng để kiểm 8 màn PL10/PL11)
npx --yes resvg-cli --fit-width 1600 --no-system-font \
  --font-file /path/to/NotoSans-Regular.ttf --font-file /path/to/NotoSans-Bold.ttf \
  --font-default-family "Noto Sans" \
  namios-update-center.svg namios-update-center.png
```
