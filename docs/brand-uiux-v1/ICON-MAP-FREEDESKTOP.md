# Ánh xạ 24 icon NaMiOS sang tên Freedesktop/KDE

**Ngày:** 09/11/2026
**Phạm vi:** chỉ phần icon trong nhánh B (Desktop assets) của `04_PROMPT_CLAUDE_CODE.md` — KHÔNG đụng 20 hình nền (đã tích hợp sẵn ở `/usr/share/wallpapers/NaMiOS-*`).
**Nguyên tắc trung thực:** `verified_on_host: NO` cho toàn bộ nội dung dưới đây — chưa có máy KDE/Plasma thật nào tra icon theme này qua `QIcon::fromTheme()`/`kbuildsycoca` để xác nhận glyph thật sự hiện ra đúng tên, đúng theo breeze palette khi `Inherits=breeze`. Mọi khẳng định “đọc được ở 16px” dưới đây đến từ một pipeline xem trước tự dựng (mục 4), không phải ảnh chụp màn hình KDE thật.

## 1. Vị trí tích hợp

```
distro/live-build/config/includes.chroot/usr/share/icons/NaMiOS-Symbolic/
├── index.theme                     # Inherits=breeze,hicolor; 8 thư mục ngữ cảnh
├── 16x16/devices/                  # override Fixed Size=16 cho 2 icon cần đơn giản hoá
│   ├── drive-removable-media-usb.svg   (bản 16px đơn giản hoá)
│   ├── scanner.svg                      (bản 16px đơn giản hoá)
│   └── usb.svg -> drive-removable-media-usb.svg   (symlink alias)
└── scalable/{actions,apps,categories,devices,mimetypes,places,status}/
    24 file .svg chính (bản sao nguyên văn từ branding/icons-system-v1/)
    + 22 symlink alias giữ tên gốc
```

Nguồn giữ nguyên, không sửa: `branding/icons-system-v1/*.svg` (24 icon 24×24, `stroke="currentColor"`, `fill="none"`, stroke-width 1.9).

Theme kế thừa `breeze,hicolor` — khi KDE/Qt tra một tên icon không có trong 24 icon này (vd icon app của Firefox, LibreOffice…), icon engine sẽ rơi xuống breeze/hicolor như bình thường; theme này **không che/ghi đè** icon ứng dụng bên thứ ba.

## 2. Bảng ánh xạ

| # | Tên gốc (nguồn) | Tên Freedesktop/KDE chính | Ngữ cảnh | File chính | Alias giữ tên gốc |
|---|---|---|---|---|---|
| 1 | printer | `printer` | Devices | `scalable/devices/printer.svg` | (trùng tên, không cần alias) |
| 2 | scanner | `scanner` | Devices | `scalable/devices/scanner.svg` | (trùng tên) — **có bản 16px riêng** |
| 3 | wifi | `network-wireless` | Devices | `scalable/devices/network-wireless.svg` | `scalable/devices/wifi.svg` |
| 4 | ethernet | `network-wired` | Devices | `scalable/devices/network-wired.svg` | `scalable/devices/ethernet.svg` |
| 5 | bluetooth | `preferences-system-bluetooth` | Categories | `scalable/categories/preferences-system-bluetooth.svg` | `scalable/categories/bluetooth.svg` |
| 6 | settings | `configure` (+ `preferences-system`) | Actions / Categories | `scalable/actions/configure.svg` | `scalable/actions/settings.svg`, `scalable/categories/preferences-system.svg` |
| 7 | folder | `folder` | Places | `scalable/places/folder.svg` | (trùng tên) |
| 8 | trash | `user-trash` | Places | `scalable/places/user-trash.svg` | `scalable/places/trash.svg` |
| 9 | document | `text-x-generic` | MimeTypes | `scalable/mimetypes/text-x-generic.svg` | `scalable/mimetypes/document.svg` |
| 10 | pdf | `application-pdf` | MimeTypes | `scalable/mimetypes/application-pdf.svg` | `scalable/mimetypes/pdf.svg` |
| 11 | image | `image-x-generic` | MimeTypes | `scalable/mimetypes/image-x-generic.svg` | `scalable/mimetypes/image.svg` |
| 12 | music | `audio-x-generic` | MimeTypes | `scalable/mimetypes/audio-x-generic.svg` | `scalable/mimetypes/music.svg` |
| 13 | camera | `camera-photo` | Devices | `scalable/devices/camera-photo.svg` | `scalable/devices/camera.svg` |
| 14 | usb | `drive-removable-media-usb` | Devices | `scalable/devices/drive-removable-media-usb.svg` | `scalable/devices/usb.svg` — **có bản 16px riêng** |
| 15 | update | `system-software-update` | Actions | `scalable/actions/system-software-update.svg` | `scalable/actions/update.svg` |
| 16 | security | `security-high` | Status | `scalable/status/security-high.svg` | `scalable/status/security.svg` |
| 17 | help | `help-contents` | Actions | `scalable/actions/help-contents.svg` | `scalable/actions/help.svg` |
| 18 | error | `dialog-error` | Status | `scalable/status/dialog-error.svg` | `scalable/status/error.svg` |
| 19 | warning | `dialog-warning` | Status | `scalable/status/dialog-warning.svg` | `scalable/status/warning.svg` |
| 20 | success | `dialog-ok`* | Status | `scalable/status/dialog-ok.svg` | `scalable/status/success.svg` |
| 21 | backup | `document-save` | Actions | `scalable/actions/document-save.svg` | `scalable/actions/backup.svg` |
| 22 | browser | `web-browser` | Applications | `scalable/apps/web-browser.svg` | `scalable/apps/browser.svg` |
| 23 | app-center | `system-software-install` | Actions | `scalable/actions/system-software-install.svg` | `scalable/actions/app-center.svg` |
| 24 | smart-ai | `namios-smartai`** | Applications | `scalable/apps/namios-smartai.svg` | `scalable/apps/smart-ai.svg` |

