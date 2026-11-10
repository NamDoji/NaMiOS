# ADR 0020 — Cơ chế staged OS-update + rollback trên nền NaMiOS thật (U19)

- **Trạng thái:** proposed · **Mức thực thi:** `specified` / `partial` (prototype chạy + test được ở mức VM/thư-mục; **CHƯA** nối apt/bootloader thật, **CHƯA** máy thật)
- **Ngày:** 10/11/2026
- **Năng lực:** Phụ lục 19 — "Nâng cấp hệ điều hành cho người dùng" (bổ sung PL15). Chốt **cơ chế** staged-update + rollback cho NaMiOS **như nó đang tồn tại** (apt + live-build), và cột mốc chi phí di trú cho các cơ chế nguyên tử tương lai.
  Cửa kiểm chứng (U19, nhóm B — máy thật): *"mất điện / boot loop / hết đĩa → vẫn boot bản cũ hoặc vào recovery; file cá nhân còn; rollback OS ≠ khôi phục dữ liệu ứng dụng."*
- **Liên quan:** ADR 0002 (nền Debian 13), ADR 0007 (cập nhật + ký metadata, fail-closed), **ADR 0014 (snapshot Timeshift + health-check + GRUB recovery — ADR này xây tiếp)**, **ADR 0017 (kiến trúc Update Service + ranh giới UI/Service/SmartAI)**. Prototype: `tools/update-center-prototype/`. Spec liên quan: `docs/specs/U15C-STAGED-ROLLBACK.md`, `docs/specs/UPDATE-CENTER-UI.md`, `docs/update/STATE-MACHINE-PL19.md`, `docs/update/PL15-PL19-MAP.md`. Nền tin cậy: `docs/security/UPDATE-KEY-CATALOG.md`, `docs/security/UPDATE-THREAT-MODEL.md`.

> PL19 **bổ sung** cho PL15, **không thay** tiêu chuẩn ký gói / khóa / firmware / quản trị tập trung. ADR này chỉ chốt **cơ chế áp dụng + quay lui OS**; tầng ký/metadata vẫn theo ADR 0007/0017 + `UPDATE-KEY-CATALOG.md`.

## Bối cảnh

NaMiOS là bản **live-build Debian 13 "trixie" + KDE Plasma 6**, cài bằng **Calamares** lên **ext4** (ADR 0014 §Bối cảnh: repo **không** có file cấu hình phân vùng tùy biến ⇒ Calamares dùng mặc định Debian = ext4, không btrfs). Đây **KHÔNG** phải distro image-based / OSTree. Nền transaction đã có (kiểm trong repo):

- **hook `0640-update-recovery.hook.chroot`** (ADR 0014) đã cài sẵn: (a) apt `DPkg::Pre-Invoke` gọi `namios-pre-update-snapshot.sh` tạo **Timeshift snapshot** trước mỗi transaction (guard: no-op trên live media + khi Timeshift chưa cấu hình); (b) `namios-health-check.sh` + `namios-health-check.service` chạy sau boot, ghi nhật ký tiếng Việt (`dpkg --audit`, `systemctl is-system-running`, lịch sử apt, snapshot gần nhất); (c) đặc tả mục GRUB "NaMiOS — Khôi phục (recovery)" cho hệ đã cài.
- **package-list `0640-update-recovery.list.chroot`**: `timeshift` (rsync mode cho ext4) + `needrestart`.
- **package-list `0620-backup.list.chroot`**: `kup-backup` + `bup` (backup `/home` versioned, đích tách quyền — U13-03).
- **Prototype `tools/update-center-prototype/`** (U15-B/C, `partial`, 66 test pytest): `update_contract.py` (máy trạng thái + journal + schema), `update_service.py` (check/download-resume/verify fail-closed/preflight/stage + che bí mật), `staged_deploy.py` (`DeploymentStore` A-B + `StagedDeployer` + `MigrationGuard`/`BackupProof` UPD-010), `boot_health.py` (`BootHealthChecker` 6 probe + boot-counter), `fault_inject.py` (13 ca mất điện/kill/đầy đĩa/đứt mạng từng pha), `sign_test_repo.py` (khóa ed25519 **TEST-ONLY**), `update_contract.schema.json`.

ADR 0014 đã chốt **rollback mức ảnh** (Timeshift) thay A-B nguyên tử và trung thực rằng **apt không nguyên tử**. ADR 0017 đã chốt **ranh giới ba thành phần** (Update Center UI ↔ Update Service đặc quyền ↔ SmartAI chỉ-đọc) + **hai tầng tin cậy** (apt GPG + release-index kiểu TUF). ADR này **không lặp lại** hai quyết định đó; nó **benchmark trung thực** các cơ chế staged/rollback cho một distro apt/live-build và **chốt cơ chế gần hạn**, kèm chi phí di trú cho các hướng nguyên tử tương lai.

