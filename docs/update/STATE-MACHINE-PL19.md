# NaMiOS — Máy trạng thái người dùng nhìn thấy (Phụ lục 19 §4)

**Ngày:** 10/11/2026 · **Trạng thái:** `specified` — ánh xạ nhãn UX PL19 §4 ↔ trạng thái **nội bộ đã hiện thực** trong `tools/update-center-prototype/update_service.py` + `update_contract.py` (`partial`, 66 test pytest). **Chưa** nối apt/bootloader thật.
**Liên quan:** PL19 `docs/specs/namios-pl19/01_LUONG_NGUOI_DUNG.md` §4 + `02_HOP_DONG_KY_THUAT.md` §2, PL15 `docs/specs/UPDATE-CENTER-UI.md` §2, ADR 0017/0020, `docs/update/PL15-PL19-MAP.md`.

> Nguyên tắc nền: Update Center là **giao diện**; mọi chuyển trạng thái thật do **Update Service** (đặc quyền, polkit-gated) thực hiện và **chỉ** đi theo `VALID_TRANSITIONS` — không nhảy cóc, không bypass. SmartAI chỉ **đọc** state đã lọc.

---

## 1. Chuỗi nhãn UX PL19 §4

```
Có bản mới → Đang tải → Đang xác minh → Sẵn sàng cài → Đang chuẩn bị
  → Cần khởi động lại → Đang kiểm tra bản mới
  → Hoàn tất  /  Đã khôi phục  /  Cần hỗ trợ
```

Trước "Có bản mới" còn pha **Đang kiểm tra** (check định kỳ / "Kiểm tra ngay"); mạng hỏng ⇒ **Cần hỗ trợ** (blocked UPD-001). "Đang tạm dừng đến ngày…" là **lớp policy** (PL19 §2, 4 chế độ), không phải một state của chu trình một-bản-cập-nhật.

---

## 2. Ánh xạ nhãn UX ↔ state nội bộ (đã hiện thực)

Trạng thái nội bộ = enum **`UpdateState`** trong `update_contract.py` (trích thật):
`available · downloading · verified · staged · reboot_pending · boot_check · completed · rolled_back · blocked`.

| # | Nhãn UX (PL19 §4) | `UpdateState` nội bộ | Hàm Update Service tạo chuyển | State kỹ thuật PL15 §2 (siêu tập journal) | Guard để tới / Ghi chú an toàn |
| --- | --- | --- | --- | --- | --- |
| 0 | Đang kiểm tra | *(tiền-`available`)* | `check()` | DISCOVERED → ELIGIBLE | Mạng hỏng ⇒ `blocked` UPD-001. |
| 1 | **Có bản mới** | `available` | `check()` ⇒ `AVAILABLE` | ELIGIBLE | Chỉ thông báo nếu đúng arch/channel, không bị thu hồi, áp dụng cho máy. Hiện changelog/dung lượng/cần-reboot thật. |
| 2 | **Đang tải** | `downloading` | `download()` ⇒ `DOWNLOADING` | DOWNLOADING → DOWNLOADED | Tải theo chunk + **resume** (`.part`); đứt mạng giữ phần đã tải. Có nút **tạm dừng tải**. |
| 3 | **Đang xác minh** | (đang ở `downloading`, chạy `verify()`) | `verify()` | (bước tạo VERIFIED) | **Fail-closed**: chữ ký metadata → hạn/clock → thu hồi → arch/model → hash payload. Bất kỳ bước nào hỏng ⇒ `blocked` + UPD-003/004/009/005. |
| 4 | **Sẵn sàng cài** | `verified` | `verify()` đạt ⇒ `VERIFIED` (+ `preflight()`) | VERIFIED → PREFLIGHT_OK | **Chỉ tới khi** `signature_status=='verified'` (bất biến `validate()`). Preflight storage/power/network; fail ⇒ `blocked` UPD-002/001/006. |
| 5 | **Đang chuẩn bị** | `staged` | `StagedDeployer.prepare()` ⇒ `STAGED` | STAGED | Chuẩn bị deployment **riêng** (default vẫn bản cũ); `MigrationGuard` chặn ⇒ `blocked` UPD-010. **Tệp của bạn chưa đổi** — không nói "đã xong". |
| 6 | **Cần khởi động lại** | `reboot_pending` | `StagedDeployer.arm_switch()` ⇒ `REBOOT_PENDING` | REBOOT_PENDING → BOOTING_NEW | **Đổi con trỏ default nguyên tử** sang bản mới, GIỮ bản cũ confirmed. Việc chưa lưu ⇒ hoãn (UPD-007). **Từ đây là vùng không-hủy** (xem §3). |
| 7 | **Đang kiểm tra bản mới** | `boot_check` | `BootHealthChecker.run()` ⇒ `BOOT_CHECK` | HEALTH_CHECK | 6 probe + boot-counter. Mất mạng do router (không phải lỗi bản) **không** nhất thiết rollback ngay. |
| 8a | **Hoàn tất** | `completed` | `boot_check` đạt ⇒ `COMPLETED` | COMMITTED | **CHỈ** tới từ `boot_check` khi health đạt (xem §4). Bản cũ **không** bị xóa (vẫn là rollback target). |
| 8b | **Đã khôi phục** | `rolled_back` | `boot_check` fail ⇒ `ROLLED_BACK` | ROLLBACK_PENDING → ROLLED_BACK | Health fail ⇒ tự `rollback_to_previous()` về bản confirmed. Mã **UPD-008** ở lớp report (không gắn contract). "Tệp cá nhân cần được kiểm ở app có chuyển dữ liệu" — không hứa tuyệt đối. |
| 8c | **Cần hỗ trợ** | `blocked` (+ `error_code`) | bất kỳ bước ⇒ `BLOCKED` | BLOCKED / FAILED / **RECOVERY_REQUIRED** | `error_code != null`; giữ bản hiện tại; **không** đường sang staged/completed. Khi **tự-rollback cũng thất bại** (không còn bản confirmed) ⇒ vào recovery từ boot menu / USB cứu hộ đã ký (ánh xạ RECOVERY_REQUIRED — xem §5). |

