"""T4 — tester độc lập cụm State/journal/recovery (WP5 ``namios_txstate``).

Map test-matrix: TX-01 (ngắt tại từng bước journal → restart không false
READY, state nhất quán), WINE-03 phần khóa (2 mutation cùng prefix → 1 hợp lệ
1 chờ/conflict).

Viết ĐỘC LẬP với ``tests/unit/txstate/test_store.py`` và
``tests/system/txstate/*`` của dev (không sao chép case, không sửa file dev).
Trọng tâm KHÁC với dev:
  1. Kill tại TẤT CẢ các bước giữa chừng (parametrize đầy đủ chuỗi, kể cả
     ngay trước READY/VERIFYING) bằng tiến trình con thật (SIGKILL) — dev chỉ
     test 2 điểm (VALIDATED, INSTALLING) bằng subprocess thật.
  2. Đối chiếu SỐ DÒNG journal với số bước đã commit thật sau crash (dev chỉ
     kiểm state cuối, không đối chiếu đếm dòng).
  3. Race THẬT bằng tiến trình OS riêng biệt (không chỉ 2 lệnh gọi tuần tự
     trên CÙNG một connection/instance như test của dev) cho
     ``acquire_prefix_lock`` — mô phỏng WINE-03 "2 mutation cùng prefix".
  4. Kiểm tra lỗ hổng actual: liệu ``create_transaction``/``advance`` có tự
     ràng buộc với prefix lock hay không (API không bắt buộc caller giữ khóa
     trước khi mutate) — tìm defect thật nếu có.
  5. ``recover()`` gọi liên tiếp/đan xen trên tx đang ``RECOVERING`` không bị
     double-advance sai bảng chuyển.
"""

from __future__ import annotations

import signal
import sqlite3
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest

from namios_core.errors import ErrorCode
from namios_core.txstate import TxState
from namios_txstate.errors import StateConflictError
from namios_txstate.store import SqliteStateStore

_SRC_DIR = str(Path(__file__).resolve().parents[3] / "src")

# Toàn bộ chuỗi happy-path trừ NEW (đã là trạng thái khởi tạo).
_FULL_CHAIN = [
    TxState.VALIDATED,
    TxState.ACQUIRING,
    TxState.STAGING,
    TxState.INSTALLING,
    TxState.VERIFYING,
]


# ---------------------------------------------------------------------------
# 1) Kill tại MỌI bước giữa chừng (bao gồm ngay trước VERIFYING) — subprocess
#    thật bị SIGKILL, không phải giả lập exception.
# ---------------------------------------------------------------------------

_CHILD_SCRIPT = textwrap.dedent("""
    import os
    import signal as _signal
    import sys
    sys.path.insert(0, {src!r})
    from pathlib import Path
    from namios_txstate.store import SqliteStateStore
    from namios_core.txstate import TxState

    db_path = Path(sys.argv[1])
    stop_after = sys.argv[2]

    store = SqliteStateStore(db_path=db_path)
    store.open()
    tx = store.create_transaction("app.t4-crash", "inst-t4-1")
    sys.stdout.write(tx.tx_id)
    sys.stdout.flush()

    chain = [
        TxState.VALIDATED,
        TxState.ACQUIRING,
        TxState.STAGING,
        TxState.INSTALLING,
        TxState.VERIFYING,
    ]
    current = tx
    for i, to in enumerate(chain):
        current = store.advance(current.tx_id, to, f"op-{{i}}", f"buoc {{i}}")
        if to.value == stop_after:
            # Chết NGAY sau khi bước này đã commit — không finally, không dọn.
            os.kill(os.getpid(), _signal.SIGKILL)
    """)


def _run_child_and_get_tx_id(db_path: Path, stop_after: str) -> str:
    script = _CHILD_SCRIPT.format(src=_SRC_DIR)
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(db_path), stop_after],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == -signal.SIGKILL, (proc.returncode, proc.stdout, proc.stderr)
    tx_id = proc.stdout.strip()
    assert tx_id
    return tx_id