## Các phương án đã benchmark (trung thực theo nền thực)

| Tiêu chí | **(1) Transactional apt**<br>(snapshot + boot-health + GRUB fallback) | (4) btrfs/ZFS snapshot<br>(snapper-style) | (3) A/B partition<br>(dual-root) | (2) OSTree / rpm-ostree / bootc<br>(image atomic) |
| --- | --- | --- | --- | --- |
| Nguyên tử thật | **Không** (apt theo gói) | Một phần (rollback subvolume CoW) | **Có** (đổi slot) | **Có** (deploy theo commit) |
| Mức rollback | Ảnh hệ thống (snapshot) + previous GRUB entry | Subvolume snapshot CoW | Slot A↔B | Deployment/commit |
| Yêu cầu filesystem | **ext4 (đang có)** — rsync/hardlink | **btrfs** (phải đổi) | 2 phân vùng root + /home chung | ostree repo riêng |
| Đổi Calamares | **Không** | Có (scheme btrfs subvolume) | Có (tạo 2 root + logic slot) | Viết lại (ostree compose) |
| Đổi pipeline live-build | **Không** (giữ apt/dpkg/hook/Wine/l10n) | Thấp (thêm snapper + grub-btrfs) | Trung bình (installer module) | **Rebase toàn bộ** (bỏ apt-image) |
| Giữ apt/Debian (ADR 0002) | **Có** | **Có** | Có | **Không** (hệ sinh thái Fedora/OSTree) |
| Tái dùng hook 0640 + prototype | **Trực tiếp** | Phần lớn | Một phần | Rất ít |
| Chi phí di trú | **THẤP** | Trung bình | Cao | **Rất cao (M-level)** |
| Đã kiểm trên HW thật | Chưa (nhóm B) | Chưa | Chưa | Chưa |
| Rủi ro bảo trì | Thấp | Trung bình | Cao | Cao (bootc-trên-Debian chưa chín) |

**Ghi chú chi phí di trú:**

- **(1) Transactional apt — THẤP.** Chỉ cần viết `namios-update-service` thật **bọc** apt + Timeshift (hook 0640 đã có) + GRUB, nối `boot_health.py` vào greenboot/boot-counter thật, nối `recover()` vào `dpkg --configure -a` / `timeshift --restore`. **Không** đổi filesystem, **không** đổi Calamares, **không** rebase pipeline. Toàn bộ `staged_deploy.py`/`boot_health.py`/`fault_inject.py` ánh xạ 1-1 (xem §Ánh xạ).
- **(4) btrfs/snapper — Trung bình.** Đổi default Calamares sang **btrfs subvolume** (`@`, `@home`) + thêm `snapper` + `grub-btrfs` ⇒ snapshot CoW **rẻ hơn hẳn** rsync và rollback subvolume nhanh/gần-nguyên-tử, **vẫn giữ apt/Debian**. Timeshift đã hỗ trợ chế độ btrfs. Giá: đổi scheme cài + test lại máy thật + máy ext4 cũ **không** chuyển tại chỗ. Đây là **bước nâng cấp tự nhiên** của (1).
- **(3) A/B dual-root — Cao.** Calamares phải tạo **2 phân vùng root** + `/home` chung + logic đổi slot ở bootloader; ~gấp đôi dung lượng root; cần module installer + updater ghi sang slot không hoạt động. Đổi slot là **nguyên tử thật**, nhưng là khối việc installer + bootloader lớn, **không có chuẩn desktop Debian** sẵn.
- **(2) OSTree/rpm-ostree/bootc — Rất cao (M-level).** Rebase **toàn bộ** pipeline từ live-build/apt sang ostree compose; **rời bỏ mô hình đóng gói apt/dpkg** (mâu thuẫn ADR 0002); mọi package-list/hook/Việt-hoá/Wine/Calamares phải làm lại; ostree-trên-Debian (bootc) **chưa chín**, đội **chưa có máy thật**. Nguyên tử + rollback theo commit là mạnh nhất, nhưng là **tái kiến trúc cả distro**.

> **Trung thực về OSTree:** repo NaMiOS **KHÔNG dùng OSTree**. Tài liệu kỹ thuật PL19 §Nguồn liệt kê OSTree atomic rollbacks [1] như **tham khảo năng lực**, **không** phải tuyên bố đã dùng. Mọi phát biểu kiểu "NaMiOS dùng cập nhật nguyên tử" đều **sai** ở thời điểm này.

