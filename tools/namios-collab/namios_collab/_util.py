# -*- coding: utf-8 -*-
"""NaMiCollab Giai đoạn 1 — tiện ích dùng chung (I/O nguyên tử, hash, mutex).

Không mạng, không ``shell=True``, không ``eval``. Cùng quy ước với
``tools/update-center-prototype/staged_deploy.py`` (ghi file: temp +
fsync + ``os.replace`` nguyên tử trên POSIX).
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import socket
import tempfile
import time
from typing import Any, Iterator


def now_ns() -> int:
    """Mốc thời gian đơn điệu cho nhãn version/lease (không dùng cho lịch thật)."""
    return time.time_ns()


def hostname() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return "unknown-host"


def pid() -> int:
    return os.getpid()


def pid_is_alive(check_pid: int) -> bool:
    """``True`` nếu pid còn sống trên MÁY NÀY. Chỉ có ý nghĩa khi
    ``hostname`` của bản ghi khớp máy hiện tại — stale-lock qua máy khác
    không kiểm được bằng ``os.kill`` (đúng giới hạn advisory-lock cục bộ)."""
    if check_pid <= 0:
        return False
    try:
        os.kill(check_pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Tiến trình tồn tại nhưng thuộc user khác — vẫn coi là "sống".
        return True
    return True


def _fsync_dir(dir_path: str) -> None:
    try:
        fd = os.open(dir_path, os.O_DIRECTORY)
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_bytes(path: str, data: bytes) -> None:
    """Ghi file nguyên tử: temp (cùng thư mục) + fsync + ``os.replace``.

    ``os.replace`` là rename nguyên tử trên POSIX cùng filesystem — không có
    trạng thái "ghi nửa vời" khi tiến trình bị kill giữa chừng.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".namicollab-tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        _fsync_dir(directory)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def atomic_write_json(path: str, obj: Any) -> None:
    atomic_write_bytes(path, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


class MutexTimeoutError(TimeoutError):
    """Hết thời gian chờ gate mutex (nghẽn bất thường, không phải conflict logic)."""


@contextlib.contextmanager
def file_mutex(
    gate_path: str,
    timeout_seconds: float = 5.0,
    stale_seconds: float = 10.0,
    poll_interval: float = 0.002,
) -> Iterator[None]:
    """Mutex ngắn hạn giữa nhiều luồng/tiến trình cùng máy, dựng trên
    ``os.O_CREAT | os.O_EXCL`` (tạo file nguyên tử — race-free ở tầng kernel
    trên local filesystem; hầu hết SMB mount hiện đại cũng nguyên tử, một số
    NFS/WebDAV cũ KHÔNG đảm bảo — xem ADR-0023 §rủi ro Giai đoạn 1).

    Dùng làm "cửa hẹp" bọc quanh đoạn đọc-sửa-ghi trạng thái khóa/version
    trong sidecar JSON, KHÔNG phải khóa chính của tài liệu người dùng.
    Gate "mồ côi" (tiến trình giữ gate bị kill) được dọn khi quá
    ``stale_seconds`` để không treo vĩnh viễn trong test/thực tế.
    """
    deadline = time.monotonic() + timeout_seconds
    acquired = False
    while not acquired:
        try:
            fd = os.open(gate_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, str(pid()).encode("ascii"))
            os.close(fd)
            acquired = True
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(gate_path)
            except FileNotFoundError:
                continue  # gate vừa biến mất giữa check — thử lại ngay
            if age > stale_seconds:
                with contextlib.suppress(FileNotFoundError):
                    os.remove(gate_path)
                continue
            if time.monotonic() > deadline:
                raise MutexTimeoutError(
                    f"hết thời gian chờ gate mutex: {gate_path} (có thể bị giữ bởi "
                    "tiến trình khác lâu bất thường)"
                ) from None
            time.sleep(poll_interval)
    try:
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(gate_path)
