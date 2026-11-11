# NaMiOS — Windows Feature Parity (phân tích + backlog dev-ready)

> **Loại tài liệu:** phân tích nghiệp vụ/sản phẩm (grounded trên repo) → backlog có ưu
> tiên cho các đội khác nhận việc. CHỈ phân tích + đề xuất. KHÔNG sửa code/gói khác,
> KHÔNG build, KHÔNG commit.
> **Ngày:** 2026-11-11 · **Người soạn:** phân tích nghiệp vụ/sản phẩm (Team 7).
> **Đối tượng:** người Việt phổ thông chuyển từ Windows (văn phòng/kế toán/ít rành
> công nghệ) — "quen tay kiểu Windows 11 + ít-thao-tác kiểu macOS".

## Quy ước trung thực (bắt buộc đọc)

- Mọi khẳng định "CURRENT STATE" lấy từ **bằng chứng repo** (file/gói), KHÔNG phải
  bằng chứng boot/pilot thật. **`verified_on_host: NO` cho toàn bộ tài liệu này** —
  đã vào được desktop KDE trong QEMU nhưng chưa có pilot máy thật (xem `docs/STATUS.md`,
  ADR 0011 "Bối cảnh môi trường hiện tại"). "File không lỗi khi build" KHÔNG suy ra
  "đã giống Windows trên máy thật". Chỗ suy đoán ghi rõ **[GIẢ ĐỊNH]**.
- **Ranh giới IP (ADR 0011 §3, LIC-004 — ràng buộc cứng):** NaMiOS **được** bắt chước
  **bố cục + luồng thao tác** (taskbar dưới, nút mở app góc trái, khay/đồng hồ góc phải,
  Alt+Tab, Win+E/D/L, click-phải, kéo-thả). NaMiOS **TUYỆT ĐỐI KHÔNG**: chép icon/font/
  âm thanh/hoạt ảnh độc quyền Microsoft; gọi menu là "Start Menu"; đặt nhãn ổ Linux là
  `C:` (ngoài phạm vi prefix Wine); tuyên bố "giống Windows 100%". **Parity = hành vi
  quen thuộc, KHÔNG phải pixel-clone.** Mọi đề xuất dưới đây tuân thủ giới hạn này; chỗ
  nào chạm ranh giới có ghi **[IP]**.
- **Mức ưu tiên:** **P0** chặn khả dụng/niềm tin (làm trước pilot) · **P1** cần cho pilot
  nghiệp vụ / trải nghiệm chuyên nghiệp · **P2** đánh bóng sau pilot.
- **Công sức:** **S** vài ngày/1 wave · **M** 1–2 tuần · **L** nhiều tuần + **cần phần
  cứng/build host thật** · **XL** cần đối tác/pháp lý/pilot thật (ngoài lập trình thuần).
- **Đội sở hữu:** **1** = thiết kế · **3** = dev nền tảng/desktop · **5** = Wine/tương
  thích · **6** = SmartAI.

## 0. CHẶN GỐC (master gate) — đọc trước

Mọi dòng "verified_on_host: NO" dưới đây chỉ mở khoá được khi có **build host Linux
amd64 có nested-virt** để `lb build` → boot QEMU/KVM → **cài Calamares lên đĩa thật** →
bấm thử từng hành vi (xem checklist trong `docs/specs/UX-WINDOWS-FAMILIAR.md` §8,
`.../WINDOWS-HABITS.md` §6, `.../UX-INTERACTION.md` §8). Đây là **đòn bẩy lớn nhất** —
đã là #1 trong `NANG-CAP-NHU-CAU-NGUOI-DUNG.md` §0/Top-10. Tài liệu này KHÔNG lặp lại
nó như một dòng parity riêng, nhưng **mọi mục "verify on boot" bên dưới đều khoá sau
cổng này**.

---

## A. Phân tích theo tính năng Windows

Mỗi mục: **WINDOWS FEATURE → vì sao người dùng dựa vào → CURRENT STATE (bằng chứng
repo) → GAP → ĐỀ XUẤT CỤ THỂ → PRIORITY · EFFORT · ĐỘI.**

### A1. Nút Bắt đầu + Tìm kiếm (Start menu + Search)

- **Vì sao dựa vào:** điểm vào duy nhất để mở app/tìm file/tắt máy; người Windows bấm
  phím Win theo phản xạ.
- **CURRENT STATE:** Kickoff ghim trong panel dưới (`plasma-org.kde.plasma.desktop-appletsrc`
  `[Containments][1][Applets][2] plugin=org.kde.plasma.kickoff`); phím **Meta mở Kickoff**
  qua `kwinrc [ModifierOnlyShortcuts] Meta=org.kde.plasmashell,…,activateLauncherMenu`;
  lưới "Ưa thích" đã ghim sẵn Office/trình duyệt (`favorites=…writer/calc/impress/firefox…`).
  **Tìm kiếm toàn cục kiểu Spotlight:** KRunner gán **Meta+Space** (+ giữ Alt+Space/Alt+F2)
  trong `kglobalshortcutsrc [org.kde.krunner.desktop]`.
