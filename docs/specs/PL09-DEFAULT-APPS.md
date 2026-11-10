# NaMiOS — Phụ lục 09: Ứng dụng mặc định (A/B/C) + ClamAV on-demand

**Ngày:** 10/11/2026. **Theo:** `docs/specs/namios-pl09/NaMiOS_Phu_luc_09_Nguoi_Viet_An_toan_Ung_dung_Giao_dien.md`
§2.3 (VN09-016..023, ứng dụng mặc định và phân phối) + §2.4 (VN09-024..036,
bảo mật/chống mã độc). Xây trên hạ tầng CÓ SẴN, KHÔNG dựng hệ trạng thái thứ
hai: `src/namios_essentials` (Phụ lục 11, `docs/specs/PHU-LUC-11-APP11-
MAPPING.md`) cho mô hình manifest/chống mạo danh; `docs/specs/namios-pl01-
dacta/contracts/app-manifest.schema.json` (Phụ lục 01 DAC_TA) được XEM XÉT
làm hợp đồng cơ sở nhưng KHÔNG dùng trực tiếp (lý do ở §5).

**Trạng thái thật:** `specified` — đã viết file/code, **CHƯA** `lb build` +
boot thật (đúng quy ước Phụ lục 13 §5, giống `docs/SECURITY-DEFAULTS.md`).
Mọi khẳng định dưới đây được chứng minh bằng CHẠY THẬT code có sẵn trong repo
(không chỉ đọc code rồi suy luận) — lệnh + kết quả trích ở từng mục.

## 1. Ba loại "cài sẵn" (A/B/C) — không trộn loại

Theo đúng §1 đặc tả Phụ lục 09: *"'Cài sẵn' phải phân biệt ba loại: (A) ứng
dụng Linux cài trong ảnh hệ thống; (B) lối mở trang chính thức...; (C) ứng
dụng Windows chạy trong capsule Wine chỉ sau khi được kiểm thử theo phiên bản
và nghiệp vụ."* Ba loại này ĐÃ có kiểu dữ liệu đúng tên trong
`src/namios_essentials/_types.py:74` (`DeliveryType`): `INSTALLED_NATIVE` (A),
`OFFICIAL_WEB` (B), `WINE_OPTIONAL` (C) — đợt này chỉ dùng A và B (không có
app Windows/Wine nào trong phạm vi giao).

Nhãn hiển thị tương ứng do `src/namios_essentials/labels.py:50`
(`delivery_label`) chọn theo đúng kiểu, và `web_label_is_honest` (dòng 79)
CHẶN một `OFFICIAL_WEB` hiển thị cụm "đã cài"/"bản Linux" — đây chính là cửa
nghiệm thu VN09-016: *"không mục nào có tên 'đã cài' khi chỉ là web
shortcut."*

## 2. Bốn shortcut web chính thức (loại B) — VN09-018/020

| App | URL chính thức dùng cho shortcut | Hostname | File `.desktop` | `app_id` trong manifest |
| --- | --- | --- | --- | --- |
| Facebook | `https://www.facebook.com/` | `www.facebook.com` | `usr/share/applications/namios-facebook.desktop` | `facebook.web` |
| Zalo Web | `https://chat.zalo.me/` | `chat.zalo.me` | `usr/share/applications/namios-zalo-web.desktop` | `zalo.web` |
| TikTok | `https://www.tiktok.com/` | `www.tiktok.com` | `usr/share/applications/namios-tiktok.desktop` | `tiktok.web` |
| YouTube | `https://www.youtube.com/` | `www.youtube.com` | `usr/share/applications/namios-youtube.desktop` | `youtube.web` |

**Lưu ý trung thực về URL Zalo:** bảng ở §1 đặc tả Phụ lục 09 nêu
`https://www.zalo.me/pc` (trang tải app PC) và `https://id.zalo.me/` (cổng
đăng nhập/định danh dùng chung của Zalo) làm ví dụ "lối mở bản Web". Shortcut
đợt này trỏ tới `https://chat.zalo.me/` — ứng dụng web nhắn tin THẬT của Zalo
(nơi quét QR để chat), đúng với tên "Zalo Web" hơn trang tải app hoặc cổng
định danh thuần. Cả ba (`zalo.me`, `id.zalo.me`, `chat.zalo.me`) đều là
subdomain của CÙNG MỘT domain gốc `zalo.me` đã nằm trong allowlist (xem §4) —
đây KHÔNG phải một domain khác hay một sự nới allowlist, chỉ là chọn đúng
trang con cho đúng tên tính năng.

