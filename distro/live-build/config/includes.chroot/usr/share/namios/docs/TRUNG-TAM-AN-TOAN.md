# Trung tâm An toàn (NaMiOS Security Center) — SEC-1

- **Mốc:** scaffold đầu tiên, 11/11/2026.
- **verified_on_host: NO cho lớp giao diện PySide6** (`ui.py`/`__main__.py`/hook
  cài đặt) — container phát triển hiện tại KHÔNG có PySide6/display (headless).
  **ĐÃ chạy thật** (không phải chỉ đọc lại) toàn bộ lớp lõi KHÔNG-GUI
  (`probes.py`/`actions.py`) bằng Python 3.11 thật trong sandbox này, kèm cả
  một bản giả lập `pkexec`/`ufw` để xác nhận luồng argv→pkexec→kết quả hoạt
  động đúng — xem mục 6.

## 1. Đây là gì — và KHÔNG phải là gì

Trung tâm An toàn là MỘT nơi gom 5 "thẻ" trạng thái an toàn mà người quen
Windows ("có phần mềm diệt virus") sẽ tìm: **Cập nhật**, **Tường lửa (UFW)**,
**AppArmor**, **Quét virus (ClamAV)**, **Sao lưu (Kup)**. Mỗi thẻ đọc trạng
thái THẬT bằng lệnh con an toàn (argv tĩnh, timeout, không shell — xem mục 3)
rồi hiển thị nguyên văn; khi một công cụ chưa cài, thẻ hiện **"CHƯA CÀI"** +
lệnh cài chính xác — **KHÔNG BAO GIỜ một dấu tích xanh giả**.

**KHÔNG** tự chế lại tường lửa/AppArmor/scanner/backup — mọi "hành động" chỉ
BẬT/MỞ công cụ thật đã có trong ảnh qua `pkexec` khi cần quyền (nguyên tắc
trung thực SEC-1: "OPEN them, don't reimplement").

**KHÔNG** thay thế `namios-security-center` (bảng kdialog/zenity một dòng
lệnh, ghi bởi `hooks/normal/0630-security-default.hook.chroot` phần (d),
launcher "NaMiSecurity") — hai công cụ cùng tồn tại trong đợt này, không đụng
tới nhau. `namios-security-center` là bảng tóm tắt nhanh (không có hành động);
Trung tâm An toàn (`namios-antoan`) là app đầy đủ có hành động + "Giới thiệu".

## 2. File đã tạo (TOÀN BỘ mới, không sửa file có sẵn nào)

| File | Vai trò |
| --- | --- |
| `includes.chroot/opt/namios/namios_antoan-src/__init__.py` | Gói Python — re-export + đăng ký i18n khi import |
| `includes.chroot/opt/namios/namios_antoan-src/__main__.py` | `python3 -m namios_antoan` — mở cửa sổ (import PySide6 trì hoãn) |
| `includes.chroot/opt/namios/namios_antoan-src/probes.py` | CHỈ ĐỌC trạng thái 5 thẻ (Python thuần, test được không cần PySide6) |
| `includes.chroot/opt/namios/namios_antoan-src/actions.py` | Hành động CÓ thay đổi/mở công cụ (pkexec cho việc cần quyền) |
| `includes.chroot/opt/namios/namios_antoan-src/ui.py` | Cửa sổ 5-thẻ PySide6, chạy probe/action trong `QThread` riêng |
| `includes.chroot/opt/namios/namios_antoan-src/branding.py` | Đọc `brand.json` (fail-safe, fallback cứng) + dựng QSS bố cục thẻ |
| `includes.chroot/opt/namios/namios_antoan-src/_i18n.py` | Catalog VI/EN riêng (`antoan.*`), gồm "Giới thiệu" + 7 điều không-overclaim |
| `includes.chroot/usr/share/applications/namios-antoan.desktop` | Launcher "NaMiOS Security Center / Trung tâm An toàn" |
| `hooks/normal/0309-namios-antoan.hook.chroot` | Cài `/opt/namios/namios_antoan` + wrapper `/usr/bin/namios-antoan` (mirror `0305-namios-assistant.hook.chroot`) |
| `usr/share/namios/docs/TRUNG-TAM-AN-TOAN.md` | File này |

