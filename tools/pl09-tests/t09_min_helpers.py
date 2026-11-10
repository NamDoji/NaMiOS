# -*- coding: utf-8 -*-
"""Helper TỐI THIỂU cho bộ test T09 (Phụ lục 09, docs/specs/namios-pl09/).

Mục đích duy nhất của file này: che các ô mà §3 (T09-A..T09-J) đòi kiểm,
nhưng KHÔNG có module thật nào trong ``src/`` hoặc ``tools/`` hiện thực —
cụ thể là:

  * T09-C — phát hiện tệp USB loại thực/đuôi kép (chưa có engine quét thật,
    VN09-028: "quét tùy chính sách khi mount... kiểm loại file thực và đuôi
    kép"). ``classify_usb_file`` CHỈ phân loại (đọc byte đầu + tên tệp) —
    không mount/không autorun/không thực thi gì.
  * T09-E — chính sách PHẠM VI thư mục của một Wine capsule (VN09-031: "chỉ
    mount thư mục cần cho tác vụ; không map toàn bộ home mặc định"). Repo
    này CHƯA có bwrap/namespace thật cho Wine; ``wine_capsule_path_allowed``
    mô phỏng ĐÚNG quyết định allow/deny containment mà một bind-mount thật
    sẽ phải tuân theo.
  * T09-F — vùng cách ly (quarantine) có ID + quyền IT + điều tra + audit
    (VN09-029/030). Repo CHƯA có tích hợp ClamAV/engine quét thật;
    ``QuarantineStore`` mô hình hoá ĐÚNG quy trình (không xoá vô điều kiện).
  * T09-H — hợp đồng accessibility (VN09-006/009/010). Đây CHỈ là khẳng định
    ở MỨC HỢP ĐỒNG/CONFIG (các hành trình cốt lõi PHẢI luôn trong tập
    "khả dụng bằng bàn phím" bất kể cờ accessibility nào bật) — KHÔNG phải
    đo bằng screen reader/automation thật trên desktop thật.
  * T09-J — sao lưu theo phiên bản + khôi phục đúng hash + không đè bản mới
    hơn khi chưa xem trước, cộng ngưỡng phát hiện biến động tệp hàng loạt
    (VN09-032). Repo CHƯA có engine backup thật (btrfs snapshot/borg/restic).
    ``BackupStore``/``bulk_change_rate_exceeds_threshold`` mô hình hoá ĐÚNG
    3 bất biến nghiệm thu, KHÔNG mã hoá/giải mã file thật, KHÔNG đụng ổ đĩa
    ngoài ``tmp_path`` của test.

Mọi hàm/ lớp ở đây CHỈ LÀ LOGIC THUẦN PYTHON (dataclass + so sánh chuỗi/số) —
KHÔNG gọi subprocess, KHÔNG I/O ngoài những gì caller tự truyền vào, KHÔNG mô
phỏng phần cứng (USB/ransomware/scanner) thật. Xác minh ĐẦY ĐỦ các case này
cần máy pilot thật (xem phần "sim-only vs need-real-HW" trong báo cáo tổng
kết kèm bộ test này).
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field, replace

__all__ = [
    # T09-C
    "EXECUTABLE_EXTENSIONS",
    "DISGUISE_EXTENSIONS",
    "FileTypeVerdict",
    "sniff_magic",
    "classify_usb_file",
    # T09-E
    "wine_capsule_path_allowed",
    # T09-F
    "QuarantineRecord",
    "QuarantineStore",
    # T09-H
    "AccessibilityFlags",
    "CORE_KEYBOARD_JOURNEYS",
    "keyboard_reachable_journeys",
    "effective_animation_ms",
    # T09-J
    "BackupSnapshot",
    "RestoreResult",
    "BackupStore",
    "bulk_change_rate_exceeds_threshold",
]


# --------------------------------------------------------------------------- #
# T09-C — USB: đuôi kép / loại tệp thực (VN09-028)                            #
# --------------------------------------------------------------------------- #

#: Đuôi CUỐI bị coi là "có thể thực thi" — không tự chạy, chỉ dùng để gắn cờ.
EXECUTABLE_EXTENSIONS: frozenset[str] = frozenset(
    {"exe", "scr", "com", "bat", "cmd", "msi", "pif", "jar", "vbs", "js", "ps1", "wsf"}
)

#: Đuôi "trông lành" hay bị dùng làm lớp ngụy trang NGAY TRƯỚC đuôi thực thi
#: (vd ``bao_cao.pdf.exe``).
DISGUISE_EXTENSIONS: frozenset[str] = frozenset(
    {"pdf", "docx", "doc", "xlsx", "xls", "jpg", "jpeg", "png", "txt", "zip", "mp3", "mp4"}
)


@dataclass(frozen=True)
class FileTypeVerdict:
    """Kết quả phân loại MỘT tệp (không mount/không chạy)."""

    filename: str
    claimed_ext: str
    real_kind: str  # "pe_executable" | "pdf" | "jpeg" | "text" | "unknown"
    double_extension_disguise: bool
    type_mismatch: bool  # đuôi NGƯỢC với magic bytes thật (vd ".pdf" nhưng magic MZ)
    block_execution: bool
    safe_to_preview: bool
    warning_vi: str = ""


def sniff_magic(head_bytes: bytes) -> str:
    """Dò loại tệp THẬT từ vài byte đầu (không tin đuôi tệp)."""

    if head_bytes.startswith(b"MZ"):
        return "pe_executable"
    if head_bytes.startswith(b"%PDF"):
        return "pdf"
    if head_bytes[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if not head_bytes:
        return "unknown"
    try:
        head_bytes.decode("utf-8")
        return "text"
    except UnicodeDecodeError:
        return "unknown"


def classify_usb_file(filename: str, head_bytes: bytes = b"") -> FileTypeVerdict:
    """Phân loại một tệp (từ USB hoặc bất kỳ nguồn chưa tin cậy) — CHỈ ĐỌC,
    không thực thi, không autorun (VN09-028 nghiệm thu: "``Hoa_don.pdf.exe``
    không chạy qua preview"). Dò ĐUÔI KÉP (tên có đuôi "lành" ngay trước đuôi
    thực thi) VÀ dò LOẠI THỰC qua magic bytes (bắt cả trường hợp không có
    đuôi kép nhưng nội dung thật là PE)."""

    exts = [p.lower() for p in filename.split(".")[1:]]
    last_ext = exts[-1] if exts else ""
    disguise_ext = exts[-2] if len(exts) >= 2 else ""

    double_extension_disguise = bool(
        disguise_ext in DISGUISE_EXTENSIONS and last_ext in EXECUTABLE_EXTENSIONS
    )

    real_kind = sniff_magic(head_bytes)
    claimed_ext = disguise_ext if double_extension_disguise else last_ext

    # Lệch loại: đuôi khai KHÔNG phải thực thi nhưng magic bytes lại là PE
    # thật (vd đổi tên "virus.exe" thành "invoice.pdf" không đổi nội dung).
    type_mismatch = bool(real_kind == "pe_executable" and last_ext not in EXECUTABLE_EXTENSIONS)

    block_execution = bool(
        last_ext in EXECUTABLE_EXTENSIONS or real_kind == "pe_executable" or double_extension_disguise
    )
    safe_to_preview = bool(
        not block_execution and not type_mismatch and real_kind in ("pdf", "jpeg", "text")
    )

    warning_vi = ""
    if double_extension_disguise:
        warning_vi = (
            f"Tệp '{filename}' có ĐUÔI KÉP đáng ngờ (.{disguise_ext}.{last_ext}) — "
            "có thể là tệp thực thi ngụy trang, KHÔNG mở trực tiếp."
        )
    elif type_mismatch:
        warning_vi = (
            f"Tệp '{filename}' khai đuôi '.{last_ext}' nhưng nội dung thật là chương trình "
            "thực thi (PE) — KHÔNG mở trực tiếp."
        )
    elif block_execution:
        warning_vi = f"Tệp '{filename}' là tệp thực thi/script — không tự chạy."

    return FileTypeVerdict(
        filename=filename,
        claimed_ext=claimed_ext,
        real_kind=real_kind,
        double_extension_disguise=double_extension_disguise,
        type_mismatch=type_mismatch,
        block_execution=block_execution,
        safe_to_preview=safe_to_preview,
        warning_vi=warning_vi,
    )


# --------------------------------------------------------------------------- #
# T09-E — Phạm vi thư mục capsule Wine (VN09-031)                             #
# --------------------------------------------------------------------------- #


def wine_capsule_path_allowed(granted_dirs: tuple[str, ...], requested_path: str) -> bool:
    """``True`` CHỈ khi ``requested_path`` nằm trong (hoặc LÀ) một trong các
    thư mục đã cấp cho capsule (VN09-031: "chỉ mount thư mục cần cho tác vụ;
    không map toàn bộ home mặc định"). Containment theo đường dẫn TUYỆT ĐỐI
    đã chuẩn hoá (``os.path.abspath`` — gỡ ``..``/``.``) để một yêu cầu kiểu
    ``granted/../../etc/passwd`` không "leo" ra ngoài phạm vi đã cấp. Danh
    sách ``granted_dirs`` RỖNG → luôn ``False`` (deny-by-default, không có
    capsule nào được mount full home ngầm)."""

    if not granted_dirs:
        return False
    req_abs = os.path.abspath(requested_path)
    for granted in granted_dirs:
        g_abs = os.path.abspath(granted)
        if req_abs == g_abs or req_abs.startswith(g_abs + os.sep):
            return True
    return False


# --------------------------------------------------------------------------- #
# T09-F — Quarantine có ID + quyền IT + điều tra + audit (VN09-029/030)       #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class QuarantineRecord:
    quarantine_id: str
    original_path: str
    detected_as: str
    quarantined_at: str
    restored: bool = False
    deleted: bool = False
    audit_log: tuple[str, ...] = ()


@dataclass
class QuarantineStore:
    """Mô hình vùng cách ly tối thiểu (VN09-029/030 nghiệm thu: "Quarantine
    có ID, quyền IT, điều tra, restore và audit; không xóa vô điều kiện").
    KHÔNG có đường nào xoá mà không qua ``request_delete(..., it_permission=
    True)`` tường minh — ``it_permission`` không có giá trị mặc định, buộc
    caller phải tự quyết định, không có "xoá nhanh" ngầm."""

    _items: dict[str, QuarantineRecord] = field(default_factory=dict)
    _seq: int = 0

    def quarantine(self, original_path: str, detected_as: str, *, at: str) -> QuarantineRecord:
        self._seq += 1
        qid = f"QR-{self._seq:04d}"
        rec = QuarantineRecord(
            quarantine_id=qid,
            original_path=original_path,
            detected_as=detected_as,
            quarantined_at=at,
            audit_log=(f"{at} cách ly: nghi {detected_as}",),
        )
        self._items[qid] = rec
        return rec

    def get(self, quarantine_id: str) -> QuarantineRecord | None:
        return self._items.get(quarantine_id)

    def request_delete(self, quarantine_id: str, *, it_permission: bool, at: str) -> QuarantineRecord:
        """Xoá VĨNH VIỄN khỏi quarantine — CẦN quyền IT tường minh. Thiếu
        quyền → ``PermissionError`` (không có nhánh xoá âm thầm)."""

        rec = self._items[quarantine_id]
        if not it_permission:
            raise PermissionError(
                f"{quarantine_id}: cần quyền IT tường minh trước khi xoá vĩnh viễn khỏi quarantine"
            )
        updated = replace(
            rec, deleted=True, audit_log=(*rec.audit_log, f"{at} xoá vĩnh viễn (có quyền IT)")
        )
        self._items[quarantine_id] = updated
        return updated

    def restore(self, quarantine_id: str, *, investigated: bool, at: str) -> QuarantineRecord:
        """Khôi phục một mục bị báo nhầm (false positive) — PHẢI điều tra
        trước (``investigated=True``), không khôi phục mù."""

        rec = self._items[quarantine_id]
        if rec.deleted:
            raise ValueError(f"{quarantine_id}: đã xoá vĩnh viễn — không thể khôi phục")
        if not investigated:
            raise PermissionError(
                f"{quarantine_id}: phải điều tra trước khi khôi phục (không khôi phục mù)"
            )
        updated = replace(
            rec,
            restored=True,
            audit_log=(*rec.audit_log, f"{at} khôi phục sau điều tra (báo nhầm/false positive)"),
        )
        self._items[quarantine_id] = updated
        return updated


# --------------------------------------------------------------------------- #
# T09-H — Hợp đồng accessibility (VN09-006/009/010, MỨC CONFIG/CONTRACT)      #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AccessibilityFlags:
    screen_reader: bool = False
    reduce_motion: bool = False
    keyboard_only: bool = False


#: Hành trình CỐT LÕI phải hoàn tất được bằng bàn phím (VN09-006/009 nghiệm
#: thu: "hoàn thành đăng nhập, kết nối Wi-Fi, cài app và in test bằng bàn
#: phím"; VN09-009: "8/10 người pilot ... đổi Wi-Fi, tìm file, in tài liệu").
CORE_KEYBOARD_JOURNEYS: frozenset[str] = frozenset(
    {
        "complete_onboarding",
        "open_zalo_web",
        "change_wifi",
        "print_test_page",
        "install_app",
    }
)


def keyboard_reachable_journeys(flags: AccessibilityFlags) -> frozenset[str]:
    """HỢP ĐỒNG mức thiết kế: các hành trình CỐT LÕI PHẢI luôn nằm trong tập
    "khả dụng bằng bàn phím" — BẤT KỂ cờ accessibility nào đang bật/tắt (bật
    screen_reader/reduce_motion/keyboard_only không được rút bớt tập này).
    ĐÂY KHÔNG PHẢI kết quả đo bằng screen reader/automation thật trên desktop
    thật — xem đầu file."""

    return CORE_KEYBOARD_JOURNEYS


def effective_animation_ms(flags: AccessibilityFlags, base_ms: int) -> int:
    """VN09-014 nghiệm thu: "chế độ reduce motion bỏ hiệu ứng không cần
    thiết". ``reduce_motion=True`` → 0ms (bỏ hẳn); ngược lại giữ ``base_ms``
    trong khung 120–250ms đã chốt (kẹp hai đầu để không lọt giá trị ngoài
    khung thiết kế)."""

    if flags.reduce_motion:
        return 0
    return max(120, min(250, base_ms))


# --------------------------------------------------------------------------- #
# T09-J — Backup/restore theo hash + ngưỡng ransomware (VN09-032)             #
# --------------------------------------------------------------------------- #


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class BackupSnapshot:
    path: str
    content: bytes
    content_hash: str
    saved_at: str
    saved_mtime: float


@dataclass(frozen=True)
class RestoreResult:
    path: str
    restored: bool
    content_hash: str
    restored_at: str
    skipped_reason: str = ""


class BackupStore:
    """Mô hình tối giản sao lưu theo phiên bản + khôi phục (VN09-032). BA bất
    biến nghiệm thu được mô hình hoá:

      1. Khôi phục xong → hash đúng với bản đã lưu (``content_hash``).
      2. Có mốc THỜI ĐIỂM khôi phục hiển thị (``restored_at``).
      3. KHÔNG đè tệp cục bộ MỚI HƠN bản backup khi chưa xem trước
         (``preview_confirmed``) — trả về lý do rõ ràng, không âm thầm bỏ qua
         và không âm thầm đè.

    Đây là logic THUẦN — không mã hoá/giải mã, không đụng ổ đĩa ngoài những gì
    caller truyền vào qua tham số.
    """

    def __init__(self) -> None:
        self._snapshots: dict[str, BackupSnapshot] = {}

    def save(self, path: str, content: bytes, *, at: str, mtime: float) -> BackupSnapshot:
        snap = BackupSnapshot(
            path=path, content=content, content_hash=_sha256(content), saved_at=at, saved_mtime=mtime
        )
        self._snapshots[path] = snap
        return snap

    def hashes(self) -> dict[str, str]:
        return {p: s.content_hash for p, s in self._snapshots.items()}

    def restore(
        self,
        path: str,
        *,
        local_mtime: float | None,
        now: str,
        preview_confirmed: bool = False,
    ) -> RestoreResult:
        snap = self._snapshots.get(path)
        if snap is None:
            return RestoreResult(
                path=path, restored=False, content_hash="", restored_at="", skipped_reason="no_backup"
            )

        local_is_newer = local_mtime is not None and local_mtime > snap.saved_mtime
        if local_is_newer and not preview_confirmed:
            return RestoreResult(
                path=path,
                restored=False,
                content_hash=snap.content_hash,
                restored_at="",
                skipped_reason="local_newer_needs_preview",
            )

        return RestoreResult(
            path=path, restored=True, content_hash=snap.content_hash, restored_at=now
        )


def bulk_change_rate_exceeds_threshold(
    changed_count: int, window_seconds: float, *, threshold_per_minute: float
) -> bool:
    """VN09-032: "phát hiện biến động tệp hàng loạt bằng quy tắc XÁC ĐỊNH có
    ngưỡng false positive" — tỉ lệ thay đổi/phút vượt ngưỡng → nghi vấn (gợi ý
    tạm dừng tiến trình theo policy, KHÔNG tự xoá/tự quyết định một mình).
    Quy tắc tất định (chia số đếm cho khung thời gian), không gọi SmartAI."""

    if window_seconds <= 0:
        return changed_count > 0
    rate_per_minute = changed_count / (window_seconds / 60.0)
    return rate_per_minute > threshold_per_minute