**Cả 4 file `.desktop`:**
- `Exec=xdg-open <URL>` — tĩnh, không wrapper, không form đăng nhập hộ (đúng
  yêu cầu VN09-018 "không pin trang đăng nhập giả"; `xdg-utils` tồn tại thật
  trong trixie, xác nhận qua `qa.debian.org/madison.php` 10/11/2026:
  `xdg-utils 1.2.1-2 | trixie`; mẫu dùng `Exec=xdg-open ...` đã có sẵn trong
  repo ở `usr/share/applications/namios-huong-dan.desktop`, không phải cách
  dùng mới).
- `Name=<Brand> (Dịch vụ web)` + `Name[vi]=<Brand> — Dịch vụ web, cần mạng và
  tài khoản riêng` — câu honest bắt buộc nằm NGAY trong tên hiển thị, không
  chỉ trong Comment (người dùng lướt menu vẫn thấy ngay).
- `Comment`/`Comment[vi]` nêu rõ: loại B, KHÔNG phải app Linux cài sẵn,
  KHÔNG offline, cần tài khoản riêng, NaMiOS không lưu đăng nhập hộ.
- `Categories=Network;` theo đúng yêu cầu giao việc.
- `Icon=internet-web-browser` — icon GENERIC, KHÔNG dùng logo Facebook/Zalo/
  TikTok/YouTube thật (chưa có hồ sơ quyền nhãn hiệu — xem `trademark_status:
  "pending"` trong manifest §5 và `anti_impersonation.effective_trademark_
  status`, APP11-033: thiếu hồ sơ quyền → luôn `replace_with_text`).
- Thêm 3 khóa `X-NaMiOS-*` (delivery type, app-manifest id, official hostname)
  để liên kết ngược sang `default-app-manifest.json` — không bắt buộc theo
  chuẩn `.desktop` nhưng không phá chuẩn (khóa `X-` tùy ý được cho phép).

## 3. Bảy ứng dụng thiết yếu native (loại A) — VN09-017

Danh sách lấy từ package-lists ĐÃ CÓ SẴN trong repo (không thêm gói mới ở
mục này, chỉ mô tả lại trong manifest):

| App | Gói Debian | Version trixie (xác nhận qua madison 10/11/2026) | Nguồn package-list | Rebrand hiển thị |
| --- | --- | --- | --- | --- |
| Firefox ESR | `firefox-esr` | `140.15.0esr-1~deb13u1` | `0400-office-browser.list.chroot` | không đổi tên |
| NaMiOffice | `libreoffice` | `4:25.2.3-2+deb13u6` | `0400-office-browser.list.chroot` | hook `0450-namioffice-brand.hook.chroot` |
| NaMiPDF | `okular` | `4:25.04.2-1+deb13u1` | `0100-desktop-kde.list.chroot` | hook `0453-namipdf-brand.hook.chroot` (giữ chữ "Okular") |
| Dolphin | `dolphin` | `4:25.04.3-1+deb13u1` | `0100-desktop-kde.list.chroot` | không đổi tên |
| Fcitx5 | `fcitx5` (+`fcitx5-unikey`) | `5.1.12-2` | `0200-locale-vi.list.chroot` | không đổi tên |
| Kate | `kate` | `4:25.04.3-2` | `0100-desktop-kde.list.chroot` | không đổi tên |
| NaMiMail | `thunderbird` | `1:140.12.0esr-1~deb13u1` | `0405-mail-notes.list.chroot` | hook `0452-namimail-brand.hook.chroot` (giữ chữ "Thunderbird") |

