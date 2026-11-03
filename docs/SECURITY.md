# Chính sách bảo mật — NaMiOS

**Trạng thái:** M1 (lõi Python thuần) — rà soát adversarial lần đầu
03/11/2026. Song ngữ: mục chính tiếng Việt, tóm tắt tiếng Anh ở cuối file.
Nguồn sự thật đầy đủ: `docs/threat-model.md` (thiết kế, chưa kiểm chứng) +
`docs/specs/DAC_TA_HE_DIEU_HANH.md` §10 (SEC-001..012) + §8 (VN/DATA-001/002)
+ `qa/evidence-index/SEC-SWEEP/` (bằng chứng test thật cho tài liệu này).

## 1. Nguyên tắc gốc

- Chạy chương trình Windows là **thực thi mã không tin cậy** (COMP-008).
  Prefix Wine KHÔNG phải ranh giới bảo mật.
- Catalog/metadata KHÔNG được điều khiển lệnh root (SEC-008).
- "Schema hợp lệ" ≠ "an toàn để chạy" — validation luôn 2 tầng (schema +
  semantic) ở mọi nơi nhận dữ liệu từ nguồn không tin cậy (manifest, recipe,
  catalog, evidence report).
- **Không-secret-trong-log:** mọi `ErrorBody.details`, log kỹ thuật, dòng
  chẩn đoán, gói export (diagnostics bundle) PHẢI đi qua `Redactor`
  (`namios_security.redact_text`/`redact_obj`) trước khi ghi ra bất kỳ nơi
  người/máy khác có thể đọc được. KHÔNG truyền mật khẩu/token qua command
  line hay biến môi trường log được. KHÔNG lưu key Office/Windows/DB
  password trong manifest.

## 2. Tài sản cần bảo vệ (tóm tắt — chi tiết `docs/threat-model.md` §1)

| Tài sản | Vì sao giá trị |
| --- | --- |
| Thư mục home + tài liệu người dùng | Dữ liệu cá nhân/công việc |
| Credentials/secret (password/token/cookie/OTP/QR/private key) | Truy cập hệ thống khác |
| SSH keys & browser profile | Truy cập hệ thống khác, phiên đăng nhập |
| CSDL nghiệp vụ (MISA/SQL) | Dữ liệu kế toán — sai/mất là P0 |
| Catalog & profile keys production | Gốc tin cậy cho manifest/chứng nhận |
| State store giao dịch | Tính toàn vẹn install/journal |
| Toàn vẹn hệ thống (root/OS) | Quyền đặc quyền, boot |
| Log & gói chẩn đoán | Có thể rò secret/PII nếu không lọc |

## 3. Lớp phòng thủ map SEC-001..SEC-012 → hiện thực M1

| Req | Phòng thủ | Hiện thực (package) | Trạng thái M1 |
| --- | --- | --- | --- |
| SEC-001 | Desktop/app user thường; helper typed, xác thực caller qua kênh truyền (uid, KHÔNG tin PID tự khai)/Polkit/param/path/state; từ chối → `E_PERMISSION_DENIED` TRƯỚC khi có side-effect | `namios_helper` (`caller.py`/`policy.py`/`authenticated.py`/`service.py`/`allowlist.py`) | Logic kiểm chứng (fake bus); polkitd/D-Bus thật là M3 BLOCKED |
| SEC-002 | FD-based path: traversal/symlink (trung gian+leaf)/mount/hardlink/TOCTOU; không chỉ kiểm chuỗi `..` | `namios_security.safe_path` (`resolve_within`/`open_within`, `dir_fd`+`O_NOFOLLOW` MỖI bước) | **Giữ** cho module này — xem §5 về 2 module KHÁC tự chế lại yếu hơn |
| SEC-003/004/005 | Sandbox bubblewrap/AppArmor; mạng/audio/camera/display theo hồ sơ; app bị chặn không tự chạy lại ngoài sandbox | — (cần Wine/bwrap thật) | **BLOCKED M2** — chưa hiện thực tại M1 |
| SEC-006 | HTTPS+TLS; verify hash/chữ ký; chặn redirect/SSRF ngoài policy; không `curl\|bash` | `namios_security.run_argv` (argv-only, `shell=False`); tải mạng thật là M2/M3 | Argv-only đã kiểm; phần tải mạng thật BLOCKED |
| SEC-007/008 | Catalog ký riêng; chặn downgrade/replay/revoked; fail closed | `namios_catalog.store` (revocation), `namios_eco.validator` (state machine, URL anti-spoof), `namios_evidence._gate` (revoked tuyệt đối) | Logic gate kiểm chứng; ký thật (TUF) là M2/M3 |
| SEC-009 | Secret qua KWallet; không log plaintext; `Redactor` 2 lớp (field + content) | `namios_security.redactor` | Giữ cho field có tên rõ + nhiều pattern nội dung; **1 gap đã tìm thấy** (SEC-SWEEP-003, §6) |
| SEC-010 | Firewall mặc định chặn inbound; không mở SQL/RDP mặc định | — | Ngoài phạm vi code M1 (cấu hình hệ thống/ISO) |
| SEC-011 | CVE: triage ≤24h, vá/giảm thiểu ≤72h (target nội bộ) | Quy trình — xem §7 | Áp dụng từ lần sweep này |
| SEC-012 | Mã hóa ổ đĩa trước pilot dữ liệu nhạy cảm | — | Ngoài phạm vi code M1 |
| COMP-004 | Recipe allowlist 6 action; cấm shell/eval/url-script/template nội suy; argv-only | `namios_recipe._parse`, `namios_manifest._recipe_build` (2 lớp độc lập) | **Giữ** — kiểm bằng `tests/security/sweep/test_injection_adversarial.py`, 28/28 pass |
| DATA-001 | Không ghi đè tài liệu khi chuyển định dạng; dữ liệu tách khỏi prefix/cache | — (M1 chưa có "mở tài liệu qua engine khác") | Ngoài phạm vi module hiện có |
| DATA-002 | Import Windows = sao chép có báo cáo, KHÔNG di chuyển/xóa; chặn hibernated; không mở BitLocker; không log recovery key | `namios_welcome.migrate` | **Giữ phần lớn** (no-overwrite/no-delete/hibernated-block/BitLocker-skip, 5/5 pass); **1 gap TOCTOU** (SEC-SWEEP-001, §6) |

