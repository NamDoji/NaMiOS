# NaMi 2026.11 "Đông Sơn" — RELEASE-READINESS (Go / No-Go)

> **Loại tài liệu:** đánh giá sẵn-sàng-phát-hành của **release manager**, brutally honest.
> **Ngày:** 2026-11-11 · **Repo HEAD:** `ff7928d` (branch `main`).
> **Phạm vi file:** CHỈ viết tài liệu này. READ-ONLY cho mọi file khác. Không sửa config/app.
> Không `git commit`/push. Mọi "hiện trạng" lấy từ **bằng chứng repo** (file + khoá đã đọc),
> KHÔNG từ quan sát boot. **`verified_on_host: NO` cho toàn bộ hệ thống.**
>
> Nguồn nghiệm thu: `docs/design/hig/NaMi-Human-Interface-2026.md` (§12/§13 + điều kiện dừng),
> `docs/design/prototype-luxury-dongson/docs/CLAUDE_CODE_HANDOFF.md` ("Điều kiện dừng phát
> hành"), `docs/design/HIG-ADOPTION-VERDICT.md`, `docs/design/P0-UI-AUDIT.md`,
> `docs/design/WINDOWS11-PARITY.md`, + sweep repo (packages / hooks / assets / version / secret
> / license / honesty / a11y).

---

## 0. VERDICT (3 dòng)

1. **NO-GO cho "phát hành chính thức công khai".** Trạng thái hiện tại là **ALPHA**,
   `verified_on_host: NO` ở MỌI nơi — chưa có ISO nào được build + boot + **cài + nâng cấp +
   rollback trên phần cứng thật**, và nhiều **điều kiện dừng-phát-hành** (nhãn hiệu, giấy phép
   hình nền, rò rỉ bảo mật live→installed) **chưa được giải quyết**.
2. **GO (có điều kiện) cho phát hành NỘI BỘ/ALPHA thử nghiệm** — sau khi xong danh mục
   **CODE-FIXABLE-NOW** bên dưới (đặc biệt **C1 rò bảo mật**, **C2 ship TBD**, **C3 build dễ vỡ**,
   **C4 logo sen cũ**) và dán nhãn rõ "bản thử nghiệm, chưa chứng nhận".
3. **Không thể CHỨNG NHẬN "official public release"** cho tới khi: (a) có **1 lượt
   boot+cài+nâng-cấp+rollback thật trên phần cứng** với bằng chứng (`verified_on_host: YES`),
   **và** (b) **mọi điều kiện dừng** (§4) được gỡ — gồm **quyết định của chủ dự án về nhãn
   hiệu/giấy phép** (§3).

---

## 1. CODE-FIXABLE-NOW — tôi sửa ngay (không cần boot-test)

> Xếp hạng theo mức nghiêm trọng. Mỗi mục: **What / Where (file:line) / Fix / Owner**.
> Đây là các việc sửa được **trong mã/cấu hình**, không cần máy thật.

### C1 — [BLOCKER · BẢO MẬT] Workaround "chỉ dành cho Live" RÒ sang máy đã cài
- **What:** Máy người dùng **cài bằng Calamares** bị kế thừa 2 thứ chỉ nên có trên ảnh Live:
  (a) nới lỏng bảo mật X — `Xwrapper.config` `allowed_users=anybody` + `needs_root_rights=yes`;
  (b) ép software-GL toàn hệ → máy có **GPU thật vẫn bị ghim software rendering** (chậm). Hook
  dọn dẹp sau cài **không** gỡ 2 thứ này.
- **Where:**
  - đặt: `distro/live-build/config/hooks/normal/0410-console-startx-x11.hook.chroot:38-41`
    (`allowed_users=anybody`, `needs_root_rights=yes`).
  - đặt: `distro/live-build/config/hooks/normal/0400-qemu-desktop-autologin.hook.chroot:56-75`
    (`/etc/environment` softGL + `/etc/profile.d/namios-softgl.sh`).
  - **thiếu dọn:** `distro/live-build/config/hooks/normal/0420-installed-sddm-restore.hook.chroot`
    (chỉ khôi phục sddm.service/default.target/getty/autologin — KHÔNG đụng `/etc/environment`,
    `namios-softgl.sh`, `Xwrapper.config`).
- **Fix:** mở rộng hook `0420` (chạy trên máy đã cài, gate `boot=live` = false) để: xoá
  `/etc/profile.d/namios-softgl.sh`, gỡ các key softGL khỏi `/etc/environment`, và reset
  `/etc/X11/Xwrapper.config` về mặc định an toàn.
- **Owner:** release manager (tôi).

### C2 — [BLOCKER · BUILD-002] ISO ship kèm metadata `TBD`
- **What:** Ảnh phát hành sẽ chứa build-metadata còn **nguyên chữ "TBD"** (vi phạm quy tắc
  "KHÔNG ship bản có TBD ra ngoài lab"). Không hook/script nào tự đóng dấu ngày build + commit.
- **Where:** `distro/live-build/config/includes.chroot/etc/namios-release:4-5`
  (`NAMIOS_BUILD_DATE_UTC`, `NAMIOS_SOURCE_COMMIT` = `"TBD: ..."`);
  `distro/live-build/build-manifest.yaml` (toàn bộ `TBD`); không có stamping trong
  `distro/live-build/ci-build.sh` hay `config/hooks/` (grep `NAMIOS_BUILD_DATE`/`rev-parse` = rỗng).
- **Fix:** thêm 1 hook chroot/binary (hoặc 1 bước trong `ci-build.sh` TRƯỚC `lb build`) đóng dấu
  `NAMIOS_BUILD_DATE_UTC="$(date -u +%FT%TZ)"` + `NAMIOS_SOURCE_COMMIT="$(git rev-parse HEAD)"`
  vào `/etc/namios-release`; điền `build-manifest.yaml` tương ứng.
- **Owner:** release manager (tôi).

### C3 — [BLOCKER · BUILD DỄ VỠ] `0630` hard-abort cả build vì gói tuỳ chọn
- **What:** Hook bảo mật `exit 1` (giết nguyên `lb build` ~40 phút) nếu thiếu `ufw`/`apparmor`/
  `flatpak`. Kết hợp với **C5** (ci-build.sh âm thầm DROP gói thiếu) → một lần đổi tên gói ở
  trixie là build sập. Trái với quy ước fail-safe của chính dự án (`0620` chỉ cảnh báo).
- **Where:** `distro/live-build/config/hooks/normal/0630-security-default.hook.chroot:71`
  (ufw), `:92` (apparmor), `:114` (flatpak) — cả 3 đều `exit 1`. So sánh:
  `0620-backup-config.hook.chroot:59-61` (chỉ warn khi thiếu `kup-backup`).
- **Fix:** đổi 3 chỗ `exit 1` → cảnh báo + bỏ qua (giữ fail-safe), vẫn ghi log rõ để review.
- **Owner:** release manager (tôi).

### C4 — [BLOCKER · THƯƠNG HIỆU] Hình nền/khoá/greeter mặc định = logo SEN CŨ + chữ "NaMiOS"
- **What:** Ảnh `namios-default.png` là **plate "Sen Việt" v2** (hoa sen đỏ + wordmark
  **"NaMiOS"** + tagline "Nét sen Việt, mở tương lai.") — tức bản phát hành tên **"Đông Sơn"**
  lại hiện **logo sen cũ + chữ NaMiOS** ở màn khoá và greeter Live. Đây vừa là brand-drift vừa
  là **rò tên hiển thị "NaMiOS"** (lẽ ra là "NaMi"/trống đồng).
- **Where:** `.../usr/share/backgrounds/namios/namios-default.png` được trỏ bởi 3 bề mặt:
  `.../etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc:144` (desktop),
  `.../etc/xdg/kscreenlockerrc:67` (màn khoá),
  `.../usr/share/sddm/themes/breeze/theme.conf.user:58` (greeter Breeze — Live ép dùng Breeze
  qua hook `0400`). (Theme SDDM `namios`, Plymouth, Plasma splash, icon `namios`/
  `start-here-namios` ĐÃ là trống đồng Đông Sơn — chỉ còn file này sót lại.)
- **Fix:** tái sinh `namios-default.png` theo nhận diện Đông Sơn (navy/gold, không wordmark
  "NaMiOS"), **hoặc** trỏ 3 khoá trên sang 1 wallpaper v3 đã được duyệt (ví dụ gói procedural
  `NaMiOS-23-Trong-Dong-Tia-Nang`/`NaMiOS-25-Sen-Dem-Dang-Nhap`). *(Lưu ý phối hợp với D3:
  không trỏ sang ảnh AI chưa cấp phép.)*
- **Owner:** release manager (tôi) + xác nhận thiết kế của chủ dự án.

### C5 — [CAO · BUILD IM LẶNG DEGRADE] `ci-build.sh` âm thầm DROP gói không có trong trixie
- **What:** Trước `lb build`, script thay mọi gói không tìm thấy bằng comment
  `# DROPPED-NOT-IN-TRIXIE` và **vẫn build xanh**. Một gói quan trọng bị gõ sai/đổi tên sẽ
  **biến mất khỏi ảnh mà build không báo lỗi** → ảnh thiếu chức năng nhưng "CI xanh".
- **Where:** `distro/live-build/ci-build.sh` (vòng lặp pre-validate, ~dòng 44-56:
  `printf '# DROPPED-NOT-IN-TRIXIE: %s\n'`).
- **Fix (phần code được):** thêm 1 **allowlist "must-have"** (ví dụ: `sddm`, `plasma-desktop`,
  `calamares`, `systemsettings`, `fonts-noto-core`, `fcitx5`, `libreoffice`, `firefox-esr`,
  `grub-pc`, `plymouth`) và **fail build** nếu bất kỳ gói must-have nào bị DROP. *(Việc xác minh
  từng tên gói low-confidence có thật trong snapshot = thuộc bucket NEEDS-BOOT-TEST, cần build
  host.)*
- **Owner:** release manager (tôi).
- **Liên quan (từ audit package-list, cần xác nhận tại build host):** 3 tên low-confidence —
  `sddm-theme-breeze` (`0100-desktop-kde.list.chroot:25`), `libreoffice-help-vi` /
  `firefox-esr-l10n-vi` (`0400-office-browser.list.chroot`). Archive-areas ĐÃ đủ:
  `distro/live-build/auto/config:67` = `main contrib non-free non-free-firmware` (bao winetricks
  [contrib], libfdk-aac2t64 [non-free], firmware-* [non-free-firmware]) → KHÔNG phải blocker.

### C6 — [TB · THƯƠNG HIỆU] Website công khai + design-system CSS còn màu "Sen Việt" v2
- **What:** Bề mặt phát hành công khai (**website tải về**) dùng 100% bảng màu cũ
  `#C93643`/`#122A3A`/`#F2C66D`/`#92212E`, 0 token Đông Sơn v3.
- **Where:** `website/css/tokens.css:21-22,24,88-89,98-99,120-121` (12 tham chiếu v2, 0 v3);
  `branding/design-system/components.css:28,29,31,45,72,73,82,83,94` (preview, không ship vào
  ISO nhưng là tài sản thương hiệu).
- **Fix:** ánh xạ sang v3 Đông Sơn (navy `#092D4F` / gold `#DEA93E` / vermilion `#D64C3E` /
  ivory `#FFF9EF`), đồng bộ với `design/tokens.json` / `docs/design/nami-tokens.json` (đã v3).
- **Owner:** release manager (tôi).

### C7 — [THẤP · BUILD] Trùng tiền tố số hook `0710`
- **What:** 2 hook cùng số `0710` → log cùng tên `namios-hook 0710`, thứ tự chạy không tất định
  (dù sửa file rời nhau nên không clash chức năng).
- **Where:** `distro/live-build/config/hooks/normal/0710-calamares-branding.hook.chroot` +
  `.../0710-printing-setup.hook.chroot`.
- **Fix:** đổi số `0710-printing-setup` → `0715`/`0720`.
- **Owner:** release manager (tôi).

### C8 — [THẤP · VERSION] `pyproject.toml` còn `0.0.0.dev0`
- **What:** Gói Python helper (ship dưới `/opt/namios/*`) vẫn mang version `0.0.0.dev0` trong khi
  OS là `2026.11`. Đây là chuỗi `0.0.0` **duy nhất** còn sót trong repo.
- **Where:** `pyproject.toml:7` (`version = "0.0.0.dev0"`).
- **Fix:** đặt `2026.11` (hoặc semver thật) cho nhất quán version-string.
- **Owner:** release manager (tôi).

### C9 — [THẤP · VỆ SINH REPO] File rác ở gốc repo + token local
- **What:** 3 file 0-byte untracked `Them` / `cho` / `chon` (do gõ nhầm lệnh shell "Them cho
  chon"). Riêng `.gh-token` (40 byte) ở gốc repo **đã được `.gitignore`** (`.gitignore:10`) +
  **KHÔNG được git theo dõi** + **không nằm trong payload ISO** (live-build chỉ đóng gói
  `includes.chroot/`, không phải gốc repo) → **không phải secret bị commit/ship**; chỉ là vệ sinh
  local.
- **Where:** gốc repo `./Them`, `./cho`, `./chon`, `./.gh-token`.
- **Fix:** xoá 3 file rác; cân nhắc gỡ/đổi `.gh-token` khỏi working tree.
- **Owner:** release manager (tôi).

### C10 — [THẤP · TRUNG THỰC HỒ SƠ] Tài liệu audit nói quá phần việc còn lại
- **What:** Vài tài liệu còn ghi "chưa làm" cho thứ **đã làm xong**, làm sai hồ sơ phát hành:
  SDDM/icon/splash đã là **trống đồng** (không còn SEN), và **`NaMi-HighContrast.colors` đã tồn
  tại** và đo WCAG thật (21:1).
- **Where:** `docs/design/P0-UI-AUDIT.md` (§2.1/§3 "SDDM dùng logo SEN cũ"; §5 R1 "high-contrast
  chưa có .colors"); `.../usr/share/namios/docs/BRAND.md:189-196`;
  `.../usr/share/namios/docs/SPLASH.md:41`.
- **Fix:** cập nhật các câu đã lỗi thời để hồ sơ trung thực (không phải defect ship, nhưng là
  tính trung thực của audit-trail).
- **Owner:** release manager (tôi).

---

## 2. NEEDS-BOOT-TEST — chỉ chủ dự án, trên phần cứng thật, mới clear được

> Không thể xác minh trong container headless. Mỗi dòng cần boot/cài thật + bằng chứng ảnh/video.

1. **Chuỗi boot/login hiển thị thật:** Plymouth → SDDM theme `namios` → Plasma splash → desktop,
   trên **GPU thật và VM** — xác nhận **không màn đen/không treo**.
2. **Aurorae `NaMiOSLotus` nghi treo đăng nhập** (`dfbbf3c`) — hiện đang **comment tắt**, dùng
   Breeze fallback; cần **bisect** tách Aurorae khỏi desktoptheme rồi mới bật
   (`WINDOWS11-PARITY.md §3.2`).
3. **Gõ tiếng Việt** fcitx5 Telex/VNI; không mất dấu trong đường dẫn tệp.
4. **Phím tắt** (Meta+P chuyển màn hình, Meta+các phím), **focus ring** nhìn rõ, **screen reader
   (Orca)**, và **`NaMi-HighContrast.colors`** hiển thị đúng khi bật "Tương phản cao".
5. **Màu Selection đảo chiều** (nền gold + chữ navy) nhìn bằng mắt (`NaMiOS.colors`).
6. **Thiết bị/vòng đời thật:** Wi-Fi / Bluetooth / in trang thử / cập nhật / **rollback** (VM
   snapshot) — không giả "đã khôi phục" (HIG §12.3).
7. **`namios-auto-compositing.sh`** lật Blur/Contrast an toàn trên GPU thật mà KWin không crash.
8. **Cài → nâng cấp → rollback trên phần cứng thật**; đặc biệt **xác nhận C1 đã dọn** softGL +
   `Xwrapper.config` trên máy đã cài (sau khi sửa).
9. **Xác nhận 3 gói low-confidence (C5) có thật trong snapshot trixie** + **review MỌI dòng
   `DROPPED` trong `build.log`**.
10. **Secure Boot** (`shim-signed` hoãn) — pilot cài **BIOS offline**; không hạ bảo mật để thay
    splash (HIG §10.3).
11. **Taskbar/cửa sổ/Dolphin** (căn giữa, nút phải, "Máy này") — kiểm Wayland + X11
    (`WINDOWS11-PARITY.md §9`).

---

## 3. NEEDS-OWNER-DECISION — nhãn hiệu / pháp lý (chỉ chủ dự án quyết)

### D1 — Tên "NaMi" / "NaMiOS" chưa rà soát nhãn hiệu
- `.../usr/share/namios-branding/logo/brand.json:7` = `"trademark review pending"`. Điều kiện
  dừng #1 của HANDOFF ("Chưa rõ quyền dùng tên NaMi/NaMiOS"). Phải có ý kiến pháp lý trước phát
  hành **chính thức/thương mại**. (Lớp l10n đã khoá tên để đổi không cần sửa từng màn.)

### D2 — nWord / nExcel / nPowerPoint / nDraw / nOffice (+ NaMiData/NaMiMath)
- `docs/branding/TRADEMARK-LICENSE-COMPLIANCE.md §1c` **tự flag**: các tên này **cố ý gợi**
  Microsoft **Word® / Excel® / PowerPoint®**, **CHƯA rà soát pháp lý**. Áp qua override tĩnh
  `.desktop` + hook `0450`/`0454`. **Quyết:** giữ (kèm ý kiến luật sư) hay lùi về tên trung tính
  (NaMiWriter/NaMiSheet/…). Rủi ro nhãn hiệu CAO.

### D3 — Giấy phép + nguồn gốc HÌNH NỀN (nghiêm trọng)
- 20 gói hình nền `NaMiOS-01..20` (đặt tên địa danh: Hạ Long, Hội An, Huế, Đà Lạt, Bản Giốc…,
  gồm **`NaMiOS-20-Bien-Dao-Viet-Nam`**) ghi `License` = **"ảnh minh hoạ tạo bằng AI"**, **không
  có rights_evidence**. Trong khi đó `design/wallpaper-manifest.json` có **HARD RULE**: *KHÔNG
  đóng gói vào ISO cho tới khi rights_evidence là bằng chứng cấp phép thật + hội đồng ký duyệt*
  (UX12-026/UX12-048) — nhưng **cả 25 gói đã được đóng vào `includes.chroot`**. Provenance ledger
  (`.../usr/share/namios/docs/WALLPAPER-PROVENANCE.md`) **chỉ xác nhận an toàn cho 5 gói procedural
  `NaMiOS-21..25`**; 20 gói kia nằm diện "phải gỡ/thay trước phát hành".
  - **Quyết (a):** lập trường pháp lý về ảnh do **AI sinh** (bản quyền output + điều khoản công cụ).
  - **Quyết (b):** gỡ hay giữ 20 ảnh AI; nếu giữ, cần bằng chứng + người ký.
  - **Quyết (c):** **`NaMiOS-20-Bien-Dao-Viet-Nam`** là ảnh **AI về chủ quyền biển đảo** — HIG
    §5.3 cảnh báo **không** đưa biểu tượng chủ quyền/bản đồ **chưa kiểm chứng** vào hình nền thông
    tin → **khuyến nghị GỠ** cho tới khi có kiểm chứng.
  - *Trước khi cấp phép xong:* chỉ ship 5 gói procedural đã duyệt + đặt **mặc định** là 1 gói đã
    duyệt (liên quan C4). (Ngoài ra hook `0400:155-163` còn **ghi đè toàn bộ wallpaper gói `Next`
    bằng ảnh Hạ Long** `namios-desktop-default.png` — cũng là ảnh AI diện D3.)

### D4 — Web-launcher dịch vụ bên thứ 3 (Zalo / Facebook / TikTok / YouTube)
- 4 `.desktop` dùng **tên + hostname** dịch vụ (nhãn hiệu bên thứ 3) theo kiểu nominative. Nhãn
  đã **trung thực** ("Dịch vụ web, cần tài khoản riêng, không lưu đăng nhập hộ", loại B) và
  **icon dùng `internet-web-browser` chung** (không chép logo bên thứ 3 — tốt). **Quyết:** go/no-go
  shipping các shortcut này. (`.../usr/share/applications/namios-{zalo-web,facebook,tiktok,youtube}.desktop`.)

### D5 — Kênh phát hành
- Hiện **"alpha"** ở mọi nơi (`os-release` VERSION, `namios-release` NAMIOS_CHANNEL,
  `RELEASE-NOTES-2026.11.md`). **Quyết:** kênh công khai (alpha/beta/stable) + có tuyên bố
  "official public release" ngay bây giờ, hay ship alpha trước.

---

## 4. Điều kiện DỪNG-phát-hành phải gỡ trước khi chứng nhận (tổng hợp)

Trích HANDOFF "Điều kiện dừng phát hành" + HIG §10.3/§12/§14 + HIG-ADOPTION-VERDICT §4:

1. Chưa rõ quyền dùng **tên NaMi/NaMiOS** + quyền **logo/font/hình nền** → **D1, D3**.
2. Luồng **cài có thể xoá dữ liệu** phải hiện phân vùng + xác nhận 2 bước → **NEEDS-BOOT-TEST #8**
   (Calamares `namios` branding có, cần chứng thực hành vi thật).
3. **Cập nhật/rollback** không được phá boot/mất dữ liệu mà chưa có recovery đã thử →
   **NEEDS-BOOT-TEST #6**.
4. **Trạng thái tương thích** công bố phải có dữ liệu kiểm thử (không giả `nWine`/driver) — hiện
   nhãn đã trung thực (nWine, web-launcher), cần giữ.
5. **Không hạ bảo mật để thay hình** → **C1** (rò `Xwrapper allowed_users=anybody` sang máy cài)
   phải sửa; Secure Boot nói rõ (NEEDS-BOOT-TEST #10).
6. **Không ship bản có `TBD`** (BUILD-002) → **C2**.
7. Thành phần cốt lõi dùng được **bằng bàn phím** + thông báo lỗi có cách xử lý →
   **NEEDS-BOOT-TEST #4**.

---

## 5. Những điểm ĐÃ ĐẠT (ghi nhận, giảm phạm vi lo)

- **Version-string nhất quán 2026.11:** `os-release`, `lsb-release`, `etc/namios-release`,
  Calamares `branding.desc` đồng bộ `2026.11 (Đông Sơn)` + kênh `alpha`; tên hiển thị `NAME="NaMi"`.
  (Chỉ còn C8 `pyproject` 0.0.0.dev0 là chuỗi 0.0.0 sót.)
- **Không rò secret vào ISO:** không có `ghp_`/private-key bị commit; `.gh-token` đã gitignore +
  untracked + ngoài payload ISO (C9 chỉ là vệ sinh).
- **Không có asset BROKEN (file thiếu):** SDDM `namios`/Plymouth/Calamares/Plasma splash/icon
  `namios`+`start-here-namios` đều resolve; icon + splash + badge đã là **trống đồng Đông Sơn**
  (chỉ còn C4 `namios-default.png` là logo sen cũ).
- **Package-lists:** không có gói "không tồn tại"; archive-areas đủ (`auto/config:67`); cú pháp
  sạch; chỉ còn 3 tên low-confidence cần xác nhận ở build host (C5).
- **Hooks:** tất cả có `set -euo pipefail`; **không** `curl|bash`/token nhúng/tắt Secure Boot;
  mọi `-src` được tham chiếu đều tồn tại; idempotent tốt. (Vấn đề còn lại: C1, C3, C7.)
- **Trung thực/nói-đúng:** web-launcher + `nWine` đã nói thật (loại B, "một số phần mềm Windows…
  kế toán/USB-token thường KHÔNG chạy"); không overclaim "chạy mọi app/driver"; docs An toàn cấm
  "chặn 100%".
- **Giấy phép font:** Noto/Liberation2/DejaVu/Inter(OFL)/Carlito/Caladea — mở, phân phối được,
  **không font Microsoft** (`0300-fonts.list.chroot`).
- **A11y:** `NaMi-HighContrast.colors` đã có, đo WCAG thật (chữ 21:1), KDE tự liệt kê trong Colors
  (còn cần boot-test screen reader/focus — NEEDS-BOOT-TEST #4).
- **CI quality-gate XANH tại HEAD:** `ruff` / `black` / `mypy src/namios_core` PASS; `pytest`
  collect **2598 tests** không lỗi. (Lưu ý: CI này **chỉ** kiểm Python helper — KHÔNG build/boot
  ISO.)

---

## 6. ĐƯỜNG TỐI THIỂU tới "official release" (checklist tuần tự)

1. **Sửa xong CODE-FIXABLE-NOW** (§1) — ưu tiên **C1** (rò bảo mật), **C2** (TBD), **C3** (build
   dễ vỡ), **C4** (logo sen cũ); rồi C5–C10.
2. **Chủ dự án quyết D1–D5** (§3) — có **sign-off pháp lý** cho **D1** (tên) + **D2** (nOffice) +
   **D3** (hình nền AI/chủ quyền). Cho tới lúc đó: chỉ ship 5 wallpaper procedural + default là 1
   ảnh đã duyệt.
3. **Build ISO trên build host amd64 thật có nested-virt** (`build-release.yml`/`ci-build.sh`) —
   **review MỌI dòng `DROPPED`** trong `build.log`; xác nhận không gói must-have nào bị drop
   (sau C5).
4. **Boot + cài + nâng cấp + rollback trên PHẦN CỨNG THẬT** (không chỉ VM) — đủ bucket §2, có
   **bằng chứng ảnh/video F01–F07**; lật `verified_on_host → YES`. **Xác nhận C1 đã dọn** softGL +
   Xwrapper trên máy đã cài.
5. **Gỡ hết điều kiện dừng §4:** không TBD; không giả tương thích/rollback; không hạ bảo mật;
   nhãn hiệu + giấy phép font/hình nền có **bằng chứng**; AI consent-gate đã kiểm.
6. **Thử người dùng thật** (≥5 chưa-Linux + ≥5 quen-Windows, **≥80% hoàn thành độc lập** 8 tác vụ
   P0 — HIG §12.1).
7. **Chỉ khi đó** mới dán nhãn kênh = `stable` + chứng nhận **"official public release"**.

---

*Soạn bởi release manager, 2026-11-11, repo HEAD `ff7928d`. Bằng chứng: đọc §12/§13 + điều kiện
dừng của HIG/HANDOFF, HIG-ADOPTION-VERDICT, P0-UI-AUDIT, WINDOWS11-PARITY, + sweep repo
(package-lists, hooks, assets, os-release/lsb-release/namios-release, brand.json, wallpapers +
provenance, TRADEMARK-LICENSE-COMPLIANCE, ci-build.sh, auto/config, website tokens). Chạy thật
trong phiên: `ruff`/`black`/`mypy` PASS, `pytest --collect-only` = 2598. `verified_on_host: NO`
cho mọi khẳng định về hành vi boot/hiển thị. Không commit/push.*
