"""Test nạp/truy vấn ``holidays_vn.json`` + nhắc giỗ tuỳ người dùng
(``namios_lich.holidays``) — thuần Python, không cần GUI."""

from __future__ import annotations

import datetime
from pathlib import Path

from namios_lich.holidays import (
    add_reminder,
    holidays_on_date,
    load_holiday_defs,
    load_reminders,
    reminder_defs,
    resolve_holiday_for_year,
    upcoming_holidays,
)


def test_load_bundled_holidays_non_empty() -> None:
    defs = load_holiday_defs()
    assert len(defs) >= 15
    ids = {d.id for d in defs}
    assert "tet_nguyen_dan_1" in ids
    assert "quoc_khanh" in ids


def test_solar_holiday_fixed_every_year() -> None:
    defs = load_holiday_defs()
    quoc_khanh = next(d for d in defs if d.id == "quoc_khanh")
    assert resolve_holiday_for_year(quoc_khanh, 2026) == datetime.date(2026, 9, 2)
    assert resolve_holiday_for_year(quoc_khanh, 2030) == datetime.date(2030, 9, 2)


def test_lunar_holiday_resolves_to_known_solar_date() -> None:
    """Tết Nguyên Đán Mùng 1 (lễ ÂM lịch, type="lunar") phải quy đổi đúng
    ra ngày dương đã kiểm trong ``test_lunar.py`` (10/02/2024, 17/02/2026)."""

    defs = load_holiday_defs()
    mung_1 = next(d for d in defs if d.id == "tet_nguyen_dan_1")
    assert resolve_holiday_for_year(mung_1, 2024) == datetime.date(2024, 2, 10)
    assert resolve_holiday_for_year(mung_1, 2026) == datetime.date(2026, 2, 17)


def test_holidays_on_date_matches_tet() -> None:
    defs = load_holiday_defs()
    found = holidays_on_date(datetime.date(2024, 2, 10), defs)
    assert any(h.id == "tet_nguyen_dan_1" for h in found)


def test_upcoming_holidays_sorted_and_within_window() -> None:
    defs = load_holiday_defs()
    today = datetime.date(2026, 11, 11)
    upcoming = upcoming_holidays(today, defs, count=3)
    assert len(upcoming) == 3
    deltas = [h.days_remaining for h in upcoming]
    assert deltas == sorted(deltas)
    assert all(d >= 0 for d in deltas)


def test_custom_reminder_roundtrip(tmp_path: Path) -> None:
    config_dir = tmp_path / "namios-config"
    add_reminder(config_dir, "Ông Nội", lunar_day=12, lunar_month=7)
    reminders = load_reminders(config_dir)
    assert len(reminders) == 1
    assert reminders[0].name_vi == "Ông Nội"
    assert (reminders[0].lunar_day, reminders[0].lunar_month) == (12, 7)

    defs = reminder_defs(reminders)
    assert defs[0].type == "lunar"
    assert defs[0].cong_lap is False

    # Thêm lại cùng tên với ngày khác -> cập nhật, không tạo bản trùng.
    add_reminder(config_dir, "Ông Nội", lunar_day=20, lunar_month=8)
    reminders_after = load_reminders(config_dir)
    assert len(reminders_after) == 1
    assert (reminders_after[0].lunar_day, reminders_after[0].lunar_month) == (20, 8)