@pytest.mark.parametrize("stop_at", _FULL_CHAIN)
def test_kill_after_every_single_journal_step_never_produces_false_ready(
    tmp_path: Path, stop_at: TxState
) -> None:
    """TX-01: với MỖI bước của chuỗi (kể cả ngay trước VERIFYING, điểm sát
    READY nhất) — ngắt tiến trình thật rồi phục hồi KHÔNG BAO GIỜ false READY,
    và số dòng journal khớp đúng số bước đã thật sự commit (không thiếu,
    không dư) trước khi ``recover()`` can thiệp."""

    db_path = tmp_path / "state.sqlite3"
    tx_id = _run_child_and_get_tx_id(db_path, stop_after=stop_at.value)

    store = SqliteStateStore(db_path=db_path)
    store.open()

    before = store.get(tx_id)
    assert before is not None
    assert before.state is stop_at, "state đã lưu phải khớp đúng bước cuối commit trước khi chết"

    # Đối chiếu số dòng journal: 1 dòng "create" + đúng số bước đã advance
    # tới và bao gồm stop_at (index trong _FULL_CHAIN + 1), không có dòng
    # "ma" nào vượt quá bước đã thực sự hoàn tất.
    expected_steps = _FULL_CHAIN.index(stop_at) + 1
    rows = store._connection.execute(
        "SELECT before, after FROM journal WHERE tx_id = ? ORDER BY id ASC", (tx_id,)
    ).fetchall()
    assert len(rows) == 1 + expected_steps, (
        f"stop_at={stop_at}: kỳ vọng {1 + expected_steps} dòng journal, thấy {len(rows)}"
    )
    assert rows[-1]["after"] == stop_at.value

    recovered = store.recover()
    assert len(recovered) == 1
    assert recovered[0].tx_id == tx_id
    # Bất biến cốt lõi TX-001: không postcheck thật => KHÔNG BAO GIỜ READY,
    # BẤT KỂ bước nào bị ngắt (kể cả ngắt ngay sau VERIFYING).
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    assert store.get(tx_id).state is TxState.NEEDS_ATTENTION  # type: ignore[union-attr]

    # recover() lần 2 phải idempotent — không re-ghi journal thêm cho tx đã
    # ổn định ở NEEDS_ATTENTION.
    rows_after_first_recover = store._connection.execute(
        "SELECT COUNT(*) FROM journal WHERE tx_id = ?", (tx_id,)
    ).fetchone()[0]
    assert store.recover() == ()
    rows_after_second_recover = store._connection.execute(
        "SELECT COUNT(*) FROM journal WHERE tx_id = ?", (tx_id,)
    ).fetchone()[0]
    assert rows_after_second_recover == rows_after_first_recover


def test_kill_right_after_verifying_still_needs_attention_not_ready(tmp_path: Path) -> None:
    """Điểm biên quan trọng nhất: ngắt NGAY SAU KHI VERIFYING đã commit (chỉ
    còn một bước cuối tới READY) — phải vẫn NEEDS_ATTENTION, không được
    "lạc quan" vì state cuối cùng trông rất gần hoàn tất."""

    db_path = tmp_path / "state.sqlite3"
    tx_id = _run_child_and_get_tx_id(db_path, stop_after=TxState.VERIFYING.value)

    store = SqliteStateStore(db_path=db_path)
    store.open()
    assert store.get(tx_id).state is TxState.VERIFYING  # type: ignore[union-attr]

    recovered = store.recover()
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    assert recovered[0].state is not TxState.READY


# ---------------------------------------------------------------------------
# 2) Journal nói dối (write-ahead đã ghi "after" cao hơn thực tế do crash
#    giữa 2 câu lệnh) KHÔNG được recover() tin tưởng mù quáng, kể cả khi
#    journal "after" là một bước TRUNG GIAN khác (không chỉ READY như test
#    của dev) — ví dụ journal nói "after=VERIFYING" nhưng transactions.state
#    thực tế vẫn còn STAGING.
# ---------------------------------------------------------------------------


