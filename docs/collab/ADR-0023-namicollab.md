# ADR 0023 — NaMiCollab: cộng tác + lưu trữ, ba giai đoạn (M4)

- **Trạng thái:** proposed · **Mức thực thi:** Giai đoạn 1 `partial` (prototype
  logic chạy + **35/35 pytest PASS** ở mức filesystem cục bộ — xem
  `tools/namios-collab/`; **CHƯA** test trên SMB/WebDAV server thật, **CHƯA**
  nối vào LibreOffice/Dolphin/NaMiOffice UI, **CHƯA** máy thật). Giai đoạn 2
  `specified` (thiết kế, **chưa viết code, chưa có server**). Giai đoạn 3
  `specified` ở mức **C3** (thiết kế, **không khả thi** bằng NaMiOffice/LO
  fork hiện tại — cần engine CRDT/OT riêng, chỉ gắn nhãn "cùng sửa trực
  tiếp" sau khi qua test-gate ở §4).
- **Ngày:** 10/11/2026
- **Năng lực:** `docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md` §4
  "Cộng tác và lưu trữ — một sản phẩm dịch vụ riêng". ADR này chốt **thiết
  kế 3 giai đoạn** đúng văn bản kit và hiện thực **Giai đoạn 1 ở mức
  logic/prototype** — mức duy nhất làm được ở môi trường build hiện tại
  (không server, không máy thật — xem `CLAUDE.md` §Môi trường build).
- **Liên quan:** `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §5 (NaMiCollab
  — đã nêu 3 giai đoạn ở mức tóm tắt, ADR này **không mâu thuẫn**, chỉ
  **chi tiết hóa** + gắn prototype thật); `docs/office/COMPAT-MATRIX.md`
  mục "Cộng tác & lưu trữ" (`CL-01`..`CL-05`); `docs/office/feature-registry.json`
  (cùng 5 dòng CL); ADR 0007 (cập nhật + ký metadata, fail-closed — mô hình
  tin cậy tham chiếu cho Giai đoạn 2/3); ADR 0017 (ranh giới ba thành phần —
  mẫu áp dụng cho ranh giới NaMiCollab-UI / NaMiCollab-Service /
  SmartAI-chỉ-đọc ở Giai đoạn 2). Prototype: `tools/namios-collab/`.

> **Không đổi quyết định đã có.** `ECOSYSTEM-MAIL-NOTES-FORMS.md` §5 đã ghi
> "NaMiCollab — CHƯA PHÁT HÀNH" và liệt kê 3 giai đoạn ở mức tóm tắt; ADR này
> **giữ nguyên** phân loại đó, chỉ bổ sung: (a) chi tiết thiết kế Giai đoạn
> 2/3 mà tài liệu đó chưa đi sâu, (b) **prototype logic thật** cho Giai đoạn
> 1 (tài liệu đó mới dừng ở "LO mở SMB/WebDAV sẵn có, chưa kiểm UX"), (c)
> test-gate rõ ràng trước khi được gắn nhãn "cùng sửa trực tiếp" ở Giai
> đoạn 3.

## Bối cảnh

NaMiOS hiện có **hạ tầng mạng/lưu trữ sẵn có** (không phải viết mới):
Samba/CIFS client + WebDAV qua KIO của Dolphin (`0160-network.list.chroot`,
`0720-connectivity.list.chroot` — xem `ECOSYSTEM-MAIL-NOTES-FORMS.md` §5).
LibreOffice (nền NaMiOffice) đã có cơ chế lock sidecar riêng dạng
`.~lock.<tên file>.<đuôi>#` chứa `user,host,date,appdatadir`, so sánh mốc
thời gian để phát hiện lock "cũ" [1][5]. Đây là **tầng lock đã tồn tại**,
độc lập với mọi thứ ADR này thêm vào — NaMiCollab Giai đoạn 1 **không thay
thế** cơ chế đó, mà thêm một lớp **advisory lock + conflict-detector +
version-history tầng ứng dụng** có thể dùng cho cả file LibreOffice và các
loại tài liệu khác (NaMiNotes, v.v.) mà LibreOffice không quản lý.

Kit (03_MAIL_NOTES_FORMS_COLLAB.md §4) chốt rõ **ba giai đoạn, không nhảy
cóc**, và một ràng buộc cứng xuyên suốt về dữ liệu nhạy cảm + cloud. ADR này
áp dụng nguyên văn, không nới ra.

## Quyết định — ba giai đoạn

### Giai đoạn 1 — file local/SMB/WebDAV, không cần cloud để dùng Office

**Mục tiêu (kit):** "file local/SMB/WebDAV theo quyền, locks, cảnh báo
conflict, lịch sử bản cục bộ, link chia sẻ qua hệ thống sẵn có; không yêu
cầu cloud để dùng Office."

**Thiết kế:**

1. **Lưu trữ** — dùng nguyên hạ tầng đã có: file trên local disk, SMB
   mount (`smb://`), WebDAV mount (`webdav://` hoặc `dav://`) qua KIO/GIO —
   **không viết server/protocol mới**. "Link chia sẻ" ở giai đoạn này nghĩa
   là chia sẻ qua **hệ thống mạng nội bộ sẵn có** (Samba share, WebDAV
   path), không phải link có hạn kiểu Giai đoạn 2.
2. **Lock** — hai tầng song song, không trộn lẫn:
   - Tầng có sẵn: LibreOffice `.~lock.*#` cho file đang mở trong Writer/
     Calc/Impress [1][5].
   - Tầng mới (ADR này, `tools/namios-collab/namios_collab/lock_manager.py`):
     **advisory lock exclusive/shared** tầng ứng dụng, dùng sidecar JSON
     `<path>.namilock.json`, mô hình giống `LOCK`/`UNLOCK` của WebDAV
     (exclusive loại trừ mọi lock khác; shared cho phép nhiều reader, loại
     trừ exclusive) [2][3] — để dùng được cho **cả tài liệu NaMiOffice và
     loại tài liệu khác** (NaMiNotes, v.v.) mà bản thân format không có
     cơ chế lock riêng.
3. **Phát hiện conflict** — `conflict_detector.py`: mô hình optimistic
   concurrency ba hash (base/current/new), giống nguyên lý
   "three-way merge" của Git [4] — nhưng **không tự merge**, chỉ phân loại
   `clean` / `needs_merge` (định dạng text có cơ hội merge dòng) /
   `conflict` (container nhị phân ODF/OOXML, phải chọn giữ bản nào).
4. **Lịch sử bản cục bộ** — `version_store.py`: snapshot/list/restore vào
   sidecar `<path>.namihistory/`, mỗi bản có hash SHA-256, **không bao giờ
   restore mà không tự chụp bản an toàn của trạng thái hiện tại trước**.
5. **Quyền** — giai đoạn này **dùng nguyên quyền hệ điều hành/SMB/WebDAV
   đã có** (POSIX permission, SMB ACL phía server) — **không** tự dựng hệ
   quyền mới; "theo quyền" trong câu kit nghĩa là tôn trọng quyền sẵn có,
   không bypass.

**Trạng thái thật:** prototype logic (`tools/namios-collab/`) đã chạy, pytest
**35/35 PASS** trên filesystem cục bộ (`tmp_path`, mô phỏng SMB/WebDAV mount
bằng một thư mục local — **chưa phải mount SMB/WebDAV thật**). Xem
`docs/collab/NAMICOLLAB-PHASE-MATRIX.md` cho C-level đầy đủ và danh sách
việc còn lại trước khi gọi "đạt Giai đoạn 1" (kiểm trên mount SMB/WebDAV
thật, nối vào LibreOffice/Dolphin, UX cảnh báo cho người dùng cuối).

### Giai đoạn 2 — server NaMiCollab hoặc tích hợp nền được phê duyệt

**Mục tiêu (kit):** "một server NaMiCollab hoặc tích hợp nền được phê
duyệt, tài khoản/tổ chức, ACL theo tệp, version history, comments/mentions,
share link hết hạn, offline sync và conflicts."

**Thiết kế (CHỈ thiết kế — chưa viết code, chưa có server):**

- **Kiến trúc 3 thành phần**, theo đúng mẫu đã chốt ở ADR 0017 cho Update
  Service (UI ↔ Service đặc quyền ↔ SmartAI chỉ-đọc): **NaMiCollab Client**
  (plugin NaMiOffice/Dolphin, không giữ secret) ↔ **NaMiCollab Service**
  (API có auth, giữ token/ACL, KHÔNG chạy trong tiến trình NaMiOffice) ↔
  **NaMiCollab Server** (lưu file + metadata + audit).
- **Tài khoản/tổ chức:** mô hình org → user → role, tối thiểu `owner` /
  `editor` / `commenter` / `viewer` theo file, không phải theo toàn server.
- **ACL theo tệp:** mỗi file có bảng quyền riêng (không kế thừa ngầm toàn
  thư mục trừ khi khai báo rõ), audit log mọi thay đổi ACL.
- **Version history (server-side):** mở rộng mô hình `version_store.py`
  của Giai đoạn 1 (snapshot + hash + verify) sang multi-user — mỗi version
  gắn tác giả + conflict-resolution trail, không chỉ hash+timestamp.
- **Comments/mentions:** gắn vào vị trí trong tài liệu (đoạn/ô/slide),
  thông báo người được mention — cần schema riêng theo từng loại tài liệu
  (Writer/Sheet/Slides khác cấu trúc anchor).
- **Share link hết hạn:** token ký (không phải UUID đoán được), TTL bắt
  buộc, scope (xem/sửa/comment), revoke tức thì, log truy cập qua link.
- **Offline sync + conflicts:** client giữ bản local + queue thay đổi khi
  mất mạng; khi có mạng lại, đồng bộ qua `conflict_detector.py` (tái dùng
  mô hình base/current/new) — nếu `conflict` (container nhị phân) phải hỏi
  người dùng, **không** tự chọn bản thắng.
- **An toàn (bắt buộc trước khi vận hành thật):** mã hóa khi truyền (TLS)
  + khi lưu (at-rest) [6]; rotate/refresh token hết hạn; threat model riêng
  (tham chiếu mô hình fail-closed của ADR 0007/`UPDATE-THREAT-MODEL.md`:
  sai token/hết hạn/thu hồi ⇒ chặn, không có "cho qua vì tiện").

**Trạng thái thật:** `specified` — **chưa có một dòng code server nào**,
**chưa có hạ tầng vận hành** (domain, TLS cert, DB, backup, SLA). Đây là
**sản phẩm/dịch vụ riêng** cần quyết định đầu tư (tự host vs managed) trước
khi bắt đầu — ngoài phạm vi "làm được ở môi trường build hiện tại".

### Giai đoạn 3 — đồng tác giả thời gian thực

**Mục tiêu (kit):** "cần protocol/CRDT/OT hoặc engine được chứng minh,
phân quyền và audit; chỉ gắn 'cùng sửa trực tiếp' sau test mất mạng,
2–20 người cùng sửa, merge và không mất nội dung."

**Thiết kế (CHỈ thiết kế — không khả thi bằng NaMiOffice/LibreOffice fork
hiện tại, đã chốt **C3** ở `COMPAT-MATRIX.md` dòng `CL-03`):**

- **Lựa chọn engine đã biết (không tự viết CRDT/OT từ đầu — rủi ro
  correctness rất cao):** CRDT kiểu **Yjs** [7] hoặc **Automerge** [8] cho
  dữ liệu có cấu trúc (text + rich metadata); hoặc **OT** kiểu
  Collabora Online/OnlyOffice-online (LibreOffice Online là **sản phẩm
  server riêng**, khác NaMiOffice desktop fork — không quy đổi 1:1).
- **Kiến trúc tối thiểu:** mỗi tài liệu có một "document session" trên
  NaMiCollab Server (Giai đoạn 2 đã có account/ACL) giữ CRDT state +
  broadcast patch qua WebSocket tới các client đang mở; client áp patch
  vào buffer riêng rồi render lại UI NaMiOffice (**cần hook sâu vào UNO/
  model nội bộ của LibreOffice — chưa đánh giá độ khả thi kỹ thuật, đây
  là rủi ro kiến trúc lớn nhất của giai đoạn 3, không phải chỉ vấn đề
  network**).
- **Audit + phân quyền thời gian thực:** mọi patch phải gắn tác giả +
  timestamp, có thể replay để điều tra; quyền sửa/chỉ-xem phải chặn ở tầng
  server (không tin client).

**Test-gate — ĐIỀU KIỆN BẮT BUỘC trước khi gắn nhãn "cùng sửa trực tiếp"
("real-time co-authoring") ở BẤT KỲ UI/docs/landing page nào:**

1. **Test mất mạng giữa chừng:** một client mất kết nối khi đang gõ, gõ
   tiếp offline, kết nối lại — phải merge đúng, không mất ký tự, không
   tạo bản sao trùng.
2. **Test 2–20 người cùng sửa cùng lúc** trên cùng vùng tài liệu — không
   có "last write wins" làm mất nội dung của người khác.
3. **Test merge không mất nội dung** qua nhiều vòng edit chồng chéo (ví dụ
   kịch bản fuzz: N client random-edit trong T giây, so sánh kết quả hội tụ
   của mọi client phải giống nhau bit-for-bit và chứa đúng tổng các edit).
4. Audit log đọc lại được toàn bộ phiên, không có patch "biến mất".

**Trạng thái thật:** `specified`, **C3** — chưa viết một dòng code CRDT/OT
nào, chưa chọn engine chính thức, chưa có server Giai đoạn 2 để gắn vào.
**Không được tuyên bố "NaMiOS có đồng tác giả thời gian thực" ở bất kỳ đâu
cho tới khi cả 4 test ở trên có bằng chứng PASS cụ thể** (log/video/report,
không phải "đã code nên chắc chạy").

## Ràng buộc cứng xuyên suốt 3 giai đoạn (nguyên văn kit — không nới)

- **Không** chuyển trực tiếp tài liệu nhạy cảm sang dịch vụ **cloud AI**
  hoặc bên thứ ba. SmartAI (ADR 0018) mặc định local-first; NaMiCollab
  Giai đoạn 2/3 **không** tự động đẩy nội dung tài liệu qua endpoint AI nào
  khi chưa có opt-in rõ ràng của người dùng/tổ chức.
- **Tích hợp OneDrive/SharePoint/Google Drive** (nếu làm — chưa có kế
  hoạch cụ thể, chỉ là chính sách nếu tương lai làm): phải theo
  **least-privilege / scope tối thiểu**, hiển thị rõ nhà cung cấp + chỗ lưu
  + chính sách dữ liệu cho người dùng thấy TRƯỚC khi cấp quyền, xử lý được
  token hết hạn và API nhà cung cấp đổi (không "crash âm thầm" khi OAuth
  scope bị provider thu hẹp).
- **IRM/nhãn bảo mật Microsoft 365:** file có nhãn IRM có thể **không mở
  được** ngoài client chính chủ — NaMiCollab (mọi giai đoạn) **không né
  tránh** bảo vệ đó, không cố bẻ khóa/giả mạo client được cấp quyền (đã
  chốt C3 ở `CL-05`, giữ nguyên).

## Ánh xạ prototype → khái niệm đích (Giai đoạn 1 → 2/3)

| Khái niệm trong prototype (`tools/namios-collab/`) | Vai trò ở Giai đoạn 1 (đã làm) | Mở rộng cho Giai đoạn 2/3 (thiết kế, chưa làm) |
| --- | --- | --- |
| `LockManager` (`lock_manager.py`) — sidecar JSON, exclusive/shared, stale theo lease+pid | Khóa advisory cục bộ, 1 máy/1 mount point | Giai đoạn 2: lock chuyển thành bản ghi trên server (không phải sidecar file) để nhiều máy thấy cùng trạng thái; Giai đoạn 3: lock "intent to edit" không còn cần nữa vì CRDT cho phép sửa đồng thời thật |
| `file_mutex` (`_util.py`, `O_CREAT|O_EXCL`) | Cửa hẹp race-free cho đọc-sửa-ghi sidecar | Giai đoạn 2: thay bằng transaction DB (Postgres `SELECT ... FOR UPDATE` hoặc tương đương) — filesystem mutex không scale ra nhiều máy |
| `ConflictReport`/`detect()` (`conflict_detector.py`) — base/current/new hash, clean/needs_merge/conflict | Phát hiện xung đột cục bộ khi lưu lại file đã bị người khác đổi | Giai đoạn 2: cùng mô hình áp cho offline-sync; Giai đoạn 3: thay hẳn bằng CRDT merge tự động — không còn "phát hiện rồi hỏi người dùng" cho vùng dữ liệu CRDT quản lý (vẫn cần cho phần ngoài phạm vi CRDT, ví dụ đổi tên file) |
| `LocalVersionHistory` (`version_store.py`) — snapshot/restore, luôn chụp bản an toàn trước khi ghi đè | Lịch sử 1 máy, không có tác giả đa người | Giai đoạn 2: version gắn tác giả + tổ chức, lưu trên server, có thể xem diff giữa 2 version của 2 người khác nhau |

## Trung thực về giới hạn (KHÔNG được quảng cáo quá)

- **Giai đoạn 1 là "advisory", không phải "mandatory".** `LockManager` chỉ
  có hiệu lực với tiến trình nào CŨNG gọi nó — không chặn được ai đó ghi
  trực tiếp vào file qua `cp`/editor khác. Đây đúng bản chất "advisory
  lock" (khác `flock()` mandatory ở một số hệ) — không được mô tả thành
  "khóa file tuyệt đối".
- **Gate mutex `O_CREAT|O_EXCL` race-free trên local ext4 và hầu hết SMB
  mount hiện đại, nhưng CHƯA kiểm trên NFS/WebDAV server cụ thể nào** — một
  số NFS cũ (trước NFSv3 lock đầy đủ) không đảm bảo `O_EXCL` nguyên tử qua
  mạng. Trước khi tuyên bố "khóa an toàn qua WebDAV", cần test trên server
  WebDAV thật (pilot — xem PHASE-MATRIX).
- **Conflict detector không tự merge.** `needs_merge` chỉ là gợi ý "định
  dạng CÓ CƠ HỘI merge theo dòng" — không có engine 3-way merge thật trong
  prototype này.
- **Version history không thay backup hệ thống.** Đây là lịch sử CỤC BỘ
  theo từng file, không nén/dedupe, không mã hóa riêng, không đồng bộ nhiều
  máy — khác hoàn toàn Kup/bup (ADR 0014/0020, backup `/home`).
- **Giai đoạn 2 chưa có một dòng code/server nào** — mọi mục ở §Giai đoạn 2
  là thiết kế để tránh vừa-làm-vừa-nghĩ, không phải tiến độ đã đạt.
- **Giai đoạn 3 là C3 — không khả thi bằng NaMiOffice/LibreOffice fork
  hiện tại** theo đúng phân loại đã chốt ở `COMPAT-MATRIX.md` (`CL-03`,
  "Không giả bằng nút menu" là quy tắc cứng của kit). Không có dòng mã
  CRDT/OT nào trong repo ở thời điểm ADR này viết.
- **Prototype chỉ test trên filesystem cục bộ (`tmp_path`/thư mục tạm,
  không có mount SMB/WebDAV thật trong môi trường build hiện tại — xem
  `CLAUDE.md` §Môi trường build).** 35/35 pytest PASS chứng minh ĐÚNG LOGIC
  (race-free giữa nhiều luồng, phân loại conflict đúng theo định dạng,
  restore không mất dữ liệu) — **KHÔNG** chứng minh hành vi trên SMB/WebDAV
  server thật, trên nhiều máy thật, hay khi tích hợp vào LibreOffice/Dolphin
  UI. Bước đó là **pilot**, chưa chạy.

## Hệ quả

- Giai đoạn 1: nối `tools/namios-collab/namios_collab/` vào một UX cụ thể
  (ví dụ: Dolphin service menu "Khóa để sửa" / NaMiOffice sidebar hiển thị
  trạng thái khóa + lịch sử) — hiện vẫn là **module Python độc lập**, chưa
  có UI. Test trên mount SMB/WebDAV thật (Samba server + WebDAV server lab)
  trước khi gọi "đạt Giai đoạn 1" theo đúng cảnh báo ở `COMPAT-MATRIX.md`
  ("'Có nút menu' chưa đủ").
- Giai đoạn 2: cần quyết định đầu tư (server tự host vs dịch vụ nền được
  phê duyệt) trước khi bắt đầu code — ngoài phạm vi ADR này.
- Giai đoạn 3: KHÔNG bắt đầu trước khi Giai đoạn 2 có server thật để gắn
  CRDT session vào, và KHÔNG tuyên bố "cùng sửa trực tiếp" trước khi qua
  đủ 4 test ở §Giai đoạn 3.
- Cập nhật `docs/office/COMPAT-MATRIX.md`/`feature-registry.json` dòng
  `CL-01` khi Giai đoạn 1 có UX thật + test SMB/WebDAV pilot (hiện vẫn giữ
  **C2** — ADR này KHÔNG tự nâng C-level, chỉ thêm prototype làm bằng
  chứng cho bước tiếp theo).

## Nguồn

- [1] LibreOffice/OpenOffice document lock file (`.~lock.<file>#`,
  nội dung `user,host,date,appdatadir`, so mốc thời gian để phát hiện lock
  cũ): https://ask.libreoffice.org/t/globally-disable-lock/47757 ;
  https://forum.openoffice.org/en/forum/viewtopic.php?t=111180
- [2] RFC 4918 — HTTP Extensions for WebDAV (LOCK method, lock-token,
  shared vs exclusive lock, bảng tương thích lock):
  https://www.rfc-editor.org/rfc/rfc4918 ;
  https://www.rfc-editor.org/info/rfc4918/
- [3] MS-SMB2 — Oplock/Lease trên SMB2/3 (mô hình lease cho file đang mở
  đồng thời, tham khảo năng lực tầng dưới của SMB mount, KHÔNG dùng trong
  prototype này — prototype dùng advisory lock tầng ứng dụng riêng):
  https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/50855e7c-0d71-41b7-a005-cc08f728c03a
- [4] Git three-way merge (nguyên lý base/ours/theirs tham khảo cho mô hình
  base/current/new của `conflict_detector.py`): https://git-scm.com/docs/git-merge
- [5] File locking (advisory vs mandatory, khái niệm chung):
  https://en.wikipedia.org/wiki/File_locking
- [6] OWASP — mã hóa khi truyền/khi lưu, quản lý token/phiên (tham khảo
  thiết kế an toàn Giai đoạn 2, chưa có code):
  https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html
- [7] Yjs — CRDT cho ứng dụng cộng tác: https://yjs.dev/ ; https://docs.yjs.dev/
- [8] Automerge — CRDT library + sync protocol: https://automerge.org/ ;
  https://github.com/automerge/automerge
- ADR 0007 (cập nhật + ký metadata, fail-closed); ADR 0017 (ranh giới ba
  thành phần); ADR 0018 (SmartAI core, local-first);
  `docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md` §4;
  `docs/office/ECOSYSTEM-MAIL-NOTES-FORMS.md` §5;
  `docs/office/COMPAT-MATRIX.md` (`CL-01`..`CL-05`);
  `tools/namios-collab/`.