**KHÔNG đụng:** `namios-control-panel`, `namios-security-center`
(+ `.desktop` của nó), `namios-mo-sao-luu`, `namios-assistant*`,
`namios-smartai*`, `namios-chan-doan`, bất kỳ `package-lists/*`,
`appletsrc`/skel Plasma configs, calamares, bootloader.

## 3. Lệnh trạng thái CHỈ ĐỌC dùng cho từng thẻ (`probes.py`, KHÔNG cần quyền root)

| Thẻ | Lệnh/đọc file dùng để xác định trạng thái |
| --- | --- |
| Cập nhật | `apt list --upgradable` (đọc cache apt cục bộ, KHÔNG gọi mạng) + đọc file `/etc/apt/apt.conf.d/51namios-unattended` (unattended-upgrades bật/tắt) |
| Tường lửa (UFW) | `which ufw` (đã cài?) + `systemctl is-active ufw.service` (KHÔNG dùng `ufw status` ở bước đọc tự động vì lệnh đó cần root — xem mục 4) |
| AppArmor | `aa-enabled --quiet` (nếu có) hoặc đọc `/sys/module/apparmor/parameters/enabled` |
| Quét virus (ClamAV) | `which clamscan`/`which freshclam` (đã cài?) + `stat` tuổi các file `/var/lib/clamav/{daily,main}.{cvd,cld}` + `systemctl is-active clamav-daemon.service` (mong đợi KHÔNG chạy — đúng thiết kế on-demand) |
| Sao lưu (Kup) | `dpkg-query -W -f='${Status}' kup-backup` (đã cài?) + đọc `~/.config/kuprc` (Backups enabled/Plan/Destination UUID) + quét `/proc/*/comm` tìm `kupdaemon` đang chạy |

Mọi lệnh con ở trên chạy qua `namios_security.run_argv` (WP8 — argv tĩnh,
`shell=False`, timeout 8s) hoặc đọc file/`\`/proc\`` bằng Python thuần; không
cái nào cần `pkexec`/mật khẩu quản trị, và tất cả đều fail-safe (thiếu công cụ
→ `installed=False` + `install_hint`, KHÔNG raise).

## 4. Hành động CẦN quyền quản trị (`actions.py`, LUÔN qua `pkexec`)

| Hành động | Lệnh thật chạy sau `pkexec` |
| --- | --- |
| Bật tường lửa | `pkexec ufw --force enable` (hỏi xác nhận trong app TRƯỚC khi gọi; `--force` chỉ bỏ qua câu hỏi "yes" tương tác của chính `ufw` vì không có TTY khi chạy từ GUI, KHÔNG phải bỏ qua xác nhận của NaMiOS) |
| Xem chi tiết luật tường lửa | `pkexec ufw status verbose` |
| Xem chi tiết hồ sơ AppArmor | `pkexec aa-status` |
| Cập nhật chữ ký ClamAV | `pkexec freshclam` |

**KHÔNG có nút "Bật AppArmor"**: AppArmor LSM chỉ enforce thật khi kernel
cmdline có `apparmor=1 security=apparmor` (cấu hình bootloader + cần reboot,
xem `docs/SECURITY-DEFAULTS.md` §3) — một nút bấm trong app không thể làm
việc này một cách trung thực, nên app chỉ giải thích + hướng dẫn đọc tài liệu,
không giả vờ có một hành động runtime không tồn tại.

**Quét virus "Quét thư mục này"** chạy `clamscan -r <thư mục người dùng
chọn>` **KHÔNG qua `pkexec`** — quét bằng quyền user hiện tại là đúng mô hình
(không có lý do kỹ thuật/bảo mật để chạy scanner bằng root trên file của
chính user), timeout rộng (30 phút) cho thư mục lớn.

**Mở Trung tâm cập nhật** (`namios-control-panel --category update` → Discover
→ `kcmshell6 kcm_updates`) và **Mở cài đặt Sao lưu** (`namios-mo-sao-luu` →
`kcmshell6/5 kcm_kup` → `systemsettings`) KHÔNG qua `pkexec` — chỉ khởi chạy
tiến trình độc lập (`subprocess.Popen` argv-only, `start_new_session=True`,
KHÔNG chờ/KHÔNG capture output), các công cụ đó tự xin quyền riêng nếu cần.

## 5. Gói/công cụ nền — ĐÃ CÓ SẴN trong package-lists, KHÔNG cần thêm gì