- **GAP:** (1) icon nút Bắt đầu là **placeholder** `start-here-namios` (chưa có asset thật —
  `usr/share/namios-branding/README-PLACEHOLDER.md`). (2) Menu chưa có **"nhóm việc"** (Văn
  phòng/Thuế/Kế toán/Bảo hiểm/Giáo dục/Hành chính) mà `DESIGN-SYSTEM.md` §7 mô tả — hiện là
  Kickoff trần theo category Freedesktop. (3) Tên group KRunner (`org.kde.krunner.desktop` vs
  `krunner.desktop`) chưa chắc trên trixie thật (ghi rõ trong `UX-INTERACTION.md` §3). Tất cả
  `verified_on_host: NO`.
- **ĐỀ XUẤT:** vẽ **[IP]** icon Bắt đầu riêng NaMiOS (không chép logo Start); bổ sung lớp
  "nhóm việc" (có thể là Kickoff categories tùy biến hoặc widget `org.namios.workgroups` đã
  dự kiến ở `namios-add-widgets.sh`); boot-test Meta + Meta+Space, nếu KRunner không mở thì
  `kreadconfig6` để dò group đúng.
- **PRIORITY: P1 · EFFORT: S–M · ĐỘI: 1 (icon + nhóm việc) + 3 (verify + widget).**

### A2. Thanh tác vụ + Khay hệ thống (Taskbar + System tray)

- **Vì sao dựa vào:** trực quan "app nào đang mở", ghim app hay dùng, trạng thái mạng/âm
  lượng/pin/đồng hồ luôn ở góc phải.
- **CURRENT STATE:** 1 panel dưới (`location=4` BottomEdge, `formfactor=2`) chứa Kickoff +
  **Icon-Only Task Manager** (`org.kde.plasma.icontasks`, `launchers=…dolphin/firefox/office…`)
  + **System Tray** (`org.kde.plasma.systemtray`) + **Digital Clock** (24h, ngày). Panel kiểu
  dock nổi (`floating=1`).
- **GAP:** cấu trúc applet có thể bị Plasma **tự renumber lần đăng nhập đầu** (hành vi bình
  thường, không phải lỗi — ghi rõ trong file); tập applet mặc định trong systray (VN·Telex/
  Wi‑Fi/loa/pin) chưa xác nhận bày đủ; blur dock chỉ hiện khi compositing BẬT (máy có GPU) —
  dưới QEMU/TCG panel đặc. `verified_on_host: NO`.
- **ĐỀ XUẤT:** boot-test panel hiện đủ 4 cụm; xác nhận systray mặc định có Fcitx5 + plasma-nm
  + plasma-pa; chụp ảnh thật đối chiếu mockup `DESIGN-SYSTEM.md` §6.
- **PRIORITY: P1 (verify) · EFFORT: S · ĐỘI: 3.**

### A3. File Explorer — "This PC" / ổ đĩa / Quick access

- **Vì sao dựa vào:** "Máy này" gom ổ đĩa + thư mục nhanh (Documents/Downloads/Desktop) là
  mô hình tư duy lõi của người Windows để tìm file.
