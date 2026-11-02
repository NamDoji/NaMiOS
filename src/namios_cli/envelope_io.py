"""JSON envelope writer + exit-code mapper (CLI-001/CLI-003) — WP3.

``namios_core.envelope`` chỉ định kiểu; module này hiện thực việc GHI THẬT
một dòng JSON ra stdout và tạo ``operation_id``. Xem M1-INTERFACES.md §1.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import IO, Any

from namios_core.envelope import Envelope
from namios_core.errors import ErrorCode, exit_code_for
from namios_core.exitcodes import ExitCode


def new_operation_id() -> str:
    """``uuid4`` hex — 1 lần/lệnh, dùng để truy vết journal (FACT CLI-001)."""

    return uuid.uuid4().hex


def _envelope_to_jsonable(env: Envelope) -> Mapping[str, Any]:
    """Chuyển ``Envelope`` thành dict JSON-serializable mà KHÔNG trộn log.

    ``data``/``error.details`` là ``Mapping`` tự do do caller cấp — PHẢI đã
    qua ``Redactor`` (WP8) trước khi tới đây; module này không tự redact.
    """

    error_obj: Mapping[str, Any] | None
    if env.error is None:
        error_obj = None
    else:
        error_obj = {
            "code": env.error.code,
            "message_vi": env.error.message_vi,
            "details": env.error.details,
        }

    return {
        "api_version": env.api_version,
        "operation_id": env.operation_id,
        "status": env.status,
        "data": env.data,
        "warnings": list(env.warnings),
        "error": error_obj,
    }


def emit_json(env: Envelope, stdout: IO[str]) -> None:
    """Ghi ĐÚNG MỘT đối tượng JSON + ``\\n`` ra ``stdout`` (FACT CLI-001).

    KHÔNG ghi log/tiến trình/cảnh báo người-đọc vào đây — caller dùng
    ``stderr`` riêng cho những thứ đó. ``ensure_ascii=False`` để tiếng Việt
    có dấu hiển thị nguyên dạng, không escape \\uXXXX.
    """

    payload = _envelope_to_jsonable(env)
    stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=False))
    stdout.write("\n")
    stdout.flush()


def envelope_exit_code(env: Envelope) -> ExitCode:
    """Suy ra ``ExitCode`` từ một ``Envelope`` đã tạo xong (FACT CLI-003).

    ``status == "ok"`` → luôn ``ExitCode.OK``. ``status == "error"`` → tra
    bảng ổn định ``ErrorCode -> ExitCode`` của WP1 (không tự chế mapping).
    """

    if env.status == "ok":
        return ExitCode.OK
    assert env.error is not None, "envelope lỗi phải có error body"
    return exit_code_for(ErrorCode(env.error.code))
