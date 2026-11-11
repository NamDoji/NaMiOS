# NaMiOS Control Panel — Bảng điều khiển NaMiOS

- **Liên quan:** ADR 0011 (`docs/adr/0011-giao-dien-quen-thuoc-va-ranh-gioi-ip.md`),
  `docs/specs/UX-WINDOWS-FAMILIAR.md` §28 UI-003 ("Cài đặt + onboarding: nhóm
  Công việc/Thiết bị/Mạng/Cá-nhân-hóa/Tài-khoản/Riêng-tư/Cập-nhật/Khôi-phục").
- **Việc này KHÔNG viết lại System Settings/KDE.** KDE đã có `systemsettings` +
  hàng chục module `kcmshell6 kcm_*` sẵn — việc này CHỈ thêm một **hub đặt tên
  kiểu Windows** (Accounts/Display/Network/Devices/Personalization/Time &
  Language/Apps/Update) để người quen Windows bấm đúng chỗ ngay lần đầu, thay
  vì phải học cấu trúc System Settings gốc của KDE.
- **verified_on_host: NO cho HÀNH VI THẬT khi bấm** (mở đúng trang, polkit hỏi
  đúng lúc, không treo) — container phát triển này **headless, không có
  desktop session KDE Plasma** (xem ADR 0011 "Bối cảnh môi trường hiện tại").
  Việc **GÓI NÀO CHẮC CHẮN CÓ MẶT** trong ảnh thì ĐÃ được xác nhận bằng cách
  tải trực tiếp `Packages.gz` + `Contents-amd64.gz` THẬT của Debian 13 trixie
  (`deb.debian.org/debian/dists/trixie/main/...`, tải ngày 11/11/2026) và dò
  theo chuỗi phụ thuộc `Depends` (không phải `Recommends` — xem §2) — đây là
  bằng chứng apt thật, không phải suy đoán tên module.

## 1. File đã tạo (tất cả MỚI, không sửa file nào khác)

| File | Vai trò |
| --- | --- |
| `usr/local/bin/namios-control-panel` | Script hub chính — menu kdialog (TTY dự phòng), 8 mục Windows-style, mỗi mục gọi `kcmshell6`/`systemsettings`/ứng dụng thật đã xác nhận có gói. |
| `usr/share/applications/namios-control-panel.desktop` | Launcher chính trong menu ứng dụng ("NaMiOS Control Panel" / "Bảng điều khiển NaMiOS"). |
| `usr/share/applications/namios-cpl-accounts.desktop` | Launcher riêng "Accounts" → `namios-control-panel --category accounts`. |
| `usr/share/applications/namios-cpl-display.desktop` | Launcher riêng "Display" → `--category display`. |
| `usr/share/applications/namios-cpl-network.desktop` | Launcher riêng "Network" → `--category network`. |
| `usr/share/applications/namios-cpl-devices.desktop` | Launcher riêng "Devices" → `--category devices`. |
| `usr/share/applications/namios-cpl-personalization.desktop` | Launcher riêng "Personalization" → `--category personalization`. |
| `usr/share/applications/namios-cpl-timelang.desktop` | Launcher riêng "Time & Language" → `--category timelang`. |
| `usr/share/applications/namios-cpl-apps.desktop` | Launcher riêng "Apps" → `--category apps`. |
| `usr/share/applications/namios-cpl-update.desktop` | Launcher riêng "Update" → `--category update`. |
| `usr/share/namios/docs/CONTROL-PANEL.md` | File này. |

Lý do có cả 1 launcher hub **và** 8 launcher riêng từng mục: Kickoff tìm kiếm
theo tên ứng dụng — một người gõ "network"/"mang" trong tìm kiếm nên thấy
thẳng kết quả "Network/Mạng" (giống gõ trong Windows Search), không bắt buộc
phải mở hub rồi chọn tiếp. Mỗi launcher riêng gọi `--category <id>` nên mở
thẳng mục đó rồi thoát — không quay lại menu 8 mục (khác với mở từ hub, vòng
lặp quay lại menu chính sau khi đóng một mục).

## 2. Chuỗi phụ thuộc apt đã xác nhận ("Depends-chain")

Mọi gói liệt kê dưới đây được xác nhận **CHẮC CHẮN CÓ MẶT** trong ảnh NaMiOS
qua chuỗi `Depends` cứng sau (không phụ thuộc vào việc `lb build` có bật cài
`Recommends` hay không — vấn đề này đang bỏ ngỏ ở nơi khác trong repo, xem
`package-lists/0680-peripherals-extra.list.chroot` và
`package-lists/0700-printing.list.chroot`):

```
task-kde-desktop (package-lists/0100-desktop-kde.list.chroot, khai tường minh)
  --Depends--> kde-standard
    --Depends--> kde-plasma-desktop
      --Depends--> plasma-desktop   (kéo theo: accountsservice, breeze,
      |                              kde-cli-tools, polkit-kde-agent-1 — đều
      |                              Depends CỨNG của plasma-desktop)
      |              --Depends--> breeze --Depends--> breeze-icon-theme
      --Depends--> plasma-workspace
```

→ `plasma-desktop` và `plasma-workspace` **chắc chắn có mặt**, nên MỌI KCM do
hai gói này cung cấp cũng chắc chắn có mặt — không cần `Recommends`.

Ngoài ra, các gói sau đã được **khai báo tường minh** (hard package, không
phải Recommends) ở các file `package-lists/*.list.chroot` hiện có (việc này
KHÔNG sửa các file đó, chỉ đọc lại để xác nhận): `kscreen`, `plasma-nm`,
`plasma-pa`, `plasma-discover` (`0100-desktop-kde.list.chroot`), `bluedevil`
(`0180-bluetooth-power-time.list.chroot`), `print-manager`
(`0500-print.list.chroot`).

**Phát hiện đáng chú ý:** `print-manager` có `Depends` **cứng** vào gói
`systemsettings` (xác nhận qua `Packages.gz` thật). Vì `print-manager` đã được
khai tường minh ở `0500-print.list.chroot`, lệnh `systemsettings` (binary
dùng làm **lớp dự phòng cuối** trong `open_kcm()` của script này) **chắc chắn
có mặt** trong ảnh NaMiOS, bất kể cấu hình `Recommends` của `lb build` — đây
là bằng chứng cụ thể hơn nhiều so với suy đoán "chắc là có" ở các module khác
trong repo.

`kcmshell6` (binary ưu tiên số 1 trong `open_kcm()`) đến từ gói
`libkf6kcmutils-bin` — gói này **CHỈ** được kéo qua `Recommends` của
`kinfocenter`/`plasma-disks` trong chuỗi đã dò, **KHÔNG** có trong chuỗi
`Depends` cứng nào đã xác nhận. Vì vậy script **không** coi `kcmshell6` là
chắc chắn có — nó LUÔN thử `kcmshell6` trước rồi tự rơi xuống `systemsettings
<module>` (chắc chắn có, xem trên) nếu `kcmshell6` vắng mặt. Không có nhánh
nào trong script có thể thành "nút chết" vì lý do này.

## 3. Bảng ánh xạ 8 mục → module/ứng dụng thật

Cột "Gói" = gói Debian cung cấp `.so` của KCM (xác nhận qua
`Contents-amd64.gz` thật). Cột "Bằng chứng" = `depends-chain` (chắc chắn có,
xem §2) hoặc `explicit-list` (đã khai trong `package-lists/*` hiện có) hoặc
`unconfirmed` (chưa xác nhận gói có mặt — ghi rõ TODO, KHÔNG dùng làm nhánh
duy nhất mà luôn có lớp dự phòng).

| Mục (Windows) | Mục con | Module/lệnh | Gói | Bằng chứng | verified_on_host |
| --- | --- | --- | --- | --- | --- |
| **Accounts** / Tài khoản | — | `kcm_users` | plasma-workspace | depends-chain | NO |
| **Display** / Màn hình & Hiển thị | — | `kcm_kscreen` | kscreen | explicit-list | NO |
| **Network** / Mạng | — | `kcm_networkmanagement` | plasma-nm | explicit-list | NO |
| **Devices** / Thiết bị | Thêm thiết bị mới | `namios-ket-noi-thiet-bi` (đã có sẵn, không viết lại) | — | explicit-list (0180/0500/0680) | NO (tool đã có, verified_on_host: NO sẵn ở file đó) |
| | Bluetooth | `kcm_bluetooth` | bluedevil | explicit-list | NO |
| | Máy in & máy quét | `kcm_printer_manager` | print-manager | explicit-list | NO |
| | Chuột | `kcm_mouse` | plasma-desktop | depends-chain | NO |
| | Touchpad | `kcm_touchpad` | plasma-desktop | depends-chain | NO |
| | Âm thanh | `kcm_pulseaudio` | plasma-pa | explicit-list | NO |
| **Personalization** / Cá nhân hoá | Giao diện tổng thể | `kcm_lookandfeel` | plasma-workspace | depends-chain | NO |
| | Hình nền | `kcm_wallpaper` | plasma-workspace | depends-chain | NO |
| | Màu sắc | `kcm_colors` | plasma-workspace | depends-chain | NO |
| | Phông chữ | `kcm_fonts` | plasma-workspace | depends-chain | NO |
| | Bộ biểu tượng | `kcm_icons` | plasma-workspace | depends-chain | NO |
| **Time & Language** / Ngôn ngữ & Thời gian | Ngày & Giờ | `kcm_clock` | plasma-desktop | depends-chain | NO |
| | Vùng & Ngôn ngữ | `kcm_regionandlang` | plasma-workspace | depends-chain | NO |
| | Bố cục bàn phím | `kcm_keyboard` | plasma-desktop | depends-chain | NO |
| **Apps** / Ứng dụng | Cài/Gỡ phần mềm | `plasma-discover` (binary, không phải KCM) | plasma-discover | explicit-list | NO |
| | Ứng dụng mặc định | `kcm_componentchooser` | plasma-desktop | depends-chain | NO |
| | Liên kết định dạng tệp | `kcm_filetypes` | kde-cli-tools (Depends cứng của plasma-desktop) | depends-chain | NO |
| | Khởi động cùng hệ thống | `kcm_autostart` | plasma-workspace | depends-chain | NO |
| **Update** / Cập nhật | — | `plasma-discover-update` (binary riêng, xác nhận qua Contents thật: `usr/bin/plasma-discover-update`, gói `plasma-discover`) | plasma-discover | explicit-list | NO |

### TODO rõ ràng — KHÔNG đoán, để nguyên dự phòng

- **`kcm_updates`** (gói `kde-config-updates`): dùng làm lớp dự phòng cuối
  cùng của `do_update()` nếu `plasma-discover`/`plasma-discover-update` vắng
  mặt (không nên xảy ra vì `plasma-discover` đã explicit-list, nhưng vẫn giữ
  lớp phòng hờ). **Gói này CHƯA được xác nhận có mặt trong ảnh NaMiOS** (không
  nằm trong bất kỳ `package-lists/*` nào, không nằm trong chuỗi Depends cứng
  đã dò) — nếu thiếu, `open_kcm` sẽ tự rơi xuống `systemsettings` trần (chắc
  chắn có, xem §2) rồi báo lỗi rõ nếu cả hai đều thất bại. KHÔNG phải nút
  chết, chỉ là lớp cuối ít chắc chắn hơn các lớp trước.
- **`kcm_kaccounts`** (Online Accounts — gói `kaccounts-integration`): KHÔNG
  đưa vào mục Accounts vì gói này không nằm trong bất kỳ `package-lists/*`
  nào và không có trong chuỗi Depends cứng đã dò — thêm vào sẽ là một nhánh
  không thể xác nhận. Nếu NaMiOS sau này cần "tài khoản trực tuyến" (Google/
  Nextcloud...), cần thêm `kaccounts-integration` vào package-lists trước
  (việc đó KHÔNG thuộc phạm vi sửa của việc này), rồi mới thêm nhánh menu.
- **Tên icon** của 8 file `namios-cpl-*.desktop` (`system-users`,
  `preferences-desktop-display`, `preferences-system-network`,
  `preferences-desktop-peripherals`, `preferences-desktop-theme`,
  `preferences-system-time`, `preferences-desktop-default-applications`,
  `system-software-update`) là tên chuẩn theo freedesktop Icon Naming
  Specification — `breeze-icon-theme` chắc chắn có mặt (depends-chain, xem
  §2) và theo đuổi chuẩn này, nhưng **CHƯA** đối chiếu từng tên với đúng file
  icon thật đã đóng gói trong `breeze-icon-theme` ở trixie. Đây là rủi ro MỸ
  THUẬT thuần tuý (icon trống hiện icon mặc định của theme, không làm nút
  chết — `Exec=` của mọi file này gọi thẳng `namios-control-panel`, không phụ
  thuộc Icon). Launcher hub + mọi script dùng `Icon=namios` (asset NaMiOS
  thật, đã xác nhận tồn tại tại `usr/share/icons/hicolor/*/apps/namios.png`).

## 4. Vì sao Accounts/Display/Network là 1 trang, còn Devices/Personalization/
   Time & Language/Apps là submenu

Trong Windows Settings thật, cả 8 mục đều là trang "hub" nhiều mục con. Ở
NaMiOS, 3 mục đầu (Accounts, Display, Network) ánh xạ khá trọn vẹn vào **một**
KCM KDE sẵn có (`kcm_users`, `kcm_kscreen`, `kcm_networkmanagement`) nên mở
thẳng, không cần đoán xem "trang con nào là đúng nhất". 5 mục còn lại không có
một KCM duy nhất phủ hết — script dùng submenu liệt kê từng KCM đã xác nhận
thay vì đoán một module "đại diện" rồi gắn nhầm, giữ đúng nguyên tắc "không
đoán mò" của CLAUDE.md.

## 5. An toàn & giới hạn đã biết

- Script không tự xin quyền quản trị — mọi hành động cần quyền (vd sửa tài
  khoản người dùng khác) do chính KCM/polkit hỏi, không phải
  `namios-control-panel`.
- Không có nhánh nào gọi `curl|bash`, `eval`, hay ghép chuỗi người dùng vào
  dòng lệnh thực thi — mọi lệnh là argv tĩnh, đã `bash -n` kiểm cú pháp.
- Script luôn `exit 0` — lỗi/thiếu gói chỉ hiện thông báo tiếng Việt, không
  làm sập phiên người dùng.
- Trùng việc với "NaMiOS Sao lưu" (Kup, hook `0620-backup-config.hook.chroot`)
  và "NaMiOS Chẩn đoán" mục 4 (Timeshift, `usr/local/bin/namios-chan-doan`):
  mục Update của Control Panel CHỈ trỏ sang hai công cụ đó bằng dòng ghi chú
  (`show_text`), KHÔNG viết lại logic sao lưu/khôi phục.

## 6. Checklist cần bấm thử trên máy thật (điền lại khi có desktop, không tự
   đánh dấu trước — giống mẫu đã dùng ở `UX-INTERACTION.md`/`UX-WINDOWS-FAMILIAR.md`)

