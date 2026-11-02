# Runbook — Dựng build host cho NaMiOS (build ISO + QEMU boot-test)

**Trạng thái tài liệu:** `verified_on_host: NO` — runbook này CHƯA được chạy hết trên một build host thật. Nội dung là hướng dẫn tái lập + script kiểm tra điều kiện, soạn theo đặc tả (§5.1, §14 BUILD-001..003, INSTALL-001/002) và inventory M0 thật của môi trường hiện tại. Khi chạy trên host thật, cập nhật lại các mục "Kết quả thật" trong runbook này và `docs/STATUS.md`.

**Liên quan:** `docs/specs/DAC_TA_HE_DIEU_HANH.md` §5.1, §5.2, §14; `docs/adr/0002-nen-debian-13.md`; `docs/_m0_inventory_raw.md`; `scripts/preflight-build-host.sh`.

**Sự thật môi trường phát triển hiện tại (02/11/2026, xem `docs/_m0_inventory_raw.md`):** container Debian 12 bookworm, không `/dev/kvm`, CPU không có cờ `vmx`/`svm`, thiếu `live-build`/`debootstrap`/`xorriso`/`qemu`/`wine`. **Container này KHÔNG build được ISO và KHÔNG chạy được QEMU boot-test.** Runbook này soạn để đội IT/hạ tầng dựng một build host RIÊNG, khác máy agent, rồi mới chạy các bước build/boot thật.

---

## 1. Mục tiêu runbook

Cho một người vận hành (IT/hạ tầng) đủ thông tin để:

1. Dựng một **build host** (máy thật hoặc VM) đáp ứng điều kiện phần cứng BUILD-001.
2. Cài đúng bộ công cụ cần cho Debian live-build + QEMU boot-test + (khi cần) Wine/.NET fixture (M2).
3. Tự kiểm tra host bằng `scripts/preflight-build-host.sh` trước khi bắt đầu build thật.
4. Biết chạy build ISO + boot-test ở đâu, và biết rõ phần nào của pipeline build **chưa có trong repo tại thời điểm viết runbook này** (xem mục 6).

Runbook này **không** tự chạy build; nó mô tả cách người vận hành/một agent khác chạy trên host đáp ứng điều kiện.

---

## 2. Yêu cầu phần cứng / VM (BUILD-001)

| Hạng mục | Yêu cầu tối thiểu | Lý do |
| --- | --- | --- |
| Kiến trúc CPU | x86-64 (amd64) | Debian live-build target amd64; NaMiOS v1 không nhắm kiến trúc khác |
| Ảo hóa lồng (nested virt) | Intel VT-x hoặc AMD-V bật ở **mọi** tầng hypervisor phía trên (nếu build host là VM trong VM/cloud) | Cần cho QEMU chạy accelerated (`-accel kvm`) khi boot-test ISO (INSTALL-001); không có vẫn boot được qua TCG nhưng rất chậm, không đại diện cho trải nghiệm thật |
| `/dev/kvm` | Phải tồn tại và user vận hành đọc/ghi được (thường qua group `kvm`) | QEMU accelerated boot-test |
| Số nhân CPU | >= 4 (khuyến nghị >= 8 nếu build song song) | live-build chroot + mksquashfs song song, QEMU boot-test |
| RAM | >= 16 GB | debootstrap/live-build chroot, mksquashfs nén trong RAM/tmpfs, QEMU boot-test cấp RAM ảo riêng |
| Disk trống | >= 100 GB, trên filesystem hỗ trợ file lớn + nhiều inode (ext4/xfs/btrfs) | `work/`, `chroot/`, `cache/`, ISO output, cache APT, SBOM/log; build lại nhiều lần trong lúc debug |
| Hệ điều hành host build | **Debian 13 trixie amd64 sạch** (không phải Debian 12, không phải distro khác) | ADR 0002: pin nền để snapshot package list khớp mục tiêu release; build trên distro khác dễ lẫn version/binary không đại diện |
| Mạng | Egress tới snapshot.debian.org / mirror Debian đã chốt (xem mục 4) | debootstrap/live-build tải package |
| Quyền | User thường có `sudo` cho các bước cần đặc quyền (chroot, mount, losetup, nhóm `kvm`); **không** chạy toàn bộ pipeline hoặc Wine bằng root | CLAUDE.md: không chạy Wine bằng root; hạn chế bề mặt rủi ro |

Gợi ý nền tảng cấp build host: VM KVM/libvirt trên bare-metal Linux của chính dự án, hoặc máy ảo cloud có bật nested-virtualization (một số nhà cung cấp mặc định tắt — phải xin bật ở tầng hypervisor, không chỉ trong guest). Không dùng container không có `/dev/kvm` (ví dụ môi trường agent hiện tại) làm build host cho M3.

