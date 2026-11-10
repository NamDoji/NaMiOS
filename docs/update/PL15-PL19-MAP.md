# NaMiOS — PL15 (đã làm) vs PL19 (bổ sung): bản đồ phân việc

**Ngày:** 10/11/2026 · **Trạng thái:** `specified`. PL19 **bổ sung** PL15, **không thay** tiêu chuẩn bảo mật/ký/khóa/firmware/quản trị tập trung của PL15.
**Liên quan:** `docs/specs/namios-pl19/` (README + 01/02/03), ADR 0014/0017/**0020**, `docs/specs/U15C-STAGED-ROLLBACK.md`, `docs/specs/UPDATE-CENTER-UI.md`, `docs/update/STATE-MACHINE-PL19.md`.

---

## 1. PL15 đã giao gì (nền bảo mật + chữ ký + máy trạng thái + prototype)

| Hạng mục | Tạo tác trong repo | Mức |
| --- | --- | --- |
| **ADR cơ chế update/recovery** | ADR 0014 (snapshot Timeshift + health-check + GRUB recovery), ADR 0017 (kiến trúc Update Service + ranh giới UI/Service/SmartAI + hai tầng tin cậy) | `proposed`/`specified` |
| **Kiểm kê nền** | `docs/spec-package/U15-INVENTORY.md` (apt+GPG, Discover/PackageKit, Flatpak, unattended-upgrades, Timeshift, Kup/bup, UFW/AppArmor, SmartAI; fwupd vắng) | — |
| **Máy trạng thái + hợp đồng dữ liệu** | `update_contract.py` (enum `UpdateState`, `VALID_TRANSITIONS`, `UpdateContract`, `TransactionJournal` idempotent/resume) + `update_contract.schema.json` | `partial` |
| **Update Service (quyền-giới-hạn)** | `update_service.py` — check / download-resume / **verify fail-closed** (chữ ký + hash + hạn + thu hồi + arch/model) / preflight / stage + **che bí mật** log | `partial` |
| **Khóa test + repo ký giả** | `sign_test_repo.py` (ed25519 **TEST-ONLY**), fixture metadata/payload/revocation đã ký | `partial` |
| **Staged + boot-health + migration** | `staged_deploy.py` (`DeploymentStore` A-B nguyên tử-mô-phỏng + `StagedDeployer` + `MigrationGuard`/`BackupProof` → UPD-010), `boot_health.py` (6 probe + boot-counter), `fault_inject.py` (13 ca mất-điện/kill/đầy-đĩa/đứt-mạng từng pha) | `partial` (66 test) |
| **Mô hình khóa kiểu TUF** | `docs/security/UPDATE-KEY-CATALOG.md` (root/targets/snapshot/timestamp/CI + threshold + rotation/revocation), `UPDATE-THREAT-MODEL.md` | DESIGN |
| **Đặc tả UI + catalog lỗi** | `docs/specs/UPDATE-CENTER-UI.md` (4 chế độ + máy trạng thái UX + ErrorCard/AIPlanCard), `update-error-catalog.json` (UPD-001..010) | `specified` |
| **Nền transaction trên ISO (M2)** | hook `0640-update-recovery.hook.chroot` (apt Pre-Invoke snapshot + `namios-health-check.service`) + list `0640` (timeshift/needrestart) + `0620` (kup-backup/bup) | `specified` (chưa máy thật) |

**Tinh thần PL15:** *gói giả chữ ký / hash sai / metadata hết hạn / mirror độc hại → 100% chặn, có mã lỗi, không bypass; update lỗi vẫn boot hoặc vào recovery; SmartAI không cài gói không ký.* Đó là **bảo mật chuỗi cập nhật + cơ chế quay lui + ranh giới quyền**.

---

## 2. PL19 bổ sung gì (luồng người dùng + 4 chế độ + giờ yên tĩnh + 14 ca U19 + vòng đời theo thành phần)

| Hạng mục PL19 | Thêm gì so với PL15 | Tạo tác / neo |
| --- | --- | --- |
| **Luồng người dùng nhìn thấy** | Phát hiện/thông báo một-lần, **câu chữ tiếng Việt nguyên văn** (toast "NaMiOS 1.1… [Xem thay đổi][Cài tối nay][Để sau]"), màn xác nhận trước-cài, màn trong/sau nâng cấp, bảng lỗi tiếng Việt | PL19 §1, §3, §5; nối `UPDATE-CENTER-UI.md` |
| **4 chế độ là first-class** | `notify` / `auto_download_ask_install` (mặc định pilot) / `auto_install_safe` / `auto_scheduled` — mỗi chế độ nói rõ *máy làm gì · khi nào reboot · dùng mạng di động không* | Enum `USER_POLICIES` **đã có** trong contract; PL19 cấp ngữ nghĩa UI |
| **Giờ yên tĩnh & chính sách tải** | Giờ yên tĩnh, chỉ-khi-cắm-sạc, giới hạn mạng tính phí, **"Tạm dừng đến ngày…"** (có ngày kết thúc hiển thị), "Kiểm tra lịch sử"; vá khẩn vẫn thông báo dù đã tạm dừng | PL19 §2 (mới so với PL15) |
| **Máy trạng thái người dùng §4** | Nhãn UX PL19 §4 (Có bản mới → … → Hoàn tất/Đã khôi phục/Cần hỗ trợ) **ánh xạ** vào `UpdateState` nội bộ; chốt chuyển không-đảo + guard + chống-completed-giả | `docs/update/STATE-MACHINE-PL19.md` (mới) |
| **Vòng đời cập nhật theo thành phần** | OS / NaMiOffice / NaMiPDF / browser / SmartAI / driver / **firmware** mỗi thứ **nhịp riêng**, hiển thị chung trong Update Center; **firmware KHÔNG** theo nút tự-động OS; app đổi version mà OS giữ version, file người dùng còn | Enum `COMPONENTS` (os/app/ai/firmware/driver/recipe) **đã có**; PL19 cấp quy tắc UI + tách firmware |
| **ADR cơ chế thật + chi phí di trú** | Benchmark trung thực apt-transactional / btrfs-snapper / A-B / OSTree; **chốt transactional apt gần hạn**, OSTree/A-B = tương lai M-level | **ADR 0020** (mới) |
| **14 ca nghiệm thu U19** | U19-01…14 (thông báo một-lần, 4 chế độ+giờ yên tĩnh, resume, chặn chữ ký/hash/hạn/thu-hồi, preflight, việc-chưa-lưu, mất-điện từng pha, boot-loop rollback, migration không tương thích, Wi-Fi theo model/ring, app riêng, firmware xác-nhận, USB offline, SmartAI bị tắt/đề-nghị-bỏ-chữ-ký) | PL19 §03 (bảng ca) |

**Tinh thần PL19:** biến nền bảo mật PL15 thành **trải nghiệm người dùng phổ thông tin cậy** — máy nói đang làm gì, khi nào cần khởi động lại, quay về đâu, lỗi nào cần xử lý; **không** đổi tiêu chuẩn ký/khóa/firmware.

---

## 3. Ranh giới PL15 ↔ PL19 (một dòng)

> **PL15 = chuỗi cập nhật đáng tin (chữ ký, metadata, máy trạng thái, Update Service, staged/rollback prototype).**
> **PL19 = con người dùng chuỗi đó (thông báo, 4 chế độ, giờ yên tĩnh, vòng đời theo thành phần, 14 ca nghiệm thu) + chốt cơ chế thật bằng ADR 0020.**
> PL19 **không** nới lỏng bất kỳ bất biến bảo mật nào của PL15: vẫn fail-closed, vẫn "completed chỉ sau boot-health", vẫn không nút "cài dù sao", firmware vẫn xác nhận riêng.

---

## 4. Trung thực / ranh giới nhóm B (máy thật)

- **Khóa test, không production.** Ký bằng `sign_test_repo.py` (TEST-ONLY); release-index TUF thật **chưa có khóa** (ADR 0007 SEC-007, `UPDATE-KEY-CATALOG.md`).
- **OSTree chưa áp dụng** — tùy chọn tương lai M-level (ADR 0020). Cơ chế gần hạn là **transactional apt** (snapshot + boot-health + GRUB fallback), **không** nguyên tử.
- **Rollback OS ≠ khôi phục dữ liệu ứng dụng** — migration cần backup riêng (Kup/bup + `MigrationGuard` dry-run restore; UPD-010).
- **Nhóm B (chưa làm, cần phần cứng thật):** U19-07/08 rút-điện-thật + boot-loop, U19-10 ring rollout + regression theo model, U19-12 firmware, U19-13 USB bundle offline, từng loại app/driver riêng. Chừng nào chưa chạy đủ nhóm B, PL19 vẫn `partial` — **không** công bố "NaMiOS tự cập nhật an toàn".
