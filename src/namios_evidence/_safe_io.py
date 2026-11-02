"""Đọc file evidence-report an toàn — dùng ``namios_security`` (WP8, đã phát
hành) thay vì tự chế lại path/exec an toàn (FACT M1-INTERFACES §7.8:
"mọi WP khác chỉ import từ đây").

``load(path)`` của ``EvidenceValidator`` (§7.7) nhận một đường dẫn tuyệt đối
duy nhất (không base+candidate) — ở đây ta tách ``path`` thành
``dirname``/``basename`` rồi gọi ``namios_security.open_within`` để có đủ
bất biến FD-based (chặn symlink/traversal/mount/TOCTOU) trên thành phần
cuối, cộng thêm so khớp ``realpath`` trên phần thư mục để chặn symlink
trung gian phía trên ``dirname`` (``open_within`` chỉ pin từ ``base`` nó
nhận, nên ``base`` ở đây phải đã là ``realpath``).
"""

from __future__ import annotations

import os
import stat as stat_module

from namios_security import PathUnsafeError as _SecPathUnsafeError
from namios_security import open_within

__all__ = ["PathUnsafeError", "read_text_safe"]

#: Giới hạn kích thước file evidence-report đọc được — chống DoS bằng file khổng lồ.
_MAX_EVIDENCE_BYTES = 2 * 1024 * 1024  # 2 MiB


class PathUnsafeError(Exception):
    """Đường dẫn vi phạm chính sách an toàn (ánh xạ ``E_PATH_UNSAFE``)."""

    def __init__(self, path: str, reason_vi: str) -> None:
        self.path = path
        self.reason_vi = reason_vi
        super().__init__(f"Đường dẫn không an toàn '{path}': {reason_vi}")


def read_text_safe(path: str, *, max_bytes: int = _MAX_EVIDENCE_BYTES) -> str:
    """Đọc nội dung text của ``path`` (đường dẫn tuyệt đối) với các bất biến
    an toàn: không symlink ở bất kỳ thành phần nào bên trong thư mục chứa
    file, không băng mount point, chỉ file thường, giới hạn kích thước."""

    if not path or not os.path.isabs(path):
        raise PathUnsafeError(path=path, reason_vi="phải là đường dẫn tuyệt đối")
    if "\x00" in path:
        raise PathUnsafeError(path=path, reason_vi="đường dẫn chứa NUL byte")
    base = os.path.dirname(path)
    leaf = os.path.basename(path)
    if not leaf or leaf in (".", ".."):
        raise PathUnsafeError(path=path, reason_vi="tên file không hợp lệ")

    # Containment chống traversal: nếu path chứa '..', phạm vi cho phép là
    # tiền tố TRƯỚC thành phần '..' ĐẦU TIÊN; realpath cuối cùng phải nằm
    # trong phạm vi đó. So khớp realpath==abspath KHÔNG bắt được traversal
    # thuần '..' (cả hai cùng chuẩn hoá lexical khi không có symlink), nên
    # kiểm containment riêng. '..' roundtrip quay lại ĐÚNG trong phạm vi vẫn
    # được chấp nhận (không chặn quá tay — đối chứng control-case).
    _parts = path.split(os.sep)
    if ".." in _parts:
        _root = os.sep.join(_parts[: _parts.index("..")]) or os.sep
    else:
        _root = base
    _root_real = os.path.realpath(_root, strict=False)
    _full_real = os.path.realpath(path, strict=False)
    if _full_real != _root_real and not _full_real.startswith(_root_real + os.sep):
        raise PathUnsafeError(
            path=path,
            reason_vi="thành phần '..' thoát ra ngoài phạm vi cho phép (traversal)",
        )

    base_real = os.path.realpath(base, strict=False)
    if base_real != os.path.abspath(base):
        raise PathUnsafeError(
            path=path,
            reason_vi="thư mục chứa file có symlink trung gian hoặc thành phần '..'",
        )

    try:
        with open_within(base_real, leaf, "rb") as handle:
            st = os.fstat(handle.fileno())
            if not stat_module.S_ISREG(st.st_mode):
                raise PathUnsafeError(path=path, reason_vi="không phải file thường (regular file)")
            if st.st_size > max_bytes:
                raise PathUnsafeError(
                    path=path, reason_vi=f"file vượt giới hạn kích thước {max_bytes} bytes"
                )
            data = handle.read(st.st_size)
    except _SecPathUnsafeError as exc:
        raise PathUnsafeError(path=path, reason_vi=exc.reason_vi) from exc
    except OSError as exc:
        raise PathUnsafeError(
            path=path, reason_vi=f"không mở được an toàn ({exc.strerror or exc})"
        ) from exc

    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PathUnsafeError(path=path, reason_vi="nội dung không phải UTF-8 hợp lệ") from exc
