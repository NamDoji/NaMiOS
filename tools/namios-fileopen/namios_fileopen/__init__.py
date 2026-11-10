# -*- coding: utf-8 -*-
"""namios_fileopen — PL20 vertical slice: MIME routing + archive safety.

Đọc TRƯỚC: ``docs/specs/namios-pl20/02_MO_TEP_VA_DINH_DANG.md`` và
``docs/specs/namios-pl20/04_KIEN_TRUC_QA.md`` (bảng F20-01..F20-12, routing
file/plugin contract, bảo mật định dạng).

Hai module:
  * ``mime_router`` — dò MIME theo NỘI DUNG (magic bytes + soi ZIP nông),
    phát hiện lệch đuôi/nội dung + đuôi kép ngụy trang, chọn app NaMiOS
    theo registry nội bộ, hỗ trợ "đổi app mặc định" (``FileAssociationRegistry``).
  * ``archive_safety`` — quét ZIP/TAR CHỈ ĐỌC METADATA để chặn zip-bomb
    (tỉ lệ nén/tổng dung lượng/số entry) và path traversal/symlink escape,
    KHÔNG BAO GIỜ gọi ``extractall``.

Đây là LOGIC THUẦN (dataclass + stdlib ``zipfile``/``tarfile``) — KHÔNG mở
app NaMiOffice/NaMiPDF/NaMiArchive/NaMiImages/NaMiMedia thật, KHÔNG nối vào
Dolphin/NaMiFiles double-click thật, KHÔNG phát âm thanh/video thật. Xem
``README.md`` cùng thư mục để biết rõ phần nào là sim (kiểm được bằng
pytest ở đây) và phần nào cần máy pilot thật (desktop/Dolphin/codec)."""

from __future__ import annotations

from .archive_safety import (
    ArchiveSafetyReport,
    assess_archive,
    assess_tar,
    assess_zip,
    is_unsafe_archive_member_path,
)
from .mime_router import (
    APP_CATALOG,
    CapabilityReport,
    FileAssociationRegistry,
    route_file,
    sniff_content_kind,
)

__all__ = [
    "route_file",
    "sniff_content_kind",
    "CapabilityReport",
    "FileAssociationRegistry",
    "APP_CATALOG",
    "assess_zip",
    "assess_tar",
    "assess_archive",
    "is_unsafe_archive_member_path",
    "ArchiveSafetyReport",
]
