# NaMiOS — Mockup giao diện (bản thiết kế)

> **Trung thực:** đây là **bản thiết kế giao diện (mockup)** cho hướng "quen thuộc như
> Windows" của NaMiOS — **KHÔNG phải ảnh chụp hệ thống đang chạy**. Giao diện desktop
> thật dựng trên KDE Plasma; chỉ xác nhận được khi boot ISO trên VM/máy thật
> (`verified_on_boot: NO` tới lúc đó). Mockup dùng để chốt hướng nhìn/thao tác trước khi
> cấu hình KDE + theme thật.

## Tệp

| Tệp | Nội dung |
| --- | --- |
| `namios-login.svg` / `.png` | Màn hình **Đăng nhập**: avatar + tên người dùng, ô mật khẩu, đồng hồ góc dưới trái, khay (VN·Telex / wifi / trợ năng / nguồn). |
| `namios-desktop.svg` / `.png` | **Màn hình chính**: taskbar dưới (nút Bắt đầu + tìm kiếm + app ghim + khay VN/wifi/loa/pin/đồng hồ), menu Bắt đầu mở (app ghim + nhóm việc Văn phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính), icon desktop (Tệp của tôi/Máy này/Thùng rác), cửa sổ Soạn thảo văn bản (LibreOffice Writer) mở một hợp đồng, bong bóng Hỏi SmartAI. |

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
