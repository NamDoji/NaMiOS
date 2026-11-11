# NaMiOS — Nâng cấp "đẹp, chuyên nghiệp, hiện đại, hướng-tương-lai" (MODERN-FUTURE-UX)

> **Loại tài liệu:** đề xuất thiết kế/UX có ưu tiên, grounded trên repo thật. **CHỈ phân
> tích + đề xuất. KHÔNG sửa code/gói khác, KHÔNG build, KHÔNG commit** (đúng vai trò
> senior product/UX designer, Team 1+3, read-only trừ file này).
> **Ngày:** 2026-11-11. **Phạm vi:** lấy phần tốt nhất của Windows 11 + macOS, vẫn là
> "HĐH cho người Việt" thật (không phải bản chép Windows/macOS) — đúng ranh giới
> **ADR-0011** (bố cục/luồng thao tác quen thuộc ĐƯỢC bắt chước; icon/font/âm thanh/
> thương hiệu độc quyền KHÔNG được chép).

## Quy ước đọc tài liệu này

- **verified_on_boot/verified_on_host: NO cho hầu hết mục dưới đây**, giữ đúng kỷ luật
  trung thực của repo (xem `docs/STATUS.md`, ADR 0011 "Bối cảnh môi trường hiện tại").
  Môi trường soạn tài liệu này KHÔNG có desktop KDE thật, KHÔNG có GPU — mọi khẳng định
  "sẽ đẹp hơn" dựa trên đọc mã nguồn/cấu hình đã có trong repo + kiến thức công khai về
  KWin/Plasma 6 (có đối chiếu 3 bản KDE Plasma Announcement 6.2/6.3/6.4 qua `web_fetch`
  trong phiên làm việc này — `web_search` không khả dụng trong môi trường này).
- **Ràng buộc trên hết (không đổi dù "đẹp hơn" có thể đòi hỏi)**: NaMiOS phải **chạy được
  trên máy yếu/không GPU** (mục tiêu đã có từ M0, hiện thực hoá bằng
  `kwinrc [Compositing] Enabled=false` mặc định + `namios-auto-compositing.sh` chỉ bật
  hiệu ứng trên máy có GPU thật) và **không được tái phát bug treo màn đăng nhập** đã từng
  xảy ra thật (bisect `dfbbf3c`/`23d774a`/`386f89d`, xem `docs/STATUS.md` + git log). Mọi
  đề xuất "hiện đại hơn" trong tài liệu này được chấm RISK theo đúng 2 ràng buộc này trước
  khi chấm P0/P1/P2.
- Mỗi mục: **WHAT** (trải nghiệm) → **WHY** (vì sao đọc là hiện đại/cao cấp) → **MECHANISM**
  (khoá/thành phần KDE Plasma 6 thật) → **RISK** (đặc biệt máy yếu/không-GPU + an toàn đăng
  nhập) → **PRIORITY** (P0/P1/P2 theo thang đã dùng trong `WINDOWS-FEATURE-PARITY.md`) →
  **MUST-VERIFY-ON-REAL-HARDWARE** (có/không).
- **Phát hiện quan trọng khi rà repo (không được bỏ qua):** `WINDOWS-FEATURE-PARITY.md`
  A20 và `NANG-CAP-NHU-CAU-NGUOI-DUNG.md` §3.2 (cả hai ghi ngày 2026-11-11, cùng ngày viết
  tài liệu này) đều liệt **"wizard `namios-welcome` mới ghi `welcome.json`, CHƯA áp hiệu
  lực thật"** là gap **P0**. Nhưng đọc trực tiếp `src/namios_welcome/firstrun.py` (mtime
  mới nhất trong cây `src/`) cho thấy đã có `apply_runtime_desktop_settings()` gọi thật
  `kwriteconfig6` (KScreen `ScaleFactor`), ghi `~/.config/fcitx5/conf/unikey.conf`
  (IME Telex/VNI), `xdg-mime default` (mimeapps.list), `lpoptions -d` (máy in mặc định) —
  và hàm này **đã được gọi** từ `ui.py:247`, không phải code chết. **Hai tài liệu kia có
  thể đã lỗi thời vài giờ** so với code hiện tại; tài liệu này KHÔNG lặp lại "P0: nối
  apply() → hiệu lực thật" như một việc chưa làm, mà đổi khung thành mục #8 dưới đây
  (xác nhận boot-test + phản hồi trực quan ngay, không phải "chưa viết code"). Nếu khi đọc
  tài liệu này mà `apply_runtime_desktop_settings` đã bị revert/chưa merge, coi lại mục #8
  như P0 "chưa làm" đúng như 2 tài liệu kia.

---

## A. Mười mục nâng cấp (đúng danh sách bắt buộc của việc này)