- **CURRENT STATE:** Dolphin (NaMiFiles) ship (`0100-desktop-kde.list.chroot`). Thanh địa chỉ
  text sửa được bật (`dolphinrc [General] EditableUrl=true`). Places panel **mặc định của
  Dolphin** tự tính Home/Desktop/Documents/Downloads/Trash theo `$HOME` (đạt phần "thư mục
  nhanh" ngay cả khi không có `user-places.xbel`). Desktop ở chế độ Folder View hiện icon file
  (`[Containments][2][General] url=desktop:/`). Nhãn dung lượng/filesystem = default Dolphin
  Places khi mount; SMB qua `kio-extras`; NTFS/exFAT qua `ntfs-3g`/`exfatprogs` (`0190`).
- **GAP:** (1) **KHÔNG có nhóm "Máy này" gom ổ** kiểu This-PC + không có thứ tự Quick-access
  tùy biến — `user-places.xbel` bị **hoãn có chủ đích** vì `/etc/skel` copy nguyên văn, ghi
  cứng path sẽ sai cho mọi user (`UX-WINDOWS-FAMILIAR.md` §6). (2) Không có icon "Máy này"/
  "Thùng rác" trên desktop (hoãn — `WINDOWS-HABITS.md` §4). (3) Toàn bộ chưa boot-verify.
- **ĐỀ XUẤT:** cho **`namios-welcome` (first-run)** sinh `user-places.xbel` **lúc đăng nhập
  đầu** (biết `$HOME` thật) với nhóm **"Máy này"** gom ổ gắn + Quick-access sắp xếp kiểu
  Windows — đây là đường kỹ thuật đúng, không vi phạm "path tĩnh sai". **[IP]** giữ nhãn
  "Máy này", KHÔNG gọi ổ Linux là `C:`.
- **PRIORITY: P1 · EFFORT: M · ĐỘI: 3 (gắn vào namios-welcome apply()).**

### A4. Mô hình "ổ C:/D:" (drive letters)

- **Vì sao dựa vào:** người Windows nghĩ theo "ổ C, ổ D, ổ USB" chứ không theo mount point
  Linux (`/`, `/media/...`).
- **CURRENT STATE:** Dolphin Places hiển thị ổ gắn bằng nhãn thiết bị + dung lượng (default
  KIO/udisks2). Repo **tuân thủ**: không file nào đặt nhãn `C:` cho ổ Linux (`UX-WINDOWS-FAMILIAR.md`
  §3); `C:` chỉ trong phạm vi prefix Wine.
- **GAP:** không có lớp "dịch" giúp người dùng nối "ổ D nhà tôi" ↔ phân vùng/USB cụ thể; nhãn
  mặc định udisks đôi khi là UUID/khó đọc.
- **ĐỀ XUẤT:** **[IP]** KHÔNG giả lập drive-letter; thay vào đó hiển thị nhãn dễ hiểu ("Ổ dữ
  liệu", "USB của bạn") + dung lượng trong "Máy này" (gắn với A3). Giải thích 1 dòng trong
  NaMiHelp: "Windows gọi ổ C/D; ở đây là Máy này + tên ổ".
- **PRIORITY: P2 · EFFORT: S · ĐỘI: 1 (nhãn + help) + 3 (Places).**

### A5. Control Panel / Settings

- **Vì sao dựa vào:** một nơi chỉnh mọi thứ (màn hình, mạng, máy in, tài khoản, cập nhật);
  người ít rành cần **nhóm theo việc + tìm kiếm**.
- **CURRENT STATE:** KDE **System Settings** là Control Panel thật của Plasma (kéo theo
  `task-kde-desktop`, `0100`). `namios-welcome` làm onboarding chọn vài mặc định. ADR 0011 §6
  yêu cầu nhóm Công việc/Thiết bị/Mạng/Cá-nhân-hóa/Tài-khoản/Riêng-tư/Cập-nhật/Khôi-phục +
  **tìm kiếm không dấu**.
- **GAP:** (1) **System Settings KHÔNG được khai báo tường minh** trong `package-lists/` —
  **[GIẢ ĐỊNH]** đi kèm transitive qua `task-kde-desktop`; rủi ro thiếu/đổi tên. (2) Hiện là
  System Settings **trần** (nhóm KDE mặc định tiếng Anh/phần dịch), **chưa có** mặt tiền "Cài
  đặt" nhóm theo việc + tìm-không-dấu như ADR yêu cầu.
- **ĐỀ XUẤT:** khai báo rõ `systemsettings` trong package-list; dựng **landing "Cài đặt" của
  NaMiOS** nhóm các KCM theo việc + ô tìm không dấu (có thể là trang khởi đầu trỏ sang KCM
  thật, không viết lại từng KCM). **[IP]** nhãn tiếng Việt riêng, không chép bố cục pixel
  Windows Settings.
- **PRIORITY: P1 · EFFORT: M · ĐỘI: 1 (nhóm + nhãn) + 3 (landing + khai gói).**

### A6. Click-phải context menu + F5/Refresh

- **Vì sao dựa vào:** chuột-phải để sao chép/đổi tên/thuộc tính; F5 là phản xạ "làm mới".
- **CURRENT STATE:** menu ngữ cảnh Dolphin/Plasma = default (không cần file riêng). **F5 đã
  hoạt động kiểu Windows mà KHÔNG cần cấu hình thêm:** Dolphin F5=Reload (KStandardShortcut::Reload,
  tầng app), Desktop có action "Refresh Desktop" F5 sẵn (Folder View) — đã đối chiếu mã nguồn
  KDE thật và giải thích đầy đủ trong `usr/share/namios/docs/WINDOWS-HABITS.md` §2.
- **GAP:** chỉ còn **verify on boot** (F5 Dolphin/Desktop; không xung đột F5 Firefox/Impress).
  KHÔNG nên thêm F5 toàn cục (KGlobalAccel) — rủi ro cướp phím của mọi app (lý do trong §2.3).
- **ĐỀ XUẤT:** chạy checklist `WINDOWS-HABITS.md` §6; không thêm khoá nào.
- **PRIORITY: P2 (verify) · EFFORT: S · ĐỘI: 3.**

### A7. Chia/dán cửa sổ (Aero Snap) + Overview

- **Vì sao dựa vào:** kéo cửa sổ ra biên để chia đôi màn hình (đa nhiệm); xem tổng quan mọi
  cửa sổ.
- **CURRENT STATE:** `kwinrc [Windows] ElectricBorderMaximize=true, ElectricBorderTiling=true,
  BorderSnapZone=10, WindowSnapZone=10` (Aero-snap/tiling); Alt+Tab lưới thumbnail
  (`[TabBox] LayoutName=thumbnail_grid`); **Overview kiểu Mission Control** bật +
  hot-corner trên-trái (`[Effect-overview] BorderActivate=7`, `[Plugins] overviewEnabled=true`).
  Phần lớn đã là mặc định KWin 6, repo chỉ **chốt tường minh**.
- **GAP:** hiệu ứng kính mờ/animation chỉ hiện khi **compositing BẬT** (máy có GPU);
  `kwinrc [Compositing] Enabled=false` để chạy máy không GPU (QEMU) → snap/tile vẫn chạy nhưng
  không mượt; cử chỉ 4-ngón touchpad + hot-corner cần **Wayland thật** để xác nhận. Custom
  Tiling (Meta+T) không soạn tĩnh được (`UX-INTERACTION.md` §4). `verified_on_host: NO`.
- **ĐỀ XUẤT:** verify snap/Overview trên cả Wayland + X11; để `namios-auto-compositing` bật
  compositing khi máy thật có GPU (đã có autostart).
- **PRIORITY: P2 (verify) · EFFORT: S · ĐỘI: 3.**

### A8. Thông báo + Action Center / Quick Settings

- **Vì sao dựa vào:** thông báo gom một chỗ; Win11 có "Quick Settings" (Wi‑Fi/âm lượng/độ
  sáng 1 chạm).
- **CURRENT STATE:** Plasma có hệ **Notifications + Do-Not-Disturb** mặc định qua System Tray
  (đi kèm `task-kde-desktop`). Không có `plasmanotifyrc`/cấu hình thông báo riêng trong repo
  (grep chỉ thấy tham chiếu trong docs, không có file config).
- **GAP:** (1) chưa cấu hình mặc định thông báo (lịch sử, không-làm-phiền khi trình chiếu).
  (2) **Chưa có "Quick Settings" 1-chạm kiểu Win11** được ghim rõ — KDE có applet gần tương
  đương (brightness/audio/network trong systray) nhưng chưa chốt cụm.
- **ĐỀ XUẤT:** thêm `plasmanotifyrc` mặc định hợp lý; **[IP]** cân nhắc gom nhóm systray
  (mạng/âm/độ sáng) làm cụm "Cài đặt nhanh" tiếng Việt — không chép pixel panel Win11.
- **PRIORITY: P2 · EFFORT: S · ĐỘI: 1 (gom cụm + nhãn) + 3 (config).**

### A9. Thùng rác (Recycle Bin)

- **Vì sao dựa vào:** xoá nhầm → khôi phục; icon Thùng rác trên desktop là phản xạ.
- **CURRENT STATE:** **Trash hoạt động** qua KIO (có sẵn khi cài `dolphin`+`kio-extras`);
  xoá-vào-thùng-rác + khôi phục là default, không cần override (`dolphinrc` ghi rõ).
- **GAP:** **KHÔNG có icon Thùng rác trên desktop** — hoãn có chủ đích vì applet pre-seed tĩnh
  bị Plasma bỏ qua trong containment Desktop (activityId sinh lúc chạy); đường đúng là
  `usr/local/bin/namios-add-widgets.sh` (evaluateScript lúc đăng nhập đầu) — ngoài phạm vi wave
  trước (`WINDOWS-HABITS.md` §4).
- **ĐỀ XUẤT:** thêm applet `org.kde.plasma.trash` vào `namios-add-widgets.sh` (tái dùng đúng
  cơ chế đã chạy cho SmartAI/nhóm việc). Giao rõ quyền sửa file đó.
- **PRIORITY: P2 · EFFORT: S · ĐỘI: 3.**

### A10. Lịch sử clipboard (Clipboard history)

- **Vì sao dựa vào:** Win+V (Win10/11) dán lại nội dung đã copy trước đó — dân văn phòng dùng
  nhiều.
- **CURRENT STATE:** **Klipper** (quản lý clipboard của Plasma, phím mặc định **Meta+V**) đi
  kèm `plasma-workspace`/`task-kde-desktop` theo mặc định — **nhưng repo KHÔNG cấu hình/ghim/
  tài liệu hoá** nó (grep `klipper` chỉ ra trong docs/manifest, không có `klipperrc` trong
  `/etc/skel`).
- **GAP:** tính năng có sẵn nhưng **người dùng không biết** (không pin trong systray, không
  nêu trong help, kích thước lịch sử default). Đây là **win dễ** cho cảm giác "ngang Windows".
- **ĐỀ XUẤT:** thêm `klipperrc` mặc định (bật history, size hợp lý, bỏ qua mật khẩu) + đảm bảo
  Klipper trong systray + 1 dòng NaMiHelp "Meta+V = dán lại thứ đã copy".
- **PRIORITY: P2 · EFFORT: S · ĐỘI: 3.**

### A11. Windows Update (cập nhật hệ thống)

- **Vì sao dựa vào:** máy tự vá bảo mật, cập nhật an toàn, quay lui được khi hỏng.
- **CURRENT STATE:** APT + `unattended-upgrades` (vá bảo mật tự động) + `needrestart` (báo
  dịch vụ cần restart) + `timeshift` snapshot trước update (`0640`); app/metadata qua
  `plasma-discover`+`packagekit`+`appstream` (`0100`). ADR-0014.
- **GAP:** Timeshift chạy **rsync (ext4), KHÔNG A/B nguyên tử**; apt không nguyên tử → mất
  điện giữa update vẫn rủi ro (ghi rõ `0640`). Chu kỳ update→reboot→rollback **chưa diễn tập
  thật**. Lớp "Update Center" điều phối (SmartAI, ADR-0017) **đang làm, chưa nối**.
- **ĐỀ XUẤT:** diễn tập `apt upgrade`→`needrestart`→snapshot→rollback trên VM (cần build host);
  viết help tiếng Việt "cập nhật an toàn + cách quay lui"; nối Update Center của SmartAI khi
  sẵn sàng. Giữ `unattended-upgrades` chỉ security-pocket.
- **PRIORITY: P1 · EFFORT: M · ĐỘI: 6 (Update Center) + 3 (diễn tập + help).**

### A12. Kỳ vọng "Defender / diệt virus"

- **Vì sao dựa vào:** người Windows tin phải có "phần mềm diệt virus bảo vệ realtime".
- **CURRENT STATE:** `clamav` + `clamav-freshclam` **chỉ on-demand** (KHÔNG cài `clamav-daemon`/
  on-access — quyết định VN09-029, `0635` giải thích đầy đủ rủi ro treo/ngốn CPU); `ufw`
  deny-incoming; `apparmor(+profiles/utils)` (`0630`).
- **GAP:** không có bảo vệ realtime → **lệch kỳ vọng**; nhưng bật on-access ClamAV có rủi ro
  thật (treo/CPU) chưa benchmark trên phần cứng pilot.
- **ĐỀ XUẤT:** **giáo dục kỳ vọng, không overclaim** — Security Center tiếng Việt giải thích
  mô hình bảo vệ Linux (quyền user + AppArmor + firewall + cập nhật) + nút **"Quét thư mục
  này"** bằng ClamAV. **TUYỆT ĐỐI không hứa "chặn 100% mã độc"** (VN09-030). Benchmark
  on-access tách riêng khi có phần cứng.
- **PRIORITY: P1 · EFFORT: S (UI/giáo dục) / M (benchmark) · ĐỘI: 1 (nội dung) + 3 (nút quét).**

### A13. Driver / Plug-and-Play (nhận thiết bị "như Windows")

- **Vì sao dựa vào:** cắm chuột/USB/máy in/Wi‑Fi là chạy ngay, không cài driver thủ công.
- **CURRENT STATE:** firmware rộng (`0150` iwlwifi/realtek/atheros/brcm/mediatek + `0720`
  libertas/ti); `udisks2` tự mount USB (`0190`); NetworkManager + plasma-nm + Bluetooth
  bluez/bluedevil/blueman; `usbutils`/`mtp-tools`/`rfkill` + script `namios-ket-noi-thiet-bi`/
  `namios-chan-doan` (`0650/0680/0720`); `non-free`+`non-free-firmware` bật (`auto/config`).
- **GAP:** **toàn bộ phần cứng chưa test máy thật** (DAC_TA §27); "nhận USB ID" ≠ "chạy đúng
  nghiệp vụ"; NVIDIA rời/Wi‑Fi hiếm/scanner ADF chưa có profile; script chỉ trả lời "bus có
  thấy không", chưa có **DB thiết bị theo model** (DEV-001/008).
- **ĐỀ XUẤT:** HW pilot (HW-001: ≥5 máy + ≥2 máy in) chạy ma trận DEV-002..008; dựng **DB
  thiết bị theo model** hiển thị "đầy đủ/một phần/chưa kiểm/không hỗ trợ" (đúng từ vựng trung
  thực). Ưu tiên Canon/HP/Epson/Brother phổ biến VN.
- **PRIORITY: P1 · EFFORT: L (cần phần cứng) · ĐỘI: 3.**

### A14. In ấn (Printing)

- **Vì sao dựa vào:** văn phòng/kế toán in hợp đồng/báo cáo/hoá đơn hằng ngày + xuất PDF.
- **CURRENT STATE:** CUPS đầy đủ (`cups`/`cups-filters`/`cups-client`/`cups-browsed`) +
  driverless (IPP/eSCL/Avahi/`ipp-usb`) + driver theo hãng (gutenprint/escpr/brlaser/foo2zjs/
  postscript-hp/hplip) + **"In ra PDF"** (`printer-driver-cups-pdf`) (`0500/0700-printing/0680`).
  Mạnh nhất trong các mục. PDF: Okular + poppler/qpdf/ocrmypdf/tesseract-vie (`0420`).
- **GAP:** (1) **Ký số PDF chưa có đường tích hợp** (Okular xem/điền form, nhưng ký bằng chứng
  thư/USB token chưa có — nhu cầu kế toán thật). (2) In từ app Wine, A4/A5, 2 mặt, font Việt có
  dấu, mã vạch/QR **chưa test** (thiếu phần cứng, DEV-002). (3) `verified_on_host: NO`.
- **ĐỀ XUẤT:** bật **ký PDF bằng chứng thư mềm (.p12/PKCS#12)** sẵn trong Okular/LibreOffice +
  help tiếng Việt; bộ kiểm in trên máy thật (A4/A5/2-mặt/dấu/PDF/Wine); giữ `cups-pdf` làm
  đường "In → PDF" mặc định. Token USB/eID = nhánh PKCS#11 riêng.
- **PRIORITY: P1 · EFFORT: M (ký mềm + docs) / L (kiểm in HW) · ĐỘI: 3 (+ 5 cho in từ Wine).**

### A15. Fonts

- **Vì sao dựa vào:** tài liệu Office từ đối tác (Calibri/Cambria) phải mở không lệch dòng/
  ngắt trang; chữ Việt đủ dấu.
- **CURRENT STATE:** Noto core/ui/mono + Liberation2 + DejaVu + **Inter** (UI, OFL) +
  **Carlito/Caladea** (metric-compat Calibri/Cambria — `fonts-crosextra-*`) (`0300-fonts.list.chroot`).
  **KHÔNG chép font Microsoft** (VN-005). Cascade sans-serif Inter→Noto; UI font = Inter
  (`kdeglobals [General] font=Inter`).
- **GAP:** glyph tiếng Việt của **Inter** (dấu kết hợp/ư/ơ/đ) + ánh xạ metric Carlito↔Calibri,
  Caladea↔Cambria **chưa xác nhận trên LibreOffice thật** (`verified_on_host: NO`). PL12.1 còn
  cân nhắc Be Vietnam Pro (chưa vendor).
- **ĐỀ XUẤT:** verify trên pilot: mở .docx/.xlsx đối tác, so layout; nếu Inter thiếu dấu, giữ
  Noto làm UI (lưới an toàn đã có). Không thêm font MS.
- **PRIORITY: P2 (verify) · EFFORT: S · ĐỘI: 1 (duyệt glyph) + 3 (gói).**

### A16. Task Manager

- **Vì sao dựa vào:** Ctrl+Shift+Esc / Ctrl+Alt+Del để kết thúc app treo, xem CPU/RAM.
- **CURRENT STATE:** **Plasma System Monitor** (`org.kde.plasma-systemmonitor`, đã rebrand
  nhãn "Theo dõi hệ thống" ở hook `0130`) là Task-Manager tương đương. **CẢNH BÁO:** gói
  `plasma-systemmonitor` **KHÔNG được khai báo tường minh** trong `package-lists/` — **[GIẢ
  ĐỊNH]** đi kèm transitive qua `task-kde-desktop`.
- **GAP:** (1) gói không khai rõ → rủi ro không có mặt. (2) **Chưa gán phím tắt kiểu Windows**
  (Ctrl+Shift+Esc) để mở nhanh — `kglobalshortcutsrc` không có entry này. (Ctrl+Alt+Del mở Task
  Manager được ghi "NOT required" trong `WINDOWS-HABITS.md` §3.)
- **ĐỀ XUẤT:** khai `plasma-systemmonitor` tường minh trong package-list; thêm entry
  `kglobalshortcutsrc` gán **Ctrl+Shift+Esc → launch plasma-systemmonitor** (verify tên
  desktop-file-id trên trixie thật trước khi tin).
- **PRIORITY: P2 · EFFORT: S · ĐỘI: 3.**

### A17. Hộp thoại Run (Win+R)

- **Vì sao dựa vào:** gõ lệnh/tên app nhanh (`notepad`, đường dẫn, URL).
- **CURRENT STATE:** **KRunner** phủ vai trò này — `kglobalshortcutsrc [org.kde.krunner.desktop]
  _launch=Meta+Space␉Alt+Space␉Alt+F2` (chạy app, mở file, tính toán, tìm). Mạnh hơn Run của
  Windows.
- **GAP:** chỉ còn rủi ro **tên group** (`org.kde.krunner.desktop` vs `krunner.desktop`) chưa
  chắc trên trixie (`UX-INTERACTION.md` §3); fail-safe = không crash nếu sai. `verified_on_host: NO`.
- **ĐỀ XUẤT:** boot-test Meta+Space; nếu không mở, `kreadconfig6` dò group đúng rồi sửa. (Không
  cần giả lập "Win+R" riêng — KRunner đã vượt.)
- **PRIORITY: P2 (verify) · EFFORT: S · ĐỘI: 3.**

### A18. Thanh địa chỉ Explorer (address bar)

- **Vì sao dựa vào:** gõ/dán đường dẫn trực tiếp để nhảy thư mục; thấy path đầy đủ.
- **CURRENT STATE:** `dolphinrc [General] EditableUrl=true` (thanh địa chỉ text sửa được kiểu
  Explorer) + `BrowseThroughArchives=true` + `ShowSpaceInfo=true`.
- **GAP:** tên khoá `EditableUrl` soạn theo cấu trúc dolphinrc đã biết, **phải đối chiếu đúng
  phiên bản Dolphin trixie** (`dolphinrc` ghi rõ `verified_on_host: NO`).
- **ĐỀ XUẤT:** verify thanh địa chỉ sửa được + Ctrl+L focus vào ô địa chỉ (default Dolphin).
- **PRIORITY: P2 (verify) · EFFORT: S · ĐỘI: 3.**

### A19. Parity phím tắt (keyboard shortcuts)

- **Vì sao dựa vào:** phản xạ Win+E/D/L, PrtSc, Alt+Tab, Ctrl+C/V — sai 1 phím là "khó dùng".
- **CURRENT STATE:** `kglobalshortcutsrc` công bố Meta+E→Dolphin, Meta+D→Show Desktop,
  Meta+L→Lock, Print→Spectacle, Alt+Tab→Walk Through Windows, Meta+Space→KRunner; Ctrl+C/V giữ
  mặc định toolkit (không override — đúng, vì là shortcut tầng app). Registry đầy đủ 27 action ở
  `design/keyboard-shortcuts.json` (9 hệ thống + 4 cửa sổ + 14 app) với `p_level`/`overridable`.
- **GAP:** (1) **bộ phát hiện xung đột chạy CI chưa được dựng** (UX12-019) — "không trùng" hiện
  là đối chiếu **thủ công một lần**, không phải bằng chứng CI (`DESIGN-SYSTEM.md` PL12.4). (2) 3
  xung đột tiềm ẩn đã biết (Ctrl+Space IME vs IDE, Super+Space, Shift+F10). (3) chưa boot-test
  khi **Fcitx5 + Wine** cùng chạy (ADR 0011 test UI-04). `verified_on_host: NO`.
- **ĐỀ XUẤT:** dựng CI conflict-detector trên `design/keyboard-shortcuts.json` (UX12-019);
  boot-test toàn bộ map khi IME bật (checklist `UX-WINDOWS-FAMILIAR.md` §8). **[IP]** chỉ ánh xạ
  hành vi, không chép tài sản.
- **PRIORITY: P1 · EFFORT: S–M · ĐỘI: 1 (registry + CI) + 3 (boot-test).**

### A20. OOBE / First-run (thiết lập lần đầu)

- **Vì sao dựa vào:** lần đầu bật máy quyết định ấn tượng "chuyên nghiệp"; chọn ngôn ngữ/bộ gõ/
  app mặc định/máy in trong vài phút.
- **CURRENT STATE:** **Calamares** (`calamares`+`calamares-settings-debian`) cài lên đĩa, có
  branding NaMiOS (`etc/calamares/branding/namios/`); **`namios-welcome`** (PySide6) wizard
  first-run chọn Telex/VNI, cỡ chữ 100/125/150%, app docx/xlsx/pdf, máy in + `migrate.py` nhập
  dữ liệu từ Windows (`src/namios_welcome/`, hook `0300`, autostart).
- **GAP (P0 từ `NANG-CAP` §3.2):** wizard **mới ghi `welcome.json`, CHƯA áp hiệu lực thật** —
  chọn Telex nhưng chưa chắc Fcitx5 đổi; chọn app mặc định chưa chắc ghi `mimeapps.list`; chọn
  scale chưa chắc áp KDE. "Có UI, chưa có tác dụng". Chưa có tour 60 giây cho người ít rành.
- **ĐỀ XUẤT:** **nối `apply()` → hiệu lực thật** (ghi Fcitx5 Telex/VNI, KDE scale, `mimeapps.list`,
  máy in mặc định) — đây là mục làm "ít-thao-tác" thành thật. Thêm tour 3–5 "việc đầu tiên"
  (mở Word, gõ Việt, lưu, in PDF, nối Wi‑Fi).
- **PRIORITY: P0 (nối hiệu lực) / P1 (tour) · EFFORT: M · ĐỘI: 3.**

### A21. Khả năng tiếp cận (Accessibility) + ngôn ngữ mặc định

- **Vì sao dựa vào:** người ít rành/thị lực kém cần chữ to, đọc màn hình, giao diện **tiếng
  Việt**.
- **CURRENT STATE:** Design system đặt mục tiêu **WCAG 2.2 AA**, đã đo/chỉnh 3 token tương phản
  (`DESIGN-SYSTEM.md` PL12.2/12.6), phóng chữ 100–200%, glossary 55 thuật ngữ. Hạ tầng lớp phủ
  dịch **vi_NM** đã có (memory). **NHƯNG ngôn ngữ hiển thị mặc định đã đổi sang tiếng Anh**
  (10/11, `0200-locale-vi`/`0210`) vì bản dịch KDE tiếng Việt chỉ phủ một phần.
- **GAP:** **[CĂNG THẲNG MỤC TIÊU]** đối tượng là người Việt ít rành nhưng **mặc định tiếng
  Anh** — ngược nhu cầu; với kế toán/văn phòng, tiếng Anh là rào cản lớn hơn việc trộn ngôn
  ngữ. Accessibility (screen reader, 200% text) **chưa test** (`blocked-infra`).
- **ĐỀ XUẤT:** **[cần chủ dự án quyết]** mặc định **tiếng Việt** + đầu tư lớp phủ **vi_NM** phủ
  các chuỗi KDE phổ biến nhất (giảm trộn ngôn ngữ); hoặc màn chào cho chọn ngôn ngữ 1-chạm (mở
  sẵn tiếng Việt). Test screen reader + 200% text khi có desktop thật.
- **PRIORITY: P0 (ngôn ngữ — cần chốt) / P1 (a11y test) · EFFORT: S (quyết định) / M (overlay) ·
  ĐỘI: 1 (+ 3 cho overlay/gói).**

---

## B. Chỗ KDE ĐÃ LÀM TỐT — KHÔNG phát sinh việc (giữ trung thực, không bịa gap)

- **F5/Refresh** (Dolphin + Desktop) đã đúng kiểu Windows ở tầng app — chỉ verify (A6).
- **Aero Snap / tiling** biên màn hình đã là mặc định KWin — chỉ chốt + verify (A7).
- **Alt+Tab** lưới thumbnail — mặc định, chỉ pin (A2/A19).
- **Trash/restore** qua KIO — mặc định đầy đủ (A9).
- **Thanh địa chỉ sửa được** — bật 1 khoá, hơn Explorer ở nhiều mặt (A18).
- **Run dialog** — KRunner vượt Win+R (A17).
- **Clipboard history** — Klipper có sẵn, chỉ cần ghim/tài liệu hoá (A10).
- **In ấn** — CUPS + driverless + nhiều driver hãng + In-ra-PDF: **mạnh hơn** mặc định Windows
  ở khoản PDF (A14).
- **Font metric-compat** Carlito/Caladea đã có — tránh trôi layout mà không chép font MS (A15).

**Ranh giới IP đã tuân thủ tốt (giữ nguyên):** không `C:` cho ổ Linux; không chép icon/font/âm
thanh MS; icon Bắt đầu/launcher để placeholder chờ asset riêng; LibreOffice không đặt tên hiển
thị "Word/Excel".

---

## C. TOP-15 BACKLOG (xếp hạng theo tác động) — mỗi dòng 1 việc + đội sở hữu

> Gate chung #0: **cấp build host nested-virt** (đã là #1 ở `NANG-CAP-NHU-CAU-NGUOI-DUNG.md`) —
> mở khoá mọi dòng "verify on boot" dưới đây.

| # | Việc (dev nhận được ngay) | P | Effort | Đội |
|---|---|---|---|---|
| 1 | **Nối `namios-welcome.apply()` → hiệu lực THẬT** (Fcitx5 Telex/VNI + KDE scale + `mimeapps.list` + máy in mặc định), không chỉ ghi `welcome.json` — làm "ít-thao-tác" thành thật (A20). | P0 | M | 3 |
| 2 | **Chốt ngôn ngữ mặc định = tiếng Việt** + đầu tư lớp phủ **vi_NM** giảm trộn ngôn ngữ; đúng đối tượng ít rành (A21). | P0 | S–M | 1 (+3) |
| 3 | **Sinh `user-places.xbel` "Máy này" + Quick-access lúc đăng nhập đầu** (qua namios-welcome, biết `$HOME` thật) — This-PC mental model (A3). | P1 | M | 3 |
| 4 | **Landing "Cài đặt" nhóm theo việc + tìm-không-dấu** phủ lên KDE System Settings; **khai `systemsettings` tường minh** trong package-list (A5). | P1 | M | 1 (+3) |
| 5 | **Lớp "nhóm việc" cho menu Bắt đầu** (Văn phòng/Thuế/Kế toán/...) + **vẽ icon Bắt đầu riêng** thay placeholder `start-here-namios` (A1). | P1 | S–M | 1 (+3) |
| 6 | **Windows Update parity:** diễn tập `apt`→`needrestart`→Timeshift→rollback trên VM + nối **Update Center (SmartAI)** + help "cập nhật an toàn/quay lui" (A11). | P1 | M | 6 (+3) |
| 7 | **Security Center (kỳ vọng diệt virus):** giải thích mô hình bảo vệ Linux + nút **"Quét thư mục này"** (ClamAV on-demand); KHÔNG hứa chặn 100% (A12). | P1 | S | 1 (+3) |
| 8 | **CI phát hiện xung đột phím tắt** (UX12-019) trên `design/keyboard-shortcuts.json` + boot-test full map khi Fcitx5 bật (A19). | P1 | S–M | 1 (+3) |
| 9 | **DB thiết bị theo model + ma trận PnP** (máy in/Wi‑Fi/scanner Canon/HP/Epson/Brother) — cần HW pilot (A13). | P1 | L | 3 |
| 10 | **Ký số PDF bằng chứng thư mềm (.p12)** trong Okular/LibreOffice + help tiếng Việt; bộ kiểm in A4/A5/2-mặt/dấu/PDF/Wine (A14). | P1 | M | 3 (+5) |
| 11 | **Icon Thùng rác trên desktop** qua `namios-add-widgets.sh` (applet `org.kde.plasma.trash`) (A9). | P2 | S | 3 |
| 12 | **Bật + tài liệu hoá Clipboard history (Klipper, Meta+V)**: `klipperrc` mặc định + ghim systray + 1 dòng help — win dễ (A10). | P2 | S | 3 |
| 13 | **Task Manager:** khai `plasma-systemmonitor` tường minh + gán **Ctrl+Shift+Esc** mở nhanh trong `kglobalshortcutsrc` (A16). | P2 | S | 3 |
| 14 | **Boot-verify lớp quen thuộc đã viết** (taskbar 4 cụm, Aero-snap, Overview, F5, địa chỉ sửa, double-click, group-id KRunner) trên Wayland + X11 (A2/A6/A7/A17/A18). | P1 | S | 3 |
| 15 | **Thông báo + "Cài đặt nhanh":** `plasmanotifyrc` mặc định + gom cụm systray (mạng/âm/độ sáng) kiểu quick-settings tiếng Việt (A8). | P2 | S | 1 (+3) |

*Hết tài liệu. Nguồn bằng chứng chính: `docs/specs/UX-WINDOWS-FAMILIAR.md`, `docs/adr/0011-...md`,
`docs/roadmap/NANG-CAP-NHU-CAU-NGUOI-DUNG.md`, `docs/apps/NAMI-APP-CATALOG.md`,
`docs/design/DESIGN-SYSTEM.md`, `distro/live-build/config/includes.chroot/etc/skel/.config/*`
(kwinrc, kglobalshortcutsrc, dolphinrc, kdeglobals, plasma-org.kde.plasma.desktop-appletsrc,
mimeapps.list), `distro/live-build/config/package-lists/*.list.chroot`,
`distro/live-build/config/includes.chroot/usr/share/namios/docs/{WINDOWS-HABITS,UX-INTERACTION}.md`.*
