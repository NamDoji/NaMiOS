# T1 — Manifest & Semantic — Evidence (tester độc lập)

Phạm vi: `namios_manifest` (WP2 — schema tầng 1 + semantic tầng 2 +
`_recipe_build` dùng khi `ManifestValidatorImpl.load()`) và phần
`validate_semantic`. `namios_recipe` (WP10) được tham chiếu để so sánh
hành vi (hai lớp phòng thủ độc lập theo thiết kế).

Test case IDs theo `docs/spec-package/qa/test-matrix.csv`: MAN-01, MAN-02,
MAN-03 (gián tiếp MAN-04 không nằm trong phạm vi T1 — thuộc T5).

## Lệnh chạy

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
  /home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/T1 -p no:cacheprovider -q
```

## Meta

- `run_id`: t1-20261102-001
- `commit_sha`: b0a96d66fc6cb62e5550c2bc81f54d3ef3fa09e1 (branch `prod`, worktree hiện tại)
- `python_version`: 3.11.2
- `host_os_build`: Debian 12 (host build M1, xem `CLAUDE.md`)
- `timestamp`: 2026-11-02T09:42:50Z
- `reviewer`: null (chưa có QA review độc lập ký)

## Kết quả tổng

```
26 collected
23 passed
3 failed  <-- DEFECT THẬT (xem defects.md), KHÔNG phải test sai
```

Chi tiết từng case: xem `stdout.txt` (log pytest đầy đủ) và `defects.md`
(3 defect tìm thấy, có repro/expected/actual).

Không có case nào `blocked_external_dependency` trong cụm T1 (toàn bộ
WP2/WP10 là Python thuần, chạy được đầy đủ tại host M1 này — không cần
Wine/VM/bus thật).
