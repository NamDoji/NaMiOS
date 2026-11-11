# BRANDING-MAP-OLD-NEW — NaMi 2026.11 "Đông Sơn" (alpha)

> Bảng hợp nhất old→new qua các bề mặt (boot/installer/login/splash/shell/apps/website/
> version), gom từ `docs/design/P0-UI-AUDIT.md` §3, `docs/branding/
> TRADEMARK-LICENSE-COMPLIANCE.md`, và git log các commit rebrand. **`verified_on_host: NO`**
> cho mọi dòng — bảng này đối chiếu **bằng chứng repo** (file + khoá đã đọc), không phải quan
> sát trên máy đã boot. Cột "Trạng thái" lấy nguyên nghĩa từ `P0-UI-AUDIT.md` (DONE = cấu hình
> nguồn đã đổi trong repo; PARTIAL = đổi một phần hoặc chưa tái xuất asset nhị phân; TODO =
> chưa làm).

## 1. Nhận diện/tên gọi tổng quát

| Bề mặt | Cũ | Mới (2026.11 "Đông Sơn") | Trạng thái | Bằng chứng |
| --- | --- | --- | --- | --- |
| Tên hiển thị (NAME/PRETTY_NAME) | `NaMiOS` | **`NaMi`** (`PRETTY_NAME="NaMi – Hệ điều hành cho người Việt"`) | DONE | `etc/os-release` |
| ID kỹ thuật (không hiển thị) | `namios` | **giữ nguyên `namios`** (field kỹ thuật, tool đọc `ID_LIKE=debian`) | DONE (chủ đích không đổi) | `etc/os-release` `ID=` |
| Tên mã thương hiệu (codename) | "Sen bừng sáng" (v1) → "Sen Việt" (v2) | **"Đông Sơn" (v3)** | DONE | `etc/os-release` `VERSION_CODENAME=dong-son`; git log `0798827` |
| Phiên bản | `0.0.0-dev` / `TBD` | **`2026.11`**, kênh **`alpha`** | DONE | `etc/os-release` `VERSION_ID`; `etc/namios-release` `NAMIOS_VERSION`/`NAMIOS_CHANNEL`; commit `ff7928d` |
| Build date/commit | `TBD` | vẫn **`TBD: tự đóng dấu trên host lúc build thật`** | TODO (cố ý — chỉ host thật mới điền được) | `etc/namios-release` |
| Repo/URL | `github.com/NamDoji/NaMiOS` | giữ nguyên (chưa đổi theo tên hiển thị "NaMi") | DONE (chủ đích) | `etc/os-release` `HOME_URL`/`SUPPORT_URL` |
| Tác giả | (chưa có trường) | **"Đỗ Chí Cường & Đỗ Bảo Nam"** (`NAMIOS_AUTHORS`, field additive) | DONE | `etc/namios-release`, thêm 11/11/2026 |

## 2. Palette & token màu

| Bề mặt | Cũ | Mới (v3 Đông Sơn) | Trạng thái |
| --- | --- | --- | --- |
| Palette gốc | v2 "Sen Việt": đỏ-son `#C93643` / mực đêm `#122A3A`; v1 "Sen bừng sáng": jade | **navy `#092D4F` / gold `#DEA93E` / vermilion `#D64C3E` / teal `#278F8D` / ivory `#FFF9EF`** | DONE (`brand.json` v3.0, `BRAND.md`) |
| `ANSI_COLOR` (terminal) | đỏ son | **vermilion** `#D64C3E` xấp xỉ bằng mã ANSI 16-màu `1;31` (terminal thường không hỗ trợ truecolor cho trường này) | DONE | `etc/os-release` comment |
| KColorScheme | `NaMiOS.colors` — accent đỏ-son, chữ trắng/đỏ | **accent gold**, Selection **đảo chiều** (nền gold, chữ navy), link teal-deep/teal-light đo lại WCAG | DONE |
| `kdeglobals` accent | `201,54,67` (đỏ) | **`222,169,62`** (gold) | DONE |
| High-contrast scheme | không có | **MỚI**: `NaMi-HighContrast.colors` (mọi cặp ≥10:1) | DONE (mới thêm, commit `93f200a`) |
| Plasma desktoptheme | "Sen Việt" tối | **`NaMiOS-Sen`**: navy/navy-subtle + gold/teal | DONE |
| QML palette app | `SenVietPalette.qml` (Sen Việt) | token surface/text/brand/action v3 | DONE |
| Hiển thị "Gallery.qml" | "Sen Việt" | **"Đông Sơn"** | DONE |
| WCAG | chưa đo hệ thống | **35/36 cặp tương phản PASS** (fail duy nhất gold/ivory 2.04:1 — chủ đích, không dùng làm nền nút) | DONE (`HIG-ADOPTION-VERDICT.md`) |

## 3. Logo mark

