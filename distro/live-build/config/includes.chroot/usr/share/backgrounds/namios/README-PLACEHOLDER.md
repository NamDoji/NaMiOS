# NaMiOS wallpaper mặc định — CÓ bản SVG tạm, còn thiếu bản raster chính thức

**Cập nhật (việc desktop "giống Windows", 02/11/2026):** đã thêm
`namios-default.svg` — hình nền vector tự soạn (gradient + hình khối đồng
tâm, màu thương hiệu NaMiOS `#951F3D`), KHÔNG sao chép pixel/icon/font của
Microsoft hay bên thứ ba nào (LIC-004). File SVG hợp lệ cú pháp XML (đã kiểm
bằng `xml.dom.minidom`), nhưng **verified_on_host: NO** — chưa xác nhận hiển
thị đúng trên Plasma wallpaper plugin `org.kde.image` trên desktop KDE Plasma
thật (Debian 13 trixie). Đây vẫn là hình nền **mặc định tạm**, không phải
branding chính thức cuối cùng của dự án — logo/icon set NaMiOS chính thức vẫn
TBD (xem `usr/share/namios-branding/README-PLACEHOLDER.md`).

## Còn thiếu (TBD)

- Bản raster độ phân giải cao (`.png`/`.jpg`, khuyến nghị ≥ 1920×1080, có thể
  xuất lại từ `namios-default.svg` bằng công cụ render SVG thật trên máy có
  công cụ đó — container phát triển hiện tại không có công cụ render ảnh để
  tự xuất PNG, chỉ xác nhận được cú pháp XML).
- Cấu hình trỏ Plasma `lookandfeel`/theme mặc định tới đúng file này (cấu
  hình container `[Containments][1]` `wallpaperplugin=org.kde.image` đã có
  trong `etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc`, nhưng
  đường dẫn ảnh cụ thể do plugin `org.kde.image` tự lưu vào config riêng của
  nó lúc chạy thật — CHƯA xác nhận trỏ đúng `namios-default.svg` trên desktop
  thật).

KHÔNG dùng wallpaper có watermark/logo của bên thứ ba không có quyền
phân phối lại.
