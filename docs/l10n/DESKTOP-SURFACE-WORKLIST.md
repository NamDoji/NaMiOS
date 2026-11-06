# NaMiOS — WORKLIST dịch bề mặt desktop mặc định (lần đầu đăng nhập)

**Trạng thái:** DESIGN / l10n work-planning — soạn 06/11/2026.
**Phạm vi:** toàn bộ bề mặt người dùng NHÌN THẤY trên desktop NaMiOS mặc định (Debian 13 trixie + KDE Plasma, SDDM autologin → phiên **Plasma X11**, giao diện mặc định tiếng Việt chuẩn Bắc Ninh).
**Không thuộc phạm vi:** machine field, nội dung tài liệu (docbook), chuỗi của ứng dụng chạy qua Wine.

> **TRUNG THỰC — đọc trước khi dùng số liệu.** Các con số % ở đây TRÍCH từ l10n.kde.org
> (nhánh **stable-kf6**, đội **vi**) đọc ngày 06/11/2026 qua công cụ web; chúng là **ước lượng
> theo bề mặt web**, chưa đối chiếu với đúng phiên bản `.po`/`.mo` mà gói Debian 13 trixie THẬT
> đóng vào ISO. Mọi dòng đánh dấu **[cần xác minh trên ISO]** phải được xác nhận lại bằng cách
> mở đúng catalog trong ISO (vd `msgunfmt /usr/share/locale/vi/LC_MESSAGES/<domain>.mo`) trước
> khi coi là chốt. Debian đóng gói bản dịch theo gói nguồn (không còn metapackage `kde-l10n-vi`
> kiểu cũ), nên độ phủ thực tế có thể lệch với l10n.kde.org.

---

## 0. Bối cảnh cấu hình NaMiOS (đã có trong repo)

- Ngôn ngữ hiển thị Plasma: `etc/skel/.config/plasma-localerc` → `[Translations] LANGUAGE=vi:en_US`
  (ưu tiên tiếng Việt, tự rơi về `en_US` khi **thiếu** bản dịch — đây là nguồn gốc của mọi chuỗi
  còn tiếng Anh trên desktop).
- Locale hệ thống: `hooks/normal/0100-locale-vi` + `--bootappend-live` = `vi_VN.UTF-8`, TZ `Asia/Ho_Chi_Minh`.
- Gói dịch đang kéo vào ISO: `0210-l10n-vi.list.chroot` → `task-vietnamese` + `task-vietnamese-kde-desktop`.
  **Đây là lớp phủ gốc.** Chỗ nào 2 task này KHÔNG mang bản dịch tới thì ra tiếng Anh.
- Panel mặc định (`plasma-org.kde.plasma.desktop-appletsrc`): 1 panel đáy kiểu Windows gồm
  **Kickoff** (nút Bắt đầu) + **icontasks** (thanh tác vụ) + **systemtray** (khay hệ thống) +
  **digitalclock** (đồng hồ). Menu chuột phải desktop = `org.kde.contextmenu`.
- Ứng dụng lõi kéo vào (0100/0110): dolphin, konsole, kate, plasma-discover, plasma-nm, plasma-pa,
  kscreen, ark, okular, spectacle, kcalc, gwenview, sddm, calamares.
- Phần RIÊNG của NaMiOS (`namios-welcome` first-run wizard, CLI `namios`, branding) đã 100% tiếng
  Việt do `namios_i18n` kiểm soát (xem `docs/specs/I18N.md`) — **không** phụ thuộc upstream, KHÔNG
  nằm trong worklist này.

### Cơ chế giao hàng bản dịch bù (đề xuất)

Soạn một gói **`namios-l10n-vi`** chứa các `.mo` bù/ghi đè đặt tại
`/usr/share/locale/vi/LC_MESSAGES/<domain>.mo`. Hai hướng kỹ thuật, chọn 1 và ghi ADR:
1. **Đóng góp ngược upstream** (KDE l10n-vi) cho các chuỗi mới — đúng tinh thần cộng đồng, nhưng
   chậm vào Debian trixie.
2. **Overlay tại chỗ**: merge bản dịch của ta vào `.po` gốc rồi `msgfmt` ghi đè `.mo` trong gói
   `namios-l10n-vi` (ưu tiên cài sau 2 task vi). Phải bảo toàn `msgctxt`/`Plural-Forms` và
   `charset=UTF-8`. **Rủi ro:** lệch phiên bản khi KDE cập nhật → cần gắn version gói KDE.

