"""Đọc file PE/sidecar JSON an toàn cho ``namios_dotnet`` (NET-001).

Dùng lại nền an toàn dùng chung ``namios_security`` (WP8 — FD-based,
``O_NOFOLLOW``, chặn symlink/traversal/mount; KHÔNG tự chế lại FD-walk ở
đây, đúng quy tắc chống giẫm chân M1-INTERFACES §0). Lớp này CHỈ thêm: giới
hạn kích thước đọc (chống DoS từ file đầu vào không tin cậy) + helper tìm
sidecar "đi kèm" (cùng thư mục) cho ``.runtimeconfig.json``/``.deps.json``.

Input là KHÔNG tin cậy (NET-001): không bao giờ đọc vượt giới hạn, không bao
giờ coi "tồn tại" là "an toàn" — mọi lượt đọc thật đều đi qua
``namios_security.open_within`` (lại xác thực FD-based từ đầu).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from namios_core.errors import ErrorCode
from namios_dotnet._errors import DotnetAnalysisError
from namios_security import PathUnsafeError, open_within

__all__ = [
    "DEFAULT_MAX_PE_BYTES",
    "DEFAULT_MAX_SIDECAR_BYTES",
    "ReadResult",
    "read_bytes_capped",
    "read_sidecar_if_present",
]

#: Giới hạn đọc file PE — đủ cho header/section table/CLR header của hầu hết
#: app thật; chặn DoS bằng file khổng lồ (NET-001).
DEFAULT_MAX_PE_BYTES = 8 * 1024 * 1024  # 8 MiB

#: Giới hạn đọc sidecar JSON (``.runtimeconfig.json``/``.deps.json``).
DEFAULT_MAX_SIDECAR_BYTES = 1 * 1024 * 1024  # 1 MiB


@dataclass(frozen=True)
class ReadResult:
    """Kết quả đọc có giới hạn — ``truncated=True`` nghĩa là file còn dữ liệu
    phía sau vị trí giới hạn mà ta CHỦ ĐỘNG không đọc tiếp (không phải lỗi)."""

    data: bytes
    truncated: bool


def _split_base_and_name(path: str) -> tuple[str, str]:
    if not path or not os.path.isabs(path):
        raise DotnetAnalysisError(
            code=ErrorCode.E_PATH_UNSAFE, reason_vi="đường dẫn phải tuyệt đối"
        )
    base = os.path.dirname(path)
    name = os.path.basename(path)
    if not base or not name:
        raise DotnetAnalysisError(
            code=ErrorCode.E_PATH_UNSAFE,
            reason_vi="đường dẫn thiếu thư mục cha hoặc tên file hợp lệ",
        )
    return base, name


def read_bytes_capped(path: str, *, max_bytes: int) -> ReadResult:
    """Đọc tối đa ``max_bytes`` của file thường tại ``path`` một cách an
    toàn. Ném ``DotnetAnalysisError`` nếu không mở được an toàn (symlink/
    traversal/không tồn tại/không phải file thường/...)."""

    if max_bytes <= 0:
        raise DotnetAnalysisError(code=ErrorCode.E_INTERNAL, reason_vi="max_bytes phải dương")
    base, name = _split_base_and_name(path)
    try:
        fh = open_within(base, name, "rb")
    except PathUnsafeError as exc:
        raise DotnetAnalysisError(code=exc.code, reason_vi=exc.reason_vi) from exc
    try:
        # Đọc nhiều hơn 1 byte so với giới hạn để phát hiện "còn dữ liệu
        # phía sau" mà không cần tin số liệu stat() (vốn có thể đổi giữa lúc
        # stat và lúc đọc — TOCTOU); ta chỉ dựa vào SỐ BYTE THẬT đã đọc được.
        data = fh.read(max_bytes + 1)
    finally:
        fh.close()
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]
    return ReadResult(data=data, truncated=truncated)


def read_sidecar_if_present(
    pe_path: str, suffix: str, *, max_bytes: int = DEFAULT_MAX_SIDECAR_BYTES
) -> tuple[str, ReadResult] | None:
    """Tìm + đọc sidecar "đi kèm" ``pe_path`` CÙNG THƯ MỤC (vd đổi
    ``MyApp.dll`` → ``MyApp.runtimeconfig.json`` khi ``suffix`` là
    ``".runtimeconfig.json"``). Trả ``None`` nếu không có sidecar — KHÔNG
    phải lỗi (sidecar là tuỳ chọn).

    Bước kiểm tra tồn tại (``os.path.lexists``) chỉ là gợi ý UX để tránh thử
    mở không cần thiết; nó KHÔNG phải biên an toàn — biên an toàn thật là
    lượt đọc thật qua ``open_within`` ngay sau đó (tự xác thực lại từ đầu,
    không tin kết quả lexists)."""

    if not pe_path or not os.path.isabs(pe_path):
        raise DotnetAnalysisError(
            code=ErrorCode.E_PATH_UNSAFE, reason_vi="đường dẫn PE phải tuyệt đối"
        )
    stem, _dot_ext = os.path.splitext(pe_path)
    sidecar_path = stem + suffix
    if not os.path.lexists(sidecar_path):
        return None
    result = read_bytes_capped(sidecar_path, max_bytes=max_bytes)
    return sidecar_path, result
