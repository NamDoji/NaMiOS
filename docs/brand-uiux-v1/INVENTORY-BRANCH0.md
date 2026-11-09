# NaMiOS — Kiểm kê hiện trạng (BRANCH 0)

**Ngày:** 09/11/2026
**Phạm vi:** Bước 0 của `docs/brand-uiux-v1/04_PROMPT_CLAUDE_CODE.md` — kiểm kê thực tế stack trước khi làm BRANCH A (design system).
**Nguyên tắc trung thực:** `implemented` = có mã/cấu hình trong repo chạy/validate được ở môi trường dev; `partial` = có khung nhưng chưa đủ/chưa nối; `absent` = chưa có. **`tested`: KHÔNG hạng mục nào được kiểm thử trên MÁY THẬT.** Mọi gói/hook ghi `verified_on_host: NO` — tên gói + cú pháp chưa xác nhận trên build host Debian 13 trixie thật, chưa qua `lb build` + boot máy thật. Không có module giả.

## Cây repo (gọn)

```
branding/            tài sản nhận diện: logo-sen-viet-v2, icons-system-v1 (24 SVG), style/, wallpaper/, design-system/ (MỚI — BRANCH A)
distro/live-build/   cấu hình Debian live-build: package-lists/, hooks/, includes.chroot/ (script + plasmoid + config)
docs/                spec-package (Phụ lục), adr/ (0001–0015 + 0016 MỚI), brand-uiux-v1/, design/, support/
src/                 ~25 gói Python: namios_smartai, namios_doctor, namios_core, namios_welcome, namios_security, ...
tests/               unit/integration/system/security/qa (chạy ở dev, không phải máy thật)
catalog/ contracts/ fixtures/ qa/   danh mục thiết bị/compat, hợp đồng sự kiện, dữ liệu mô phỏng
```

## Bảng kiểm kê

| # | Hạng mục | Stack dự kiến | Trạng thái | Kiểm thử máy thật |
|---|----------|---------------|-----------|-------------------|
| 1 | Distro nền | Debian 13 **trixie** | partial | ❌ chưa |
| 2 | Desktop shell/toolkit | KDE **Plasma 6 / Qt6 / QML** (+ Kirigami) | partial | ❌ chưa |
| 3 | Mạng | **NetworkManager** (+ plasma-nm) | partial | ❌ chưa |
| 4 | In / quét | **CUPS / SANE** (+ IPP/eSCL driverless) | partial | ❌ chưa |
| 5 | Bluetooth | **BlueZ / Bluedevil** | partial | ❌ chưa |
| 6 | Cập nhật | **Discover / PackageKit** + unattended-upgrades (+ Timeshift) | partial | ❌ chưa |
| 7 | Bộ gõ (IME) | **fcitx5** (+ Unikey Telex/VNI) | partial | ❌ chưa |
| 8 | Logger / chẩn đoán | **journald** + `namios-chan-doan` | implemented (dev) | ❌ chưa |
| 9 | AI | **namios-smartai** (rule-based + seam LLM) | partial | ❌ chưa |
| A | Design system | tokens + component preview (BRANCH A) | implemented (dev) | ❌ chưa |

## Chi tiết + bằng chứng

### 1. Distro nền — Debian 13 trixie — `partial`
- `distro/live-build/build-manifest.yaml:38` → `release_codename: "trixie"`; dòng 42: `point_release: "TBD (đọc /etc/debian_version trong chroot)"`.
- `distro/live-build/ci-build.sh:8` → `NAMIOS_LB_DISTRIBUTION="${NAMIOS_LB_DISTRIBUTION:-trixie}"`; có bước pre-validate drop gói không có trong trixie (ghi log `DROPPED-NOT-IN-TRIXIE`).
- ADR: `docs/adr/0002-nen-debian-13.md`.
- **Chưa test:** chưa chạy `lb build` sinh ISO xác nhận; point-release chưa chốt. Theo bộ nhớ dự án đã từng boot tới Plasma trong QEMU (headless), **không phải máy thật**.

