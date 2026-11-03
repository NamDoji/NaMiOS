"""Safe path resolution + open — hiện thực ``namios_core.security_types.SafePath``.

FD-based (``openat``-style qua ``dir_fd``), chặn:

- traversal (``..``) và candidate tuyệt đối.
- symlink trung gian HOẶC ở thành phần cuối (``O_NOFOLLOW`` tại MỌI bước,
  không phải chỉ bước cuối — khác với so-sánh ``realpath`` đơn thuần vốn có
  cửa sổ TOCTOU giữa lúc stat và lúc open).
- băng qua mount point (so khớp ``st_dev`` với ``base`` ở mọi bước).
- hardlink nguy hiểm khi mở để ghi (``st_nlink > 1`` trên leaf đã tồn tại).

TOCTOU: việc đi từng thành phần bằng ``dir_fd`` + ``O_NOFOLLOW`` nghĩa là
không có khoảng hở "stat rồi open lại theo chuỗi" cho walk — mỗi bước mở
atomic ngay trên thư mục cha đã pin bằng FD trước đó; nếu kẻ tấn công đổi
một symlink trung gian GIỮA các bước, bước mở kế tiếp sẽ thất bại với
``ELOOP``/``ENOTDIR`` thay vì âm thầm theo link mới.
"""

from __future__ import annotations

import os
import stat as stat_module
from typing import IO

from namios_security._errors import PathUnsafeError

__all__ = ["SafePathImpl", "resolve_within", "open_within"]

_OPEN_FLAGS_BY_MODE: dict[str, tuple[int, bool]] = {
    # mode -> (flags bổ sung so với O_NOFOLLOW|O_CLOEXEC, is_write)
    "rb": (os.O_RDONLY, False),
    "wb": (os.O_WRONLY | os.O_CREAT | os.O_TRUNC, True),
    "xb": (os.O_WRONLY | os.O_CREAT | os.O_EXCL, True),
    "ab": (os.O_WRONLY | os.O_CREAT | os.O_APPEND, True),
}


def _reject_empty(path_label: str, value: str) -> None:
    if not value:
        raise PathUnsafeError(path=path_label, reason_vi="đường dẫn rỗng")
    if "\x00" in value:
        raise PathUnsafeError(path=path_label, reason_vi="đường dẫn chứa NUL byte")


def _split_candidate(base: str, candidate: str) -> list[str]:
    _reject_empty(candidate, candidate)
    if os.path.isabs(candidate):
        raise PathUnsafeError(
            path=candidate, reason_vi="candidate phải là đường dẫn tương đối, không phải tuyệt đối"
        )
    raw_parts = candidate.split("/")
    parts: list[str] = []
    for part in raw_parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise PathUnsafeError(
                path=candidate, reason_vi="không cho phép thành phần '..' (parent traversal)"
            )
        if "\x00" in part:
            raise PathUnsafeError(path=candidate, reason_vi="thành phần đường dẫn chứa NUL byte")
        parts.append(part)
    if not parts:
        raise PathUnsafeError(
            path=candidate, reason_vi="candidate rút gọn về rỗng (trỏ chính base)"
        )
    return parts


def _open_base_fd(base: str) -> tuple[int, int]:
    _reject_empty(base, base)
    if not os.path.isabs(base):
        raise PathUnsafeError(path=base, reason_vi="base phải là đường dẫn tuyệt đối")
    try:
        base_fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise PathUnsafeError(
            path=base, reason_vi=f"không mở được base ({exc.strerror or exc})"
        ) from exc
    try:
        base_st = os.fstat(base_fd)
    except OSError:
        os.close(base_fd)
        raise
    if not stat_module.S_ISDIR(base_st.st_mode):
        os.close(base_fd)
        raise PathUnsafeError(path=base, reason_vi="base không phải thư mục")
    return base_fd, base_st.st_dev


def _walk_to_parent_fd(base: str, candidate: str) -> tuple[int, str, int]:
    """Đi qua mọi thành phần trừ thành phần cuối bằng ``dir_fd`` +
    ``O_NOFOLLOW``. Trả ``(parent_fd, leaf_name, base_dev)``. Caller PHẢI
    ``os.close(parent_fd)`` sau khi dùng."""

    parts = _split_candidate(base, candidate)
    current_fd, base_dev = _open_base_fd(base)
    open_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        for name in parts[:-1]:
            try:
                next_fd = os.open(name, open_flags, dir_fd=current_fd)
            except OSError as exc:
                raise PathUnsafeError(
                    path=candidate,
                    reason_vi=(
                        f"không đi qua được thành phần '{name}' an toàn "
                        f"(symlink/không tồn tại/không phải thư mục: {exc.strerror or exc})"
                    ),
                ) from exc
            os.close(current_fd)
            current_fd = next_fd
            next_st = os.fstat(current_fd)
            if next_st.st_dev != base_dev:
                os.close(current_fd)
                raise PathUnsafeError(
                    path=candidate, reason_vi=f"thành phần '{name}' băng qua mount point khác"
                )
        return current_fd, parts[-1], base_dev
    except PathUnsafeError:
        raise
    except Exception:
        os.close(current_fd)
        raise