---

## 3. Chuẩn bị Debian 13 trixie amd64 sạch

1. Cài Debian 13 (trixie) amd64 "sạch" — netinst hoặc cloud image chính thức từ `debian.org`, không dùng bản tuỳ biến sẵn của bên thứ ba.
2. Cập nhật hệ thống và ghi lại **thời điểm/point release** thật (BUILD-002 — phải pin snapshot thật, không phải placeholder):

   ```sh
   sudo apt-get update
   sudo apt-get -y upgrade
   cat /etc/debian_version
   cat /etc/os-release
   uname -a
   ```

   Ghi các giá trị này vào build manifest thật (xem mục 7) — KHÔNG copy giá trị ví dụ trong runbook này làm giá trị "đã build".

3. Tạo user vận hành không phải root, thêm vào các group cần thiết:

   ```sh
   sudo adduser namios-build
   sudo usermod -aG sudo,kvm namios-build
   ```

   Đăng xuất/đăng nhập lại (hoặc `newgrp kvm`) để group `kvm` có hiệu lực trong phiên làm việc.

---

## 4. Cài bộ công cụ build (lệnh `apt` cụ thể)

Chạy từng bước, không gộp thành một lệnh tải-và-chạy từ xa (không `curl | bash`).

### 4.1 Live-build + tạo rootfs + ISO (BUILD-001)

```sh
sudo apt-get update
sudo apt-get install -y live-build debootstrap xorriso squashfs-tools fakeroot
# mmdebstrap là lựa chọn thay thế debootstrap, không bắt buộc cả hai:
sudo apt-get install -y mmdebstrap
```

### 4.2 QEMU + OVMF cho boot-test (INSTALL-001, INSTALL-002 UEFI)

```sh
sudo apt-get install -y qemu-system-x86 qemu-utils ovmf
```

Kiểm tra firmware UEFI có sẵn (đường dẫn có thể khác theo version package):

```sh
ls /usr/share/OVMF/
```

### 4.3 Wine + winetricks (chuẩn bị cho M2, không phải để build ISO)

```sh
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y wine wine32:i386 wine64 winetricks
```

Lưu ý bắt buộc (CLAUDE.md + §9 Bộ điều phối Wine): **không chạy Wine bằng root**; mỗi ứng dụng dùng prefix riêng dưới `~/.local/share/namios/prefixes/<app-id>/<instance-id>/` của user vận hành/test, không dùng `$HOME` của root hoặc user hệ thống dùng chung. Runner Wine dùng cho fixture/test phải khóa version cụ thể (ghi version `wine --version` vào manifest), không dùng "wine mới nhất lúc build" mà không ghi lại.

### 4.4 Công cụ hỗ trợ khác

```sh
sudo apt-get install -y git python3 python3-venv python3-pip
```

(`git`/`python3` cần để clone repo NaMiOS và chạy script trong `scripts/`, `tests/`.)

---

## 5. Xác minh từng công cụ (checklist tay, trước khi dùng script)

Sau khi cài, xác minh thủ công từng công cụ tồn tại và chạy được (không giả định cài xong là chạy được):

```sh
lb --version          || echo "THIEU: live-build"
debootstrap --version || echo "THIEU: debootstrap"
mmdebstrap --version   || echo "THIEU: mmdebstrap (tuy chon)"
xorriso -version       || echo "THIEU: xorriso"
mksquashfs -version    || echo "THIEU: squashfs-tools"
fakeroot -v            || echo "THIEU: fakeroot"
qemu-system-x86_64 --version || echo "THIEU: qemu"
ls /usr/share/OVMF/OVMF_CODE*.fd 2>/dev/null || echo "THIEU: OVMF"
wine --version          || echo "THIEU: wine"
winetricks --version    || echo "THIEU: winetricks"
test -e /dev/kvm && echo "/dev/kvm: co" || echo "/dev/kvm: KHONG CO"
grep -Eq '(vmx|svm)' /proc/cpuinfo && echo "CPU virt flag: co" || echo "CPU virt flag: KHONG CO"
```

---

## 6. Chạy tự động: `scripts/preflight-build-host.sh`

Thay cho chạy từng lệnh tay ở mục 5, chạy script kiểm tra tổng hợp (nằm trong repo này, đã review an toàn — không `curl|bash`, không `eval`, không cần root):

```sh
cd namios   # thư mục repo đã clone trên build host
scripts/preflight-build-host.sh
```