---

## 1. Bảng domain (gettext) theo từng mảng bề mặt + độ phủ vi ước lượng

Nguồn %: l10n.kde.org `stats/gui/stable-kf6/team/vi/` (đọc 06/11/2026). **Tổng đội vi stable-kf6 ≈ 9%
đã dịch** (≈15.7k đã dịch / ≈12.3k mờ "fuzzy" / phần còn lại chưa dịch trên 324 gói).
Nguồn: https://l10n.kde.org/team-infos.php?teamcode=vi và https://l10n.kde.org/stats/gui/stable-kf6/team/vi/

| Bề mặt người dùng | Domain gettext (gói) | vi đã dịch (ước lượng) | Ghi chú |
|---|---|---|---|
| **Nút Bắt đầu (Kickoff)**: tab Ứng dụng/Nơi chốn/Lịch sử, ô tìm kiếm, Nguồn/Khởi động lại/Tắt máy | `plasma_applet_org.kde.plasma.kickoff` (gói **plasma-desktop**) | ~30% dịch + ~40% **fuzzy** | Fuzzy = HIỆN tiếng Anh cho tới khi được duyệt lại. Rất dễ thấy. |
| **Khay — Âm lượng** | `plasma_applet_org.kde.plasma.volume` (gói **plasma-pa**) | **0%** (164 chưa dịch) | [cần xác minh trên ISO] nhưng gần như chắc trống. Cực kỳ dễ thấy. |
| **Khay — Mạng/Wi-Fi** | `plasma_applet_org.kde.plasma.networkmanagement` + `plasmanetworkmanagement*` (gói **plasma-nm**) | **0%** (≈1893 chưa dịch) | Dễ thấy ngay. Nhiều chuỗi nhất trong nhóm khay. |
| **Khay — Pin & độ sáng** | `plasma_applet_org.kde.plasma.battery` + **powerdevil** | battery (plasma-workspace) ~ một phần; powerdevil ~22% | Thông báo pin/sạc/tiết kiệm điện phần lớn còn tiếng Anh. |
| **Khay — Thông báo / Khay chung / Bảng tạm (Klipper)** | plasmashell applets (gói **plasma-workspace**) | plasma-workspace ~68% | Phần lớn đã có vi; còn vài chuỗi mới. |
| **Đồng hồ + Lịch** | `plasma_applet_org.kde.plasma.digitalclock` (gói **plasma-workspace**) | ~ theo plasma-workspace (~68%) | Tên tháng/thứ lấy từ **locale** (glibc/CLDR), không từ domain này. |
| **Màn khoá / Đăng nhập (SDDM + lookandfeel)** | **sddm** + `plasma_lookandfeel_org.kde.breeze.desktop` (plasma-workspace) | lookandfeel ~ theo plasma-workspace | NaMiOS **autologin** nên màn SDDM gần như không thấy; màn Khoá đã TẮT (`kscreenlockerrc`). |
| **Hộp thoại Đăng xuất/Tắt máy/Khởi động lại** | logout greeter — `plasma_lookandfeel*` / ksmserver (gói **plasma-workspace**) | ~68% | "Shut Down/Restart/Log Out" có thể đã có vi — [cần xác minh]. |
| **Trình quản lý tệp Dolphin**: menu, thanh công cụ | **dolphin** + **dolphin-plugins** | ~61% | Menu lõi phần lớn có vi; còn rải rác. |
| **Dolphin — panel Nơi chốn** (Home/Desktop/Downloads/Trash/Network…) | **kio** framework (`kf6_kio` / `kfileplacesmodel`) | [cần xác minh trên ISO] (frameworks không nằm trong stats GUI) | Tên nơi chốn do KIO sinh; nếu KIO thiếu vi → ra tiếng Anh. Rất dễ thấy. |
| **Hộp thoại Mở/Lưu tệp** | **kio** / **kfilewidgets** / **kxmlgui** (frameworks) | [cần xác minh trên ISO] | Nút Mở/Lưu/Hủy, "File name", "Places", "New Folder". |
| **Menu chuẩn ứng dụng** (File/Edit/View/Help, "Configure…") | **kxmlgui** / **kconfigwidgets** (frameworks) | [cần xác minh trên ISO] | Dùng chung mọi app KDE. |
| **Trung tâm phần mềm (Discover)** | **discover** / **plasma-discover** | **~5%** (45 dịch / 171 fuzzy / 593 chưa) | Top-level app dễ thấy, gần như trống. |
| **Cài đặt hệ thống — tên nhóm cấp cao** | **systemsettings** (vỏ) | ~67% (vỏ nhỏ, 82 chuỗi) | Tên từng KCM đến từ hàng chục gói khác → độ phủ lệch nhau. |
| **Cài đặt — Màn hình/Hiển thị (KScreen)** | **kscreen** | **0%** (152 chưa) | KCM hiển thị trống vi. |
| **Hộp thoại quyền (polkit)** | **polkit-kde-agent-1** | ~73% | "Authentication Required", nút xác thực — phần lớn đã có vi. |
| **Hỏi mật khẩu SSH/khoá** | **ksshaskpass** | ~73% | Ít thấy lần đầu. |
| **Theme/Breeze (tooltip, nhãn widget nền)** | **breeze** | **0%** (105 chưa) | Ít chuỗi, độ thấy thấp nhưng vẫn lộ. |
| **Konsole** (terminal) | **konsole** | ~6% dịch + ~35% fuzzy | Không mở mặc định lần đầu nhưng có trên taskbar/menu. |
| **Trình xem ảnh Gwenview** | **gwenview** | **~0%** | Mở khi bấm ảnh. |
| **Nén/giải nén Ark** | **ark** | **~0%** | Qua menu chuột phải Dolphin. |
| **Máy tính KCalc** | **kcalc** | **~0%** | Trong menu. |
| **Chụp màn hình Spectacle** | **spectacle** | **0%** (433 chưa) | Phím PrintScreen. |
| **Theo dõi hệ thống** | **plasma-systemmonitor** | **0%** (278 chưa) | Ít thấy lần đầu. |
| **Xem PDF Okular** | **okular** | ~45% | Mở PDF (mimeapps mặc định). |
| **Soạn thảo Kate** | **kate** | ~78% | Phần lớn có vi. |
| **Trình cài đặt Calamares** | **calamares** + `calamares-settings-debian` | [cần xác minh trên ISO] | Chỉ hiện khi người dùng bấm "Cài đặt"; Calamares dùng catalog Qt `.qm` riêng (khác gettext). |

