"""NaMiOS — Phụ lục 12 (UX12-001..048): thiết kế giao diện, phím tắt, hình nền.

``namios_ux`` là lõi honest-core LÀM-ĐƯỢC-TẠI-CHỖ cho phần DỮ LIỆU/LOGIC thuần
của Phụ lục 12 — kiểm được bằng test, KHÔNG phải framework UI/Storybook/nghiên
cứu người dùng thật. TÁI DÙNG (không fork): ``namios_sys`` (``data_authority``
— phím tắt không thành lệnh từ nội dung tài liệu), ``namios_e08.actuator``
(tập forbidden-tool-markers cho UX12-024), và ``namios_i18n`` (song ngữ VI/EN +
glossary UX12-037 đăng ký qua ``_i18n.py``).

Bốn mảnh honest-core:
  - ``shortcuts``: registry phím tắt (``ShortcutBinding``), phát hiện xung đột
    (UX12-019), tuỳ chỉnh/reset có kiểm soát (UX12-021), chặn phím tắt vượt
    quyền fail-closed (UX12-024).
  - ``wallpaper``: hợp đồng ``WallpaperEntry`` + gate fail-closed đóng gói
    (UX12-026/031/046) — KHÔNG đoán quyền sử dụng.
  - ``tokens``: ``DesignToken`` + công thức WCAG relative luminance/contrast
    ratio tự viết (UX12 §3.2 [4]) để gate cặp màu text/surface.
  - ``glossary``: glossary tiếng Việt thống nhất (UX12-037), TÁI DÙNG
    ``namios_i18n`` làm kho thuật ngữ (không dựng kho song song).

Phần cần Figma/Storybook/máy pilot/nghiên cứu người dùng thật/hội đồng nghiệm
thu (UX12-001..018/022/023/033..036/038..045/047/048, phần lớn §4 "Đầu ra
Claude Code phải bàn giao") = BLOCKED, ngoài phạm vi module dữ liệu này — xem
``docs/specs/PHU-LUC-12-UX12-MAPPING.md``.
"""

from __future__ import annotations

from namios_ux import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_ux._errors import UxErrorCode
from namios_ux.glossary import (
    GLOSSARY_NAMESPACE,
    GLOSSARY_TERM_IDS,
    REQUIRED_GLOSSARY_TERMS,
    load_glossary,
    missing_required_terms,
)
from namios_ux.shortcuts import (
    SHORTCUT_FORBIDDEN_MARKERS,
    OverrideResult,
    PLevel,
    ShortcutAction,
    ShortcutBinding,
    ShortcutConflict,
    ShortcutScope,
    detect_conflicts,
    has_blocking_conflict,
    resolve_override,
    shortcut_action_is_safe,
)
from namios_ux.tokens import (
    WCAG_LARGE_TEXT_MIN_RATIO,
    WCAG_NORMAL_TEXT_MIN_RATIO,
    DesignToken,
    TokenCategory,
    contrast_ratio,
    meets_wcag,
    token_pair_meets_wcag,
)
from namios_ux.wallpaper import (
    HARD_GATE_CODES,
    WallpaperEntry,
    validate_wallpaper,
    wallpaper_is_shippable,
)

__all__ = [
    "UxErrorCode",
    # shortcuts (UX12-019/020/021/024)
    "ShortcutScope",
    "PLevel",
    "ShortcutBinding",
    "ShortcutAction",
    "ShortcutConflict",
    "OverrideResult",
    "SHORTCUT_FORBIDDEN_MARKERS",
    "detect_conflicts",
    "has_blocking_conflict",
    "resolve_override",
    "shortcut_action_is_safe",
    # wallpaper (UX12-025..032/046)
    "WallpaperEntry",
    "HARD_GATE_CODES",
    "validate_wallpaper",
    "wallpaper_is_shippable",
    # tokens (UX12 §3.2 [4])
    "TokenCategory",
    "DesignToken",
    "WCAG_NORMAL_TEXT_MIN_RATIO",
    "WCAG_LARGE_TEXT_MIN_RATIO",
    "contrast_ratio",
    "meets_wcag",
    "token_pair_meets_wcag",
    # glossary (UX12-037)
    "GLOSSARY_NAMESPACE",
    "GLOSSARY_TERM_IDS",
    "REQUIRED_GLOSSARY_TERMS",
    "load_glossary",
    "missing_required_terms",
]
