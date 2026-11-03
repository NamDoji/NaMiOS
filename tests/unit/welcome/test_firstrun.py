"""Test logic ``ConfigApplier`` — ghi config đúng, idempotent, hoàn tác,
validate lựa chọn không hợp lệ. KHÔNG dùng GUI."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from namios_welcome.firstrun import ConfigApplier, FirstRunChoices, FirstRunValidationError


def _choices(**overrides: object) -> FirstRunChoices:
    base = {
        "ime_method": "telex",
        "ui_scale_percent": 125,
        "default_app_docx": "libreoffice-writer",
        "default_app_xlsx": "libreoffice-calc",
        "default_app_pdf": "okular",
        "default_printer": None,
    }
    base.update(overrides)
    return FirstRunChoices(**base)  # type: ignore[arg-type]


def _fixed_clock(fixed: datetime) -> Callable[[], datetime]:
    def clock() -> datetime:
        return fixed

    return clock


# --- apply ghi đúng -------------------------------------------------------


def test_apply_writes_config_file_under_home_no_root_needed(tmp_path: Path) -> None:
    config_dir = tmp_path / "config" / "namios"
    applier = ConfigApplier(config_dir, clock=_fixed_clock(datetime(2026, 11, 3, tzinfo=UTC)))
    choices = _choices()

    report = applier.apply(choices)

    assert Path(report.config_path).exists()
    payload = json.loads(Path(report.config_path).read_text(encoding="utf-8"))
    assert payload["ime_method"] == "telex"
    assert payload["ui_scale_percent"] == 125
    assert payload["default_app_docx"] == "libreoffice-writer"
    assert payload["applied_at"] == "2026-11-03T00:00:00+00:00"
    assert report.previous is None
    assert report.current == choices


def test_apply_creates_config_dir_if_missing(tmp_path: Path) -> None:
    config_dir = tmp_path / "chua-ton-tai" / "sau" / "namios"
    applier = ConfigApplier(config_dir)

    applier.apply(_choices())

    assert config_dir.is_dir()


def test_read_current_returns_none_when_no_config_yet(tmp_path: Path) -> None:
    applier = ConfigApplier(tmp_path / "config")
    assert applier.read_current() is None


def test_read_current_returns_none_on_corrupt_file_without_raising(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "welcome.json").write_text("{khong phai json hop le")

    applier = ConfigApplier(config_dir)

    assert applier.read_current() is None


# --- idempotent -----------------------------------------------------------


def test_apply_twice_with_same_choices_is_idempotent(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    fixed = _fixed_clock(datetime(2026, 11, 3, 9, 0, tzinfo=UTC))
    applier = ConfigApplier(config_dir, clock=fixed)
    choices = _choices()

    first = applier.apply(choices)
    second = applier.apply(choices)

    assert first.current == second.current == choices
    assert second.previous == choices
    content_first_read_again = Path(first.config_path).read_text(encoding="utf-8")
    content_second = Path(second.config_path).read_text(encoding="utf-8")
    assert content_first_read_again == content_second


def test_apply_updates_previous_to_last_applied_value(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    applier = ConfigApplier(config_dir)
    first_choices = _choices(ime_method="telex")
    second_choices = _choices(ime_method="vni")

    applier.apply(first_choices)
    report2 = applier.apply(second_choices)

    assert report2.previous == first_choices
    assert report2.current == second_choices
    assert applier.read_current() == second_choices


# --- hoàn tác (revert) -----------------------------------------------------


def test_revert_restores_previous_choices(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    applier = ConfigApplier(config_dir)
    first_choices = _choices(ui_scale_percent=100)
    second_choices = _choices(ui_scale_percent=150)

    applier.apply(first_choices)
    applier.apply(second_choices)
    assert applier.read_current() == second_choices

    restored = applier.revert()

    assert restored == first_choices
    assert applier.read_current() == first_choices


def test_revert_returns_none_when_no_backup_exists(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    applier = ConfigApplier(config_dir)
    applier.apply(_choices())

    restored = applier.revert()

    assert restored is None
    assert applier.read_current() == _choices()


def test_revert_without_any_apply_returns_none(tmp_path: Path) -> None:
    applier = ConfigApplier(tmp_path / "config")
    assert applier.revert() is None


# --- validate --------------------------------------------------------------


def test_apply_rejects_invalid_ime_method(tmp_path: Path) -> None:
    applier = ConfigApplier(tmp_path / "config")
    bad_choices = _choices(ime_method="qwerty")

    with pytest.raises(FirstRunValidationError):
        applier.apply(bad_choices)
    assert applier.read_current() is None


def test_apply_rejects_invalid_ui_scale_percent(tmp_path: Path) -> None:
    applier = ConfigApplier(tmp_path / "config")
    bad_choices = _choices(ui_scale_percent=200)

    with pytest.raises(FirstRunValidationError):
        applier.apply(bad_choices)


def test_apply_rejects_blank_default_app(tmp_path: Path) -> None:
    applier = ConfigApplier(tmp_path / "config")
    bad_choices = _choices(default_app_docx="   ")

    with pytest.raises(FirstRunValidationError):
        applier.apply(bad_choices)


def test_apply_accepts_none_default_printer(tmp_path: Path) -> None:
    applier = ConfigApplier(tmp_path / "config")
    choices = _choices(default_printer=None)

    report = applier.apply(choices)

    assert report.current.default_printer is None
