# NaMiOffice — đổi tên hiển thị LibreOffice

**Yêu cầu:** Cuong (09/11/2026): *"libreoffice đổi tên NaMiOffice"*.
**Trạng thái:** `partial` — rebrand mức hiển thị đã dựng (dev/ISO), CHƯA build lại mã nguồn LibreOffice. QEMU-only cho tới pilot máy thật (nhóm B). `verified_on_host: NO`.

## Làm được gì (người dùng THẤY "NaMiOffice")

| Chỗ | Trước | Sau | Cơ chế |
|-----|-------|-----|--------|
| Menu Bắt đầu + thanh tác vụ | LibreOffice Calc/Writer… | **NaMiWriter / NaMiSheet / NaMiSlides** (+ NaMiDraw/NaMiData/NaMiMath); suite = NaMiOffice — xem [NAMIOFFICE-APPS.md](NAMIOFFICE-APPS.md) | sửa `Name=`/`Name[vi]=` trong `/usr/share/applications/libreoffice-*.desktop` (hook `0450`) |
| Màn splash khởi động | logo LibreOffice | splash **NaMiOffice** nền ngà + sen (`intro.png`) | chép đè `…/program/intro.png` |
| Nền hộp thoại *Giới thiệu* (About) | nền LibreOffice | logo **NaMiOffice** nền ngà (`about.svg`/`about.png`) | chép đè `…/program/shell/about.svg` |

Ảnh sinh bằng `branding/office/make-namioffice-brand.py` (PIL, bộ nhận diện Sen Việt v2). **Quy tắc kiêng kỵ:** hoa sen/logo KHÔNG BAO GIỜ đặt trên nền đen — mọi asset office dùng nền ngà (ivory). Ảnh gốc ở `branding/office/out/`, ship vào chroot tại `…/usr/share/namios/office-brand/`.

## CHƯA làm được (vẫn còn chữ "LibreOffice") — nói thẳng

- **Tiêu đề cửa sổ** (title bar) và **dòng chữ trong hộp About** ("LibreOffice 25.x", "Build ID…") đến từ chuỗi `ProductName` **biên dịch sẵn** trong binary. Chỉ đổi 100% khi **build lại LibreOffice từ mã nguồn** với `--with-vendor="NaMiOS"` + `PRODUCTNAME="NaMiOffice"` (hoặc vá resource). Đây là tầng lớn (vài giờ build, toolchain riêng) — **xếp sau**, không gắn nhãn hoàn thành ở bước này.
- Phần mở rộng/Trợ giúp (Help) có thể còn tham chiếu "LibreOffice".

## Bản quyền & nhãn hiệu (phải giữ)

LibreOffice do **The Document Foundation (TDF)** phát hành theo **MPL-2.0 / LGPL-3.0+**. Giấy phép **cho phép** tạo bản chỉnh sửa và **đổi tên**; chính sách nhãn hiệu TDF còn **yêu cầu** bản đã sửa phải đổi tên (không được tiếp tục gọi là "LibreOffice"). Vì vậy:

- Giữ dòng tín dụng **"dựa trên LibreOffice (The Document Foundation)"** trong splash + About (đã có).
- Không tuyên bố NaMiOffice do TDF phát hành.

## Nguồn xác minh / điều cần kiểm trên máy thật

- Đường dẫn branding (`program/intro.png`, `program/shell/about.svg`) theo tài liệu cộng đồng TDF + bố cục gói Debian `libreoffice-core`. Hook dò nhiều đường dẫn (`/usr/lib/libreoffice`, `/usr/lib64/…`, `/opt/libreoffice*`) và bỏ qua an toàn nếu không thấy.
- **Cần kiểm khi boot thật:** (1) menu hiện "NaMiOffice …"; (2) splash NaMiOffice khi mở app; (3) About hiện nền NaMiOffice. Nếu splash không đổi, có thể bản dựng LibreOffice đọc intro từ `brand` package khác — ghi lại để chỉnh đường dẫn trong hook.

## Tái lập

```sh
python3 branding/office/make-namioffice-brand.py   # sinh lại 3 ảnh
# hook 0450-namioffice-brand.hook.chroot áp lúc build chroot
```
