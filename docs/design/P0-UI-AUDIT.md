# NaMi P0 — Khảo sát UI hiện trạng (HIG §10.1)

> **Loại tài liệu:** báo cáo khảo sát P0 của `docs/design/hig/NaMi-Human-Interface-2026.md`.
> Mọi "hiện trạng" lấy từ **bằng chứng repo** (file + khoá đã đọc), KHÔNG từ quan sát boot.
> **`verified_on_host: NO`** cho toàn bộ. **Phạm vi file:** chỉ viết tài liệu. Không sửa
> config/theme/app. Không `git commit`/push. **Ngày:** 2026-11-11.
> Đường dẫn gốc runtime: `distro/live-build/config/includes.chroot/` (viết tắt `$CH`).

## 1. Bảng khảo sát nền tảng (HIG §10.1)

| Hạng mục | Giá trị thực trong repo | Bằng chứng | Trạng thái |
|---|---|---|---|
| Base distro | **Debian 13 "trixie"** (live-build) | `distro/live-build/config/auto/config` `DISTRIBUTION=${…:-trixie}`; ADR 0002 | DONE |
| DE / compositor | **KDE Plasma 6** · KWin (`kwin-wayland \| kwin-x11`); **compositing TẮT mặc định** (máy yếu/VM) | `0100-desktop-kde.list.chroot`; `$CH/etc/skel/.config/kwinrc`; `namios-auto-compositing.sh` | DONE |
| Toolkit | **Qt 6 / PySide6** (app Python) + **bash/HTML** (guide, web-launcher); QML (SDDM/Plasma) | `$CH/opt/namios/*-src/ui.py` (PySide6); `$CH/usr/share/namios/qml/*.qml` | DONE |
| Display manager (login) | **SDDM** — theme `namios` | `$CH/usr/share/sddm/themes/namios/{Main,Background,Clock}.qml`, `theme.conf` | PARTIAL (dùng PNG logo SEN cũ — xem §4) |
| Bootloader | **GRUB** — `grub-pc`+`grub-pc-bin`+`grub2-common` (BIOS) + `grub-efi-amd64-bin` (UEFI, chưa signed) · **isolinux** cho ISO live | `0700-installer.list.chroot`; `config/bootloaders/{grub-pc,isolinux}`; hook `0145-grub-bootmenu-brand` | PARTIAL |
| Plymouth (boot splash) | theme **`namios`** (module `two-step`) | `$CH/usr/share/plymouth/themes/namios/namios.plymouth` | PARTIAL |
| Installer | **Calamares** + `calamares-settings-debian`; branding `namios` | `0700-installer.list.chroot`; `$CH/etc/calamares/branding/namios/{branding.desc,show.qml,*.png}` | PARTIAL |
| Icon theme | **NaMiOS-Lotus** (squircle kiểu iOS) kế thừa **Breeze** | `$CH/etc/skel/.config/kdeglobals` `[Icons]`; `$CH/usr/share/icons/NaMiOS-Lotus` | PARTIAL |
| App launcher | **Kickoff** (Plasma) + `.desktop` tùy biến; tìm bằng gõ chữ | `$CH/etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc` | PARTIAL |
| File manager | **Dolphin** | `$CH/etc/skel/.config/dolphinrc`; `mimeapps.list` | PARTIAL |
| Update stack | **Plasma Discover** + **PackageKit** (trên nền **apt/dpkg**) | `0100-desktop-kde.list.chroot` (`plasma-discover`, `packagekit`) | PARTIAL |
| Package manager | **apt / dpkg** (Debian) | base Debian | DONE |
| Secure Boot | **CHƯA hỗ trợ** — mới có `grub-efi-amd64-bin` *không* signed; `shim-signed`+`grub-efi-amd64-signed` ("việc sau"); pilot cài BIOS offline | chú thích `0700-installer.list.chroot` | TODO |
| IME tiếng Việt | **fcitx5** (Telex/VNI) | `$CH/etc/skel/.config/fcitx5`; `0205-ime-demo.list.chroot` | PARTIAL |
| Font | Noto Sans/UI/Mono + DejaVu + Liberation2 (đủ dấu VN, cấp phép phân phối, **không font MS**) | `0300-fonts.list.chroot` | DONE |
| Quyền phân phối app gộp | web-launcher NaMi-sở-hữu trỏ dịch vụ bên thứ 3 (Zalo/FB/TikTok/YT/Windows-app) — cần **attribution + giấy phép** | `$CH/usr/share/applications/namios-{zalo-web,facebook,tiktok,youtube,windows-app}.desktop` | TODO (rủi ro — §5) |

