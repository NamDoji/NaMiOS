"""Lỗi ổn định của WP5 (txstate) — bọc ``namios_core.errors.ErrorCode``.

Các lỗi này là implementation detail của ``namios_txstate`` (caller/WP3 bắt
``TxStateError`` và dùng ``.code``/``namios_core.errors.exit_code_for`` để suy
ra exit code — KHÔNG đổi ``ErrorCode`` tùy tiện).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from namios_core.errors import ErrorCode


class TxStateError(Exception):
    """Lỗi nền cho mọi exception do ``namios_txstate`` phát ra."""

    def __init__(
        self,
        code: ErrorCode,
        message_vi: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message_vi)
        self.code = code
        self.message_vi = message_vi
        self.details = details


class StateConflictError(TxStateError):
    """Chuyển trạng thái bất hợp lệ, hoặc mutex/khóa prefix đang bận
    (``E_STATE_CONFLICT`` → exit 6)."""

    def __init__(self, message_vi: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.E_STATE_CONFLICT, message_vi, details)


class TransactionNotFoundError(TxStateError):
    """``tx_id`` không tồn tại trong store (coi là input sai → E_INPUT_SCHEMA)."""

    def __init__(self, message_vi: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.E_INPUT_SCHEMA, message_vi, details)


class PathUnsafeError(TxStateError):
    """Đường dẫn state.sqlite3/thư mục chứa nó vi phạm chính sách an toàn
    (symlink lạ, không phải file thường, ...) → ``E_PATH_UNSAFE`` (exit 2)."""

    def __init__(self, message_vi: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.E_PATH_UNSAFE, message_vi, details)
