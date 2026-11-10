# -*- coding: utf-8 -*-
"""NaMiOS — NaMiCollab Giai đoạn 1: Local Version History Store.

Đọc TRƯỚC: ``docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md`` §4
("lịch sử bản cục bộ") và ``docs/collab/ADR-0023-namicollab.md`` Giai đoạn 1.

Lưu các snapshot của MỘT file vào thư mục sidecar ``<path>.namihistory/``
cạnh file gốc — không cần cloud, không cần server, hoạt động trên bất kỳ
file local/SMB/WebDAV-mount nào. Mỗi snapshot = bản sao nội dung tại một
thời điểm + hash SHA-256 + nhãn tuỳ chọn, ghi vào manifest JSON.

Nguyên tắc cứng (đặt tên method để không ai gọi nhầm):
  * ``snapshot()``  — KHÔNG BAO GIỜ sửa file gốc, chỉ đọc và sao lưu.
  * ``restore()``   — THEO ĐÚNG yêu cầu task: "never overwrite without a
    snapshot". Trước khi ghi đè ``path`` bằng nội dung một version cũ,
    ``restore()`` LUÔN tự chụp một snapshot an toàn của trạng thái HIỆN TẠI
    trước (trừ khi file hiện tại đã giống hệt bản muốn restore — không có
    gì để mất). Sau khi ghi, verify lại hash của file trên đĩa khớp hash đã
    lưu — sai thì raise, KHÔNG để lỗi âm thầm.

Giới hạn trung thực:
  - Đây là lịch sử CỤC BỘ trên MỘT máy/MỘT mount point — không đồng bộ
    nhiều máy, không thay cho backup hệ thống (Kup/bup — xem ADR 0014/0020).
  - Không nén/dedupe giữa các version (mỗi snapshot là bản sao đầy đủ) —
    chấp nhận được cho prototype, cần tối ưu dung lượng trước khi dùng cho
    file lớn/nhiều version (ghi rõ trong PHASE-MATRIX).
  - Không mã hóa snapshot — thừa hưởng quyền filesystem của thư mục chứa
    file gốc, không thêm/giảm bảo vệ.
"""
from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import Optional

from namios_collab import _util


class VersionStoreError(Exception):
    pass


class VersionNotFoundError(VersionStoreError):
    pass


class RestoreVerificationError(VersionStoreError):
    """Hash sau khi ghi KHÔNG khớp hash đã lưu trong manifest — chặn, không
    để người dùng tưởng restore thành công trong khi nội dung trên đĩa sai."""


@dataclass
class VersionEntry:
    version_id: str
    path: str
    created_ns: int
    sha256: str
    size_bytes: int
    label: str
    snapshot_file: str  # tên file trong .namihistory/, đường dẫn tương đối
    reason: str = "manual"  # "manual" | "pre-restore-safety"

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "path": self.path,
            "created_ns": self.created_ns,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "label": self.label,
            "snapshot_file": self.snapshot_file,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VersionEntry":
        return cls(
            version_id=d["version_id"],
            path=d["path"],
            created_ns=int(d["created_ns"]),
            sha256=d["sha256"],
            size_bytes=int(d["size_bytes"]),
            label=d.get("label", ""),
            snapshot_file=d["snapshot_file"],
            reason=d.get("reason", "manual"),
        )