\* `dialog-ok` không nằm trong bảng chính thức của Freedesktop Icon Naming Specification (bảng Status chỉ có `dialog-error/information/password/question/warning`), nhưng là tên quy ước phổ biến trong nhiều theme KDE/GTK (dùng chung với `dialog-error`/`dialog-warning` cho nhất quán 3 trạng thái). Ghi nhận ở đây để không tự nhận là chuẩn spec.
\*\* `namios-smartai` là tên riêng của NaMiOS (không có icon SmartAI chuẩn Freedesktop); đặt ở ngữ cảnh Applications vì đại diện cho trợ lý/app SmartAI.

Tất cả alias là **symlink tương đối thật** (không phải file trùng lặp nội dung), đã kiểm tồn tại đích (`find -type l` + `test -e`, 23/23 alias trỏ đúng, 0 gãy).

## 3. Icon cần bản 16px đơn giản hoá riêng

Theo `03_NaMiOS_Brand_UIUX_Design_System.md` §4: *“nếu biểu tượng không phân biệt được ở 16px thì có bản symbolic giản lược riêng”*. Sau khi xem trước (mục 4), hai icon không đọc được ở 16px bằng glyph gốc:

- **usb** (`drive-removable-media-usb`): glyph gốc là biểu trưng USB 3 nhánh (trident) với 2 hình chữ nhật nhỏ ở đầu nhánh — ở 16px các nhánh/đầu mút chụm lại thành một vệt không phân biệt được là USB. **Bản 16px thay bằng hình ổ USB (nắp hẹp + thân rộng + 2 vạch khe)** — dễ nhận ở cỡ nhỏ hơn biểu trưng trident. File: `16x16/devices/drive-removable-media-usb.svg`.
- **scanner**: glyph gốc (nắp hình thang + đáy + 2 vạch trong) dồn thành một khối tròn/mái vòm đặc ở 16px, dễ nhầm hộp/chuông. **Bản 16px rút còn 2 hình: nắp hình thang trên + thân chữ nhật có khe hở** để giữ im lặng thị giác giữa 2 khối. File: `16x16/devices/scanner.svg`.

Cả hai bản 16px đã qua 2 vòng thử (vòng 1 vẫn chưa đạt — glyph usb vòng 1 teo thành mũi tên trơn, không còn đọc được là USB; đã sửa vòng 2). Bản 24/32px vẫn dùng glyph gốc nguyên văn (không đổi).

**Borderline — chưa đủ chứng cứ để khẳng định cần sửa, cần mắt người xem trên KDE thật:**
- `backup`: hộp + mũi tên bên trong hơi rối ở 16px nhưng mũi tên còn phân biệt được qua giả lập; để nguyên.
- `document` vs `pdf`: silhouette gần như giống hệt nhau ở 16px (khác biệt là 1 dòng kẻ phụ trong nội dung) — đây là giới hạn thiết kế gốc, không phải lỗi riêng ở bước này; nêu để nhóm thiết kế icon xem lại khi làm bộ MIME-type đầy đủ.
- `settings` (configure): 8 vạch răng quanh vòng tròn co lại nhưng vẫn tạo được cảm giác “bánh răng”; chấp nhận được, không tạo bản riêng.

