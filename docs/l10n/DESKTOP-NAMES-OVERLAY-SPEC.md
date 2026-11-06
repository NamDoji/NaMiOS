# NaMiOS — Đặc tả lớp phủ TÊN `.desktop` / `.directory` / metadata (desktop-names overlay)

> **Phạm vi:** MẢNG CUỐI của giao diện còn tiếng Anh — các chuỗi **KHÔNG** nằm trong
> catalog gettext `.mo`, nên **lớp phủ `vi_NM` hiện có (SPEC §4.1) KHÔNG với tới**:
> 1. Tên **nhóm/mục trong Cài đặt hệ thống** (systemsettings category) — file `.desktop`.
> 2. Tên **mục nhóm ứng dụng trong Kickoff** (menu desktop) — file `.directory`.
> 3. Tên + mô tả **ứng dụng trong menu Bắt đầu** — `Name`/`GenericName`/`Comment` trong `*.desktop`.
> 4. Tên **mục Cài đặt / Trung tâm thông tin (KCM/kinfocenter)** + **cảm biến/trang bộ theo dõi
>    hệ thống (libksysguard/plasma-systemmonitor)** — phần lớn là **metadata JSON nhúng
>    (KPluginMetaData)** hoặc **vẫn là gettext**, KHÔNG phải `.desktop` → §6 nói rõ.
>
> **TRUNG THỰC:** cơ chế dưới đây dẫn URL spec/manpage/nguồn KDE. Chuỗi gốc + việc "upstream
> đã có vi hay chưa" đã **đối chiếu mã nguồn KDE thật** cho các app/nhóm nêu tên; chỗ nào CHƯA
> soi được đánh dấu **[cần xác minh trên ISB]** (ISB = ảnh/snapshot Debian 13 trixie đã build) —
> KHÔNG coi là chắc. Soạn 2026-11-07.

---

## 0. Tóm tắt điều hành (đọc trước)

1. **Vì sao `vi_NM` không cứu được mảng này.** Giá trị `Name`/`GenericName`/`Comment` trong
   `.desktop`/`.directory` được chọn theo **hậu tố locale ngay trong file** (`Name[vi]=…`), **khớp
   theo `LC_MESSAGES`** của tiến trình (`vi_VN` → `vi` → giá trị mặc định), **không đi qua gettext,
   không đọc catalog `.mo`, và `vi_NM` KHÔNG phải một mã locale khớp được** (LC_MESSAGES=`vi_VN`
   chỉ khớp `vi_VN`, `vi`, rồi mặc định — xem §2, [spec localized-keys]). → Muốn Việt hoá mảng này
   phải **ghi/sửa đúng khoá `Name[vi]=` trong chính file**, không thể dựa `vi_NM:…` của lớp phủ `.mo`.
