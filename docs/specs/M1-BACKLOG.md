# M1-BACKLOG — Backlog M1 → 10 WP → 5 cụm QA

**Trạng thái:** DESIGN (02/11/2026). Nguồn: `docs/spec-package/planning/backlog.csv` (B005–B009), `docs/specs/M1-WORK-PACKAGES.md`, `qa/plans/M1-QA-PLAN.md`.
Cột `trạng thái` = `not_started` cho toàn bộ M1 (chưa có code). Cập nhật khi WP được merge.

## Backlog gốc M1 (từ B005–B009)

| B-id | Priority | depends_on | requirement_ids | Tiêu đề | Acceptance gốc |
| --- | --- | --- | --- | --- | --- |
| B005 | P0 | B004 | REPO-001, REPO-003 | Skeleton source packaging CI | Chạy được test logic trên môi trường ghi rõ |
| B006 | P0 | B005 | COMP-004 | Schema và semantic validator | Chặn TBD/shell/unknown keys/dependency chưa duyệt |
| B007 | P0 | B005 | CLI-001, CLI-003 | CLI doctor và lỗi JSON | JSON parse được; không secrets; exit code đúng |
| B008 | P0 | B006 | CLI-002, TX-001, COMP-005 | Plan state store và journal | Chặn stale plan / concurrent mutation / crash false READY |
| B009 | P0 | B004, B005 | SEC-001, SEC-002, CLI-004 | Helper tối thiểu và kiểm soát privilege | Không arbitrary command/path/package; negative tests đạt |

> B004 (M0: threat model + ADR nền tảng) là tiền đề; thuộc M0, không nằm trong 10 WP M1 nhưng là điều kiện khởi động (ADR_KHOI_DAU đã có).

## Ánh xạ B → WP → QA (M1)

Một backlog item M0 được PHÂN RÃ thành nhiều WP interface-complete; thêm WP dẫn xuất từ contracts (catalog, planner tách khỏi state, security tách khỏi helper, recipe, evidence) để 10 dev rời nhau.

| B-id | WP phụ trách | requirement_ids | Cụm QA | Test IDs khả thi tại đây | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| B005 | WP1 (skeleton+core+CI) | REPO-001, REPO-003 | — (khung cho mọi cụm) | ENV-01 (khung), nền CLI-01 | not_started |
| B006 | WP2 (manifest+semantic) | COMP-004 | T1 | MAN-01, MAN-02, MAN-03 | not_started |
| B006 | WP10 (recipe allowlist+dry-run) | COMP-004 | T1, T2 | MAN-03 (recipe), SEC-04 | not_started |
| B007 | WP3 (CLI+doctor+envelope+exit) | CLI-001, CLI-003 | T3 | CLI-01, ENV-01 | not_started |
| B008 | WP5 (txstate+journal+recovery) | TX-001, COMP-005 | T4 | TX-01, WINE-03 (khóa) | not_started |
| B008 | WP6 (install planner) | CLI-002 | T3 | CLI-02, CLI-03 (logic) | not_started |
| B009 | WP7 (system-helper typed+Polkit/D-Bus) | SEC-001, CLI-004 | T2 | SEC-01 (logic; Polkit thật blocked) | not_started |
| B009 | WP8 (security primitives) | SEC-002, SEC-009, SUP-002 | T2 | SEC-02, SEC-03, SEC-04, SEC-11 | not_started |
| (contracts §11.2) | WP4 (catalog+VN search+revocation) | compat-catalog, UX-006 | T5 | UX-03 | not_started |
| (contracts §11.2) | WP9 (evidence model+gate) | §11.2 (gate), UX-002 | T5 | MAN-04 | not_started |

## Bảng 10 WP (tóm tắt + trạng thái)

| WP | Package src sở hữu | Map B | Cụm QA | Trạng thái |
| --- | --- | --- | --- | --- |
| WP1 | `namios_core` + pyproject/ci/scripts/conftest | B005 | khung | not_started |
| WP2 | `namios_manifest` | B006 | T1 | not_started |
| WP3 | `namios_cli`,`namios_doctor` | B007 | T3 | not_started |
| WP4 | `namios_catalog` | §11.2/UX-006 | T5 | not_started |
| WP5 | `namios_txstate` | B008 | T4 | not_started |
| WP6 | `namios_planner` | B008 (CLI-002) | T3 | not_started |
| WP7 | `namios_helper` | B009 (SEC-001/CLI-004) | T2 | not_started |
| WP8 | `namios_security` | B009 (SEC-002) | T2 | not_started |
| WP9 | `namios_evidence` | §11.2 | T5 | not_started |
| WP10 | `namios_recipe` | B006 (COMP-004) | T1/T2 | not_started |

## Ngoài phạm vi M1 (BLOCKED — không nằm trong 10 WP)
- B010–B016 (M2 Wine/.NET), B017–B022 (M3 ISO/desktop), B023–B037 (M4 app thương mại/pilot), B035–B036 (M5): BLOCKED tại host hiện tại. Điều kiện mở khóa: build host Linux amd64 nested-virt + wine/live-build/qemu + bộ cài có quyền dùng do chủ dự án cấp (FACT CLAUDE.md, M0 inventory).
- `task_verified` cho mọi app thương mại: KHÔNG cấp ở M1; mọi manifest giữ `compatibility.status = untested`.
