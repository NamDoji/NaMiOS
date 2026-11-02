# QA — Verify M3-PREP (NaMiOS) — 02/11/2026

Vai trò: VERIFY AN TOÀN + TRUNG THỰC. Không sửa file nào ngoài
`qa/evidence-index/M3-PREP/`. Mọi lệnh dưới đây đã **CHẠY THẬT** trên
container agent hiện tại (Debian 12 bookworm, không `/dev/kvm`), không
phải suy đoán từ đọc code tĩnh — trừ phần "review tay" vì không có
`shellcheck` trên host (đã kiểm chứng ở mục 1).

Phạm vi được bàn giao để verify:
- `scripts/preflight-build-host.sh`, `docs/runbooks/BUILD-HOST-SETUP.md`, `docs/runbooks/README.md` (role RUNBOOK)
- `distro/live-build/**`, `scripts/build-iso.sh`, `scripts/boot-test-qemu.sh`, `packaging/debian/namios-base/**` (role DISTRO)

---

## 1. Review an toàn 3 script shell (set -euo pipefail / không curl|bash / không eval / không wine-root / argv / quote biến)

### 1.1 shellcheck có sẵn trên host?

```
$ command -v shellcheck
$ pip show shellcheck-py
(không có output nào — không có binary 'shellcheck' và không có package shellcheck-py)
```

