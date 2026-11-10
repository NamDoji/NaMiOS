# -*- coding: utf-8 -*-
"""archive_safety — quét an toàn ZIP/TAR KHÔNG giải nén (zip-bomb + path
traversal + symlink escape).

Đọc TRƯỚC: ``docs/specs/namios-pl20/02_MO_TEP_VA_DINH_DANG.md`` §3
("Giải nén chọn thư mục, kiểm file trùng, bảo vệ path traversal (../,
absolute path, symlink/hardlink), archive bomb, kích thước giải nén, số
mục, nested archive và malware; không tự chạy chương trình sau giải nén")
và ``docs/specs/namios-pl20/04_KIEN_TRUC_QA.md`` §2 ("Archives: ngăn zip
slip/path traversal, symlink escape, bomb, file count/size, nested depth,
encrypted ambiguity").

Module này CHỈ ĐỌC METADATA (``zipfile``/``tarfile`` ở chế độ liệt kê
entry/header) — KHÔNG BAO GIỜ gọi ``extractall``/``extract`` và KHÔNG viết
bất kỳ byte nội dung nào ra đĩa. Với một symlink nghi vấn, chỉ đọc phần
TARGET (vài byte, dạng chuỗi đường dẫn) nếu kích thước khai báo nhỏ — không
đọc nội dung file thường.

Giới hạn trung thực:
  - Ngưỡng (``DEFAULT_MAX_*``) là giá trị SIM hợp lý cho vertical slice này,
    KHÔNG phải số đã chốt sản phẩm — pin số thật cần quyết định theo dung
    lượng đĩa máy baseline + corpus thật (xem 04_KIEN_TRUC_QA.md §4: "không
    đưa số giả trong marketing").
  - Với TAR nén (``.tar.gz``/``.tar.bz2``/``.tar.xz``), liệt kê entry vẫn
    cần giải mã tuần tự qua từng header (TAR không có central directory như
    ZIP) — công cụ bỏ (``break``) NGAY khi vượt ngưỡng tổng/dung lượng/số
    mục, nên KHÔNG giải mã toàn bộ một tar.gz bomb cố ý làm rất dài, nhưng
    vẫn phải đọc tới điểm vượt ngưỡng đó (không né được 100% CPU của một
    bomb rất "tinh vi" ngay từ byte đầu — xem ``assess_tar``).
  - Phát hiện "nested archive" (một entry .zip/.tar bên trong) CHỈ theo
    TÊN đuôi — KHÔNG mở xuống để quét sâu (mở xuống đúng là một cách khác
    để tự biến thành nạn nhân zip-bomb lồng).
  - KHÔNG phải virus scanner — không quét nội dung file để tìm mã độc, chỉ
    quét CẤU TRÚC archive (bomb/traversal/escape/số lượng).
"""

from __future__ import annotations

import os
import posixpath
import re
import stat
import tarfile
import zipfile
from dataclasses import dataclass, field

__all__ = [
    "DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES",
    "DEFAULT_MAX_COMPRESSION_RATIO",
    "DEFAULT_MAX_SINGLE_ENTRY_BYTES",
    "DEFAULT_MAX_ENTRY_COUNT",
    "ArchiveSafetyReport",
    "is_unsafe_archive_member_path",
    "looks_like_nested_archive",
    "assess_zip",
    "assess_tar",
    "assess_archive",
]

# ---------------------------------------------------------------------------
# Ngưỡng mặc định (SIM — xem giới hạn trung thực ở đầu file).
# ---------------------------------------------------------------------------

DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MiB
DEFAULT_MAX_COMPRESSION_RATIO = 100.0  # 100:1 — DEFLATE lý thuyết tối đa ~1032:1
DEFAULT_MAX_SINGLE_ENTRY_BYTES = 100 * 1024 * 1024  # 100 MiB
DEFAULT_MAX_ENTRY_COUNT = 10_000