## 4. Validation 2 tầng (bắt buộc ở mọi điểm nhận dữ liệu không tin cậy)

Mọi dữ liệu từ nguồn ngoài (manifest JSON, recipe step, catalog entry,
evidence report) đi qua ĐÚNG 2 tầng, không được bỏ tầng nào:

1. **Schema** (`validate_schema`/`catalog_schema.validate_raw`) — cấu trúc,
   kiểu, `additionalProperties: false`.
2. **Semantic** (`validate_semantic`/`namios_eco.validator`/`namios_evidence._gate`) —
   TBD/null bắt buộc, runner chưa pin, dependency chưa duyệt, recipe có
   shell/eval/url-script/template, revoked, `task_verified` thiếu evidence
   **và** thiếu `qa_reviewer` độc lập.

"Schema hợp lệ" KHÔNG BAO GIỜ được coi là "an toàn để chạy".

## 5. Nguyên tắc path-safety dùng chung — và một bài học từ sweep này

`namios_security.safe_path` (WP8) là nguồn DUY NHẤT đã CHỨNG MINH giữ được
TOCTOU bằng cách đi `dir_fd` + `O_NOFOLLOW` qua TỪNG thành phần đường dẫn,
rồi so khớp `st_dev` sau mỗi bước — một symlink-swap đúng lúc giữa hai bước
walk vẫn bị phát hiện (xem `tests/security/sweep/test_sec002_safe_path_adversarial.py`,
15/15 pass kể cả 2 mô phỏng race trực tiếp).

