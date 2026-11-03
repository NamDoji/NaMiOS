"""``resolve_lang`` — thứ tự ưu tiên explicit > biến môi trường > mặc định VI."""

from __future__ import annotations

import pytest

from namios_i18n import ENV_VAR, Lang, resolve_lang


def test_default_is_vi_when_nothing_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert resolve_lang() == Lang.VI
    assert resolve_lang(None) == Lang.VI


def test_env_var_selects_en(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "en")
    assert resolve_lang() == Lang.EN


def test_env_var_is_case_and_whitespace_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "  EN  ")
    assert resolve_lang() == Lang.EN


def test_unrecognized_env_var_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "fr")
    assert resolve_lang() == Lang.VI


def test_explicit_lang_enum_wins_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "en")
    assert resolve_lang(Lang.VI) == Lang.VI


def test_explicit_string_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert resolve_lang("EN") == Lang.EN
    assert resolve_lang(" vi ") == Lang.VI


def test_explicit_unrecognized_string_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR, "en")
    # Tham số explicit sai (không phải "vi"/"en") KHÔNG được âm thầm đọc env
    # thay — luôn có đường rơi an toàn về DEFAULT_LANG (VI).
    assert resolve_lang("fr") == Lang.VI


def test_empty_env_var_is_treated_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "")
    assert resolve_lang() == Lang.VI
