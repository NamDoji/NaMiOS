"""Mã lỗi ổn định cho ``namios_ux`` (Phụ lục 12, UX12-001..048).

Giống quy ước ``namios_sys``/``namios_e08``/...: enum ``(str, Enum)``, chuỗi
KHÔNG đổi sau phát hành (machine-readable, không đi qua ``t()``).
"""

from __future__ import annotations

from enum import Enum

__all__ = ["UxErrorCode"]


class UxErrorCode(str, Enum):
    """Mã lỗi machine-readable cho tầng thiết kế UX (Phụ lục 12)."""

    # Registry phím tắt (UX12-019/021/024)
    E_UX_SHORTCUT_CONFLICT = "E_UX_SHORTCUT_CONFLICT"
    E_UX_SHORTCUT_P0_SYSTEM_CONFLICT = "E_UX_SHORTCUT_P0_SYSTEM_CONFLICT"
    E_UX_SHORTCUT_UNKNOWN_ACTION = "E_UX_SHORTCUT_UNKNOWN_ACTION"
    E_UX_SHORTCUT_NOT_OVERRIDABLE = "E_UX_SHORTCUT_NOT_OVERRIDABLE"
    E_UX_SHORTCUT_CLAIMED_BY_APP = "E_UX_SHORTCUT_CLAIMED_BY_APP"
    E_UX_SHORTCUT_COMBO_TAKEN = "E_UX_SHORTCUT_COMBO_TAKEN"
    E_UX_SHORTCUT_UNSAFE_ACTION = "E_UX_SHORTCUT_UNSAFE_ACTION"
    E_UX_SHORTCUT_INVALID_COMBO = "E_UX_SHORTCUT_INVALID_COMBO"

    # Hình nền (UX12-025..032/046)
    E_UX_WALLPAPER_MISSING_TITLE = "E_UX_WALLPAPER_MISSING_TITLE"
    E_UX_WALLPAPER_MISSING_LOCATION = "E_UX_WALLPAPER_MISSING_LOCATION"
    E_UX_WALLPAPER_MISSING_AUTHOR = "E_UX_WALLPAPER_MISSING_AUTHOR"
    E_UX_WALLPAPER_MISSING_LICENSE = "E_UX_WALLPAPER_MISSING_LICENSE"
    E_UX_WALLPAPER_MISSING_RIGHTS_EVIDENCE = "E_UX_WALLPAPER_MISSING_RIGHTS_EVIDENCE"
    E_UX_WALLPAPER_MISSING_SHA256 = "E_UX_WALLPAPER_MISSING_SHA256"
    E_UX_WALLPAPER_INVALID_SHA256 = "E_UX_WALLPAPER_INVALID_SHA256"
    E_UX_WALLPAPER_MISSING_VARIANTS = "E_UX_WALLPAPER_MISSING_VARIANTS"
    E_UX_WALLPAPER_AI_UNDISCLOSED = "E_UX_WALLPAPER_AI_UNDISCLOSED"

    # Design token / tương phản màu (UX12 §3.2 [4]).
    # ĐẶT TÊN "COLOR" chứ không phải "TOKEN" ở đây có chủ đích: ruff S105
    # ("possible hardcoded password") coi chuỗi tên hằng chứa "token" là nghi
    # vấn — tránh false-positive mà không cần per-file-ignore trong pyproject.
    E_UX_COLOR_CONTRAST_FAIL = "E_UX_COLOR_CONTRAST_FAIL"
    E_UX_COLOR_INVALID_HEX = "E_UX_COLOR_INVALID_HEX"

    # Glossary tiếng Việt (UX12-037)
    E_UX_GLOSSARY_MISSING_TERM = "E_UX_GLOSSARY_MISSING_TERM"
