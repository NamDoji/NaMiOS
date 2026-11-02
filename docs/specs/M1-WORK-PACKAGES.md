# M1-WORK-PACKAGES — 10 gói dev song song

**Trạng thái:** DESIGN (02/11/2026). Phạm vi: M1 lõi Python thuần (backlog B005–B009 + contracts), chạy+test được tại host hiện tại. KHÔNG có Wine/ISO/app thương mại (M2+ BLOCKED).
**Mục tiêu:** 10 dev Sonnet code song song KHÔNG giẫm chân; interface-complete theo `docs/specs/M1-INTERFACES.md`; 5 tester xác minh độc lập (xem `qa/plans/M1-QA-PLAN.md`).

Nguyên tắc chống xung đột (FACT CLAUDE.md §"Quy ước đội agent"):
- Mỗi dev sở hữu MỘT package `src/…` + thư mục test tương ứng; chỉ sửa trong phạm vi sở hữu + file chỉ định.
- Interface chung (`namios_core`) do **WP1** phát hành TRƯỚC; 9 WP còn lại code theo Protocol/enum/dataclass trong đó.
- File giao thoa duy nhất là `pyproject.toml` + `tests/conftest.py` → **chỉ WP1** sở hữu. Thêm package mới KHÔNG cần sửa `pyproject.toml` (dùng `packages.find where=["src"]`).
- Branch/worktree cô lập mỗi WP.

## Thứ tự thực hiện (dependency graph)

```
WP1 (nền + namios_core interfaces)   ← PHẢI xong & merge trước
      │
      ├── WP8 security  (nền kỹ thuật, nhiều WP phụ thuộc)
      │
      ├── WP2 manifest ──┬── WP4 catalog
      │                  ├── WP9 evidence
      │                  └── WP6 planner ── (WP5, WP10)
      ├── WP5 txstate
      ├── WP10 recipe
      ├── WP7 helper (sau WP8)
      └── WP3 CLI (code theo interface ngay; wiring subcommand sau khi các WP có impl)
```

Lát cắt song song thực tế: sau khi **WP1** merge, cả WP2/WP3/WP5/WP8/WP10 bắt đầu NGAY (chỉ phụ thuộc `namios_core`). WP4/WP6/WP9/WP7 bắt đầu sau khi interface của phụ thuộc có sẵn (interface đã có từ WP1 nên thực chất chỉ chờ impl ở bước wiring/integration test).

---

## WP1 — Skeleton + packaging + CI + `namios_core`

- **Requirement IDs:** B005, REPO-001, REPO-003.
- **Sở hữu (ghi được):**
  - `pyproject.toml` (DUY NHẤT WP1 sửa), `README` phần "chạy test M1".
  - `src/namios_core/**` (envelope, exitcodes, errors, txstate enum, compat enum+tuple, paths, manifest_types, các Protocol §7).
  - `ci/**` (GitHub Actions: lint `ruff`, format `black --check`, typecheck `mypy`, `pytest -q`, schema validation, license/SBOM check placeholder).
  - `scripts/run_tests.sh`, `scripts/make_venv.sh`.
  - `tests/conftest.py` (fixtures gốc dùng chung: tmp XDG dirs, fake user/host).
  - `docs/STATUS.md` (cập nhật trạng thái M1).
- **Phụ thuộc:** không (gói nền).
- **Acceptance (đo được):**
  - `python -m venv` + `pip install -e .` thành công trên host; `import namios_core` OK.
  - `namios_core` chứa đủ enum/dataclass/Protocol trong M1-INTERFACES §1–§7, mypy `strict` pass trên `namios_core`.
  - `pytest` chạy (kể cả khi chỉ có test placeholder) exit 0; CI workflow lint+type+test cấu hình xong.
  - `packages.find where=["src"]` tự nhận mọi package con (xác minh bằng `pip show -f`).
  - KHÔNG business logic trong `namios_core` (chỉ kiểu + hằng số + hàm path thuần).
- **Test chứng minh:** ENV-01 (doctor/inventory host — phần khung), `MAN-*`/`CLI-*` chạy được nhờ khung test WP1 dựng.

## WP2 — Manifest schema loader + semantic validator 2 tầng

