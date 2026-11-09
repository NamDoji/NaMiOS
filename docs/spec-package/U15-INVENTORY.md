# NaMiOS — U15-A: Kiểm kê cơ chế cập nhật / sao lưu / boot / firmware thật

**Ngày:** 09/11/2026 · **Người lập:** đội phát triển (Claude Code) · **Mốc:** Phụ lục 15 §10 **U15-A** (Kiểm kê/ADR + threat model + danh mục khóa).
**Đối chiếu:** `docs/spec-package/NaMiOS_Phu_luc_15_Update_Center_Bao_mat_Cap_nhat.md` (§1, §2, §4, §5, §7, §10), `docs/adr/ADR-0014-update-recovery-strategy.md`, `docs/adr/0007-cap-nhat-bao-ve-metadata.md`, `docs/STATUS-U13-KIEM-KE.md`.

## 0. Tuyên bố trung thực (đọc trước)

> **NaMiOS CHƯA có dịch vụ cập nhật ký riêng (custom signed Update Service).** Những gì đang có là: (1) **apt + repo Debian đã ký GPG** (kế thừa từ Debian, cơ chế có thật nhưng là của upstream, chưa phải thiết kế riêng của NaMiOS), và (2) một lớp **cấu hình tĩnh** cho cập nhật-bảo-mật-tự-động + snapshot-trước-update + health-check (viết trong repo, **chưa boot máy thật**). **Không** tồn tại: Update Service đặc quyền riêng, Update Center 4-chế-độ, metadata kiểu TUF (vai trò/threshold/chống rollback-freeze), staged deployment, hợp đồng dữ liệu + mã lỗi `UPD-*`, hay đường firmware (fwupd **vắng mặt**).

**Quy tắc chấm trạng thái** (kế thừa §5 Phụ lục 13 — đã dùng xuyên suốt U13):

- `absent` — không có trong repo.
- `specified` — đã có yêu cầu/thiết kế/cấu hình trong repo, **chưa** có bằng chứng chạy.
- `partial` — có artifact + bằng chứng chạy **một phần** (ví dụ cơ chế của Debian đã chín, hoặc boot QEMU), **chưa** đủ cửa kiểm chứng.
- `completed` — **chỉ** khi chạy trên **máy thật** (pilot) qua đúng cửa kiểm chứng.

**Sự thật nền:** NaMiOS hiện **chưa test trên máy thật nào**; mọi bằng chứng là boot QEMU/TCG. Theo quy tắc trên, **không cơ chế cập nhật nào đạt `completed`.**

## 1. Bảng kiểm kê cơ chế hiện có

