# NaMiOS — Mockup giao diện (bản thiết kế)

> **Trung thực:** đây là **bản thiết kế giao diện (mockup)** cho hướng "quen thuộc như
> Windows" của NaMiOS — **KHÔNG phải ảnh chụp hệ thống đang chạy**. Giao diện desktop
> thật dựng trên KDE Plasma; chỉ xác nhận được khi boot ISO trên VM/máy thật
> (`verified_on_boot: NO` tới lúc đó). Mockup dùng để chốt hướng nhìn/thao tác trước khi
> cấu hình KDE + theme thật.

> **Hệ thiết kế (token màu/chữ/spacing/trạng thái/từ vựng):** [`../DESIGN-SYSTEM.md`](../DESIGN-SYSTEM.md)
> (PRA-036/037/039/040). 5 màn hình chính dưới đây dùng CHUNG các token đó.

## Tệp

| Tệp | Nội dung |
| --- | --- |
| `namios-login.svg` / `.png` | Màn hình **Đăng nhập**: avatar + tên người dùng, ô mật khẩu, đồng hồ góc dưới trái, khay (VN·Telex / wifi / trợ năng / nguồn). |
| `namios-desktop.svg` / `.png` | **Màn hình chính**: taskbar dưới (nút Bắt đầu + tìm kiếm + app ghim + khay VN/wifi/loa/pin/đồng hồ), menu Bắt đầu mở (app ghim + nhóm việc Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính), icon desktop (Tệp của tôi/Máy này/Thùng rác), cửa sổ Soạn thảo văn bản (LibreOffice Writer) mở một hợp đồng, bong bóng Hỏi SmartAI. |
| `namios-apps.svg` / `.png` | **Ứng dụng** (PRA-036): danh mục app theo nhóm việc + badge *chế độ chạy* (Máy Việt/Web/Thử-Wine/Máy ảo Windows) + chip trạng thái. Thể hiện **"mở được ≠ dùng được"**: MISA mở GUI nhưng DB lỗi = ▲ Một phần; app mới tải = ■ Chưa kiểm (KHÔNG xanh); app WPF = ✕ Bị chặn. |
| `namios-devices.svg` / `.png` | **Thiết bị** (PRA-001): máy đa chức năng liệt kê **in · scan · copy · fax RIÊNG**; in+scan = ● Đạt nhưng copy/fax = ■ Chưa kiểm — chứng minh in+scan được KHÔNG tự thành copy được. |
| `namios-network.svg` / `.png` | **Mạng** (PRA-029): mỗi lỗi (sai mật khẩu / cổng đăng nhập / DNS lỗi / mất Internet) có **việc-cần-làm RIÊNG** — không "khởi động router" chung. |
| `namios-smartai.svg` / `.png` | **SmartAI — Bảng tác vụ** (PRA-032/038): thang tiến độ *đã gửi hàng đợi → máy báo xong → **bạn** xác nhận đã nhận*; "nhấn nút ≠ xong"; ô Quyền đã cấp (hết hạn + Hoàn tác) + Nguồn kết quả + bước bị chặn + Chi tiết cho kỹ thuật viên. |

## Nguyên tắc thiết kế

- **Quen thuộc như Windows** về bố cục + thao tác (taskbar dưới, nút Bắt đầu trái, khay phải,
  nhấp đúp mở tệp) — NHƯNG **không sao chép biểu tượng/phông/thương hiệu Microsoft** (ràng buộc
  pháp lý, đúng SYS-006). Mọi icon là vector tự vẽ; phông là Noto Sans.
- **Tiếng Việt chỉnh chu** toàn bộ; bộ gõ Telex mặc định; định dạng ngày/giờ/tiền VN.
- **Phân nhóm theo việc** (Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính) — khớp
  `namios_eco` + menu Bắt đầu SYS-003.
- **SmartAI là trợ lý, không chiếm quyền**: bong bóng "Hỏi SmartAI" phụ trợ; desktop dùng được
  khi AI tắt (SYS-035).

## Dựng lại ảnh từ SVG

```bash
# cần Node + @resvg/resvg-js + một phông có tiếng Việt (vd Noto Sans)
node render.js namios-login.svg namios-login.png 1920
```