- **Requirement IDs:** B006, COMP-004, §11.1.
- **Sở hữu:** `src/namios_manifest/**`; `tests/unit/manifest/**`.
- **Phụ thuộc:** WP1 (`namios_core`), WP8 (`SafePath` để load an toàn). Dùng `contracts/app-manifest.schema.json` (chỉ đọc).
- **Mô tả:** hiện thực `ManifestValidator` (§7.1). Tầng 1: JSON Schema (draft 2020-12, `additionalProperties:false` → unknown key fail). Tầng 2: semantic — chặn TBD/null bắt buộc để cài, runner chưa pin, dependency chưa duyệt, recipe ngoài allowlist/shell, revoked, task_verified thiếu evidence. Trả `install_ready` riêng với `schema.ok`.
- **Acceptance:**
  - Load `contracts/sample-misa-sme-wine.json`: schema PASS nhưng `validate_semantic(...).install_ready == False` (vì build/runner/hash null → `E_SEMANTIC_TBD`).
  - Manifest thêm key lạ hoặc field `shell`/action ngoài enum → fail ở tầng đúng với `ErrorCode` đúng (`E_INPUT_UNKNOWN_KEY`/`E_SEMANTIC_RECIPE`), KHÔNG tạo process.
  - Dependency profile không thuộc `approved_dependency_ids` → `E_SEMANTIC_DEPENDENCY`.
  - Mọi lỗi trả `ValidationError.path` trỏ đúng vị trí.
- **Test chứng minh:** MAN-01, MAN-02, MAN-03 (unit), gián tiếp MAN-04.

## WP3 — CLI framework + `doctor` + JSON envelope + exit codes

- **Requirement IDs:** B007, CLI-001, CLI-003.
- **Sở hữu:** `src/namios_cli/**`, `src/namios_doctor/**`; `tests/unit/cli/**`.
- **Phụ thuộc:** WP1. (Các subcommand khác gọi impl WP2/4/5/6/9 ở bước wiring — dùng dependency injection qua Protocol, không import cứng.)
- **Mô tả:** parser argv (`--` kết thúc options; argv-only), `emit_json` (một JSON/ stdout, log→stderr), mapper `ErrorCode→ExitCode`, lệnh `namios doctor --json` (capability report: os/kernel/session/python/kvm/tooling theo host THẬT, không bịa). Khung subcommand cho `catalog validate`, `app inspect/plan-install/install`, `evidence validate` (gọi Protocol tương ứng).
- **Acceptance:**
  - `namios doctor --json` in JSON hợp lệ (parse được), chứa `api_version/operation_id/status/data/warnings/error`, KHÔNG secret, stdout KHÔNG lẫn log.
  - Mỗi nhánh lỗi định nghĩa sẵn trả đúng exit code 0/2/3/4/5/6/7/8/9 (test bảng).
  - Doctor phản ánh host thật: `has_kvm=false`, wine/live-build/qemu = absent (FACT inventory M0).
- **Test chứng minh:** CLI-01, ENV-01.

## WP4 — Catalog store + tìm kiếm tiếng Việt accent-insensitive + revocation

- **Requirement IDs:** compat-catalog (§5.2 mô-đun 7), UX-006.
- **Sở hữu:** `src/namios_catalog/**`; `tests/unit/catalog/**`; `fixtures/catalog/**` (manifest giả vô hại cho test tìm kiếm/1000 records).
- **Phụ thuộc:** WP1, WP2 (`Manifest`), WP8 (path).
- **Mô tả:** hiện thực `CatalogStore` (§7.2). Lưu entry (JSON có schema trên đĩa trong `fixtures`/cache), index tìm kiếm fold dấu + casefold (giữ nguyên tên hiển thị/tên file thật). Revocation list + `is_revoked`.
- **Acceptance:**
  - `search("do chi cuong")` và `search("Đỗ Chí Cường")` cùng khớp entry tên "Đỗ Chí Cường"; hoa/thường không ảnh hưởng; tên file gốc không đổi.
  - `is_revoked(app_id)` đúng theo revocation record; entry revoked không xuất hiện như "cài được".
  - Tìm trên 1.000 record fixture trả đúng tập kết quả (chuẩn hóa đúng); (PERF-02 ≤300ms là TARGET, đo ở máy tham chiếu — không chặn unit).
- **Test chứng minh:** UX-03 (unit), dữ liệu cho PERF-02.

## WP5 — Transaction state store + journal + state machine + crash recovery

