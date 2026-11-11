"""Lớp COMMON song ngữ VI/EN dùng chung toàn hệ thống NaMiOS — ``namios_i18n``.

Mục tiêu (đợt nâng cấp 03/11/2026, chỉ đạo chủ dự án): một chỗ DUY NHẤT giữ
toàn bộ chuỗi human-facing, có bản tiếng Việt (mặc định, chin chu) và bản
tiếng Anh song song, đổi ngôn ngữ qua tham số hoặc biến môi trường
``NAMIOS_LANG`` — KHÔNG sửa rải rác từng module.

Ràng buộc BẮT BUỘC (không được vi phạm khi dùng module này):
  - Tiếng Việt LUÔN là mặc định khi không có chỉ định khác (FACT VN-001).
    800 test hiện có của repo giả định chuỗi tiếng Việt y nguyên hiện tại —
    catalog ``locale/vi.json`` PHẢI giữ đúng từng ký tự các chuỗi đó.
  - Trường máy đọc (``error.code``, ``status``, exit code, JSON key) KHÔNG
    bao giờ đi qua ``t()`` — chỉ phần human-readable (``message_vi``, help
    text, label UI, warnings) mới dịch.
  - KHÔNG phụ thuộc module NaMiOS khác (``namios_core``/``namios_cli``/...)
    — ``namios_i18n`` là nền, các module khác import NÓ, không ngược lại.

Cách dùng:
    from namios_i18n import Lang, t, add_catalog

    t("cli.main.error.manifest_load_failed")                 # VI mặc định
    t("cli.main.error.manifest_load_failed", lang=Lang.EN)   # ép EN
    # hoặc: os.environ["NAMIOS_LANG"] = "en" rồi gọi t(...) không kèm lang

    add_catalog(Lang.VI, {"my_module.greeting": "Xin chào {name}"})
    t("my_module.greeting", name="Cường")  # "Xin chào Cường"
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any

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


class Lang(str, Enum):
    """Hai ngôn ngữ hỗ trợ ở M1. VI là mặc định toàn hệ thống (FACT VN-001);
    EN chạy song song, không thay thế."""

    VI = "vi"
    EN = "en"


#: Biến môi trường chọn ngôn ngữ hiệu lực khi không có tham số ``lang`` tường
#: minh (DESIGN — hợp đồng common cho mọi CLI/module đọc cùng một biến).
ENV_VAR = "NAMIOS_LANG"

#: Ngôn ngữ mặc định khi KHÔNG có ``explicit`` và biến môi trường cũng không
#: đặt (hoặc đặt giá trị không nhận diện được) — FACT VN-001.
DEFAULT_LANG = Lang.VI

#: Biến locale POSIX của HỆ THỐNG (theo thứ tự ưu tiên glibc). Dùng để "Tiếng
#: Anh chuẩn theo ngôn ngữ của máy tính" (VN-001, Cuong 06/11): khi không có
#: NAMIOS_LANG, ngôn ngữ app NaMiOS đi theo locale máy — máy đặt vi_VN → tiếng
#: Việt, máy đặt en_US → tiếng Anh. ISO NaMiOS (11/11) mặc định LANG=vi_VN → tiếng Việt.
_SYSTEM_LOCALE_VARS = ("LC_ALL", "LC_MESSAGES", "LANG")

#: Thư mục chứa catalog gốc đóng gói cùng module (``vi.json``/``en.json``).
_LOCALE_DIR = Path(__file__).resolve().parent / "locale"


def _normalize_lang_value(value: str) -> Lang | None:
    """Chuẩn hoá một chuỗi ngôn ngữ thô (có thể có khoảng trắng/hoa-thường
    lẫn lộn) về ``Lang``; trả ``None`` nếu không nhận diện được — KHÔNG
    raise, để caller (env var không tin cậy) luôn có đường rơi về an toàn."""

    try:
        return Lang(value.strip().lower())
    except ValueError:
        return None


def _lang_from_system_locale() -> Lang | None:
    """Suy ngôn ngữ từ locale POSIX của máy (``LC_ALL``/``LC_MESSAGES``/``LANG``),
    fail-safe: lấy tiền tố ngôn ngữ (``vi_VN.UTF-8`` → ``vi``, ``en_US.UTF-8`` →
    ``en``); ``C``/``POSIX``/ngôn ngữ khác → bỏ qua, thử biến kế; không nhận được
    → ``None`` (để rơi về DEFAULT_LANG). KHÔNG raise."""

    for var in _SYSTEM_LOCALE_VARS:
        value = os.environ.get(var)
        if not value:
            continue
        prefix = value.strip().split(".")[0].split("@")[0].split("_")[0].lower()
        normalized = _normalize_lang_value(prefix)
        if normalized is not None:
            return normalized
    return None


def resolve_lang(explicit: Lang | str | None = None) -> Lang:
    """Phân giải ngôn ngữ hiệu lực theo đúng thứ tự ưu tiên (DESIGN):

    1. ``explicit`` (tham số truyền trực tiếp vào lệnh/hàm gọi) nếu có.
    2. Biến môi trường ``NAMIOS_LANG`` nếu có VÀ nhận diện được.
    3. Locale HỆ THỐNG (``LC_ALL``/``LC_MESSAGES``/``LANG``) — "tiếng Anh theo
       ngôn ngữ máy"; ISO NaMiOS (11/11) mặc định ``LANG=vi_VN`` → tiếng Việt.
    4. ``DEFAULT_LANG`` (VI) — luôn có đường rơi an toàn, không bao giờ lỗi.
    """

    if explicit is not None:
        if isinstance(explicit, Lang):
            return explicit
        normalized = _normalize_lang_value(str(explicit))
        return normalized if normalized is not None else DEFAULT_LANG

    env_value = os.environ.get(ENV_VAR)
    if env_value:
        normalized = _normalize_lang_value(env_value)
        if normalized is not None:
            return normalized

    system_lang = _lang_from_system_locale()
    if system_lang is not None:
        return system_lang

    return DEFAULT_LANG


def _load_locale_file(lang: Lang) -> dict[str, str]:
    path = _LOCALE_DIR / f"{lang.value}.json"
    with path.open("r", encoding="utf-8") as fh:
        raw: Any = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError(
            f"Catalog ngôn ngữ '{lang.value}' ({path}) phải là object JSON key->chuỗi."
        )
    result: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(
                f"Catalog ngôn ngữ '{lang.value}' ({path}): key/value phải là chuỗi "
                f"(key={key!r})."
            )
        result[key] = value
    return result


class _MissingAsEmpty(dict[str, Any]):
    """``dict`` dùng với ``str.format_map`` — param thiếu trả chuỗi rỗng
    thay vì ném ``KeyError``. Đây là lớp "format an toàn" bắt buộc theo
    hợp đồng ``Translator.t()``: KHÔNG bao giờ crash vì thiếu tham số."""

    def __missing__(self, key: str) -> str:  # noqa: D105
        return ""


def _safe_format(template: str, params: Mapping[str, Any]) -> str:
    """Format ``template`` bằng ``str.format_map`` — CHỈ thay thế placeholder
    ``{name}`` khai báo sẵn trong catalog bằng giá trị trong ``params``,
    KHÔNG ``eval``/nội suy lệnh nào (không có đường nào để injection chạy mã:
    giá trị param luôn được chèn dưới dạng văn bản thuần, không được
    diễn giải lại thành format-spec mới). Param thiếu → rỗng, không
    ``KeyError``; param thừa bị bỏ qua. Template hỏng (vd dấu ``{``/``}``
    không khớp, index vị trí không tồn tại) → trả nguyên văn template thay vì
    crash, để một key catalog sai không bao giờ làm hỏng toàn luồng CLI/UI.
    """

    safe_params = _MissingAsEmpty({str(k): v for k, v in dict(params).items()})
    try:
        return template.format_map(safe_params)
    except (ValueError, IndexError, KeyError, TypeError):
        return template


class Translator:
    """Bộ dịch key->chuỗi dùng chung toàn hệ thống (lớp COMMON — M1-i18n).

    Mỗi instance giữ catalog riêng cho từng ``Lang`` (nạp từ
    ``locale/vi.json``/``locale/en.json`` khi khởi tạo). ``add_catalog`` cho
    module khác đóng góp thêm key của riêng mình (merge, không cần sửa 2 file
    JSON chung) — dùng cho các WP/module khác khi wire ở pha sau.
    """

    def __init__(self) -> None:
        self._catalogs: dict[Lang, dict[str, str]] = {lang: {} for lang in Lang}
        for lang in Lang:
            self._catalogs[lang].update(_load_locale_file(lang))

    def add_catalog(self, lang: Lang | str, entries: Mapping[str, str]) -> None:
        """Nạp thêm (hoặc ghi đè nếu trùng key) các cặp key->chuỗi cho một
        ngôn ngữ. Dùng để module khác đóng góp catalog riêng của mình thay
        vì chỉnh trực tiếp ``locale/vi.json``/``locale/en.json`` (sở hữu bởi
        ``namios_i18n``)."""

        lang_enum = lang if isinstance(lang, Lang) else Lang(str(lang).strip().lower())
        bucket = self._catalogs.setdefault(lang_enum, {})
        bucket.update({str(k): str(v) for k, v in entries.items()})

    def has_key(self, key: str, lang: Lang | None = None) -> bool:
        """``True`` nếu ``key`` có trong catalog của ``lang`` (không fallback)
        — dùng cho test parity (mọi key phải có CẢ vi lẫn en)."""

        target = lang if lang is not None else DEFAULT_LANG
        return key in self._catalogs.get(target, {})

    def all_keys(self, lang: Lang | None = None) -> frozenset[str]:
        """Tập toàn bộ key hiện có của ``lang`` (mặc định VI) — tiện cho test
        parity đối chiếu vi/en."""

        target = lang if lang is not None else DEFAULT_LANG
        return frozenset(self._catalogs.get(target, {}))

    def t(self, key: str, /, lang: Lang | str | None = None, **params: Any) -> str:
        """Dịch ``key`` sang ngôn ngữ hiệu lực (``resolve_lang(lang)``).

        Thứ tự tra cứu khi key thiếu ở ngôn ngữ hiệu lực (fallback, DESIGN):
        ngôn ngữ hiệu lực → VI → EN → chính ``key`` (trả nguyên văn, không
        raise) — luôn có chuỗi để hiển thị, không bao giờ ``KeyError``.
        Format tham số qua ``str.format_map`` an toàn (xem ``_safe_format``):
        thiếu param không crash, không injection.

        ``key`` là positional-only (``/`` — PEP 570, thêm 03/11/2026 lúc
        WIRE caller thật): một số catalog có placeholder tên chính là
        ``{key}`` (vd ``eco.catalog_schema.error.unknown_property``,
        ``eco.validator.error.executable_key_forbidden``) — caller cần gọi
        ``t("some.catalog.key", lang=Lang.VI, key=bad_field_name)``; nếu
        ``key`` (tham số đầu) vẫn là tên thường, Python sẽ báo "got multiple
        values for argument 'key'" vì ``key=bad_field_name`` cố bind lại
        đúng tên tham số đó thay vì rơi vào ``**params``. Đổi thành
        positional-only KHÔNG đổi hành vi của bất kỳ call site hiện có nào
        (toàn repo luôn gọi ``t(key, ...)`` vị trí, không ai gọi
        ``t(key="...")`` bằng từ khoá — xem ``tests/unit/i18n/``) — chỉ GIẢI
        PHÓNG tên ``key`` để dùng làm tên tham số format tự do.
        """

        resolved = resolve_lang(lang)
        template = self._lookup(key, resolved)
        if template is None:
            return key
        return _safe_format(template, params)

    def _lookup(self, key: str, lang: Lang) -> str | None:
        order: list[Lang] = [lang]
        for fallback_lang in (Lang.VI, Lang.EN):
            if fallback_lang not in order:
                order.append(fallback_lang)
        for candidate_lang in order:
            value = self._catalogs.get(candidate_lang, {}).get(key)
            if value is not None:
                return value
        return None


#: Instance dùng chung toàn tiến trình (singleton tiện dụng — mọi module gọi
#: ``namios_i18n.t(...)``/``namios_i18n.add_catalog(...)`` thao tác trên
#: CÙNG một instance này, trừ khi tự tạo ``Translator()`` riêng để cô lập,
#: vd trong test).
_default_translator = Translator()


def get_default_translator() -> Translator:
    """Trả instance ``Translator`` dùng chung mặc định (singleton)."""

    return _default_translator


def add_catalog(lang: Lang | str, entries: Mapping[str, str]) -> None:
    """Thêm catalog vào instance dùng chung mặc định — xem
    ``Translator.add_catalog``. Mọi module ngoài ``namios_i18n`` góp thêm key
    riêng của mình qua hàm này ở pha wire (M1-INTERFACES §0: KHÔNG sửa trực
    tiếp ``locale/vi.json``/``locale/en.json`` của ``namios_i18n``)."""

    _default_translator.add_catalog(lang, entries)


def has_key(key: str, lang: Lang | None = None) -> bool:
    """Xem ``Translator.has_key`` trên instance dùng chung mặc định."""

    return _default_translator.has_key(key, lang)


def t(key: str, /, lang: Lang | str | None = None, **params: Any) -> str:
    """Hàm tiện ích dịch ``key`` bằng instance dùng chung mặc định — xem
    ``Translator.t`` (``key`` positional-only — cùng lý do, cho phép
    ``params`` chứa một tham số format tên ``key``)."""

    return _default_translator.t(key, lang, **params)
