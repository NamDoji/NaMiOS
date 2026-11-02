"""Đọc file manifest an toàn (interim — chờ ``namios_security`` của WP8).

WP2 phụ thuộc ``SafePath`` (§7.8) nhưng tại thời điểm viết, ``namios_security``
(WP8) chưa có hiện thực trong repo. Để KHÔNG chặn tiến độ và KHÔNG đụng vào
thư mục của WP khác, module này tự hiện thực một lớp đọc file tối thiểu đạt
các bất biến bắt buộc (FD-based, ``O_NOFOLLOW`` chống symlink ở thành phần
cuối, chặn traversal/parent-symlink bằng so khớp ``realpath``, giới hạn kích
thước để chống DoS). Khi WP8 phát hành ``namios_security.SafePath`` thật,
``namios_manifest`` nên chuyển sang gọi nó thay cho module này (TODO ghi rõ
ràng, KHÔNG phải business logic ẩn).

KHÔNG dùng ``shell=True``/``eval``/nối chuỗi path không kiểm tra (FACT
CLAUDE.md/SEC-002).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

__all__ = ["PathUnsafeError", "read_text_safe"]

#: Giới hạn kích thước file manifest đọc được — chống DoS bằng file khổng lồ.
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024  # 2 MiB


@dataclass(frozen=True)
class PathUnsafeError(Exception):
    """Đường dẫn vi phạm chính sách an toàn (ánh xạ ``E_PATH_UNSAFE``)."""

    path: str
    reason_vi: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Đường dẫn không an toàn '{self.path}': {self.reason_vi}"


def read_text_safe(path: str, *, max_bytes: int = _MAX_MANIFEST_BYTES) -> str:
    """Đọc nội dung text của ``path`` với các bất biến an toàn tối thiểu.

    - Không theo symlink ở thành phần cuối (``O_NOFOLLOW``).
    - Chặn mọi symlink trung gian trên đường dẫn bằng so khớp
      ``os.path.realpath`` với bản thân tuyệt đối-hóa KHÔNG resolve symlink.
    - Chỉ đọc file thường (regular file), không device/FIFO/socket.
    - Giới hạn kích thước đọc để chống DoS.
    - Mở trước, kiểm tra sau qua ``fstat`` trên FD đã mở (giảm cửa sổ TOCTOU
      so với stat-rồi-open).
    """

    if not path or not os.path.isabs(path):
        raise PathUnsafeError(path=path, reason_vi="phải là đường dẫn tuyệt đối")

    real = os.path.realpath(path, strict=False)
    abs_no_follow = os.path.abspath(path)
    if real != abs_no_follow:
        raise PathUnsafeError(
            path=path,
            reason_vi="đường dẫn chứa symlink trung gian hoặc thành phần '..' dẫn ra ngoài",
        )

    open_flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)  # tránh treo nếu path là FIFO
    )
    try:
        fd = os.open(path, open_flags)
    except OSError as exc:
        raise PathUnsafeError(
            path=path, reason_vi=f"không mở được an toàn ({exc.strerror or exc})"
        ) from exc

    try:
        st = os.fstat(fd)
        import stat as stat_module

        if not stat_module.S_ISREG(st.st_mode):
            raise PathUnsafeError(path=path, reason_vi="không phải file thường (regular file)")
        if st.st_size > max_bytes:
            raise PathUnsafeError(
                path=path, reason_vi=f"file vượt giới hạn kích thước {max_bytes} bytes"
            )
        data = os.read(fd, st.st_size)
    finally:
        os.close(fd)

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PathUnsafeError(path=path, reason_vi="nội dung không phải UTF-8 hợp lệ") from exc
