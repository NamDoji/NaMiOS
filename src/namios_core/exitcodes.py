"""Bảng exit code 0–9 (CLI-003) — FACT. Xem M1-INTERFACES.md §2.

Mã 1 CỐ Ý không dùng (dành cho lỗi runtime ngoài hợp đồng của interpreter).
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Exit code chuẩn cho mọi lệnh CLI của NaMiOS M1."""

    OK = 0
    INPUT = 2
    DEPENDENCY = 3
    NETWORK = 4
    PERMISSION = 5
    CONFLICT = 6
    CANCELLED = 7
    VERIFY = 8
    INTERNAL = 9
