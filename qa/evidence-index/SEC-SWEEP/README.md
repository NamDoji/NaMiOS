# SEC-SWEEP — rà soát bảo mật adversarial độc lập (02-03/11/2026)

**Phạm vi:** vai trò RA SOÁT BẢO MẬT ADVERSARIAL (owns `tests/security/sweep/**`,
`docs/SECURITY.md`, `qa/evidence-index/SEC-SWEEP/**`) theo chỉ đạo chủ dự án
03/11/2026 ("đợt nâng cấp COMMON + song ngữ + BẢO MẬT, không bị tấn công").
Bộ test tấn công ĐỘC LẬP (khác `tests/unit/**` của dev, khác `tests/qa/T1..T5`
của QA theo WP) trên API công khai các module, map từng lớp phòng thủ
`docs/threat-model.md` §4 / `docs/specs/DAC_TA_HE_DIEU_HANH.md` §10
(SEC-001..SEC-012) + §8 (DATA-001/002).

**Commit tại thời điểm test:** `8c3a7e077983155c91eeb11f71b5d5663702e1e5`
**Python:** 3.11.2 (`.venv` có sẵn — không cài thêm gì)
**Lệnh chạy:** xem `cmd.txt`. **Output đầy đủ:** `stdout.txt`/`stderr.log`.

## Kết quả

```
140 passed, 6 xfailed in 3.93s   (tests/security/sweep, 146 test)
968 passed, 1 skipped, 6 xfailed (toàn repo — baseline 800 passed/1 skipped KHÔNG vỡ)
```