### 1. Fractional / per-screen scaling

**WHAT.** Màn hình laptop 125–150% + màn ngoài 100% cùng lúc, chữ/icon sắc nét ở mọi tỉ
lệ (không mờ/không lệch — đúng cách Windows 11 và macOS làm scaling hỗn hợp).

**WHY hiện đại/cao cấp.** Scaling mờ/lem là dấu hiệu "desktop Linux chưa hoàn thiện" rõ
nhất với người mới chuyển máy. Đây đúng lúc để làm: **Plasma 6.3 (phát hành ~đầu 2025) đã
đại tu cách tính fractional scaling, "snap" phần tử vào lưới pixel của màn hình, giảm mờ/
khoảng hở** — xác nhận qua KDE Announcement 6.3 (`kde.org/announcements/plasma/6/6.3.0/`,
mục "Graphics").

**MECHANISM.** Scale theo từng màn hình lưu ở `KScreen` (console `kscreen-console`/KCM
"Cấu hình màn hình"), key thực tế theo **hash connector+EDID của màn hình đó** — KHÔNG
seed tĩnh được trong `/etc/skel` vì hash không biết trước khi cài (cùng loại vấn đề đã ghi
đúng ở `UX-WINDOWS-FAMILIAR.md` §6 cho `user-places.xbel`). Per-output fractional scaling
**thật-mượt chỉ có đầy đủ trên Wayland**; trên X11, Plasma chỉ scale toàn cục một mức
(`Xft.dpi`/`QT_SCALE_FACTOR`-kiểu), không scale riêng từng màn — gắn trực tiếp vào mục #2.
`src/namios_welcome/firstrun.py` đã có `_apply_ui_scale()` ghi `kwriteconfig6 --group
KScreen --key ScaleFactor` cho ĐÚNG MỘT mức (không phân biệt nhiều màn) — đây là lớp "ít
nhất có một mức scale áp dụng được", không phải per-monitor thật.

