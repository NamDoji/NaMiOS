"""``namios_lich`` — NaMiLịch: Âm lịch Việt Nam + ngày lễ, tự viết, offline
hoàn toàn (VN-1, ``docs/roadmap/NEW-FUNCTIONS-DIRECTION.md``).

Thuần Python (``lunar``/``holidays``), KHÔNG phụ thuộc GUI. ``ui``/
``__main__`` là cửa sổ PySide6 mỏng chỉ dùng trên desktop thật — tách khỏi
logic để test được không cần GUI (xem ``tests/unit/lich/``).
"""

from __future__ import annotations

from namios_lich.holidays import (
    CustomReminder,
    HolidayDef,
    UpcomingHoliday,
    add_reminder,
    holidays_on_date,
    load_holiday_defs,
    load_reminders,
    reminder_defs,
    remove_reminder,
    resolve_holiday_for_year,
    save_reminders,
    upcoming_holidays,
)
from namios_lich.lunar import (
    CAN,
    CHI,
    TIME_ZONE,
    LunarDate,
    convert_lunar_to_solar,
    convert_solar_to_lunar,
    day_can_chi,
    day_can_chi_for_date,
    month_can_chi,
    solar_date_to_lunar,
    year_can_chi,
)

__all__ = [
    "TIME_ZONE",
    "CAN",
    "CHI",
    "LunarDate",
    "convert_solar_to_lunar",
    "convert_lunar_to_solar",
    "year_can_chi",
    "month_can_chi",
    "day_can_chi",
    "solar_date_to_lunar",
    "day_can_chi_for_date",
    "HolidayDef",
    "UpcomingHoliday",
    "CustomReminder",
    "load_holiday_defs",
    "resolve_holiday_for_year",
    "upcoming_holidays",
    "holidays_on_date",
    "load_reminders",
    "save_reminders",
    "add_reminder",
    "remove_reminder",
    "reminder_defs",
]
