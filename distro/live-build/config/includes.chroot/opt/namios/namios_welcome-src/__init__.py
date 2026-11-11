"""``namios_welcome`` — chuyển dữ liệu Windows an toàn + ÁP THẬT mặc định
lần đầu (bộ gõ fcitx5/cỡ chữ Plasma/MIME app mặc định/máy in — xem
``apply_runtime_desktop_settings``), không chỉ ghi ``welcome.json``.

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
    RuntimeApplyOutcome,
    RuntimeApplyReport,
    RuntimeApplyStatus,
    UiScalePercent,
    WelcomeDoneMarker,
    apply_runtime_desktop_settings,
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
    "WelcomeDoneMarker",
    "RuntimeApplyStatus",
    "RuntimeApplyOutcome",
    "RuntimeApplyReport",
    "apply_runtime_desktop_settings",
]