| Bề mặt | Cũ | Mới (v3) | Trạng thái |
| --- | --- | --- | --- |
| Logo mark (khái niệm) | hoa sen 7 cánh (v1 "Sen bừng sáng" → v2 "Sen Việt") | **mặt trống đồng Đông Sơn** | DONE (SVG: 4 master thay + 5 mới) |
| Icon nút Bắt đầu (`start-here-namios`) | PNG sen đỏ-vàng squircle | PNG trống đồng (34 ảnh raster thay ở commit `93f200a`, mọi cỡ `hicolor`/`NaMiOS-Lotus`) | DONE (raster) |
| **SDDM login PNG** | sen | **vẫn còn SEN** (`NaMiOS_Symbol_Transparent_1024.png`) | **TODO — CHƯA tái xuất trống đồng** |
| Plymouth boot-splash PNG | sen | chưa xác minh đã đổi hết sang trống đồng | **TODO (xác minh + tái xuất)** |
| Calamares installer PNG (`logo.png`, `welcome.png`, `bg-welcome.png`, `bg-progress.png`) | sen | chưa xác minh đã đổi hết sang trống đồng | **TODO (xác minh)** |
| Favicon / `hicolor` icon set | sen | trống đồng (theo cùng đợt 34 ảnh ở `93f200a`) | DONE |

## 4. Boot / installer / login / splash

| Bề mặt | Cũ | Mới | Trạng thái | Ghi chú |
| --- | --- | --- | --- | --- |
| GRUB boot menu | nhận diện Debian mặc định | hook `0145-grub-bootmenu-brand` áp nhãn NaMi | PARTIAL | cần boot-test |
| Plymouth theme | `namios` (two-step) | palette v3 (asset PNG chưa xác nhận hết) | PARTIAL | |
| SDDM theme | `namios` (QML `Main`/`Background`/`Clock`) | nền/màu v3, **logo vẫn SEN** | PARTIAL | §3 |
| Calamares branding | `namios` (branding.desc, show.qml) | version string đã `2026.11 (Đông Sơn)`; PNG asset chưa xác nhận v3 | PARTIAL | commit `ff7928d` cho version; §3 cho PNG |
| Wallpaper mặc định | gói 20 ảnh Việt Nam (chọn Vịnh Hạ Long làm mặc định) | giữ nguyên bộ ảnh, không đổi theo v3 | DONE (không đổi, ngoài phạm vi rebrand màu) | |

## 5. Shell (desktop/taskbar/cửa sổ)

| Bề mặt | Cũ | Mới | Trạng thái |
| --- | --- | --- | --- |
| Vị trí taskbar | căn trái (kiểu Windows 10) | **căn giữa** (2 `panelspacer` quanh Kickoff+Task Manager, kiểu Windows 11) | DONE (cấu hình, chưa boot-test nhìn mắt) |
| Nút điều khiển cửa sổ | không xác định vị trí (đường `kdecoration2` bị comment) | **góc phải, thứ tự `IAX`** (min/max/close) trên viền Breeze mặc định | DONE (cấu hình) |
| Viền cửa sổ riêng (Aurorae `NaMiOSLotus`) | nút tròn 3 màu kiểu macOS | thiết kế macOS **vẫn y nguyên, đang TẮT** (chưa sửa sang kiểu Windows vuông) | TODO (hoãn, chờ bisect treo đăng nhập) |
| Panel | mặc định Plasma | nổi (`floating=1`), bo góc 28px, dày 36px | DONE (cấu hình, tin cậy trung bình — chưa đối chiếu mã nguồn panelview) |
| Icon theme | Breeze | **NaMiOS-Lotus** (squircle kiểu iOS, kế thừa Breeze) | PARTIAL (chưa đồng bộ hoàn toàn với ngôn ngữ Windows-11) |

## 6. Ứng dụng (tên hiển thị `.desktop`)

