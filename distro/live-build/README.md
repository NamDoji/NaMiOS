# NaMiOS — cấu hình Debian live-build (M3-PREP)

**verified_on_host: NO.** Toàn bộ nội dung thư mục này là CẤU HÌNH CHƯA
THỰC THI, soạn trước để chạy trên một build host Linux amd64 thật (có
`live-build`/`debootstrap`/`xorriso`/`qemu`+`/dev/kvm`) sau này. Container
phát triển hiện tại là Debian 12, **thiếu toàn bộ** công cụ trên và
**không có** `/dev/kvm` — xem `CLAUDE.md`, `docs/_m0_inventory_raw.md`,
`docs/adr/0002-nen-debian-13.md`. Không có file `.iso` nào được tạo ra từ
thư mục này; không đổi đuôi archive thành `.iso`; không tuyên bố đã
build/boot bất cứ thứ gì khi chưa chạy trên host thật.

Liên quan requirement: BUILD-001, BUILD-002, BUILD-003, BUILD-004 (độ ưu
tiên P0/P0/P0/P1), INSTALL-001/002 (boot test), VN-001/002/005, LIC-006
(§14, §5.1, §5.2 `docs/specs/DAC_TA_HE_DIEU_HANH.md`), ADR 0002.

## 1. Cấu trúc thư mục và ý nghĩa từng phần

```
distro/live-build/
  README.md                  — file này (runbook)
  build-manifest.yaml         — khung pin snapshot/kernel/package (placeholder, điền trên host thật)
  .gitignore                  — loại trừ output build (chroot/, cache/, binary*, *.iso, *.log, ...)
  auto/
    config                    — script gọi `lb config noauto ...` với tham số cố định (idiom chuẩn Debian Live Manual)
    clean                     — script gọi `lb clean noauto ...`
  config/
    package-lists/*.list.chroot   — danh sách gói apt theo nhóm (desktop/locale/font/office/in ấn/wine)
    hooks/normal/*.hook.chroot    — hook chạy TRONG chroot lúc build (locale, timezone, Fcitx5 mặc định)
    includes.chroot/...           — file tĩnh chèn thẳng vào ảnh (branding text placeholder, KHÔNG icon/font/âm thanh Microsoft)
```

Live-build (khi có binary `lb` trên host thật) sẽ tự tạo thêm các thư mục
sinh ra lúc build (`chroot/`, `cache/`, `binary*`, `.build/`, `*.iso`) —
những thư mục đó KHÔNG commit vào repo (xem `.gitignore` trong thư mục
này). Tư thế quản lý này theo đúng khuyến nghị "Managing a configuration
with Git" của Debian Live Manual [S10]: giữ `auto/` + `config/` trong git,
build lại bằng `lb clean` rồi `lb config` (qua `auto/config`) rồi `lb
build` mỗi lần cần ISO mới.

### `auto/config`

Gọi `lb config noauto --architectures amd64 --distribution trixie
--archive-areas "main contrib non-free-firmware" --binary-images
iso-hybrid --debian-installer none --bootappend-live "boot=live
components locales=vi_VN.UTF-8 timezone=Asia/Ho_Chi_Minh" "${@}"`.

- `--distribution` lấy từ biến môi trường `NAMIOS_LB_DISTRIBUTION` nếu có
  (mặc định `trixie` theo ADR 0002). Không hardcode số point-release —
  BUILD-002 yêu cầu ghi lại point release **thật** đo được trên host vào
  `build-manifest.yaml` sau khi build, không suy ra trước.
- `--archive-areas` gồm `non-free-firmware` (LIC-006): cần cho firmware
  không tự do của một số thiết bị WiFi/GPU trên máy pilot thật (danh sách
  thiết bị cụ thể **TBD**, chốt khi có máy pilot — xem §26 BLOCKED trong
  `docs/STATUS.md`). Đây là lý do rõ ràng, không mặc định tuyên bố toàn bộ
  NaMiOS là "100% phần mềm tự do" khi còn thành phần không tự do trong
  ảnh.
- Nếu đặt biến môi trường `NAMIOS_APT_SNAPSHOT_URL` (ví dụ một URL
  `snapshot.debian.org/archive/debian/<timestamp>/`), script sẽ truyền
  thêm `--mirror-bootstrap`/`--mirror-binary` trỏ tới URL đó để pin
  snapshot (BUILD-002). KHÔNG có giá trị mặc định cố định trong script —
  timestamp snapshot phải do người build chốt và tự chịu trách nhiệm ghi
  lại trong `build-manifest.yaml`; không được bịa một timestamp để "có vẻ
  pin".