| # | Cơ chế | Vai trò trong chuỗi cập nhật | Trạng thái | Bằng chứng trong repo |
| --- | --- | --- | --- | --- |
| 1 | **apt + repo Debian ký GPG** | Nguồn + xác thực gói OS/app (chữ ký repo, `Release`/`Release.gpg`/`InRelease`) | **partial** (upstream Debian, chưa cấu hình riêng NaMiOS, chưa repo NaMiOS) | Nền Debian 13 (`docs/adr/0002-nen-debian-13.md`); **không** có file apt repo/keyring tùy biến nào trong `distro/live-build/config/` → dùng mặc định Debian. |
| 2 | **unattended-upgrades** (chỉ pocket security) | Tự cài vá bảo mật, **không** dist-upgrade, **không** auto-reboot | **specified** | Hook `distro/live-build/config/hooks/normal/0600-security-updates.hook.chroot` ghi `/etc/apt/apt.conf.d/51namios-unattended` (`Origins-Pattern` = `*-security`; `Automatic-Reboot "false"`). |
| 3 | **Timeshift snapshot trước-update** (rsync, ext4) | Điểm quay lui trước mỗi transaction apt | **specified** (ADR-0014) | Package-list `0640-update-recovery.list.chroot` (`timeshift`, `needrestart`); hook `0640-update-recovery.hook.chroot` cài `/usr/local/bin/namios-pre-update-snapshot.sh` + apt hook `/etc/apt/apt.conf.d/80namios-snapshot` (`DPkg::Pre-Invoke`). |
| 4 | **Health check sau boot** | Phát hiện dpkg dở dang / phiên apt đứt / dịch vụ fail / snapshot gần nhất | **specified** | Cùng hook `0640`: `/usr/local/bin/namios-health-check.sh` + unit `namios-health-check.service` (bật qua symlink `multi-user.target.wants`), ghi `/var/log/namios-health.log` tiếng Việt, luôn `exit 0`. |
| 5 | **needrestart** | Liệt kê dịch vụ cần restart sau nâng thư viện/kernel (chế độ liệt-kê, không tự restart ồ ạt) | **specified** | `0640-update-recovery.list.chroot`. |
| 6 | **GRUB + mục "Khôi phục (recovery)"** | Bootloader + đường vào rescue để `dpkg --configure -a` / `timeshift --restore` | GRUB: **partial** (upstream). Mục recovery: **specified** — **chưa implement** | ADR-0014 §"GRUB recovery" đặc tả `/etc/grub.d/11_namios_recovery` (0755) + `update-grub` ở **hậu-cài** Calamares; **không** tìm thấy file này trong repo → mới là đặc tả. |
| 7 | **Discover + PackageKit** | Front-end GUI xem/cài/cập nhật gói + metadata danh mục | **specified** (gói có mặt, **không** phải Update Center 4-chế-độ của NaMiOS) | `0100-desktop-kde.list.chroot` dòng `plasma-discover`, `packagekit`. Đây là UI update **chung của KDE**, chưa phải UI 4-chế-độ + hợp đồng `UPD-*` mà PL15 §3 đòi. |
| 8 | **Flatpak + xdg-desktop-portal** | Kênh app sandbox + remote Flathub | **specified** | `0630-security.list.chroot` (`flatpak`, `xdg-desktop-portal`, `xdg-desktop-portal-kde`); hook `0630-security-default.hook.chroot` (c) cài `namios-flatpak-setup.service` chạy `flatpak remote-add flathub` ở **first-boot** (argv tĩnh, offline-safe). |
| 9 | **Sao lưu dữ liệu người dùng (Kup + bup)** | Backup `/home` theo phiên bản, đích tách ổ (U13-03) — **tách khỏi** snapshot hệ thống | **specified** | `0620-backup.list.chroot` (`kup-backup`, `bup`); hook `0620-backup-config.hook.chroot`; `docs/runbooks/backup-restore.md`. |
| 10 | **fwupd / LVFS (firmware)** | Cập nhật firmware/BIOS thiết bị | **absent** | `grep -rin fwupd distro/` → **không có**. Chỉ xuất hiện trong tài liệu đặc tả (PL15 §2/§4 [3], PL08 E08-006) như **tham khảo**, chưa có gói, chưa có đường cập nhật/phục hồi firmware. |
| 11 | **SmartAI (userspace tool)** | Giải thích/chẩn đoán/đề xuất — **chỉ đọc** | **specified** | `namios-smartai` + `namios-smartai-policy.sh`; `docs/specs/SMARTAI-ORCHESTRATOR.md` §4 (3 guardrail), §5 (tắt AI máy vẫn boot/gõ/in/cập nhật). **Chưa** nối riêng vào luồng Update Center. |

## 2. Các lớp an toàn phụ đã có (liên quan chuỗi cập nhật)

- **UFW** (deny-incoming mặc định) + **AppArmor** (cần `apparmor=1 security=apparmor` ở bootappend — xem `docs/SECURITY-DEFAULTS.md`): hook `0630`. Giảm bề mặt tấn công máy nhận bản, **không** phải cơ chế xác thực cập nhật.
- **Mã lỗi chẩn đoán `NM-*`** (`docs/support/error-codes.md`, `error-catalog.json`): hướng người-dùng-cuối cho mạng/driver/đĩa/quyền/app-crash. **Khác không gian tên** với `UPD-*` mà PL15 §7 đòi cho chuỗi cập nhật — hai tập này **không** trùng, `UPD-*` **chưa tồn tại**.
- **ADR-0007** (02/11): đã **quyết định hướng** = apt + repo ký + "ưu tiên đánh giá TUF" cho catalog metadata, fail-closed; nhưng phần verify metadata (phiên bản/thời hạn/revocation) mới là **spike cần làm ở M1**, chưa có mã.

## 3. Khoảng cách: apt-signing hiện có **vs** yêu cầu PL15 (TUF-grade)

