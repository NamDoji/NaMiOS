# NaMi — Bộ icon ứng dụng "Đông Sơn" (rollout toàn hệ điều hành)

**verified_on_host: NO** — render trong sandbox; chưa xác nhận hiển thị trên
Dolphin/Start menu/Plasma thật (cần boot QEMU hoặc máy thật + `kbuildsycoca6` +
`gtk-update-icon-cache`/`update-icon-caches`).

Phong cách (duyệt ở teaser v4, Cuong #18397 "Ok"): ô squircle macOS + motif
Trống Đồng Đông Sơn mờ (vành chấm đồng + tia mặt trời) + glyph chức năng TRẮNG
sạch. App **Trợ lý** = mặt trời 12 tia vàng (biểu tượng thương hiệu).

- Generator: `branding/dongson-v3-render/make_app_icons_dongson_full.py`
  (import helper từ `make_app_icons_dongson_v4.py` + `make_app_icons_macos_v3.py`).
- Contact sheet: `branding/dongson-v3-render/app-icons-dongson-preview/full-set.png`
- 36 thiết kế glyph → **63 tên icon** (gồm alias) → **506 file PNG**
  (378 file NaMiOS-Lotus 6 cỡ 32/48/64/128/256/512 + 128 lần GHI ĐÈ entry
  hicolor đã tồn tại; KHÔNG tạo tên/thư mục hicolor lạc).
- Đã THÊM `32x32/apps` vào `NaMiOS-Lotus/index.theme` (Directories + section).

## Bảng ánh xạ (app → icon-name → cỡ → màu ô)

Cỡ: **L** = NaMiOS-Lotus (luôn 32·48·64·128·256·512). **H** = hicolor (chỉ các
cỡ đã có sẵn, ghi đè).

| App (nhãn) | icon-name(s) | Cỡ đã ghi | Màu ô |
|---|---|---|---|
| Trợ lý (nAssistant) | `namios`, `namios-assistant` | L 32–512 · H `namios` 16–512 | navy + mặt trời vàng (hero) |
| Văn bản — Writer | `libreoffice-writer`, `libreoffice-oasis-text`, `ooo-writer`, `namioffice-writer` | L 32–512 · H `namioffice-writer` 48–512 | blue |
| Bảng tính — Calc | `libreoffice-calc`, `libreoffice-oasis-spreadsheet`, `ooo-calc`, `namioffice-calc` | L 32–512 · H `namioffice-calc` 48–512 | green |
| Trình chiếu — Impress | `libreoffice-impress`, `libreoffice-oasis-presentation`, `ooo-impress`, `namioffice-impress` | L 32–512 · H `namioffice-impress` 48–512 | vermilion |
| Vẽ — Draw | `libreoffice-draw`, `libreoffice-oasis-drawing`, `namioffice-draw` | L 32–512 · H `namioffice-draw` 48–512 | gold |
| Cơ sở dữ liệu — Base | `libreoffice-base`, `namioffice-base` | L 32–512 · H `namioffice-base` 48–512 | teal |
| Công thức — Math | `libreoffice-math`, `namioffice-math` | L 32–512 · H `namioffice-math` 48–512 | slate |
| Văn phòng — Start Center | `libreoffice-startcenter`, `libreoffice-main`, `namioffice-startcenter` | L 32–512 | navy |
| Trình duyệt | `internet-web-browser` | L 32–512 | teal |
| Tệp — Dolphin | `system-file-manager`, `org.kde.dolphin` | L 32–512 | gold |
| Cài đặt — Bảng điều khiển | `preferences-system`, `systemsettings` | L 32–512 · H `preferences-system` 16–512 | graphite |
| Cửa hàng — Discover | `plasmadiscover`, `plasma-discover`, `org.kde.discover` | L 32–512 · H cả 3 tên 16–512 | blue |
| Cập nhật | `system-software-update` | L 32–512 · H 16–512 | teal |
| An toàn | `security-high` | L 32–512 | vermilion |
| Cổng Dịch vụ | `namios-services` | L 32–512 | gold |
| Máy chiếu | `video-display` | L 32–512 | navy |
| Màn hình (hiển thị) | `preferences-desktop-display` | L 32–512 | graphite |
| Chẩn đoán | `namios-diagnostics` | L 32–512 | teal |
| Hướng dẫn | `namios-guide`, `help-contents` | L 32–512 | blue |
| Chạy phần mềm Windows | `namios-run` | L 32–512 | slate |
| Hỏi AI | `namios-ai` | L 32–512 | navy |
| Lịch | `namios-calendar` | L 32–512 | red |
| Thiết bị / Kết nối | `preferences-desktop-peripherals`, `namios-connect` | L 32–512 | teal |
| Tài khoản | `system-users` | L 32–512 | teal |
| Ứng dụng | `preferences-desktop-default-applications` | L 32–512 | slate |
| Mạng | `preferences-system-network` | L 32–512 | blue |
| Cá nhân hoá | `preferences-desktop-theme` | L 32–512 | vermilion |
| Thời gian & Ngôn ngữ | `preferences-system-time` | L 32–512 | blue |
| Cài hệ điều hành — Calamares | `system-software-install` | L 32–512 | teal |
| Dòng lệnh — Konsole | `utilities-terminal`, `konsole`, `org.kde.konsole` | L 32–512 · H cả 3 tên 16–512 | graphite |
| PDF — Okular | `okular` | L 32–512 · H 16–512 | vermilion |
| Ảnh — Gwenview | `image-viewer`, `gwenview`, `org.kde.gwenview` | L 32–512 | teal |
| Media — VLC/Haruna | `vlc`, `haruna` | L 32–512 · H cả 2 tên 16–512 | gold |
| Nhạc — Elisa | `elisa` | L 32–512 · H 16–512 | gold |
| Lưu trữ — Ark | `ark` | L 32–512 · H 16–512 | slate |
| Máy in | `printer` | L 32–512 | blue |

## Đã sửa `.desktop` để KÍCH HOẠT icon riêng (working tree)

Mọi `namios-*.desktop` trước đây dùng chung `Icon=namios` (index.theme ghi rõ:
"cần apps-dev đổi Icon= nếu muốn kích hoạt icon riêng"). Đã đổi `Icon=`:

| .desktop | Icon cũ | Icon mới |
|---|---|---|
| namios-chan-doan | namios | `namios-diagnostics` |
| namios-dichvu | namios | `namios-services` |
| namios-huong-dan | namios | `namios-guide` |
| namios-smartai | namios | `namios-ai` |
| namios-windows-app | namios | `namios-run` |
| namios-lich | namios | `namios-calendar` |
| namios-control-panel | namios | `preferences-system` |
| namios-ket-noi-thiet-bi | namios | `preferences-desktop-peripherals` |

`namios-assistant.desktop` giữ `Icon=namios` (= mặt trời hero). Các app còn lại
(antoan, manchieu, cpl-*, web shortcuts, go-cai-dat, calamares) vốn đã trỏ đúng
tên freedesktop chuẩn — không cần sửa.

## STEP 5 — wordmark "NaMiOS" → "NaMi"

Đã sửa nội dung `<text>…NaMiOS</text>` → `NaMi` (giữ nguyên tagline + mọi thứ
khác) trong 3 lockup SVG shipped:
- `usr/share/namios-branding/logo/NaMiOS_Logo_Master_Outlined.svg`
- `usr/share/namios-branding/logo/NaMiOS_Logo_Master_Outlined_Dark.svg`
- `usr/share/namios-branding/logo/NaMiOS_Logo_Master_Stacked.svg`

Không đụng boot splash (đã xong trước) và PNG lockup.

## Phạm vi — ĐÃ phủ vs CHƯA phủ

**Đã phủ** (toàn bộ 25 app có `.desktop` trong includes.chroot + bộ nOffice +
app hệ thống hay gặp): Trợ lý, nOffice 7 app, Trình duyệt + 4 web shortcut
(Facebook/TikTok/YouTube/Zalo dùng chung `internet-web-browser`), Tệp, Cài đặt,
7 nhóm Control Panel (Accounts/Apps/Devices/Display/Network/Personalization/
Time), Cập nhật, Cửa hàng, Gỡ cài đặt, An toàn, Cổng Dịch vụ, Máy chiếu,
Chẩn đoán, Hướng dẫn, Chạy Windows, Hỏi AI, Lịch, Kết nối thiết bị, Cài hệ
điều hành (Calamares), Dòng lệnh, PDF, Ảnh, Media, Nhạc, Lưu trữ, Máy in.

**CHƯA phủ (cố ý — ngoài bộ lõi task yêu cầu, giữ icon cũ):**
- Soạn thảo văn bản: Kate/KWrite (`kate`, `org.kde.kate`, `org.kde.kwrite`,
  `accessories-text-editor`).
- Máy tính: KCalc (`kcalc`, `org.kde.kcalc`, `accessories-calculator`).
- Thư: Thunderbird/KMail (`thunderbird`, `kmail`, `internet-mail`, `mail-client`).
- Firefox (`firefox`, `firefox-esr`) — task chỉ định trình duyệt dùng
  `internet-web-browser`; để nguyên theo quyết định wave trước.
- Chụp màn hình Spectacle (`spectacle`), `hwinfo`.
- Icon thương hiệu/menu drum của wave trước: `namios-welcome`,
  `start-here-namios`, `start-here-kde`, `start-here` — KHÔNG đụng.
- `NaMiOS-Symbolic` (wifi/pin/âm lượng/cảnh báo…) — ngoài phạm vi theo ràng buộc.

## Lưu ý build (GATED — chưa build/commit/push)
Khi build: chạy generator lại nếu cần, rồi để live-build gộp theme; trên host
cần làm mới cache icon (`gtk-update-icon-cache` cho hicolor, `kbuildsycoca6` cho
KDE) để Start menu/Dolphin nhận icon mới.
