"""Exception hierarchy WP8 — ánh xạ ổn định tới ``namios_core.errors.ErrorCode``.

Mọi lỗi an toàn (path/exec) ném từ ``namios_security`` PHẢI là một trong các
lớp dưới đây, mang theo ``code`` để caller (CLI/WP khác) map thẳng sang
``ErrorBody.code`` / exit code qua ``namios_core.errors.exit_code_for``.
"""

from __future__ import annotations

from dataclasses import dataclass

from namios_core.errors import ErrorCode

__all__ = ["PathUnsafeError", "ExecPolicyError"]


@dataclass
class PathUnsafeError(Exception):
    """Đường dẫn vi phạm chính sách an toàn (``E_PATH_UNSAFE``).

    Ném khi: traversal (``..``), path tuyệt đối trong candidate, symlink
    trung gian hoặc symlink ở thành phần cuối, vượt ranh giới ``base``,
    băng qua mount point, hoặc hardlink nguy hiểm khi ghi.
    """

    path: str
    reason_vi: str
    code: ErrorCode = ErrorCode.E_PATH_UNSAFE

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Đường dẫn không an toàn '{self.path}': {self.reason_vi}"


@dataclass
class ExecPolicyError(Exception):
    """Vi phạm chính sách thực thi argv-only (ánh xạ ``E_PERMISSION_DENIED``).

    Ném khi: ``argv`` rỗng, phần tử không phải ``str``, ``argv[0]`` không
    phải đường dẫn tuyệt đối, hoặc file đích không tồn tại/không thực thi
    được.
    """

    reason_vi: str
    code: ErrorCode = ErrorCode.E_PERMISSION_DENIED

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Vi phạm chính sách thực thi: {self.reason_vi}"