| App gốc | Nhãn NaMi/n trước đợt 11/11 | Nhãn hiện tại (2026.11) | Giữ tên gốc trong `Name=`? | Trạng thái |
| --- | --- | --- | --- | --- |
| Firefox ESR | `NaMiWeb (Firefox)` | **`NaMiBrowser (Firefox)`** | Có (bắt buộc — chính sách nhãn hiệu Mozilla) | DONE |
| Thunderbird | `NaMiMail (Thunderbird)` | giữ nguyên | Có (bắt buộc) | DONE |
| LibreOffice Writer | `NaMiWriter` | **`nWord`** | Không trong `Name=` chính (có ở Comment/docs) | DONE — xem cảnh báo nhãn hiệu §1c `TRADEMARK-LICENSE-COMPLIANCE.md` |
| LibreOffice Calc | `NaMiSheet` | **`nExcel`** | như trên | DONE — cảnh báo nhãn hiệu |
| LibreOffice Impress | `NaMiSlides` | **`nPowerPoint`** | như trên | DONE — cảnh báo nhãn hiệu |
| LibreOffice Draw | `NaMiDraw` | **`nDraw`** | như trên | DONE |
| LibreOffice Start Center | `NaMiOffice` | **`nOffice`** | như trên | DONE |
| LibreOffice Base | `NaMiData` | giữ nguyên (ngoài phạm vi đợt 11/11) | như trên | không đổi |
| LibreOffice Math | `NaMiMath` | giữ nguyên (ngoài phạm vi đợt 11/11) | như trên | không đổi |
| Okular | `NaMiPDF (Okular)` | giữ nguyên | Có | DONE |
| Dolphin | `NaMiFiles` | giữ nguyên | Không (Comment) | DONE |
| Kate | `NaMiText` | giữ nguyên | Không (Comment) | DONE |
| Gwenview | `NaMiẢnh` | **`NaMiImages`** | Không (Comment) | DONE (đổi 10/11/2026) |
| Ark | `NaMiNén` | **`NaMiArchive`** | Không (Comment) | DONE (đổi 10/11/2026) |
| Spectacle | `NaMiChụp` | giữ nguyên | Không (Comment) | DONE |
| KCalc | `NaMiTính` | giữ nguyên | Không (Comment) | DONE |
| Konsole | `NaMiDòng lệnh` | giữ nguyên | Không (Comment) | DONE |
| Plasma Discover | `NaMiCửa hàng` | giữ nguyên | Không (Comment) | DONE |
| Print Manager | `NaMiMáy in` | giữ nguyên | Không (Comment) | PARTIAL — id `.desktop` thật chưa xác nhận trên snapshot trixie |
| system-config-printer | `NaMiMáy in (nâng cao)` | giữ nguyên | Không (Comment) | DONE |
| Simple Scan | `NaMiQuét` | giữ nguyên | Không (Comment) | DONE |
| Skanlite | `NaMiQuét (Skanlite)` | giữ nguyên | Có (phân biệt 2 app quét) | DONE |
| Blueman | `NaMiBluetooth` | giữ nguyên | Không (Comment) | DONE |
| fcitx5-config-qt | (chưa có nhãn) | **`NaMiType`** (MỚI 10/11) | Không (Comment); `NoDisplay=true` gốc → ẩn khỏi menu mặc định | DONE (nhãn) / chờ quyết định UX hiện/ẩn |
| VLC (MỚI — NaMiMedia) | (chưa cài player nào) | **`NaMiMedia`** | Có (tín dụng ở Comment) | DONE — xem ghi chú bằng sáng chế `gstreamer1.0-plugins-ugly` §1a |
| Security Center (MỚI) | — | **`NaMiSecurity`** ("An toàn") | Không áp dụng (tự viết) | DONE |
| Facebook/Zalo/TikTok/YouTube (web shortcut) | tên dịch vụ gốc | **KHÔNG đổi, cố ý** | Có (bắt buộc — không phải phần mềm NaMi phân phối lại) | DONE (chủ đích không rebrand) |

## 7. Website

| Bề mặt | Cũ | Mới | Trạng thái |
| --- | --- | --- | --- |
| `website/data/release-manifest.json` `product` | — | `"NaMiOS"` (chưa đồng bộ theo tên hiển thị mới "NaMi") | **TODO — lệch với `os-release`** |
| `release-manifest.json` `version`/`channel` | `0.1.0-example` / `beta` | **chưa cập nhật khớp `2026.11`/`alpha`** | **TODO — lệch với `etc/namios-release`** |
| Trang About/tiến độ | tham chiếu `docs/releases/boot-evidence/*`, `G0-FEASIBILITY-REPORT.md` | không đổi theo rebrand Đông Sơn | không nằm trong phạm vi rebrand này |

**Phát hiện cần theo dõi:** `release-manifest.json` hiện **chưa đồng bộ** với phiên bản
`2026.11 "Đông Sơn" alpha` đã đóng dấu ở `etc/os-release`/`etc/namios-release` (commit
`ff7928d`) — vẫn ghi `product: "NaMiOS"`, `version: "0.1.0-example"`, `channel: "beta"`. Đây là
**lệch pha cần chủ dự án quyết định** trước khi công bố website: đồng bộ số phiên bản, hoặc
giữ `release-manifest.json` như một "mẫu ví dụ" riêng (schema đang ghi `"0.1.0-example"` gợi ý
đây vẫn là placeholder, chưa phải dữ liệu phát hành thật).

## 8. Tổng kết nhất quán

- **Nhất quán đầy đủ (DONE cả nguồn + asset):** tên hiển thị NaMi, codename Đông Sơn, số phiên
  bản 2026.11/alpha, palette navy/gold trong mọi file `.colors`/`desktoptheme`/`kdeglobals`/
  QML, tên app `.desktop`, tác giả.
  (bảng §1, §2, §6).
- **Lệch pha đã biết (TODO, có bằng chứng cụ thể):** PNG/ICO raster của SDDM/Plymouth/Calamares
  vẫn là logo Sen cũ (§3, §4); viền cửa sổ Aurorae vẫn thiết kế macOS, chưa đổi sang Windows
  (§5); `website/data/release-manifest.json` chưa đồng bộ version/tên sản phẩm với
  `os-release` (§7).
- **Rủi ro cần quyết định ngoài phạm vi kỹ thuật:** nhãn `nWord`/`nExcel`/`nPowerPoint` gợi
  trùng tên Microsoft Office (§6) — cần rà soát pháp lý trước khi phát hành công khai.