"NaMiOffice"/"NaMiPDF"/"NaMiMail" là **tên hiển thị rebrand**, KHÔNG phải mã
nguồn viết mới — mỗi hook rebrand tương ứng đều GIỮ chữ gốc (Okular/
Thunderbird) hoặc ghi rõ "dựa trên LibreOffice" trong tài liệu, đúng giấy
phép MPL/LGPL/GPL của từng dự án. Manifest ở §5 lặp lại đúng quy tắc này
(trường `publisher`/`icon_provenance` luôn ghi tên dự án gốc).

## 4. Luật allowlist hostname — chặn domain giả (VN09-018, E11-06)

Logic chặn **đã có sẵn** ở `src/namios_essentials/anti_impersonation.py`, có
2 lớp:
- `check_official_url(url)` (dòng 75): fail-closed — thiếu HTTPS hoặc host
  không khớp/không phải subdomain của một domain trong
  `OFFICIAL_DOMAIN_ALLOWLIST` (dòng 36) → `allowed=False`. Nếu host CHỨA một
  brand token đã biết (`BRAND_TOKENS`, dòng 56) nhưng không allowlisted →
  gắn thêm `impersonation_suspected=True` + mã lỗi
  `E_APP11_DOMAIN_IMPERSONATION_SUSPECTED`.
- `may_render_login_form(check)` (dòng 113): CỔNG DUY NHẤT quyết định có cho
  hiện form đăng nhập không — trả đúng `check.allowed`, nên domain giả không
  bao giờ có đường hiện ô nhập mật khẩu.

Đây là module xử lý "lối mở trang web" của Phụ lục 11 (không phải
`update_center.evaluate_web_shortcut`, vốn chỉ quyết định badge Update Center
— "sự cố dịch vụ" khác với "NaMiOS chưa cập nhật", APP11-019/E11-03, KHÔNG
liên quan hostname/đăng nhập; ghi rõ ở đây để tránh lẫn hai hàm).

**Đã CHẠY THẬT (không chỉ đọc code) để xác nhận cả 4 shortcut + 1 domain giả
mẫu VN09-018 nêu đích danh:**

```
https://www.facebook.com/      -> allowed=True  impersonation_suspected=False may_render_login_form=True
https://chat.zalo.me/          -> allowed=True  impersonation_suspected=False may_render_login_form=True
https://www.tiktok.com/        -> allowed=True  impersonation_suspected=False may_render_login_form=True
https://www.youtube.com/       -> allowed=True  impersonation_suspected=False may_render_login_form=True
https://zalo-login.example/    -> allowed=False impersonation_suspected=True  may_render_login_form=False  error_code=E_APP11_DOMAIN_IMPERSONATION_SUSPECTED
https://www.facebook-login.example/ -> allowed=False impersonation_suspected=True may_render_login_form=False error_code=E_APP11_DOMAIN_IMPERSONATION_SUSPECTED
```

Khớp đúng nghiệm thu VN09-018: *"URL thay bằng `zalo-login.example` bị
chặn/cảnh báo."* Lưu ý: đây là kiểm TĨNH theo host (chưa crawl redirect chain
thật) — đúng giới hạn đã ghi ở `docs/specs/PHU-LUC-11-APP11-MAPPING.md`
(APP11-003 "BLOCKED: crawl redirect chain thật").

## 5. `default-app-manifest.json` — vì sao KHÔNG dùng schema Phụ lục 01 (DAC_TA)

File: `distro/live-build/config/includes.chroot/usr/share/namios/apps/
default-app-manifest.json` (11 mục: 7 loại A + 4 loại B).

`docs/specs/namios-pl01-dacta/contracts/app-manifest.schema.json` được đọc
và THỬ VALIDATE trước — **không tương thích**: schema đó mô hình một
**installer/recipe Wine** (field bắt buộc `application.installer_sha256`,
`runtime.runner_id`/`wow64_strategy`, `recipe[]` các action
`create_prefix`/`run_installer`/..., `license` là object lồng, tên field
`id`/`mode`/`source` khác hẳn). Chạy thật `jsonschema` validate một mục
(`firefox-esr`) với schema này ra **11 lỗi** (thiếu `name`/`mode`/
`application`/`source`/`runtime`, `license` sai kiểu, field lạ bị
`additionalProperties:false` chặn) — xác nhận đây là hợp đồng cho tuyến cài
Wine/installer rời (Phụ lục 01 §DAC_TA + APP-ZAL), không phải cho "gói apt đã
có trong ảnh" hay "shortcut web".