**Kết luận §1:** repo THỰC có đầy đủ nền tảng (KDE Plasma 6 / Qt+PySide6 / Calamares / SDDM /
GRUB / Plymouth / Discover). → đủ điều kiện chuyển sang P1 bằng patch thật (không còn ở trạng
thái "chưa có repo, chỉ tạo prototype" mà HIG §10.1 cảnh báo).

## 2. SCREEN MATRIX — mọi màn hình/app/.desktop + trạng thái

Tổng: **25 `.desktop` trong `applications/`** + 4 autostart + 3 Desktop + theme metadata.

### 2.1. Màn hình hệ thống (shell / lifecycle)

| Màn | Thành phần thực | Trạng thái | Ghi chú |
|---|---|---|---|
| Boot menu | GRUB + isolinux, hook `0145-grub-bootmenu-brand` | PARTIAL | đã vá "auto-ENTER" (memory abf8bae); CẦN boot-test |
| Boot splash | Plymouth theme `namios` | PARTIAL | watermark/background PNG — xác minh logo v3 |
| Đăng nhập | SDDM theme `namios` | PARTIAL | dùng `NaMiOS_Symbol_Transparent_1024.png` = **logo SEN cũ** (chưa tái xuất từ SVG trống đồng) |
| Màn khóa | `kscreenlockerrc`, `ksplashrc` | PARTIAL | — |
| Desktop | Plasma 6 (panel đáy, systray, đồng hồ) + autostart polish/widgets | PARTIAL | icon Desktop VN: `may-tinh-cua-toi`, `tai-lieu-cua-toi`, `thung-rac` |
| Mở ứng dụng | Kickoff (gõ tìm) | PARTIAL | — |
| Trung tâm điều khiển | KDE quick-settings / systray | TODO | chưa có panel quick-settings tùy biến NaMi |
| Trình quản lý tệp | Dolphin | PARTIAL | vị trí Tải xuống/Tài liệu/Ảnh theo XDG |
| Cài đặt | **`namios-control-panel`** (/usr/local/bin) + 9 shortcut `cpl-*` (mở KDE System Settings theo category) | PARTIAL | network/update/apps/devices/display/personalization/timelang/accounts |
| Cập nhật | Discover + PackageKit; shortcut `namios-cpl-update` | PARTIAL | tiến trình thật qua PackageKit; changelog VN TODO |
| Cài đặt (installer) | Calamares branding `namios` | PARTIAL | welcome/progress/logo PNG — xác minh v3 + 2 bước xác nhận xóa đĩa |
| Giới thiệu (About) | `opt/namios/namios_core/about.py` | PARTIAL | phiên bản/giấy phép/nguồn mở |

### 2.2. Ứng dụng NaMi (opt/namios + /usr/local/bin)

| App (.desktop `Name`) | Nhãn VN nội bộ | Nguồn | Trạng thái |
|---|---|---|---|
| **nControl** (+9 cpl-*) | "Cài đặt" | `/usr/local/bin/namios-control-panel` | PARTIAL |
| **nAssistant** | "Trợ lý" | `namios_assistant-src` (PySide6, KB offline + LLM online) | PARTIAL (branding.py fallback lệch — §4) |
| **nConnect** | "Kết nối thiết bị" | `namios-ket-noi-thiet-bi` (+ máy in) | PARTIAL |
| **An toàn** | "An toàn" | `namios_antoan-src` | PARTIAL |
| **Dịch vụ** | "Dịch vụ VN" | `namios_dichvu-src` (danh bạ DVC) | PARTIAL |
| **Lịch** | "Lịch" | `namios_lich-src` (âm lịch/lễ VN) | PARTIAL |
| **Màn chiếu** | "Màn chiếu" | `namios_manchieu-src` | PARTIAL |
| **nGuide** | "Hướng dẫn nhanh" | `namios-huong-dan` → HTML | PARTIAL |
| Chẩn đoán | "Chẩn đoán" | `namios-chan-doan` | PARTIAL |
| Welcome (lần đầu) | — | `namios_welcome-src` (firstrun + migrate) | PARTIAL |
| Smart AI | — | `namios-smartai.desktop` | PARTIAL |
| Web: Zalo/FB/TikTok/YouTube | — | web-launcher NaMi-sở-hữu | TODO (attribution §5) |
| Windows app | — | `namios-windows-app` (Wine) | TODO (không hứa "mọi app chạy") |