class LocalVersionHistory:
    """Lịch sử bản cục bộ cho các file, mỗi file có sidecar riêng
    ``<path>.namihistory/`` (manifest.json + các file snapshot ``NNN-<hash
    ngắn>.snap``)."""

    def __init__(self, *, mutex_timeout_seconds: float = 5.0) -> None:
        self.mutex_timeout_seconds = mutex_timeout_seconds

    # -- đường dẫn sidecar ------------------------------------------------
    @staticmethod
    def _history_dir(path: str) -> str:
        return path + ".namihistory"

    @staticmethod
    def _manifest_path(path: str) -> str:
        return os.path.join(LocalVersionHistory._history_dir(path), "manifest.json")

    @staticmethod
    def _gate_path(path: str) -> str:
        return path + ".namihistory.gate"

    def _read_manifest(self, path: str) -> list[VersionEntry]:
        manifest = self._manifest_path(path)
        try:
            raw = _util.read_json(manifest)
        except FileNotFoundError:
            return []
        return [VersionEntry.from_dict(e) for e in raw.get("entries", [])]

    def _write_manifest(self, path: str, entries: list[VersionEntry]) -> None:
        manifest = self._manifest_path(path)
        _util.atomic_write_json(
            manifest, {"path": path, "entries": [e.to_dict() for e in entries]}
        )

    # -- API công khai ------------------------------------------------
    def list_versions(self, path: str) -> list[VersionEntry]:
        with _util.file_mutex(self._gate_path(path), timeout_seconds=self.mutex_timeout_seconds):
            return self._read_manifest(path)

    def snapshot(self, path: str, *, label: str = "", reason: str = "manual") -> VersionEntry:
        """Chụp trạng thái HIỆN TẠI của ``path`` thành một version mới.
        Raise ``FileNotFoundError`` nếu ``path`` không tồn tại (không có gì
        để chụp — không tạo version rỗng giả)."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"không có file để snapshot: {path!r}")

        with open(path, "rb") as fh:
            data = fh.read()
        content_hash = _util.sha256_bytes(data)

        with _util.file_mutex(self._gate_path(path), timeout_seconds=self.mutex_timeout_seconds):
            entries = self._read_manifest(path)
            seq = len(entries) + 1
            short_hash = content_hash.split(":", 1)[1][:12]
            snapshot_name = f"{seq:04d}-{short_hash}.snap"
            history_dir = self._history_dir(path)
            os.makedirs(history_dir, exist_ok=True)
            snapshot_path = os.path.join(history_dir, snapshot_name)
            _util.atomic_write_bytes(snapshot_path, data)

            entry = VersionEntry(
                version_id=f"v{seq}",
                path=path,
                created_ns=_util.now_ns(),
                sha256=content_hash,
                size_bytes=len(data),
                label=label,
                snapshot_file=snapshot_name,
                reason=reason,
            )
            self._write_manifest(path, [*entries, entry])
            return entry

    def get_version(self, path: str, version_id: str) -> VersionEntry:
        for entry in self.list_versions(path):
            if entry.version_id == version_id:
                return entry
        raise VersionNotFoundError(f"không có version {version_id!r} cho {path!r}")

    def read_version_bytes(self, path: str, version_id: str) -> bytes:
        entry = self.get_version(path, version_id)
        snapshot_path = os.path.join(self._history_dir(path), entry.snapshot_file)
        with open(snapshot_path, "rb") as fh:
            data = fh.read()
        actual_hash = _util.sha256_bytes(data)
        if actual_hash != entry.sha256:
            raise RestoreVerificationError(
                f"snapshot {entry.snapshot_file!r} đã hỏng trên đĩa: hash hiện tại "
                f"{actual_hash} != hash đã lưu {entry.sha256}"
            )
        return data

    def restore(
        self, path: str, version_id: str, *, safety_label: str = "pre-restore-safety"
    ) -> tuple[VersionEntry, Optional[VersionEntry]]:
        """Ghi đè ``path`` bằng nội dung của ``version_id``.

        LUÔN snapshot trạng thái hiện tại của ``path`` trước khi ghi đè
        (nguyên tắc "never overwrite without a snapshot"), TRỪ hai trường
        hợp không cần: (a) ``path`` hiện chưa tồn tại — không có gì để mất;
        (b) nội dung hiện tại đã giống hệt (cùng hash) bản muốn restore —
        ghi đè sẽ là no-op, chụp thêm một bản trùng là lãng phí.

        Trả về ``(version_đã_restore, safety_snapshot_hoặc_None)``. Sau khi
        ghi, verify lại hash file trên đĩa — không khớp thì raise
        ``RestoreVerificationError`` (không để restore "coi như xong" trong
        khi nội dung sai)."""
        target_entry = self.get_version(path, version_id)
        target_bytes = self.read_version_bytes(path, version_id)

        safety_entry: Optional[VersionEntry] = None
        if os.path.isfile(path):
            current_hash = _util.sha256_file(path)
            if current_hash != target_entry.sha256:
                safety_entry = self.snapshot(path, label=safety_label, reason="pre-restore-safety")
            # else: hiện tại đã khớp bản muốn restore — không cần safety snapshot.
        # else: path chưa tồn tại — không có gì để mất, bỏ qua safety snapshot.

        _util.atomic_write_bytes(path, target_bytes)

        written_hash = _util.sha256_file(path)
        if written_hash != target_entry.sha256:
            raise RestoreVerificationError(
                f"restore {version_id!r} cho {path!r} THẤT BẠI khi verify: "
                f"hash sau khi ghi {written_hash} != hash version {target_entry.sha256}"
            )
        return target_entry, safety_entry

    def purge_history(self, path: str) -> None:
        """Xóa TOÀN BỘ lịch sử của ``path`` (không xóa ``path`` chính nó).
        Dùng khi người dùng chủ động muốn dọn — không gọi tự động ở nơi
        khác trong module này."""
        history_dir = self._history_dir(path)
        gate = self._gate_path(path)
        with _util.file_mutex(gate, timeout_seconds=self.mutex_timeout_seconds):
            if os.path.isdir(history_dir):
                for name in os.listdir(history_dir):
                    with contextlib.suppress(FileNotFoundError):
                        os.remove(os.path.join(history_dir, name))
                with contextlib.suppress(OSError):
                    os.rmdir(history_dir)
        with contextlib.suppress(FileNotFoundError):
            os.remove(gate)
