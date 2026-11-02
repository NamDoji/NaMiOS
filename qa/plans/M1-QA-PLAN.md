# M1-QA-PLAN — 5 tester xác minh độc lập

**Trạng thái:** DESIGN (02/11/2026). Phạm vi: xác minh M1 (lõi Python thuần) trên host hiện tại (Debian 12, python 3.11, venv + pytest). Nguồn test: `docs/spec-package/qa/test-matrix.csv`.
**Nguyên tắc (FACT CLAUDE.md/§18):** tester xác minh ĐỘC LẬP với dev (ưu tiên negative/adversarial) TRƯỚC khi gộp; mock/stub KHÔNG phải bằng chứng app thương mại; test thiếu môi trường giữ `blocked`/`not_run` có lý do, KHÔNG đổi `skipped→pass`. Evidence lưu `qa/evidence-index/`.

## Dòng test CHẠY ĐƯỢC tại host này (gate G0/G1, unit/security, không cần bộ cài thương mại)

Lọc từ test-matrix.csv theo tiêu chí: `test_level ∈ {unit, security}` HOẶC prerequisite "không cần bộ cài thương mại"/"fixture tự viết"/mock được; và phần logic không cần KVM/wine/ISO.

| test_id | area | level | gate | Ghi chú khả thi tại đây |
| --- | --- | --- | --- | --- |
| MAN-01 | Manifest | unit | G0 | Chạy đầy đủ (fixture manifest). |
| MAN-02 | Manifest | unit | G1 | Chạy đầy đủ. |
| MAN-03 | Manifest | unit | G1 | Chạy đầy đủ. |
| MAN-04 | Chứng nhận | unit | G1 | Chạy đầy đủ (evidence fixture). |
| CLI-01 | CLI | unit | G1 | Chạy đầy đủ (CLI local). |
| UX-03 | Tìm kiếm | unit | G1 | Chạy đầy đủ (catalog fixture). |
| NET-01 | Phân loại .NET | unit | G0 | Parser PE static CHẠY ĐƯỢC (fixture nhỏ tự viết, không thực thi). Giới hạn: M1 chỉ phần parser an toàn; đầy đủ .NET là M2. |
| SEC-02 | Đường dẫn | security | G1 | Chạy đầy đủ (fixture symlink/traversal an toàn trong tmp). |
| SEC-03 | Đường dẫn (TOCTOU) | security | G1 | Chạy được (đổi symlink giữa resolve/open trong fixture). |
| SEC-04 | Injection | security | G1 | Chạy được (filename metachar → argv). |
| SEC-11 | Bí mật | security | G1 | Chạy được (fake secret corpus → redaction/log/export). |
| SEC-01 | Đặc quyền | security | G1 | Phần LOGIC policy chạy với fake D-Bus/mock Polkit; phần Polkit/bus THẬT → blocked (thiếu môi trường), ghi lý do. |
| TX-01 | Giao dịch | system | G1 | Crash sim bằng process con/kill giữa journal step — CHẠY ĐƯỢC tại đây (không cần VM cho metadata layer). |
| CLI-02 | Plan (stale) | integration | G1 | Phần LOGIC build_plan/verify_at_apply/stale chạy được bằng fixture file; phần "cài thật" blocked. |
| CLI-03 | Plan (hết hạn/revoked) | integration | G1 | Như CLI-02: logic chạy được. |
| WINE-03 | Khóa prefix | integration | G1 | Phần mutex/hàng đợi CHẠY ĐƯỢC (không cần wine, dùng StateStore lock); phần install/repair thật blocked. |
| NET-04 | .NET phụ thuộc | integration | G1 | Phần parser malformed-PE không-crash/không-vượt-quyền chạy được; chạy app thật blocked. |

**BLOCKED tại đây (giữ `not_run`, lý do `blocked_external_dependency`):** mọi dòng cần VM/KVM, wine, ISO, bộ cài/giấy phép thương mại hoặc phần cứng — gồm MAN-05, SEC-05/06/07/08/09/10/12, WINE-01/02, TX-02/03/04, VN-01..04, WORD-*, EXCEL-*, OFF-*, ZALO-*, MISA-*, AMIS-01, SIGN-01, NET-02/03 (chạy runtime thật), ISO-*, UPD-*, BACK-01, DIAG-01 (phần tích hợp), HW-*, UX-01/02, PERF-01/02 (số đo trên máy tham chiếu), DATA-01, VM-01, REL-*, LIC-01. Ghi rõ điều kiện mở khóa: build host Linux amd64 nested-virt + wine/live-build/qemu + bộ cài có quyền dùng do chủ dự án cấp.

> Lưu ý ranh giới: TX-02/TX-03 (hết đĩa / hủy installer) cần hành vi filesystem+process thật ở mức giao dịch cài — M1 chỉ test được LOGIC state machine (đã nằm trong TX-01). Phần "staging đầy đĩa/installer nonzero" giữ blocked cho M2/M3. DIAG-01 phần redaction logic trùng SEC-11 (chạy được); phần "default telemetry off + export preview UI" là M3.

---

## 5 cụm tester