## Quyết định

**Chọn (1) Transactional apt cho gần hạn (U19 alpha).** Dựng `namios-update-service` thật = **lớp điều phối đặc quyền mỏng** (polkit-gated, argv tĩnh — ADR 0017) bọc apt + Timeshift + GRUB, chạy đúng trình tự:

```
check → verify(release-index TUF + apt GPG) → preflight(storage/power/network)
      → migration-guard(backup đã-kiểm-khôi-phục) → Timeshift snapshot (hook 0640)
      → staged apt-apply (ghi journal idempotent)
      → arm reboot: đặt GRUB default = bản mới (greenboot boot-counter), GIỮ entry cũ
      → reboot → boot-health gate (6 probe + boot-counter)
          ├─ đạt → confirm (giữ bản cũ làm rollback target), COMPLETED
          └─ fail → GRUB previous-entry fallback + timeshift --restore, ROLLED_BACK
```

**Cụ thể:**

1. **Snapshot-trước-update** dùng **Timeshift rsync** (ext4, hardlink) đã có ở hook 0640 — làm "bản staged/rollback" mức ảnh. **KHÔNG** phải A-B nguyên tử; mất điện giữa một transaction dpkg ⇒ phục hồi bằng snapshot / `dpkg --configure -a`, **không** phải "bật lại A-B tức thì".
2. **Boot-health gate kiểu greenboot/boot-counter:** sau reboot, `namios-health-check` chạy bộ probe (`boot_health.py`: `kernel_up`, `login_ok`, `data_mount`, `basic_network`, `ui_not_crash_loop`, `update_service_responds`; 4 probe **tới hạn** + ngưỡng 5/6 + UI-crash-lặp luôn fail + tối đa `max_boot_attempts`). Đạt ⇒ `confirm`; fail ⇒ **GRUB previous-entry fallback**.
3. **GRUB fallback + recovery entry:** GRUB `saved_entry`/`boot_success` counter; nếu bản mới không "confirmed" sau N lần boot, GRUB tự chọn **entry trước**. Mục "NaMiOS — Khôi phục (recovery)" (ADR 0014) cho cứu hộ thủ công; **USB cứu hộ đã ký** khi tự-rollback thất bại.
4. **Tầng tin cậy (PL15/ADR 0017):** verify = **apt GPG** (toàn vẹn + nguồn gói) + **release-index kiểu TUF** (root/targets/snapshot/timestamp — `UPDATE-KEY-CATALOG.md`) ở trước, fail-closed; sai chữ ký/hash/hạn/thu hồi/arch ⇒ `blocked` + UPD-00x, **không** nút "cài dù sao", **không** mirror lạ.
5. **Giữ tối thiểu bản-đang-boot + bản-rollback** cho tới khi bản mới qua health + thời gian canary; dọn cache **không** xóa bản phục hồi (`prune_old(keep_last_confirmed>=2)`).

### Ánh xạ prototype → hiện thực thật (giữ từ `U15C-STAGED-ROLLBACK.md`)

| Khái niệm prototype | Hiện thực thật trên NaMiOS alpha |
| --- | --- |
| `DeploymentStore` A-B + con trỏ `default` đổi `os.replace` nguyên tử | **Timeshift snapshot** trước-update + apt staged-apply; "đổi con trỏ" = đặt **GRUB default entry** + boot-counter greenboot. **KHÔNG** A-B nguyên tử thật. |
| `StagedDeployer.prepare/arm_switch` | `namios-update-service` (polkit-gated) chạy preflight → snapshot → apt-apply → arm GRUB. |
| `BootHealthChecker` 6 probe + `max_boot_attempts` | `namios-health-check.sh` đọc `dpkg --audit`, `systemctl is-system-running`, `mountpoint /home`, ping gateway, đếm restart `plasmashell`, D-Bus ping update-service; boot-counter GRUB. |
| `recover()` fallback về bản confirmed | Boot vào snapshot trước-update / `dpkg --configure -a` / `timeshift --restore`; GRUB previous-entry. |
| `MigrationGuard` + `BackupProof` (UPD-010) | Backup `/home` bằng **Kup + bup** (hook 0620, tách quyền) + dry-run restore thật trước khi cho migration chạy. |
| Repo ký + verify (`sign_test_repo.py`, khóa TEST-ONLY) | **apt GPG** (gói) + **release-index TUF** (quản trị tin cậy cấp bản phát hành) — còn là **thiết kế, chưa có khóa thật**. |

