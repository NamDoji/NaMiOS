# -*- coding: utf-8 -*-
"""NaMiOS — NaMiCollab Giai đoạn 1: Lock Manager (advisory, sidecar JSON).

Đọc TRƯỚC: ``docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md`` §4 và
``docs/collab/ADR-0023-namicollab.md`` (Giai đoạn 1 — "file local/SMB/WebDAV
theo quyền, locks, cảnh báo conflict, lịch sử bản cục bộ... không yêu cầu
cloud để dùng Office").

Đây là PROTOTYPE LOGIC chạy cục bộ (không server, không mạng, không phụ
thuộc Samba/WebDAV thật) minh họa đúng mô hình khóa của Giai đoạn 1:
  - **advisory** (không phải mandatory lock của kernel) — chỉ tiến trình
    nào CŨNG gọi ``LockManager`` mới tôn trọng khóa;
  - **exclusive-vs-shared** — một writer độc quyền, hoặc nhiều reader chia
    sẻ, không trộn lẫn;
  - **phát hiện stale lock** — qua lease hết hạn hoặc (cùng host + pid đã
    chết) — để một tiến trình crash không khóa file vĩnh viễn.

Giới hạn trung thực (đọc kỹ trước khi dựa vào kết quả — xem thêm
``docs/collab/NAMICOLLAB-PHASE-MATRIX.md``):
  - Đây KHÔNG thay thế lock thật của SMB server (oplock/byte-range lock) hay
    sidecar ``.~lock.<file>#`` của LibreOffice. Hai cơ chế đó vẫn hoạt động
    độc lập song song; module này là một lớp advisory TẦNG ỨNG DỤNG bổ sung
    cho NaMiCollab, chưa nối vào LibreOffice/Dolphin.
  - Chưa test trên SMB/WebDAV server thật (chỉ test trên filesystem cục bộ
    trong ``pytest``, dùng ``tempfile``) — xem mục "pilot" trong ADR-0023.
  - Stale-detection theo pid chỉ đúng khi ``hostname`` khớp máy hiện tại;
    qua máy khác chỉ còn tiêu chí lease hết hạn.
"""
from __future__ import annotations

import contextlib
import os
import secrets
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from namios_collab import _util


class LockMode(str, Enum):
    EXCLUSIVE = "exclusive"
    SHARED = "shared"


class LockError(Exception):
    """Lỗi chung của lock manager."""


@dataclass
class LockHolder:
    token: str
    owner: str
    mode: LockMode
    acquired_ns: int
    lease_seconds: float
    pid: int
    hostname: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "owner": self.owner,
            "mode": self.mode.value,
            "acquired_ns": self.acquired_ns,
            "lease_seconds": self.lease_seconds,
            "pid": self.pid,
            "hostname": self.hostname,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LockHolder":
        return cls(
            token=d["token"],
            owner=d["owner"],
            mode=LockMode(d["mode"]),
            acquired_ns=int(d["acquired_ns"]),
            lease_seconds=float(d["lease_seconds"]),
            pid=int(d["pid"]),
            hostname=d["hostname"],
            note=d.get("note", ""),
        )

    def is_stale(self, *, now_ns: int, current_hostname: str) -> bool:
        lease_expired = now_ns > self.acquired_ns + int(self.lease_seconds * 1e9)
        if lease_expired:
            return True
        if self.hostname == current_hostname and not _util.pid_is_alive(self.pid):
            return True
        return False


@dataclass
class LockHandle:
    """Trả về cho caller khi ``acquire`` thành công — cần để ``release``."""

    path: str
    token: str
    owner: str
    mode: LockMode
    acquired_ns: int
    lease_seconds: float


class LockConflictError(LockError):
    def __init__(self, path: str, requested_mode: LockMode, holders: list[LockHolder]):
        self.path = path
        self.requested_mode = requested_mode
        self.holders = holders
        owners = ", ".join(f"{h.owner}({h.mode.value})" for h in holders)
        super().__init__(
            f"không lấy được khóa {requested_mode.value} trên {path!r}: "
            f"đang bị giữ bởi [{owners}]"
        )


class LockNotHeldError(LockError):
    pass


@dataclass
class LockStatus:
    path: str
    holders: list[LockHolder] = field(default_factory=list)

    @property
    def is_locked(self) -> bool:
        return len(self.holders) > 0

    @property
    def is_exclusive(self) -> bool:
        return any(h.mode is LockMode.EXCLUSIVE for h in self.holders)