| Thuộc tính PL15 §4 đòi | apt + repo ký GPG cho sẵn | Khoảng trống phải xây (U15-B→D) |
| --- | --- | --- |
| Toàn vẹn + nguồn gói | ✔ Chữ ký repo (`InRelease`) + hash trong `Packages` | — (giữ) |
| **Nhiều vai trò khóa** (root/targets/snapshot/timestamp) | ✘ Một khóa repo duy nhất, không tách vai trò | Thiết kế vai trò kiểu TUF (xem `docs/security/UPDATE-KEY-CATALOG.md`). |
| **Threshold/quorum** (m-trong-n ký) | ✘ Một khóa ký là đủ | Quorum cho root/targets; tách quyền người-build ≠ người-duyệt. |
| **Chống rollback** (không cho tụt về bản cũ/metadata cũ) | △ Yếu — apt chặn `Packages` cũ hơn qua `Date`/`Valid-Until` nhưng không có "snapshot version" cưỡng chế tiến | Số phiên bản metadata tăng nghiêm ngặt + chống tụt (TUF snapshot role). |
| **Chống freeze** (ghim bản cũ để che vá mới) | △ Dựa `Valid-Until` của `Release` (có thể dài) | Metadata `timestamp` hạn ngắn, làm tươi liên tục. |
| **Chống mix-and-match** (ghép gói từ nhiều ảnh) | △ Trong một repo thì nhất quán; không có "snapshot" ảnh toàn cục | Snapshot role khóa một tập gói nhất quán theo thời điểm. |
| **Hết hạn metadata + clock sai** | △ `Valid-Until`; nếu NTP sai thì hành vi mơ hồ | Xử lý tường minh "không xác minh được thời hạn" (UPD-004), không âm thầm bỏ kiểm. |
| **Revocation khóa/bản** | ✘ Không có danh sách thu hồi bản phát hành | Danh sách thu hồi (UPD-009) + đẩy tới máy. |
| **Dịch vụ cập nhật quyền-tối-thiểu** | ✘ apt chạy như root; Discover gọi PackageKit | **Update Service** polkit-gated, tách khỏi UI (ADR-0017). |
| **UI 4 chế độ + trạng thái tiếng Việt** | ✘ Discover là UI chung | Update Center (UI-only) — U15-B. |
| **Staged deployment + ring rollout + kill-switch** | ✘ apt đẩy ngay khi có | Kênh `testing→pilot→stable→hotfix` + ring + halt (U15-D). |
| **Hợp đồng dữ liệu + mã lỗi `UPD-*`** | ✘ | Schema §7 + `UPD-001..010` — U15-B. |
| **Firmware (fwupd/LVFS, ngưỡng pin)** | ✘ vắng mặt | Đánh giá thêm fwupd ở U15-D, **không** hứa rollback firmware. |

**Tóm tắt khoảng cách:** apt-signing cho **toàn vẹn + nguồn** của gói trong **một** repo đã ký — đủ làm **nền**, nhưng **thiếu toàn bộ** tầng quản trị-tin-cậy kiểu TUF (nhiều vai trò, threshold, chống rollback/freeze/mix-and-match, revocation bản phát hành), **thiếu** dịch vụ cập nhật tách-quyền, **thiếu** UI 4 chế độ, **thiếu** staged rollout và **thiếu** hợp đồng `UPD-*`. Firmware **chưa có đường nào**.

## 4. Kết luận U15-A (phần kiểm kê)

1. Dùng lại tối đa cái đã chín: **apt + repo ký** (nguồn/toàn vẹn gói) và **Timeshift + health-check** (ADR-0014, rollback mức ảnh). Không viết lại package manager.
2. Phần PL15 đòi thêm được chốt ở **ADR-0017** (kiến trúc Update Center ↔ Update Service ↔ SmartAI) + **threat model** (`docs/security/UPDATE-THREAT-MODEL.md`) + **danh mục khóa** (`docs/security/UPDATE-KEY-CATALOG.md`).
3. **Không** tuyên bố đã có updater; mọi hạng mục mới ở trạng thái `specified` cho tới khi có bằng chứng máy thật (U15-C/D).

## 5. Việc U15-B/C/D phải xây tiếp (tham chiếu nhanh)

- **U15-B — Update Center MVP + xác thực metadata:** Update Service quyền-tối-thiểu (polkit-gated), UI 4 chế độ (§3), check/changelog/download-resume, verify metadata kiểu TUF với **khóa lab gắn nhãn dev**, preflight storage/power/network, hợp đồng dữ liệu + mã lỗi `UPD-001..010`, server giả có signed metadata + ca phản công (gói giả chữ ký / hash sai / metadata hết hạn). Không dùng production key.
- **U15-C — Transaction/rollback:** staged deployment, boot health (mở rộng `namios-health-check.sh`), auto rollback/recovery (Timeshift + GRUB recovery từ ADR-0014), migration guard, backup proof; fault injection trên VM rồi 5 máy pilot (gồm ca mất điện).
- **U15-D — Mở rộng:** phân kênh app/AI/firmware (đánh giá thêm fwupd), ring rollout + IT policy + revocation, SmartAI giải thích (chỉ-đọc); diễn tập khóa bị lộ / CDN bị thay / bản lỗi Wi‑Fi. Ký release chỉ sau QA + SBOM/provenance + phê duyệt quorum.

Chi tiết kiến trúc ở `docs/adr/ADR-0017-update-service-architecture.md`; threat model ở `docs/security/UPDATE-THREAT-MODEL.md`; danh mục khóa ở `docs/security/UPDATE-KEY-CATALOG.md`.