> Lưu ý domain "frameworks" (kio/kxmlgui/kfilewidgets/kconfigwidgets/kwidgetsaddons/kcmutils):
> l10n.kde.org tách riêng khỏi trang "GUI apps" ở trên → **[cần xác minh trên ISO]** cho toàn nhóm.
> Đây là nhóm **dùng chung** (file dialog, menu chuẩn, nơi chốn) nên mỗi % tăng ở đây lan ra MỌI app.

---

## 2. WORKLIST ưu tiên (xếp theo độ nhìn-thấy GIẢM DẦN)

Nguyên tắc xếp: cái người dùng thấy **ngay khi vào desktop** và nơi upstream vi **còn trống** đứng trước.

| # | Hạng mục | Domain | Vì sao ưu tiên | Trạng thái upstream |
|---|---|---|---|---|
| 1 | **Khay: Âm lượng** (popup Volume) | plasma-pa | Thấy ngay ở khay, bấm là bung | **0% → làm batch1** |
| 2 | **Khay: Mạng/Wi-Fi** (popup Network) | plasma-nm | Thấy ngay, chuỗi nhiều, thao tác đầu tiên của người mới | **0% → làm batch1** |
| 3 | **Nút Bắt đầu (Kickoff)**: tab Ứng dụng/Nơi chốn/Lịch sử + ô "Tìm kiếm…" + Nguồn/Khởi động lại/Tắt máy | plasma-desktop (kickoff) + session actions | Bề mặt bấm NHIỀU nhất; nhiều chuỗi đang **fuzzy** = hiện tiếng Anh | ~30% + fuzzy → **làm batch1** (ưu tiên chuỗi fuzzy/trống) |
| 4 | **Khay: Pin & độ sáng + chế độ điện** | battery + powerdevil | Laptop thấy ngay; "Charging/Power Save…" còn tiếng Anh | battery một phần / powerdevil ~22% → **làm batch1** |
| 5 | **Dolphin — panel Nơi chốn** (Home/Desktop/Tài liệu/Tải xuống/Thùng rác/Mạng) | kio (kfileplacesmodel) | Mở Dolphin là thấy cột trái; tên nơi chốn hay lộ tiếng Anh | [cần xác minh] → **làm batch1 (đề xuất)** |
| 6 | **Hộp thoại Mở/Lưu tệp** (nút Mở/Lưu/Hủy, "Tên tệp", "Nơi chốn", "Thư mục mới") | kio/kfilewidgets/kxmlgui | Mọi app gọi tới; lưu tài liệu lần đầu là gặp | [cần xác minh] → **làm batch1 (đề xuất)** |
| 7 | **Menu chuột phải desktop** + chế độ chỉnh sửa/Thêm tiện ích | plasmashell/plasma-desktop | Hành vi khám phá đầu tiên của người mới | một phần → **làm batch1** |
| 8 | **Thông báo + Bảng tạm (Klipper) + Khay chung** | plasma-workspace | Popup khay; phần lớn có vi, vá chuỗi mới | ~68% → **làm batch1 (bù phần thiếu)** |
| 9 | **Trung tâm phần mềm (Discover)**: điều hướng Cài/Gỡ/Cập nhật/Đã cài | discover | App top-level, gần như trống vi | ~5% → **làm batch1** |
| 10 | **Hộp thoại quyền (polkit)**: "Cần xác thực", nút Xác thực/Hủy | polkit-kde-agent-1 | Hiện khi cài phần mềm/đổi cài đặt hệ thống | ~73% → **vá phần thiếu (batch2)** |
| 11 | Hộp thoại Đăng xuất/Tắt máy/Khởi động lại (greeter) | plasma-workspace (lookandfeel) | Có thể đã có vi — xác minh rồi vá | ~68% [cần xác minh] → batch2 |
| 12 | Cài đặt hệ thống — tên nhóm + KScreen (Hiển thị) | systemsettings + kscreen | Vào khi chỉnh máy; KScreen 0% | kscreen 0% → batch2 |
| 13 | Đồng hồ + Lịch (nhãn "Hôm nay", định dạng) | plasma-workspace (digitalclock) | Tháng/thứ do locale; chỉ vá nhãn widget | ~68% → batch2 |
| 14 | Breeze (tooltip/nhãn nền) | breeze | 0% nhưng ít chuỗi, độ thấy thấp | 0% → batch2 |
| 15 | Ark / KCalc / Gwenview / Spectacle / Konsole / System Monitor | từng gói | Mở theo thao tác, không phải màn đầu | 0–6% → batch3 theo nhu cầu |
| 16 | Okular (PDF) | okular | Mở khi bấm PDF | ~45% → batch3 vá |
| 17 | Calamares (trình cài đặt) | calamares (.qm Qt, KHÔNG gettext) | Chỉ khi cài lên đĩa; cơ chế dịch khác | [cần xác minh] → batch riêng |