Đã rà lại toàn bộ `distro/live-build/config/package-lists/*.list.chroot`
trước khi viết app này — **tất cả công cụ nền app này tham chiếu ĐÃ được khai
báo**, không cần DEV thêm package-list mới cho đợt SEC-1 này:

- `ufw` — `package-lists/0630-security.list.chroot`.
- `apparmor` + `apparmor-utils` (cho `aa-status`/`aa-enabled`) —
  `package-lists/0630-security.list.chroot`.
- `clamav` (`clamscan`) + `clamav-freshclam` (`freshclam`) — file RIÊNG
  `package-lists/0635-antivirus.list.chroot` (CHỦ Ý chỉ on-demand, KHÔNG
  `clamav-daemon` — xem VN09-029/030, `docs/specs/PL09-DEFAULT-APPS.md` §6).
- `kup-backup` + `bup` — `package-lists/0620-backup.list.chroot`.
- `pkexec` (gói `policykit-1`) — KHÔNG có dòng khai riêng trong
  package-lists, nhưng ĐÃ được giả định có mặt bởi nhiều call-site `pkexec`
  khác trong repo hiện có (`namios-chan-doan`, `namios-smartai`,
  `namios-pre-update-snapshot.sh`) qua chuỗi phụ thuộc polkit-kde-agent-1 của
  `plasma-workspace` — app này KHÔNG giới thiệu phụ thuộc mới, chỉ dùng lại
  giả định đã có. **Nếu DEV muốn chắc chắn hơn**, có thể khai tường minh
  `policykit-1` ở một package-list hiện có (vd `0630-security.list.chroot`)
  — việc đó KHÔNG làm trong đợt này (ngoài phạm vi "chỉ file namios_antoan").
- `python3-pyside6.qtwidgets` — đã có sẵn cho `namios_assistant`/
  `namios_welcome` (`0110-desktop-familiar.list.chroot`), app này TÁI DÙNG.

**Kết luận cho DEV:** không cần sửa package-list nào cho SEC-1 chạy đúng,
NHƯNG nếu muốn tăng độ tin cậy của `pkexec`, xem xét khai `policykit-1` tường
minh (hiện chỉ "chắc có" qua Depends chain, chưa "đã xác nhận" theo đúng quy
ước `apt-cache show` của repo này).

## 6. Đã chạy thật — lớp lõi không-GUI (sandbox hiện tại, KHÔNG có PySide6)

Đã `python3 -m py_compile` toàn bộ 7 file `.py` mới — PASS. Đã `bash -n` hook
`0309-namios-antoan.hook.chroot` — PASS.

Đã import + chạy thật `namios_antoan.probes`/`namios_antoan.actions` trong
một bản sao cách ly có `namios_core`/`namios_security`/`namios_i18n` (copy từ
chính repo, mô phỏng đúng `PYTHONPATH=/opt/namios` lúc chạy trong ảnh thật):

- Cả 5 `probe_*` chạy không raise trên máy sandbox (không có ufw/apparmor/
  clamav/kup-backup cài) → đúng nhánh `installed=False` + `install_hint` cho
  cả 4 thẻ (tường lửa/AppArmor/virus/sao lưu), và thẻ Cập nhật đọc đúng số gói
  chờ cập nhật thật (0, vì sandbox đã cập nhật) qua `apt list --upgradable`
  thật.
- Mọi `actions.*` không-privileged (`open_update_center`,
  `open_backup_settings`) trả `success=False` kèm thông báo rõ khi không tìm
  thấy Discover/kcmshell6 (đúng, sandbox không có KDE) — KHÔNG raise.