- In bảng OK/MISSING/WARN cho từng mục (OS, arch, CPU virt flag, `/dev/kvm`, RAM, disk, từng binary bắt buộc).
- Thoát mã **0** nếu toàn bộ mục bắt buộc đạt (host coi là sẵn sàng bước build/boot-test).
- Thoát mã **3** nếu thiếu ít nhất một mục bắt buộc — đọc cột "CHI_TIET" và dòng gợi ý `-> ...` để biết lệnh cài/khắc phục.
- Thêm `--json` để lấy kết quả dạng JSON (dùng cho CI hoặc ghi log evidence), ví dụ:

  ```sh
  scripts/preflight-build-host.sh --json > docs/releases/evidence/preflight-$(date -u +%Y%m%dT%H%M%SZ).json
  ```

- Tuỳ chọn `--build-dir PATH` để kiểm tra dung lượng trống đúng ổ đĩa dự định build (mặc định là thư mục hiện tại); `--min-ram-gb`, `--min-disk-gb`, `--min-cores` để chỉnh ngưỡng nếu đội hạ tầng có lý do khác với mặc định (16GB RAM / 100GB disk / 4 cores).

**Script này KHÔNG cài gì, KHÔNG đổi hệ thống** — chỉ đọc thông tin (`/etc/os-release`, `/proc`, `df`, `command -v`). Chạy nó an toàn trên cả máy agent hiện tại (sẽ báo MISSING đúng với sự thật inventory M0) và trên build host thật.

**Kết quả đã chạy trên container agent hiện tại (02/11/2026, để đối chiếu — KHÔNG phải kết quả build host thật):** `overall_status=not_ready`, exit 3, 14/18 mục bắt buộc MISSING (OS không phải Debian 13, không `/dev/kvm`, không cờ `vmx`/`svm`, RAM 7GB < 16GB, disk 68GB < 100GB, thiếu toàn bộ `lb`/`debootstrap`/`xorriso`/`mksquashfs`/`fakeroot`/`qemu-system-x86_64`/OVMF/`wine`/`winetricks`). Đây đúng với sự thật ở `docs/_m0_inventory_raw.md`; khi chạy trên build host thật đạt điều kiện, dán lại output `--json` vào evidence thay cho đoạn này.

---

## 7. Chạy build ISO + QEMU boot-test (sau khi preflight PASS)

Khi `scripts/preflight-build-host.sh` thoát mã 0:

1. **Build manifest** — trước khi build, ghi lại (không dùng giá trị giả):
   - Debian snapshot/mirror timestamp đã dùng cho `debootstrap`/`live-build` (BUILD-002).
   - Version `live-build`, `debootstrap`/`mmdebstrap`, `xorriso`, kernel package được chọn.
   - Commit SHA của repo NaMiOS tại thời điểm build.
   - Danh sách metapackage/package list dùng (`namios-base`, v.v. — xem §5.2 đặc tả).

   Vị trí build manifest thật thuộc module `image-builder`/`distro/live-build` (xem `docs/specs/DAC_TA_HE_DIEU_HANH.md` §5.2 mục 8, §19). Runbook này chỉ nêu yêu cầu nội dung manifest theo BUILD-002, không tự tạo cấu hình live-build.

2. **Build ISO** — chạy `scripts/build-iso.sh` (ĐÃ có trong repo cùng cấu hình `distro/live-build/`; **`verified_on_host: NO`** — mới kiểm `bash -n` + review logic, CHƯA chạy thật trên build host nào). Script tự gọi `scripts/preflight-build-host.sh` trước, chạy `lb build`, xuất ISO + `SHA256SUMS`; thiếu toolchain → báo lỗi + thoát non-zero, KHÔNG tạo `.iso` giả. Cú pháp thật:

   ```sh
   sudo scripts/build-iso.sh \
     --live-build-dir distro/live-build \
     --output-dir build/out \
     --snapshot-url https://snapshot.debian.org/archive/debian/<YYYYMMDDTHHMMSSZ>/ \
     --sign-key-id <DEV_GPG_KEY_ID>
   # tuỳ chọn: --clean (build lại từ đầu), --no-sudo, --skip-preflight (KHÔNG khuyến nghị)
   ```

   Không tự ý tạo file `.iso` giả hoặc đổi đuôi archive thành `.iso` để "có kết quả" — vi phạm trực tiếp BUILD-001.

