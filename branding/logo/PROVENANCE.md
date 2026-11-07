# NaMiOS — nguồn gốc & quy tắc dùng logo

**Bộ nhận diện:** NaMiOS Logo Standard **v1.0 — "Sen bừng sáng"**, đóng gói
07/11/2026. **Chủ dự án:** Đỗ Chí Cường và Đỗ Bảo Nam.

**Nguồn:** chủ dự án cung cấp (owner-provided). `brand.json` ghi
`approval_status = "production_asset_candidate; trademark review pending"`.

## Trung thực — chưa làm (phải làm trước phát hành thương mại)

- **CHƯA** đăng ký nhãn hiệu / kết luận độc quyền. Không tuyên bố logo được cơ
  quan Nhà nước bảo trợ, cũng không tuyên bố hoa sen là biểu tượng quốc gia được
  chỉ định chính thức.
- Trước phát hành thương mại: test nhận diện mù 3 giây ở 16/32/128 px, so với các
  logo hoa sen khác, và tra cứu nhãn hiệu tương tự (README gói logo §"Chất lượng").

## Bộ màu (nguồn duy nhất = `branding/logo/04_Guide/brand.json`)

| Vai trò | Sáng → Đậm |
| --- | --- |
| Nền navy (icon/wallpaper) | `#254A60` → `#0B2034` |
| Cánh vàng | `#FFE1A1` → `#E5A53E` |
| Cánh san hô | `#FF8B6C` → `#D94D43` |
| Cánh xanh ngọc / "OS" | `#64C3AA` → `#168A82` |
| Mực chữ nền sáng | `#172C3D` |

**Màu nhấn desktop (KDE highlight/selection/focus) = JADE `#168A82`** — đổi từ
ruby `#a21f46` (màu AvaB) sang bộ màu riêng NaMiOS ngày 07/11/2026.

## Dùng ở đâu trong hệ

- **Hình nền:** `branding/wallpaper/make-wallpaper.py` → navy gradient + logo bản
  nền-tối, canh giữa → `usr/share/backgrounds/namios/namios-default.png` (hook
  `0400` ghi đè mọi wallpaper KDE bằng ảnh này).
- **Nút Bắt đầu + icon ứng dụng:** `start-here-namios` + `namios` trong
  `usr/share/icons/hicolor/<size>/apps/` (từ `02_Icons/NaMiOS_App_Icon_*`).
- **Bộ màu KDE:** `usr/share/color-schemes/NaMiOS.colors` (nhấn jade).
- **Giới thiệu hệ thống:** hook `0120` thêm `LOGO=namios` vào `/etc/os-release`.
- **Favicon/web:** `02_Icons/NaMiOS_Favicon.ico`.

## Quy tắc (rút gọn — bản đầy đủ: `branding/logo/04_Guide/README.md`)

Không bóp méo / xoay / đổi thứ tự cánh / tô màu lạ từng cánh / đặt chữ trong hình
sen. Khoảng trống quanh logo ≥ 1/8 chiều cao biểu tượng. Logo ngang ≥ 240 px;
icon < 48 px dùng bản `App_Icon_Small_Master`. Sửa hình master thì xuất lại **toàn
bộ** biến thể + tăng phiên bản, không sửa lẻ từng PNG.