- Dựng một bản giả lập `pkexec` (exec thẳng argv còn lại, mô phỏng "người
  dùng đã cấp quyền") + một bản giả lập `ufw` ghi log lời gọi — xác nhận
  `actions.enable_firewall()` gọi đúng `pkexec ufw --force enable` và
  `actions.view_firewall_detail()` gọi đúng `pkexec ufw status verbose`,
  `ArgvSafeExec` xác nhận đúng `argv[0]` tuyệt đối/tồn tại/thực thi được cho
  cả `pkexec` và lệnh đích, kết quả `ActionResult(success=True, message=...)`
  chứa đúng output của lệnh giả lập.

**CHƯA xác nhận trên desktop thật:** cửa sổ PySide6 có mở đúng không, 5 thẻ
có vẽ đúng layout/màu trạng thái không, hộp thoại polkit thật có hiện đúng
khi bấm "Bật tường lửa"/"Xem chi tiết"/"Cập nhật chữ ký" không, `clamscan`
thật quét một thư mục thật có trả kết quả đúng không, `QFileDialog` có mở
đúng không. Tất cả cần build ISO (`lb build`) + boot máy/VM thật có KDE
Plasma + ufw/apparmor/clamav/kup-backup đã cài.

## 7. Checklist kiểm thử bắt buộc trên máy/VM thật (boot-test)

1. Mở "Trung tâm An toàn" từ menu KDE (namios-antoan.desktop) — cửa sổ mở
   đúng, 5 thẻ tự kiểm tra khi mở (không cần bấm gì), không treo UI.
2. Trên máy CHƯA cài ufw/apparmor/clamav/kup-backup: xác nhận cả 4 thẻ hiện
   "CHƯA CÀI" + đúng lệnh cài, KHÔNG có dấu tích xanh nào.
3. Cài đủ 4 gói trên, khởi động lại dịch vụ liên quan, mở lại app — xác nhận
   thẻ Tường lửa/AppArmor đổi đúng theo trạng thái thật (`systemctl status
   ufw.service`/`aa-enabled` đối chiếu tay).
4. Bấm "Bật tường lửa" khi đang tắt — hộp thoại polkit hiện, nhập đúng mật
   khẩu → tường lửa bật thật (đối chiếu `ufw status` chạy tay bằng sudo); bấm
   "Huỷ" ở polkit → app báo "đã từ chối cấp quyền", không đổi gì.
5. Bấm "Xem chi tiết luật"/"Xem chi tiết hồ sơ" — hộp thoại polkit hiện, sau
   khi cấp quyền thấy đúng output `ufw status verbose`/`aa-status` thật.
6. Bấm "Quét thư mục này", chọn một thư mục nhỏ có vài file — `clamscan` chạy
   thật (KHÔNG hỏi mật khẩu), kết quả hiện đúng summary; thử một thư mục có
   file test-virus EICAR để xác nhận nhánh "PHÁT HIỆN" hiển thị đúng.
7. Bấm "Cập nhật chữ ký" — polkit hiện, `freshclam` chạy thật (cần mạng), tuổi
   chữ ký ở thẻ Quét virus cập nhật lại sau khi Làm mới.
8. Bấm "Mở Trung tâm cập nhật"/"Mở cài đặt Sao lưu" — đúng Discover/KCM Kup
   mở lên, không lỗi.
9. Bấm "Giới thiệu" — đọc lại đúng 7 điều không-overclaim, xác nhận không có
   chữ nào kiểu "an toàn tuyệt đối"/"chặn 100%" ở BẤT KỲ đâu trong app.
10. Đổi `NAMIOS_LANG=en`, mở lại app — toàn bộ chrome UI + "Giới thiệu" hiện
    đúng tiếng Anh.

## 8. Tuân thủ CLAUDE.md / an toàn

- Không `curl|bash`, không `eval`, không `shell=True`, không nối chuỗi vào
  lệnh thực thi — mọi lệnh con là `list[str]` tĩnh qua `namios_security.
  run_argv` (probes/hành động cần output) hoặc `subprocess.Popen` argv-only
  fire-and-forget (mở app khác, không cần output).
- Hành động cần quyền quản trị LUÔN qua `pkexec` — KHÔNG `sudo` âm thầm,
  KHÔNG lưu mật khẩu, KHÔNG tự cấp quyền.
- Fail-safe tuyệt đối: thiếu PySide6 → wrapper báo lỗi rõ rồi exit 1 (KHÔNG
  treo im lặng); thiếu bất kỳ công cụ nền nào → `installed=False` +
  `install_hint`, không raise; mọi exception không lường được trong luồng
  `QThread` bị bắt thành thông báo lỗi hiển thị, không làm sập cửa sổ.
- KHÔNG overclaim: không có chuỗi nào trong code/i18n nói "an toàn tuyệt
  đối"/"chặn 100% mã độc"/"đã bảo vệ hoàn toàn" — xem `_i18n.py` mục
  "Tuyên bố giới hạn trung thực" (7 điều, VI+EN), và mọi `headline`/`detail`
  trong `probes.py` chỉ mô tả ĐÚNG trạng thái đọc được, không suy diễn thêm.