**RISK.** (a) **Khoá vào mục #2**: muốn per-monitor fractional scaling thật-mượt nghĩa là
cần Wayland — mà Wayland hiện bị **chủ động ẩn** vì từng treo đăng nhập dưới QEMU/TCG
software-raster (xem mục #2). (b) Không thể test trong QEMU/TCG hiện tại vì không có
EDID/nhiều-màn-hình thật. (c) `_apply_ui_scale()` ghi scale toàn cục chưa chắc có hiệu lực
tức thì (cần `KWin reconfigure` hoặc đăng xuất/đăng nhập lại — chưa boot-test).

**PRIORITY: P1** (giá trị hình ảnh cao trên máy thật có GPU, nhưng phải chờ quyết định #2).
**MUST-VERIFY-ON-REAL-HARDWARE: CÓ** — cần máy/VM nhiều màn hình thật, HiDPI thật; không
mô phỏng được trong QEMU/TCG.

---

### 2. Wayland vs X11 — phiên mặc định (RỦI RO TRUNG THỰC, đọc kỹ trước khi đổi)

**WHAT.** Quyết định NaMiOS có chuyển phiên mặc định sang **Wayland** (đúng ý định ban đầu
của `ADR-0003`: "Wayland là ứng viên mặc định") để mở khoá hầu hết các mục "hiện đại" còn
lại trong tài liệu này, hay tiếp tục **X11** như hiện tại.

**WHY quan trọng nhất trong tài liệu này.** Gần như MỌI mục "hướng tương lai" ở đây —
scaling theo từng màn (#1), cử chỉ 4-ngón mở Overview, pinch 3-ngón zoom accessibility
(Plasma 6.4), compositing mượt/tear-free, cách ly input/hiển thị tốt hơn (SEC-004 trong
`docs/threat-model.md`) — chỉ có đầy đủ hoặc chỉ có trên Wayland. Giữ X11 vĩnh viễn giới
hạn trần "hiện đại" của NaMiOS.

**MECHANISM.** Lựa chọn phiên ở SDDM (`wayland-sessions/` vs `xsessions/` desktop file) +
khoá `DisplayServer=`/`Session=` trong `/etc/sddm.conf.d/*.conf` (đã dùng đúng cơ chế "file
sau theo ABC đè file trước" ở `10-namios-theme.conf`, có thể tái dùng cho session).

**RISK — PHẢI NÊU THẬT, KHÔNG ĐƯỢC NHẸ HOÁ.** Lịch sử commit của CHÍNH repo này cho thấy
Wayland **đã bị chủ động ẩn** sau khi gây **treo thật** ở màn đăng nhập dưới QEMU/TCG
software-raster:

- `23d774a fix(boot): ẩn phiên Wayland → ép X11 (plasmax11) trong QEMU headless`
- `386f89d fix(login): ẩn phiên Wayland → SDDM chỉ còn X11 (plasmax11)...`
- `dfbbf3c` là build từng kẹt phiên `plasmax11` (nghi do theme/Aurorae, chưa bisect tách
  hẳn — xem mục #3), nhưng **bản thân phiên Wayland cũng có lịch sử treo riêng**, không
  chỉ do theme.

Đây là **bằng chứng thật, không phải lý thuyết**. Chưa có boot thật trên máy có GPU nào
xác nhận lại Wayland ổn định từ sau các lần fix đó. Đẩy Wayland trở lại làm mặc định hàng
loạt **trước khi có pilot máy GPU thật** là đi ngược trực tiếp mục tiêu "chạy được trên máy
yếu/không GPU" và có rủi ro thật tái phát đúng lớp bug mà nhiều wave trước đã tốn công sửa
(`docs/releases/boot-evidence/`).

**ĐỀ XUẤT — KHÔNG đổi mặc định hàng loạt, mà làm có-kiểm-soát:**

1. Giữ cơ chế `systemd-detect-virt` đã có trong `namios-auto-compositing.sh` làm hình mẫu:
   SDDM chọn **Wayland CHỈ khi phát hiện GPU thật** (ví dụ qua `drm`/`lspci` kiểm tra driver
   GPU hoạt động, không phải llvmpipe software), **X11 là lưới an toàn** khi không chắc
   (VM, máy cũ, phát hiện lỗi) — đúng nguyên tắc fail-closed đã dùng ở script đó.
2. KHÔNG được coi "build không lỗi" là "Wayland đã ổn" — chỉ chốt sau khi boot thật trên
   ≥1 máy GPU thật (gate chung #0 của `WINDOWS-FEATURE-PARITY.md`) VÀ thử lại đúng kịch bản
   từng treo (QEMU/TCG) để xác nhận fallback X11 vẫn chạy.
3. Luôn giữ X11 chọn được tay trong SDDM (không gỡ hẳn) làm phương án thoát hiểm.

**PRIORITY: P0** (cổng quyết định — mở hoặc khoá phần lớn các mục P1 còn lại) — nhưng
**câu trả lời KHÔNG được là "cứ đổi mặc định sang Wayland"** cho tới khi có bằng chứng thật.
**MUST-VERIFY-ON-REAL-HARDWARE: CÓ** — mục rủi ro cao nhất trong toàn tài liệu.

---

### 3. Vật liệu kiểu Fluent/Acrylic + chuyển động nhất quán

**WHAT.** Panel/popup kính mờ có chữ vẫn đọc rõ (Windows 11 gọi "Mica/Acrylic", macOS gọi
"vibrancy"), chuyển động mở/đóng/hover nhất quán về thời lượng/easing.

**WHY hiện đại/cao cấp.** Tín hiệu hình ảnh "cao cấp" rõ nhất; đã là **ý định thiết kế có
sẵn** (`branding/style/namios.css` — "kính mờ", squircle iOS, bóng mềm nhiều lớp;
desktoptheme `NaMiOS-Sen`).

**MECHANISM — PHẦN LỚN ĐÃ CẤU HÌNH SẴN, KHÔNG PHẢI VIỆC MỚI.** Đọc `etc/skel/.config/kwinrc`
thật trong repo cho thấy:

- `[Plugins] blurEnabled=true` + **`contrastEnabled=true`** — hiệu ứng "Background Contrast"
  của KWin chính là cơ chế **giữ chữ rõ trên nền mờ**, tương đương trực tiếp "Acrylic" của
  Windows. Đã cấu hình, không phải đề xuất mới.
- `scaleEnabled`/`slideEnabled`/`slidingpopupsEnabled=true`, `wobblywindowsEnabled=false`,
  `cubeslideEnabled=false` — chuyển động mượt kiểu iPadOS, tắt hiệu ứng "kiểu cũ".
- `kdeglobals [KDE] AnimationDurationFactor=0.6` — **quyết định thiết kế đã có lý do ghi rõ**:
  rút ngắn ~40% thời lượng animation để animation Plasma Quick (chạy qua `QPainter` raster
  khi compositing tắt) vẫn mượt trên máy yếu/không GPU — đây là **cân bằng đúng đắn đã làm**,
  không phải lỗ hổng cần vá.
- Desktoptheme `NaMiOS-Sen` tự có file `colors` riêng để panel luôn tối/chữ sáng (fix bug
  "icon khay tối trên panel tối") độc lập với `ColorScheme=NaMiOS` sáng của vùng nội dung.

**RISK.** (a) **TOÀN BỘ blur/contrast/trong-suốt là hiệu ứng OpenGL compositing — mà
compositing TẮT theo mặc định** (`[Compositing] Enabled=false`, `OpenGLIsUnsafe=true`) để
tránh màn đen trên máy không GPU/QEMU. Đường DUY NHẤT để thấy các hiệu ứng này là
`namios-auto-compositing.sh` (đã có trong `includes.chroot`, dùng `systemd-detect-virt --vm`
để chỉ bật compositing khi KHÔNG phải VM) — **script này tồn tại nhưng chưa từng boot-test
trên máy GPU thật** (tự ghi `verified_on_host: NO` trong chính file). (b) **Viền cửa sổ
riêng (Aurorae "NaMiOS Lotus", 3 nút tròn)** — nửa còn lại của "chrome" đồng bộ — **ĐANG BỊ
COMMENT TẮT** trong `kwinrc` vì nghi (chưa xác nhận) liên quan tới lần treo đăng nhập
`dfbbf3c`; tức hôm nay cửa sổ vẫn dùng viền Breeze trần, dù asset NaMiOS đã dựng xong. (c)
Tương phản chữ trên nền kính mờ với **dấu tiếng Việt cỡ nhỏ** chưa được đo riêng (khác biệt
non-text contrast token `--line` đã bị PL12.2 flag ~1.2–1.5:1, không đạt 3:1).

**PRIORITY: P0** (mở khoá rẻ nhất, nhiều giá trị nhất trong tài liệu này — mã đã viết sẵn,
chỉ còn thiếu bước boot-test; không cần code mới). **MUST-VERIFY-ON-REAL-HARDWARE: CÓ** —
cụ thể: (1) auto-compositing thật sự lật `Enabled=true`+`OpenGLIsUnsafe=false` trên máy GPU
và KWin không crash; (2) chữ tiếng Việt có dấu đọc được trên nền blur ở cỡ chữ nhỏ; (3)
bisect lại Aurorae riêng (tách khỏi desktoptheme) trước khi bật lại viền cửa sổ riêng.

---

### 4. Panel/widget được chuốt lại

**WHAT.** Taskbar/dock dưới cùng cảm giác "đã hoàn thiện" (icon đúng, systray đầy đủ, cụm
rõ ràng) thay vì cảm giác "KDE mặc định chưa chỉnh".

**WHY.** Panel là thành phần nhìn thấy nhiều nhất — ấn tượng đầu "rẻ" hay "cao cấp" nằm ở
đây nhiều hơn mọi màn hình khác.

**MECHANISM.** `plasma-org.kde.plasma.desktop-appletsrc` đã cấu hình panel dạng dock nổi
(`floating=1`) gồm Kickoff + Icon-Only Task Manager + System Tray + Digital Clock. Plasma
6.3 thêm **"Clone Panels"** (nhân bản cấu hình panel 1 chạm) + script hoá được độ trong suốt
panel theo từng màn hình — hữu ích khi làm nhất quán đa màn hình sau này.

**GAP THẬT (không bịa).** (a) Icon nút Bắt đầu vẫn là placeholder generic (`start-here.png`
trong `icons/NaMiOS-Lotus/64x64/apps/`, không phải glyph riêng NaMiOS). (b) Danh sách applet
trong `System Tray` **không được khai rõ** trong `appletsrc` — phụ thuộc mặc định Plasma,
chưa xác nhận có đủ Fcitx5 + plasma-nm + plasma-pa trên Debian 13 trixie thật (đúng gap A2
đã ghi trong `WINDOWS-FEATURE-PARITY.md`). (c) Plasma có thể tự renumber applet ở lần đăng
nhập đầu (hành vi bình thường, đã ghi rõ, không phải lỗi).

**RISK.** Thấp — chủ yếu là verify cấu hình, không đụng tới an toàn/hiệu năng.

**PRIORITY: P1. MUST-VERIFY-ON-REAL-HARDWARE: CÓ** (so khớp ảnh chụp thật với
`docs/design/mockups/namios-desktop.svg`).

---

### 5. Trung tâm thông báo + Cài đặt nhanh (Quick Settings)

**WHAT.** Cụm 1-chạm kiểu Win11 (Wi-Fi/âm lượng/độ sáng/Không làm phiền) + lịch sử thông báo,
tiếng Việt.

**WHY.** Gap đã được xác nhận cụ thể trong `WINDOWS-FEATURE-PARITY.md` A8: không có
`plasmanotifyrc`, không có cụm "Cài đặt nhanh" được gom tên.

**MECHANISM — khung sự thật, không phóng đại.** KDE **không có một widget "Quick Settings"
tách biệt** như Win11/GNOME mới — **System Tray chính là nơi chứa** network/volume/
brightness/battery applet (đã có sẵn trong `appletsrc`). Việc đúng cần làm là **gom nhóm +
đặt tên tiếng Việt** cho cụm đó ("Cài đặt nhanh"), không phải xây một panel mới từ đầu.
Lịch sử thông báo + Không-làm-phiền là mặc định Plasma (6.3 đã thêm: khi tắt DND, hiện số
thông báo đã bỏ lỡ thay vì dội hết một lúc — xác nhận qua KDE Announcement 6.3). Config mặc
định hợp lý nằm ở `plasmanotifyrc` (hiện **không tồn tại** trong `/etc/skel`, xác nhận bằng
grep thật trong repo).

**RISK.** Thấp–trung bình. Thêm applet (ví dụ gom/hiển thị rõ cụm quick-settings) nên dùng
ĐÚNG cơ chế đã chứng minh an toàn: `namios-add-widgets.sh` (gọi `evaluateScript` qua D-Bus
lúc đăng nhập lần đầu, đã dùng cho `org.namios.smartai`/`org.namios.workgroups`) — không cần
GPU/compositing, hoạt động được cả khi compositing tắt.

**PRIORITY: P1** (gom nhóm + nhãn) **/ P2** (polish DND/lịch sử).
**MUST-VERIFY-ON-REAL-HARDWARE: CÓ** — xác nhận đúng applet nào thật sự nạp vào systray trên
Debian 13 trixie + đúng tên khoá `plasmanotifyrc` Plasma 6 đọc.

---

### 6. Tìm kiếm/launcher toàn cục được chuốt lại

**WHAT.** Meta+Space mở tìm kiếm kiểu Spotlight: app, file, tính toán, đổi đơn vị, giờ còn
đọc được mã màu (`KRunner Gets Color`, Plasma 6.4).

**WHY.** Đã là mục tự nhận "hơn Win+R" trong chính phân tích của repo (A17,
`WINDOWS-FEATURE-PARITY.md`) — KRunner thực sự mạnh hơn Run/Search của Windows ở nhiều mặt,
chỉ còn 1 rủi ro cấu hình cần đóng.

**MECHANISM.** `kglobalshortcutsrc [org.kde.krunner.desktop] _launch=Meta+Space...` đã thêm
(giữ nguyên Alt+Space/Alt+F2 cũ — `UX-INTERACTION.md` §3); lớp "nhóm việc" cho Kickoff
(`org.namios.workgroups`) đã dựng + tự thêm qua `namios-add-widgets.sh`.

**RISK.** Đúng MỘT rủi ro đã được repo tự ghi: tên group `org.kde.krunner.desktop` (kiểu
reverse-DNS Plasma 6 mới) **vs** `krunner.desktop` (tên cũ) — chưa chắc 100% trên Debian 13
trixie thật. Fail-safe: nếu sai, Meta+Space không làm gì (không crash, Alt+Space/Alt+F2 vẫn
chạy).

**PRIORITY: P1 (verify)** — gần xong, chỉ còn 1 lệnh `kreadconfig6` cần chạy trên máy thật
(đã viết sẵn trong `UX-INTERACTION.md` §3). **MUST-VERIFY-ON-REAL-HARDWARE: CÓ.**

---

### 7. Sáng/Tối tự động

**WHAT.** Tự đổi giữa chrome desktop tối + vùng nội dung sáng (đã là ý định thiết kế gốc,
`DESIGN-SYSTEM.md` §1) theo giờ trong ngày, giống "Auto" của Win11/macOS.

**WHY.** Đổi theo giờ đọc là "hệ thống biết tự lo" — tín hiệu cao cấp. NHƯNG cần nói thật:
phần lớn người dùng mục tiêu (kế toán/văn phòng) sẽ muốn **MỘT** chế độ sáng ổn định khớp
màu khi in ấn tài liệu Office hơn là đổi màu tự động.

**MECHANISM.** System Settings > Màu sắc có lịch tự đổi theme sáng/tối (theo giờ cố định
hoặc giờ mặt trời mọc/lặn) — **khác hẳn** `kwinrc [NightColor]` (tính năng giảm ánh sáng
xanh, không phải đổi theme). Hiện `kdeglobals [General] ColorScheme=NaMiOS` là **MỘT** theme
cố định (tối chrome/sáng nội dung theo đúng ý định thiết kế) — chưa cấu hình lịch tự đổi nào.

**RISK.** Thấp về kỹ thuật, nhưng có **xung đột mục tiêu cần nói rõ, không lờ đi**: trục
"chrome tối/nội dung sáng" của Design System KHÔNG phải cùng trục với "dark mode toàn ứng
dụng" (ví dụ canvas LibreOffice tối) — việc đó lớn hơn (tầng app, không phải tầng shell) và
có thể LÀM HẠI trải nghiệm kế toán/văn phòng cần xem tài liệu khớp màu in. Không để "cảm
giác hiện đại" đẩy sang dark-mode toàn diện mặc định.

**PRIORITY: P2** — giữ nguyên chế độ "tối-chrome/sáng-nội-dung" làm mặc định trung thực;
lịch tự đổi riêng cho SHELL (không đụng nội dung Office) là nice-to-have.
**MUST-VERIFY-ON-REAL-HARDWARE: Không cấp thiết** (effort nhỏ khi làm).

---

### 8. Onboarding/first-run liền mạch

**WHAT.** `namios-welcome` không chỉ hỏi rồi lưu, mà **cho thấy ngay** từng lựa chọn đã có
hiệu lực + một tour ngắn "4 việc đầu tiên".

**WHY.** Khoảnh khắc first-run quyết định cảm giác "hoàn chỉnh" hay "demo dở" nhiều nhất —
đã là mục P0 tự nhận ở cả `WINDOWS-FEATURE-PARITY.md` (#1 trong Top-15) và
`NANG-CAP-NHU-CAU-NGUOI-DUNG.md` (#4 trong Top-10).

**MECHANISM — CẬP NHẬT so với 2 tài liệu kia (xem cảnh báo đầu tài liệu).** Đọc trực tiếp
`src/namios_welcome/firstrun.py` (bản mới nhất trong repo) cho thấy `apply_runtime_desktop_
settings()` ĐÃ gọi thật: `kwriteconfig6` (KScreen `ScaleFactor`), ghi
`~/.config/fcitx5/conf/unikey.conf` (Telex/VNI) + `fcitx5-remote -r` để nạp lại, `xdg-mime
default` (mimeapps.list), `lpoptions -d` (máy in mặc định) — và hàm này **được gọi thật** từ
`ui.py:247`, không phải code chết chưa nối. Nếu đúng, phần lớn gap "có UI, chưa có tác dụng"
mà 2 tài liệu khác liệt P0 **có thể đã đóng một phần** trong vài giờ gần nhất.

**ĐỀ XUẤT UX bổ sung (phần còn thiếu thật, không trùng việc đã làm):** (1) sau MỖI bước
wizard, hiện trạng thái "Đã áp dụng ✓" ngay (không chỉ ở cuối) — mỗi `RuntimeApplyOutcome`
đã có đủ dữ liệu (`status`/`detail`) để vẽ UI này ngay, chỉ cần `ui.py` hiển thị tức thì
thay vì gộp báo cáo ở cuối. (2) Tour 3–5 "việc đầu tiên" (mở Văn phòng, gõ tiếng Việt, lưu,
in PDF, nối Wi-Fi) — chưa thấy trong `ui.py`.

**RISK.** Thấp (không cần GPU/compositing) — nhưng PHẢI boot-test thật: mã gọi `fcitx5-remote
-r`, `xdg-mime`, `lpoptions` có chạy đúng trên Debian 13 trixie thật với Fcitx5 đang chạy
không, hay chỉ "không lỗi vì thiếu lệnh" (code đã có nhánh `skipped` khi thiếu lệnh, dễ nhầm
"đạt" với "bỏ qua an toàn").

**PRIORITY: P0** (xác nhận boot-test) — nhưng khung lại là **"verify + hiển thị ngay"**,
không phải "viết lại từ đầu" như 2 tài liệu khác mô tả.
**MUST-VERIFY-ON-REAL-HARDWARE: CÓ.**

---

### 9. Khả năng tiếp cận (Accessibility)

**WHAT.** Đạt mục tiêu đã tự đặt (WCAG 2.2 AA) + tận dụng các cải tiến "miễn phí" của Plasma
6.4: điều khiển con trỏ bằng numpad, pinch 3-ngón để zoom, trang "Hoạt ảnh" gom mọi cấu hình
giảm-chuyển-động vào 1 nơi, Breeze Dark tối hơn (dễ đọc hơn), nền tối hẳn phía sau hộp thoại
xác thực (dễ thấy ô nhập mật khẩu).

**WHY.** Đã là giá trị có sẵn của repo (mục tiêu WCAG AA, PL12.2 đã đo + chỉnh 3 token
tương phản, glossary 55 thuật ngữ) — mục này tận dụng tiếp, không phải bắt đầu từ 0.

**MECHANISM.** System Settings > Khả năng tiếp cận; Plasma 6.4 thêm trang **"Hoạt ảnh"**
riêng gom toggle giảm-chuyển-động — điểm chỉ-một-nơi tốt để trỏ người dùng tới (đối chiếu
`kde.org/announcements/plasma/6/6.4.0/`, mục "Accessibility"/"UI & Visual Design"). Hiệu ứng
Zoom "sắc từng pixel" (6.3) hữu ích cho người yếu thị lực đọc tài liệu/số liệu kế toán.

**RISK.** Các cải tiến mới nhất kể trên (numpad điều khiển con trỏ, pinch 3-ngón) **CHỈ có
trên phiên Wayland** (xác nhận từ Announcement 6.4) — lại khoá vào mục #2. Trên X11 (mặc
định hiện tại), người dùng accessibility chỉ có bộ tính năng đời cũ hơn. Test screen reader
+ 200% chữ vẫn `blocked-infra` (UX12-035, `docs/backlog/UX12-backlog.md`) — chưa làm được.

**PRIORITY: P1** (trong tầm tay, chủ yếu verify + 1 lượt test screen reader/200% chữ dành
riêng, đã được flag đúng chỗ). **MUST-VERIFY-ON-REAL-HARDWARE: CÓ.**

---

### 10. Micro-interaction "có hồn"

**WHAT.** Hàng loạt chi tiết nhỏ: hover mượt, icon "thở" nhẹ khi mở, Clock widget hiện "hôm
nay có 6 lịch" khi nhiều việc, kéo file ra khỏi cửa sổ không bị nhảy lên trên cùng, badge số
thông báo-đã-lỡ khi tắt Không-làm-phiền, biểu tượng máy in nhấp nháy khi đang in — cộng dồn
thành cảm giác "có người chăm chút", không phải một tính năng lớn nào.

**WHY.** Đây đúng nghĩa "feels alive" — không phải 1 feature to, mà mật độ chi tiết nhỏ.

**MECHANISM.** Phần lớn **đã có sẵn, miễn phí** trong Plasma 6.3/6.4 (xác nhận qua
Announcement 6.3: Digital Clock hiện đủ sự kiện khi >5 lịch, kéo-thả không nhảy cửa sổ;
Announcement 6.3: badge số thông báo-đã-lỡ khi thoát Không-làm-phiền; widget máy in có
spinner khi đang in) — NaMiOS **không cần tự xây**, chỉ cần KHÔNG chạy một bản Plasma cũ
hơn thiếu các chi tiết này.

**RISK.** Gần như không có rủi ro kỹ thuật — rủi ro duy nhất là **compositing tắt theo mặc
định xoá mất lớp hiệu ứng hover/slide** mang theo hầu hết các tín hiệu này (khoá vào #3).

**PRIORITY: P2** (hưởng lợi "miễn phí" ngay khi #2/#3 được mở khoá — không cần làm thêm).
**MUST-VERIFY-ON-REAL-HARDWARE: xác nhận nhanh sau khi compositing đã an toàn trên máy thật.**

---

## B. Chỗ KDE đã làm tốt — KHÔNG phát sinh việc (giữ trung thực, không bịa gap)

- **Background Contrast + Blur effect** (tương đương Acrylic) **đã cấu hình sẵn** trong
  `kwinrc` — chỉ chờ compositing được xác nhận an toàn, không cần code mới (mục #3).
- **`AnimationDurationFactor=0.6`** là một quyết định cân bằng performance/premium đã làm
  đúng, có lý do ghi rõ — không phải thứ cần "sửa".
- **KRunner** đã vượt Win+R về năng lực (tính toán, đổi đơn vị, giờ cả mã màu ở 6.4) — chỉ
  còn 1 rủi ro tên group cần verify (mục #6).
- **Digital Clock, notification missed-count, printer spinner, no-window-jump-on-drag** —
  tất cả đã là hành vi mặc định của Plasma 6.3+ mà NaMiOS không cần tự xây (mục #10).
- **`namios-add-widgets.sh` (evaluateScript qua D-Bus)** là cơ chế đúng, đã chứng minh hoạt
  động (SmartAI + nhóm việc) để thêm widget lúc đăng nhập đầu — tái dùng được cho Thùng rác,
  cụm Quick Settings, v.v. mà không cần sửa `appletsrc` tĩnh (vốn bị Plasma bỏ qua).
- **`namios-welcome` `apply_runtime_desktop_settings()`** — theo đọc mã nguồn hiện tại, đã
  nối thật tới hệ thống (không chỉ ghi JSON) — xem cảnh báo "CẬP NHẬT" ở đầu tài liệu và mục
  #8; cần boot-test xác nhận, nhưng KHÔNG cần viết lại từ đầu.

**Việc KHÔNG nên làm (giữ đúng phạm vi, không lấn macOS/Windows quá đà):**

- **Global menu kiểu macOS** (menu app rời khỏi cửa sổ, nằm trên top bar) — Plasma có widget
  cho việc này, nhưng KHÔNG nên làm: phá đúng mô hình "menu nằm trong cửa sổ" mà người dùng
  Windows quen (ADR-0011 "quen thuộc KHÔNG phải pixel-clone", mục tiêu là Windows-familiar,
  không phải lai macOS ở điểm này). Không đưa vào roadmap.
- **Dark-mode toàn ứng dụng mặc định** (canvas LibreOffice tối) — xem mục #7, đây là việc
  tầng app lớn hơn, có thể làm hại workflow in ấn/khớp màu của kế toán/văn phòng; không nên
  làm chỉ vì "nhìn hiện đại hơn".

---

## Top-10 "làm cho NaMiOS cảm giác cao cấp" (mỗi dòng 1 việc, đội sở hữu + ưu tiên)

| # | Việc | Đội | Ưu tiên |
|---|---|---|---|
| 1 | **Boot-test `namios-auto-compositing.sh` trên máy GPU thật** — bật Blur/Contrast (Acrylic/kính-mờ tương đương Windows) đã cấu hình sẵn trong `kwinrc`, mã đã viết, chỉ thiếu xác nhận. | 3 | P0 |
| 2 | **Quyết định Wayland có-kiểm-soát** (chỉ bật khi phát hiện GPU thật, giống logic `systemd-detect-virt` đã dùng cho compositing) — KHÔNG đổi mặc định hàng loạt, có lịch sử treo đăng nhập thật phải tránh lặp lại. | 3 | P0 |
| 3 | **Xác nhận boot thật `apply_runtime_desktop_settings()` của `namios-welcome`** (IME/scale/mimeapps/máy in) + hiện "Đã áp dụng ✓" ngay sau mỗi bước, không chỉ ở cuối. | 3 | P0 |
| 4 | **Vẽ icon Bắt đầu riêng NaMiOS** (thay `start-here.png` placeholder) + khai rõ 5 applet systray mặc định (Fcitx5/mạng/âm/pin/thông báo) trong tài liệu + verify trên máy thật. | 1 (+3) | P1 |
| 5 | **Bisect lại Aurorae "NaMiOS Lotus" tách khỏi desktoptheme** trên đúng kịch bản từng treo (`dfbbf3c`) để bật an toàn viền cửa sổ riêng — nửa "chrome" còn thiếu của mục #3. | 3 | P1 |
| 6 | **Gom cụm systray thành "Cài đặt nhanh" tiếng Việt** + viết `plasmanotifyrc` mặc định (Không-làm-phiền khi trình chiếu, lịch sử hợp lý) qua đúng cơ chế `namios-add-widgets.sh`. | 1 (+3) | P1 |
| 7 | **Verify tên group `org.kde.krunner.desktop` vs `krunner.desktop`** cho Meta+Space (1 lệnh `kreadconfig6` đã viết sẵn trong `UX-INTERACTION.md` §3) — gần xong, chỉ thiếu bấm nút. | 3 | P1 |
| 8 | **Đo tương phản tiếng Việt (dấu thanh, cỡ chữ nhỏ) trên nền kính mờ** trước khi công bố "đẹp" — nối tiếp PL12.2, áp riêng cho hiệu ứng Background Contrast. | 1 | P1 |
| 9 | **Lịch sáng/tối tự động cho SHELL (không đụng canvas Office)** qua System Settings > Màu sắc — giữ nguyên trục "tối-chrome/sáng-nội-dung" đã chốt, không lấn sang dark-mode toàn ứng dụng. | 1 (+3) | P2 |
| 10 | **KHÔNG làm global menu kiểu macOS** — giữ menu trong cửa sổ đúng mô hình Windows-quen-thuộc (ADR-0011); dồn công sức vào #1–#8 trước khi nghĩ tới mở rộng macOS-hoá. | 3 | P2 |

---

*Nguồn bằng chứng chính: `docs/design/DESIGN-SYSTEM.md`, `docs/specs/UX-WINDOWS-FAMILIAR.md`,
`docs/adr/0011-...md`, `docs/roadmap/WINDOWS-FEATURE-PARITY.md`,
`docs/roadmap/NANG-CAP-NHU-CAU-NGUOI-DUNG.md`,
`distro/live-build/config/includes.chroot/usr/share/namios/docs/UX-INTERACTION.md`,
`distro/live-build/config/includes.chroot/etc/skel/.config/{kwinrc,kdeglobals,plasmarc,
plasma-org.kde.plasma.desktop-appletsrc}`, `distro/live-build/config/includes.chroot/
usr/local/bin/namios-auto-compositing.sh`, `src/namios_welcome/{firstrun.py,ui.py}`,
`branding/style/namios.css`, `design/tokens.json`, git log (`23d774a`, `386f89d`, `dfbbf3c`,
`64a6ade`), và 3 trang KDE Announcement Plasma 6.2/6.3/6.4 (`kde.org/announcements/plasma/6/`)
đọc qua `web_fetch` trong phiên làm việc này.*