- Không `curl|bash`, không tải/thực thi nội dung từ xa trong script này.

### `auto/clean`

Gọi `lb clean noauto "${@}"` — dọn chroot/cache cũ trước khi build lại
sạch. Không xoá file nguồn trong `config/`.

### `config/package-lists/*.list.chroot`

Mỗi file là MỘT nhóm gói Debian thật (tên gói theo hiểu biết về Debian
13 trixie tại thời điểm soạn tài liệu). **Mọi tên gói PHẢI được xác nhận
lại bằng `apt-cache show <tên gói>` trên build host thật trước khi build**
(điều kiện spike trong ADR 0002) — đây là lý do mỗi file đều có dòng
`verified_on_host: NO` ở đầu. Nếu một tên gói không còn đúng trên
snapshot thật, `lb build` sẽ báo lỗi rõ ("unable to locate package") —
đó là thất bại đúng, không phải lỗi quy trình; sửa tên gói rồi build lại,
không tự bỏ qua hay giả định đã cài.

- `0100-desktop-kde.list.chroot` — KDE Plasma + SDDM + Dolphin/Konsole/Kate (§5.1 "Desktop").
- `0200-locale-vi.list.chroot` — `locales`, `tzdata`, Fcitx5 + engine Unikey (VN-001/VN-002).
- `0300-fonts.list.chroot` — font có quyền phân phối, phủ glyph tiếng Việt (VN-005). KHÔNG font Microsoft.
- `0400-office-browser.list.chroot` — LibreOffice (bản thay thế, không phải Microsoft Office — APP-OFF-006) + Firefox ESR (§5.1).
- `0500-print.list.chroot` — CUPS + driver in (hạ tầng chung cho thiết bị in — liên quan DEV-* ở M4, bản thân in ấn cơ bản thuộc §5.1).
- `0600-wine.list.chroot` — gói `wine`/`winetricks` từ Debian (§5.1 "Wine"); KHÔNG cấu hình prefix/app cụ thể ở đây — đó là M2/M4 (`namios-compat`).
- `0900-namios-packages.list.chroot.disabled` — **CHƯA kích hoạt** (đuôi `.disabled` nên `lb` bỏ qua). Giải thích trong file: các metapackage `namios-*` (xem `packaging/debian/`) chưa có `.deb` thật và chưa có apt repo cục bộ nào cho build này trỏ tới; chỉ đổi tên bỏ `.disabled` SAU KHI đã build `.deb` thật và có repo cục bộ hợp lệ.

### `config/hooks/normal/*.hook.chroot`

Hook chạy **trong chroot lúc build ảnh** (không chạy trên máy người dùng
cuối, không chạy ở thời điểm boot Live). Tất cả hook ở đây đã được
review theo yêu cầu CLAUDE.md: không `curl|bash`, không tải script tùy ý,
có `set -euo pipefail`, chỉ dùng công cụ đã cài qua package-lists
(`locales`, `tzdata`, `fcitx5`, `im-config`), thoát non-zero rõ ràng nếu
thiếu điều kiện tiên quyết (không âm thầm bỏ qua).

- `0100-locale-vi.hook.chroot` — bật locale `vi_VN.UTF-8`, set `LANG` mặc định (VN-001).
- `0110-timezone.hook.chroot` — set timezone mặc định `Asia/Ho_Chi_Minh` (VN-001); người dùng đổi được sau khi cài.
- `0200-fcitx5-default-im.hook.chroot` — đăng ký Fcitx5 là input method mặc định + khung profile Unikey (Telex) cho user mới trong `/etc/skel`. **Cú pháp file `profile` của Fcitx5 trong khối này là khung theo tài liệu upstream, CHƯA xác nhận trên gói Debian 13 thật** — phải kiểm thử Telex/VNI thật trên máy có desktop session (VN-002) trước khi coi là đạt.

Thứ tự số thứ tự (0100/0110/0200) có ý nghĩa: live-build chạy hook theo
thứ tự ký tự tên file trong `config/hooks/normal/`.

### `config/includes.chroot/...`

File tĩnh chèn thẳng vào ảnh, không cần logic. Chỉ gồm text do NaMiOS tự
viết (không sao chép icon/font/âm thanh của Microsoft hay bên thứ ba
không có quyền phân phối):

