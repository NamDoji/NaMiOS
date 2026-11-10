# tools/namios-collab — NaMiCollab Giai đoạn 1 (prototype logic)

Đọc trước: `docs/collab/ADR-0023-namicollab.md` và
`docs/collab/NAMICOLLAB-PHASE-MATRIX.md`.

Prototype **logic thuần Python** (không server, không mạng, chỉ thư viện
chuẩn) cho Giai đoạn 1 của NaMiCollab (`03_MAIL_NOTES_FORMS_COLLAB.md` §4):
file local/SMB/WebDAV theo quyền, locks, cảnh báo conflict, lịch sử bản
cục bộ — không cần cloud để dùng Office.

## Cấu trúc

```
tools/namios-collab/
├── namios_collab/
│   ├── _util.py             # atomic write, sha256, file_mutex (O_CREAT|O_EXCL)
│   ├── lock_manager.py      # LockManager: exclusive/shared advisory lock, stale detect
│   ├── conflict_detector.py # detect(): base/current/new hash -> clean/needs_merge/conflict
│   └── version_store.py     # LocalVersionHistory: snapshot/list/restore + verify hash
└── tests/
    ├── test_lock_manager.py
    ├── test_conflict_detector.py
    └── test_version_store.py
```

## Chạy test

```bash
cd tools/namios-collab
python3 -m pytest tests/ -v
```

Kết quả hiện tại: **35/35 PASS**, chạy trên filesystem cục bộ (`tmp_path`
của pytest) — không cần mạng, không cần SMB/WebDAV server, không cần root.

## Dùng thử nhanh (API, chưa có CLI/UI)

```python
from namios_collab import LockManager, LockMode, detect_from_disk, LocalVersionHistory

mgr = LockManager()
handle = mgr.acquire("/path/to/BaoCao.odt", owner="giaovien_a", mode=LockMode.EXCLUSIVE)
# ... sửa file ...
mgr.release(handle)

history = LocalVersionHistory()
entry = history.snapshot("/path/to/BaoCao.odt", label="truoc khi sua")
# ... lỡ sửa hỏng ...
history.restore("/path/to/BaoCao.odt", entry.version_id)  # tự chụp safety snapshot trước khi ghi đè
```

## Giới hạn trung thực (đọc trước khi dùng cho việc thật)

- **Advisory, không mandatory.** Chỉ có hiệu lực giữa các tiến trình CŨNG
  gọi `LockManager` — không chặn được ghi trực tiếp bằng công cụ khác.
- **Chưa test trên SMB/WebDAV server thật** — chỉ test trên filesystem cục
  bộ (xem `CLAUDE.md` §Môi trường build: máy này không có server để mount).
  Đây là bước **pilot còn treo**, không phải đã hoàn tất.
- **Chưa nối vào LibreOffice/Dolphin/NaMiOffice UI** — hiện là module
  Python độc lập, không có nút/menu nào gọi tới nó.
- **`conflict_detector` không tự merge** — chỉ phân loại, việc merge/chọn
  bản nào là quyết định ở tầng trên (người dùng hoặc UX tương lai).
- **`version_store` không thay backup hệ thống** (Kup/bup, ADR 0014/0020)
  — là lịch sử cục bộ theo từng file, không nén/dedupe, không mã hóa riêng.

Chi tiết đầy đủ về Giai đoạn 2 (server, chưa viết code) và Giai đoạn 3
(CRDT/OT thời gian thực, C3, chưa khả thi bằng fork LibreOffice) xem
`docs/collab/ADR-0023-namicollab.md`.
