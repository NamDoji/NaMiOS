# SEC-I18N — Verify tổng (03/11/2026)

Vai trò: verify độc lập toàn bộ đợt nâng cấp COMMON i18n (VI/EN song ngữ) +
security sweep do 3 work-package khác giao (I18N, SEC, WIRE). KHÔNG sửa file
nào ngoài `qa/evidence-index/SEC-I18N/**`.

## 1. Full test suite

```
.venv/bin/python -m pytest tests -q -p no:cacheprovider
```

**Kết quả: 980 passed, 1 skipped, 6 xfailed, 0 failed.**

- Baseline 800 xanh giữ nguyên (không test cũ nào vỡ).
- Delta = 28 test i18n unit mới (namios_i18n) + 146 test security sweep mới
  (140 pass + 6 xfail strict = bằng chứng 4 lỗ hổng thật, xem mục 5) + một số
  test CLI mới cho `--lang`/parity.
- 1 skipped, 6 xfailed — khớp đúng với báo cáo của WIRE/SEC, không có fail
  bất ngờ nào. **ĐẠT điều kiện 0 fail và ≥ 800 pass.**

## 2. Gates (lint/format/type)

```
.venv/bin/ruff check src        → All checks passed!
.venv/bin/black --check src     → All done! 94 files would be left unchanged.
.venv/bin/mypy src/namios_i18n  → Success: no issues found in 2 source files
```

Tất cả xanh.

## 3. i18n parity (vi.json ↔ en.json)

Tự load 2 file catalog và so khớp tập key (không dùng lại số do I18N tự báo):

```python
vi = json.load(open("src/namios_i18n/locale/vi.json"))   # 113 keys
en = json.load(open("src/namios_i18n/locale/en.json"))   # 113 keys
missing in en: []
missing in vi: []
→ PARITY_OK
```

**113/113 key trùng khớp 2 bên, không thiếu key nào.**

## 4. Song ngữ thật (chạy CLI thật, không chỉ đọc test)

### 4a. `--help` đổi ngôn ngữ

- `NAMIOS_LANG=vi namios --help` → "NaMiOS CLI (M1 — lõi Python thuần)",
  mô tả subcommand bằng tiếng Việt, mô tả `--lang` tiếng Việt.
- `NAMIOS_LANG=en namios --help` → "NaMiOS CLI (M1 — pure-Python core)", mô
  tả subcommand + `--lang` bằng tiếng Anh.
- **Xác nhận: đổi ngôn ngữ thật, không phải hard-code.**

### 4b. `doctor --json` — machine field KHÔNG đổi theo ngôn ngữ

Chạy `namios doctor --json` với `NAMIOS_LANG=vi` và `=en`, diff 2 output JSON:
chỉ khác duy nhất `operation_id` (UUID random mỗi lần chạy, như thiết kế).
Toàn bộ field còn lại (`status`, `data.host.*`, `data.tooling.*`,
`warnings`, `error`) **byte-for-byte giống nhau**. Đúng hợp đồng
M1-INTERFACES §1/§3: envelope JSON không phụ thuộc `--lang`/`NAMIOS_LANG`.

### 4c. Lớp bọc người-đọc (OK/LỖI↔ERROR) đổi, nội dung message_vi KHÔNG đổi

Ép lỗi thật (`namios catalog validate /tmp/khong-ton-tai.json`):

```
NAMIOS_LANG=vi → "LỖI [E_INPUT_SCHEMA]: Không tải được manifest."   exit=2
NAMIOS_LANG=en → "ERROR [E_INPUT_SCHEMA]: Không tải được manifest." exit=2
```

- Từ bọc đổi `LỖI`→`ERROR` theo ngôn ngữ (catalog `cli.main.render.*`).
- **Nội dung message bên trong ("Không tải được manifest.") giữ tiếng Việt
  ở CẢ HAI trường hợp** — đúng thiết kế cố ý của WIRE (message_vi là field
  hợp đồng dữ liệu, không dịch).
- **Exit code giống nhau (2) ở cả 2 ngôn ngữ** — hành vi máy không đổi.
- Trường hợp `status=ok`: cả 2 ngôn ngữ in `OK (operation_id=...)` giống
  nhau — đúng vì catalog `cli.main.render.ok` cố ý dùng chung chuỗi "OK" ở
  cả vi.json và en.json (viết tắt quốc tế, không cần dịch).

**Kết luận mục 4: song ngữ THẬT ở lớp hiển thị người-đọc (help + từ bọc
OK/LỖI), envelope JSON/exit-code/message_vi là hợp đồng dữ liệu bất biến
theo đúng M1-INTERFACES — không phải song ngữ giả/chỉ-test-mới-qua.**

## 5. Tổng hợp lỗ hổng bảo mật THẬT (đã tự kiểm tra lại độc lập, không chỉ
tin báo cáo của SEC)

Đã đọc trực tiếp source code + chạy lại bằng chứng độc lập (không chỉ chạy
test suite có sẵn) cho cả 4 finding P1/P2 do work-package SEC báo:

