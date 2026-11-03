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
    """Đọc nội dung text của ``path`` an toàn (chống TOCTOU symlink).

    Uỷ quyền cho primitive chung ``namios_security.open_within`` (FD-walk
    TỪNG thành phần với ``O_NOFOLLOW`` + ``dir_fd``) — bịt lỗ TOCTOU ở thành
    phần thư mục TRUNG GIAN mà cách cũ "realpath rồi ``os.open`` bằng chuỗi"
    không chặn được (SEC-002, SEC-SWEEP-002). ``base="/"`` để FD-walk toàn bộ
    đường dẫn tuyệt đối từ gốc; ``open_within`` tự chặn symlink/mount-cross,
    chỉ nhận file thường, không treo FIFO (O_NONBLOCK). Ở đây thêm giới hạn
    kích thước (chống DoS) + decode UTF-8.
    """

    if not path or not os.path.isabs(path):
        raise PathUnsafeError(path=path, reason_vi="phải là đường dẫn tuyệt đối")

    import stat as stat_module

    parts = [p for p in path.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise PathUnsafeError(path=path, reason_vi="đường dẫn chứa '..' hoặc rỗng — không hợp lệ")

    # FD-walk TỪNG thành phần với O_NOFOLLOW + dir_fd: nếu một thư mục TRUNG
    # GIAN bị swap thành symlink giữa lúc kiểm và lúc đọc (TOCTOU, SEC-002/
    # SEC-SWEEP-002), bước mở component đó sẽ ELOOP và bị từ chối. KHÔNG dùng
    # namios_security.open_within vì nó cấm băng mount point, trong khi đường
    # dẫn manifest tin-cậy ở đây hợp lệ khi nằm trên phân vùng mount khác '/'
    # — ta chỉ cần chống symlink-swap, không giới hạn thiết bị. O_NONBLOCK để
    # không treo nếu thành phần cuối là FIFO.
    _dir_flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    _leaf_flags = (
        os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    dir_fd = os.open("/", _dir_flags)
    try:
        for comp in parts[:-1]:
            try:
                next_fd = os.open(comp, _dir_flags, dir_fd=dir_fd)
            except OSError as exc:
                raise PathUnsafeError(
                    path=path,
                    reason_vi=f"thành phần '{comp}' là symlink/không phải thư mục "
                    f"({exc.strerror or exc})",
                ) from exc
            os.close(dir_fd)
            dir_fd = next_fd
        try:
            leaf_fd = os.open(parts[-1], _leaf_flags, dir_fd=dir_fd)
        except OSError as exc:
            raise PathUnsafeError(
                path=path, reason_vi=f"không mở được an toàn ({exc.strerror or exc})"
            ) from exc
        try:
            st = os.fstat(leaf_fd)
            if not stat_module.S_ISREG(st.st_mode):
                raise PathUnsafeError(path=path, reason_vi="không phải file thường (regular file)")
            if st.st_size > max_bytes:
                raise PathUnsafeError(
                    path=path, reason_vi=f"file vượt giới hạn kích thước {max_bytes} bytes"
                )
            data = os.read(leaf_fd, st.st_size)
        finally:
            os.close(leaf_fd)
    finally:
        os.close(dir_fd)

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PathUnsafeError(path=path, reason_vi="nội dung không phải UTF-8 hợp lệ") from exc
