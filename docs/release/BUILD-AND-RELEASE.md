# BUILD-AND-RELEASE — NaMi 2026.11 "Đông Sơn" (alpha)

> **Loại tài liệu:** gói bàn giao HIG Phụ lục 22 §13.6 ("Hướng dẫn build, cài thử trên VM,
> nâng cấp từ bản cũ, gỡ branding và hoàn nguyên"). **Phạm vi sở hữu: chỉ `docs/release/`.**
> Không `git commit`/push. **`verified_on_host: NO` cho mọi bước dưới đây** — không một ISO
> nào của release này đã được build/boot/cài thành công trên host thật trong phiên soạn tài
> liệu này. Mọi lệnh liệt kê là lệnh **thật có trong repo** (không bịa), nhưng **chưa chạy
> xong lần nào** trừ khi ghi rõ khác.
>
> Nguồn đọc: `distro/live-build/README.md`, `scripts/build-iso.sh`, `scripts/boot-test-qemu.sh`,
> `scripts/preflight-build-host.sh`, `distro/live-build/ci-build.sh`,
> `.github/workflows/build-release.yml`, `docs/adr/ADR-0020-os-update-rollback-mechanism.md`,
> `docs/adr/0009-quyen-so-huu-va-thuong-hieu.md`, `docs/branding/TRADEMARK-LICENSE-COMPLIANCE.md`.

## 0. Phiên bản đang nói tới

| Trường | Giá trị | Nguồn |
| --- | --- | --- |
| Tên hiển thị | `NaMi` (`NAME=`/`PRETTY_NAME=`) | `.../etc/os-release` |
| Phiên bản | `2026.11` ("Đông Sơn") | `.../etc/os-release` `VERSION_ID`, `.../etc/namios-release` `NAMIOS_VERSION` |
| Kênh | `alpha` | `.../etc/namios-release` `NAMIOS_CHANNEL` |
| Nền tảng gốc | Debian 13 "trixie" (ID_LIKE=debian) | ADR 0002, `.../etc/os-release` |
| ID kỹ thuật | `namios` (giữ nguyên, KHÔNG đổi theo tên hiển thị "NaMi" — field kỹ thuật cho script/tool) | `.../etc/os-release` `ID=` |
| Build date / commit | **TBD — tự đóng dấu trên host lúc build thật** (chưa có giá trị thật) | `.../etc/namios-release` `NAMIOS_BUILD_DATE_UTC`/`NAMIOS_SOURCE_COMMIT` |
| Tác giả | Đỗ Chí Cường & Đỗ Bảo Nam | `.../etc/namios-release` `NAMIOS_AUTHORS` |

## 1. Build ISO

### 1.1 Build cục bộ trên build host thật (đường chính)

**Điều kiện host (bắt buộc, do `scripts/preflight-build-host.sh` kiểm tra thật):** Linux
amd64, khuyến nghị Debian 13 trixie sạch, `sudo`, cờ ảo hoá CPU (vmx/svm) + `/dev/kvm` đọc/ghi
được, RAM ≥16GB (ngưỡng mặc định, chỉnh được), disk trống ≥100GB, các lệnh `lb`
(live-build)/`debootstrap` hoặc `mmdebstrap`/`xorriso`/`mksquashfs`/`fakeroot`/
`qemu-system-x86_64`/firmware OVMF. Container phát triển hiện tại (Debian 12, không
`/dev/kvm`) **không đạt** — đây là kết quả ĐÚNG của script, không phải lỗi.

```sh
# 1) Kiểm tra host có đủ điều kiện không (tự kiểm JSON hoặc bảng text)
scripts/preflight-build-host.sh
# hoặc: scripts/preflight-build-host.sh --json

# 2) Build ISO (script tự gọi lại preflight, tự cd vào distro/live-build)
scripts/build-iso.sh --output-dir build/out
#   tuỳ chọn: --clean (lb clean --purge trước khi build lại từ đầu)
#             --snapshot-url <snapshot.debian.org/.../> (pin apt snapshot, BUILD-002)
#             --sign-key-id <KEYID> (ký SHA256SUMS bằng dev GPG key đã có sẵn trong keyring —
#                                    script KHÔNG tạo/lưu key nào; KHÔNG dùng production key)

# 3) Boot-test ISO vừa sinh ra (xem §2)
scripts/boot-test-qemu.sh --iso build/out/<timestamp>/<ten-file>.iso
```

Debug thủ công không qua wrapper (tương đương bước trong `distro/live-build/README.md`):

```sh
cd distro/live-build
sudo ./auto/clean --purge   # chỉ khi cần build sạch lại từ đầu
./auto/config
sudo lb build 2>&1 | tee build.log
sha256sum *.iso > SHA256SUMS
```

Exit code của `build-iso.sh`: `0` = ISO + `SHA256SUMS` sinh ra thật; `3` = host thiếu điều
kiện (dừng, không build); `4` = `lb build` chạy nhưng thất bại thật (không giả lập ISO).
Script **tự in** danh sách việc còn thiếu trước khi coi là artifact phát hành (điền
`build-manifest.yaml` bằng giá trị thật, viết test report, bổ sung SBOM/chữ ký nếu thiếu).

### 1.2 Build qua GitHub Actions (`build-release.yml`)

Workflow `build-release` (`.github/workflows/build-release.yml`) là **dispatch thủ công**
(`workflow_dispatch`, cần quyền `contents: write`), chạy trên `ubuntu-latest`, timeout 120
phút:

1. Biên dịch lớp phủ dịch `vi_NM` (`scripts/build-l10n-overlay.sh`, `.po` → `.mo`) trước khi
   stage.
2. Dọn đĩa runner (~25GB) rồi copy `distro/live-build` sang `/mnt/nm/lb` (đĩa lớn hơn).
3. Chạy `distro/live-build/ci-build.sh` **bên trong container `debian:trixie --privileged`**
   — đây là build host Linux amd64 thật (không phải giả lập): `ci-build.sh` tự cài
   `live-build`, mở `contrib non-free non-free-firmware`, **pre-validate từng dòng gói** của
   `config/package-lists/*.list.chroot` bằng `apt-cache show` thật (dòng nào không có trong
   trixie bị comment `# DROPPED-NOT-IN-TRIXIE:` + log ra, **không** âm thầm bỏ qua), rồi
   `./auto/config` + `lb build`.
4. Gom ISO, tính `sha256sum`, rồi **chia thành các phần <2GB** (`split -b 1900m`) vì GitHub
   Release giới hạn 2GiB/file (ISO NaMiOS ~2.8GB). File nguyên bị xoá, chỉ giữ `*.part*` +
   `.sha256` + công cụ ghép 1-chạm (`release-helpers/ghep-iso.bat`/`.sh` +
   `README-TAI-ISO.txt`).
5. Phát hành lên GitHub Release tag `iso-<YYYYMMDD>` (`gh release create`/`upload`), ghi chú
   cách ghép file (`cat *.part* > ten.iso && sha256sum -c`, hoặc double-click `.bat`/`.sh`).

Cách chạy thủ công: GitHub → Actions → "build-release" → Run workflow (nhập "Ghi chú phát
hành" tuỳ chọn). **Không** có lịch tự động (chỉ dispatch), **không** dùng Actions artifact
(tránh đụng quota repo private).

## 2. Boot-test ISO trên QEMU

`scripts/boot-test-qemu.sh --iso <path>` boot ISO ở chế độ **Live, KHÔNG gắn ổ cứng ảo nào**
(chỉ `-cdrom` read-only) — đúng tinh thần "Live mode thử không ghi ổ trong" (INSTALL-001).

```sh
# UEFI (mặc định, theo yêu cầu INSTALL-002), có màn hình đồ hoạ
scripts/boot-test-qemu.sh --iso build/out/<timestamp>/<ten-file>.iso

# Headless + timeout (dùng cho kiểm tra tự động/CI)
scripts/boot-test-qemu.sh --iso <iso> --headless --timeout 120

# Không có /dev/kvm (TCG phần mềm — CHẬM, chỉ kiểm cấu trúc boot, KHÔNG đại diện hiệu năng thật)
scripts/boot-test-qemu.sh --iso <iso> --no-kvm
```

Exit code `3` = BLOCKED (thiếu `qemu-system-x86_64`/KVM/OVMF — không giả lập "đã boot").
Script tự đối chiếu `SHA256SUMS` cạnh ISO nếu có (chỉ cảnh báo, không chặn cứng).

**Quan trọng — đọc đúng giới hạn của script:** exit code `0` chỉ xác nhận **QEMU khởi động và
thoát được**. Nó **không** suy ra "cài/boot Live thành công về mặt chức năng" — kết luận đó
phải do người kiểm thử quan sát màn hình/console thật và ghi vào test report (yêu cầu HIG
§13.5). Những điểm cần nhìn trực tiếp khi boot-test (theo `docs/design/P0-UI-AUDIT.md` §6
"CANNOT-VERIFY-WITHOUT-BOOT-TEST"): GRUB/isolinux boot menu lên đúng, Plymouth splash
`namios` hiện, SDDM đăng nhập (autologin ở cấu hình alpha hiện tại), desktop Plasma lên không
treo, panel căn giữa kiểu Win11 hiển thị đúng, gõ tiếng Việt fcitx5 hoạt động, màu/Selection
hiển thị đúng hướng (gold nền/navy chữ).

## 3. Cài thử — luồng Calamares cần xác minh

Installer = **Calamares** + `calamares-settings-debian`, branding `namios`
(`distro/live-build/config/includes.chroot/etc/calamares/branding/namios/` — có
`branding.desc`, `show.qml`, `logo.png`, `bg-welcome.png`, `bg-progress.png`,
`welcome.png`, `app-{writer,calc,impress}.png`). `branding.desc` đã đồng bộ version
"2026.11 (Đông Sơn)" (commit `ff7928d`).

Danh sách cần xác minh trên host thật khi chạy thử Calamares (chưa làm, TODO):

1. **Bước xác nhận đúng thiết bị trước khi ghi đĩa** (INSTALL-001) — Calamares mặc định có
   màn hình xác nhận phân vùng; chưa xác nhận NaMiOS có **2 bước xác nhận xoá đĩa** riêng theo
   yêu cầu HIG §8.1 (`docs/design/HIG-ADOPTION-VERDICT.md` khuyến nghị thứ tự việc #4) — hiện
   dùng mặc định `calamares-settings-debian`/`modules/partition.conf`.
2. **GRUB offline** — `package-lists/0700-installer.list.chroot` đã bake sẵn
   `grub-pc`/`grub-pc-bin`/`grub2-common`/`grub-efi-amd64-bin` vào squashfs để Calamares
   **không cần tải qua mạng** lúc cài (vá lỗi pilot 10/11/2026: cài BIOS trên máy thật từng
   thất bại vì Calamares cố tải `grub-pc` từ `deb.debian.org` không có mạng). **Chưa build +
   cài thử lại để xác nhận Calamares không còn tải grub từ mạng** (`verified_on_host: NO`).
3. **Secure Boot — CHƯA hỗ trợ.** Chỉ có `grub-efi-amd64-bin` (module, không ký); thiếu
   `shim-signed` + `grub-efi-amd64-signed`. Máy UEFI bật Secure Boot sẽ **không boot được** ISO
   này; cần tắt Secure Boot ở BIOS/UEFI khi cài thử, hoặc tách ảnh BIOS/UEFI-signed riêng
   (việc sau, chưa làm).
4. **Phân vùng = ext4** (mặc định Debian qua `calamares-settings-debian`, repo không có file
   cấu hình phân vùng tuỳ biến — xem ADR-0020 §Bối cảnh). Không phải btrfs/A-B.
5. Sau khi cài xong, đối chiếu bảng branding ở `docs/design/P0-UI-AUDIT.md` §2.1 (SDDM dùng
   PNG logo sen cũ — chưa tái xuất trống đồng; Plymouth/Calamares PNG cần xác minh phiên bản
   v3) ngay trên máy đã cài, không chỉ trên Live.

## 4. Nâng cấp từ bản NaMi/NaMiOS cũ hơn

**Trạng thái cơ chế: `specified`/`partial` (ADR-0020), KHÔNG có `namios-update-service` thật
chạy trên máy nào.** Cơ chế đã **chốt thiết kế** (không phải đã triển khai xong):

```
check → verify (apt GPG + release-index kiểu TUF) → preflight (storage/power/network)
      → migration-guard (backup đã kiểm khôi phục) → Timeshift snapshot (hook 0640)
      → staged apt-apply → arm GRUB default = bản mới (giữ entry cũ)
      → reboot → boot-health gate (6 probe) → đạt: confirm · fail: GRUB previous-entry + timeshift --restore
```

Nền đã có trong repo (đọc được, chưa nối thành dịch vụ thật):
- Hook `0640-update-recovery.hook.chroot` (ADR 0014): apt `Pre-Invoke` tạo Timeshift snapshot
  trước mỗi transaction + `namios-health-check.sh`/`.service` + mục GRUB "Khôi phục".
- Package-list `0640-update-recovery.list.chroot` (`timeshift`, `needrestart`).
- Prototype `tools/update-center-prototype/` (66 test pytest: `update_service.py`,
  `staged_deploy.py`, `boot_health.py`, `fault_inject.py`) — **mô phỏng mức thư mục/VM, chưa
  nối apt/bootloader thật**.
- UI: Plasma Discover + PackageKit (trên apt/dpkg thật) — đây là đường **nâng cấp gói thông
  thường đang dùng được hôm nay** cho người dùng cuối (`sudo apt update && sudo apt
  full-upgrade`, hoặc qua Discover), **không** có changelog tiếng Việt tự động và **không** có
  staged-rollback tự động đi kèm.

**TODO / manual cho tới khi U19 (nhóm B — máy thật) đạt:** nâng cấp giữa các bản ISO NaMi hiện
chỉ nên thực hiện bằng:
1. `sudo timeshift --create --comments "truoc khi nang cap NaMi"` (nếu đã cấu hình Timeshift)
   **trước khi** `apt upgrade`, thủ công — vì `namios-update-service` thật chưa tồn tại để tự
   làm bước này cho người dùng.
2. `sudo apt update && sudo apt full-upgrade` (hoặc Discover) để lấy gói mới trong cùng nhánh
   trixie; **không** có cơ chế "ISO sang ISO" (cài đè) nào khác ngoài cài lại từ ISO mới +
   restore `/home` thủ công.
3. Sau nâng cấp, tự kiểm `dpkg --audit` sạch + `systemctl is-system-running` — đây chính là 2
   trong 6 probe mà `boot_health.py` dự kiến tự động hoá sau này.

## 5. Rollback

Hai lớp rollback đã **thiết kế**, một lớp **có hạ tầng gói sẵn**, chưa lớp nào **nối máy
thật**:

| Lớp | Cơ chế | Trạng thái |
| --- | --- | --- |
| OS (ảnh hệ thống) | Timeshift snapshot (rsync, ext4) trước-update (hook 0640) + GRUB previous-entry fallback + boot-counter kiểu greenboot | `specified`/`partial` — gói đã cài, **chưa nối `namios-health-check` → GRUB tự fallback thật trên máy** |
| Dữ liệu người dùng | Kup + bup backup `/home` versioned (hook 0620-backup, tách quyền) | gói đã cài; **chưa test dry-run restore thật** |
| Thủ công (luôn dùng được, không chờ U19) | `sudo timeshift --restore` (chọn snapshot trước khi lỗi) rồi reboot; hoặc chọn mục GRUB "NaMi — Khôi phục (recovery)" nếu có | thao tác apt/Timeshift chuẩn, không đặc thù NaMi |

**Sự thật quan trọng (ADR-0020, không được quảng cáo khác đi):** rollback **không nguyên tử**
(không phải A-B/OSTree) — mất điện giữa một transaction dpkg phục hồi bằng snapshot/`dpkg
--configure -a`, không "bật lại tức thì". **Rollback OS ≠ khôi phục dữ liệu ứng dụng** —
snapshot hệ thống loại trừ `/home`; không được để người dùng hiểu nhầm "rollback xong là dữ
liệu tự về". Nếu Timeshift chưa cấu hình, lần đó **không có điểm rollback** (snapshot lỗi
`|| true`, không chặn vá bảo mật, nhưng health-check phải nói rõ cho người dùng thấy, không
giấu).

## 6. Gỡ branding NaMi / hoàn nguyên về gốc (HIG §13.6)

**Không có script/cơ chế tự động "gỡ branding một lệnh" trong repo ở thời điểm này —
TODO / thủ công.** Lý do: branding NaMi được **bake thẳng vào ảnh lúc build** (qua
`config/hooks/normal/*.hook.chroot` sửa file hệ thống trong chroot và
`config/includes.chroot/...` chèn file tĩnh), **không** phải một lớp cấu hình runtime có thể
tắt bằng một cờ. Gỡ hoàn toàn nghĩa là build lại một ISO khác (hoặc sửa tay từng mục dưới đây
trên máy đã cài) — tham chiếu bảng đầy đủ ở `docs/release/BRANDING-MAP-OLD-NEW.md`:

| Bề mặt | Việc cần làm để hoàn nguyên | Rủi ro/lưu ý |
| --- | --- | --- |
| `/etc/os-release`, `/etc/lsb-release`, `/etc/issue*`, `/etc/motd` | Phục hồi về bản gốc Debian (gói `base-files` cung cấp `/etc/os-release`/`/etc/issue` mặc định) — `sudo apt install --reinstall base-files` **có thể** phục hồi phần Debian gốc nhưng NaMi đã ghi đè các file này trực tiếp trong `includes.chroot` nên cần đối chiếu/khôi phục tay nếu `dpkg` không coi là "owned" bởi gói | Chưa thử nghiệm; file do `includes.chroot` chèn không nằm trong gói `.deb` nào nên `apt`/`dpkg` **không tự quản lý được việc gỡ** |
| SDDM theme (`namios`) | Đổi `/etc/sddm.conf` (hoặc file trong `/etc/sddm.conf.d/`) `Current=` về `breeze` (theme Breeze có sẵn cùng KDE Plasma) | An toàn, không cần build lại |
| Plymouth boot splash (`namios`) | `sudo plymouth-set-default-theme -R <theme-goc>` (ví dụ `spinner`/`breeze` nếu có cài) | An toàn, cần theme gốc còn cài song song |
| Icon theme (`NaMiOS-Lotus`) | `kdeglobals [Icons] Theme=` đổi về `breeze` | Static config, an toàn |
| Color scheme (`NaMiOS.colors`/`NaMi-HighContrast.colors`) | `kdeglobals [General] ColorScheme=` đổi về `BreezeLight`/`BreezeDark` | Static config, an toàn |
| Wallpaper mặc định (Vịnh Hạ Long + bộ 20 ảnh VN) | Đổi `plasma-org.kde.plasma.desktop-appletsrc` `Image=` về wallpaper Breeze mặc định | Static config |
| `.desktop` Name/Comment đổi nhãn "NaMi*" (`0130`, `0450`–`0455` hooks) | Mỗi hook chỉ đổi khoá `Name=`/`Name[vi]=`/`Comment[vi]=` trong file `.desktop` hệ thống — hoàn nguyên = ghi lại `Name=` gốc (vd. "Dolphin", "Ark", "VLC media player") cho từng file bị 6 hook này đụng tới; **không có file "gốc" được repo lưu lại song song** để diff tự động, phải tra `Name=` gốc theo tên gói (`apt-cache show <goi>` hoặc tải lại `.desktop` gốc từ gói `.deb`, như cách `TRADEMARK-LICENSE-COMPLIANCE.md` §1 đã làm) | Cao nhất trong bảng này — 6 hook + nhiều app bị đụng, chưa có tooling hoàn nguyên hàng loạt |
| Taskbar căn giữa / nút cửa sổ góc phải (`appletsrc`/`kwinrc`) | Xoá 2 applet `panelspacer` vừa thêm + trả `AppletOrder` về cũ; xoá dòng `ButtonsOnRight=IAX` trong `kwinrc` | Static config |
| Panel thickness=36 | Xoá khoá `[PlasmaViews][Panel 1] thickness=36` (panel về mặc định Plasma) | Static config |
| Logo/icon raster (start-here-namios, favicon, hicolor) | Cài đè gói icon theme gốc (`breeze-icon-theme`) và set lại `Icons Theme=` ở trên — icon app riêng lẻ của NaMi (ví dụ icon menu Start) không có "bản gốc Debian" tương ứng để phục hồi, chỉ có thể **xoá** | Không nghịch đảo 1-1 được cho icon tự vẽ |
| nWine / `namios-windows-app`, 4 app Việt (nLịch/Dịch vụ/An toàn/gói ngôn ngữ) | Gỡ gói/`.desktop` tương ứng qua Discover ("Gỡ cài đặt phần mềm", xem `usr/share/namios/docs/GO-CAI-DAT.md`) nếu muốn bỏ hẳn tính năng, không chỉ đổi nhãn | An toàn — đây là app riêng, không phải rebrand app có sẵn |

**Đường hoàn nguyên "sạch nhất" hiện có (khuyến nghị thật sự, không phải lý tưởng hoá):** cài
lại **Debian 13 trixie + task `kde-plasma-desktop`** trực tiếp từ ISO Debian chính thức — vì
NaMiOS/NaMi là bản phân phối lại 100% dựa trên gói Debian/KDE gốc (không build lại
binary nào, xem `docs/branding/TRADEMARK-LICENSE-COMPLIANCE.md` nguyên tắc 1), nên về **mặt
chức năng** không có gì "NaMi-only" ngoài lớp nhãn/cấu hình liệt kê ở bảng trên. Build một ISO
Debian "sạch" luôn cho kết quả hoàn nguyên đầy đủ hơn là gỡ tay từng dòng trong bảng.

## 7. Nguồn

`distro/live-build/README.md` · `scripts/{preflight-build-host.sh,build-iso.sh,
boot-test-qemu.sh}` · `distro/live-build/ci-build.sh` ·
`.github/workflows/build-release.yml` · `docs/adr/ADR-0020-os-update-rollback-mechanism.md` ·
`docs/adr/0014-*` (Timeshift/health-check — tên file đối chiếu trong ADR-0020) ·
`docs/specs/U15C-STAGED-ROLLBACK.md` · `docs/branding/TRADEMARK-LICENSE-COMPLIANCE.md` ·
`docs/design/P0-UI-AUDIT.md` · `distro/live-build/config/includes.chroot/usr/share/namios/
docs/GO-CAI-DAT.md`.