class LockManager:
    """Quản lý khóa advisory trên một đường dẫn file, dùng sidecar JSON.

    Mỗi ``path`` có một sidecar ``<path>.namilock.json`` (danh sách holder)
    và một gate mutex tạm ``<path>.namilock.gate`` (xem ``_util.file_mutex``)
    bọc quanh đoạn đọc-sửa-ghi để nhiều luồng/tiến trình giành khóa cùng lúc
    không ghi đè lẫn nhau (race-free ở mức ``O_CREAT|O_EXCL``).
    """

    def __init__(
        self,
        *,
        default_lease_seconds: float = 300.0,
        mutex_timeout_seconds: float = 5.0,
    ) -> None:
        self.default_lease_seconds = default_lease_seconds
        self.mutex_timeout_seconds = mutex_timeout_seconds

    # -- đường dẫn sidecar ------------------------------------------------
    @staticmethod
    def _sidecar_path(path: str) -> str:
        return path + ".namilock.json"

    @staticmethod
    def _gate_path(path: str) -> str:
        return path + ".namilock.gate"

    def _read_holders(self, path: str) -> list[LockHolder]:
        sidecar = self._sidecar_path(path)
        try:
            raw = _util.read_json(sidecar)
        except FileNotFoundError:
            return []
        except (ValueError, OSError):
            # Sidecar hỏng/đọc nửa vời — coi như không có khóa hợp lệ, KHÔNG
            # tự xóa (giữ bằng chứng cho người vận hành xem).
            return []
        return [LockHolder.from_dict(h) for h in raw.get("holders", [])]

    def _write_holders(self, path: str, holders: list[LockHolder]) -> None:
        sidecar = self._sidecar_path(path)
        if not holders:
            with contextlib.suppress(FileNotFoundError):
                os.remove(sidecar)
            return
        _util.atomic_write_json(
            sidecar, {"path": path, "holders": [h.to_dict() for h in holders]}
        )

    def _drop_stale(self, holders: list[LockHolder]) -> tuple[list[LockHolder], list[LockHolder]]:
        now = _util.now_ns()
        host = _util.hostname()
        live, stale = [], []
        for h in holders:
            (stale if h.is_stale(now_ns=now, current_hostname=host) else live).append(h)
        return live, stale

    # -- API công khai ------------------------------------------------
    def status(self, path: str, *, drop_stale: bool = True) -> LockStatus:
        """Trạng thái khóa hiện tại. ``drop_stale=True`` dọn stale holder
        trước khi trả về (và ghi lại sidecar) — không đổi hành vi logic,
        chỉ giúp caller thấy trạng thái "thật" ngay lập tức."""
        with _util.file_mutex(self._gate_path(path), timeout_seconds=self.mutex_timeout_seconds):
            holders = self._read_holders(path)
            if drop_stale:
                live, stale = self._drop_stale(holders)
                if stale:
                    self._write_holders(path, live)
                holders = live
            return LockStatus(path=path, holders=holders)

    def break_stale(self, path: str) -> list[LockHolder]:
        """Dọn mọi holder stale trên ``path``. Trả về danh sách holder đã
        bị dọn (rỗng nếu không có gì stale)."""
        with _util.file_mutex(self._gate_path(path), timeout_seconds=self.mutex_timeout_seconds):
            holders = self._read_holders(path)
            live, stale = self._drop_stale(holders)
            if stale:
                self._write_holders(path, live)
            return stale

    def acquire(
        self,
        path: str,
        owner: str,
        mode: LockMode | str = LockMode.EXCLUSIVE,
        *,
        lease_seconds: float | None = None,
        note: str = "",
    ) -> LockHandle:
        """Giành khóa trên ``path``. Ném ``LockConflictError`` nếu không
        giành được NGAY (prototype không hàng-đợi/blocking-wait — caller tự
        quyết định retry, giống UX "tệp đang được người khác chỉnh" của
        LibreOffice, không giống mutex chờ vô hạn)."""
        mode = LockMode(mode)
        lease = self.default_lease_seconds if lease_seconds is None else lease_seconds
        token = secrets.token_hex(16)
        with _util.file_mutex(self._gate_path(path), timeout_seconds=self.mutex_timeout_seconds):
            holders, _stale = self._drop_stale(self._read_holders(path))

            if holders:
                existing_exclusive = any(h.mode is LockMode.EXCLUSIVE for h in holders)
                if mode is LockMode.EXCLUSIVE or existing_exclusive:
                    # exclusive mới ⇒ cần hoàn toàn trống; shared mới ⇒
                    # chỉ cần KHÔNG có exclusive đang giữ.
                    raise LockConflictError(path, mode, holders)

            new_holder = LockHolder(
                token=token,
                owner=owner,
                mode=mode,
                acquired_ns=_util.now_ns(),
                lease_seconds=lease,
                pid=_util.pid(),
                hostname=_util.hostname(),
                note=note,
            )
            self._write_holders(path, [*holders, new_holder])
            return LockHandle(
                path=path,
                token=token,
                owner=owner,
                mode=mode,
                acquired_ns=new_holder.acquired_ns,
                lease_seconds=lease,
            )

    def release(self, handle: LockHandle, *, force: bool = False) -> None:
        """Trả khóa. Mặc định đòi đúng ``token`` đã nhận khi ``acquire`` —
        chống "ai cũng gọi release được" (release giả danh). ``force=True``
        cho người vận hành phá khóa theo ``owner`` khi không còn ``token``
        (ví dụ sau crash không cứu được handle) — dùng cẩn trọng."""
        with _util.file_mutex(self._gate_path(handle.path), timeout_seconds=self.mutex_timeout_seconds):
            holders = self._read_holders(handle.path)
            if force:
                remaining = [h for h in holders if h.owner != handle.owner]
            else:
                remaining = [h for h in holders if h.token != handle.token]
                if len(remaining) == len(holders):
                    raise LockNotHeldError(
                        f"không tìm thấy khóa token={handle.token!r} của {handle.owner!r} "
                        f"trên {handle.path!r} (đã release trước đó hoặc token sai)"
                    )
            self._write_holders(handle.path, remaining)
