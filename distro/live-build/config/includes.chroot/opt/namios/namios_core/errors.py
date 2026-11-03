"""Mã lỗi ổn định (stable error codes) — DESIGN. Xem M1-INTERFACES.md §3.

Enum chuỗi, bất biến trên các phiên bản M1; dùng trong ``ErrorBody.code``.
Map 1→1 tới ``namios_core.exitcodes.ExitCode``.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from namios_core.exitcodes import ExitCode


class ErrorCode(str, Enum):
    """Mã lỗi ổn định dùng xuyên suốt M1 (KHÔNG đổi giá trị chuỗi sau khi phát hành)."""

    E_INPUT_SCHEMA = "E_INPUT_SCHEMA"
    E_INPUT_UNKNOWN_KEY = "E_INPUT_UNKNOWN_KEY"
    E_SEMANTIC_TBD = "E_SEMANTIC_TBD"
    E_SEMANTIC_RECIPE = "E_SEMANTIC_RECIPE"
    E_SEMANTIC_DEPENDENCY = "E_SEMANTIC_DEPENDENCY"
    E_ENTITLEMENT_REQUIRED = "E_ENTITLEMENT_REQUIRED"
    E_HASH_MISMATCH = "E_HASH_MISMATCH"
    E_SOURCE_POLICY = "E_SOURCE_POLICY"
    E_PERMISSION_DENIED = "E_PERMISSION_DENIED"
    E_STATE_CONFLICT = "E_STATE_CONFLICT"
    E_PLAN_STALE = "E_PLAN_STALE"
    E_CANCELLED = "E_CANCELLED"
    E_POSTCHECK_FAILED = "E_POSTCHECK_FAILED"
    E_PATH_UNSAFE = "E_PATH_UNSAFE"
    E_REVOKED = "E_REVOKED"
    E_EVIDENCE_MISSING = "E_EVIDENCE_MISSING"
    E_INTERNAL = "E_INTERNAL"


#: Ánh xạ ổn định ErrorCode → ExitCode (FACT M1-INTERFACES §3). Mọi WP map lỗi
#: của mình về một trong các ErrorCode này rồi dùng bảng này để suy ra exit code.
ERROR_CODE_EXIT_MAP: Mapping[ErrorCode, ExitCode] = {
    ErrorCode.E_INPUT_SCHEMA: ExitCode.INPUT,
    ErrorCode.E_INPUT_UNKNOWN_KEY: ExitCode.INPUT,
    ErrorCode.E_SEMANTIC_TBD: ExitCode.INPUT,
    ErrorCode.E_SEMANTIC_RECIPE: ExitCode.INPUT,
    ErrorCode.E_SEMANTIC_DEPENDENCY: ExitCode.DEPENDENCY,
    ErrorCode.E_ENTITLEMENT_REQUIRED: ExitCode.DEPENDENCY,
    ErrorCode.E_HASH_MISMATCH: ExitCode.NETWORK,
    ErrorCode.E_SOURCE_POLICY: ExitCode.NETWORK,
    ErrorCode.E_PERMISSION_DENIED: ExitCode.PERMISSION,
    ErrorCode.E_STATE_CONFLICT: ExitCode.CONFLICT,
    ErrorCode.E_PLAN_STALE: ExitCode.CONFLICT,
    ErrorCode.E_CANCELLED: ExitCode.CANCELLED,
    ErrorCode.E_POSTCHECK_FAILED: ExitCode.VERIFY,
    ErrorCode.E_PATH_UNSAFE: ExitCode.INPUT,
    ErrorCode.E_REVOKED: ExitCode.INPUT,
    ErrorCode.E_EVIDENCE_MISSING: ExitCode.INPUT,
    ErrorCode.E_INTERNAL: ExitCode.INTERNAL,
}


def exit_code_for(code: ErrorCode) -> ExitCode:
    """Trả ``ExitCode`` tương ứng một ``ErrorCode`` theo bảng ổn định §3."""

    return ERROR_CODE_EXIT_MAP[code]
