"""Builders tiện lợi cho ``Envelope`` ok/error — WP3.

KHÔNG tự chế mã lỗi mới: mọi ``code`` PHẢI là giá trị của
``namios_core.errors.ErrorCode`` (nguồn ổn định của WP1).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from namios_core.envelope import API_VERSION, Envelope, ErrorBody
from namios_core.errors import ErrorCode


def ok_envelope(
    operation_id: str,
    data: Mapping[str, Any] | None,
    warnings: Sequence[str] = (),
) -> Envelope:
    """Envelope ``status="ok"`` (FACT CLI-001: ``error`` phải là ``None``)."""

    return Envelope(
        api_version=API_VERSION,
        operation_id=operation_id,
        status="ok",
        data=data,
        warnings=tuple(warnings),
        error=None,
    )


def error_envelope(
    operation_id: str,
    code: ErrorCode,
    message_vi: str,
    details: Mapping[str, Any] | None = None,
    warnings: Sequence[str] = (),
) -> Envelope:
    """Envelope ``status="error"`` (FACT CLI-001: ``data`` phải là ``None``).

    ``details`` PHẢI đã qua ``Redactor`` (WP8) trước khi truyền vào đây nếu
    chứa bất kỳ dữ liệu động/đầu vào người dùng — module này KHÔNG tự redact.
    """

    return Envelope(
        api_version=API_VERSION,
        operation_id=operation_id,
        status="error",
        data=None,
        warnings=tuple(warnings),
        error=ErrorBody(code=code.value, message_vi=message_vi, details=details),
    )