- `etc/namios-release` — placeholder thông tin phiên bản/build/commit, tất cả giá trị còn `TBD`; **PHẢI điền giá trị thật trước khi phát hành** (BUILD-002) — không ship bản có `TBD` ra ngoài lab.
- `etc/issue`, `etc/motd` — banner văn bản tiếng Việt đơn giản, không chứa asset nhị phân.
- `usr/share/namios-branding/README-PLACEHOLDER.md` — ghi rõ còn thiếu asset branding thật (logo, icon set, splash) và điều kiện giấy phép bắt buộc trước khi thêm.
- `usr/share/backgrounds/namios/README-PLACEHOLDER.md` — tương tự, cho wallpaper mặc định Plasma.

### `build-manifest.yaml`

Khung ghi lại snapshot OS/kernel/package versions, tool versions
(`lb`/`debootstrap`/`xorriso`...), source commit, và danh sách artifact
bắt buộc theo BUILD-003 (ISO, SHA256SUMS, chữ ký tách rời, SBOM, package
list, source references, build log, test report, release notes). **Toàn
bộ giá trị hiện là placeholder `"TBD: chốt trên host"` hoặc `null`** —
không được điền giá trị giả để "trông như đã build". Sau khi build thật
trên host hợp lệ, cập nhật file này (hoặc một bản sinh tự động tương
đương) với giá trị đo được thật, rồi coi đó là bằng chứng (không phải
file này ở trạng thái hiện tại).

## 2. Các bước chạy THẬT trên build host (chưa chạy ở đây)

Điều kiện tiên quyết: build host Linux amd64 (khuyến nghị Debian 13
trixie sạch), có `sudo`, `/dev/kvm` cho boot-test, và các gói
`live-build debootstrap xorriso fakeroot squashfs-tools qemu-system-x86
ovmf`. Có thể dùng `scripts/preflight-build-host.sh` (ở gốc repo) để tự
kiểm tra điều kiện này trước — script đó độc lập, do phần runbook build
host sở hữu; `scripts/build-iso.sh` ở đây sẽ tự gọi nó nếu có.

```sh
# 1) Kiểm tra điều kiện host (tùy chọn, build-iso.sh cũng tự gọi lại bước này)
scripts/preflight-build-host.sh

# 2) Build ISO (chạy từ gốc repo; script tự cd vào distro/live-build)
scripts/build-iso.sh --output-dir build/out

# 3) Boot-test ISO vừa sinh ra, Live mode, KHÔNG ghi đĩa
scripts/boot-test-qemu.sh --iso build/out/<ten-file>.iso
```

Nếu muốn chạy `lb` trực tiếp (không qua wrapper) để debug:

```sh
cd distro/live-build
sudo ./auto/clean --purge   # chỉ khi cần build sạch lại từ đầu
./auto/config
sudo lb build 2>&1 | tee build.log
sha256sum *.iso > SHA256SUMS
```

`lb build` cần quyền root để tạo chroot/debootstrap — đây là yêu cầu bình
thường của live-build, KHÔNG phải vi phạm quy tắc "không chạy Wine bằng
root" (quy tắc đó áp dụng cho runner Wine ở M2/M4, không áp dụng cho bước
build ảnh ở M3).

## 3. Trạng thái artifact theo BUILD-003 (hiện tại)

| Artifact | Trạng thái |
| --- | --- |
| ISO | chưa sinh |
| SHA256SUMS | chưa sinh |
| Chữ ký tách rời | chưa có — chỉ ký bằng dev key có nhãn rõ trong lab; key production do maintainer giữ riêng, không có trong repo |
| SBOM (SPDX/CycloneDX) | chưa sinh |
| Package list | chưa sinh (sẽ xuất từ `lb` sau khi build) |
| Source references | commit hiện tại của repo tại thời điểm build (ghi trong `build-manifest.yaml`) |
| Build log | chưa có |
| Test report | chưa có — xem `scripts/boot-test-qemu.sh` cho boot-test; test ứng dụng/app sâu hơn thuộc M4 |
| Release notes | chưa viết |

## 4. Nguồn

- [S09] Debian 13 trixie — https://www.debian.org/releases/trixie/
- [S10] Debian Live Manual (Managing a configuration with Git; hooks;
  package-lists; includes.chroot) —
  https://live-team.pages.debian.net/live-manual/html/live-manual.en.html
