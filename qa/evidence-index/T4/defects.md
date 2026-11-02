# T4 defects/findings — WP5 namios_txstate (02/11/2026)

KHÔNG tự sửa code dev — chỉ báo cáo theo quy tắc T4. Không có test FAIL do
code sai trong 14 test; 1 finding dưới đây là PASS nhưng lộ ra gap thiết kế
đáng chú ý theo đúng tinh thần adversarial (test được thiết kế để CHỨNG MINH
một hành vi nguy hiểm có xảy ra được hay không — nó xảy ra được).

---

## D1 — `SqliteStateStore.create_transaction()`/`advance()` KHÔNG tự ràng
buộc với `acquire_prefix_lock()` — 2 mutation cùng prefix chạy song song
được nếu caller quên giữ khóa trước

- **File/line:** `src/namios_txstate/store.py:179-249` (`create_transaction`,
  `advance`) so với `src/namios_txstate/store.py:270-286`
  (`acquire_prefix_lock`).
- **Test lộ ra (PASS, dùng để chứng minh hành vi):**
  `tests/qa/T4/test_t4_adversarial.py::test_create_transaction_and_advance_do_not_require_holding_prefix_lock`
- **Repro:**
  ```python
  store = SqliteStateStore(db_path=...)
  store.open()
  app_id, instance_id = "app.demo", "inst-1"

  tx_a = store.create_transaction(app_id, instance_id)   # không cần lock
  tx_b = store.create_transaction(app_id, instance_id)   # vẫn không bị chặn

  store.advance(tx_a.tx_id, TxState.VALIDATED, "opA1", "x")   # OK
  store.advance(tx_b.tx_id, TxState.VALIDATED, "opB1", "x")   # vẫn OK, song song
  ```
  Cả `tx_a` và `tx_b` — hai giao dịch KHÁC NHAU, cùng `(app_id, instance_id)`
  — tiến song song không hạn chế qua nhiều bước, không ai bị
  `StateConflictError`.
- **Expected (theo acceptance WP5, M1-WORK-PACKAGES.md):** "Hai thao tác
  cùng prefix: cái thứ hai nhận `E_STATE_CONFLICT` (hoặc chờ), không mutation
  song song." Đọc theo nghĩa tự nhiên, đây là một bất biến của HỆ THỐNG
  (WP5), không chỉ của một primitive rời mà caller phải tự nhớ gọi đúng.
- **Actual:** `create_transaction()` và `advance()` hoàn toàn độc lập với
  bảng `prefix_locks`/`acquire_prefix_lock()`. Primitive khóa hoạt động
  ĐÚNG khi được gọi (đã xác nhận ở test khác — UNIQUE constraint thật, race
  thật bằng OS process/threads đều chỉ cho đúng 1 người thắng) — nhưng
  KHÔNG có đường nào trong `SqliteStateStore` tự động giữ/kiểm khóa trước
  khi mutate `transactions`. Nếu caller (dự kiến là WP6 planner hoặc WP3
  CLI) quên gọi `acquire_prefix_lock()` trước `create_transaction()`/
  `advance()` — điều mà interface `StateStore` Protocol trong
  `namios_core/txstate.py` KHÔNG ép buộc về mặt kiểu/thứ tự gọi — thì 2
  mutation thật SẼ chạy song song trên cùng prefix, đúng kịch bản WINE-03
  cố tránh.
- **Mức độ rủi ro:** Trung bình-cao cho M1 (lõi state máy), vì đây là lớp
  nền mà WP6 (planner) và cuối cùng CLI dựa vào để đảm bảo "không 2 install
  cùng lúc trên 1 prefix". Nếu WP6 hiện thực đúng (luôn gọi
  `acquire_prefix_lock` trước khi `create_transaction`), rủi ro thực tế được
  giảm thiểu ở lớp gọi — nhưng bản thân WP5 không tự bảo vệ, nên BẤT KỲ
  caller nào khác (debug tool, test, CLI path khác) bỏ qua bước này đều có
  thể gây 2 giao dịch mutate đồng thời 1 prefix mà không có cảnh báo nào.
- **Gợi ý cho dev (không áp đặt):** xem xét 1 trong 2 hướng — (a) để
  `create_transaction()` tự `acquire_prefix_lock()` nội bộ (giữ khóa xuyên
  đời giao dịch, release khi vào trạng thái nghỉ), hoặc (b) nếu thiết kế
  hiện tại là CHỦ Ý (khóa là trách nhiệm của caller/WP6, WP5 chỉ cấp
  primitive) — nên ghi rõ điều này trong docstring của
  `namios_core.txstate.StateStore.acquire_prefix_lock` và trong
  M1-WORK-PACKAGES.md để tránh hiểu nhầm "hệ thống tự chặn" khi thực ra là
  "caller phải tự gọi".

---

## Không phải defect

Không có case nào trong 14 test phải sửa lại kỳ vọng — mọi test khẳng định
bất biến TX-001 (never false READY qua mọi điểm kill, mọi nhánh
CANCELLING/postcheck lỗi) và WINE-03 phần khóa (UNIQUE constraint race thật
bằng OS process/threads) đều PASS đúng như mong đợi của đặc tả, không có
false positive nào cần chỉnh.
