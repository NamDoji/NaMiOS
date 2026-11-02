"""JSON envelope CLI (CLI-001). Chỉ kiểu + hằng số — WP1.

Hiện thực ghi JSON thật (``emit_json``/``new_operation_id``) thuộc WP3
(``namios_cli``); module này chỉ định kiểu dữ liệu để mọi WP dùng chung.
Xem M1-INTERFACES.md §1.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

#: Phiên bản envelope cố định cho M1 (DESIGN).
API_VERSION: Literal["1.0"] = "1.0"


@dataclass(frozen=True)
class ErrorBody:
    """Thân lỗi khi ``Envelope.status == "error"``.

    ``code`` là một giá trị ổn định của ``namios_core.errors.ErrorCode``.
    ``details`` KHÔNG được chứa secret/argv thô/đường dẫn tài liệu người dùng —
    PHẢI đi qua ``namios_security.Redactor`` trước khi gán vào đây.
    """

    code: str
    message_vi: str
    details: Mapping[str, Any] | None


@dataclass(frozen=True)
class Envelope:
    """Đối tượng JSON envelope duy nhất in ra stdout cho mỗi lệnh ``--json``.

    Bất biến (FACT CLI-001):
      - ``status == "ok"``  ⇒ ``error is None``.
      - ``status == "error"`` ⇒ ``data is None`` và ``error is not None``.
    """

    api_version: str
    operation_id: str
    status: Literal["ok", "error"]
    data: Mapping[str, Any] | None
    warnings: tuple[str, ...]
    error: ErrorBody | None