Thay vào đó, dùng ĐÚNG hợp đồng đã có cho đúng việc này:
`docs/specs/essentials-manifest.schema.json` (Phụ lục 11, APP11-002) —
model sẵn `EssentialsManifest` (`_types.py:93`) với field khớp 1:1 yêu cầu
VN09-016 ("app_id" ↔ `id`, "loại" ↔ `delivery_type`, "nhà cung cấp" ↔
`publisher`, `official_url`, `license`, "quyền" ↔ `required_permissions`,
`offline`, và ngày kiểm lại ↔ `last_verified` + người phụ trách ↔ `owner`).
Đây là "superset rõ ràng" đúng theo chỉ dẫn giao việc — tái dùng hợp đồng Phụ
lục 11 sẵn có, KHÔNG tạo field tên khác cho cùng một ý nghĩa.

**Đã CHẠY THẬT jsonschema Draft 2020-12 trên cả 11 mục:**

```
item count: 11
all schema valid: True
```

**Đã CHẠY THẬT qua lớp ngữ nghĩa (`namios_essentials.manifest`)** — không
chỉ "đúng cấu trúc JSON" mà còn qua đúng luật fail-closed đã có:

```
firefox-esr            is_shippable=False violations=('E_APP11_MANIFEST_NO_SOURCE', 'E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE')
namioffice.libreoffice  is_shippable=False violations=('E_APP11_MANIFEST_NO_SOURCE', 'E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE')
... (6 mục loại A khác — cùng 2 mã lỗi)
facebook.web            is_shippable=False violations=('E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE',)
zalo.web / tiktok.web / youtube.web — cùng 1 mã lỗi trên
```

Hai vi phạm này là CÓ CHỦ Ý, không phải lỗi bỏ sót — giải thích để người đọc
sau không tưởng nhầm là bug:

1. **`E_APP11_MANIFEST_NO_OWNER_OR_TESTDATE`** (cả 11 mục): `last_verified`
   để `null` vì **CHƯA có lần build + boot thật nào xác nhận** 11 mục này —
   đúng quy ước "chưa build/boot thật = `specified`, không phải `completed`"
   đã dùng xuyên suốt repo (`docs/SECURITY-DEFAULTS.md` dòng 11). KHÔNG điền
   một ngày giả để file "trông như đã kiểm".