> **Về state kỹ thuật PL15 §2:** chuỗi journal đặc tả (DISCOVERED → ELIGIBLE → … → COMMITTED + RECOVERY_REQUIRED) là **siêu tập**. Prototype **gộp** chúng vào enum `UpdateState` đã hiện thực (ví dụ DOWNLOADED gộp trong `downloading`; PREFLIGHT_OK gộp trong `verified` + field `preflight`; BOOTING_NEW gộp trong `reboot_pending`; COMMITTED = `completed`). Ánh xạ này là **thật trong mã**, không bịa.

---

## 3. Chuyển trạng thái + các chuyển KHÔNG đảo được

`VALID_TRANSITIONS` (trích `update_contract.py` — nguồn sự thật):

```
available       → downloading | blocked
downloading     → verified    | blocked
verified        → staged      | blocked
staged          → reboot_pending | blocked
reboot_pending  → boot_check  | blocked
boot_check      → completed | rolled_back | blocked
completed       → (kết thúc)
rolled_back     → (kết thúc)
blocked         → (kết thúc)
```

**Vùng có thể dừng/hoãn an toàn (có nút lùi):**
- `available`/`downloading`: nút **tạm dừng tải**, **Để sau**; đứt mạng giữ `.part` để resume.
- `verified`/`staged`: **Để sau** / **Cài tối nay**; deployment mới đã chuẩn bị nhưng default **vẫn** bản cũ ⇒ chưa đụng hệ đang chạy. Việc chưa lưu ⇒ hoãn reboot (UPD-007).

**Chuyển KHÔNG đảo được / KHÔNG có nút hủy (PL19 §4 "không có nút hủy trong pha boot switch không an toàn"):**
- **`staged → reboot_pending`** (`arm_switch`): thời điểm **đổi con trỏ default nguyên tử** sang bản mới. Từ đây đến khi có kết luận health, **không** có "hủy" của người dùng; chỉ có hai lối ra do máy quyết:
  - `reboot_pending → boot_check → completed` (health đạt), hoặc
  - `reboot_pending → boot_check → rolled_back` (health fail → **tự** quay bản cũ).
  An toàn của vùng này **không** dựa vào người dùng bấm hủy đúng lúc, mà dựa vào: (a) đổi con trỏ là **nguyên tử** (`os.replace`), (b) bản cũ confirmed **không** bị xóa, (c) mất điện giữa chừng ⇒ `recover()` tự quay về bản confirmed.
- **Trạng thái kết thúc** `completed` / `rolled_back` / `blocked` là `frozenset()` — **không** chuyển tiếp. Một bản `blocked` **không bao giờ** đi tiếp sang `staged`/`completed` (không "cài dù sao").

---

