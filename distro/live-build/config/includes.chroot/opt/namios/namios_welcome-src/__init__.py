"""``namios_welcome`` — chuyển dữ liệu Windows an toàn + áp mặc định lần đầu.

Python thuần (``migrate``/``firstrun``), KHÔNG phụ thuộc GUI. ``ui``/
``__main__`` là wizard PySide6 mỏng chỉ dùng trên desktop thật (UI-005) —
tách khỏi logic để test được không cần GUI (``tests/unit/welcome/``).
"""

from __future__ import annotations

from namios_welcome.firstrun import (
    AppliedConfigReport,
    ConfigApplier,
    FirstRunChoices,
    FirstRunValidationError,
    ImeMethod,
    UiScalePercent,
)
from namios_welcome.migrate import (
    KNOWN_FOLDER_NAMES,
    ConflictEntry,
    DiscoveredFolder,
    MigratedFileEntry,
    MigrationReport,
    SkippedEntry,
    WindowsDataMigrator,
    WindowsVolumeUnsafeError,
)

__all__ = [
    "KNOWN_FOLDER_NAMES",
    "DiscoveredFolder",
    "MigratedFileEntry",
    "SkippedEntry",
    "ConflictEntry",
    "MigrationReport",
    "WindowsVolumeUnsafeError",
    "WindowsDataMigrator",
    "ImeMethod",
    "UiScalePercent",
    "FirstRunChoices",
    "AppliedConfigReport",
    "FirstRunValidationError",
    "ConfigApplier",
]