Không có test nào FAIL (theo nghĩa pytest) — 6 test lộ lỗ hổng THẬT được giữ
bằng `pytest.mark.xfail(strict=True, reason="SEC-SWEEP-NNN: ...")` làm BẰNG
CHỨNG tái lập được, không sửa code module khác để che giấu (đúng chỉ đạo:
"ghi vào findings + giữ test đó làm bằng chứng — KHÔNG tự sửa code module
khác"). Nếu sau này module owner vá đúng, test sẽ XPASS và pytest BÁO LỖI
(do `strict=True`) — đó là cơ chế nhắc cập nhật file này.

## Cấu trúc test theo lớp SEC-001..012 + DATA-001/002

| File | Lớp | Module đích | Kết quả |
| --- | --- | --- | --- |
| `test_sec002_safe_path_adversarial.py` | SEC-002 | `namios_security.safe_path` (resolve_within/open_within) | 15 passed — phòng thủ giữ, bao gồm 2 mô phỏng TOCTOU (leaf + trung gian) |
| `test_sec002_evidence_safeio_adversarial.py` | SEC-002 + DoS | `namios_evidence._safe_io.read_text_safe` | 8 passed + 1 xfailed (SEC-SWEEP-004) |
| `test_sec002_manifest_safeio_toctou_finding.py` | SEC-002 (FINDING) | `namios_manifest._safe_io.read_text_safe` | 1 xfailed (SEC-SWEEP-002) |
| `test_data002_welcome_migrate_adversarial.py` | DATA-002 + SEC-002 | `namios_welcome.migrate.WindowsDataMigrator` | 5 passed + 1 xfailed (SEC-SWEEP-001) |
| `test_injection_adversarial.py` | COMP-004 (shell/url-script/template) | `namios_security.run_argv`, `namios_recipe._parse`, `namios_manifest._recipe_build` | 28 passed |
| `test_redaction_adversarial.py` | SEC-009/SUP-002 | `namios_security.redactor` | 34 passed + 3 xfailed (SEC-SWEEP-003, 2 biến thể PEM/SSH + field tự do) |
| `test_catalog_metadata_adversarial.py` | SEC-007/008, ECO-003/006/007, §11.2 | `namios_catalog.store`, `namios_eco.validator`, `namios_evidence._gate` | 27 passed |
| `test_dos_limits_adversarial.py` | DoS (NET-001/004) | `namios_dotnet.pe_format`/`_io`, `namios_manifest._safe_io` (cap) | 10 passed |
| `test_helper_privilege_adversarial.py` | SEC-001/CLI-004 | `namios_helper` (service/authenticated/allowlist/caller/policy) | 13 passed |

## 4 finding THẬT (chi tiết: `expected_vs_actual.md`)

1. **SEC-SWEEP-001** (SEC-002, TOCTOU, P1) — `namios_welcome/migrate.py`: đọc
   file nguồn Windows qua `open(source_abs, "rb")` (builtin, theo symlink)
   sau khi chỉ dùng `resolve_within()` để TÍNH đường dẫn — không phải mở
   FD-based. Attacker thắng race có thể đổi file nguồn thành symlink trỏ
   ra ngoài `source_root` giữa hai bước, khiến `migrate()` sao chép dữ liệu
   TÙY Ý (ví dụ `~/.ssh/id_rsa`) vào home người dùng dưới một tên mục
   "Documents" hợp lệ.
2. **SEC-SWEEP-002** (SEC-002, TOCTOU, P1) — `namios_manifest/_safe_io.py`:
   kiểm `os.path.realpath()` TRƯỚC rồi `os.open(path, O_NOFOLLOW)` SAU bằng
   một **chuỗi đường dẫn đầy** (không phải FD-based walk từng thành phần
   như `namios_security.safe_path`) — `O_NOFOLLOW` chỉ bảo vệ thành phần
   CUỐI, không bảo vệ thành phần TRUNG GIAN bị đổi thành symlink GIỮA hai
   bước. `ManifestValidatorImpl.load()` (API công khai WP2) đọc file
   manifest từ nguồn KHÔNG tin cậy (catalog/profile — TA-01) qua đúng hàm
   này. Module tự nhận là bản "interim chờ WP8" (docstring có TODO) nhưng
   code đang LIVE.
3. **SEC-SWEEP-003** (SEC-009, lộ bí mật, P1) — `namios_security/redactor.py`:
   nội dung khối **PEM/SSH private key** (`-----BEGIN RSA/OPENSSH PRIVATE
   KEY-----…`) nằm trong CHUỖI TỰ DO (không dưới field tên `private_key`)
   KHÔNG bị lọc bởi `redact_text()` (không có regex nhận diện khối PEM) lẫn
   `redact_obj()` (chỉ lọc theo TÊN field, không quét NỘI DUNG). Kịch bản
   thực: traceback/log tự do, hoặc field `message`/`details` chứa nguyên
   văn nội dung một file lỗi do khóa SSH người dùng nhúng vào.
4. **SEC-SWEEP-004** (DoS — treo tiến trình, P2) — `namios_security/safe_path.py`
   `open_within()` mở file với cờ `O_NOFOLLOW` nhưng KHÔNG có `O_NONBLOCK`;
   mở một FIFO (named pipe) không có writer khiến `os.open()` **treo vô
   hạn** (xác nhận bằng `timeout 5s` thật trên host — process bị kernel
   kill mới thoát). Ảnh hưởng mọi caller của `open_within`/`read_text_safe`
   (vd `namios_evidence`) khi path đầu vào không tin cậy có thể là FIFO.
   `namios_manifest/_safe_io.py` đã tự thêm `O_NONBLOCK` riêng (không bị
   ảnh hưởng) — chỉ `namios_security.safe_path` (nền chung WP8) thiếu.

## Nguyên tắc độc lập đã tuân theo

- KHÔNG import `tests/unit/**/_fixtures.py` hay `tests/qa/**` của dev/QA khác
  — `_fixtures.py` trong thư mục này tự dựng `Manifest`/raw dict riêng.
- Mọi test dùng API CÔNG KHAI của module đích (không gọi hàm private `_`
  trừ khi chính module đó coi hàm đó là bề mặt test được — ví dụ
  `_parse_one`/`_build_one` KHÔNG được gọi trực tiếp, chỉ qua
  `parse_recipe_steps`/`build_recipe_steps`).
- Mô phỏng TOCTOU bằng monkeypatch "attacker thắng race đúng lúc" (không
  threading thật — xác định, không flaky) theo đúng cách
  `tests/qa/T3/test_planner_adversarial.py` đã làm cho `verify_at_apply`
  (nơi phòng thủ THẬT SỰ giữ, dùng làm đối chứng).
- Test tiết lộ FIFO-hang (SEC-SWEEP-004) chạy trong subprocess có
  `timeout=3.0` cứng để KHÔNG treo cả tiến trình pytest sweep khi lỗ hổng
  còn mở.

## Phạm vi KHÔNG làm ở đây (ngoài vai trò)

- KHÔNG sửa code `namios_welcome`/`namios_manifest`/`namios_security` để
  che giấu 4 finding — giữ nguyên test xfail làm bằng chứng, chờ chủ biên
  tương ứng vá.
- SEC-05/06/07/08/09/10 mức thiết bị/bus/TLS thật (cần Wine/polkitd/mạng
  thật) — **BLOCKED tại host này** (đã ghi rõ ở `docs/threat-model.md` §5),
  không giả lập để báo đạt.