## 4. Quy tắc chống "Hoàn tất giả" (anti-false-completed)

Bất biến cứng, enforce trong mã (`update_contract.py`):

1. **`completed` CHỈ tới từ `boot_check`.** `transition()`:
   `if new_state == COMPLETED and self.state != BOOT_CHECK: raise IllegalTransition("'completed' chỉ tới được sau 'boot_check'...")`.
2. **`boot_check` chỉ tới từ `reboot_pending`** (đã staged + đã xác minh chữ ký) — không đường tắt.
3. **`verified` và mọi state sau** (`staged/reboot_pending/boot_check/completed`) **đòi** `signature_status=='verified'` (`validate()` `requires_verified_sig`). Không ký đạt ⇒ không có đường tới completed.
4. **Một tool apt/cài trả "success" KHÔNG đủ** để nâng `completed` — phải qua **boot-health thật** (`BootHealthChecker`: 4 probe tới hạn + ngưỡng + UI-crash-lặp + boot-counter). Health fail ⇒ **luôn** `rolled_back`, **không bao giờ** `completed`.
5. **UI không nói "đã cập nhật xong" ở `staged`** (PL15 UI §3.4): chỉ "đã chuẩn bị xong, chọn giờ khởi động".

Hệ quả người dùng: màn **Hoàn tất** chỉ hiện sau khi máy đã boot bản mới **và** vượt kiểm tra khởi động; nếu không, hiện **Đã khôi phục** (kèm báo cáo + lưu ý kiểm dữ liệu ở app có migration) hoặc **Cần hỗ trợ**.

---

## 5. Guard tóm tắt theo cạnh

| Cạnh | Guard (điều kiện ĐẠT mới đi) | Nếu hỏng |
| --- | --- | --- |
| available → downloading | Chế độ người dùng cho phép / bấm Tải; mạng+ổ đủ theo chế độ | blocked UPD-001/UPD-002 |
| downloading → verified | **Chữ ký ∧ hash ∧ hạn ∧ không-thu-hồi ∧ arch/model** đều đạt (fail-closed) | blocked UPD-003/004/009/005 |
| verified → staged | Preflight pass (storage/power/network) **∧** MigrationGuard cho (backup `restore_verified` + `dry_run_ok`, hoặc không có migration) | blocked UPD-002/001/006/**010** |
| staged → reboot_pending | Deployment mới `is_complete` **∧** không còn việc chưa lưu (hoặc người dùng chấp nhận) | UPD-007 (hoãn), giữ `staged` |
| reboot_pending → boot_check | Đã reboot vào bản mới | recover() quay bản cũ nếu mất điện |
| boot_check → completed | Boot-health **đạt** (critical probes + ngưỡng + không UI-crash-lặp, trong `max_boot_attempts`) | — |
| boot_check → rolled_back | Boot-health **fail** ⇒ tự rollback về bản confirmed | UPD-008 (report) |
| bất kỳ non-terminal → blocked | Lỗi xác thực/preflight/migration | error_code bắt buộc |

**RECOVERY_REQUIRED (ánh xạ "Cần hỗ trợ" mức nặng):** nếu `rollback_to_previous()`/`recover()` **không** tìm được bản confirmed để quay về (`latest_confirmed()==None` ⇒ `bootable=False`), máy **không** tự khôi phục được ⇒ hướng người dùng vào **recovery từ boot menu** hoặc **USB cứu hộ đã ký** (ADR 0014/0020). Enum đã hiện thực chưa có state `recovery_required` riêng — đây là **khoảng trống trung thực** cần bổ sung khi nối bootloader thật.

---

## 6. Khoảng trống trung thực

- Prototype mô phỏng **A-B nguyên tử** (hai slot + con trỏ rename); NaMiOS alpha thật là **snapshot Timeshift + GRUB previous-entry**, **KHÔNG** nguyên tử (ADR 0020). Đọc máy trạng thái này như **đặc tả hành vi đích**, không phải "đã chạy trên máy thật".
- `boot_check` dùng probe **tiêm vào** (mô phỏng). Probe thật (`dpkg --audit`/`systemctl`/`mountpoint`/ping/plasmashell/D-Bus) nằm ở `namios-health-check.sh` (hook 0640) — chưa nối vào máy trạng thái.
- `RECOVERY_REQUIRED` chưa là state nội bộ riêng (xem §5).
- Chưa chạy U19-01…14 trên VM/máy thật; power-cut thật + ring rollout = **nhóm B**.
