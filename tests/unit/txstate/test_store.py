"""Unit test ``namios_txstate.store.SqliteStateStore`` — hiện thực
``namios_core.txstate.StateStore`` (§7.3, TX-001). Gồm negative cases:
chuyển trạng thái sai, tx không tồn tại, mutex bận, path không an toàn."""

from __future__ import annotations

from pathlib import Path

import pytest

from namios_core.errors import ErrorCode, exit_code_for
from namios_core.exitcodes import ExitCode
from namios_core.txstate import TxState
from namios_txstate.errors import PathUnsafeError, StateConflictError, TransactionNotFoundError
from namios_txstate.store import SqliteStateStore


def _store(tmp_path: Path) -> SqliteStateStore:
    s = SqliteStateStore(db_path=tmp_path / "state.sqlite3")
    s.open()
    return s


# -- create_transaction / get -------------------------------------------------


def test_create_transaction_starts_at_new(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")

    assert tx.state is TxState.NEW
    assert tx.app_id == "app.demo"
    assert tx.instance_id == "inst-1"
    fetched = store.get(tx.tx_id)
    assert fetched == tx


def test_get_unknown_tx_id_returns_none(tmp_path: Path) -> None:
    store = _store(tmp_path)
    assert store.get("khong-ton-tai") is None


def test_open_is_idempotent_and_persists_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    store1 = SqliteStateStore(db_path=db_path)
    store1.open()
    tx = store1.create_transaction("app.a", "i1")
    store1.close()

    store2 = SqliteStateStore(db_path=db_path)
    store2.open()
    assert store2.get(tx.tx_id) == tx


# -- advance / state machine ------------------------------------------------


def test_full_happy_path_chain_to_ready(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")

    chain = [
        TxState.VALIDATED,
        TxState.ACQUIRING,
        TxState.STAGING,
        TxState.INSTALLING,
        TxState.VERIFYING,
        TxState.READY,
    ]
    current = tx
    for i, to in enumerate(chain):
        current = store.advance(current.tx_id, to, operation_id=f"op-{i}", note_vi=f"buoc {i}")
        assert current.state is to

    assert store.get(tx.tx_id).state is TxState.READY  # type: ignore[union-attr]


def test_installing_to_ready_direct_rejected(tmp_path: Path) -> None:
    """Bất biến TX-001: không được nhảy thẳng INSTALLING -> READY, phải qua VERIFYING."""
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")
    tx = store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    tx = store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")
    tx = store.advance(tx.tx_id, TxState.STAGING, "op3", "x")
    tx = store.advance(tx.tx_id, TxState.INSTALLING, "op4", "x")

    with pytest.raises(StateConflictError) as excinfo:
        store.advance(tx.tx_id, TxState.READY, "op5", "nhay thang")

    assert excinfo.value.code is ErrorCode.E_STATE_CONFLICT
    assert exit_code_for(excinfo.value.code) is ExitCode.CONFLICT
    # Trạng thái lưu trong DB KHÔNG đổi khi transition bị từ chối.
    assert store.get(tx.tx_id).state is TxState.INSTALLING  # type: ignore[union-attr]


def test_new_to_arbitrary_far_state_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")
    with pytest.raises(StateConflictError):
        store.advance(tx.tx_id, TxState.VERIFYING, "op1", "nhay xa")


def test_terminal_states_have_no_outgoing_transition(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")
    tx = store.advance(tx.tx_id, TxState.CANCELLING, "op1", "huy")
    tx = store.advance(tx.tx_id, TxState.CANCELLED, "op2", "huy xong")

    with pytest.raises(StateConflictError):
        store.advance(tx.tx_id, TxState.RECOVERING, "op3", "khong duoc")


def test_advance_unknown_tx_id_raises_not_found(tmp_path: Path) -> None:
    store = _store(tmp_path)
    with pytest.raises(TransactionNotFoundError):
        store.advance("khong-ton-tai", TxState.VALIDATED, "op1", "x")


def test_advance_journals_before_updating_state(tmp_path: Path) -> None:
    """append_journal ghi TRƯỚC khi transactions.state đổi — kiểm bằng cách
    đếm số dòng journal tăng đúng 1 sau mỗi advance() và nội dung khớp."""

    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")  # đã có 1 dòng journal "create"

    rows_before = store._connection.execute("SELECT COUNT(*) FROM journal").fetchone()[0]
    store.advance(tx.tx_id, TxState.VALIDATED, "op-1", "ghi nhan buoc 1")
    rows_after = store._connection.execute("SELECT COUNT(*) FROM journal").fetchone()[0]

    assert rows_after == rows_before + 1
    last = store._connection.execute(
        "SELECT before, after, operation_id, note_vi FROM journal ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert last["before"] == TxState.NEW.value
    assert last["after"] == TxState.VALIDATED.value
    assert last["operation_id"] == "op-1"
    assert last["note_vi"] == "ghi nhan buoc 1"


# -- prefix mutex -------------------------------------------------------------


def test_prefix_lock_second_acquire_conflicts(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lock = store.acquire_prefix_lock("app.demo", "inst-1")

    with pytest.raises(StateConflictError) as excinfo:
        store.acquire_prefix_lock("app.demo", "inst-1")
    assert excinfo.value.code is ErrorCode.E_STATE_CONFLICT

    lock.release()
    # Sau release, giành lại được — không mutation song song bị kẹt vĩnh viễn.
    lock2 = store.acquire_prefix_lock("app.demo", "inst-1")
    lock2.release()


def test_prefix_lock_different_instance_does_not_conflict(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lock_a = store.acquire_prefix_lock("app.demo", "inst-1")
    lock_b = store.acquire_prefix_lock("app.demo", "inst-2")  # instance khác, không đụng
    lock_a.release()
    lock_b.release()


def test_prefix_lock_release_twice_is_safe(tmp_path: Path) -> None:
    store = _store(tmp_path)
    lock = store.acquire_prefix_lock("app.demo", "inst-1")
    lock.release()
    lock.release()  # không raise


# -- recover() -----------------------------------------------------------------


def test_recover_with_no_stuck_transactions_returns_empty(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")
    store.advance(tx.tx_id, TxState.CANCELLING, "op1", "x")
    store.advance(tx.tx_id, TxState.CANCELLED, "op2", "x")

    assert store.recover() == ()


def test_recover_stuck_mid_flight_without_postcheck_goes_to_needs_attention(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")
    store.advance(tx.tx_id, TxState.STAGING, "op3", "x")
    store.advance(tx.tx_id, TxState.INSTALLING, "op4", "x")
    # "crash" ở đây = tiến trình chết trong lúc INSTALLING, store mới mở lên.

    recovered = store.recover()
    assert len(recovered) == 1
    assert recovered[0].tx_id == tx.tx_id
    assert recovered[0].state is TxState.NEEDS_ATTENTION
    # Không bao giờ là READY khi không có kiểm tra thực tế.
    assert store.get(tx.tx_id).state is not TxState.READY  # type: ignore[union-attr]


def test_recover_with_postcheck_true_promotes_to_ready(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    store = SqliteStateStore(db_path=db_path, postcheck=lambda tx: True)
    store.open()
    tx = store.create_transaction("app.demo", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    store.advance(tx.tx_id, TxState.ACQUIRING, "op2", "x")
    store.advance(tx.tx_id, TxState.STAGING, "op3", "x")
    store.advance(tx.tx_id, TxState.INSTALLING, "op4", "x")
    store.advance(tx.tx_id, TxState.VERIFYING, "op5", "x")

    recovered = store.recover()
    assert recovered[0].state is TxState.READY


def test_recover_with_postcheck_false_stays_needs_attention(tmp_path: Path) -> None:
    db_path = tmp_path / "state.sqlite3"
    store = SqliteStateStore(db_path=db_path, postcheck=lambda tx: False)
    store.open()
    tx = store.create_transaction("app.demo", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")

    recovered = store.recover()
    assert recovered[0].state is TxState.NEEDS_ATTENTION


def test_recover_is_idempotent_on_needs_attention(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tx = store.create_transaction("app.demo", "inst-1")
    store.advance(tx.tx_id, TxState.VALIDATED, "op1", "x")
    first = store.recover()
    assert first[0].state is TxState.NEEDS_ATTENTION

    # Gọi lại recover() không xử lý lại NEEDS_ATTENTION đã ổn định.
    second = store.recover()
    assert second == ()
    assert store.get(tx.tx_id).state is TxState.NEEDS_ATTENTION  # type: ignore[union-attr]


# -- path safety ---------------------------------------------------------------


def test_open_rejects_symlinked_parent_dir(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir, target_is_directory=True)

    store = SqliteStateStore(db_path=link_dir / "state.sqlite3")
    with pytest.raises(PathUnsafeError):
        store.open()


def test_open_rejects_symlinked_db_file(tmp_path: Path) -> None:
    real_file = tmp_path / "real.sqlite3"
    real_file.write_text("khong phai db")
    link_file = tmp_path / "state.sqlite3"
    link_file.symlink_to(real_file)

    store = SqliteStateStore(db_path=link_file)
    with pytest.raises(PathUnsafeError):
        store.open()


def test_state_db_path_default_uses_namios_core_paths(
    xdg_tmp_dirs, monkeypatch: pytest.MonkeyPatch
) -> None:
    from namios_core.paths import state_db_path

    store = SqliteStateStore()  # không truyền db_path -> dùng namios_core.paths.state_db_path()
    assert store._db_path == state_db_path()
    store.open()
    assert store._db_path.exists()
    store.close()