- **Requirement IDs:** B008, TX-001, COMP-005.
- **Sở hữu:** `src/namios_txstate/**`; `tests/unit/txstate/**`, `tests/system/txstate/**` (crash sim).
- **Phụ thuộc:** WP1, WP8.
- **Mô tả:** hiện thực `StateStore` (§7.3) trên `state.sqlite3`. Bảng `transactions`, `journal`. Thi hành bảng chuyển hợp lệ §4 (transition sai → `E_STATE_CONFLICT`). Ghi journal TRƯỚC/ SAU mỗi bước. `recover()` quét tx dở → `RECOVERING`→`NEEDS_ATTENTION`/`READY` dựa kiểm tra thực, KHÔNG false READY. Prefix mutex (`acquire_prefix_lock`) theo (app_id, instance_id); khóa theo người dùng.
- **Acceptance:**
  - Chuyển `INSTALLING→READY` trực tiếp bị từ chối (phải qua VERIFYING).
  - Mô phỏng kill sau mỗi journal step rồi `recover()`: không tx nào ở READY nếu chưa VERIFYING pass; state nhất quán.
  - Hai thao tác cùng prefix: cái thứ hai nhận `E_STATE_CONFLICT` (hoặc chờ), không mutation song song.
- **Test chứng minh:** TX-01 (system, crash sim bằng process con/giả lập — chạy được tại đây), WINE-03 phần khóa (unit-able, không cần wine).

## WP6 — Install planner (plan / verify-at-apply / stale-reject)

- **Requirement IDs:** CLI-002.
- **Sở hữu:** `src/namios_planner/**`; `tests/unit/planner/**`.
- **Phụ thuộc:** WP1, WP2 (Manifest + semantic), WP5 (tx/lock), WP8 (digest/path), WP10 (recipe dry-run để liệt kê changes).
- **Mô tả:** hiện thực `InstallPlanner` (§7.4). `build_plan` gom user/host, profile digest, artifact digests, danh sách thay đổi (từ recipe dry-run), dung lượng ước tính, permissions, `expires_at`. `verify_at_apply` tính lại digest + so user/host + hạn dùng; sai → `E_PLAN_STALE`.
- **Acceptance:**
  - Đổi nội dung installer (digest khác) giữa plan và apply → `verify_at_apply.ok == False`, code `E_PLAN_STALE`.
  - Plan tạo cho user A, apply bởi user B → reject.
  - Plan quá `expires_at` → reject. Plan nguyên vẹn, đúng user/host, còn hạn → ok.
- **Test chứng minh:** CLI-02, CLI-03 (gán test_level integration nhưng phần logic plan/stale CHẠY ĐƯỢC tại đây bằng fixture file — không cần VM; xem QA plan).

## WP7 — System-helper API typed (no RunCommand) + Polkit/D-Bus interface + policy

- **Requirement IDs:** B009, SEC-001, CLI-004.
- **Sở hữu:** `src/namios_helper/**` (hiện thực mô-đun `namios_system_helper`); `tests/security/helper/**`; `packaging/debian/` phần policy file + D-Bus/Polkit `.policy`/`.conf` mẫu (chỉ file của WP7).
- **Phụ thuộc:** WP1, WP8.
- **Mô tả:** hiện thực `SystemHelper` (§7.5) + layer xác thực: kiểm danh tính caller (uid từ D-Bus, không tin PID thô), Polkit action-per-method, kiểu tham số, `allowlist_key` hợp lệ. KHÔNG `RunCommand`; KHÔNG nhận repo/key/package tùy ý. D-Bus có thể mô phỏng (in-process fake bus) để test logic policy tại đây — bus thật là tích hợp M3.
- **Acceptance:**
  - Caller không hợp lệ / Polkit deny → `E_PERMISSION_DENIED` (exit 5), KHÔNG thay đổi hệ thống.
  - Truyền `allowlist_key` ngoài allowlist → từ chối; không có đường nào nhận lệnh/đường dẫn/package tự do.
  - Không tồn tại method kiểu `RunCommand` (test introspection interface).
- **Test chứng minh:** SEC-01 (security — phần logic policy chạy được với fake bus/mock Polkit; phần tích hợp Polkit thật giữ blocked nếu môi trường thiếu, ghi lý do).

## WP8 — Security primitives: safe path/FD + argv-only exec + redaction

- **Requirement IDs:** SEC-002, SEC-009, SUP-002.
- **Sở hữu:** `src/namios_security/**`; `tests/security/security/**`.
- **Phụ thuộc:** WP1.
- **Mô tả:** hiện thực `SafePath`/`SafeExec`/`Redactor` (§7.8). `resolve_within` dùng FD-based (`os.open` + `O_NOFOLLOW`, `openat`-style qua `dir_fd`), chống symlink/hardlink/traversal/TOCTOU/mount; kiểm owner/type. `run_argv` argv-only, `shell=False`, `argv[0]` tuyệt đối + allowlist, timeout. `Redactor` fold mật khẩu/token/OTP/QR/đường dẫn tài liệu/IP nội bộ/username — allowlist field + regex, kèm test corpus dữ liệu nhạy cảm.
- **Acceptance:**
  - Symlink/`..`/absolute path trỏ ra ngoài `base` → `E_PATH_UNSAFE`, không đọc/ghi ngoài.
  - Đổi symlink giữa resolve và open (TOCTOU) → không vượt ranh giới (FD-based chứng minh).
  - Filename chứa space/metachar shell → qua `run_argv` được coi là dữ liệu argv, không sinh lệnh phụ.
  - Redactor loại hết fake secret trong corpus test; không rò ở `details`/log/export.
