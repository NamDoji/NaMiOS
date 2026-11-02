"""State machine giao dịch (TX-001) + Transaction State Store API (§7.3).

Nguồn sự thật THI HÀNH bảng chuyển là WP5 (``namios_txstate``); module này chỉ
khai báo enum/bảng hợp lệ/Protocol dùng chung — các WP khác chỉ đọc.
Xem M1-INTERFACES.md §4, §7.3.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class TxState(str, Enum):
    """Trạng thái giao dịch cài đặt/gỡ ứng dụng."""

    NEW = "NEW"
    VALIDATED = "VALIDATED"
    ACQUIRING = "ACQUIRING"
    STAGING = "STAGING"
    INSTALLING = "INSTALLING"
    VERIFYING = "VERIFYING"
    READY = "READY"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    REMOVING = "REMOVING"
    REMOVED = "REMOVED"


#: Bảng chuyển hợp lệ (DESIGN, FACT nội dung §4). Trạng thái không có trong
#: khóa (ví dụ CANCELLED/REMOVED) là terminal trong phạm vi giao dịch đó.
VALID_TRANSITIONS: Mapping[TxState, frozenset[TxState]] = {
    TxState.NEW: frozenset({TxState.VALIDATED, TxState.FAILED, TxState.CANCELLING}),
    TxState.VALIDATED: frozenset({TxState.ACQUIRING, TxState.FAILED, TxState.CANCELLING}),
    TxState.ACQUIRING: frozenset({TxState.STAGING, TxState.FAILED, TxState.CANCELLING}),
    TxState.STAGING: frozenset({TxState.INSTALLING, TxState.FAILED, TxState.CANCELLING}),
    TxState.INSTALLING: frozenset({TxState.VERIFYING, TxState.FAILED, TxState.CANCELLING}),
    TxState.VERIFYING: frozenset({TxState.READY, TxState.FAILED, TxState.CANCELLING}),
    TxState.CANCELLING: frozenset({TxState.CANCELLED, TxState.NEEDS_ATTENTION}),
    TxState.FAILED: frozenset({TxState.RECOVERING}),
    TxState.RECOVERING: frozenset({TxState.READY, TxState.NEEDS_ATTENTION}),
    TxState.READY: frozenset({TxState.REMOVING}),
    TxState.REMOVING: frozenset({TxState.REMOVED, TxState.NEEDS_ATTENTION}),
    TxState.NEEDS_ATTENTION: frozenset({TxState.RECOVERING, TxState.REMOVING}),
    TxState.CANCELLED: frozenset(),
    TxState.REMOVED: frozenset(),
}


def validate_transition(from_state: TxState, to_state: TxState) -> bool:
    """``True`` nếu chuyển ``from_state`` → ``to_state`` hợp lệ theo bảng §4.

    Bất biến TX-001: KHÔNG được đánh dấu ``READY`` trừ khi đi qua ``VERIFYING``
    — bảng trên đã mã hoá điều này (không có cạnh nào khác dẫn tới ``READY``).
    """

    return to_state in VALID_TRANSITIONS.get(from_state, frozenset())


@dataclass(frozen=True)
class Transaction:
    """Một giao dịch cài/gỡ ứng dụng tại một thời điểm."""

    tx_id: str
    app_id: str
    instance_id: str
    state: TxState
    updated_at: str


@dataclass(frozen=True)
class JournalEntry:
    """Một dòng journal ghi TRƯỚC khi đổi trạng thái (TX-001)."""

    tx_id: str
    operation_id: str
    phase: str
    when: str
    before: TxState
    after: TxState
    note_vi: str


class PrefixLock(Protocol):
    """Mutex giữ trong lúc giao dịch chạy trên một (app_id, instance_id)."""

    def release(self) -> None: ...


class StateStore(Protocol):
    """API transaction state store trên ``state.sqlite3`` (WP5 hiện thực)."""

    def open(self) -> None: ...  # tạo/migrate schema state.sqlite3

    def create_transaction(self, app_id: str, instance_id: str) -> Transaction: ...  # NEW

    def append_journal(self, e: JournalEntry) -> None: ...  # ghi TRƯỚC khi đổi state

    def advance(
        self, tx_id: str, to: TxState, operation_id: str, note_vi: str
    ) -> Transaction: ...  # validate transition; E_STATE_CONFLICT nếu sai

    def get(self, tx_id: str) -> Transaction | None: ...

    def acquire_prefix_lock(
        self, app_id: str, instance_id: str
    ) -> PrefixLock: ...  # mutex; E_STATE_CONFLICT nếu bận

    # tx dở sau crash → RECOVERING/NEEDS_ATTENTION
    def recover(self) -> tuple[Transaction, ...]: ...
