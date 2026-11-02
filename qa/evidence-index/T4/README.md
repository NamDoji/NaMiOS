# T4 — State / journal / recovery — evidence (02/11/2026)

**Tester:** T4 (độc lập, không phải dev WP5). **Phạm vi:** TX-01, WINE-03
(phần khóa), nhắm vào `namios_txstate` (WP5 — `SqliteStateStore`).
**Test file:** `tests/qa/T4/test_t4_adversarial.py` (14 test, viết độc lập
với `tests/unit/txstate/test_store.py` và `tests/system/txstate/*` của dev —
không sao chép case, không sửa file dev).

## Lệnh chạy

```
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/node/.openclaw/workspace/code_projects/namios/src \
/home/node/.openclaw/workspace/code_projects/namios/.venv/bin/python -m pytest \
  /home/node/.openclaw/workspace/code_projects/namios/tests/qa/T4 \
  -p no:cacheprovider -q
```

## Kết quả (commit `b0a96d66`, Python 3.11.2, Debian 12)

```
14 passed in ~2.5-2.7s (chạy lặp 4 lần liên tiếp để kiểm tính ổn định của
test timing-sensitive — race bằng threads/subprocess — không có lần nào
flaky/fail ngẫu nhiên)
```

Toàn bộ 14/14 PASS. Trong đó:

### Khẳng định bất biến ĐANG ĐÚNG (12 test)
- `test_kill_after_every_single_journal_step_never_produces_false_ready`
  (parametrize 5 điểm: VALIDATED, ACQUIRING, STAGING, INSTALLING, VERIFYING)
  — ngắt tiến trình thật (SIGKILL) tại MỖI bước của chuỗi, kể cả **ngay sau
  VERIFYING** (điểm sát READY nhất) — `recover()` không bao giờ false READY,
  và số dòng journal khớp CHÍNH XÁC số bước đã commit thật (không thiếu,
  không dư dòng "ma").
- `test_kill_right_after_verifying_still_needs_attention_not_ready` — biên
  quan trọng nhất của TX-001, xác nhận lại rõ ràng.
- `test_recover_ignores_journal_entry_claiming_mid_flight_state_ahead_of_real_state`
  — journal "nói dối" ở một bước TRUNG GIAN (không chỉ READY) vẫn không được
  tin; `recover()` dựa vào `transactions.state` thật.
- `test_two_real_os_processes_racing_same_prefix_lock_exactly_one_wins`
  (WINE-03) — hai **tiến trình OS độc lập** (không chung connection Python
  như test dev) tranh cùng prefix đồng thời (đồng bộ bằng file-marker để thu
  hẹp race window) → đúng 1 `WON`, đúng 1 `CONFLICT`, không lần nào cả hai
  cùng thắng.
- `test_prefix_lock_race_many_threads_only_one_winner_no_double_grant` — 20
  vòng × 5 luồng (mỗi luồng connection sqlite riêng) tranh cùng prefix → mọi
  vòng đều đúng 1 thắng/4 conflict, không có double-grant nào qua UNIQUE
  constraint.
- `test_recover_twice_in_a_row_on_same_failed_tx_without_reopen_is_consistent`,
  `test_cancelling_mid_flight_tx_survives_crash_recovery_without_turning_into_ready`,
  `test_postcheck_exception_during_recover_does_not_leave_tx_as_ready`,
  `test_error_code_mapping_stable_for_state_conflict_from_bad_transition` —
  các biên phụ (CANCELLING giữa đường, postcheck lỗi, mã lỗi ổn định).

### Finding cần báo cho dev/BA (1 test PASS nhưng là bằng chứng gap thiết kế)
- `test_create_transaction_and_advance_do_not_require_holding_prefix_lock`
  — xem `defects.md` mục D1. Test PASS (không raise) chính là bằng chứng:
  `create_transaction()`/`advance()` của `SqliteStateStore` **không tự ràng
  buộc** với `acquire_prefix_lock()` — hai giao dịch khác nhau trên CÙNG
  `(app_id, instance_id)` tiến song song thoải mái nếu caller không tự nhớ
  giữ khóa trước. Không phải test sai; là gap giữa acceptance WP5 ("2 thao
  tác cùng prefix ... không mutation song song") và hiện thực (chỉ có
  primitive rời, không có enforcement tự động).

## Không chạy được tại đây (not applicable trong phạm vi T4)

Không có dòng `blocked_external_dependency`. TX-01 và WINE-03 (phần khóa)
đều chạy được bằng subprocess/threads thật ngay tại host này (Debian 12,
không cần VM/Wine) — khớp đúng mô tả QA plan "Mô phỏng kill bằng subprocess
+ SIGKILL" và "unit-able, không cần wine" cho WINE-03 phần khóa.