def resolve_within(base: str, candidate: str) -> str:
    """Trả đường dẫn tuyệt đối thật của ``candidate`` bên trong ``base``.

    Ném ``PathUnsafeError`` (ánh xạ ``E_PATH_UNSAFE``) nếu vi phạm bất kỳ
    bất biến an toàn (traversal/symlink/mount)."""

    parent_fd, leaf, base_dev = _walk_to_parent_fd(base, candidate)
    try:
        try:
            leaf_st = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            leaf_st = None
        except OSError as exc:
            raise PathUnsafeError(
                path=candidate, reason_vi=f"không stat được thành phần cuối ({exc.strerror or exc})"
            ) from exc

        if leaf_st is not None:
            if stat_module.S_ISLNK(leaf_st.st_mode):
                raise PathUnsafeError(
                    path=candidate, reason_vi="thành phần cuối là symlink (không cho phép)"
                )
            if leaf_st.st_dev != base_dev:
                raise PathUnsafeError(
                    path=candidate, reason_vi="thành phần cuối băng qua mount point khác"
                )

        parent_real = os.readlink(f"/proc/self/fd/{parent_fd}")
        result = os.path.join(parent_real, leaf)

        base_real = os.path.realpath(base, strict=False)
        if result != base_real and not result.startswith(base_real.rstrip("/") + "/"):
            raise PathUnsafeError(path=candidate, reason_vi="đường dẫn kết quả vượt ranh giới base")
        return result
    finally:
        os.close(parent_fd)


def open_within(base: str, candidate: str, mode: str) -> IO[bytes]:
    """Mở ``candidate`` bên trong ``base`` an toàn (FD-based, ``O_NOFOLLOW``).

    ``mode`` thuộc {``"rb"``, ``"wb"``, ``"xb"``, ``"ab"``}. Ghi đè file đã
    tồn tại có >1 hardlink bị chặn (phòng tấn công hardlink)."""

    if mode not in _OPEN_FLAGS_BY_MODE:
        raise PathUnsafeError(path=candidate, reason_vi=f"mode '{mode}' không được hỗ trợ")
    extra_flags, is_write = _OPEN_FLAGS_BY_MODE[mode]

    parent_fd, leaf, base_dev = _walk_to_parent_fd(base, candidate)
    try:
        try:
            leaf_st = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            leaf_st = None
        except OSError as exc:
            raise PathUnsafeError(
                path=candidate, reason_vi=f"không stat được thành phần cuối ({exc.strerror or exc})"
            ) from exc

        if leaf_st is not None:
            if stat_module.S_ISLNK(leaf_st.st_mode):
                raise PathUnsafeError(
                    path=candidate, reason_vi="thành phần cuối là symlink (không cho phép)"
                )
            if is_write and leaf_st.st_nlink > 1:
                raise PathUnsafeError(
                    path=candidate,
                    reason_vi=(
                        "file đích có nhiều hardlink (>1) — từ chối ghi để chống tấn công hardlink"
                    ),
                )
            if leaf_st.st_dev != base_dev:
                raise PathUnsafeError(
                    path=candidate, reason_vi="thành phần cuối băng qua mount point khác"
                )

        open_flags = extra_flags | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(leaf, open_flags, mode=0o600, dir_fd=parent_fd)
        except OSError as exc:
            raise PathUnsafeError(
                path=candidate, reason_vi=f"không mở được an toàn ({exc.strerror or exc})"
            ) from exc

        final_st = os.fstat(fd)
        if not stat_module.S_ISREG(final_st.st_mode):
            os.close(fd)
            raise PathUnsafeError(path=candidate, reason_vi="không phải file thường (regular file)")
        if final_st.st_dev != base_dev:
            os.close(fd)
            raise PathUnsafeError(path=candidate, reason_vi="file đích băng qua mount point khác")

        return os.fdopen(fd, mode)
    finally:
        os.close(parent_fd)


class SafePathImpl:
    """Hiện thực ``namios_core.security_types.SafePath`` (Protocol)."""

    def resolve_within(self, base: str, candidate: str) -> str:
        return resolve_within(base, candidate)

    def open_within(self, base: str, candidate: str, mode: str) -> IO[bytes]:
        return open_within(base, candidate, mode)
