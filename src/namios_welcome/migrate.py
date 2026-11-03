"""Chuyển dữ liệu Windows AN TOÀN sang home người dùng NaMiOS (DATA-002).

``WindowsDataMigrator`` quét MỘT phân vùng/thư mục Windows đã được mount sẵn
(đường dẫn do caller truyền vào — module này KHÔNG tự mount/unmount, KHÔNG
tự dò ổ đĩa) và liệt kê 4 thư mục quen thuộc: ``Documents``/``Desktop``/
``Downloads``/``Pictures``. Luồng chuyển dữ liệu LUÔN là **sao chép có báo
cáo**, KHÔNG BAO GIỜ di chuyển hay xóa file nguồn (DATA-002 P0) — module này
không gọi bất kỳ API xóa/move nào trên phía nguồn.

Ranh giới an toàn:

- Mọi đường dẫn tương đối (tên thư mục/tên file dưới ``source_root`` hay
  ``dest_home``) đi qua ``namios_security.resolve_within``/``open_within``
  (FD-based, chặn ``..``, symlink trung gian/leaf, băng mount point) trước
  khi đọc hoặc ghi — xem ``namios_security.safe_path`` để biết chi tiết bất
  biến. Module này KHÔNG tự chế lại logic path an toàn.
- KHÔNG ghi đè file đích đã tồn tại: trùng tên → đổi tên kiểu
  ``"tên (1).ext"`` (ghi log ``conflicts``); nếu không tìm được tên trống
  trong giới hạn hợp lý thì bỏ qua (ghi log ``skipped``).
- Từ chối đọc khi phân vùng nguồn có dấu hiệu **hibernated/Fast Startup**
  (file ``hiberfil.sys`` ở gốc ``source_root`` — NTFS ở trạng thái này có
  thể không nhất quán khi đọc song song với Windows) hoặc khi không liệt kê
  được nội dung ``source_root`` (coi là **volume lỗi**) — ném
  ``WindowsVolumeUnsafeError`` và KHÔNG đọc gì thêm.
- KHÔNG BAO GIỜ tự mở BitLocker (module không gọi bất kỳ API giải mã nào —
  chỉ đọc đường dẫn đã mount sẵn do caller cung cấp). KHÔNG ghi nội dung
  file vào log/báo cáo (báo cáo chỉ chứa tên quan hệ + kích thước byte,
  không chứa nội dung); để giảm rủi ro lộ khóa khôi phục, các file có tên
  khớp mẫu xuất khóa khôi phục BitLocker quen thuộc (``*.bek``,
  ``BitLockerRecoveryKey*``) bị bỏ qua, không sao chép.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from namios_i18n import Lang, t
from namios_security import PathUnsafeError, open_within, resolve_within

# NOTE (i18n, 03/11/2026): ``reason_vi`` dưới đây đi qua ``namios_i18n.t``
# (nhóm key ``welcome.migrate.error.*``, VI/EN đã seed) nhưng LUÔN ép
# ``lang=Lang.VI`` — cùng lý do với ``firstrun.py`` (field đặt tên theo quy
# ước ``_vi``, một nguồn sự thật chung, không đổi theo ngôn ngữ hiển thị).

__all__ = [
    "KNOWN_FOLDER_NAMES",
    "DiscoveredFolder",
    "MigratedFileEntry",
    "SkippedEntry",
    "ConflictEntry",
    "MigrationReport",
    "WindowsVolumeUnsafeError",
    "WindowsDataMigrator",
]

#: 4 thư mục quen thuộc cần liệt kê theo yêu cầu (thứ tự ổn định cho báo cáo).
KNOWN_FOLDER_NAMES: tuple[str, ...] = ("Documents", "Desktop", "Downloads", "Pictures")

#: Tên thư mục profile Windows điển hình khi ``source_root`` là gốc phân
#: vùng (ví dụ ``/mnt/windows``) chứ không phải thẳng thư mục profile.
_PROFILES_PARENT_NAMES: tuple[str, ...] = ("Users",)

#: Tên file đánh dấu hibernate/Fast Startup — đọc NTFS lúc này không an toàn.
_HIBERNATION_MARKER_NAMES: frozenset[str] = frozenset({"hiberfil.sys"})

#: Mẫu tên file xuất khóa khôi phục BitLocker — không sao chép, không log nội dung.
_BITLOCKER_KEY_FILENAME_PREFIXES: tuple[str, ...] = ("bitlockerrecoverykey",)
_BITLOCKER_KEY_FILENAME_SUFFIXES: tuple[str, ...] = (".bek",)

#: Số lần thử tối đa khi đổi tên tránh ghi đè trước khi bỏ qua.
_MAX_RENAME_ATTEMPTS = 500


@dataclass(frozen=True)
class DiscoveredFolder:
    """Một thư mục quen thuộc tìm thấy dưới ``source_root``."""

    category: str
    source_path: str


@dataclass(frozen=True)
class MigratedFileEntry:
    category: str
    relative_path: str
    size_bytes: int


@dataclass(frozen=True)
class SkippedEntry:
    category: str
    relative_path: str
    reason_vi: str


@dataclass(frozen=True)
class ConflictEntry:
    category: str
    relative_path: str
    resolved_relative_path: str
    reason_vi: str


@dataclass(frozen=True)
class MigrationReport:
    """Báo cáo sau một lần ``migrate()`` — KHÔNG chứa nội dung file."""

    categories_found: tuple[str, ...]
    files_copied: int
    bytes_copied: int
    copied_files: tuple[MigratedFileEntry, ...]
    skipped: tuple[SkippedEntry, ...]
    conflicts: tuple[ConflictEntry, ...]


@dataclass
class WindowsVolumeUnsafeError(Exception):
    """Từ chối đọc phân vùng nguồn (hibernated/Fast Startup hoặc lỗi)."""

    source_root: str
    reason_vi: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return t(
            "welcome.migrate.error.volume_unsafe_prefix",
            lang=Lang.VI,
            source_root=self.source_root,
            reason=self.reason_vi,
        )


def _is_bitlocker_key_filename(name: str) -> bool:
    lowered = name.lower()
    if lowered.endswith(_BITLOCKER_KEY_FILENAME_SUFFIXES):
        return True
    return any(lowered.startswith(prefix) for prefix in _BITLOCKER_KEY_FILENAME_PREFIXES)


def _check_hibernation_marker(root: Path) -> None:
    try:
        entries = {entry.name.lower() for entry in os.scandir(root)}
    except OSError as exc:
        raise WindowsVolumeUnsafeError(
            source_root=str(root),
            reason_vi=t(
                "welcome.migrate.error.cannot_list_volume",
                lang=Lang.VI,
                detail=exc.strerror or exc,
            ),
        ) from exc
    if entries & _HIBERNATION_MARKER_NAMES:
        raise WindowsVolumeUnsafeError(
            source_root=str(root),
            reason_vi=t("welcome.migrate.error.hibernation_detected", lang=Lang.VI),
        )


def _next_available_relative_path(dest_home: Path, relative_path: str) -> str | None:
    """Trả về một ``relative_path`` CHƯA tồn tại dưới ``dest_home`` bằng cách
    chèn hậu tố ``" (n)"`` trước phần mở rộng. ``None`` nếu không tìm được
    trong ``_MAX_RENAME_ATTEMPTS`` lần thử."""

    parent = os.path.dirname(relative_path)
    base_name = os.path.basename(relative_path)
    stem, ext = os.path.splitext(base_name)
    for attempt in range(1, _MAX_RENAME_ATTEMPTS + 1):
        candidate_name = f"{stem} ({attempt}){ext}"
        candidate_relative = os.path.join(parent, candidate_name) if parent else candidate_name
        if not (dest_home / candidate_relative).exists():
            return candidate_relative
    return None


class WindowsDataMigrator:
    """Quét + sao chép Documents/Desktop/Downloads/Pictures từ một phân vùng
    Windows đã mount sẵn sang home người dùng NaMiOS — KHÔNG di chuyển/xóa
    nguồn, KHÔNG ghi đè đích, KHÔNG tự mở BitLocker."""

    def __init__(self, source_root: Path | str) -> None:
        self._source_root = Path(source_root)
        if not self._source_root.is_dir():
            raise WindowsVolumeUnsafeError(
                source_root=str(self._source_root),
                reason_vi=t("welcome.migrate.error.source_not_a_directory", lang=Lang.VI),
            )

    @property
    def source_root(self) -> Path:
        return self._source_root

    def check_volume_safety(self) -> None:
        """Ném ``WindowsVolumeUnsafeError`` nếu volume hibernated/Fast
        Startup hoặc không liệt kê được (coi là lỗi)."""

        _check_hibernation_marker(self._source_root)

    def _profile_candidates(self) -> tuple[Path, ...]:
        """Các gốc có thể chứa 4 thư mục quen thuộc: ``source_root`` trực
        tiếp, hoặc ``source_root/Users/<ai đó>`` nếu được truyền gốc phân
        vùng thay vì thẳng thư mục hồ sơ người dùng."""

        candidates: list[Path] = [self._source_root]
        for users_name in _PROFILES_PARENT_NAMES:
            users_dir = self._source_root / users_name
            if not users_dir.is_dir() or users_dir.is_symlink():
                continue
            try:
                child_entries = sorted(os.scandir(users_dir), key=lambda e: e.name)
            except OSError:
                continue
            for entry in child_entries:
                if entry.is_dir(follow_symlinks=False):
                    candidates.append(Path(entry.path))
        return tuple(candidates)

    def discover_folders(self) -> tuple[DiscoveredFolder, ...]:
        """Liệt kê các thư mục quen thuộc tìm thấy (không copy gì).

        Tìm trực tiếp dưới ``source_root``; nếu không thấy gì ở đó, thử các
        hồ sơ con dưới ``source_root/Users/*`` (trường hợp ``source_root``
        là gốc phân vùng chứ không phải thẳng thư mục hồ sơ)."""

        for profile_root in self._profile_candidates():
            found: list[DiscoveredFolder] = []
            for name in KNOWN_FOLDER_NAMES:
                try:
                    resolved = resolve_within(str(profile_root), name)
                except PathUnsafeError:
                    continue
                candidate_path = Path(resolved)
                if candidate_path.is_dir() and not candidate_path.is_symlink():
                    found.append(DiscoveredFolder(category=name, source_path=str(candidate_path)))
            if found:
                return tuple(found)
        return ()

    def _iter_category_files(self, category_root: Path) -> list[str]:
        """Trả danh sách ``relative_path`` (POSIX-style) của mọi file thường
        dưới ``category_root``, KHÔNG theo symlink."""

        relative_paths: list[str] = []
        for dirpath, dirnames, filenames in os.walk(category_root, followlinks=False):
            dirnames.sort()
            for filename in sorted(filenames):
                full_path = Path(dirpath) / filename
                if full_path.is_symlink():
                    continue
                relative_paths.append(str(full_path.relative_to(category_root)))
        return relative_paths

    def migrate(
        self,
        dest_home: Path | str,
        *,
        categories: Sequence[str] | None = None,
    ) -> MigrationReport:
        """Sao chép (KHÔNG di chuyển/xóa nguồn) các thư mục quen thuộc tìm
        thấy sang ``dest_home``. ``categories`` lọc theo tên (mặc định cả
        4). Luôn gọi ``check_volume_safety()`` trước khi đọc bất kỳ gì."""

        self.check_volume_safety()
        dest_home_path = Path(dest_home)
        dest_home_path.mkdir(parents=True, exist_ok=True)

        wanted = set(categories) if categories is not None else set(KNOWN_FOLDER_NAMES)
        folders = [f for f in self.discover_folders() if f.category in wanted]

        files_copied = 0
        bytes_copied = 0
        copied_entries: list[MigratedFileEntry] = []
        skipped: list[SkippedEntry] = []
        conflicts: list[ConflictEntry] = []
        categories_found: list[str] = []

        for folder in folders:
            categories_found.append(folder.category)
            category_root = Path(folder.source_path)
            for relative in self._iter_category_files(category_root):
                base_name = os.path.basename(relative)
                if _is_bitlocker_key_filename(base_name):
                    skipped.append(
                        SkippedEntry(
                            category=folder.category,
                            relative_path=relative,
                            reason_vi=t(
                                "welcome.migrate.error.bitlocker_key_skipped", lang=Lang.VI
                            ),
                        )
                    )
                    continue

                try:
                    # Kiểm tra sớm (sẽ mở lại FD-based bằng open_within ở bước
                    # copy); không giữ chuỗi path để tránh dùng lại gây TOCTOU.
                    resolve_within(str(category_root), relative)
                except PathUnsafeError as exc:
                    skipped.append(
                        SkippedEntry(
                            category=folder.category,
                            relative_path=relative,
                            reason_vi=t(
                                "welcome.migrate.error.source_path_unsafe",
                                lang=Lang.VI,
                                reason=exc.reason_vi,
                            ),
                        )
                    )
                    continue

                dest_relative = os.path.join(folder.category, relative)
                final_relative = dest_relative
                if (dest_home_path / dest_relative).exists():
                    alternative = _next_available_relative_path(dest_home_path, dest_relative)
                    if alternative is None:
                        skipped.append(
                            SkippedEntry(
                                category=folder.category,
                                relative_path=relative,
                                reason_vi=t(
                                    "welcome.migrate.error.no_available_rename", lang=Lang.VI
                                ),
                            )
                        )
                        continue
                    conflicts.append(
                        ConflictEntry(
                            category=folder.category,
                            relative_path=relative,
                            resolved_relative_path=alternative,
                            reason_vi=t(
                                "welcome.migrate.error.destination_conflict_renamed",
                                lang=Lang.VI,
                            ),
                        )
                    )
                    final_relative = alternative

                dest_abs_parent = (dest_home_path / final_relative).parent
                dest_abs_parent.mkdir(parents=True, exist_ok=True)

                try:
                    # Đọc nguồn bằng open_within (FD-based, O_NOFOLLOW từng
                    # thành phần) — KHÔNG dùng builtin open() trên chuỗi đã
                    # resolve, vì giữa resolve và open, file nguồn có thể bị
                    # swap thành symlink trỏ ra ngoài source_root (TOCTOU,
                    # SEC-002/DATA-002, SEC-SWEEP-001). Lấy size từ fstat trên
                    # chính FD đã pin, không os.path.getsize(chuỗi) lần nữa.
                    with (
                        open_within(str(category_root), relative, "rb") as src,
                        open_within(str(dest_home_path), final_relative, "xb") as dst,
                    ):
                        shutil.copyfileobj(src, dst)
                        size_bytes = os.fstat(src.fileno()).st_size
                except PathUnsafeError as exc:
                    skipped.append(
                        SkippedEntry(
                            category=folder.category,
                            relative_path=relative,
                            reason_vi=t(
                                "welcome.migrate.error.source_path_unsafe",
                                lang=Lang.VI,
                                reason=exc.reason_vi,
                            ),
                        )
                    )
                    continue
                except OSError as exc:
                    skipped.append(
                        SkippedEntry(
                            category=folder.category,
                            relative_path=relative,
                            reason_vi=t(
                                "welcome.migrate.error.io_error_copying",
                                lang=Lang.VI,
                                detail=exc.strerror or exc,
                            ),
                        )
                    )
                    continue

                files_copied += 1
                bytes_copied += size_bytes
                copied_entries.append(
                    MigratedFileEntry(
                        category=folder.category,
                        relative_path=final_relative,
                        size_bytes=size_bytes,
                    )
                )

        return MigrationReport(
            categories_found=tuple(categories_found),
            files_copied=files_copied,
            bytes_copied=bytes_copied,
            copied_files=tuple(copied_entries),
            skipped=tuple(skipped),
            conflicts=tuple(conflicts),
        )