_NESTED_ARCHIVE_EXTS = {"zip", "tar", "gz", "tgz", "bz2", "7z", "rar", "xz", "jar"}
_SYMLINK_TARGET_READ_CAP = 4096  # chỉ đọc target symlink nếu khai báo nhỏ hơn mức này
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def is_unsafe_archive_member_path(name: str) -> bool:
    """``True`` nếu ``name`` (tên entry HOẶC target của symlink/hardlink
    trong archive) có dấu hiệu path traversal/absolute path — không an
    toàn để giải vào một thư mục đích theo đường dẫn tương đối.

    Chặn CẢ BA kiểu: ``../`` tương đối, absolute POSIX (``/etc/passwd``),
    absolute Windows (``C:\\...``) — và còn chuẩn hoá bằng
    ``posixpath.normpath`` để bắt cả trường hợp "thoát" khỏi root dù không
    có literal ``..`` lộ liễu (ví dụ nhiều lớp lồng ghép lạ)."""
    if not name:
        return False
    normalized = name.replace("\\", "/")
    if normalized.startswith("/"):
        return True
    if _WINDOWS_DRIVE_RE.match(normalized):
        return True
    if ".." in normalized.split("/"):
        return True
    virtual_root = "/__namios_extract_root__"
    joined = posixpath.normpath(posixpath.join(virtual_root, normalized))
    if joined != virtual_root and not joined.startswith(virtual_root + "/"):
        return True
    return False


def looks_like_nested_archive(name: str) -> bool:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext in _NESTED_ARCHIVE_EXTS


@dataclass
class ArchiveSafetyReport:
    path: str
    archive_kind: str  # "zip" | "tar" | "unknown"
    safe: bool
    entry_count: int
    total_uncompressed_bytes: int
    total_compressed_bytes: int
    compression_ratio: float
    blocked_reasons: list[str] = field(default_factory=list)
    suspicious_entries: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "archive_kind": self.archive_kind,
            "safe": self.safe,
            "entry_count": self.entry_count,
            "total_uncompressed_bytes": self.total_uncompressed_bytes,
            "total_compressed_bytes": self.total_compressed_bytes,
            "compression_ratio": self.compression_ratio,
            "blocked_reasons": list(self.blocked_reasons),
            "suspicious_entries": list(self.suspicious_entries),
            "notes": list(self.notes),
            "errors": list(self.errors),
        }

    def to_text_vi(self) -> str:
        lines = [
            "=== BÁO CÁO ARCHIVE SAFETY (NaMiOS, PL20) ===",
            f"Tệp: {self.path}",
            f"Loại archive: {self.archive_kind}",
            f"Số entry: {self.entry_count}",
            f"Tổng dung lượng giải nén (khai báo): {self.total_uncompressed_bytes:,} byte",
            f"Tổng dung lượng nén trên đĩa: {self.total_compressed_bytes:,} byte",
            f"Tỉ lệ nén (uncompressed/compressed): {self.compression_ratio:.1f}",
            "",
            "AN TOÀN ĐỂ GIẢI NÉN? " + ("CÓ" if self.safe else "KHÔNG — BỊ CHẶN"),
        ]
        for r in self.blocked_reasons:
            lines.append(f"  ! lý do chặn: {r}")
        for s in self.suspicious_entries:
            lines.append(f"  ! entry nghi vấn: {s}")
        for n in self.notes:
            lines.append(f"  * {n}")
        for e in self.errors:
            lines.append(f"  !! lỗi khi quét: {e}")
        return "\n".join(lines)


def _finalize(
    path: str, archive_kind: str, entry_count: int, total_uncompressed: int, total_compressed: int,
    blocked_reasons: list[str], suspicious: list[str], notes: list[str], errors: list[str],
) -> ArchiveSafetyReport:
    if total_compressed > 0:
        ratio = total_uncompressed / total_compressed
    elif total_uncompressed > 0:
        ratio = float("inf")
    else:
        ratio = 1.0
    safe = not blocked_reasons and not suspicious and not errors
    return ArchiveSafetyReport(
        path=path, archive_kind=archive_kind, safe=safe, entry_count=entry_count,
        total_uncompressed_bytes=total_uncompressed, total_compressed_bytes=total_compressed,
        compression_ratio=ratio, blocked_reasons=blocked_reasons, suspicious_entries=suspicious,
        notes=notes, errors=errors,
    )


