# UX-V1 — Kết quả kiểm chứng (VERIFY)

- Ngày: 2026-11-03 (UTC 05:28)
- Chủ đề: Desktop "giống Windows" (UI-001..007) + namios-welcome (DATA-001/002, UI-005) + bước tự kiểm chứng ISO trong build-iso.yml (BUILD-003/INSTALL-001).
- Vai trò: VERIFY — chỉ chạy lệnh đọc/kiểm, KHÔNG sửa file của DESKTOP/WELCOME/ISOVERIFY, không chạy git (chỉ đọc).
- Môi trường: container headless, không có desktop KDE Plasma → mọi kết luận "giống Windows về thị giác" giữ `verified_on_boot: NO` đúng ADR 0011. Báo cáo này chỉ xác nhận: cú pháp, logic đơn vị (pytest), lint/type, và tính nhất quán giữa tài liệu ⇄ code.

## 1. Full python test suite

Lệnh:
```
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest /home/node/.openclaw/workspace/code_projects/namios/tests -q -p no:cacheprovider
```
Kết quả: **800 passed, 1 skipped in 5.33s**
Yêu cầu: >= 772 pass, 0 fail → **PASS** (800 ≥ 772; 0 fail; 1 skip trước đó đã có, không mới).

Riêng module welcome (double-check):
```
.../.venv/bin/python -m pytest tests/unit/welcome -q -p no:cacheprovider
```
Kết quả: **28 passed in 0.22s** — khớp đúng số 28 test mới mà WELCOME báo cáo.

## 2. ruff / black / mypy trên src mới

| Lệnh | Kết quả |
| --- | --- |
| `.venv/bin/ruff check src` | **All checks passed!** (exit 0) |
| `.venv/bin/black --check src` | **All done! 92 files would be left unchanged.** (exit 0) |
| `.venv/bin/mypy src/namios_welcome` | **Success: no issues found in 5 source files** (exit 0) |

→ **PASS** cả 3 lệnh, không có lỗi mới.

## 3. Parse config KDE bằng configparser (strict) + mimeapps.list/.desktop

Script `configparser.ConfigParser(strict=True, interpolation=None)` đọc từng file dưới
`distro/live-build/config/includes.chroot/etc/skel/.config/`:

| File | Kết quả | Số section |
| --- | --- | --- |
| dolphinrc | OK | 2 |
| kdeglobals | OK | 3 |
| kglobalshortcutsrc | OK | 4 |
| kwinrc | OK | 1 |
| mimeapps.list | OK | 2 |
| plasma-localerc | OK | 2 |
| plasma-org.kde.plasma.desktop-appletsrc | OK | 10 |
| autostart/namios-welcome.desktop | OK (configparser, section `Desktop Entry` đọc đủ key `Exec`/`Icon`/`Name[vi]`...) | 1 |

Không có lỗi cú pháp INI/trùng key ở bất kỳ file nào → **PASS**.

Đối chiếu nội dung `mimeapps.list` ⇄ tuyên bố UX-WINDOWS-FAMILIAR.md mục 4: khớp đúng
(DOCX/XLS/PPTX→LibreOffice, PDF→okular, có cảnh báo verified_on_host: NO rõ ràng).

Đối chiếu `kglobalshortcutsrc` + `kwinrc` ⇄ bảng ánh xạ mục 2 của UX-WINDOWS-FAMILIAR.md:
khớp đúng từng dòng (Meta→Kickoff qua `[ModifierOnlyShortcuts]`, Meta+E→dolphin,
Meta+D→Show Desktop, Meta+L→Lock Session, Print→Spectacle, Alt+Tab giữ mặc định KWin).

## 4. `bash -n` hook 0300-namios-welcome.hook.chroot + quét curl|bash / eval

```
bash -n distro/live-build/config/hooks/normal/0300-namios-welcome.hook.chroot
```
→ cú pháp hợp lệ (exit 0).

`grep -nE 'curl.*\|\s*bash|curl.*\|\s*sh\b|eval\s'` trên file: chỉ khớp 2 dòng **comment**
tự khai "KHÔNG curl|bash, KHÔNG eval" (dòng 18, 52) — không có lệnh thực thi nguy hiểm nào.
Đọc toàn bộ nội dung hook xác nhận: `set -euo pipefail`, chỉ copy file tĩnh
(`cp -a`), tạo wrapper tĩnh bằng heredoc không nội suy input, không có `wget`/`curl` nào.
→ **PASS**.

Phát hiện phụ (không phải lỗi cú pháp, đã được DESKTOP/WELCOME tự ghi nhận là "blocked"
sẵn — xác nhận lại ở đây): hook kiểm tra `/opt/namios/namios_welcome-src/{__init__.py,__main__.py}`
và **chủ động `exit 1`** nếu thiếu. Tại thời điểm kiểm tra, điểm staging
`distro/live-build/config/includes.chroot/opt/namios/namios_welcome-src/` **chỉ có**
`README-PLACEHOLDER.md` (chưa có mã nguồn thật), trong khi mã nguồn thật nằm ở
`src/namios_welcome/` (ngoài phạm vi hook/includes.chroot). Đây là **gap liên-luồng đã biết
và đã khai báo trong cả hai báo cáo DESKTOP và WELCOME** (không phải phát hiện mới), ghi
lại ở mục "blocked" dưới đây theo đúng vai trò VERIFY (không tự sửa, không thuộc phạm vi
sở hữu `qa/evidence-index/UX-V1/`).

