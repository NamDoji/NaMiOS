"""Lỗi ổn định của WP7 (``namios_helper``) — bọc ``namios_core.errors.ErrorCode``.

Caller (D-Bus adaptor / CLI) bắt ``HelperError`` và dùng ``.code`` +
``namios_core.errors.exit_code_for`` để suy ra exit code — KHÔNG đổi
``ErrorCode`` tùy tiện (M1-INTERFACES.md §3).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from namios_core.errors import ErrorCode


class HelperError(Exception):
    """Lỗi nền cho mọi exception do ``namios_helper`` phát ra."""

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


class PermissionDeniedError(HelperError):
    """Caller không hợp lệ HOẶC Polkit từ chối action
    (``E_PERMISSION_DENIED`` → exit 5). KHÔNG BAO GIỜ thay đổi hệ thống khi
    lỗi này được ném."""

    def __init__(self, message_vi: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.E_PERMISSION_DENIED, message_vi, details)


class UnknownAllowlistKeyError(HelperError):
    """``allowlist_key`` không trỏ tới plan đã duyệt sẵn nào — caller KHÔNG
    được truyền tên package/repo/key tự do (``E_INPUT_SCHEMA`` → exit 2,
    CLI-004)."""

    def __init__(self, message_vi: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.E_INPUT_SCHEMA, message_vi, details)


class StalePlanError(HelperError):
    """``ApplyApprovedPackagePlan`` nhận một ``ApprovedPackagePlan`` không
    khớp (digest sai/không tồn tại trong registry nội bộ) —
    (``E_PLAN_STALE`` → exit 6)."""

    def __init__(self, message_vi: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(ErrorCode.E_PLAN_STALE, message_vi, details)