### 2. Desktop shell/toolkit — KDE Plasma 6 / Qt6 / QML / Kirigami — `partial`
- `distro/live-build/config/package-lists/0100-desktop-kde.list.chroot`: `task-kde-desktop`, `kwin-x11`, `sddm` + `sddm-theme-breeze`, `dolphin`, `konsole`, `kate`, `plasma-discover`, `plasma-nm`, `plasma-pa`, `kscreen`, `ark`, `okular`, `kde-spectacle`, `libgl1-mesa-dri`, `plasma-workspace-wallpapers`.
- **Component QML thật đã có (quan trọng cho ADR-0016):** `distro/.../usr/share/plasma/plasmoids/org.namios.smartai/contents/ui/main.qml` (widget “Hỏi SmartAI”) và `org.namios.workgroups/.../main.qml` (widget “nhóm việc”) — xác nhận toolkit thực tế là **QML/Plasma**.
- Nhận diện Plasma: `usr/share/color-schemes/NaMiOS.colors` (nhấn đỏ son #C93643, foreground đỏ đài #92212E), hook theme kính mờ + Aurorae (commit `dfbbf3c`, `64a6ade`).
- **Honest:** `kwin-x11` ép rõ (phiên X11), **Kirigami KHÔNG được khai tường minh** trong package-list (đi kèm qua phụ thuộc Plasma/`kirigami2`); cần xác nhận khi dựng component QML thật. `verified_on_host: NO`. Boot/hiển thị chỉ kiểm được khi boot Plasma thật.

### 3. Mạng — NetworkManager — `partial`
- `0160-network.list.chroot`: `network-manager`, `wpasupplicant`, `iw`, `modemmanager`, `cifs-utils`, `smbclient`, `kio-extras`; GUI qua `plasma-nm` (ở list 0100).
- Chẩn đoán dùng `nmcli`/`ip` trong `namios-chan-doan` (mã `NM-NET-*`) và playbook mạng trong `namios-smartai` (C1 mất mạng / C2 không ra Internet / C3 mất sau sleep).
- Catalog lỗi `NET-001..005` ở spec 03 §6.2. **Chưa test** adapter thật.

### 4. In / quét — CUPS / SANE — `partial`
- `0500-print.list.chroot`: `cups`, `cups-filters`, `print-manager`, `printer-driver-all`; driverless: `avahi-daemon`, `libnss-mdns`, `ipp-usb`, `sane-airscan`, `sane-utils`, `skanlite`.
- Ma trận driver per-model + in thử thuộc **M4 (DEV-*)**, **chưa làm**. Catalog `PRN-001..004`, `SCAN-001` ở spec 03 §6.1. **Chưa test** máy in/MFP thật.

### 5. Bluetooth — BlueZ / Bluedevil — `partial`
- `0180-bluetooth-power-time.list.chroot`: `bluez`, `bluedevil`.
- Catalog `BT-001..004` (discover/pair/profile/service) ở spec 03 §6.3. **Chưa test** tai nghe/chuột thật.

### 6. Cập nhật — Discover / PackageKit + unattended-upgrades — `partial`
- Backend GUI: `plasma-discover` + `packagekit` + `appstream` (list 0100).
- Tự động bản vá bảo mật: `unattended-upgrades` (list `0180-...`); hook `0600-security-updates.hook.chroot` + `0630-security-default.hook.chroot`. **Chưa có hook riêng tên “unattended-upgrades”** — cấu hình nằm trong hook bảo mật (cần xác nhận apt `50unattended-upgrades` khi build thật).
- Khôi phục: `0640-update-recovery.list.chroot` → `timeshift` (chế độ rsync vì ext4, **không phải A/B nguyên tử** — ADR-0014), `needrestart`. **Chưa test** luồng update→rollback thật.

### 7. Bộ gõ (IME) — fcitx5 — `partial`
- Gói `fcitx5` ở `0200-locale-vi.list.chroot`; hook `0200-fcitx5-default-im.hook.chroot` (đặt fcitx5 mặc định qua `im-config`); `/etc/skel/.config/fcitx5/profile` + `conf/unikey.conf` (khung Unikey **Telex**); `/etc/environment.d/90-namios-im.conf`.
- **Honest (ghi rõ trong hook):** “nội dung file `profile` là khung theo tài liệu upstream, CHƯA xác nhận cú pháp trên gói fcitx5 Debian 13 thật” → **phải test gõ Telex/VNI trong Qt/GTK/trình duyệt/Wine (VN-002)** trước khi coi là đạt. **Chưa test.**

### 8. Logger / chẩn đoán — journald + namios-chan-doan — `implemented (dev)`
- `distro/.../usr/local/bin/namios-chan-doan`: 3 màn hình (Mạng `NM-NET-*`, Phần cứng/driver `NM-DRV/DSK-*`, Quyền/ứng dụng `NM-PERM/APP-*`); đọc `journalctl -p err -b` (dòng 231–234) + `coredumpctl list` (dòng 216–218, cần `systemd-coredump` ở `0650-diagnostics.list.chroot`); có nhánh khi lệnh thiếu/bị `kernel.dmesg_restrict` → báo “không xác định”, không suy diễn.
- An toàn: argv tĩnh, không `eval`/`curl|bash`, luôn `exit 0`; che bí mật khi “Xuất log”. Nguồn nghĩa mã: `docs/support/error-codes.md`.
- **Honest:** mới review bằng `bash -n` + đọc lại (`verified_on_host: NO`); chưa xác nhận định dạng `lspci/dmesg/journalctl` trên trixie thật.

### 9. AI — namios-smartai — `partial`
- **CLI nền:** `distro/.../usr/local/bin/namios-smartai` — kênh mà widget desktop khởi chạy; chạy **OFFLINE**, rule-based playbook tất định (mạng C1–C3, in C4–C6, IME…); guardrail mã hoá cứng: không nới chính sách bảo mật, không là điều kiện boot, không tự xác nhận app “chạy được”; chỉ argv tĩnh; `exit 0`. Có LLM/engine thì **chỉ ghi nhận để hiển thị** (`NAMIOS_SMARTAI_API_KEY`/`NAMIOS_SMARTAI_LLM`), playbook vẫn chạy khi thiếu (dòng 119–136, 168).
- **Widget QML:** `org.namios.smartai` (main.qml).
- **Gói Python** `src/namios_smartai/` (orchestrator/planner/policy/redaction/intent/triage…): model ngôn ngữ **chỉ xuất hiện ở bước `intent`** như một **SEAM** — `FakeModelProvider` tất định dựa từ khoá (`intent.py`), `allow_external_model=False` mặc định (`_types.py:593`); orchestrator/diagnose là mã tất định, không gọi model. Có unit test ở `tests/` (chạy dev).
- **Honest:** AI hiện là **chẩn đoán rule-based + seam LLM chưa nối model thật**; chưa đánh giá 30 ca gắn nhãn; chưa test máy thật.

### A. Design system (BRANCH A — tạo trong lượt này) — `implemented (dev)`
- `branding/design-system/tokens.json` — nguồn sự thật token (màu Sen Việt ngà ấm, đã **đo** tương phản WCAG; typography Noto Sans + fallback DejaVu có dấu; spacing/radius/control/motion + cờ reduced-motion; sáng/tối; focus ring).
- `branding/design-system/components.css` + `components-preview.html` — preview 12 component (Button, Field, Select, Checkbox, Dialog, Toast, Progress, DeviceCard, ConnectionStepper, ErrorCard, AIPlanCard) ở cả sáng/tối, focus, disabled/loading/error, tôn trọng `prefers-reduced-motion`, nhãn tiếng Việt, mở được ở mọi trình duyệt.
- ADR: `docs/adr/ADR-0016-design-system-integration.md`.
- **Honest:** đây là **lớp token + preview web**, CHƯA nối vào desktop KDE/Qt thật. Màu đã đo WCAG nhưng **chưa test hiển thị trên màn hình thật** (1366×768 / 1920×1080 / 2560×1440 @ 100/125/150/200%), chưa test người dùng.

## Lưu ý nguồn sự thật màu (cần hợp nhất)
Tồn tại **hai** bộ token:
- `design/tokens.json` (bộ **PL12**): nền **navy** `#0a1322`, brand **ruby** `#a21f46`.
- `branding/design-system/tokens.json` (bộ **Sen Việt v1.0** — mới, theo spec 03): nền **NGÀ ấm** `#F5F2EB`/gradient `#FBF8F2→#EFE3D1`, nhấn **đỏ son** `#C93643`, vàng `#F2C66D`, mực `#182E3B`. Khớp với `usr/share/color-schemes/NaMiOS.colors`.

→ Bộ Sen Việt là nhận diện đã chốt 09/11/2026. Nhóm thiết kế cần **hợp nhất, tránh 2 nguồn lệch** ở lần cập nhật `docs/design/DESIGN-SYSTEM.md` kế tiếp (đã ghi trong `$meta.supersedes_note` của token mới).

## Blocker để vượt BRANCH 0/A sang thực tế
1. Build host Debian 13 trixie thật + `apt-cache show` xác nhận mọi tên gói (`verified_on_host: NO` hiện diện khắp các list).
2. `lb build` ra ISO + boot **máy thật** (Plasma, SDDM, fcitx5, NM, CUPS, BlueZ) — hiện mới có bằng chứng QEMU headless.
3. Dựng component QML/Kirigami thật từ token (ADR-0016) + test visual đa độ phân giải/scaling + bàn phím/screen reader/giảm chuyển động.
4. Máy thật theo khảo sát: ≥3 adapter Wi‑Fi, 3 máy in/MFP, 2 thiết bị Bluetooth; nếu không có → ghi `not tested`.
