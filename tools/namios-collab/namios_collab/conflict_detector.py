# -*- coding: utf-8 -*-
"""NaMiOS — NaMiCollab Giai đoạn 1: Conflict Detector (base-hash vs current).

Đọc TRƯỚC: ``docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md`` §4
("cảnh báo conflict") và ``docs/collab/ADR-0023-namicollab.md`` Giai đoạn 1.

Mô hình ba-chiều kiểu "optimistic concurrency" quen thuộc (git/SMB oplock
đều theo cùng nguyên lý này):

  * ``base_hash``  — hash của file lúc người dùng BẮT ĐẦU sửa (checkout).
  * ``current_hash`` — hash của file TRÊN KHO CHIA SẺ ngay lúc chuẩn bị lưu.
  * ``new_hash`` (tuỳ chọn) — hash của nội dung người dùng ĐANG MUỐN lưu.

Phân loại (``ConflictStatus``):
  * ``CLEAN``        — ``current_hash == base_hash`` (không ai đổi gì từ lúc
    base), HOẶC nội dung mới trùng khớp ``current_hash`` (đổi đã được áp
    dụng rồi, ví dụ hai người lưu cùng một nội dung) ⇒ an toàn để lưu.
  * ``NEEDS_MERGE``  — ``current_hash != base_hash`` NHƯNG định dạng file
    được coi là "có thể merge theo dòng" (text/markdown/CSV/JSON — xem
    ``MERGEABLE_SUFFIXES``) ⇒ CÓ THỂ thử merge ba-chiều (merge thật KHÔNG
    nằm trong module này — xem ADR-0023 Giai đoạn 2/3).
  * ``CONFLICT``     — ``current_hash != base_hash`` VÀ định dạng là
    container nhị phân (ODF/OOXML zip — DOCX/XLSX/PPTX/ODT/ODS/ODP...) ⇒
    KHÔNG tự merge được, người dùng phải chọn giữ bản nào/so sánh thủ công.

Giới hạn trung thực:
  - Module này CHỈ PHÁT HIỆN và PHÂN LOẠI — không tự merge, không tự ghi
    đè, không tự xóa bản nào. Hành động xử lý (giữ bản nào, merge dòng nào)
    là UX/người dùng quyết định ở tầng trên.
  - ``NEEDS_MERGE`` không đồng nghĩa "chắc chắn merge được không mất nội
    dung" — chỉ là định dạng CÓ CƠ HỘI merge theo dòng/cấu trúc văn bản.
    Merge thật (3-way diff) là công cụ khác, chưa viết ở đây.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from namios_collab import _util

# Đuôi file coi là "có thể merge theo dòng" — text thuần hoặc cấu trúc dòng
# rõ ràng. ODF/OOXML (zip nhị phân) CỐ Ý không nằm trong danh sách này.
MERGEABLE_SUFFIXES: frozenset[str] = frozenset(
    {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".yaml", ".yml", ".ini", ".cfg"}
)

# Container nhị phân biết trước (ODF/OOXML) — chỉ để ghi rõ lý do trong
# ``ConflictReport.detail``, KHÔNG dùng để quyết định (quyết định dựa trên
# "không thuộc MERGEABLE_SUFFIXES", đóng-mặc-định an toàn hơn mở-mặc-định).
KNOWN_BINARY_CONTAINER_SUFFIXES: frozenset[str] = frozenset(
    {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp", ".odb", ".pdf"}
)


class ConflictStatus(str, Enum):
    CLEAN = "clean"
    NEEDS_MERGE = "needs_merge"
    CONFLICT = "conflict"


@dataclass
class ConflictReport:
    path: str
    base_hash: str
    current_hash: Optional[str]
    new_hash: Optional[str]
    status: ConflictStatus
    mergeable_format: bool
    detail: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "base_hash": self.base_hash,
            "current_hash": self.current_hash,
            "new_hash": self.new_hash,
            "status": self.status.value,
            "mergeable_format": self.mergeable_format,
            "detail": self.detail,
        }


def is_mergeable_format(path: str) -> bool:
    _root, ext = os.path.splitext(path)
    return ext.lower() in MERGEABLE_SUFFIXES


def compute_hash(path: str) -> str:
    """Hash nội dung file hiện có trên đĩa. Raise ``FileNotFoundError``
    nếu ``path`` không còn tồn tại — caller (``detect_from_disk``) đổi
    thành báo cáo ``CONFLICT`` "đã bị xóa", không để lỗi lan ra ngoài."""
    return _util.sha256_file(path)


def detect(
    path: str,
    base_hash: str,
    current_hash: Optional[str],
    new_hash: Optional[str] = None,
) -> ConflictReport:
    """Phân loại xung đột từ ba hash đã có sẵn (không đọc đĩa — tiện cho
    test và cho trường hợp ``current_hash`` lấy từ nơi khác, ví dụ server
    NaMiCollab Giai đoạn 2 trong tương lai)."""
    mergeable = is_mergeable_format(path)

    if current_hash is None:
        return ConflictReport(
            path=path,
            base_hash=base_hash,
            current_hash=None,
            new_hash=new_hash,
            status=ConflictStatus.CONFLICT,
            mergeable_format=mergeable,
            detail="file không còn tồn tại trên kho chia sẻ (đã bị xóa/di chuyển)",
        )

    if current_hash == base_hash:
        return ConflictReport(
            path=path,
            base_hash=base_hash,
            current_hash=current_hash,
            new_hash=new_hash,
            status=ConflictStatus.CLEAN,
            mergeable_format=mergeable,
            detail="không ai đổi file từ lúc bắt đầu sửa (base == current)",
        )

    if new_hash is not None and new_hash == current_hash:
        return ConflictReport(
            path=path,
            base_hash=base_hash,
            current_hash=current_hash,
            new_hash=new_hash,
            status=ConflictStatus.CLEAN,
            mergeable_format=mergeable,
            detail="nội dung muốn lưu đã khớp bản hiện có trên kho (đổi đã được áp dụng)",
        )

    ext_hint = os.path.splitext(path)[1].lower()
    if mergeable:
        detail = (
            f"file đã bị người khác đổi từ lúc base (đuôi {ext_hint!r} coi là "
            "có thể merge theo dòng — cần công cụ merge ba-chiều, chưa chạy ở đây)"
        )
        status = ConflictStatus.NEEDS_MERGE
    else:
        binary_note = " (container nhị phân đã biết)" if ext_hint in KNOWN_BINARY_CONTAINER_SUFFIXES else ""
        detail = (
            f"file đã bị người khác đổi từ lúc base; đuôi {ext_hint!r}{binary_note} "
            "không merge tự động được — phải chọn giữ bản nào hoặc so sánh thủ công"
        )
        status = ConflictStatus.CONFLICT

    return ConflictReport(
        path=path,
        base_hash=base_hash,
        current_hash=current_hash,
        new_hash=new_hash,
        status=status,
        mergeable_format=mergeable,
        detail=detail,
    )


def detect_from_disk(path: str, base_hash: str, new_hash: Optional[str] = None) -> ConflictReport:
    """Tiện ích: tự đọc ``current_hash`` từ ``path`` trên đĩa rồi gọi
    ``detect``. Không mạng — ``path`` phải đã là file local/SMB/WebDAV đã
    mount (Giai đoạn 1 không tự nói chuyện protocol)."""
    try:
        current_hash = compute_hash(path)
    except FileNotFoundError:
        current_hash = None
    return detect(path, base_hash, current_hash, new_hash)