## 4. Phương pháp xem trước 16/24/32px (trung thực về công cụ)

Sandbox này **không có `cairosvg`/`libcairo` khả dụng** (thiếu `libcairo.so.2`, không có quyền `apt-get install`/root để cài hệ thống) và cũng không có `rsvg-convert`/`inkscape`. Theo đúng hướng dẫn (“IF available, else just note…”), thay vì chỉ ghi chú suông, đã dựng một pipeline xem trước thay thế bằng thư viện Python thuần (không cần thư viện hệ thống):

- `svgpathtools` (thuần Python) để phân giải `path`/`rect`/`circle`/`ellipse` kể cả cung tròn (`A`/`a`) và nhiều subpath trong một thuộc tính `d`.
- `matplotlib` backend `Agg` (bundle C extension riêng, không qua cairo) để rasterize ra PNG đúng 16×16/24×24/32×32 px với `stroke-width` tỉ lệ đúng theo kích thước.

Trong lúc dựng, phát hiện và sửa 1 lỗi trong chính script xem trước: tách subpath theo kiểu cắt chuỗi `d` thủ công làm sai toán quãng “moveto tương đối” (`m` nối tiếp sau subpath trước) — icon `error`, `printer`, `scanner`, `settings`, `trash`, `update`, `warning`, `help`, `security` từng hiện sai hình (vd `error` ra hình “cấm” một vạch thay vì hình X hai vạch). Đã sửa bằng `Path.continuous_subpaths()` của `svgpathtools` (tính đúng toạ độ tuyệt đối trước khi tách), dựng lại toàn bộ 24×3 ảnh, so khớp lại bằng mắt qua contact-sheet phóng 10× mới kết luận như mục 3. Đây là **giả lập gần đúng** (không anti-alias/hinting như renderer thật của Qt/Skia dùng trong KDE) — đủ để bắt lỗi chồng nét/giao nhau cấu trúc, nhưng **không thay thế** việc xem trên màn KDE thật ở mục 5.

Toàn bộ 24 SVG gốc + 2 SVG 16px mới đã qua `xml.dom.minidom.parse()` — **26/26 file thật là XML hợp lệ, 0 lỗi**.

## 5. Còn phải làm trên máy thật (verified_on_host: NO)

- Copy `NaMiOS-Symbolic/` vào `~/.local/share/icons/` hoặc build ISO, chạy `kbuildsycoca6`/đăng xuất-đăng nhập, rồi dùng `QIcon::fromTheme("configure")` (hoặc Kiconthemes' `kiconfinder`/Spectacle chụp menu) để xác nhận glyph thật sự hiện ra, đúng màu theo `currentColor`/breeze palette ở cả nền sáng và tối.
- Test ở 16/24/32/48px **trên màn hình thật** (không phải giả lập) theo đúng yêu cầu spec 03 §4, đặc biệt 2 icon vừa đơn giản hoá (usb, scanner) và 3 icon borderline (mục 3).
- Test tại 1366×768, 1920×1080, 2560×1440 và scale 100/150/200% theo `04_PROMPT_CLAUDE_CODE.md`.
- Theo spec 03 §4: 24 icon hiện tại vẫn là **“bộ hạt giống”** — trước khi release chính thức cần làm thêm icon cho folder loại khác, MIME type mở rộng, action, device, status đầy đủ hơn, và review với người dùng thật (chưa làm ở bước này, ngoài phạm vi 24 icon được giao).

## 6. Ranh giới — không đụng icon bên thứ ba

Icon trong `NaMiOS-Symbolic/` chỉ là 24 icon chức năng hệ thống (mạng, thiết bị, trạng thái, tệp...). **Không tạo, không ghi đè** icon cho Firefox, LibreOffice, Zalo, Thunderbird hay bất kỳ ứng dụng bên thứ ba nào — các icon đó tiếp tục lấy từ gói ứng dụng gốc hoặc theme `NaMiOS-Lotus`/`hicolor` đã có sẵn trong repo (`usr/share/icons/NaMiOS-Lotus/{48,64,128,256}x256/apps/firefox*.png`, `libreoffice-*.png`...). Việc này giữ đúng nguyên tắc spec 03 mục 4: *“Icon chỉ là ký hiệu chức năng, không thay logo thương mại… mà chưa có quyền.”*
