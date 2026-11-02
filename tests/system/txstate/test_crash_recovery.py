"""TX-01 (system): mô phỏng crash GIỮA các bước giao dịch bằng tiến trình con
thật (SIGKILL) + bằng ghi journal thủ công (mô phỏng crash giữa journal-write
và cập nhật bảng ``transactions``), rồi kiểm ``recover()`` KHÔNG BAO GIỜ đưa
giao dịch dở về ``READY`` một cách sai (false READY).

Theo acceptance WP5 (M1-WORK-PACKAGES.md): "Mô phỏng kill sau mỗi journal
step rồi recover(): không tx nào ở READY nếu chưa VERIFYING pass; state nhất
quán." + "chạy được tại đây" (process con/giả lập, không cần VM thật).
"""

from __future__ import annotations

import signal
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

from namios_core.txstate import TxState
from namios_txstate.store import SqliteStateStore

_CHILD_SCRIPT = textwrap.dedent("""
    import sys
    sys.path.insert(0, {src!r})
    from pathlib import Path
    from namios_txstate.store import SqliteStateStore
    from namios_core.txstate import TxState

    db_path = Path(sys.argv[1])
    stop_after = sys.argv[2]

    store = SqliteStateStore(db_path=db_path)
    store.open()
    tx = store.create_transaction("app.crash-demo", "inst-crash-1")
    sys.stdout.write(tx.tx_id)
    sys.stdout.flush()

    chain = [TxState.VALIDATED, TxState.ACQUIRING, TxState.STAGING, TxState.INSTALLING]
    current = tx
    for i, to in enumerate(chain):
        current = store.advance(current.tx_id, to, f"op-{{i}}", f"buoc {{i}}")
        if to.value == stop_after:
            # "Crash" ngay sau khi bước này HOÀN TẤT (đã commit) — tiến trình
            # tự giết chính nó để mô phỏng mất tiến trình giữa hai bước kế
            # tiếp của giao dịch (không có cơ hội dọn dẹp/finally).
            import os, signal as _signal
            os.kill(os.getpid(), _signal.SIGKILL)
    """)


def _run_child_and_get_tx_id(db_path: Path, stop_after: str) -> str:
    src_dir = str(Path(__file__).resolve().parents[3] / "src")
    script = _CHILD_SCRIPT.format(src=src_dir)
    # argv cố định (sys.executable + "-c" + script sinh từ template nội bộ,
    # không có input người dùng/mạng); shell=False, không shell=True/eval.
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(db_path), stop_after],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Tiến trình con PHẢI chết bởi SIGKILL (crash thật), không phải exit code 0.
    assert proc.returncode == -signal.SIGKILL, (proc.returncode, proc.stdout, proc.stderr)
    tx_id = proc.stdout.strip()
    assert tx_id
    return tx_id


def test_real_process_killed_mid_flight_recovers_without_false_ready(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    tx_id = _run_child_and_get_tx_id(db_path, stop_after=TxState.INSTALLING.value)

    # Tiến trình mới (store mới) mở lại DB sau "crash" và phục hồi.
    store = SqliteStateStore(db_path=db_path)
    store.open()
    before = store.get(tx_id)
    assert before is not None
    assert before.state is TxState.INSTALLING  # bước cuối đã commit thật trước khi bị kill

    recovered = store.recover()
    assert len(recovered) == 1
    assert recovered[0].tx_id == tx_id
    # Bất biến cốt lõi: không có postcheck thật => KHÔNG BAO GIỜ tự thành READY.
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    assert store.get(tx_id).state is TxState.NEEDS_ATTENTION  # type: ignore[union-attr]

    # recover() lần 2 không còn gì để xử lý (đã ổn định ở NEEDS_ATTENTION).
    assert store.recover() == ()


def test_real_process_killed_right_after_validated_also_recovers_safely(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    tx_id = _run_child_and_get_tx_id(db_path, stop_after=TxState.VALIDATED.value)

    store = SqliteStateStore(db_path=db_path)
    store.open()
    assert store.get(tx_id).state is TxState.VALIDATED  # type: ignore[union-attr]

    recovered = store.recover()
    assert recovered[0].state is TxState.NEEDS_ATTENTION


def test_crash_between_journal_write_and_state_update_is_not_trusted_blindly(
    tmp_path: Path,
) -> None:
    """Mô phỏng crash ở hạt mịn nhất: journal ĐÃ ghi "after=READY" (write-ahead
    đã xảy ra) nhưng bảng ``transactions`` CHƯA được cập nhật (tiến trình chết
    đúng giữa hai câu lệnh) — ``recover()`` KHÔNG được tin journal cũ, vẫn
    phải đòi bằng chứng thật (postcheck) trước khi cho READY."""

    db_path = tmp_path / "state.sqlite3"
    store = SqliteStateStore(db_path=db_path)
    store.open()
    tx = store.create_transaction("app.crash-demo", "inst-crash-2")
    tx = store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    tx = store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")
    tx = store.advance(tx.tx_id, TxState.STAGING, "op3", "x")
    tx = store.advance(tx.tx_id, TxState.INSTALLING, "op4", "x")
    tx = store.advance(tx.tx_id, TxState.VERIFYING, "op5", "x")

    # Mô phỏng: write-ahead journal cho bước VERIFYING->READY đã ghi xong,
    # nhưng UPDATE transactions SET state=READY chưa xảy ra khi crash.
    raw = sqlite3.connect(str(db_path))
    raw.execute(
        "INSERT INTO journal (tx_id, operation_id, phase, when_ts, before, after, note_vi) "
        "VALUES (?, 'op6', 'advance', '2026-01-01T00:00:00+00:00', ?, ?, 'gia lap crash')",
        (tx.tx_id, TxState.VERIFYING.value, TxState.READY.value),
    )
    raw.commit()
    raw.close()
    store.close()

    # transactions.state thật vẫn còn VERIFYING (chưa được áp dụng).
    store2 = SqliteStateStore(db_path=db_path)
    store2.open()
    assert store2.get(tx.tx_id).state is TxState.VERIFYING  # type: ignore[union-attr]

    recovered = store2.recover()
    assert len(recovered) == 1
    # Dù journal "nói" là READY, không có postcheck thật => vẫn NEEDS_ATTENTION.
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    assert recovered[0].state is not TxState.READY


def test_crash_then_postcheck_confirms_real_completion_allows_ready(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    tx_id = _run_child_and_get_tx_id(db_path, stop_after=TxState.INSTALLING.value)

    # Lần này store có postcheck thật (giả lập: WP6/WP9 xác nhận file đã verify
    # xong) -> được phép phục hồi về READY, nhưng CHỈ vì có bằng chứng.
    store = SqliteStateStore(db_path=db_path, postcheck=lambda tx: tx.tx_id == tx_id)
    store.open()
    recovered = store.recover()
    assert recovered[0].state is TxState.READY