- [ ] Menu hub 8 mục hiện đúng bằng `kdialog` (không rơi về TTY) trên phiên
      Plasma thật.
- [ ] Accounts → `kcm_users` mở đúng trang Người dùng, polkit hỏi mật khẩu khi
      thêm user mới.
- [ ] Display → `kcm_kscreen` mở đúng trang Hiển thị.
- [ ] Network → `kcm_networkmanagement` mở đúng trang Mạng (không trùng/ xung
      đột với applet `plasma-nm` ở khay hệ thống).
- [ ] Devices → cả 6 nhánh con mở đúng (đặc biệt "Thêm thiết bị mới" gọi đúng
      `namios-ket-noi-thiet-bi`).
- [ ] Personalization → cả 5 nhánh con mở đúng, không trùng cửa sổ.
- [ ] Time & Language → cả 3 nhánh con mở đúng; xác nhận `kcm_regionandlang`
      không xung đột với cấu hình Fcitx5 (hook `0200-fcitx5-default-im.hook.chroot`).
- [ ] Apps → Discover mở đúng (không phải cửa sổ trống do thiếu backend
      PackageKit); `kcm_filetypes`/`kcm_componentchooser`/`kcm_autostart` mở
      đúng.
- [ ] Update → `plasma-discover-update` mở thẳng trang Cập nhật của Discover
      (không phải trang chủ Discover).
- [ ] 8 launcher `namios-cpl-*.desktop` xuất hiện và tìm được qua Kickoff
      bằng tiếng Việt không dấu (ADR 0011 §6 "tìm kiếm không dấu") — vd gõ
      "mang" ra kết quả "Mạng".
- [ ] Không launcher nào hiện 2 lần trong menu ứng dụng (trùng với category
      gốc của `systemsettings`).