### SEC-SWEEP-001 (P1) — `namios_welcome/migrate.py` dòng ~297 vs ~345
**XÁC NHẬN THẬT.** `source_abs = resolve_within(...)` (string) được TÍNH ở
dòng 297, nhưng đọc ở dòng 345 bằng `open(source_abs, "rb")` (builtin,
THEO symlink) — không dùng `open_within`. Trong khi đó phía đích (dest)
CÙNG dòng đã dùng `open_within(...)` đúng cách. Đây là một TOCTOU rõ ràng,
đọc code thấy ngay không cần giả định: cửa sổ race giữa `resolve_within()`
trả về và `open()` thật thi hành cho phép hoán đổi symlink ra ngoài
`source_root`.

### SEC-SWEEP-002 (P1) — `namios_manifest/_safe_io.py` dòng ~52-68
**XÁC NHẬN THẬT.** Hàm `read_text_safe()` tự ghi chú nó là "module tạm/
interim — chờ namios_security của WP8" với TODO rõ ràng chuyển sang
`resolve_within`/`open_within` khi WP8 có hàng thật. WP8 (namios_security)
NAY ĐÃ CÓ hàm FD-based đi từng bước (`resolve_within`/`open_within`,
xem `safe_path.py` dòng ~98-102) nhưng `namios_manifest` CHƯA chuyển sang
dùng — vẫn kiểm `os.path.realpath(path) == abspath(path)` rồi `os.open(path,
O_NOFOLLOW)` lại bằng CHUỖI đường dẫn đầy đủ. `O_NOFOLLOW` chỉ chặn symlink ở
thành phần CUỐI, không chặn thành phần thư mục TRUNG GIAN bị đổi thành
symlink giữa 2 bước. Debt kỹ thuật này đã tồn tại từ khi viết module (ghi rõ
trong docstring) và vẫn chưa được dọn dù `namios_security` đã sẵn sàng.

### SEC-SWEEP-003 (P1) — `namios_security/redactor.py`
**XÁC NHẬN THẬT bằng repro độc lập** (không chỉ chạy lại test có sẵn):

```python
from namios_security.redactor import redact_text
pem = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
redact_text("Error reading file: " + pem)
# → trả về NGUYÊN VẸN khối PEM, không che — xác nhận LEAKED
```
`redact_text()`/`redact_obj()` chỉ che theo TÊN field nhạy cảm, không quét
NỘI DUNG chuỗi tìm mẫu khóa riêng (PEM/OpenSSH). Một traceback hoặc field
`message`/`stdout_log` tự do chứa khối private key sẽ lọt nguyên vẹn qua
lớp chống-rò-rỉ — vi phạm SEC-009 (no-secret-in-log).

### SEC-SWEEP-004 (P2) — `namios_security/safe_path.py` dòng ~203
**XÁC NHẬN THẬT.** `open_within()` xây `open_flags` KHÔNG có `os.O_NONBLOCK`
(dòng 203: `extra_flags | os.O_NOFOLLOW | O_CLOEXEC`, thiếu `O_NONBLOCK`).
Mở một FIFO không có writer qua đường này sẽ treo vô hạn ở `os.open()` kernel
call, TRƯỚC khi kiểm tra "không phải file thường" kịp chạy — đây là DoS khả
thi nếu attacker đặt được FIFO vào đường dẫn bị mở. Đáng chú ý:
`namios_manifest/_safe_io.py` (module khác, xem mục SEC-SWEEP-002) đã TỰ
thêm `O_NONBLOCK` kèm comment giải thích đúng rủi ro này, nhưng hàm chung
`namios_security.open_within` — nơi MỌI module khác lẽ ra phải delegate vào
— lại thiếu. Mức độ P2 vì cần attacker đặt được FIFO tại đường dẫn bị mở
(không phải lỗ hổng từ-xa thuần).

### Không có finding mới nào phát hiện thêm trong quá trình verify-tổng.

Tất cả 4 lỗ hổng trên đều được giữ nguyên trong code (KHÔNG patch — ngoài
phạm vi vai trò verify), có test `xfail(strict=True)` làm bằng chứng tái lập
tại `tests/security/sweep/**` + chi tiết repro tại
`qa/evidence-index/SEC-SWEEP/expected_vs_actual.md`.

## 6. Kết luận tổng

| Hạng mục | Kết quả |
|---|---|
| Full suite | 980 passed / 1 skipped / 6 xfailed / **0 failed** |
| ruff/black/mypy | xanh |
| i18n parity vi↔en | 113/113, khớp 100% |
| Song ngữ thật (help, wrapper OK/LỖI, exit code, JSON machine field) | ĐẠT |
| Lỗ hổng bảo mật thật còn mở | **4** (2×P1 TOCTOU, 1×P1 rò bí mật PEM trong redactor, 1×P2 DoS FIFO) — cần work-package chủ module vá |

Không có vi phạm phạm vi (chỉ tạo file trong
`qa/evidence-index/SEC-I18N/**`, không chạy git, không sửa file khác).
