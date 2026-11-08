# ADR 0014 — Chiến lược cập nhật và khôi phục OS (U13-02)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` / `partial` (chưa test mất-điện trên máy thật)
- **Ngày:** 08/11/2026
- **Năng lực:** Phụ lục 13 — **U13-02 "Cập nhật và khôi phục OS"** (P0).
  Cửa kiểm chứng: *"Mất điện / hết dung lượng / update lỗi vẫn khởi động hoặc vào recovery, file cá nhân còn."*
- **Liên quan:** ADR 0002 (nền Debian 13), ADR 0007 (cập nhật + ký metadata, fail-closed), U13-01 (Calamares cài đặt), U13-03 (sao lưu dữ liệu người dùng).

## Bối cảnh

NaMiOS là bản live-build **Debian 13 "trixie" + KDE Plasma 6**, cài lên đĩa bằng **Calamares**. Hiện tại (xem `docs/STATUS-U13-KIEM-KE.md`) U13-02 mới ở mức `specified`: chỉ có `unattended-upgrades` (chỉ pocket security). **Chưa có** bản boot trước, health check, hay đường khôi phục. Đây là lỗ hổng P0 lớn — Phụ lục 13 §1 nói thẳng: *"mất dữ liệu sau update... sẽ khiến họ quay về Windows"*.

Phụ lục 13 §1 nhắc rpm-ostree như một **tham khảo về năng lực** (chuẩn bị bản cập nhật thành deployment, áp dụng khi khởi động lại, có lệnh rollback) [1] — **không** phải quyết định NaMiOS phải chọn Fedora/rpm-ostree. Yêu cầu là có ADR so sánh trung thực theo phần cứng, gói ứng dụng và năng lực bảo trì.

**Ràng buộc hệ thống tệp (đã kiểm trong repo):** trình cài là `calamares` + `calamares-settings-debian` (`distro/live-build/config/package-lists/0700-installer.list.chroot`). **Không** có file cấu hình phân vùng/`partition.conf` tùy biến nào trong `distro/live-build/config` → Calamares dùng **mặc định Debian = ext4** (không phải btrfs). Vì thế mọi phương án snapshot ở dưới phải chạy được **trên ext4**, tức dạng **rsync/hardlink**, không phải CoW của btrfs.

## Các phương án đã cân nhắc

### (a) Debian apt + system snapshot (Timeshift, chế độ rsync) + GRUB recovery — **ĐƯỢC CHỌN cho alpha**

- Giữ nguyên Debian + apt. Trước mỗi phiên cập nhật, tự tạo **snapshot toàn hệ thống** bằng **Timeshift ở chế độ rsync** (phù hợp ext4; dùng hardlink nên snapshot thứ 2 trở đi tốn ít dung lượng cho phần không đổi).
- Nếu update làm hỏng hệ, người dùng **khôi phục về snapshot gần nhất** (rollback ở mức "phục hồi về ảnh trước", KHÔNG phải A-B nguyên tử).
- Thêm **health check lúc khởi động** ghi nhật ký tiếng Việt: lần apt gần nhất có hoàn tất không, dịch vụ chính có lên không.
- Thêm mục GRUB **"NaMiOS — Khôi phục (recovery)"** cho **hệ đã cài** (xem §"GRUB recovery" bên dưới) — làm ở bước hậu-cài, KHÔNG đụng GRUB của live-build.

### (b) Image-based atomic A-B (rpm-ostree) — **tham khảo năng lực, KHÔNG chọn cho alpha**

- rpm-ostree dựng bản cập nhật thành một deployment riêng, áp dụng khi reboot, rollback một lệnh là xong [1] → đây là **rollback nguyên tử thật**, mạnh hơn hẳn (a) về "update lỗi vẫn khởi động".
- **Giá phải trả:** rpm-ostree là hệ sinh thái **Fedora/OSTree**, không dùng apt/dpkg. Chọn nó nghĩa là **rời bỏ Debian/apt** — mâu thuẫn ADR 0002 (nền Debian 13) và toàn bộ package-list, hook, Việt hoá, Wine, Calamares đang gắn với Debian.
- Phương án Debian tương đương (ostree + bootc trên Debian) **chưa chín**, chưa có đường Calamares + apt chuẩn, đội **chưa có máy thật để kiểm**. Rủi ro bảo trì cao, lợi ích chưa chứng minh được ở alpha.

## Quyết định

**Chọn (a) cho bản alpha.** Cụ thể:

1. **Snapshot trước cập nhật (apt hook):** cài `/etc/apt/apt.conf.d/80namios-snapshot` với `DPkg::Pre-Invoke` gọi script snapshot. Script **no-op** khi (i) đang chạy trên live media (`boot=live`), hoặc (ii) Timeshift chưa được cấu hình (chưa có `/etc/timeshift/timeshift.json`, tức máy chưa cài hoặc chưa chọn ổ lưu snapshot). Nhờ guard (ii), hook **không** kích hoạt trong lúc `lb build` (chroot chưa có timeshift.json).
2. **Health check lúc boot:** `/usr/local/bin/namios-health-check.sh` + unit `namios-health-check.service` chạy sau khi hệ lên, ghi nhật ký tiếng Việt vào `/var/log/namios-health.log` (lần apt gần nhất hoàn tất chưa — qua `dpkg --audit` + `apt/history.log`; dịch vụ chính có `degraded`/`failed` không; snapshot trước-update gần nhất là khi nào). Luôn `exit 0`, idempotent.
3. **Khôi phục:** dùng GUI Timeshift (đã có trong bộ gói) để chọn và phục hồi snapshot; thêm mục GRUB recovery cho hệ đã cài (hậu-cài).

### Trung thực về giới hạn (KHÔNG được quảng cáo quá)

