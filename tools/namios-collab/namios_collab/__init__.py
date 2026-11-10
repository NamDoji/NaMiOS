# -*- coding: utf-8 -*-
"""namios_collab — NaMiCollab Giai đoạn 1: prototype logic (lock/conflict/history).

Đọc TRƯỚC: ``docs/specs/namioffice-v2/03_MAIL_NOTES_FORMS_COLLAB.md`` §4 và
``docs/collab/ADR-0023-namicollab.md``.

Ba module độc lập, không server, không mạng, chạy được ở bất kỳ máy có
Python 3.11+ (chỉ dùng thư viện chuẩn):

  - ``lock_manager``      — khóa advisory exclusive/shared trên một path,
    sidecar JSON, phát hiện stale lock.
  - ``conflict_detector`` — so base-hash/current-hash/new-hash để phân loại
    clean / needs_merge / conflict.
  - ``version_store``     — lịch sử bản cục bộ (snapshot/list/restore có
    verify hash, không bao giờ ghi đè mà không chụp bản an toàn trước).

Trạng thái: ``partial`` — logic đã có pytest pass trên filesystem cục bộ
(xem ``tools/namios-collab/tests/``); CHƯA test trên SMB/WebDAV server thật,
CHƯA nối vào LibreOffice/Dolphin/NaMiOffice UI. Xem
``docs/collab/NAMICOLLAB-PHASE-MATRIX.md`` cho C-level trung thực.
"""
from __future__ import annotations

from namios_collab.conflict_detector import (
    ConflictReport,
    ConflictStatus,
    detect,
    detect_from_disk,
)
from namios_collab.lock_manager import (
    LockConflictError,
    LockError,
    LockHandle,
    LockHolder,
    LockManager,
    LockMode,
    LockNotHeldError,
    LockStatus,
)
from namios_collab.version_store import (
    LocalVersionHistory,
    RestoreVerificationError,
    VersionEntry,
    VersionNotFoundError,
    VersionStoreError,
)

__all__ = [
    "ConflictReport",
    "ConflictStatus",
    "detect",
    "detect_from_disk",
    "LockConflictError",
    "LockError",
    "LockHandle",
    "LockHolder",
    "LockManager",
    "LockMode",
    "LockNotHeldError",
    "LockStatus",
    "LocalVersionHistory",
    "RestoreVerificationError",
    "VersionEntry",
    "VersionNotFoundError",
    "VersionStoreError",
]