## 5. Rà soát tài sản/nội dung Microsoft độc quyền

- `find` tên file chứa "windows"/"microsoft" dưới `distro/`, `src/`, `docs/specs/`: chỉ
  có `docs/specs/UX-WINDOWS-FAMILIAR.md` (tên file tài liệu ánh xạ, không phải asset).
- `grep -i microsoft` trên includes.chroot + package-lists + hooks + UX spec + ADR 0011:
  toàn bộ kết quả là **comment/doc nhắc ràng buộc pháp lý** ("TUYỆT ĐỐI KHÔNG sao chép
  icon/font/âm thanh Microsoft", "không tự sao chép font Microsoft từ máy khác vào ISO"),
  không có tên file/asset Microsoft thật nào được đóng gói.
- `0300-fonts.list.chroot`: toàn bộ font là gói mở (fonts-noto-core, fonts-noto-ui-core,
  fonts-liberation2, fonts-dejavu-core) — không có Calibri/Cambria/Segoe/Times New Roman.
- Wallpaper `usr/share/backgrounds/namios/namios-default.svg`: kiểm well-formed bằng
  `xml.dom.minidom.parse` → **OK, root tag `svg`**; grep base64/woff/ttf/eot/segoe/calibri/
  arial trong nội dung SVG → **none found** (không nhúng font/asset lạ).

→ **PASS**, không phát hiện tài sản Microsoft độc quyền bị chép.

## 6. YAML `.github/workflows/build-iso.yml`

```
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/build-iso.yml'))"
```
→ Parse thành công, top-level keys: `name`, `on` (PyYAML 1.1 hiển thị là `True` — đây là
quirk chuẩn của PyYAML với khóa `on:`/`yes:`/`no:` trong YAML 1.1, KHÔNG phải lỗi cú pháp;
GitHub Actions parser của GitHub đọc đúng `on:` bình thường), `permissions`, `jobs`.
→ **PASS, YAML hợp lệ**.

Đọc trực tiếp bước mới "Tu kiem chung ISO ngay tren runner" (dòng 61-114): xác nhận đúng
các tuyên bố của ISOVERIFY —
- Nằm đúng vị trí: sau step "Collect ISO + checksum + log", trước step
  "Upload artifact" (dòng 116+).
- `if: always()`, và khi không có ISO (`ISO=""`) thì ghi `verified_on_boot: NO` rồi
  `exit 0` ngay, không chạy tiếp cài đặt công cụ (no-op sạch).
- Cài `file genisoimage xorriso` qua apt-get khi có ISO; chạy `file`, `isoinfo -d -i`,
  `xorriso -indev ... -toc`, `sha256sum`, ghi tất cả vào `out/iso-verify.txt` và
  tee thêm vào `/mnt/nm/build.log`.
- Chỉ in "KET LUAN: tim thay dau hieu bootable" khi grep thấy "El Torito" hoặc
  "bootable" trong output thật của các lệnh trên; nhánh else in CẢNH BÁO rõ, không
  tự nhận bootable.
- **Mọi nhánh output đều có dòng `verified_on_boot: NO`** (kể cả nhánh "tìm thấy dấu
  hiệu bootable" — chỉ nói "xác nhận cấu trúc trên CI", không tự nhận đã boot thật).
- `out/iso-verify.txt` nằm trong `out/` nên tự động được step "Upload artifact" hiện
  có (upload cả thư mục `out/`) gom theo, không cần sửa step upload.

→ **PASS**, logic/vị trí khớp đúng mô tả, không có fabricate "bootable" khi chưa có evidence.

## Tổng kết

| # | Hạng mục | Kết quả |
| --- | --- | --- |
| 1 | pytest full suite | PASS (800 passed, 1 skipped ≥ 772 yêu cầu, 0 fail) |
| 2 | ruff/black/mypy trên src | PASS (0 lỗi cả 3 công cụ) |
| 3 | configparser cho mọi KDE config + mimeapps.list + .desktop | PASS (7 file INI + 1 .desktop, không lỗi) |
| 4 | bash -n hook + quét curl\|bash/eval | PASS cú pháp + không có pattern nguy hiểm |
| 5 | Không có tài sản Microsoft độc quyền | PASS (chỉ có comment nhắc ràng buộc, font/wallpaper đều tự do/tự soạn) |
| 6 | YAML build-iso.yml hợp lệ + nội dung step mới đúng như khai báo | PASS |

**KHÔNG có defect mới nào được phát hiện trong phạm vi 6 lệnh kiểm được giao.**

Một gap liên-luồng đã biết (không phải defect do tôi tìm ra, cả DESKTOP và WELCOME đã tự
khai báo "blocked" trong báo cáo của họ) được xác nhận lại ở đây để chốt sổ: hook `0300` sẽ
làm `lb build` thất bại có chủ đích vì `includes.chroot/opt/namios/namios_welcome-src/`
chưa được đồng bộ từ `src/namios_welcome/` — cần bước đồng bộ (ngoài phạm vi sở hữu
file của VERIFY) trước khi build ISO phát hành thật.
