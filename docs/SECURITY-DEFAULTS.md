# Bảo mật mặc định — NaMiOS (U13-07)

**Năng lực:** U13-07 "Bảo mật mặc định" (P0) — xem bảng §2 và cổng phát hành
§6 trong
`docs/spec-package/NaMiOS_Phu_luc_13_Uu_tien_Nang_cap_va_Cong_Phat_hanh.md`.

**Trạng thái thật:** `specified`. Đã thêm cấu hình/mã nguồn vào repo (file
liệt kê dưới đây), **CHƯA** build ISO (`lb build`) và **CHƯA** boot trên máy
ảo/máy thật để xác nhận hành vi lúc chạy — theo đúng quy tắc chấm trạng thái
của Phụ lục 13 (§5): *"Nếu không có artifact chạy trên máy thật, trạng thái
vẫn là `specified`, không phải `completed`."* Trạng thái cũ trong
`docs/STATUS-U13-KIEM-KE.md` (dòng U13-07: "Firewall, sandbox/portal
(Flatpak), Security Center, scanner — chưa cấu hình/kiểm") đã lỗi thời sau
đợt này về phần **cấu hình**; người giữ file đó cần tự cập nhật — tài liệu
này không sửa trực tiếp `STATUS-U13-KIEM-KE.md`.

## 1. Câu nói trung thực với người dùng (bắt buộc, không đổi nghĩa)

> NaMiOS bật sẵn tường lửa, giới hạn quyền ứng dụng (AppArmor), chỉ cập nhật
> **bản vá an toàn** tự động, và có Trung tâm An toàn để bạn tự kiểm tra.
> **NaMiOS KHÔNG hứa chống được 100% virus/mã độc.** Hãy cẩn trọng khi mở
> file tải về, cắm USB lạ, hoặc chạy ứng dụng Windows qua Wine — những
> nguồn này có thể mang mã không an toàn mà không công cụ nào chặn được
> tuyệt đối.

Câu này in nguyên văn (ngắn hơn, trong hộp thoại) ở
`/usr/local/bin/namios-security-center` — xem §3.

**Cửa kiểm chứng của U13-07** (trích §2): *"File tải/USB/app Wine thử vượt
quyền bị xử lý; không hứa chống 100% virus."* Đợt này mới dừng ở việc BẬT
đúng các lớp phòng thủ mặc định (firewall/AppArmor/sandbox/update); phần
**"thử vượt quyền" có bị xử lý thật không** cần một bài test đối kháng
riêng trên máy thật (xem §5 "Việc CHƯA làm" dưới đây) — không coi việc ghi
cấu hình này là đã qua cửa kiểm chứng.

## 2. Các lớp phòng thủ đã cấu hình trong đợt này

| Lớp | File | Nội dung |
| --- | --- | --- |
| Gói phần mềm | `distro/live-build/config/package-lists/0630-security.list.chroot` + `0635-antivirus.list.chroot` | `ufw`, `apparmor` + `apparmor-profiles` + `apparmor-utils`, `flatpak`, `xdg-desktop-portal` + `xdg-desktop-portal-kde` (0630); `clamav` + `clamav-freshclam` on-demand (0635, VN09-029 — xem §4, ĐÃ CHUYỂN từ dạng comment sang cài thật) |
| Firewall | `.../hooks/normal/0630-security-default.hook.chroot` phần (a) | Ghi `DEFAULT_INPUT_POLICY="DROP"` / `DEFAULT_OUTPUT_POLICY="ACCEPT"` / `DEFAULT_FORWARD_POLICY="DROP"` vào `/etc/default/ufw`, `ENABLED=yes` vào `/etc/ufw/ufw.conf`, enable `ufw.service` qua symlink. **KHÔNG** chạy `ufw` sống trong chroot. |
| Giới hạn quyền ứng dụng | `.../hooks/normal/0630-security-default.hook.chroot` phần (b) | Enable `apparmor.service` qua symlink. **Cần việc riêng ở §3** để thật sự enforce lúc boot. |
| Sandbox/portal | `.../hooks/normal/0630-security-default.hook.chroot` phần (c) | Cài `/usr/local/bin/namios-flatpak-setup.sh` + unit `namios-flatpak-setup.service` (oneshot, chạy ở **first boot thật trên máy đích**, không chạy lúc build) để `flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo`. Có stamp file `/var/lib/namios/flatpak-flathub.done` để không chạy lại; luôn `exit 0` nên không chặn boot khi offline. |
| Security Center | `.../hooks/normal/0630-security-default.hook.chroot` phần (d) | `/usr/local/bin/namios-security-center` (chmod 0755, kdialog→zenity→text fallback) hiện trạng thái firewall/cập nhật-tự-động/AppArmor/**ClamAV (đã cài? tuổi chữ ký? on-access?)** + câu trung thực §1; launcher `/usr/share/applications/namios-security-center.desktop` ("Trung tâm An toàn"). Phần ClamAV mới thêm ở đợt Phụ lục 09 VN09-029/030 — xem `docs/specs/PL09-DEFAULT-APPS.md` §6. |
| Browser patch | *(đã có từ trước, không trùng lặp ở đợt này)* | `.../hooks/normal/0600-security-updates.hook.chroot` bật `unattended-upgrades` **chỉ pocket `${distro_codename}-security`**, không auto-reboot — bao gồm cả bản vá Firefox ESR (gói `firefox-esr` trong `0400-office-browser.list.chroot`). |
| Signed updates | *(đã có sẵn ở tầng apt, không phải việc mới)* | apt trixie mặc định xác minh chữ ký Release qua `Release.gpg`/InRelease trước khi cài gói — không có việc nào mới phải làm cho phần này ở đợt U13-07 này. |
| User permissions | *(đã có sẵn ở tầng hệ thống, không phải việc mới)* | Live-config/KDE tạo user thường không phải root theo mặc định Debian; chưa có audit riêng về polkit/sudoers trong đợt này (xem `docs/SECURITY.md` §3 SEC-001 — phần đó do `namios_helper` Python xử lý, nằm ngoài phạm vi 3 file live-build/docs của đợt này). |

## 3. Việc BẮT BUỘC người tích hợp build phải tự làm thêm (không nằm trong 3 file ở trên)

**Kernel cmdline cho AppArmor.** AppArmor chỉ thật sự enforce lúc chạy khi
kernel nhận tham số `apparmor=1 security=apparmor`. Hook 0630 chỉ enable
`apparmor.service` qua symlink — service có thể lên nhưng LSM không chặn gì
nếu thiếu tham số kernel này. Cần sửa
`distro/live-build/auto/config` (dòng `--bootappend-live`, hiện là
`"boot=live components locales=vi_VN.UTF-8 timezone=Asia/Ho_Chi_Minh"`)
thành dạng có thêm `apparmor=1 security=apparmor`, ví dụ:

```sh
--bootappend-live "boot=live components locales=vi_VN.UTF-8 timezone=Asia/Ho_Chi_Minh apparmor=1 security=apparmor"
```

Việc này **không** được làm trong đợt này theo đúng phạm vi giao (chỉ 3 file
package-list/hook/doc kể trên) — ghi lại ở đây để người tích hợp build (và
cho người cài lên đĩa cứng thật, nếu dùng bootloader/initrd riêng ngoài ISO
live) tự thêm và tự kiểm bằng `aa-enabled`/`aa-status` sau khi boot thật.

## 4. Scanner bổ trợ (ClamAV) — ĐÃ BẬT on-demand, on-access vẫn TẮT có chủ ý

**Cập nhật 10/11/2026 (Phụ lục 09, VN09-029/030):** quyết định đã CHỐT —
`clamav` + `clamav-freshclam` được cài THẬT (không còn ở dạng comment) qua
file RIÊNG `distro/live-build/config/package-lists/0635-antivirus.list.
chroot` (tách khỏi `0630-security.list.chroot` để không lẫn với nhóm
firewall/AppArmor/sandbox). Lý do tách + chi tiết đầy đủ xem
`docs/specs/PL09-DEFAULT-APPS.md` §6; tóm tắt:

- **CÓ**: `clamav` (lệnh `clamscan`, quét THEO YÊU CẦU/on-demand) +
  `clamav-freshclam` (cập nhật chữ ký, tự có systemd timer theo mặc định
  gói Debian — không phải cấu hình NaMiOS tự viết).
- **KHÔNG CÓ**: `clamav-daemon` (clamd — quét THƯỜNG TRÚ/on-access). Lý do:
  on-access có rủi ro thật về tốn CPU/IO và deadlock khi chưa benchmark trên
  phần cứng mục tiêu (VN09-029); vì repo build với
  `--no-install-recommends`, package này cũng không lọt vào ảnh qua
  Recommends của `clamav`. Quyết định bật on-access là MỘT THAY ĐỔI RIÊNG
  (thêm gói + hook enable có điều kiện) sau khi có số đo benchmark thật —
  KHÔNG làm ở đợt này.
- Security Center (`namios-security-center`, phần (d) của hook 0630) đã
  được MỞ RỘNG để hiện trạng thái ClamAV THẬT (đã cài?/tuổi chữ ký?/
  on-access bật-tắt?) — không chỉ nói chung "có bảo mật".

## 5. Việc CHƯA làm — cần build + boot thật (ngoài phạm vi đợt này)

- **Build ISO thật** (`lb build`) để xác nhận `apt-cache show` công nhận cả
  9 tên gói trong `0630-security.list.chroot` trên mirror trixie thật (CI
  `ci-build.sh` có bước pre-validate tự drop gói sai tên và ghi log —
  KHÔNG coi "file đã viết" là "gói đã xác nhận tồn tại trên trixie"). Gói
  cần `apt-cache show` xác nhận: `ufw`, `apparmor`, `apparmor-profiles`,
  `apparmor-utils`, `flatpak`, `xdg-desktop-portal`,
  `xdg-desktop-portal-kde` (và `clamav`/`clamav-freshclam` nếu sau này bật).
- **Boot thật trên máy pilot** để chạy: `systemctl status ufw.service`
  (phải active), người dùng tự `ufw enable` lần đầu rồi `ufw status verbose`
  phải in `deny (incoming), allow (outgoing)`; `aa-status`/`aa-enabled` phải
  báo "Yes" SAU KHI đã thêm tham số kernel ở §3; `systemctl status
  namios-flatpak-setup.service` không "failed" cả khi có và khi không có
  mạng; mở "Trung tâm An toàn" từ menu KDE phải hiện đúng 3 trạng thái +
  câu trung thực.
- **Bài test đối kháng cho đúng câu cổng phát hành** ("File tải/USB/app Wine
  thử vượt quyền bị xử lý"): thử một file tải về/USB gắn ngoài/app Wine cố
  ghi ra ngoài phạm vi cho phép (home của user khác, `/etc`, thiết bị khác)
  và xác nhận AppArmor/sandbox portal thật sự chặn — đợt này chỉa BẬT hạ
  tầng (service + gói), CHƯA viết profile AppArmor cụ thể cho app/Wine
  (việc đó thuộc U13-10 "Wine capsule có kiểm soát", xem Phụ lục 13 bảng
  §2) và chưa có bằng chứng chặn thật.
- Audit polkit/sudoers/quyền user thường cho phần "quyền người dùng" nói
  trong đầu ra U13-07 (nằm ở tầng `namios_helper`/`namios_core`, xem
  `docs/SECURITY.md` §3 SEC-001 — SEC-003/004/005 cũng đang ghi
  "BLOCKED M2 — chưa hiện thực" ở đó, khớp với ghi nhận "chưa kiểm" ở đợt
  này).

## 6. Không hứa quá — nhắc lại

Không ghi/nói ở bất kỳ nơi nào (code, UI, tài liệu marketing) rằng NaMiOS
"chống được mọi virus/mã độc" hoặc "an toàn tuyệt đối". Mọi thông báo chỉ
được nói đã làm gì (tường lửa mặc định, AppArmor, cập nhật bảo mật tự động,
Trung tâm An toàn) và nhắc người dùng tự cẩn trọng với file tải về, USB lạ,
app Wine — đúng tinh thần §6 Phụ lục 13: *"Không mở rộng marketing trước
bằng chứng."*
