"""Catalog i18n của namios_pra phải parity VN/EN + không rỗng + đăng ký được
(song ngữ qua MỘT nguồn — bất biến #6; Phụ lục 06 chuỗi người đọc đều qua đây)."""

from __future__ import annotations

from namios_i18n import Lang, has_key
from namios_pra._i18n import _EN, _VI


def test_vi_en_same_keys() -> None:
    assert set(_VI) == set(_EN), set(_VI).symmetric_difference(set(_EN))


def test_no_empty_values() -> None:
    for catalog in (_VI, _EN):
        for key, value in catalog.items():
            assert isinstance(value, str) and value.strip(), key


def test_registered_in_translator() -> None:
    for key in _VI:
        assert has_key(key, lang=Lang.VI), key
        assert has_key(key, lang=Lang.EN), key