2. **`E_APP11_MANIFEST_NO_SOURCE`** (7 mục loại A): `namios_e08.provenance_ok`
   (`driver_match.py:27`) yêu cầu `sha256` một binary CỤ THỂ — cơ chế này
   được thiết kế cho driver/firmware/installer Wine TẢI RỜI (Phụ lục 08), có
   một file duy nhất để băm. 7 gói loại A ở đây là gói apt đã có sẵn trong
   package-lists hiện hành; nguồn tin cậy THẬT của chúng là **chữ ký Release
   của apt** (đã ghi ở `docs/SECURITY-DEFAULTS.md`: *"apt trixie mặc định
   xác minh chữ ký Release... không có việc nào mới phải làm"*), KHÔNG phải
   một sha256 đơn do NaMiOS tự băm/tự khai. Cố tình KHÔNG điền `sha256` giả
   vào `package_source` — bịa một hash để "qua" `validate_manifest` vi phạm
   trực tiếp CLAUDE.md ("không giả lập để báo đạt"). Đây là MỘT GIỚI HẠN ĐÃ
   BIẾT khi tái dùng `Provenance` cho gói apt, ghi lại ở đây làm việc còn mở:
   hoặc (a) một build host thật tính `sha256sum` của `.deb` đã pin snapshot
   rồi điền vào, hoặc (b) `namios_essentials` cần thêm một đường provenance
   RIÊNG cho "nguồn = apt Release đã ký" khác với "nguồn = sha256 một file" —
   quyết định đó KHÔNG làm trong đợt này (ngoài phạm vi giao việc).

Kết luận trung thực: `default-app-manifest.json` **đúng cấu trúc (schema
valid 11/11)** và **không có mục nào thiếu license/nguồn một cách âm thầm**
— nhưng CHƯA mục nào `is_shippable=True` theo đúng nghĩa Phụ lục 11, vì chưa
qua build + boot thật. KHÔNG dán nhãn "đã release" cho file này.

## 6. ClamAV — chỉ on-demand, on-access TẮT có chủ ý (VN09-029/030)

File: `distro/live-build/config/package-lists/0635-antivirus.list.chroot`.
Cài `clamav` (lệnh `clamscan`, quét THEO YÊU CẦU) + `clamav-freshclam` (cập
nhật chữ ký, tự có systemd timer theo mặc định gói Debian). **KHÔNG** cài
`clamav-daemon` (clamd — daemon on-access).

Cả 2 tên gói đã xác nhận tồn tại trong `trixie` qua
`qa.debian.org/madison.php` (truy xuất 10/11/2026): `clamav 1.4.3+dfsg-1` và
`clamav-freshclam 1.4.3+dfsg-1`. `clamav-daemon 1.4.3+dfsg-1` cũng tồn tại
trong trixie nhưng **CHỦ Ý không đưa vào file list** — và vì repo này build
với `--no-install-recommends` (quy ước đã dùng ở `0405-mail-notes.list.
chroot`/`0620-backup.list.chroot`), package `clamav-daemon` không có đường
lọt vào ảnh qua Recommends dù `clamav` có khai nó.

**Vì sao on-access TẮT (VN09-029 nghiệm thu: "không quảng cáo mức bảo vệ
100%"):** quét thường trú theo thời gian thực (fanotify/inotify) có lịch sử
thật về tốn CPU/IO và rủi ro deadlock với một số workload khi chưa tinh
chỉnh/benchmark trên phần cứng mục tiêu — đúng cảnh báo trong đặc tả Phụ lục
09 §2.4 dòng VN09-029 ("On-access scanning chỉ bật sau benchmark, kiểm giới
hạn kernel/engine và chống deadlock/giảm tốc"). Chưa có máy pilot thật để đo,
nên KHÔNG bật mặc định — ghi lại là việc CÒN MỞ, không phải đã quyết định
"không bao giờ bật".

**Security Center hiện trạng thái THẬT (VN09-030: không lấy "quét sạch" làm
bằng chứng an toàn; Security Center phải báo riêng từng tín hiệu)** — đã MỞ
RỘNG script có sẵn `/usr/local/bin/namios-security-center` (ghi bởi
`distro/live-build/config/hooks/normal/0630-security-default.hook.chroot`
phần (d)), KHÔNG tạo UI trạng thái thứ hai. Thêm 3 dòng đọc trạng thái thật:
đã cài ClamAV hay chưa (`command -v clamscan`), tuổi chữ ký (`stat` trên
`/var/lib/clamav/{daily,main}.{cvd,cld}`, cảnh báo riêng nếu > 7 ngày — ngay
cả khi lần quét trước "sạch", đúng E11-04), và trạng thái on-access
(`systemctl is-active clamav-daemon.service`, tái dùng đúng hàm
`check_unit_active` có sẵn — không viết hàm thứ hai).

**Đã CHẠY THẬT script đã trích xuất** (môi trường không có `systemctl`/
`clamscan` → nhánh "Không xác định"/"Chưa cài", đúng fallback thiết kế sẵn):

```
Tường lửa (UFW): Không xác định
Cập nhật bảo mật tự động: Tắt
AppArmor (giới hạn quyền ứng dụng): Không xác định
Quét mã độc ClamAV (theo yêu cầu): Chua cai
Chữ ký ClamAV: Khong xac dinh (chua co du lieu chu ky/chua cai)
Quét thường trú (on-access): Không xác định — mặc định TẮT tới khi benchmark xong (VN09-029)

Lưu ý quan trọng: NaMiOS KHÔNG hứa chống được 100% virus/mã độc, kể cả
khi vừa quét sạch. ...
```

Và đã CHẠY THẬT lần nữa với `clamscan` giả lập có mặt + file chữ ký giả lập
20 ngày tuổi, xác nhận đúng 2 nhánh còn lại hoạt động:

```
Quét mã độc ClamAV (theo yêu cầu): Co cai, chi quet theo yeu cau (on-demand)
Chữ ký ClamAV: QUA HAN 20 ngay chua cap nhat - kiem mang hoac chay freshclam
```

`bash -n` xác nhận cú pháp cả hook ngoài và script bên trong (trích xuất
riêng) đều hợp lệ; script chạy thật `exit 0`, không crash khi thiếu lệnh.

`docs/SECURITY-DEFAULTS.md` §2/§4 và
`distro/live-build/config/package-lists/0630-security.list.chroot` đã được
cập nhật để KHÔNG còn nói "ClamAV còn ở dạng comment, chưa chốt" — tránh hai
nguồn sự thật mâu thuẫn (một nơi nói "chưa cài", một nơi đã cài thật).

**KHÔNG quảng cáo ở bất kỳ đâu** (file list, hook, doc này): "bảo vệ 100%",
"diệt sạch mọi mã độc", hay coi ClamAV là antivirus thường trú.

## 7. Đã xác minh thật vs. chưa — đừng đọc nhầm thành "xong"

| Đã làm (chạy thật trong đợt này) | CHƯA làm (cần build/boot/pilot thật) |
| --- | --- |
| jsonschema validate 11/11 mục `default-app-manifest.json` | `lb build` + boot ISO thật |
| `check_official_url`/`may_render_login_form` cho 4 URL thật + 2 domain giả | Crawl redirect chain thật (APP11-003 còn BLOCKED từ Phụ lục 11) |
| `validate_manifest`/`is_shippable`/`may_bundle_binary` cho 11 mục | `apt-cache show` trên build host thật cho `clamav`/`clamav-freshclam`/`xdg-utils`/7 gói loại A (chỉ xác nhận qua `madison` — không phải build host) |
| `bash -n` + chạy thật script Security Center đã mở rộng (2 tình huống: chưa cài, đã cài+chữ ký quá hạn) | Benchmark on-access ClamAV thật trên phần cứng pilot (CPU/IO/deadlock) |
| `git check-ignore` xác nhận 3 đường dẫn mới KHÔNG bị `.gitignore` chặn | Test thật mở 4 shortcut từ menu KDE, `xdg-open` thật gọi đúng Firefox ESR |
| Xác nhận `clamav`/`clamav-freshclam`/`xdg-utils` + 7 gói loại A tồn tại trong suite `trixie` qua `qa.debian.org/madison.php` | Nghiệm thu người dùng thật (8-10 người) theo §3 bộ ca mẫu Phụ lục 09 |

## 8. File đã thêm/sửa trong đợt này

**Thêm mới:**
- `distro/live-build/config/includes.chroot/usr/share/applications/namios-facebook.desktop`
- `distro/live-build/config/includes.chroot/usr/share/applications/namios-zalo-web.desktop`
- `distro/live-build/config/includes.chroot/usr/share/applications/namios-tiktok.desktop`
- `distro/live-build/config/includes.chroot/usr/share/applications/namios-youtube.desktop`
- `distro/live-build/config/includes.chroot/usr/share/namios/apps/default-app-manifest.json`
- `distro/live-build/config/package-lists/0635-antivirus.list.chroot`
- `docs/specs/PL09-DEFAULT-APPS.md` (file này)

**Sửa (để tránh hai nguồn sự thật mâu thuẫn với phần mới):**
- `distro/live-build/config/package-lists/0630-security.list.chroot` — thay
  đoạn comment cũ "ClamAV tắt, chưa chốt" bằng con trỏ sang `0635-antivirus.
  list.chroot`.
- `distro/live-build/config/hooks/normal/0630-security-default.hook.chroot`
  — mở rộng script `namios-security-center` (phần (d)) để đọc + hiện trạng
  thái ClamAV thật (đã cài/chưa, tuổi chữ ký, on-access).
- `docs/SECURITY-DEFAULTS.md` — §2 (bảng lớp phòng thủ) + §4 (ClamAV) cập
  nhật khớp với quyết định mới.