def test_recover_ignores_journal_entry_claiming_mid_flight_state_ahead_of_real_state(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "state.sqlite3"
    store = SqliteStateStore(db_path=db_path)
    store.open()
    tx = store.create_transaction("app.t4-liar", "inst-liar-1")
    tx = store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    tx = store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")
    tx = store.advance(tx.tx_id, TxState.STAGING, "op3", "x")

    # Giả lập: write-ahead journal cho bước STAGING->INSTALLING->VERIFYING
    # ĐÃ ghi (2 dòng), nhưng UPDATE transactions chưa áp dụng cho CẢ HAI —
    # tiến trình chết đúng lúc giữa ghi journal và UPDATE đầu tiên.
    raw = sqlite3.connect(str(db_path))
    raw.execute(
        "INSERT INTO journal (tx_id, operation_id, phase, when_ts, before, after, note_vi) "
        "VALUES (?, 'opX', 'advance', '2026-01-01T00:00:00+00:00', ?, ?, 'gia lap crash giua')",
        (tx.tx_id, TxState.STAGING.value, TxState.INSTALLING.value),
    )
    raw.execute(
        "INSERT INTO journal (tx_id, operation_id, phase, when_ts, before, after, note_vi) "
        "VALUES (?, 'opY', 'advance', '2026-01-01T00:00:01+00:00', ?, ?, 'gia lap crash giua')",
        (tx.tx_id, TxState.INSTALLING.value, TxState.VERIFYING.value),
    )
    raw.commit()
    raw.close()
    store.close()

    store2 = SqliteStateStore(db_path=db_path)
    store2.open()
    # transactions.state thực tế KHÔNG được cập nhật theo journal "nói dối".
    assert store2.get(tx.tx_id).state is TxState.STAGING  # type: ignore[union-attr]

    recovered = store2.recover()
    assert len(recovered) == 1
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    # recover() phải dựa vào transactions.state THẬT (STAGING, "đang chạy")
    # để đưa về FAILED->RECOVERING->NEEDS_ATTENTION, KHÔNG dựa journal cuối.


# ---------------------------------------------------------------------------
# 3) WINE-03 (phần khóa): race THẬT bằng tiến trình OS riêng biệt — không
#    chỉ 2 lệnh Python tuần tự trên cùng connection như test dev.
# ---------------------------------------------------------------------------

_LOCK_CHILD_SCRIPT = textwrap.dedent("""
    import sys
    sys.path.insert(0, {src!r})
    import time
    from pathlib import Path
    from namios_txstate.store import SqliteStateStore
    from namios_txstate.errors import StateConflictError

    db_path = Path(sys.argv[1])
    barrier_file = Path(sys.argv[2])

    store = SqliteStateStore(db_path=db_path)
    store.open()

    # Đồng bộ thô: ghi file đánh dấu "đã sẵn sàng", chờ tới khi CẢ HAI tiến
    # trình đều sẵn sàng rồi mới cùng giành khóa — tối đa hóa khả năng đụng
    # độ thật (race window hẹp) thay vì chạy tuần tự.
    marker = barrier_file.with_suffix(barrier_file.suffix + f".{{sys.argv[3]}}")
    marker.write_text("ready")
    deadline = time.time() + 10
    while time.time() < deadline:
        siblings = list(barrier_file.parent.glob(barrier_file.name + ".*"))
        if len(siblings) >= 2:
            break
        time.sleep(0.01)

    try:
        lock = store.acquire_prefix_lock("app.t4-race", "inst-race-1")
        print("WON")
        time.sleep(0.2)
        lock.release()
    except StateConflictError:
        print("CONFLICT")
    """)


def test_two_real_os_processes_racing_same_prefix_lock_exactly_one_wins(tmp_path: Path) -> None:
    """WINE-03: hai tiến trình OS ĐỘC LẬP (không chung connection/instance
    Python) tranh cùng (app_id, instance_id) đồng thời — đúng kịch bản
    "2 thao tác install/repair cùng prefix". Kỳ vọng: đúng 1 thắng
    (``acquire_prefix_lock`` thành công), cái còn lại nhận
    ``StateConflictError``/``E_STATE_CONFLICT`` — KHÔNG có đường nào cả hai
    cùng thắng (mutation song song thật)."""

    db_path = tmp_path / "state.sqlite3"
    # Tạo DB trước để tránh race khi tạo schema.
    setup_store = SqliteStateStore(db_path=db_path)
    setup_store.open()
    setup_store.close()

    barrier_file = tmp_path / "barrier"
    script = _LOCK_CHILD_SCRIPT.format(src=_SRC_DIR)

    procs = [
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-c", script, str(db_path), str(barrier_file), str(i)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(2)
    ]
    outputs = [p.communicate(timeout=15) for p in procs]
    for p, (_out, err) in zip(procs, outputs):
        assert p.returncode == 0, err

    results = [out.strip() for out, _err in outputs]
    assert results.count("WON") == 1, f"kỳ vọng đúng 1 tiến trình thắng khóa, thấy: {results}"
    assert results.count("CONFLICT") == 1, f"kỳ vọng đúng 1 tiến trình bị conflict, thấy: {results}"


def test_prefix_lock_race_many_threads_only_one_winner_no_double_grant(tmp_path: Path) -> None:
    """Stress race bằng nhiều luồng mỗi luồng có connection sqlite riêng
    (không chia sẻ connection như test dev) — chạy nhiều lần để bắt race
    hiếm nếu UNIQUE constraint không đủ atomic trong thực tế triển khai."""

    db_path = tmp_path / "state.sqlite3"
    setup_store = SqliteStateStore(db_path=db_path)
    setup_store.open()

    for round_idx in range(20):
        app_id = "app.t4-thread-race"
        instance_id = f"inst-round-{round_idx}"
        winners: list[int] = []
        conflicts: list[int] = []
        lock_box: list[object] = [None]
        start_barrier = threading.Barrier(5)

        def worker(idx: int) -> None:
            store = SqliteStateStore(db_path=db_path)
            store.open()
            start_barrier.wait()
            try:
                lock = store.acquire_prefix_lock(app_id, instance_id)
                winners.append(idx)
                lock_box[0] = lock
            except StateConflictError:
                conflicts.append(idx)
            finally:
                store.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(winners) == 1, f"round {round_idx}: kỳ vọng đúng 1 thắng, thấy {winners}"
        assert len(conflicts) == 4, f"round {round_idx}: kỳ vọng 4 conflict, thấy {conflicts}"

    setup_store.close()


# ---------------------------------------------------------------------------
# 4) Lỗ hổng tiềm ẩn: StateStore có tự ràng buộc prefix lock với
#    create_transaction/advance hay không? Acceptance WP5 nói "2 thao tác
#    cùng prefix ... không mutation song song" — kiểm tra liệu điều này có
#    được ÉP BUỘC bởi store, hay chỉ là một primitive RỜI mà caller phải tự
#    nhớ gọi (nếu caller quên, 2 mutation thật SẼ chạy song song).
# ---------------------------------------------------------------------------


def test_create_transaction_and_advance_do_not_require_holding_prefix_lock(
    tmp_path: Path,
) -> None:
    """ADVERSARIAL: cố ý KHÔNG gọi ``acquire_prefix_lock`` và tạo + advance
    HAI giao dịch khác nhau trên CÙNG (app_id, instance_id) — nếu cả hai
    thành công song song mà không ai bị ``E_STATE_CONFLICT``, đây là bằng
    chứng rằng ``advance()``/``create_transaction()`` của ``SqliteStateStore``
    KHÔNG tự thi hành mutex theo prefix; ``acquire_prefix_lock`` chỉ là một
    primitive độc lập mà caller (WP6 planner/WP3 CLI) phải tự nhớ gọi trước.
    Nếu test này PASS (không raise), đó là một FINDING cần báo cho dev/BA —
    không phải lỗi của bài test."""

    store = SqliteStateStore(db_path=tmp_path / "state.sqlite3")
    store.open()

    app_id, instance_id = "app.t4-bypass", "inst-bypass-1"

    tx_a = store.create_transaction(app_id, instance_id)
    tx_b = store.create_transaction(app_id, instance_id)  # KHÔNG bị chặn

    tx_a = store.advance(tx_a.tx_id, TxState.VALIDATED, "opA1", "x")
    tx_b = store.advance(tx_b.tx_id, TxState.VALIDATED, "opB1", "x")  # vẫn KHÔNG bị chặn

    tx_a = store.advance(tx_a.tx_id, TxState.ACQUIRING, "opA2", "x")
    tx_b = store.advance(tx_b.tx_id, TxState.ACQUIRING, "opB2", "x")

    # Cả hai giao dịch trên CÙNG prefix tiến lên song song, không ai bị
    # StateConflictError — xác nhận: mutex KHÔNG được store tự áp dụng vào
    # luồng mutate chính, chỉ tồn tại ở API acquire_prefix_lock() rời.
    assert tx_a.state is TxState.ACQUIRING
    assert tx_b.state is TxState.ACQUIRING
    assert tx_a.tx_id != tx_b.tx_id

    # Dùng acquire_prefix_lock() rõ ràng vẫn hoạt động đúng CHO BẢN THÂN NÓ
    # (vòng đời lock), nhưng điều đó không hồi tố ràng buộc hai mutation
    # vừa chạy song song ở trên.
    lock = store.acquire_prefix_lock(app_id, instance_id)
    with pytest.raises(StateConflictError):
        store.acquire_prefix_lock(app_id, instance_id)
    lock.release()


# ---------------------------------------------------------------------------
# 5) recover() gọi đan xen/lặp lại trên tx đang dở KHÔNG được double-apply
#    hoặc vi phạm bảng chuyển khi có ngoại lệ bất ngờ.
# ---------------------------------------------------------------------------


def test_recover_twice_in_a_row_on_same_failed_tx_without_reopen_is_consistent(
    tmp_path: Path,
) -> None:
    store = SqliteStateStore(db_path=tmp_path / "state.sqlite3")
    store.open()
    tx = store.create_transaction("app.t4-double-recover", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")

    first = store.recover()
    assert len(first) == 1
    assert first[0].state is TxState.NEEDS_ATTENTION

    # Gọi recover() LẦN NỮA trên CÙNG store (không mở lại) — không được
    # cố advance lại NEEDS_ATTENTION theo nhánh "đang chạy" (nó đã resting).
    second = store.recover()
    assert second == ()
    assert store.get(tx.tx_id).state is TxState.NEEDS_ATTENTION  # type: ignore[union-attr]

    # Journal không phình thêm dòng "ma" cho lần gọi thứ hai.
    rows = store._connection.execute(
        "SELECT COUNT(*) FROM journal WHERE tx_id = ?", (tx.tx_id,)
    ).fetchone()[0]
    assert store.recover() == ()
    rows_again = store._connection.execute(
        "SELECT COUNT(*) FROM journal WHERE tx_id = ?", (tx.tx_id,)
    ).fetchone()[0]
    assert rows == rows_again


def test_cancelling_mid_flight_tx_survives_crash_recovery_without_turning_into_ready(
    tmp_path: Path,
) -> None:
    """Giao dịch đang CANCELLING khi crash (không phải happy-path) cũng phải
    đi qua FAILED->RECOVERING->NEEDS_ATTENTION, KHÔNG được "khôi phục" thành
    READY (một giao dịch đang bị hủy không bao giờ nên trở thành READY)."""

    store = SqliteStateStore(db_path=tmp_path / "state.sqlite3")
    store.open()
    tx = store.create_transaction("app.t4-cancel-crash", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    store.advance(tx.tx_id, TxState.CANCELLING, "op2", "huy giua duong")
    # "crash" ngay sau khi vào CANCELLING (chưa tới CANCELLED/NEEDS_ATTENTION).

    recovered = store.recover()
    assert len(recovered) == 1
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    assert recovered[0].state is not TxState.READY
    assert recovered[0].state is not TxState.CANCELLED


def test_postcheck_exception_during_recover_does_not_leave_tx_as_ready(
    tmp_path: Path,
) -> None:
    """ADVERSARIAL: postcheck ĐỘC (ví dụ WP6 verify-at-apply) ném exception
    thay vì trả True/False — recover() không được để lộ một tx ở trạng thái
    READY một cách tình cờ nếu postcheck hỏng; nên fail loudly hoặc coi như
    chưa xác nhận (an toàn), KHÔNG bao giờ im lặng coi exception == verified."""

    def _flaky_postcheck(_tx: object) -> bool:
        raise RuntimeError("WP6 postcheck bi loi gia lap (vd mat ket noi disk)")

    store = SqliteStateStore(db_path=tmp_path / "state.sqlite3", postcheck=_flaky_postcheck)
    store.open()
    tx = store.create_transaction("app.t4-flaky-postcheck", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")

    try:
        store.recover()
    except Exception:
        # Exception lan ra ngoài là AN TOÀN (không âm thầm coi là verified).
        # Trạng thái lưu trong DB tại điểm này KHÔNG được là READY.
        pass

    final = store.get(tx.tx_id)
    assert final is not None
    assert final.state is not TxState.READY, (
        "postcheck exception không được vô tình khiến tx bị đánh dấu READY"
    )


def test_error_code_mapping_stable_for_state_conflict_from_bad_transition(
    tmp_path: Path,
) -> None:
    """Đối chiếu mã lỗi ổn định (M1-INTERFACES) không bị đổi ngầm: mọi
    transition sai phải là đúng E_STATE_CONFLICT, không phải mã khác (vd
    E_INPUT_SCHEMA) dù message_vi thay đổi thế nào."""

    store = SqliteStateStore(db_path=tmp_path / "state.sqlite3")
    store.open()
    tx = store.create_transaction("app.t4-errcode", "inst-1")

    # NEW -> READY: không có trong bảng chuyển, phải reject với đúng mã.
    with pytest.raises(StateConflictError) as excinfo:
        store.advance(tx.tx_id, TxState.READY, "op1", "nhay thang tu NEW")
    assert excinfo.value.code is ErrorCode.E_STATE_CONFLICT

    # REMOVED (terminal, không trong từ điển VALID_TRANSITIONS với khóa) ->
    # bất kỳ đâu đều phải reject.
    store.advance(tx.tx_id, TxState.VALIDATED, "op2", "x")
    store.advance(tx.tx_id, TxState.ACQUIRING, "op3", "x")
    store.advance(tx.tx_id, TxState.STAGING, "op4", "x")
    store.advance(tx.tx_id, TxState.INSTALLING, "op5", "x")
    store.advance(tx.tx_id, TxState.VERIFYING, "op6", "x")
    store.advance(tx.tx_id, TxState.READY, "op7", "x")
    store.advance(tx.tx_id, TxState.REMOVING, "op8", "x")
    store.advance(tx.tx_id, TxState.REMOVED, "op9", "x")

    with pytest.raises(StateConflictError) as excinfo2:
        store.advance(tx.tx_id, TxState.VALIDATED, "op10", "khong duoc, da REMOVED")
    assert excinfo2.value.code is ErrorCode.E_STATE_CONFLICT
