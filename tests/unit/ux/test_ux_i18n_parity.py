"""Catalog i18n của namios_ux phải parity VN/EN + không rỗng (song ngữ cho cả
hệ thống — cùng quy ước test của namios_compat/namios_sys/..."""

from __future__ import annotations

from namios_i18n import Lang, has_key
from namios_ux._i18n import _EN, _VI


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
