# T3 — expected vs actual (5 defect thật + tóm tắt 25 test pass)

## DEFECT-T3-01 — `app plan-install --json` crash khi `install_planner.build_plan()` raise `PlanBuildError`

- **test_id liên quan:** CLI-02/CLI-03 (plan revoked → reject), CLI-01 (envelope contract).
- **Test:** `test_cli_adversarial.py::test_plan_install_uncaught_plan_build_error_breaks_json_contract`
- **Repro:** wiring `install_planner` = `namios_planner.DefaultInstallPlanner` THẬT (không fake), gọi
  `namios app plan-install fixture.json --json` với `ctx.revoked_ids` chứa `app_id` của manifest.
- **Expected (CLI-001/CLI-003):** mọi lệnh `--json` in ĐÚNG MỘT envelope JSON ra stdout, exit code ∈
  {0,2,3,4,5,6,7,8,9}; app bị revoked → envelope `status="error"`, `error.code="E_REVOKED"`, exit 2.
- **Actual:** `PlanBuildError` (exception riêng của WP6 — KHÔNG thuộc Protocol trả về, mà raise thẳng)
  thoát ra ngoài `namios_cli.main.main()` không bị bắt. `_handle_app_plan_install` trong
  `src/namios_cli/main.py` chỉ `try/except` quanh `deps.manifest_validator.load(path)`, KHÔNG bọc
  `deps.install_planner.build_plan(...)`. Tiến trình CLI crash với traceback Python thật (exit code mặc
  định của interpreter, có thể là 1 — mã CỐ Ý không dùng theo CLI-003), KHÔNG có JSON nào trên stdout.
- **Verdict:** FAIL — CONFIRMED (code sai, không phải test sai).
- **File:line:** `src/namios_cli/main.py:117-153` (hàm `_handle_app_plan_install`), gốc raise tại
  `src/namios_planner/planner.py:86-100`.

## DEFECT-T3-02 — biến thể: exception nội bộ bất kỳ (không phải `PlanBuildError`) từ planner cũng crash

- **Test:** `test_cli_adversarial.py::test_plan_install_uncaught_generic_exception_from_planner`
- **Actual:** giống DEFECT-T3-01 — bất kỳ exception nào từ `build_plan()` (không riêng `PlanBuildError`)
  đều thoát ra ngoài `main()`. Cùng gốc code.
- **Verdict:** FAIL — CONFIRMED.

## DEFECT-T3-03 — `catalog validate --json` crash khi `validate_semantic()` (WP2) raise exception

- **Test:** `test_cli_adversarial.py::test_catalog_validate_uncaught_exception_from_validate_semantic`
- **Actual:** `_handle_catalog_validate` (`src/namios_cli/main.py:58-90`) chỉ bọc `.load()`; dòng
  `result = deps.manifest_validator.validate_semantic(manifest, ctx)` KHÔNG có try/except. Một bug nội
  bộ bất kỳ ở implementation thật của WP2 (`namios_manifest`) sẽ crash CLI thay vì trả `E_INTERNAL`.
- **Verdict:** FAIL — CONFIRMED.

## DEFECT-T3-04 — `catalog validate --json` crash khi `ValidationError.code` không thuộc `ErrorCode` enum

- **Test:**
  `test_cli_adversarial.py::test_catalog_validate_unknown_error_code_from_validator_crashes_valueerror`
- **Repro:** fake `validate_semantic()` trả `ValidationError(code="E_KHONG_TON_TAI", ...)` (mã lạ, mô
  phỏng WP2 bị bug/lệch phiên bản schema lỗi).
- **Expected:** mã lỗi lạ từ một module khác KHÔNG được làm sập WP3 — phải fallback an toàn về
  `E_INTERNAL` (hoặc tối thiểu không crash).
- **Actual:** `src/namios_cli/main.py:74` — `code = ErrorCode(first.code) if first is not None else
  ErrorCode.E_INTERNAL` — nhánh `first is not None` ép `ErrorCode(first.code)` KHÔNG có try/except; giá
  trị không hợp lệ ném `ValueError: 'E_KHONG_TON_TAI' is not a valid ErrorCode` thoát thẳng ra ngoài
  `main()`.
- **Verdict:** FAIL — CONFIRMED.
- **File:line:** `src/namios_cli/main.py:74`.

## DEFECT-T3-05 — `evidence validate --json` crash khi `compute_allowed_status()` (WP9) raise exception

- **Test:**
  `test_cli_adversarial.py::test_evidence_validate_uncaught_exception_from_compute_allowed_status`
- **Actual:** `_handle_evidence_validate` (`src/namios_cli/main.py:168-189`) chỉ bọc `.load()`; dòng
  `gate = deps.evidence_validator.compute_allowed_status(report)` không có try/except. Cùng pattern lỗi
  với DEFECT-T3-03.
- **Verdict:** FAIL — CONFIRMED.

---

## Quan sát phụ (không fail test, chỉ ghi lại hành vi — rủi ro thiết kế)

- `test_catalog_validate_not_install_ready_with_empty_errors_tuple_exit_code` (PASS): khi
  `SemanticResult(ok=False, errors=())` (install_ready=False nhưng không có error cụ thể),
  `_handle_catalog_validate` fallback về `ErrorCode.E_INTERNAL` (exit 9 — "lỗi nội bộ"). Về ngữ nghĩa,
  "manifest chưa sẵn sàng cài" là tình huống BÌNH THƯỜNG (không phải bug nội bộ) — dùng `E_INTERNAL` ở
  đây có thể gây hiểu sai mức nghiêm trọng khi tích hợp log/alerting thật (not blocking M1, ghi lại để
  chủ dự án/ WP3 cân nhắc).
- `test_evidence_validate_echoes_bad_gate_without_defensive_check` (PASS): WP3 tin tưởng tuyệt đối
  `GateResult` từ WP9, không tự kiểm tra lại `qa_reviewer`. Đây ĐÚNG theo nguyên tắc "không giẫm chân"
  (gate logic là trách nhiệm/test của WP9, xem T5), không coi là lỗi của WP3 — chỉ ghi lại để xác nhận
  WP3 không có lớp phòng vệ kép (single point of trust = WP9).
- 15 test `test_planner_adversarial.py` (PASS, dùng `DefaultInstallPlanner` THẬT của WP6): revoked (exact
  match, không prefix-leak), user/host strict case-sensitive + whitespace, hết hạn (boundary `>` chính
  xác, không `>=`), TOCTOU symlink-swap sau khi plan dựng xong (KHÔNG bypass được nhờ `O_NOFOLLOW`),
  multi-artifact tamper (reject toàn bộ dù chỉ 1/N bị đổi), installer path tương đối → `E_PATH_UNSAFE`,
  recipe bị dry-run từ chối → `E_SEMANTIC_RECIPE`. TẤT CẢ ĐÚNG hành vi kỳ vọng — `namios_planner` logic
  layer (độc lập khỏi lớp dispatch WP3 có bug ở trên) PASS toàn bộ negative suite của T3.

## Bảng tổng hợp

| test_id | mô tả | verdict |
| --- | --- | --- |
| CLI-01 | envelope sạch/exit-code mọi nhánh xác định được | PASS (10/10 case không liên quan 5 defect) |
| CLI-01 | exception từ WP2/WP6/WP9 thoát qua WP3 | **FAIL — 5 defect CONFIRMED** |
| CLI-02/03 (logic) | revoked/user/host/expiry/TOCTOU/multi-artifact qua `DefaultInstallPlanner` thật | PASS (15/15) |