- **Test chứng minh:** SEC-02, SEC-03, SEC-04, SEC-11 (security, CHẠY ĐƯỢC tại đây với fixture an toàn).

## WP9 — Evidence model + validator + compatibility state gate

- **Requirement IDs:** §11.2, UX-002 (nhãn), §18.3 (gate).
- **Sở hữu:** `src/namios_evidence/**`; `tests/unit/evidence/**`; `fixtures/evidence/**` (report giả vô hại).
- **Phụ thuộc:** WP1, WP2 (compat enum ở core). Dùng `contracts/evidence-report.schema.json` + `sample-evidence-not-run.json` (chỉ đọc).
- **Mô tả:** hiện thực `EvidenceValidator` (§7.7). Schema + gate `compute_allowed_status`: `task_verified` chỉ khi mọi `required` test `pass` VÀ `qa_reviewer != null`; `not_run/skipped/blocked_external_dependency` ở required → không được task_verified. Ánh xạ sang `CompatStatus`.
- **Acceptance:**
  - `sample-evidence-not-run.json` (MISA-01 required=not_run, reviewer=null) → `allowed_status` KHÔNG phải `task_verified` (là `pending/blocked`), lý do tiếng Việt rõ.
  - Report đủ pass nhưng `qa_reviewer=null` → vẫn không `task_verified` (`E_EVIDENCE_MISSING`).
  - `skipped` không bao giờ được tính như pass.
- **Test chứng minh:** MAN-04 (unit).

## WP10 — Recipe engine declarative allowlist + dry-run fixtures

- **Requirement IDs:** COMP-004.
- **Sở hữu:** `src/namios_recipe/**`; `tests/unit/recipe/**`; `catalog/recipes/**` (recipe mẫu vô hại) + `fixtures/recipe/**`.
- **Phụ thuộc:** WP1, WP8.
- **Mô tả:** hiện thực `RecipeEngine` (§7.6). `parse` chỉ nhận 6 action + param typed; reject action/param lạ, trường `shell`/`eval`/url-script/template nội suy. `dry_run` liệt kê hành động dự kiến, KHÔNG thực thi gì (M1). Kiểm dependency ∈ approved, argv-only cho `RunInstaller`.
- **Acceptance:**
  - Recipe có action ngoài enum hoặc field `shell` → `E_SEMANTIC_RECIPE`, không parse thành step.
  - `RunInstaller` với chuỗi shell ghép → bị coi là argv data, reject nếu không phải list argv hợp lệ.
  - `dry_run` recipe mẫu hợp lệ: trả planned_actions, KHÔNG tạo prefix/chạy installer thật.
- **Test chứng minh:** MAN-03 (phần recipe), SEC-04 (injection qua recipe param).

---

## Ma trận sở hữu nhanh (chống ghi đè)

| WP | package src | tests | file khác |
| --- | --- | --- | --- |
| 1 | `namios_core/` | `conftest.py` | `pyproject.toml`, `ci/`, `scripts/`, `docs/STATUS.md` |
| 2 | `namios_manifest/` | `unit/manifest/` | — |
| 3 | `namios_cli/`,`namios_doctor/` | `unit/cli/` | — |
| 4 | `namios_catalog/` | `unit/catalog/` | `fixtures/catalog/` |
| 5 | `namios_txstate/` | `unit/txstate/`,`system/txstate/` | — |
| 6 | `namios_planner/` | `unit/planner/` | — |
| 7 | `namios_helper/` | `security/helper/` | `packaging/debian/` (policy/.policy/.conf của WP7) |
| 8 | `namios_security/` | `security/security/` | — |
| 9 | `namios_evidence/` | `unit/evidence/` | `fixtures/evidence/` |
| 10 | `namios_recipe/` | `unit/recipe/` | `catalog/recipes/`,`fixtures/recipe/` |

Cấm: sửa `namios_core` (ngoài WP1), sửa `pyproject.toml`/`conftest.py` gốc (ngoài WP1), sửa `contracts/*.json` và `src/` của WP khác. Thay đổi interface PHẢI qua WP1 (đề xuất → cập nhật M1-INTERFACES → thông báo cả fleet).
