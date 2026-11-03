"""Parity giữa ``locale/vi.json`` và ``locale/en.json`` — mọi key PHẢI có CẢ
vi lẫn en (không thiếu bên nào), không rỗng, không trùng khoảng trắng thừa."""

from __future__ import annotations

import json
from pathlib import Path

from namios_i18n import Lang, Translator
from namios_i18n.translator import _LOCALE_DIR  # type: ignore[attr-defined]

_VI_PATH = Path(_LOCALE_DIR) / "vi.json"
_EN_PATH = Path(_LOCALE_DIR) / "en.json"


def _load(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict)
    return data


def test_locale_files_exist_and_parse() -> None:
    assert _VI_PATH.is_file()
    assert _EN_PATH.is_file()
    vi = _load(_VI_PATH)
    en = _load(_EN_PATH)
    assert len(vi) > 0
    assert len(en) > 0


def test_every_key_has_both_vi_and_en() -> None:
    vi = _load(_VI_PATH)
    en = _load(_EN_PATH)
    missing_in_en = sorted(set(vi) - set(en))
    missing_in_vi = sorted(set(en) - set(vi))
    assert missing_in_en == [], f"Thiếu bản EN cho các key: {missing_in_en}"
    assert missing_in_vi == [], f"Thiếu bản VI cho các key: {missing_in_vi}"


def test_no_empty_or_whitespace_only_values() -> None:
    for path, catalog in ((_VI_PATH, _load(_VI_PATH)), (_EN_PATH, _load(_EN_PATH))):
        for key, value in catalog.items():
            assert isinstance(value, str), f"{path}: '{key}' không phải chuỗi"
            assert value.strip(), f"{path}: '{key}' rỗng/chỉ khoảng trắng"


def _collect_keys_in_order(text: str) -> list[str]:
    keys: list[str] = []

    def _hook(pairs: list[tuple[str, str]]) -> dict[str, str]:
        keys.extend(k for k, _ in pairs)
        return dict(pairs)

    json.loads(text, object_pairs_hook=_hook)
    return keys


def test_no_duplicate_keys_by_reparsing_raw_text() -> None:
    # json.load tự gộp key trùng (giữ bản cuối) — đọc text thô để chắc chắn
    # không có khoá bị khai báo 2 lần trong 1 file (lỗi copy-paste).
    for path in (_VI_PATH, _EN_PATH):
        keys = _collect_keys_in_order(path.read_text(encoding="utf-8"))
        duplicates = sorted({k for k in keys if keys.count(k) > 1})
        assert duplicates == [], f"{path}: key trùng lặp: {duplicates}"


def test_translator_builtin_catalog_matches_locale_files_exactly() -> None:
    """``Translator`` phải nạp ĐÚNG nguyên văn từng template từ 2 file JSON —
    so sánh template thô (chưa format tham số), không qua ``t()`` vì nhiều
    key có placeholder ``{...}`` sẽ bị format rỗng nếu gọi ``t()`` không kèm
    tham số."""

    translator = Translator()
    vi = _load(_VI_PATH)
    en = _load(_EN_PATH)
    for key, value in vi.items():
        assert translator._lookup(key, Lang.VI) == value  # noqa: SLF001
    for key, value in en.items():
        assert translator._lookup(key, Lang.EN) == value  # noqa: SLF001
