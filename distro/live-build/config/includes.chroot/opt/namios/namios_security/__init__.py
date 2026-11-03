"""namios_security — WP8: safe path/FD, argv-only exec, redaction.

Nền an toàn dùng chung cho các WP khác (M1-INTERFACES §7.8). Mọi WP khác chỉ
import từ đây (KHÔNG tự chế lại path/exec an toàn trong module riêng)."""

from __future__ import annotations

from namios_security._errors import ExecPolicyError, PathUnsafeError
from namios_security.redactor import RedactorImpl, redact_obj, redact_text
from namios_security.safe_exec import ArgvSafeExec, run_argv
from namios_security.safe_path import SafePathImpl, open_within, resolve_within

__all__ = [
    "PathUnsafeError",
    "ExecPolicyError",
    "SafePathImpl",
    "resolve_within",
    "open_within",
    "ArgvSafeExec",
    "run_argv",
    "RedactorImpl",
    "redact_text",
    "redact_obj",
]
