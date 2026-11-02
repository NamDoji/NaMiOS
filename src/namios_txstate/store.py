"""Hiện thực ``StateStore`` (M1-INTERFACES.md §7.3, TX-001, COMP-005) trên
``state.sqlite3`` — bảng ``transactions`` + ``journal`` + ``prefix_locks``.

Bất biến bắt buộc:
- Mỗi lần ``advance()`` ghi journal TRƯỚC khi cập nhật bảng ``transactions``
  (write-ahead) — nếu crash xảy ra GIỮA hai bước này, ``recover()`` phát hiện
  được qua so khớp journal cuối cùng với trạng thái đã lưu.
- ``advance()`` KHÔNG BAO GIỜ bỏ qua bảng chuyển hợp lệ (§4) — sai →
  ``StateConflictError`` (``E_STATE_CONFLICT``).
- ``recover()`` KHÔNG BAO GIỜ tự đặt ``READY`` cho giao dịch dở trừ khi có
  ``postcheck`` xác nhận thực tế (được truyền khi khởi tạo store); mặc định
  không có postcheck ⇒ luôn dừng ở ``NEEDS_ATTENTION`` — an toàn hơn là lạc
  quan (không có "false READY").
- Mutex theo (``app_id``, ``instance_id``) hiện thực bằng UNIQUE constraint
  trên bảng ``prefix_locks``; giành khóa khi đang bận → ``StateConflictError``.
"""

from __future__ import annotations

import os
import sqlite3
import stat
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from namios_core.paths import state_db_path
from namios_core.txstate import JournalEntry, PrefixLock, Transaction, TxState, validate_transition
from namios_txstate.errors import PathUnsafeError, StateConflictError, TransactionNotFoundError

