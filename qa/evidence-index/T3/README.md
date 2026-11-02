# T3 — CLI / exit-code / plan — evidence tester độc lập

**Phạm vi:** tấn công `namios_cli` + `namios_doctor` (WP3), `namios_planner` (WP6). Map test-matrix:
CLI-01 (envelope/exit-code), CLI-02/CLI-03 (plan stale-reject — phần LOGIC chạy được tại host này).

**Commit tại thời điểm test:** `b0a96d66fc6cb62e5550c2bc81f54d3ef3fa09e1`
**Python:** 3.11.2 (`.venv` do WP1 tạo)
**Lệnh chạy:**

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
  /home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/T3 -p no:cacheprovider -q
```

**Kết quả:** `5 failed, 25 passed` — 5 fail là DEFECT THẬT (code sai), không phải test sai. Chi tiết: `expected_vs_actual.md`.

**Nguyên tắc độc lập đã tuân theo:** test files (`test_cli_adversarial.py`, `test_planner_adversarial.py`,
`_qa_fakes.py`) KHÔNG import từ `tests/unit/cli/fakes.py` hay `tests/unit/planner/_fixtures.py` của dev —
tự dựng Manifest/fake Protocol riêng theo `namios_core`, để không lặp lại đúng giả định của dev (tránh bỏ
lọt case dev không nghĩ tới).

## Cấu trúc

- `test_cli_adversarial.py` (tests/qa/T3) — 15 test: uncaught exception từ WP2/WP6/WP9 impl thoát qua
  `namios_cli.main`, envelope cleanliness, exit-code table, mã lỗi lạ, redaction biên.
- `test_planner_adversarial.py` (tests/qa/T3) — 15 test: revoked/user-host/expiry/TOCTOU symlink-swap/
  multi-artifact tamper trên `DefaultInstallPlanner` THẬT (không fake lại WP6).
- `_qa_fakes.py` — fake/manifest riêng của tester, khớp Protocol `namios_core`.

## Phạm vi BLOCKED (not_run tại host này)

- CLI-02/CLI-03 phần "cài thật"/Polkit/bus thật: BLOCKED (thiếu Wine/VM — ngoài phạm vi M1).
- Mọi test wiring `catalog validate`/`app inspect`/`evidence validate` chạy qua implementation THẬT của
  WP2/WP4/WP9 (chưa phải fake) — KHÔNG test ở đây vì các package đó (`namios_manifest`, `namios_evidence`)
  là phạm vi T1/T5; T3 chỉ test khung dispatch WP3 + planner WP6 theo Protocol.