2. **Độ phủ upstream của mảng này LỆCH và đôi khi SAI.** Đã soi mã nguồn KDE:
   - App: konsole, spectacle, discover, plasma-systemmonitor **chưa có `Name[vi]` nào**;
     kcalc/ark **có `GenericName[vi]` nhưng THIẾU `Comment[vi]`**; okular/kate **đủ cả 3**;
     dolphin **có vi NHƯNG `Comment[vi]` lại là tiếng Bồ Đào Nha** ("Gerencie seus arquivos" — lỗi
     upstream thật, cần sửa).
   - Nhóm Cài đặt hệ thống (`systemsettings/categories/*.desktop`): "Appearance & Style",
     "Networking", "Display & Monitor", "Language & Time", "System"… **thiếu `Name[vi]`**; chỉ
     "Workspace"/"Personalization" là đã có vi.
   - Nhóm Kickoff (`desktop-directories/kf5-*.directory`): phần lớn **đã có vi** ("Đồ hoạ", "Hệ
     thống", "Tiện ích"…) nhờ l10n plasma-workspace → lớp phủ ở đây **nhẹ**.
3. **Cơ chế khuyến nghị (§3):** **tạo bản SHADOW trong `/usr/local/share/…` + chèn/ghi đè CHỈ các
   khoá `Name[vi]`/`GenericName[vi]`/`Comment[vi]`** bằng hook build chroot. `/usr/local/share` đứng
   TRƯỚC `/usr/share` trong `XDG_DATA_DIRS` (mặc định) → bản shadow thắng mà **KHÔNG sửa file gói
   gốc** (sạch dpkg, tháo được bằng xoá file `/usr/local`). Dự phòng cho bề mặt KService hay nhân đôi:
   sửa tại chỗ (§3.3). Phương án `vi_NM` **không áp dụng** cho mảng này.
4. **KCM/kinfocenter/cảm biến (§6):** phần lớn là **metadata JSON nhúng** (dịch khi chạy qua
   `KPluginMetaData` + domain gettext đã đổi tên theo KCM) hoặc **thuần gettext** → **thuộc lớp phủ
   `vi_NM` `.mo`** (đã có `plasma-systemmonitor.vi_NM.po`, `kscreen.vi_NM.po`…), **không** thuộc lớp
   phủ `.desktop` này. Trường hợp tên bị **nướng cứng `Name[vi]` trong JSON** thì cần lớp phủ JSON
   riêng — **[cần xác minh trên ISB]** bằng cách soi JSON thật.

---

## 1. Phân loại bề mặt — cái nào `.desktop`, cái nào JSON, cái nào gettext

| Bề mặt người dùng | Cơ chế dịch THẬT | File / vị trí | Lớp phủ đúng |
|---|---|---|---|
| **Tên + mô tả app trong menu Bắt đầu** (Name/GenericName/Comment) | **`.desktop` localestring** (`Name[vi]`) | `/usr/share/applications/org.kde.*.desktop` | **desktop-names (tài liệu này)** |
| **Nhóm trong Cài đặt hệ thống** (Appearance, Hardware…) | **`.desktop` localestring** (`Name[vi]`), `Type=Service` | `/usr/share/systemsettings/categories/settings-*.desktop` | **desktop-names (tài liệu này)** |
| **Nhóm ứng dụng trong Kickoff** (Đồ hoạ, Hệ thống…) | **`.directory` localestring** (`Name[vi]`), `Type=Directory` | `/usr/share/desktop-directories/kf5-*.directory` | **desktop-names (tài liệu này)** |
| **Tên từng mục KCM** trong Cài đặt (Wallpaper, Mouse…) | **JSON nhúng** `KPluginMetaData` → dịch khi chạy (i18n domain theo KCM) hoặc `Name[vi]` nướng trong JSON | `.so` plugin + JSON; KCM plugin `kcm_*` | **`vi_NM` `.mo`** (domain `kcm_*`) · nếu nướng JSON → **lớp phủ JSON (§6)** · [cần xác minh ISB] |
| **Mục Trung tâm thông tin (kinfocenter)** | như KCM (JSON nhúng) | plugin `kcm_*`/`kinfocenter` | như trên — chủ yếu **`vi_NM` `.mo`** |
| **Tên cảm biến / trang bộ theo dõi hệ thống** (CPU, RAM, "Application History"…) | **gettext** (domain `plasma-systemmonitor`, `ksystemstats`, `libksysguard`) | catalog `.mo` | **`vi_NM` `.mo`** (đã có `plasma-systemmonitor.vi_NM.po`) |
| **Tên "mặt đồng hồ" cảm biến (sensor face)** | **KPackage metadata.json** `Name`/`Name[vi]` (thuộc tính XDG desktop) | `/usr/share/ksysguard/sensorfaces/<id>/metadata.json` | **lớp phủ JSON (§6)** · [cần xác minh ISB] |

**Bằng chứng (đã soi nguồn KDE):**
- systemsettings categories là `.desktop` `Type=Service`, có `X-KDE-System-Settings-Category=…`,
  cài ở `systemsettings/categories/` — danh sách 27 file (§5.2). Nguồn:
  <https://invent.kde.org/plasma/systemsettings/-/tree/master/categories>
- Kickoff/menu dùng `.directory` trong `menu/desktop/kf5-*.directory` (41 file). Nguồn:
  <https://invent.kde.org/plasma/plasma-workspace/-/tree/master/menu/desktop>
- KCM Plasma 6 dùng `KPluginMetaData` (JSON nhúng), "translation domains … renamed to match the
  KCM plugin name"; `desktoptojson` nhúng các khoá `Name[xx]` localized vào JSON. Nguồn:
  <https://develop.kde.org/docs/features/configuration/porting_kf6/> ·
  <https://api.kde.org/kpluginmetadata.html> ·
  <https://codebrowser.dev/kde/kcoreaddons/src/lib/plugin/kpluginmetadata.h.html>
- Sensor face là KPackage, `metadata.json` chứa `Name`/`Name[fr]` "based on standard XDG desktop
  file properties"; cài ở `ksysguard/sensorfaces/`. Nguồn:
  <https://develop.kde.org/docs/apps/sensor-faces/>

---

## 2. Cơ chế `.desktop`/`.directory` localized keys — vì sao bắt buộc `Name[vi]`

- Khoá kiểu `localestring`/`iconstring` có thể có hậu tố `[LOCALE]`; **giá trị được chọn bằng cách
  khớp locale POSIX hiện tại của mục `LC_MESSAGES`** với các hậu tố, theo thứ tự
  `lang_COUNTRY@MODIFIER → lang_COUNTRY → lang@MODIFIER → lang → (mặc định không hậu tố)`.
  Nguồn: [spec localized-keys] <https://specifications.freedesktop.org/desktop-entry/latest/localized-keys.html>
- NaMiOS đặt `LANG=vi_VN.UTF-8` (hook `0100-locale-vi`) → `LC_MESSAGES` hiệu dụng = `vi_VN` →
  thứ tự khớp: **`Name[vi_VN]` → `Name[vi]` → `Name=`**. Vậy **`Name[vi]` là khoá đúng** và nó Việt
  hoá được **bất kể** biến `LANGUAGE`.
- **Hệ quả quyết định:** `vi_NM` của lớp phủ `.mo` **không phải** một hậu tố locale mà spec khớp
  tới (LC_MESSAGES=`vi_VN` không bao giờ khớp `vi_NM`). Dù một số bản hiện thực (GLib
  `g_get_language_names`, KConfig của KDE) có đọc thêm `LANGUAGE` để nới danh sách ngôn ngữ, **điểm
  chung an toàn cho MỌI bản hiện thực là `Name[vi]`** (khớp cả `LC_MESSAGES=vi_VN` lẫn `LANGUAGE=…vi…`).
  → Lớp phủ này **chỉ dùng hậu tố `[vi]`**, không dùng `vi_NM`.
- **Ghi đè theo TỪNG KHOÁ:** nếu upstream đã có `Name[vi]=X` thì ghi `Name[vi]=Y` sẽ thắng X; nếu
  thiếu thì thêm mới. Không đụng `Exec`, `Icon`, `MimeType`, `Categories`… (giữ nguyên chức năng).

---

## 3. Cơ chế GHI ĐÈ / BỔ SUNG — 3 phương án + khuyến nghị

Yêu cầu: **không sửa file gốc của gói**, hợp ảnh Live (squashfs, không có đường nâng cấp apt).

### 3.1 PA-A (KHUYẾN NGHỊ) — bản shadow trong `/usr/local/share` + chèn khoá `[vi]`

- `XDG_DATA_DIRS` là **tập thư mục có THỨ TỰ ƯU TIÊN**; mặc định = `/usr/local/share:/usr/share`
  (file nào tìm thấy ở thư mục đứng trước THẮNG). Nguồn: [basedir spec]
  <https://specifications.freedesktop.org/basedir/latest/>
- **Luồng (hook build, chạy trong chroot SAU khi cài gói):** với mỗi `relpath` cần Việt hoá
  (vd `applications/org.kde.konsole.desktop`):
  1. `install -D /usr/share/$relpath /usr/local/share/$relpath` (sao **nguyên văn** bản đang cài →
     `Exec`/`Icon` khớp đúng gói thật trong ảnh, không phải tái bản tay).
  2. Chèn/ghi đè **chỉ** các khoá `Name[vi]` / `GenericName[vi]` / `Comment[vi]` trên **bản sao**
     (§4 — `desktop-file-edit` hoặc `kwriteconfig6`).
  3. (Tuỳ) `desktop-file-validate` bản sao.
- App launcher (Kickoff, KRunner) phân giải app theo **desktop-file-id** qua `XDG_DATA_DIRS`,
  **bản ở `/usr/local/share/applications` che bản ở `/usr/share/applications` theo đúng id** → thắng.
  Menu `.directory` cũng tra trong `desktop-directories` theo thứ tự data-dir.
- **Ưu:** KHÔNG đụng file gói (sạch dpkg, tháo bằng cách xoá `/usr/local/share/…`); đúng chuẩn
  XDG; không phải bảo trì tay `Exec/Icon` (sao nguyên văn từ snapshot); đồng nhất cho app + `.directory`.
- **Nhược/rủi ro:** bản sao là **toàn file** → nếu một ngày phát qua apt (không phải Live) thì bản
  sao có thể lệch bản gói khi gói nâng cấp (với ảnh Live thì vô hại vì cả hai cùng một snapshot).
  Với **systemsettings categories (`Type=Service`, KService/ksycoca)** cần **xác minh** ksycoca
  khử trùng (dedupe) theo `X-KDE-System-Settings-Category` lấy bản ƯU TIÊN nào — nếu nó gộp cả hai /
  nhân đôi nhóm thì chuyển các file đó sang §3.3. **[cần xác minh trên ISB]**

### 3.2 PA-B — `desktop-file-install --dir=/usr/local/share/applications` lúc build

- Dùng `desktop-file-install` để cài bản `.desktop` đã gắn `--set-key=Name[vi]` vào
  `/usr/local/share/applications`. Cơ chế che = y hệt PA-A (vẫn dựa XDG precedence), chỉ khác công cụ.
- **Nhược:** `desktop-file-install` **validate** và có thể từ chối khoá/`Type` mở rộng của KDE
  (`Type=Service`, nhiều `X-KDE-*`) → **không hợp** cho systemsettings categories / `.directory`.
  Hẹp hơn PA-A. Nguồn (validate có thể làm abort):
  <https://manpages.debian.org/testing/desktop-file-utils/desktop-file-edit.1.en.html>

### 3.3 PA-C (DỰ PHÒNG) — sửa TẠI CHỖ trong `/usr/share` (in-place, chỉ thêm khoá `[vi]`)

- Hook chroot chèn thẳng `Name[vi]=…` vào file trong `/usr/share/...` (chỉ thêm khoá localized,
  không đụng khoá chức năng), **giống SPEC §4.2** (ghi đè in-place đã được chấp nhận cho ảnh Live).
- **Ưu:** rủi ro chức năng thấp nhất, **không** gặp vấn đề dedupe của KService (file ở đúng chỗ cũ,
  chỉ giàu thêm 1 khoá); không staleness.
- **Nhược:** **có** sửa file gói sở hữu (chấp nhận trong squashfs; **không** dùng cho kênh `.deb`/apt).
- Dùng khi PA-A nhân đôi nhóm Cài đặt hệ thống, hoặc cho bất kỳ bề mặt KService nào che không ăn.

### 3.4 Bảng so sánh

| Tiêu chí | PA-A shadow `/usr/local` | PA-B desktop-file-install | PA-C in-place `/usr/share` |
|---|---|---|---|
| Đụng file gói | **Không** | **Không** | Có |
| Chuẩn hoá cơ chế | XDG precedence | XDG precedence | — |
| Hợp app `.desktop` | **Có** | Có | Có |
| Hợp `.directory` / `Type=Service` | **Có** (dùng kwriteconfig6) | Hạn chế (validate chặn) | **Có** |
| Giữ `Exec/Icon` tự động | **Có** (sao nguyên văn) | Có | **Có** (không đụng) |
| Rủi ro dedupe KService | Cần xác minh | Cần xác minh | **Không** |
| Hợp kênh apt sau này | Hạn chế (staleness) | Hạn chế | Không |

**KHUYẾN NGHỊ:** **PA-A** làm cơ chế chính (không đụng gói + đúng XDG), **PA-C** làm dự phòng cho
các file systemsettings categories nếu ISB cho thấy KService nhân đôi nhóm. PA-B chỉ dùng nếu đã
có sẵn `desktop-file-utils` và chỉ cho app `Type=Application`.

---

## 4. Công cụ chỉnh khoá `[vi]` (trong hook chroot)

| Công cụ | Gói | Mạnh | Yếu |
|---|---|---|---|
| `desktop-file-edit --set-key="Name[vi]" --set-value="…"` | `desktop-file-utils` | chuẩn freedesktop, hỗ trợ khoá localized `Name[de]`; tự validate | **validate** có thể **abort** với `Type=Service`/`Type=Directory` + `X-KDE-*`; phải cài thêm gói (rồi purge) |
| `kwriteconfig6 --file <path> --group "Desktop Entry" --key "Name[vi]" "…"` | `kconfig` (**đã có sẵn** trong ảnh KDE) | ghi mọi file kiểu INI (`.desktop`/`.directory`/`Type=Service`) **không validate khắt khe**; không cần cài thêm | KConfig **viết lại/chuẩn hoá** file (có thể bỏ comment, đổi thứ tự khoá) — với bản **shadow** `/usr/local` thì vô hại; **cú pháp khoá localized cần xác minh** trên KConfig 6 **[cần xác minh trên ISB]** |

- Khuyến nghị: **`desktop-file-edit`** cho app `Type=Application` (đã xác nhận hỗ trợ `--set-key=Name[de]`,
  manpage Debian ở trên); **`kwriteconfig6`** cho `.directory` + systemsettings `Type=Service` (native
  KDE, sẵn trong ảnh, không kén `Type`). Cả hai chạy trên **bản sao** `/usr/local` (PA-A).
- Nếu muốn **không cài thêm gói nào**: dùng `kwriteconfig6` cho tất cả → zero dependency mới trong ảnh.

---

## 5. MAPPING DỊCH (theo glossary `translations/vi-overlay/GLOSSARY-and-batch1.md`)

> Quy ước: "**đã có**" = upstream đã có `[vi]` tốt → **khỏi đè**. "**bù**" = thiếu → thêm.
> "**sửa**" = upstream có nhưng SAI → ghi đè. Chuỗi gốc + tình trạng vi đã soi mã nguồn KDE cho các
> dòng không đánh dấu; dòng có **[cần xác minh trên ISB]** thì chưa soi được file đó.

### 5.1 Ứng dụng (`/usr/share/applications/…`) — Name / GenericName / Comment

| App (desktop-file-id) | Name= (gốc) | GenericName= / Comment= (gốc) | Tình trạng vi upstream | Hành động overlay (vi đề xuất) |
|---|---|---|---|---|
| `org.kde.konsole` | Konsole | Terminal / Use the command line | **Chưa có vi** | bù `GenericName[vi]=Dòng lệnh` · `Comment[vi]=Dùng dòng lệnh` |
| `org.kde.dolphin` | Dolphin | File Manager / Manage your files | `GenericName[vi]=Trình quản lí tệp` **đã có**; **`Comment[vi]` SAI = tiếng Bồ** ("Gerencie seus arquivos") | giữ GenericName; **sửa** `Comment[vi]=Quản lí tệp của bạn` |
| `org.kde.okular` | Okular | Document Viewer / Universal document viewer | **đủ cả 3** (`Trình xem tài liệu` / `Trình xem tài liệu vạn năng`) | **khỏi đè** |
| `org.kde.kate` | Kate | Advanced Text Editor / KDE Advanced Text Editor | **đủ cả 3** (`Trình biên tập văn bản nâng cao`…) | **khỏi đè** |
| `org.kde.gwenview` | Gwenview | Image Viewer / A simple image viewer | `GenericName[vi]=Bộ xem ảnh đơn giản`, `Comment[vi]=Bộ xem ảnh đơn giản` **đã có** (GenericName hơi lệch nghĩa) | **khỏi đè** (tuỳ chọn tinh chỉnh `GenericName[vi]=Trình xem ảnh`) |
| `org.kde.kcalc` | KCalc | Scientific Calculator / Calculator which offers many mathematical functions… | `GenericName[vi]=Máy Tính Khoa Học` **đã có** (hoa lạ); **`Comment[vi]` thiếu** | bù `Comment[vi]=Máy tính với nhiều hàm toán học: lượng giác, logic, thống kê` (tuỳ chọn `GenericName[vi]=Máy tính khoa học`) |
| `org.kde.ark` | Ark | Archiving Tool / Work with file archives | `GenericName[vi]=Công Cụ Nén` **đã có** (hoa lạ); **`Comment[vi]` thiếu** | bù `Comment[vi]=Nén và giải nén tệp` (tuỳ chọn `GenericName[vi]=Công cụ nén`) |
| `org.kde.spectacle` | Spectacle | Screenshot Capture Utility / Take screenshots and screen recordings | **Chưa có vi** | bù `GenericName[vi]=Công cụ chụp màn hình` · `Comment[vi]=Chụp ảnh và quay màn hình` |
| `org.kde.discover` | Discover | Software Center / Install and remove apps and add-ons | **Chưa có vi** | bù `GenericName[vi]=Trung tâm phần mềm` · `Comment[vi]=Cài đặt và gỡ ứng dụng, tiện ích bổ sung` · **(DUYỆT)** `Name[vi]=Trung tâm phần mềm`? (brand vs dịch) |
| `org.kde.kinfocenter` | Info Center | Info Center / Learn about the system's hardware and status | `Name[vi]=Trung tâm thông tin`, `GenericName[vi]` **đã có**; **`Comment[vi]` thiếu** | bù `Comment[vi]=Xem thông tin phần cứng và trạng thái hệ thống` |
| `org.kde.plasma-systemmonitor` | System Monitor | System Monitor / Monitor app and system resource usage | **Chưa có vi** | bù `Name[vi]=Theo dõi hệ thống` · `GenericName[vi]=Theo dõi hệ thống` · `Comment[vi]=Theo dõi mức dùng tài nguyên của ứng dụng và hệ thống` |
| `org.kde.kwrite` | KWrite | Text Editor / … | **[cần xác minh trên ISB]** (chung repo kate, có thể đã có vi) | nếu thiếu: `GenericName[vi]=Trình biên tập văn bản` |

### 5.2 Nhóm Cài đặt hệ thống (`/usr/share/systemsettings/categories/settings-*.desktop`)

27 file (gồm `hidden.desktop`, `settings-root-category.desktop`, `CMakeLists.txt`). Nhóm người dùng
thấy + hành động:

| File `.desktop` | Name= (gốc) | vi upstream | vi đề xuất (`Name[vi]=`) |
|---|---|---|---|
| `settings-appearance` | Appearance & Style | **thiếu** | Giao diện & Kiểu dáng |
| `settings-appearance-font` | [cần xác minh ISB] (Text & Fonts?) | [cần xác minh] | Phông chữ |
| `settings-appearance-themes` | [cần xác minh ISB] (Colors & Themes?) | [cần xác minh] | Màu sắc & Chủ đề |
| `settings-workspace` | Workspace | **đã có** (`Không gian làm việc`) | **khỏi đè** |
| `settings-workspace-search` | [cần xác minh ISB] (Search?) | [cần xác minh] | Tìm kiếm |
| `settings-workspace-session` | [cần xác minh ISB] (Session?) | [cần xác minh] | Phiên làm việc |
| `settings-workspace-windowmanagement` | [cần xác minh ISB] (Window Management?) | [cần xác minh] | Quản lí cửa sổ |
| `settings-personalization` | Personalization | **đã có** (`Cá nhân hoá`) | **khỏi đè** |
| `settings-network` | Networking | **thiếu** | Mạng |
| `settings-network-networksettings` | [cần xác minh ISB] (Connections?) | [cần xác minh] | Kết nối |
| `settings-hardware` | [cần xác minh ISB] (Hardware?) | [cần xác minh] | Phần cứng |
| `settings-hardware-display` | Display & Monitor | **thiếu** | Màn hình & Hiển thị |
| `settings-hardware-input` | [cần xác minh ISB] (Input Devices?) | [cần xác minh] | Thiết bị nhập |
| `settings-hardware-input-pointing-devices` | [cần xác minh ISB] | [cần xác minh] | Thiết bị trỏ |
| `settings-hardware-input-touchscreen` | [cần xác minh ISB] | [cần xác minh] | Màn hình cảm ứng |
| `settings-hardware-keyboard` | [cần xác minh ISB] (Keyboard?) | [cần xác minh] | Bàn phím |
| `settings-hardware-multimedia` | [cần xác minh ISB] (Audio?) | [cần xác minh] | Âm thanh & Đa phương tiện |
| `settings-hardware-removable-storage` | [cần xác minh ISB] | [cần xác minh] | Lưu trữ tháo lắp |
| `settings-applications` | [cần xác minh ISB] (Applications?) | [cần xác minh] | Ứng dụng |
| `settings-applications-defaults` | [cần xác minh ISB] (Default Applications?) | [cần xác minh] | Ứng dụng mặc định |
| `settings-applications-permissions` | [cần xác minh ISB] | [cần xác minh] | Quyền ứng dụng |
| `settings-regionalsettings` | Language & Time | **thiếu** | Ngôn ngữ & Thời gian |
| `settings-security-privacy` | [cần xác minh ISB] (Security & Privacy?) | [cần xác minh] | Bảo mật & Riêng tư |
| `settings-system-administration` | System | **thiếu** | Hệ thống |

Danh sách file: <https://invent.kde.org/plasma/systemsettings/-/tree/master/categories>

### 5.3 Nhóm ứng dụng Kickoff (`/usr/share/desktop-directories/kf5-*.directory`)

Phần lớn **đã có vi** (l10n plasma-workspace). Chỉ bù những cái ISB cho thấy còn trống.

| File `.directory` | Name= (gốc) | vi upstream | vi đề xuất |
|---|---|---|---|
| `kf5-graphics` | Graphics | **đã có** (`Đồ hoạ`) | khỏi đè |
| `kf5-system` | System | **đã có** (`Hệ thống`) | khỏi đè |
| `kf5-utilities` | Utilities | **đã có** (`Tiện ích`) | khỏi đè |
| `kf5-development` | Development | [cần xác minh] | Phát triển |
| `kf5-editors` | Editors | [cần xác minh] | Trình biên tập |
| `kf5-education` | Education | [cần xác minh] | Giáo dục |
| `kf5-games` | Games | [cần xác minh] | Trò chơi |
| `kf5-internet` | Internet | [cần xác minh] | Internet |
| `kf5-multimedia` | Multimedia | [cần xác minh] | Đa phương tiện |
| `kf5-office` | Office | [cần xác minh] | Văn phòng |
| `kf5-science` | Science | [cần xác minh] | Khoa học |
| `kf5-settingsmenu` | Settings | [cần xác minh] | Cài đặt |

Danh sách file (41): <https://invent.kde.org/plasma/plasma-workspace/-/tree/master/menu/desktop>

---

## 6. KCM / kinfocenter / cảm biến — KHÔNG thuộc lớp phủ `.desktop`

- **Tên từng mục KCM trong Cài đặt** (vd "Wallpaper", "Mouse", "Display Configuration") và **mục
  kinfocenter** ("About this System", "Memory", "PCI", "Energy Information"…) ở Plasma 6 là
  **metadata JSON nhúng** trong plugin (`KPluginMetaData`). `KPluginMetaData::name()` trả về chuỗi
  đã bản địa hoá; tên được **dịch khi chạy qua domain gettext đã đổi theo tên KCM** (vd `kcm_mouse`,
  `kcm_kscreen`) **và/hoặc** `Name[vi]` **nướng cứng trong JSON** (do `desktoptojson` nhúng từ
  `.desktop` nguồn). → **Nếu là đường gettext** thì **thuộc lớp phủ `vi_NM` `.mo`** (chỉ cần thêm
  `kcm_<x>.vi_NM.po` với đúng domain). **Nếu nướng cứng JSON** thì cần **lớp phủ JSON riêng** (ghi
  `Name[vi]` vào bản sao JSON ở `/usr/local/share/...` theo cùng tư tưởng PA-A). **[cần xác minh trên
  ISB]**: soi vài plugin —
  `dpkg -L … | grep kcm` → đọc JSON nhúng (`kreadconfig6`/`strings`) xem có `Name[vi]` chưa, và chạy
  thử domain gettext để biết đường nào thắng. Nguồn: §1 (porting_kf6, kpluginmetadata).
- **Tên cảm biến + trang bộ theo dõi hệ thống** ("CPU Usage", "Memory", "Application History",
  "Processes"…) là **thuần gettext** (domain `plasma-systemmonitor`, `ksystemstats`, `libksysguard`)
  → **đã nằm trong lớp phủ `vi_NM`** (`translations/vi-overlay/po/plasma-systemmonitor.vi_NM.po` đã
  có; bổ sung `ksystemstats.vi_NM.po` / `ksgrd.vi_NM.po` nếu ISB cho thấy domain riêng).
- **Tên "mặt đồng hồ" cảm biến (sensor face)** là KPackage `metadata.json` (`Name`/`Name[vi]`) ở
  `/usr/share/ksysguard/sensorfaces/<id>/metadata.json` → **lớp phủ JSON** (PA-A áp cho JSON), **[cần
  xác minh ISB]** độ phủ vi. Nguồn: <https://develop.kde.org/docs/apps/sensor-faces/>

> **Tóm lại:** mảng "tên mục KCM/kinfocenter/cảm biến" **không** giải bằng `.desktop`; nó hoặc rơi về
> **`vi_NM` `.mo`** (đa số) hoặc cần **lớp phủ JSON** (thiểu số nướng cứng) — tách khỏi lớp phủ
> desktop-names này để tránh gộp nhầm cơ chế.

---

## 7. ĐỀ XUẤT TRIỂN KHAI (theo lối `vi_NM` overlay)

### 7.1 Bố cục repo (TẠO MỚI, không đụng cái sẵn có)

```
translations/desktop-overlay/
  README.md                         # cơ chế + cách mở rộng + cách đo
  vi/
    applications.tsv                # id .desktop  <TAB> key[vi]  <TAB> value
    systemsettings-categories.tsv   # file categories <TAB> key[vi] <TAB> value
    menu-directories.tsv            # file .directory  <TAB> key[vi] <TAB> value
  # (tuỳ) sensorfaces-json.tsv       # khi chốt lớp phủ JSON (§6)
```
- **Định dạng TSV** (3 cột, bỏ dòng `#`): `relpath_under_datadir <TAB> Key[vi] <TAB> giá trị`.
  Ví dụ: `applications/org.kde.konsole.desktop <TAB> GenericName[vi] <TAB> Dòng lệnh`.
  Hook phân giải: nguồn = `/usr/share/<relpath>`, đích = `/usr/local/share/<relpath>`.

### 7.2 Hook build (ĐỀ XUẤT — thêm khi Cuong duyệt; CHƯA tạo trong live-build)

`distro/live-build/config/hooks/normal/0130-desktop-names-overlay.hook.chroot` (PA-A):
```sh
#!/bin/bash
set -euo pipefail
# An toàn (CLAUDE.md): không curl|bash, không tải từ xa; chỉ dùng công cụ đã cài.
MAP=/opt/namios-l10n/desktop-overlay   # includes.chroot copy các .tsv vào đây
EDIT="kwriteconfig6"                    # native KDE, sẵn trong ảnh, không kén Type
for tsv in "$MAP"/vi/*.tsv; do
  [ -f "$tsv" ] || continue
  # bỏ dòng trống/comment; mỗi dòng: relpath <TAB> Key[vi] <TAB> value
  while IFS=$'\t' read -r rel key val; do
    case "$rel" in ''|'#'*) continue;; esac
    src="/usr/share/$rel"; dst="/usr/local/share/$rel"
    [ -f "$src" ] || { echo "desktop-overlay: THIẾU $src (bỏ qua)"; continue; }
    install -D "$src" "$dst"            # sao nguyên văn bản đang cài (giữ Exec/Icon)
    "$EDIT" --file "$dst" --group "Desktop Entry" --key "$key" "$val"
  done < "$tsv"
done
echo "desktop-overlay: đã đặt bản shadow /usr/local/share + khoá [vi]"
```
- `.tsv` giao vào ảnh qua `config/includes.chroot/opt/namios-l10n/desktop-overlay/` (đường dẫn MỚI).
- Nếu ISB cho thấy systemsettings categories **nhân đôi** khi shadow → đổi `dst` cho các dòng đó
  thành chính `src` (PA-C in-place) trong một hook phụ, HOẶC thêm cột cờ `inplace` trong TSV.
- **Cú pháp `kwriteconfig6` cho khoá localized `Name[vi]`** cần xác minh trên ISB; nếu KConfig escape
  ngoặc vuông thì chuyển sang `desktop-file-edit --set-key="$key" --set-value="$val"` (cài +
  purge `desktop-file-utils` trong hook như SPEC §4.2).

### 7.3 Đo độ phủ (trung thực)

- Mở rộng `scripts/l10n-coverage.py` (hoặc script phụ) để **đếm theo khoá `[vi]`**: với mỗi file
  trong `applications/` + `systemsettings/categories/` + `desktop-directories/`, kiểm tra có
  `Name[vi]`/`GenericName[vi]`/`Comment[vi]` (ưu tiên bản `/usr/local/share` nếu có) → báo 3 cột:
  **upstream có `[vi]`** / **sau overlay** / **tổng file có khoá gốc**. Không báo "100%".
- Lưu artifact `docs/releases/<ver>/desktop-names-coverage.json` kèm ngày + nguồn.

---

## 8. Checklist "cần xác minh trên ISB"

- [ ] `grep -H 'Name\[vi\]\|GenericName\[vi\]\|Comment\[vi\]' /usr/share/applications/org.kde.{konsole,dolphin,okular,kate,gwenview,kcalc,ark,spectacle,discover,kinfocenter,plasma-systemmonitor,kwrite}.desktop` → chốt đúng khoá nào thiếu (xác nhận lại 5.1).
- [ ] Đọc `Name=`/`Name[vi]` thật của **24 file** `systemsettings/categories/settings-*.desktop` (điền nốt cột [cần xác minh] 5.2).
- [ ] Đọc `.directory` `kf5-*.directory` → cái nào đã có `Name[vi]` (chốt 5.3, bù cái trống).
- [ ] **Thử PA-A trên 1 app + 1 category + 1 .directory**: đặt bản shadow `/usr/local/share` + `Name[vi]` giả → xác nhận Kickoff/Settings hiện vi và **không nhân đôi** (đặc biệt systemsettings category). Nếu nhân đôi → PA-C cho nhóm đó.
- [ ] Xác minh cú pháp `kwriteconfig6 --key "Name[vi]"` (có escape `[ ]` không); fallback `desktop-file-edit`.
- [ ] `desktop-file-validate` có chấp nhận `Type=Service`/`Type=Directory` + `X-KDE-*` không (quyết định PA-B có dùng được không).
- [ ] KCM/kinfocenter: soi JSON nhúng 2-3 plugin (`kcm_mouse`, `kcm_kscreen`, kinfocenter "About") → tên dịch bằng gettext (→ `vi_NM` `.mo`) hay `Name[vi]` nướng JSON (→ lớp phủ JSON). Chốt §6.
- [ ] Sensor face `metadata.json` ở `/usr/share/ksysguard/sensorfaces/` có `Name[vi]` chưa.
- [ ] Xác nhận `XDG_DATA_DIRS` runtime của phiên Plasma X11 thật có `/usr/local/share` đứng trước (một số cấu hình kỳ lạ có thể bỏ).

---

## 9. ĐIỂM CẦN CUONG DUYỆT (trước khi ghép vào build)

1. **Có đổi `Name[vi]` tên THƯƠNG HIỆU sang tiếng Việt không?** — `Discover` → `Trung tâm phần
   mềm`? `System Monitor` → `Theo dõi hệ thống`? (menu hiện tiếng Việt vs giữ brand quốc tế). Mặc
   định đề xuất: **dịch** mục mang nghĩa mô tả (System Monitor), **giữ brand** mục là tên riêng
   (Dolphin, Okular, Kate, Ark, Konsole, Gwenview, KCalc).
2. **Chọn công cụ chỉnh:** `kwriteconfig6` (không cài thêm gói) vs `desktop-file-edit` (chuẩn FD,
   phải cài+purge). Đề xuất `kwriteconfig6`.
3. **Cơ chế chính PA-A (shadow `/usr/local`) hay PA-C (in-place)** cho systemsettings categories —
   chờ kết quả thử nhân đôi trên ISB.
4. **Mảng KCM/kinfocenter/sensor face** (§6): làm qua `vi_NM` `.mo` (thêm `kcm_*.vi_NM.po`) hay lớp
   phủ JSON — chờ soi JSON thật rồi chốt; có thể tách thành một việc riêng.
5. Duyệt bản dịch ở §5 theo glossary (giọng điệu, "Giao diện & Kiểu dáng" vs "Hình thức", v.v.).

---

## 10. Nguồn (URL đã dùng)

- Desktop Entry — localized keys (khớp LC_MESSAGES): <https://specifications.freedesktop.org/desktop-entry/latest/localized-keys.html>
- XDG Base Directory Spec (XDG_DATA_DIRS ưu tiên, mặc định `/usr/local/share:/usr/share`): <https://specifications.freedesktop.org/basedir/latest/>
- Desktop Menu Spec (`.directory`, desktop-directories): <https://specifications.freedesktop.org/menu/latest/>
- `desktop-file-edit`(1) / `desktop-file-install`(1) (`--set-key=Name[de]`, validate có thể abort): <https://manpages.debian.org/testing/desktop-file-utils/desktop-file-edit.1.en.html>
- systemsettings categories (file `.desktop`, `Type=Service`): <https://invent.kde.org/plasma/systemsettings/-/tree/master/categories>
- plasma-workspace menu `.directory`: <https://invent.kde.org/plasma/plasma-workspace/-/tree/master/menu/desktop>
- KF6 porting KCM (metadata JSON, domain đổi theo KCM): <https://develop.kde.org/docs/features/configuration/porting_kf6/>
- KPluginMetaData (name() bản địa hoá, đọc JSON): <https://api.kde.org/kpluginmetadata.html> · <https://codebrowser.dev/kde/kcoreaddons/src/lib/plugin/kpluginmetadata.h.html>
- Sensor faces (KPackage metadata.json, Name[xx] XDG): <https://develop.kde.org/docs/apps/sensor-faces/>
- Nguồn app `.desktop` đã soi: konsole <https://invent.kde.org/utilities/konsole/-/raw/master/desktop/org.kde.konsole.desktop> · dolphin <https://raw.githubusercontent.com/KDE/dolphin/master/src/org.kde.dolphin.desktop> · okular/kate/gwenview/kcalc/ark/spectacle/discover/kinfocenter/plasma-systemmonitor (repo KDE tương ứng, nhánh master).
```