### T1 — Manifest & Semantic (độc lập WP2, WP10 phần recipe validate)
- **Mục tiêu:** chứng minh validation 2 tầng chặn đúng; "schema pass ≠ install-ready".
- **Test IDs:** MAN-01, MAN-02, MAN-03.
- **Negative/adversarial phải viết:** manifest thừa key lạ; `recipe[].action` ngoài enum; field `shell`/`eval`/url-script/template nội suy; param sai type; dependency chưa duyệt; runner null + build null (TBD) phải chặn install; manifest revoked. Kỳ vọng: `ErrorCode` đúng (§3 M1-INTERFACES), KHÔNG tạo process.
- **Evidence:** `qa/evidence-index/T1-manifest/` — mỗi case: input manifest (vô hại), lệnh `vietdesk catalog validate <file> --json`, envelope JSON, exit code, so với expected.

### T2 — Security: path / injection / redaction (độc lập WP8, WP10 phần argv)
- **Mục tiêu:** chống symlink/traversal/TOCTOU; argv-only; không rò secret.
- **Test IDs:** SEC-02, SEC-03, SEC-04, SEC-11.
- **Negative/adversarial phải viết:** symlink ra ngoài base; hardlink; absolute path; `..` lồng; đổi symlink giữa resolve và open (TOCTOU); filename `"; rm -rf /"`, space, dấu tiếng Việt → phải thành argv data; corpus fake secret (password/token/OTP/QR/đường dẫn tài liệu/IP nội bộ/username) trong error details + export → phải bị redact. KHÔNG dùng secret/đường dẫn thật.
- **Evidence:** `qa/evidence-index/T2-security/` — fixture an toàn trong tmp, log chứng minh không đọc/ghi ngoài base, diff trước/sau redaction.

### T3 — CLI / exit-code / plan (độc lập WP3, WP6)
- **Mục tiêu:** envelope sạch, exit code ổn định, plan stale-reject.
- **Test IDs:** CLI-01, CLI-02 (logic), CLI-03 (logic).
- **Negative/adversarial phải viết:** mọi nhánh lỗi 2/3/4/5/6/7/8/9 trả đúng exit + envelope `status=error`; stdout JSON KHÔNG lẫn log (bắt log ở stderr); plan sai user; plan hết hạn; plan nội dung đổi (digest khác) → `E_PLAN_STALE`; `--` + filename có dấu.
- **Evidence:** `qa/evidence-index/T3-cli/` — capture stdout (JSON) + stderr (log) riêng, bảng exit-code, plan fixtures.

### T4 — State / journal / recovery (độc lập WP5)
- **Mục tiêu:** không false READY; recovery nhất quán; mutex.
- **Test IDs:** TX-01, WINE-03 (phần khóa).
- **Negative/adversarial phải viết:** transition bất hợp lệ (vd INSTALLING→READY) bị từ chối; kill process sau từng journal step rồi `recover()` → không READY nếu chưa VERIFYING pass; hai thao tác cùng prefix → `E_STATE_CONFLICT`; journal ghi trước/sau đủ cặp. Mô phỏng crash bằng subprocess + SIGKILL.
- **Evidence:** `qa/evidence-index/T4-txstate/` — dump bảng `transactions`/`journal` sau crash, log recover, assertion state.

### T5 — Evidence / compat-gate / catalog (độc lập WP9, WP4)
- **Mục tiêu:** gate "no task_verified w/o evidence"; tìm kiếm tiếng Việt; revocation.
- **Test IDs:** MAN-04, UX-03.
- **Negative/adversarial phải viết:** evidence có required=not_run/skipped/blocked → KHÔNG task_verified; đủ pass nhưng `qa_reviewer=null` → không task_verified (`E_EVIDENCE_MISSING`); `skipped` không được tính pass; search có dấu vs không dấu vs hoa/thường cùng khớp; tên file gốc không đổi; entry revoked không hiện "cài được".
- **Evidence:** `qa/evidence-index/T5-evidence-catalog/` — evidence fixtures (gồm `sample-evidence-not-run.json`), kết quả gate, bảng search-term→match, revocation case.

---

## Định dạng evidence (FACT §11.2 — không chứa secret/tài liệu thật)
Mỗi thư mục `qa/evidence-index/<Tn-…>/<test_id>/` gồm:
- `cmd.txt`: lệnh đã chạy (argv, redacted nếu cần).
- `stdout.json` + `stderr.log` tách riêng (chứng minh không trộn).
- `expected_vs_actual.md`: expected (từ test-matrix) vs actual + verdict pass/fail/blocked.
- `meta.json`: `test_id, run_id, commit_sha, python_version, host_os_build, timestamps, result, reviewer(null nếu chưa QA)`.
- Với dòng blocked: `blocked.md` nêu lý do + điều kiện mở khóa; result giữ `blocked_external_dependency`, KHÔNG pass.

## Quy trình gộp
1. Dev mở PR theo WP (worktree cô lập). 2. Tester cụm tương ứng chạy negative suite trên nhánh dev, log evidence. 3. Chỉ gộp khi: test khả thi PASS; test blocked có lý do đúng; không secret trong source/log; envelope+exit code đúng. 4. Không tester nào ký `task_verified` cho app thương mại ở M1 (ngoài phạm vi — mọi app giữ `untested`).