3. **Boot-test bằng QEMU** — chạy `scripts/boot-test-qemu.sh` (ĐÃ có; **`verified_on_host: NO`**). UEFI + OVMF, chế độ Live, CHỈ gắn `-cdrom` read-only, KHÔNG gắn ổ cứng ảo nào (đúng INSTALL-001 "Live mode thử không ghi ổ trong"):

   ```sh
   scripts/boot-test-qemu.sh --iso build/out/namios.iso --mode uefi --memory 4096 --cpus 2
   # CI/headless (tự tắt sau 300s): thêm --headless --timeout 300
   # máy không có KVM (chỉ để smoke, rất chậm): thêm --no-kvm
   ```

   Ghi evidence boot-test (BUILD-003): boot log, ảnh/video màn hình (không chứa thông tin nhạy cảm), thời gian boot, lỗi nếu có. Live mode phải thử **không ghi ổ trong** trước (INSTALL-001); chỉ thử ghi đĩa lên đĩa ảo trắng riêng, có xác nhận đúng target device.

4. **SBOM + checksum + ký** (BUILD-003): sinh `SHA256SUMS`, SBOM (SPDX hoặc CycloneDX), package list, build log, test report, release notes. Chỉ dùng **dev-signing key có nhãn rõ trong lab** để ký thử; key production chỉ do maintainer sử dụng ở bước release riêng — không đưa key production vào build host dùng cho agent.

---

## 8. Checklist "host sẵn sàng" (map BUILD-001..003 + INSTALL-001/002)

Đánh dấu từng mục trước khi coi build host là "sẵn sàng":

- [ ] OS = Debian 13 trixie amd64 sạch, đã ghi point release/snapshot thật (BUILD-001, BUILD-002).
- [ ] CPU x86-64, có cờ `vmx`/`svm`; `/dev/kvm` tồn tại và user vận hành đọc/ghi được (BUILD-001, INSTALL-001).
- [ ] RAM >= 16GB, disk trống >= 100GB trên filesystem dùng để build (BUILD-001).
- [ ] `scripts/preflight-build-host.sh` chạy, thoát mã 0, output `--json` đã lưu làm evidence (BUILD-001).
- [ ] `live-build`, `debootstrap` hoặc `mmdebstrap`, `xorriso`, `squashfs-tools`, `fakeroot` đã cài và xác minh version (BUILD-001, BUILD-002).
- [ ] `qemu-system-x86_64` + OVMF đã cài, xác minh UEFI boot được ISO thử (bất kỳ ISO Debian official để test riêng QEMU, không cần chờ ISO NaMiOS) (INSTALL-002).
- [ ] `wine`/`winetricks` đã cài qua user thường (không phải root), version đã ghi lại cho M2 sau này.
- [ ] User vận hành có `sudo` cho bước cần đặc quyền; không chạy pipeline hoặc Wine toàn bộ bằng root.
- [ ] Repo NaMiOS đã clone trên build host, commit SHA ghi lại để đối chiếu build manifest (BUILD-002).
- [ ] `scripts/build-iso.sh` + `scripts/boot-test-qemu.sh` + cấu hình `distro/live-build/` ĐÃ có trong repo (`verified_on_host: NO` — lần chạy đầu trên host này CHÍNH LÀ bước xác minh thật đầu tiên); đối chiếu đúng commit SHA trước khi build.
- [ ] Live mode test không ghi ổ trong đã chạy trước khi thử ghi đĩa lên đĩa ảo trắng riêng (INSTALL-001).

Nếu bất kỳ mục nào KHÔNG đạt → ghi `blocked_external_dependency` với lý do cụ thể vào `docs/STATUS.md`, không đánh dấu M3 là đạt.

---

## 9. Lưu ý bảo mật (nhắc lại từ CLAUDE.md, không được bỏ qua)

- Không chạy Wine bằng root; prefix Wine theo user/app riêng.
- Không `curl | bash`; mọi script cài/build nhận tham số qua argv, không `shell=True`/`eval`, không nội suy shell từ manifest/URL.
- Dev-signing key dùng cho lab phải có nhãn rõ (ví dụ `namios-dev-signing-key`, ghi chú "KHÔNG dùng cho release thật"); không đưa production key vào build host này hay vào repo.
- Pin snapshot/version trong build manifest; nếu phải dùng placeholder tạm (vì chưa chốt trên host thật), ghi rõ `TBD — cần chốt trên build host` — không điền version giả.
- Không commit ISO, bộ cài thương mại, key production, dữ liệu thật vào repo Git (REPO-002); dùng artifact storage riêng cho ISO/binary.

---

## 10. Nguồn

- `docs/specs/DAC_TA_HE_DIEU_HANH.md` §5.1, §5.2, §14 (BUILD-001..004, INSTALL-001..004).
- `docs/adr/0002-nen-debian-13.md`.
- `docs/_m0_inventory_raw.md`.
- `CLAUDE.md` (điều kiện an toàn + chuẩn hoàn thành task).