## Trung thực về giới hạn (KHÔNG được quảng cáo quá)

- **Không nguyên tử.** Rollback là mức ảnh Timeshift + GRUB previous-entry (ADR 0014), **không** A-B/OSTree. Mất điện giữa dpkg ⇒ phục hồi bằng snapshot, không tức thì. Không được đọc prototype (mô phỏng A-B) ngược thành "NaMiOS đã có A-B nguyên tử".
- **OSTree KHÔNG được áp dụng.** Là **tùy chọn tương lai M-level** với chi phí rebase toàn pipeline (bảng §benchmark). Không có dòng mã OSTree nào trong repo.
- **Rollback OS ≠ khôi phục dữ liệu ứng dụng (PL19 §README/§3).** Snapshot hệ thống **loại trừ `/home`**; rollback hệ **không** âm thầm hoàn nguyên dữ liệu người dùng. Migration dữ liệu phải có **phương án backup riêng**: `MigrationGuard` fail-closed đòi `BackupProof.restore_verified=True` (dry-run restore đúng hash) + `dry_run_ok`; migration một-chiều mà backup không phủ `data_paths` ⇒ **chặn UPD-010**, giữ bản hiện tại. Nếu bản mới đã mở dữ liệu rồi đổi schema không tương thích ⇒ **không** cho OS rollback mù.
- **Chưa có mã Update Service thật.** ADR này + prototype là `specified`/`partial`. **Không** tuyên bố "NaMiOS tự cập nhật an toàn" trước khi gate U19 đạt trên máy thật.
- **TUF-grade là thiết kế.** Release-index nhiều vai trò/threshold/revocation **chưa tồn tại**; U15-B/U19 dùng **khóa lab TEST-ONLY** (`sign_test_repo.py`). **Không** production key trong repo/CI/ISO (ADR 0007 SEC-007).
- **Firmware là luồng riêng.** fwupd vắng mặt; **không** tự cài theo nút tự-động OS; cần model/pin/nguồn/chữ ký/xác nhận riêng; **không** hứa rollback firmware.
- **Timeshift chưa cấu hình** ⇒ lần đó **không** có điểm rollback (snapshot lỗi `|| true`, không chặn vá bảo mật); health-check phải cho người dùng thấy (ADR 0014 §trung thực).

## Hệ quả

- U19 hiện thực `namios-update-service` thật (bọc apt + Timeshift hook 0640 + GRUB) + nối `boot_health.py`/`staged_deploy.py`/`MigrationGuard` vào hệ thật; verify hai tầng (apt GPG + release-index TUF fixture lab).
- Chạy lại ma trận fault-injection §4 của prototype trên **VM QEMU** với `apt upgrade` thật + cắt nguồn ảo từng pha; kiểm `dpkg --audit` sạch + hash `/home` nguyên.
- **Nhóm B (máy thật) — chưa làm:** rút điện thật giữa update, boot-loop/desktop-crash, ring rollout + regression Wi-Fi theo model (U19-10), USB bundle offline đã ký (U19-13), từng loại app/firmware riêng. Chưa đủ nhóm B thì U19 vẫn `partial`.
- Giữ nguyên ADR 0002/0007/0014/0017. Nếu Calamares đổi sang **btrfs** ⇒ **mở lại** ADR này để lên phương án (4) snapper (nâng cấp rẻ của (1)); nếu có nhu cầu nguyên tử thật + nguồn lực ⇒ cân nhắc (3)/(2) ở M-level.

## Nguồn

- [1] OSTree atomic rollbacks & deployment: https://ostreedev.github.io/ostree/atomic-rollbacks/ ; https://ostreedev.github.io/ostree/deployment/ — **tham khảo năng lực, KHÔNG dùng trong NaMiOS.**
- [2] rpm-ostree deployment/rollback: https://coreos.github.io/rpm-ostree/administrator-handbook/
- [3] The Update Framework — roles & metadata: https://theupdateframework.io/docs/security/ ; https://theupdateframework.io/docs/metadata/
- [4] fwupd power/battery errors: https://fwupd.github.io/libfwupd/error.Error.html
- Timeshift (rsync cho ext4, btrfs mode cho btrfs): https://github.com/linuxmint/timeshift
- ADR 0002 / 0007 / 0014 / 0017; `docs/specs/U15C-STAGED-ROLLBACK.md`; `tools/update-center-prototype/`; `docs/security/UPDATE-KEY-CATALOG.md`, `UPDATE-THREAT-MODEL.md`.