def assess_zip(
    path: str,
    *,
    max_total_uncompressed_bytes: int = DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES,
    max_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
    max_single_entry_bytes: int = DEFAULT_MAX_SINGLE_ENTRY_BYTES,
    max_entry_count: int = DEFAULT_MAX_ENTRY_COUNT,
) -> ArchiveSafetyReport:
    """Quét một ZIP CHỈ QUA CENTRAL DIRECTORY (``infolist()`` — đọc metadata
    O(số entry), không giải nén bất kỳ byte nội dung nào, trừ vài byte target
    của symlink nhỏ để kiểm escape)."""
    blocked_reasons: list[str] = []
    suspicious: list[str] = []
    notes: list[str] = []
    errors: list[str] = []

    try:
        is_zip = zipfile.is_zipfile(path)
    except OSError as exc:
        errors.append(f"không đọc được tệp: {exc}")
        return _finalize(path, "unknown", 0, 0, 0, blocked_reasons, suspicious, notes, errors)
    if not is_zip:
        errors.append("tệp không phải ZIP hợp lệ (is_zipfile=False) — có thể hỏng/không phải ZIP thật.")
        return _finalize(path, "zip", 0, 0, 0, ["not_a_valid_zip"], suspicious, notes, errors)

    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        errors.append(f"ZIP báo hợp lệ ở is_zipfile() nhưng mở lỗi (central directory hỏng?): {exc}")
        return _finalize(path, "zip", 0, 0, 0, ["corrupt_central_directory"], suspicious, notes, errors)

    try:
        with zf:
            try:
                infos = zf.infolist()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"không đọc được danh sách entry: {exc!r}")
                return _finalize(path, "zip", 0, 0, 0, blocked_reasons, suspicious, notes, errors)

            entry_count = len(infos)
            if entry_count > max_entry_count:
                blocked_reasons.append(f"entry_count_exceeded:{entry_count}>{max_entry_count}")

            total_uncompressed = 0
            total_compressed = 0
            for info in infos:
                total_uncompressed += max(info.file_size, 0)
                total_compressed += max(info.compress_size, 0)

                if info.file_size > max_single_entry_bytes:
                    blocked_reasons.append(
                        f"single_entry_too_large:{info.filename}:{info.file_size}>{max_single_entry_bytes}"
                    )

                if is_unsafe_archive_member_path(info.filename):
                    suspicious.append(f"path_traversal:{info.filename}")

                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if unix_mode and stat.S_ISLNK(unix_mode):
                    if info.file_size <= _SYMLINK_TARGET_READ_CAP:
                        try:
                            target = zf.read(info).decode("utf-8", errors="replace")
                        except Exception as exc:  # noqa: BLE001
                            target = ""
                            notes.append(f"không đọc được target symlink '{info.filename}': {exc!r}")
                        if is_unsafe_archive_member_path(target):
                            suspicious.append(f"symlink_escape:{info.filename}->{target}")
                    else:
                        suspicious.append(
                            f"symlink_target_too_large_to_verify_safely:{info.filename}:{info.file_size}"
                        )

                if looks_like_nested_archive(info.filename):
                    notes.append(
                        f"entry nén lồng (không mở sâu để tránh bomb lồng): {info.filename}"
                    )

                if total_uncompressed > max_total_uncompressed_bytes:
                    blocked_reasons.append(
                        f"total_uncompressed_exceeded:{total_uncompressed}>{max_total_uncompressed_bytes}"
                    )
                    notes.append(
                        "dừng cộng dồn sớm sau khi vượt ngưỡng tổng dung lượng giải nén "
                        "(không cần đọc hết entry còn lại để biết đã KHÔNG an toàn)."
                    )
                    break

            compressed_ratio_basis = total_compressed if total_compressed > 0 else os.path.getsize(path)
            ratio = (
                total_uncompressed / compressed_ratio_basis
                if compressed_ratio_basis > 0
                else (float("inf") if total_uncompressed > 0 else 1.0)
            )
            if ratio > max_ratio:
                blocked_reasons.append(f"compression_ratio_exceeded:{ratio:.1f}>{max_ratio}")
    except Exception as exc:  # noqa: BLE001 — không để một lỗi quét làm crash cả tiến trình gọi
        errors.append(f"lỗi khi quét ZIP: {exc!r}")
        return _finalize(path, "zip", 0, 0, 0, blocked_reasons, suspicious, notes, errors)

    return _finalize(
        path, "zip", entry_count, total_uncompressed, total_compressed,
        blocked_reasons, suspicious, notes, errors,
    )