### 2.3. Thư viện / hạ tầng (không phải màn hình)
`namios_core` (About/errors/validation/manifest/txstate), `namios_security` (safe_path/safe_exec/
redactor), `namios_i18n` (vi.json/en.json + `add_catalog`). Trạng thái: DONE (hạ tầng), tái dùng
cho mọi app.

**Thống kê trạng thái:** DONE = nền tảng + font + distro; **PARTIAL = phần lớn màn hình/app** (đã
có khung, thiếu nối token v3 + boot-test); **TODO = quick-settings tùy biến, Secure Boot, attribution
web-app, changelog VN, high-contrast scheme thật**.

## 3. Old → New branding map (phần lớn ĐÃ làm ở các wave trước)

| Bề mặt | Cũ | Mới (v3 Đông Sơn) | Trạng thái |
|---|---|---|---|
| Palette nhận diện | Sen Việt v2 (đỏ son #C93643, mực đêm #122A3A) / Sen bừng sáng v1 (jade) | navy #092D4F / gold #DEA93E / vermilion #D64C3E / teal #278F8D / ivory #FFF9EF | **DONE** (`brand.json` v3.0, `BRAND.md`) |
| Logo mark | hoa sen (7 cánh) | **mặt trống đồng Đông Sơn** (4 SVG master đã thay + 5 SVG mới) | DONE (SVG) · **TODO (PNG/ICO raster chưa tái xuất)** |
| KColorScheme | đỏ-son accent, chữ trắng/đỏ | gold accent, selection chữ **navy**, chữ-đỏ vermilion-deep | DONE (`NaMiOS.colors`) |
| kdeglobals accent | 201,54,67 (đỏ) | **222,169,62 (gold)** | DONE |
| Plasma desktoptheme | Sen Việt tối | navy/navy-subtle + gold/teal | DONE (`NaMiOS-Sen/colors`) |
| QML palette app | Sen Việt | v3 surface/text/brand/action | DONE (`SenVietPalette.qml`) |
| **SDDM login PNG** | logo SEN raster | trống đồng | **TODO** — `NaMiOS_Symbol_Transparent_1024.png` vẫn SEN |
| Plymouth/Calamares PNG | — | trống đồng | TODO (xác minh + tái xuất) |
| `branding.py` fallback (4 app) | brand v2 | v3 | PARTIAL (assistant đã v3; antoan/dichvu/manchieu cần kiểm) |
| Tên hiển thị | "Sen Việt" | "Đông Sơn" | DONE (`Gallery.qml`) |

## 4. 10 tác vụ P0 (HIG §11/§12.1) ánh xạ vào repo

| # | Tác vụ P0 | Màn/app thực | Hiện trạng |
|---|---|---|---|
| 1 | Mở trình duyệt | Firefox (web-launcher) + Kickoff | PARTIAL — không ghi đè icon Firefox (HIG §10.3) |
| 2 | Tìm tệp tải về | Dolphin (XDG Downloads) | PARTIAL |
| 3 | Gõ tiếng Việt | fcitx5 Telex/VNI | PARTIAL — boot-test IME |
| 4 | Mở/sửa DOCX | LibreOffice (giữ nhận diện gốc) | PARTIAL |
| 5 | Xem PDF | `0420-pdf.list.chroot` (Okular) | PARTIAL |
| 6 | Kết nối Wi-Fi | `namios-cpl-network` → KDE Network | PARTIAL |
| 7 | Ghép Bluetooth | KDE Bluetooth / nConnect | PARTIAL |
| 8 | In trang thử | `nConnect may-in` | PARTIAL |
| 9 | Cài cập nhật | Discover + PackageKit | PARTIAL — changelog VN + tiến trình thật |
| 10 | Tìm lời giải lỗi thiết bị | nAssistant (KB offline + AI) | PARTIAL — mẫu thông báo 5-phần (§UI-KIT) |

Mỗi tác vụ cần **≥80% hoàn thành độc lập** (HIG §12.1) — chỉ đo được khi **boot-test + thử người
dùng thật** (P2–P4). Nút "được vẽ" KHÔNG tính là đạt (HIG §12.1).

## 5. RISK LIST (accessibility / license / driver / update)

| # | Rủi ro | Mức | Bằng chứng | Hành động |
|---|---|---|---|---|
| R1 | **A11y:** chưa boot-test screen reader/bàn phím/focus; high-contrast mới là token, chưa thành KColorScheme thật | Cao | `nami-tokens.json` high-contrast chưa có `.colors` | P1/P2: sinh scheme HC + demo Orca |
| R2 | **A11y:** `[Colors:Selection]` đổi chiều (nền gold + chữ navy) chưa xác nhận bằng mắt | TB | `.colors` chú thích `verified_on_boot: NO` | boot-screenshot |
| R3 | **License:** tên "NaMi/NaMiOS" **chưa rà soát nhãn hiệu** | Cao | HIG §0; `brand.json` `approval_status: trademark review pending` | khóa tên qua lớp l10n (đã có) + rà soát pháp lý trước phát hành |
| R4 | **License:** web-launcher Zalo/FB/TikTok/YT thiếu attribution + quyền dùng tên/logo bên thứ 3 | Cao | 5 `.desktop` web | thêm nguồn gốc/giấy phép trong About; không ghi đè icon Firefox/LibreOffice |
| R5 | **License:** wallpaper/âm thanh phải có nguồn + quyền + metadata; không đưa biểu tượng chủ quyền/bản đồ chưa kiểm chứng | TB | HIG §5.3 | audit `usr/share/backgrounds/namios` (wave sau) |
| R6 | **Driver:** không được tuyên bố "mọi driver/mọi app Windows chạy được" | Cao | HIG §14; `namios-windows-app` (Wine) | UI báo mức hỗ trợ theo dữ liệu thật |
| R7 | **Update:** không popup giả danh cập nhật; rollback chỉ báo "thành công" khi thật | Cao | HIG §8.4 | Discover/PackageKit tiến trình thật |
| R8 | **Security:** Secure Boot chưa có (`shim-signed` hoãn) — không hạ bảo mật để thay splash | Cao | `0700-installer.list.chroot` | tách ảnh BIOS/UEFI-signed (việc sau) |
| R9 | **Branding drift:** PNG/ICO (SDDM/Plymouth/Calamares) vẫn logo SEN cũ; `make-colorscheme.py` đọc token CŨ → chạy lại sẽ ghi đè v3 | TB | `BRAND.md §6` | tái xuất PNG + đồng bộ token nguồn |
| R10 | **Token drift:** 3 bộ token lệch nhau (PL12 ruby / Sen Việt / Đông Sơn) | TB | §7 NAMI-DESIGN-TOKENS | hợp nhất về 1 trước P2 |

## 6. Phân loại DONE / TODO / CANNOT-VERIFY-WITHOUT-BOOT-TEST

- **DONE (bằng chứng repo đủ):** base distro, font, palette v3 trong `brand.json`/`.colors`/
  desktoptheme/kdeglobals/QML, logo SVG trống đồng, tên "Đông Sơn", lớp i18n vi/en, hạ tầng
  core/security.
- **TODO (chưa làm, làm được không cần máy thật):** tái xuất PNG/ICO từ SVG v3; sinh KColorScheme
  **high-contrast** thật; đồng bộ `make-colorscheme.py`; attribution web-launcher; hợp nhất 3 bộ
  token; changelog VN cho Update; quick-settings tùy biến.
- **CANNOT-VERIFY-WITHOUT-BOOT-TEST:** màu hiển thị thật (Selection đổi chiều), IME gõ tiếng Việt,
  focus ring/screen reader, Wi-Fi/Bluetooth/in/cập nhật/rollback thật, Secure Boot, hiệu năng máy
  yếu (compositing on/off), Aurorae có gây treo đăng nhập không. **Tất cả ở P2–P4.**