**Top 10 làm trước (batch1 tập trung #1–#9, chuẩn bị #10):** Âm lượng → Mạng → Kickoff → Pin/điện →
Nơi chốn Dolphin → Hộp thoại Mở/Lưu → Menu chuột phải desktop → Thông báo/Bảng tạm → Discover → (polkit).

---

## 3. Việc còn treo cần chốt

- **Chọn cơ chế giao hàng** (đóng góp upstream vs overlay `.mo` trong `namios-l10n-vi`) → viết ADR.
- **Xác minh trên ISO thật**: dump `.mo` của từng domain trong chroot/ISO để chốt con số % và danh sách
  `msgid` còn trống (mọi dòng [cần xác minh trên ISO] ở trên).
- **Calamares** dùng dịch Qt `.qm` (không phải gettext `.mo`) → cần nhánh công việc riêng nếu muốn Việt hoá
  trình cài đặt; `calamares-settings-debian` quyết định chuỗi branding.
- **Tên nơi chốn & tháng/thứ**: một phần đến từ **glibc/CLDR locale** (không phải catalog KDE) — xác minh
  `vi_VN` CLDR đủ chưa trước khi dịch tay (tránh trùng việc).
- Giữ **glossary thống nhất** (xem `translations/vi-overlay/GLOSSARY-and-batch1.md`) cho mọi batch.