#: Trạng thái coi là "nghỉ yên" — KHÔNG cần ``recover()`` xử lý lại.
_RESTING_STATES = frozenset(
    {TxState.READY, TxState.CANCELLED, TxState.REMOVED, TxState.NEEDS_ATTENTION}
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


def _assert_safe_db_path(db_path: Path) -> None:
    """Kiểm tra tối thiểu chống symlink lạ trước khi mở DB (SEC-002).

    ``state_db_path()`` được tính từ biến XDG của tiến trình (không phải input
    tùy ý của người dùng ở runtime), nhưng vẫn kiểm tra: thư mục cha và file
    DB (nếu đã tồn tại) KHÔNG được là symlink — chặn kiểu tấn công tráo
    symlink trước khi mở.
    """

    parent = db_path.parent
    if parent.exists() and parent.is_symlink():
        raise PathUnsafeError(
            f"Thư mục chứa state.sqlite3 là symlink, từ chối mở: {parent}",
            details={"path": str(parent)},
        )
    if db_path.exists() and db_path.is_symlink():
        raise PathUnsafeError(
            f"state.sqlite3 là symlink, từ chối mở: {db_path}",
            details={"path": str(db_path)},
        )
    if db_path.exists() and not db_path.is_file():
        raise PathUnsafeError(
            f"state.sqlite3 không phải file thường, từ chối mở: {db_path}",
            details={"path": str(db_path)},
        )


_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    tx_id TEXT PRIMARY KEY,
    app_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    when_ts TEXT NOT NULL,
    before TEXT NOT NULL,
    after TEXT NOT NULL,
    note_vi TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prefix_locks (
    app_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    holder_token TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    PRIMARY KEY (app_id, instance_id)
);
"""


class _SqlitePrefixLock:
    """``PrefixLock`` hiện thực trên bảng ``prefix_locks``."""

    def __init__(
        self, store: SqliteStateStore, app_id: str, instance_id: str, holder_token: str
    ) -> None:
        self._store = store
        self._app_id = app_id
        self._instance_id = instance_id
        self._holder_token = holder_token
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        conn = self._store._connection
        conn.execute(
            "DELETE FROM prefix_locks WHERE app_id = ? AND instance_id = ? AND holder_token = ?",
            (self._app_id, self._instance_id, self._holder_token),
        )
        conn.commit()
        self._released = True


class SqliteStateStore:
    """Hiện thực ``namios_core.txstate.StateStore`` trên SQLite (WP5).

    ``postcheck``: hàm tùy chọn ``(Transaction) -> bool`` dùng DUY NHẤT trong
    ``recover()`` để quyết định một giao dịch dở có đủ bằng chứng thực tế để
    chuyển ``RECOVERING -> READY`` hay không. Không truyền ⇒ không bao giờ tự
    phục hồi về ``READY`` (mặc định an toàn nhất, tuân TX-001/TX-003).
    """

    def __init__(
        self,
        db_path: Path | None = None,
        postcheck: Callable[[Transaction], bool] | None = None,
    ) -> None:
        self._db_path = db_path if db_path is not None else state_db_path()
        self._postcheck = postcheck
        self._conn: sqlite3.Connection | None = None

    # -- lifecycle --------------------------------------------------------

    def open(self) -> None:
        _assert_safe_db_path(self._db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self._db_path.parent, 0o700)
        except OSError:
            pass
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.executescript(_SCHEMA)
        conn.commit()
        self._conn = conn
        try:
            os.chmod(self._db_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def _connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SqliteStateStore.open() chưa được gọi")
        return self._conn

    # -- transactions -------------------------------------------------------

    def create_transaction(self, app_id: str, instance_id: str) -> Transaction:
        tx_id = _new_id()
        now = _now_iso()
        conn = self._connection
        conn.execute(
            "INSERT INTO transactions (tx_id, app_id, instance_id, state, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (tx_id, app_id, instance_id, TxState.NEW.value, now),
        )
        conn.commit()
        self.append_journal(
            JournalEntry(
                tx_id=tx_id,
                operation_id=_new_id(),
                phase="create",
                when=now,
                before=TxState.NEW,
                after=TxState.NEW,
                note_vi="Tạo giao dịch mới",
            )
        )
        return Transaction(
            tx_id=tx_id, app_id=app_id, instance_id=instance_id, state=TxState.NEW, updated_at=now
        )

    def append_journal(self, e: JournalEntry) -> None:
        conn = self._connection
        conn.execute(
            "INSERT INTO journal (tx_id, operation_id, phase, when_ts, before, after, note_vi) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (e.tx_id, e.operation_id, e.phase, e.when, e.before.value, e.after.value, e.note_vi),
        )
        conn.commit()

    def advance(self, tx_id: str, to: TxState, operation_id: str, note_vi: str) -> Transaction:
        current = self.get(tx_id)
        if current is None:
            raise TransactionNotFoundError(
                f"Không tìm thấy giao dịch {tx_id}", details={"tx_id": tx_id}
            )
        if not validate_transition(current.state, to):
            raise StateConflictError(
                f"Chuyển trạng thái không hợp lệ: {current.state.value} -> {to.value}",
                details={"tx_id": tx_id, "from": current.state.value, "to": to.value},
            )
        now = _now_iso()
        # Ghi journal TRƯỚC khi đổi state (write-ahead, TX-001).
        self.append_journal(
            JournalEntry(
                tx_id=tx_id,
                operation_id=operation_id,
                phase="advance",
                when=now,
                before=current.state,
                after=to,
                note_vi=note_vi,
            )
        )
        conn = self._connection
        conn.execute(
            "UPDATE transactions SET state = ?, updated_at = ? WHERE tx_id = ?",
            (to.value, now, tx_id),
        )
        conn.commit()
        return Transaction(
            tx_id=tx_id,
            app_id=current.app_id,
            instance_id=current.instance_id,
            state=to,
            updated_at=now,
        )

    def get(self, tx_id: str) -> Transaction | None:
        conn = self._connection
        row = conn.execute(
            "SELECT tx_id, app_id, instance_id, state, updated_at FROM transactions "
            "WHERE tx_id = ?",
            (tx_id,),
        ).fetchone()
        if row is None:
            return None
        return Transaction(
            tx_id=row["tx_id"],
            app_id=row["app_id"],
            instance_id=row["instance_id"],
            state=TxState(row["state"]),
            updated_at=row["updated_at"],
        )

    # -- mutex per-prefix -----------------------------------------------------

    def acquire_prefix_lock(self, app_id: str, instance_id: str) -> PrefixLock:
        conn = self._connection
        holder_token = _new_id()
        now = _now_iso()
        try:
            conn.execute(
                "INSERT INTO prefix_locks (app_id, instance_id, holder_token, acquired_at) "
                "VALUES (?, ?, ?, ?)",
                (app_id, instance_id, holder_token, now),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise StateConflictError(
                f"Prefix ({app_id}, {instance_id}) đang bị giao dịch khác giữ khóa",
                details={"app_id": app_id, "instance_id": instance_id},
            ) from exc
        return _SqlitePrefixLock(self, app_id, instance_id, holder_token)

    # -- crash recovery -----------------------------------------------------

    def _force_write(
        self, tx_id: str, before: TxState, after: TxState, phase: str, note_vi: str
    ) -> None:
        """Ghi journal + cập nhật state TRỰC TIẾP, KHÔNG qua ``validate_transition``.

        CHỈ dùng trong ``recover()`` — đường thoát hiểm dành riêng cho việc đưa
        một giao dịch dở (bất kỳ trạng thái nào do crash để lại) về nhánh phục
        hồi an toàn (``FAILED -> RECOVERING -> READY|NEEDS_ATTENTION``). Luồng
        bình thường (``advance()``) KHÔNG được bỏ qua bảng chuyển.
        """

        now = _now_iso()
        self.append_journal(
            JournalEntry(
                tx_id=tx_id,
                operation_id=_new_id(),
                phase=phase,
                when=now,
                before=before,
                after=after,
                note_vi=note_vi,
            )
        )
        conn = self._connection
        conn.execute(
            "UPDATE transactions SET state = ?, updated_at = ? WHERE tx_id = ?",
            (after.value, now, tx_id),
        )
        conn.commit()

    def recover(self) -> tuple[Transaction, ...]:
        """Quét giao dịch dở sau crash, đưa về ``RECOVERING`` rồi
        ``READY`` (chỉ khi ``postcheck`` xác nhận) hoặc ``NEEDS_ATTENTION``
        (mặc định an toàn). KHÔNG BAO GIỜ tin journal cuối cùng ghi
        ``after=READY`` là đủ bằng chứng — luôn đòi ``postcheck`` thật.
        """

        conn = self._connection
        rows = conn.execute(
            "SELECT tx_id, app_id, instance_id, state, updated_at FROM transactions"
        ).fetchall()
        results: list[Transaction] = []
        for row in rows:
            state = TxState(row["state"])
            if state in _RESTING_STATES:
                continue
            tx_id = row["tx_id"]

            if state != TxState.FAILED and state != TxState.RECOVERING:
                # Giao dịch dở giữa chừng (bất kỳ trạng thái "đang chạy") →
                # buộc về FAILED trước (bước phát hiện crash), journal ghi rõ.
                self._force_write(
                    tx_id,
                    before=state,
                    after=TxState.FAILED,
                    phase="recover-detect",
                    note_vi="Phát hiện giao dịch dở sau crash; đánh dấu FAILED để phục hồi an toàn",
                )
                state = TxState.FAILED

            if state == TxState.FAILED:
                self._force_write(
                    tx_id,
                    before=TxState.FAILED,
                    after=TxState.RECOVERING,
                    phase="recover-start",
                    note_vi="Bắt đầu phục hồi giao dịch dở",
                )
                state = TxState.RECOVERING

            # state == RECOVERING tại đây: quyết định READY hay NEEDS_ATTENTION
            # dựa HOÀN TOÀN vào postcheck thật — không dựa vào journal cũ.
            current = self.get(tx_id)
            assert current is not None
            verified = self._postcheck(current) if self._postcheck is not None else False
            final = TxState.READY if verified else TxState.NEEDS_ATTENTION
            note = (
                "Kiểm tra thực tế xác nhận hoàn tất, phục hồi về READY"
                if verified
                else (
                    "Không có bằng chứng xác nhận hoàn tất; "
                    "chuyển NEEDS_ATTENTION để người dùng xử lý"
                )
            )
            self._force_write(
                tx_id, before=TxState.RECOVERING, after=final, phase="recover-finish", note_vi=note
            )
            final_tx = self.get(tx_id)
            assert final_tx is not None
            results.append(final_tx)
        return tuple(results)