**Kết quả: KHÔNG có `shellcheck` trên host này.** Theo đúng chỉ dẫn
nhiệm vụ ("nếu có shellcheck trên host thì chạy, không có thì review
tay + ghi rõ"), mục dưới đây là **review tay** từng script, có đối
chiếu bằng `bash -n` (kiểm cú pháp) cho cả 3 script + 2 script `sh`
liên quan trong `distro/live-build/auto/`.

```
$ bash -n scripts/preflight-build-host.sh && echo OK
OK
$ bash -n scripts/build-iso.sh && echo OK
OK
$ bash -n scripts/boot-test-qemu.sh && echo OK
OK
$ bash -n distro/live-build/auto/config && echo OK   # #!/bin/sh, kiểm bằng bash -n chỉ là cú pháp tương đương, không fail
OK
$ bash -n distro/live-build/auto/clean && echo OK
OK
```

### 1.2 Review tay theo từng tiêu chí bắt buộc

| Script | `set -euo pipefail` (hoặc `-eu` cho `/bin/sh`) | `curl\|bash` | `eval` | `shell=True` | wine chạy root | argv-only (case/while trên `"$@"`) | quote biến |
|---|---|---|---|---|---|---|---|
| `scripts/preflight-build-host.sh` | Có, dòng 36: `set -euo pipefail` | Không có | Không có | N/A (bash) | Không gọi `wine` ở đâu cả — chỉ `command -v wine` để **kiểm tra có mặt**, không thực thi | Có — `while [ $# -gt 0 ]; do case "$1" in ...` (dòng 72-128) | Có — mọi mở rộng biến path/giá trị đều trong `"..."` (ví dụ `"$BUILD_DIR"`, `"$2"`); đọc `/etc/os-release` bằng `grep`/`cut`, không `source` |
| `scripts/build-iso.sh` | Có, dòng 41 | Không có | Không có | N/A | Không gọi `wine`; chỉ có 1 dòng comment giải thích lý do `sudo lb build` KHÁC quy tắc "không chạy wine bằng root" (dòng 20-24) — không vi phạm vì không chạy wine | Có — `while [ $# -gt 0 ]; do case "$1" in ...` (dòng 86-115) | Có — `"${LIVE_BUILD_DIR}"`, `"${SIGN_KEY_ID}"`, lệnh con gọi bằng mảng `"${SUDO_PREFIX[@]}"` không nối chuỗi shell |
| `scripts/boot-test-qemu.sh` | Có, dòng 41 | Không có | Không có | N/A | Không gọi `wine` | Có — `while [ $# -gt 0 ]; do case "$1" in ...` (dòng 88-124) | Có — toàn bộ tham số QEMU build bằng mảng `QEMU_ARGS+=(...)`, không ghép chuỗi rồi `eval`/`sh -c` |
| `distro/live-build/auto/config` | `set -eu` (dòng 31) — **không có `pipefail`**, nhưng `/bin/sh` (dash) không hỗ trợ `pipefail` và script không dùng pipe nào cần bắt lỗi giữa đường → không phải vi phạm thực chất, chỉ là giới hạn của `/bin/sh` so với `bash`. Tham số `lb config` xây bằng `set -- ... "${@}"` (mở rộng danh sách, không `eval`) | Không có | Không có | N/A | Không gọi `wine` | Nhận biến môi trường `NAMIOS_LB_DISTRIBUTION`/`NAMIOS_APT_SNAPSHOT_URL`, không ghép vào chuỗi shell thực thi — truyền trực tiếp cho `lb config "$@"` qua `exec` | Có — `"${DISTRIBUTION}"`, `"${NAMIOS_APT_SNAPSHOT_URL}"` đều trong `"..."` |
| `distro/live-build/auto/clean` | `set -eu` (dòng 15), lý do như trên | Không có | Không có | N/A | Không gọi `wine` | `exec lb clean noauto "${@}"` | Có |

**Kết luận mục 1: KHÔNG phát hiện vi phạm nào** trong 5 script trên đối
với bộ tiêu chí an toàn bắt buộc của CLAUDE.md (không `curl\|bash`,
không `eval`/`shell=True`, không chạy `wine` bằng root — vì không script
nào thực thi `wine`, chỉ kiểm tra sự tồn tại —, tham số qua argv, biến
được quote). `auto/config`/`auto/clean` dùng `set -eu` (không có
`pipefail`) nhưng đây là `/bin/sh` (dash, không hỗ trợ `pipefail`) và
không có pipe nào cần theo dõi exit code giữa đường — không coi là
defect, chỉ ghi chú.

---

## 2. Chạy THẬT `scripts/preflight-build-host.sh` trên host hiện tại

### 2.1 Chạy mặc định (human-readable)

```
$ ./scripts/preflight-build-host.sh; echo "EXIT_CODE=$?"
== NaMiOS preflight-build-host.sh ==
Host: 53f331c36bf3 | Kernel: 5.14.0-333.el9.x86_64 | Arch: x86_64 | Thoi diem: 2026-11-02T13:17:49Z
Build dir kiem tra disk: /home/node/.openclaw/workspace/code_projects/namios

MUC                    BAT_BUOC TRANG_THAI CHI_TIET
---                    ---      ---      ---
os_debian13            true     MISSING  Phat hien ID=debian VERSION_CODENAME=bookworm VERSION_ID=12 (khong phai Debian 13 trixie)
arch_amd64             true     OK       uname -m = x86_64
cpu_cores              false    OK       nproc = 4
cpu_virt_flag          true     MISSING  Khong tim thay vmx/svm trong /proc/cpuinfo
dev_kvm                true     MISSING  /dev/kvm khong ton tai tren host nay
ram_total              true     MISSING  MemTotal ~ 7GB (7871948kB), can >= 16GB
disk_free              true     MISSING  Con trong ~ 68GB, can >= 100GB
tool_live_build        true     MISSING  Khong tim thay lenh 'lb'
tool_debootstrap       true     MISSING  Khong tim thay debootstrap hoac mmdebstrap
tool_xorriso           true     MISSING  Khong tim thay lenh 'xorriso'
tool_squashfs          true     MISSING  Khong tim thay lenh 'mksquashfs'
tool_fakeroot          true     MISSING  Khong tim thay lenh 'fakeroot'
tool_qemu              true     MISSING  Khong tim thay lenh 'qemu-system-x86_64'
tool_ovmf              true     MISSING  Khong tim thay file OVMF_CODE*.fd/OVMF.fd
tool_wine              true     MISSING  Khong tim thay lenh 'wine'
tool_winetricks        true     MISSING  Khong tim thay lenh 'winetricks'
not_root               false    OK       UID = 1000
kernel_info            false    OK       uname -r = 5.14.0-333.el9.x86_64

Tong: 18 muc | OK: 4 | WARN: 0 | THIEU (bat buoc): 14
Trang thai tong: not_ready
EXIT_CODE=3
```

(Bản đầy đủ không rút gọn — mỗi dòng MISSING đều có dòng `-> remediation`
kèm theo, đã xem trực tiếp trên terminal, không cắt bỏ nội dung chỉ dẫn.)

**Khớp 100% với `docs/_m0_inventory_raw.md`**: Debian 12 bookworm (không
phải trixie), không `/dev/kvm`, không có `vmx`/`svm` trong `/proc/cpuinfo`
(do là container ảo hoá lồng, không lộ cờ ảo hoá ra guest), RAM 7GB,
disk trống 68GB, thiếu toàn bộ `lb`/`debootstrap`/`xorriso`/`mksquashfs`/
`fakeroot`/`qemu-system-x86_64`/OVMF/`wine`/`winetricks`.
**14/18 mục bắt buộc MISSING → exit 3 → "not_ready" là KẾT QUẢ ĐÚNG**,
không phải lỗi script. Script không crash, không treo, in bảng đầy đủ.

### 2.2 `--json` — JSON hợp lệ, không trộn log vào stdout

```
$ ./scripts/preflight-build-host.sh --json > /tmp/preflight.json; echo "exit=$?"
exit=3
$ python3 -c "import json; d=json.load(open('/tmp/preflight.json')); print('valid JSON, overall_status=', d['overall_status'], 'checks=', len(d['checks']))"
valid JSON, overall_status= not_ready checks= 18
```
→ `python3 json.load` parse thành công, không có log lẫn vào stdout khi dùng `--json`, đúng 18 checks, `overall_status=not_ready` khớp mục 2.1.

### 2.3 `--help`

```
$ ./scripts/preflight-build-host.sh --help; echo "exit=$?"
(in usage đầy đủ)
exit=0
```

### 2.4 Tham số sai

```
$ ./scripts/preflight-build-host.sh --bogus; echo "exit=$?"
Loi: tham so khong ro: --bogus
(usage in ra stderr)
exit=2
```
→ Đúng hợp đồng exit code tài liệu hoá (2 = lỗi tham số).

### 2.5 Gọi gián tiếp qua `scripts/build-iso.sh` (tích hợp thật, không mock)

```
$ ./scripts/build-iso.sh > /tmp/build-iso.out 2>&1; echo "ACTUAL_EXIT=$?"
ACTUAL_EXIT=3
$ tail -5 /tmp/build-iso.out
Trang thai tong: not_ready
=> Host nay CHUA du dieu kien build/boot-test ISO NaMiOS. Xem
   docs/runbooks/BUILD-HOST-SETUP.md de biet lenh cai dat cu the.
[build-iso] LOI: preflight-build-host.sh bao host THIEU dieu kien bat buoc (exit 3).
[build-iso] LOI: KHONG build tiep tren host nay. Xem huong dan khac phuc o output tren.
```
→ `build-iso.sh` gọi `preflight-build-host.sh` thật, nhận đúng exit 3,
tự thoát với exit 3, **KHÔNG** build gì thêm, **KHÔNG** tạo file `.iso`
giả. (Lưu ý: lần đo đầu tiên của tester bị capture nhầm exit code của
`tail` trong pipeline — 0; đã phát hiện và chạy lại không qua pipe để
lấy đúng exit code 3 của `build-iso.sh`, ghi nhận minh bạch tại đây.)

### 2.6 `scripts/boot-test-qemu.sh` — kiểm lỗi cấu hình thật

```
$ ./scripts/boot-test-qemu.sh --iso /tmp/nonexist.iso; echo "exit=$?"
[boot-test] LOI: khong tim thay file ISO: /tmp/nonexist.iso
exit=1
```
→ Đúng hợp đồng (1 = lỗi cấu hình/thiếu file), không crash, không giả
lập "đã boot".

```
$ ./scripts/boot-test-qemu.sh --help
(in usage đầy đủ, exit 0)
```

---

## 3. Kiểm TRUNG THỰC artifact

| Kiểm tra | Lệnh | Kết quả |
|---|---|---|
| Không có file `.iso`/`.img` giả nào trong repo | `find . -iname "*.iso" -o -iname "*.img"` (loại `.git`) | **Không tìm thấy file nào.** |
| `build/` (output dir của `build-iso.sh`) trống | `find build -type f` | Trống — chưa từng build thật, khớp claim. |
| Không có file `.iso`/`.img` untracked lạ | `git status --porcelain \| grep -iE '\.iso\|\.img'` | Không có. |
| `distro/live-build/build-manifest.yaml` ghi rõ chưa build | đọc trực tiếp file | `verified_on_host: false` ở đầu file; mọi field quan trọng (`repo_commit`, `point_release`, `apt_snapshot.*`, `build_host.*`, `tool_versions.*`, `artifacts.*.status: "not_yet_generated"`, `signing.key_fingerprint: null`) đều là placeholder `"TBD: chốt trên host ..."` hoặc `null`/`not_yet_generated` — **không có giá trị bịa**. |
| LIC-006 (non-free-firmware) có ghi chú | đọc `build-manifest.yaml` mục `licensing` + `auto/config` dòng 46 | `auto/config`: `--archive-areas "main contrib non-free-firmware"`; `build-manifest.yaml.licensing.non_free_components_included` giải thích rõ lý do (driver WiFi/GPU pilot) + `claim` nói rõ KHÔNG tuyên bố 100% phần mềm tự do. Đúng LIC-006. |
| Branding không dùng tài sản Microsoft | đọc 2 file `README-PLACEHOLDER.md` + `grep -rni microsoft distro/ packaging/` | Cả 2 placeholder đều **chưa có asset nhị phân thật** (chỉ có text cảnh báo), và đều ghi rõ "TUYỆT ĐỐI KHÔNG sao chép icon/font/âm thanh Microsoft". `grep microsoft` chỉ ra các dòng cảnh báo/giải thích (font list, README, `packaging/debian/namios-base/debian/control`), không có dòng nào *dùng* asset Microsoft. |
| `packaging/debian/namios-base` không claim sở hữu (OWN-001) | đọc `debian/control` | `Description` ghi rõ: "NaMiOS KHONG so huu Debian/KDE/Fcitx5 — day chi la metapackage Depends-only... (OWN-001)"; gói chỉ `Depends:`, không đóng gói lại source bên thứ ba. |
| Secret scan | `grep -rniE "api[_-]?key\|secret\|password\|BEGIN (RSA\|OPENSSH\|PGP) PRIVATE" scripts/ distro/live-build/ packaging/` | Chỉ có 2 dòng comment nói "KHÔNG chứa secret" trong `scripts/make_workflow_fixtures.py` (file cũ, ngoài phạm vi M3-PREP) — **không có secret/key thật nào**. |

**Kết luận mục 3: KHÔNG phát hiện vi phạm trung thực.** Không có ISO/IMG
giả, build-manifest toàn placeholder có nhãn rõ, LIC-006 và quy tắc
branding non-Microsoft được tuân thủ, không có claim sở hữu sai (OWN-001),
không có secret.

---

## 4. Full test suite Python

```
$ /home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
    /home/node/.openclaw/workspace/code_projects/namios/tests -q -p no:cacheprovider
........................................................................ [  9%]
........................................................................ [ 18%]
........................................................................ [ 27%]
........................................................................ [ 37%]
....................................s................................... [ 46%]
........................................................................ [ 55%]
........................................................................ [ 65%]
........................................................................ [ 74%]
........................................................................ [ 83%]
........................................................................ [ 93%]
.....................................................                    [100%]
772 passed, 1 skipped in 6.51s
```

**Khẳng định đúng: 772 passed.** Có thêm 1 skipped (không phải fail):

```
$ ... pytest tests -q -p no:cacheprovider -rs
SKIPPED [1] tests/security/helper/test_fakebus_integration.py:67:
  blocked_external_dependency: cần D-Bus system bus thật + polkitd chạy
  ...; host build hiện tại headless, không có session bus/system
  bus/polkitd (xác nhận bởi docs/_m0_inventory_raw.md + CLAUDE.md).
```

→ Skip này **có từ trước**, lý do `blocked_external_dependency` (thiếu
D-Bus/polkitd thật trên container headless), **không liên quan** đến 2
bộ thay đổi M3-PREP (RUNBOOK/DISTRO chỉ thêm `docs/`, `distro/`,
`packaging/`, `scripts/*.sh` — không đụng `src/` hay test D-Bus). Ghi
đúng theo nguyên tắc "không đổi skipped thành pass".

---

## PASS / DEFECT

**Tổng kết: PASS — không có defect.**

- Mục 1 (an toàn script): PASS — không vi phạm `curl|bash`/`eval`/
  `shell=True`/wine-root/argv/quote. Không có `shellcheck` trên host,
  đã ghi rõ và review tay thay thế theo đúng chỉ dẫn nhiệm vụ.
- Mục 2 (chạy thật preflight + build-iso + boot-test): PASS — script
  không crash, báo đúng các công cụ/điều kiện THIẾU, exit code khớp
  hợp đồng tài liệu hoá trong từng script.
- Mục 3 (trung thực): PASS — không ISO/IMG giả, build-manifest toàn
  placeholder có nhãn, LIC-006 có ghi chú, branding không dùng tài sản
  Microsoft, OWN-001 được tôn trọng, không secret.
- Mục 4 (test suite): PASS — 772 passed, 1 skipped (pre-existing,
  không liên quan M3-PREP, lý do blocked_external_dependency hợp lệ).

**Không có defect nào được phát hiện trong phạm vi verify này.**

Ghi chú trung thực của chính tester: mục 2.5 ban đầu đo exit code qua
một lệnh có `tail` trong pipeline nên lấy nhầm exit code của `tail`
(=0) thay vì của `build-iso.sh`; đã tự phát hiện và đo lại không qua
pipe, xác nhận đúng exit code 3. Ghi lại đầy đủ ở đây để minh bạch quy
trình đo, không phải vì tìm thấy lỗi ở script.
