# NaMiCollab — Ma trận giai đoạn (ngắn, trung thực)

**Ngày:** 10/11/2026 · **Đọc cùng:** `docs/collab/ADR-0023-namicollab.md`
(thiết kế đầy đủ 3 giai đoạn) và `docs/office/COMPAT-MATRIX.md` mục
"Cộng tác & lưu trữ" (`CL-01`..`CL-05` — ADR 0023 **không đổi** C-level ở
đó, chỉ thêm prototype làm bằng chứng cho bước kế tiếp).

## Tóm tắt một dòng mỗi giai đoạn

| Giai đoạn | Có gì NGAY BÂY GIỜ (môi trường dev này) | Còn thiếu gì | C-level (`COMPAT-MATRIX.md`) |
| --- | --- | --- | --- |
| **1 — Local/SMB/WebDAV, lock, conflict, lịch sử cục bộ** | **Prototype logic chạy thật**, `tools/namios-collab/` — 35/35 pytest PASS (lock exclusive/shared + stale, conflict clean/needs_merge/conflict, snapshot/restore có verify hash) | Test trên mount SMB/WebDAV **thật** (pilot); nối vào LibreOffice/Dolphin UI; UX cảnh báo cho người dùng cuối | `CL-01` **C2** (giữ nguyên — chưa đủ bằng chứng để nâng) |
| **2 — Server NaMiCollab (account/ACL/version/comments/share-link/offline-sync)** | **Chỉ thiết kế** (ADR-0023 §Giai đoạn 2) — kiến trúc 3 thành phần, mô hình ACL/account/share-link | **Toàn bộ:** chưa một dòng code server, chưa hạ tầng (domain/TLS/DB/backup/SLA), chưa quyết định tự host vs managed | `CL-02` **C3** (giữ nguyên) |
| **3 — Đồng tác giả thời gian thực (CRDT/OT)** | **Chỉ thiết kế** (ADR-0023 §Giai đoạn 3) — chọn hướng engine (Yjs/Automerge), test-gate 4 điều kiện trước khi claim | **Toàn bộ:** chưa chọn engine chính thức, chưa code, chưa có server Giai đoạn 2 để gắn vào, chưa chạy test mất-mạng/2-20-người/merge/audit | `CL-03` **C3** (giữ nguyên — "Không giả bằng nút menu") |

## Giai đoạn 1 — chi tiết "cho ai muốn dùng/kiểm ngay"

**Đã có (verified bằng pytest, chạy trong môi trường này, không cần
mạng/server):**

- `namios_collab.lock_manager.LockManager` — khóa advisory exclusive/shared
  trên một path, sidecar `<path>.namilock.json`; phát hiện + dọn stale lock
  (lease hết hạn HOẶC cùng host + pid đã chết); race-free giữa nhiều
  luồng/tiến trình nhờ gate `O_CREAT|O_EXCL` — test bằng 2 "người dùng"
  (thread) giành khóa đồng thời: đúng 1 thắng, không double-grant.
- `namios_collab.conflict_detector.detect()`/`detect_from_disk()` — so
  base-hash / current-hash / new-hash, phân loại `clean` / `needs_merge`
  (định dạng text như `.md`/`.csv`/`.json`) / `conflict` (container nhị
  phân như `.docx`/`.xlsx`/`.pptx`/`.odt` hoặc file đã bị xóa).
- `namios_collab.version_store.LocalVersionHistory` — snapshot (hash
  SHA-256 + nhãn), list, restore; **restore luôn tự chụp bản an toàn của
  trạng thái hiện tại trước khi ghi đè** (trừ khi không có gì để mất); sau
  khi ghi, verify lại hash — sai thì chặn, không âm thầm coi như xong.

**Chưa có (không được coi là "đạt Giai đoạn 1" cho tới khi xong):**

1. Chạy lại đúng 3 bộ test trên **mount SMB thật** (Samba server lab) và
   **mount WebDAV thật** — môi trường build hiện tại không có server để
   mount (xem `CLAUDE.md` §Môi trường build). Gate mutex `O_CREAT|O_EXCL`
   được tài liệu hóa là race-free trên local ext4 + hầu hết SMB hiện đại,
   nhưng **chưa đo thật** trên một server cụ thể.
2. UI/UX: không có nút/menu nào trong Dolphin/NaMiOffice gọi tới
   `namios_collab` — hiện là module Python độc lập, gọi được qua API/CLI
   thủ công, chưa có trải nghiệm người dùng cuối.
3. Không nối với lock sẵn có của LibreOffice (`.~lock.*#`) — hai tầng lock
   chạy độc lập, chưa có lớp hợp nhất hiển thị MỘT trạng thái khóa cho
   người dùng.
4. Không có hàng đợi/chờ-khóa (prototype trả lỗi ngay khi conflict, không
   block/retry tự động) — đúng ý định thiết kế (giống UX "đang được người
   khác mở" của LibreOffice), không phải thiếu sót, nhưng cần UI xác nhận
   lại hành vi này là mong muốn trước khi ship.

## Giai đoạn 2/3 — vì sao chưa đổi C-level

- **Giai đoạn 2** đòi "server + account + ACL + ... + offline sync" — đây
  là **sản phẩm/dịch vụ riêng** cần hạ tầng vận hành thật (không chạy được
  bằng cách thêm file Python vào repo). ADR-0023 chỉ **thiết kế** kiến
  trúc; không có server nào tồn tại để test, nên giữ `C3`.
- **Giai đoạn 3** đòi CRDT/OT đã chứng minh + 4 test-gate cụ thể (mất mạng,
  2–20 người, merge không mất nội dung, audit) TRƯỚC khi được gắn nhãn
  "cùng sửa trực tiếp". Chưa chọn engine, chưa viết code, chưa có Giai
  đoạn 2 để gắn vào ⇒ giữ `C3` theo đúng quy tắc kit "Không giả bằng nút
  menu".

## Chạy lại bằng chứng Giai đoạn 1

```bash
cd tools/namios-collab
python3 -m pytest tests/ -v
# 35 passed
```

Không cần mạng, không cần quyền root, không cần SMB/WebDAV server — chạy
được trên bất kỳ máy có Python 3.11+ (chỉ thư viện chuẩn).