- **apt KHÔNG nguyên tử.** Nếu mất điện **giữa** một transaction dpkg, hệ có thể còn gói ở trạng thái half-configured. Cách phục hồi là boot vào snapshot trước-update (hoặc `dpkg --configure -a` nếu nhẹ) — **không** phải "A-B bật lại tức thì". Đây là mức tốt nhất đạt được **mà không re-base cả bản phân phối**.
- **Snapshot KHÔNG phải backup dữ liệu người dùng.** Theo mặc định NaMiOS, snapshot hệ thống **loại trừ `/home`** (dữ liệu cá nhân thuộc U13-03, sao lưu riêng, đích tách quyền). Rollback hệ **không** được âm thầm ghi đè file cá nhân.
- **Snapshot thất bại KHÔNG chặn cập nhật bảo mật.** Script snapshot kết thúc `|| true` + ghi log cảnh báo: thà cập nhật-không-có-snapshot còn hơn chặn vá bảo mật. Hệ quả honest: lần đó sẽ **không** có điểm rollback — health check phải cho người dùng thấy điều này.
- Chưa có **A-B deployment**, chưa có **USB cứu hộ** đóng gói riêng (hiện tạm dùng chính ISO Live làm đĩa cứu hộ — xem dưới). Các phần này vẫn ở trạng thái `specified`.

## GRUB recovery — làm ở HỆ ĐÃ CÀI, KHÔNG đụng live-build

Mục GRUB **"NaMiOS — Khôi phục (recovery)"** chỉ có nghĩa trên **hệ đã cài lên đĩa** (nơi có GRUB cài bền + các snapshot cục bộ). KHÔNG hack `grub.cfg`/menu của live-build (ISO Live boot bằng isolinux/grub-efi riêng, dùng cho cứu hộ chứ không chứa snapshot của máy người dùng). Cách thêm đúng chỗ (bước **hậu-cài / Calamares `shellprocess` sau khi cài**):

1. Đặt script sinh menu `/etc/grub.d/11_namios_recovery` (quyền `0755`) in ra một `menuentry` "NaMiOS — Khôi phục (recovery)" khởi động kernel hiện tại với `systemd.unit=rescue.target` (vào chế độ cứu hộ dòng lệnh để chạy `dpkg --configure -a`, kiểm đĩa, hoặc gọi `timeshift --restore`).
2. Chạy `update-grub` (một lần, trên hệ đã cài) để sinh lại `/boot/grub/grub.cfg`.
3. Ngoài ra, bản thân **Timeshift** khi bật tích hợp GRUB có thể tự thêm submenu các snapshot vào boot; cân nhắc bật ở bước hậu-cài sau khi đã test trên máy thật.

Việc nối bước này vào Calamares (job `shellprocess`/`contextualprocess`) thuộc U13-01 và sẽ ghi ADR/commit riêng; ADR này chỉ **đặc tả** nó, chưa implement, để không đụng GRUB của ISO.

## USB cứu hộ (tạm thời)

Alpha dùng **chính ISO Live NaMiOS** làm đĩa cứu hộ: boot Live → mount đĩa đã cài → `chroot` chạy `dpkg --configure -a` hoặc `timeshift --restore`. Bộ USB cứu hộ chuyên dụng (menu cứu hộ tiếng Việt, công cụ kiểm đĩa) là việc sau, vẫn `specified`.

## Hệ quả

- Người dùng có **một điểm quay lui** trước mỗi lần cập nhật (khi đã cấu hình Timeshift) + nhật ký sức khỏe tiếng Việt mỗi lần boot.
- Phân biệt rõ 3 tầng (nối tiếp ADR 0007): **snapshot hệ thống** (ADR này) ≠ **rollback gói apt** ≠ **backup/restore dữ liệu người dùng** (U13-03). apt downgrade/rollback KHÔNG đảm bảo hoàn nguyên migration dữ liệu.
- Nếu sau này đổi Calamares sang **btrfs**, nên chuyển Timeshift sang **chế độ btrfs** (hoặc snapper) để có snapshot CoW rẻ hơn và rollback subvolume nhanh hơn — khi đó mở lại ADR này.
- Tên gói phải **xác minh `apt-cache show` trên host trixie thật** trước khi build (xem package-list, `verified_on_host: NO`).

## Điều kiện để lên `completed` (cửa U13-02)

Cần **máy thật**, chưa thể làm trong QEMU/CI:

1. **Mất điện giữa update:** cài máy thật → chạy một đợt `apt upgrade` lớn → **ngắt điện cứng** giữa chừng → bật lại: máy **phải** (a) boot được, hoặc (b) vào recovery; và `dpkg --audit` sạch sau phục hồi; **file trong `/home` còn nguyên** (so hash).
2. **Hết dung lượng:** đổ đầy đĩa rồi chạy update → không được hỏng hệ không boot; snapshot/health check báo đúng tình trạng.
3. **Update lỗi (gói hỏng):** rollback về snapshot trước-update → hệ trở lại dùng được, dữ liệu người dùng còn.

Chưa chạy đủ 3 ca trên máy thật thì U13-02 vẫn là `partial`, **không** được ghi `completed` (Phụ lục 13 §5) và **không** được quảng cáo "rollback nguyên tử".

## Nguồn

- [1] rpm-ostree — deployment upgrade & rollback: https://coreos.github.io/rpm-ostree/administrator-handbook/
- Timeshift — system restore (rsync cho ext4, btrfs mode cho btrfs): https://github.com/linuxmint/timeshift
- Debian apt / dpkg — recovery sau transaction dở: `dpkg --configure -a`, `dpkg --audit`.
- ADR 0002 (nền Debian 13), ADR 0007 (cập nhật + ký metadata fail-closed).