def assess_tar(
    path: str,
    *,
    max_total_uncompressed_bytes: int = DEFAULT_MAX_TOTAL_UNCOMPRESSED_BYTES,
    max_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
    max_single_entry_bytes: int = DEFAULT_MAX_SINGLE_ENTRY_BYTES,
    max_entry_count: int = DEFAULT_MAX_ENTRY_COUNT,
) -> ArchiveSafetyReport:
    """Quét TAR (thường/.gz/.bz2/.xz tự nhận qua ``mode="r:*"``) bằng cách
    DUYỆT LẦN LƯỢT từng header (``for member in tar:`` — API tarfile đọc
    LƯỜI từng entry một, không đọc trước toàn bộ archive), dừng SỚM ngay
    khi vượt bất kỳ ngưỡng nào. KHÔNG gọi ``extractall``/``extract``."""
    blocked_reasons: list[str] = []
    suspicious: list[str] = []
    notes: list[str] = []
    errors: list[str] = []

    try:
        compressed_size_on_disk = os.path.getsize(path)
    except OSError as exc:
        errors.append(f"không đọc được kích thước tệp: {exc}")
        return _finalize(path, "tar", 0, 0, 0, blocked_reasons, suspicious, notes, errors)

    try:
        tf = tarfile.open(path, mode="r:*")
    except tarfile.ReadError as exc:
        errors.append(f"không mở được TAR (hỏng hoặc không phải TAR?): {exc}")
        return _finalize(path, "tar", 0, 0, compressed_size_on_disk, ["corrupt_or_not_tar"], suspicious, notes, errors)
    except OSError as exc:
        errors.append(f"không đọc được tệp: {exc}")
        return _finalize(path, "tar", 0, 0, compressed_size_on_disk, blocked_reasons, suspicious, notes, errors)

    entry_count = 0
    total_uncompressed = 0
    try:
        for member in tf:
            entry_count += 1
            if entry_count > max_entry_count:
                blocked_reasons.append(f"entry_count_exceeded:{entry_count}>{max_entry_count}")
                break

            size = max(member.size or 0, 0)
            total_uncompressed += size
            if size > max_single_entry_bytes:
                blocked_reasons.append(f"single_entry_too_large:{member.name}:{size}>{max_single_entry_bytes}")

            if is_unsafe_archive_member_path(member.name):
                suspicious.append(f"path_traversal:{member.name}")

            if member.issym() or member.islnk():
                if is_unsafe_archive_member_path(member.linkname):
                    suspicious.append(f"symlink_escape:{member.name}->{member.linkname}")

            if looks_like_nested_archive(member.name):
                notes.append(f"entry nén lồng (không mở sâu để tránh bomb lồng): {member.name}")

            if total_uncompressed > max_total_uncompressed_bytes:
                blocked_reasons.append(
                    f"total_uncompressed_exceeded:{total_uncompressed}>{max_total_uncompressed_bytes}"
                )
                notes.append("dừng duyệt sớm sau khi vượt ngưỡng tổng dung lượng giải nén.")
                break
    except Exception as exc:  # noqa: BLE001
        errors.append(f"lỗi khi duyệt TAR: {exc!r}")
        blocked_reasons.append("scan_error")
    finally:
        try:
            tf.close()
        except Exception:  # noqa: BLE001
            pass

    ratio = (
        total_uncompressed / compressed_size_on_disk
        if compressed_size_on_disk > 0
        else (float("inf") if total_uncompressed > 0 else 1.0)
    )
    if ratio > max_ratio:
        blocked_reasons.append(f"compression_ratio_exceeded:{ratio:.1f}>{max_ratio}")

    return _finalize(
        path, "tar", entry_count, total_uncompressed, compressed_size_on_disk,
        blocked_reasons, suspicious, notes, errors,
    )


def assess_archive(path: str, **kwargs) -> ArchiveSafetyReport:
    """Dò ZIP hay TAR rồi gọi hàm quét phù hợp; trả report "unknown" nếu
    không khớp cả hai (gọi nhầm hàm trên một tệp không phải archive)."""
    try:
        if zipfile.is_zipfile(path):
            return assess_zip(path, **kwargs)
    except OSError:
        pass
    try:
        if tarfile.is_tarfile(path):
            return assess_tar(path, **kwargs)
    except OSError:
        pass
    return ArchiveSafetyReport(
        path=path, archive_kind="unknown", safe=False, entry_count=0,
        total_uncompressed_bytes=0, total_compressed_bytes=0, compression_ratio=1.0,
        blocked_reasons=["not_a_recognized_archive"], suspicious_entries=[], notes=[],
        errors=["tệp không khớp ZIP hoặc TAR — không có gì để giải nén an toàn."],
    )
