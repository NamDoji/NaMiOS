"""``namios_i18n`` — lớp COMMON song ngữ VI/EN dùng chung toàn hệ thống.

Đợt nâng cấp 03/11/2026 (chỉ đạo chủ dự án): mọi chuỗi human-facing của
``namios_cli``/``namios_doctor``/``namios_eco``/``namios_welcome`` (và các
module sau này) PHẢI đi qua ``namios_i18n.t(key, ...)`` — xem hợp đồng đầy
đủ ở ``docs/specs/I18N.md``. Module này KHÔNG phụ thuộc module NaMiOS khác.

Tiếng Việt là ngôn ngữ MẶC ĐỊNH (FACT VN-001); tiếng Anh chạy SONG SONG, có
thể chọn qua ``lang=Lang.EN`` hoặc biến môi trường ``NAMIOS_LANG=en``.
Trường máy đọc (``error.code``, ``status``, exit code, JSON key) KHÔNG đi
qua lớp dịch này.
"""

from __future__ import annotations

from namios_i18n.translator import (
    DEFAULT_LANG,
    ENV_VAR,
    Lang,
    Translator,
    add_catalog,
    get_default_translator,
    has_key,
    resolve_lang,
    t,
)

__all__ = [
    "ENV_VAR",
    "DEFAULT_LANG",
    "Lang",
    "Translator",
    "resolve_lang",
    "add_catalog",
    "has_key",
    "t",
    "get_default_translator",
]
