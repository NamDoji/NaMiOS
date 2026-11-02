"""Hàm digest dùng nội bộ cho planner.

WP6 phụ thuộc ``namios_security`` (WP8, §7.8) cho đọc file an toàn, nhưng
module đó chưa có hiện thực trong repo tại thời điểm viết. Để KHÔNG chặn
tiến độ và KHÔNG đụng thư mục của WP khác, ``sha256_file`` tự hiện thực một
lớp mở file tối thiểu đạt bất biến an toàn cơ bản (FD-based, ``O_NOFOLLOW``
chống theo symlink ở thành phần cuối, chỉ đọc file thường). Khi
``namios_security.SafePath`` phát hành, planner nên chuyển qua gọi nó thay
cho hàm này (TODO ghi rõ, không phải business logic ẩn).

KHÔNG dùng ``shell=True``/``eval``/nối chuỗi path (FACT CLAUDE.md/SEC-002).
"""

from __future__ import annotations

import hashlib
import os
import stat as stat_module

__all__ = ["DigestError", "sha256_file", "sha256_text", "file_size_bytes"]

_READ_CHUNK = 1024 * 1024  # 1 MiB


class DigestError(Exception):
    """Không tính được digest của ``path`` (không tồn tại, không phải file
    thường, hoặc là symlink ở thành phần cuối)."""

    def __init__(self, path: str, reason_vi: str) -> None:
        super().__init__(f"Không đọc được '{path}' để tính digest: {reason_vi}")
        self.path = path
        self.reason_vi = reason_vi


def _open_regular_file_no_follow(path: str) -> int:
    if not path or not os.path.isabs(path):
        raise DigestError(path, "phải là đường dẫn tuyệt đối")

    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise DigestError(path, exc.strerror or str(exc)) from exc

    try:
        st = os.fstat(fd)
    except OSError as exc:
        os.close(fd)
        raise DigestError(path, exc.strerror or str(exc)) from exc

    if not stat_module.S_ISREG(st.st_mode):
        os.close(fd)
        raise DigestError(path, "không phải file thường (regular file)")

    return fd


def sha256_file(path: str) -> str:
    """Tính sha256 nội dung file tại ``path``. Dùng FD mở một lần, đọc toàn
    bộ nội dung từ FD đó (không `stat` rồi `open` lại) để giảm cửa sổ
    TOCTOU."""

    fd = _open_regular_file_no_follow(path)
    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, "rb") as fh:
            while True:
                chunk = fh.read(_READ_CHUNK)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise DigestError(path, exc.strerror or str(exc)) from exc
    return digest.hexdigest()


def file_size_bytes(path: str) -> int:
    fd = _open_regular_file_no_follow(path)
    try:
        return os.fstat(fd).st_size
    finally:
        os.close(fd)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