**Bài học (SEC-SWEEP-001/002):** hai module khác (`namios_manifest._safe_io`,
`namios_welcome.migrate`) đã TỰ CHẾ lại một phiên bản "kiểm `realpath()`
trước, mở bằng chuỗi path sau" — nhìn an toàn ở test thông thường nhưng vẫn
có cửa sổ TOCTOU thật (kernel chỉ áp `O_NOFOLLOW` cho thành phần CUỐI của
một lệnh `open(path_string, ...)`, không áp cho thành phần trung gian).
Quy tắc rút ra: **mọi lần đọc/ghi file từ input không tin cậy PHẢI gọi
`namios_security.resolve_within`/`open_within` thật, không tự chế lại kiểm
tra "có symlink không" bằng so sánh `realpath` rồi mở lại bằng string** —
đây chính xác là quy tắc M1-INTERFACES §0 ("9 WP còn lại import từ
`namios_core`/các package nền đã khai báo... không giẫm chân") áp dụng cho
an toàn, không chỉ cho tổ chức code.

## 6. Finding đang mở (từ `qa/evidence-index/SEC-SWEEP/`, 03/11/2026)

Chi tiết đầy đủ (repro, file:line, severity, khuyến nghị vá):
`qa/evidence-index/SEC-SWEEP/expected_vs_actual.md`.

| ID | Lớp | Module | Severity | Tóm tắt |
| --- | --- | --- | --- | --- |
| SEC-SWEEP-001 | SEC-002 (TOCTOU) | `namios_welcome.migrate` | P1 | Đọc nguồn Windows qua `open()` builtin sau `resolve_within()` — symlink-swap race bỏ qua ranh giới `source_root` |
| SEC-SWEEP-002 | SEC-002 (TOCTOU) | `namios_manifest._safe_io` | P1 | `realpath()`-rồi-`open(path_string)` không chặn symlink thư mục TRUNG GIAN bị đổi giữa 2 bước |
| SEC-SWEEP-003 | SEC-009 (lộ bí mật) | `namios_security.redactor` | P1 | Khối PEM/SSH private key trong chuỗi tự do không bị `redact_text`/`redact_obj` lọc |
| SEC-SWEEP-004 | DoS (treo tiến trình) | `namios_security.safe_path.open_within` | P2 | Thiếu `O_NONBLOCK` → mở FIFO không writer treo vô hạn |

Các finding này được giữ làm bằng chứng bằng `pytest.mark.xfail(strict=True)`
trong `tests/security/sweep/` — KHÔNG được coi là "test lỗi cần xóa"; khi
module owner vá đúng, test sẽ tự báo XPASS/lỗi để nhắc cập nhật bảng này.

## 7. Quy trình báo lỗ hổng + thu hồi (SEC-011)

- **Kênh báo (nội bộ, pha M1 — chưa có kênh public):** mở finding trong
  `qa/evidence-index/SEC-SWEEP/expected_vs_actual.md` (vai trò rà soát) hoặc
  báo trực tiếp chủ dự án; mọi finding PHẢI có test tái lập được kèm
  file:line, severity, repro — không báo "nghe nói có lỗ hổng" không kèm
  bằng chứng.
- **TARGET nội bộ (chưa phải SLA thương mại):** triage lỗi nghiêm trọng có
  khả năng khai thác trong **24 giờ làm việc** sau tiếp nhận; vá/biện pháp
  giảm thiểu trong **72 giờ** khi khả thi.
- **Thu hồi profile/chứng nhận:** dùng `namios_catalog.store.revoke()` +
  `namios_evidence._gate.compute_allowed_status` (decision="revoked" →
  `CompatStatus.REVOKED` TUYỆT ĐỐI, không xét gì khác, không thể tự phục
  hồi qua state machine tự động — `namios_eco.validator.ALLOWED_STATUS_TRANSITIONS[REVOKED] = frozenset()`).
- **Không bao giờ:** đổi `skipped`/`not_run`/`blocked_external_dependency`
  thành `pass` để "cho qua"; tự cấp `task_verified` khi thiếu `qa_reviewer`
  độc lập; vá bằng cách tắt/giảm phạm vi test adversarial.

## 8. Cadence rà soát

- Mỗi lần thêm module mới xử lý dữ liệu không tin cậy (manifest/recipe/
  catalog/evidence/path người dùng cung cấp) → PHẢI có ít nhất 1 test
  adversarial tương ứng trong `tests/security/sweep/` trước khi coi là
  "đạt" ở lớp SEC tương ứng.
- Sweep toàn diện lại khi: đổi `namios_security` (nền chung), thêm
  action/field mới vào recipe/manifest schema, hoặc trước mỗi mốc M2/M3
  (khi Wine/polkitd/mạng thật trở nên khả dụng để kiểm phần hiện đang
  BLOCKED ở §3).

---

## English summary

NaMiOS M1 security defenses (path safety, argv-only exec, 2-tier manifest/
recipe/catalog/evidence validation, secret redaction) are tested
adversarially under `tests/security/sweep/`. 140/146 adversarial tests
confirm defenses hold; 4 confirmed findings are tracked as `strict xfail`
evidence in that suite and detailed in
`qa/evidence-index/SEC-SWEEP/expected_vs_actual.md`: two TOCTOU gaps in
modules that reimplemented path-safety instead of delegating to
`namios_security.safe_path` (`namios_welcome.migrate`,
`namios_manifest._safe_io`), one secret-redaction gap (PEM/SSH private key
blocks in free-text are not scrubbed), and one DoS (opening a FIFO via
`open_within` hangs forever — missing `O_NONBLOCK`). Machine-readable
fields (`error.code`, exit codes, JSON keys) stay untranslated by design;
only human-readable `message_vi` text is Vietnamese. No destructive
operations (git push/reset, vendor contact, license bypass) were performed
as part of this review — only local test files and documentation were
added.
