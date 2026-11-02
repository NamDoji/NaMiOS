"""Security primitives (WP8 hiện thực — SEC-002/009, SUP-002). Xem
M1-INTERFACES.md §7.8.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import IO, Any, Protocol


@dataclass(frozen=True)
class CompletedProc:
    """Kết quả một tiến trình chạy qua ``run_argv`` (tương tự
    ``subprocess.CompletedProcess`` nhưng bất biến + chỉ scalar/bytes)."""

    argv: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes


class SafePath(Protocol):
    def resolve_within(
        self, base: str, candidate: str
    ) -> str: ...  # FD-based; chặn symlink/hardlink/traversal/TOCTOU; E_PATH_UNSAFE

    def open_within(self, base: str, candidate: str, mode: str) -> IO[bytes]: ...  # O_NOFOLLOW


class SafeExec(Protocol):
    def run_argv(
        self,
        argv: Sequence[str],
        *,
        timeout: float,
        env: Mapping[str, str] | None = None,
    ) -> CompletedProc: ...

    # KHÔNG shell=True, KHÔNG nối chuỗi; argv[0] phải là path tuyệt đối đã allowlist


class Redactor(Protocol):
    # mật khẩu/token/OTP/QR/đường dẫn tài liệu/IP nội bộ/username
    def redact_text(self, s: str) -> str: ...

    def redact_obj(self, o: Mapping[str, Any]) -> Mapping[str, Any]: ...
