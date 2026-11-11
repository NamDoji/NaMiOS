"""Nạp + truy vấn ngày lễ Việt Nam (``holidays_vn.json``) + nhắc giỗ tuỳ
người dùng thêm (lưu ``~/.config/namios/namios_lich/reminders.json``) — THUẦN
PYTHON, không phụ thuộc PySide6 (test được không cần GUI).

Mỗi mục lễ trong ``holidays_vn.json`` có ``type: "solar"`` (ngày/tháng DƯƠNG
cố định mỗi năm, ví dụ 1/5) hoặc ``type: "lunar"`` (ngày/tháng ÂM, cần đổi
lại sang Dương MỖI NĂM qua :func:`namios_lich.lunar.convert_lunar_to_solar`
— ví dụ Tết Trung Thu 15/8 âm rơi vào ngày Dương khác nhau mỗi năm).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from namios_lich.lunar import convert_lunar_to_solar

#: File dữ liệu lễ đóng gói cùng ứng dụng — chỉ đọc (read-only), không bao giờ
#: ghi lại. Đường dẫn tương đối theo chính module này (``__file__``) để chạy
#: đúng cả khi test từ repo gốc lẫn khi cài vào ``/opt/namios/namios_lich``.
_BUNDLED_HOLIDAYS_PATH = Path(__file__).resolve().parent / "holidays_vn.json"


@dataclass(frozen=True)
class HolidayDef:
    """Một định nghĩa lễ (từ JSON) — CHƯA gắn với năm cụ thể."""

    id: str
    name_vi: str
    type: str  # "solar" | "lunar"
    day: int
    month: int
    cong_lap: bool
    note_vi: str | None = None


@dataclass(frozen=True)
class UpcomingHoliday:
    """Một lễ ĐÃ quy đổi ra ngày Dương lịch cụ thể của một năm, kèm số ngày
    còn lại tính từ một ngày mốc (``today``)."""

    name_vi: str
    solar_date: date
    cong_lap: bool
    days_remaining: int
    is_lunar_based: bool


def load_holiday_defs(path: Path | None = None) -> list[HolidayDef]:
    """Đọc ``holidays_vn.json``. ``path=None`` → dùng file đóng gói sẵn.

    Fail-safe: file thiếu/hỏng JSON → trả danh sách RỖNG (không raise), để
    UI vẫn mở được (chỉ không hiện lễ) thay vì crash toàn ứng dụng."""

    real_path = path or _BUNDLED_HOLIDAYS_PATH
    try:
        raw = json.loads(real_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: list[HolidayDef] = []
    for item in raw.get("holidays", []):
        try:
            out.append(
                HolidayDef(
                    id=str(item["id"]),
                    name_vi=str(item["name_vi"]),
                    type=str(item["type"]),
                    day=int(item["day"]),
                    month=int(item["month"]),
                    cong_lap=bool(item.get("cong_lap", False)),
                    note_vi=item.get("note_vi"),
                )
            )
        except (KeyError, TypeError, ValueError):
            # Một mục lỗi không được làm hỏng cả danh sách — bỏ qua mục đó.
            continue
    return out


def _resolve_lunar_holiday_for_year(hol: HolidayDef, solar_year: int) -> date | None:
    """Quy đổi một lễ ÂM LỊCH sang ngày Dương lịch của năm dương ``solar_year``
    (lễ âm có thể rơi sang năm dương kế tiếp/trước — hàm thử cả năm âm lịch
    tương ứng quanh ``solar_year`` và chọn kết quả rơi đúng trong năm đó)."""

    for lunar_year_guess in (solar_year, solar_year - 1, solar_year + 1):
        dd, mm, yy = convert_lunar_to_solar(hol.day, hol.month, lunar_year_guess, 0)
        if (dd, mm, yy) != (0, 0, 0) and yy == solar_year:
            return date(yy, mm, dd)
    # Tháng 12 âm một số năm chỉ có 29 ngày — "30 Tết" không tồn tại, lùi về 29.
    if hol.month == 12 and hol.day == 30:
        for lunar_year_guess in (solar_year, solar_year - 1, solar_year + 1):
            dd, mm, yy = convert_lunar_to_solar(29, 12, lunar_year_guess, 0)
            if (dd, mm, yy) != (0, 0, 0) and yy == solar_year:
                return date(yy, mm, dd)
    return None


def resolve_holiday_for_year(hol: HolidayDef, solar_year: int) -> date | None:
    """Ngày Dương lịch cụ thể của một lễ trong năm dương ``solar_year``."""

    if hol.type == "solar":
        try:
            return date(solar_year, hol.month, hol.day)
        except ValueError:
            return None
    if hol.type == "lunar":
        return _resolve_lunar_holiday_for_year(hol, solar_year)
    return None


def upcoming_holidays(
    today: date, defs: list[HolidayDef], count: int = 5, window_days: int = 400
) -> list[UpcomingHoliday]:
    """Danh sách tối đa ``count`` lễ SẮP TỚI tính từ ``today`` (kể cả hôm
    nay, ``days_remaining=0``), sắp theo gần nhất trước — nhìn xa tối đa
    ``window_days`` ngày (đủ phủ một năm + Tết năm sau nếu đang cuối năm)."""

    results: list[UpcomingHoliday] = []
    for hol in defs:
        for candidate_year in (today.year, today.year + 1):
            solar_date = resolve_holiday_for_year(hol, candidate_year)
            if solar_date is None:
                continue
            delta = (solar_date - today).days
            if 0 <= delta <= window_days:
                results.append(
                    UpcomingHoliday(
                        name_vi=hol.name_vi,
                        solar_date=solar_date,
                        cong_lap=hol.cong_lap,
                        days_remaining=delta,
                        is_lunar_based=(hol.type == "lunar"),
                    )
                )
    results.sort(key=lambda h: h.days_remaining)
    return results[:count]


def holidays_on_date(d: date, defs: list[HolidayDef]) -> list[HolidayDef]:
    """Các lễ rơi ĐÚNG vào ngày Dương lịch ``d`` (dùng để tô màu lưới tháng)."""

    out = []
    for hol in defs:
        solar_date = resolve_holiday_for_year(hol, d.year)
        if solar_date == d:
            out.append(hol)
    return out


# --- Nhắc giỗ tuỳ người dùng thêm (VN-1: "cho phép thêm nhắc giỗ theo âm
# lịch lặp hằng năm") -------------------------------------------------------

REMINDERS_FILENAME = "reminders.json"


@dataclass(frozen=True)
class CustomReminder:
    """Một nhắc việc/giỗ do người dùng tự thêm — LẶP HẰNG NĂM theo ngày ÂM
    lịch (ví dụ giỗ ông bà ngày 12/7 âm, lặp mỗi năm dương khác nhau)."""

    name_vi: str
    lunar_day: int
    lunar_month: int


def reminders_path(config_dir: Path) -> Path:
    """``<config_dir>/namios_lich/reminders.json`` — ``config_dir`` do caller
    truyền vào (thường ``namios_core.paths.config_dir()``), module này KHÔNG
    tự biết XDG để giữ tách biệt khỏi GUI/hệ thống (test độc lập)."""

    return config_dir / "namios_lich" / REMINDERS_FILENAME


def load_reminders(config_dir: Path) -> list[CustomReminder]:
    """Đọc danh sách nhắc giỗ đã lưu. File chưa tồn tại/hỏng → trả rỗng
    (fail-safe, không raise)."""

    path = reminders_path(config_dir)
    if not path.exists():
        return []
    try:
        raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: list[CustomReminder] = []
    for item in raw:
        try:
            out.append(
                CustomReminder(
                    name_vi=str(item["name_vi"]),
                    lunar_day=int(item["lunar_day"]),
                    lunar_month=int(item["lunar_month"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return out


def save_reminders(config_dir: Path, reminders: list[CustomReminder]) -> None:
    """Ghi lại TOÀN BỘ danh sách nhắc giỗ (ghi đè, không phải append) —
    tạo thư mục cha nếu chưa có. KHÔNG dùng ``shell=True``/``eval`` — chỉ
    ``pathlib``/``json`` thuần."""

    path = reminders_path(config_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {"name_vi": r.name_vi, "lunar_day": r.lunar_day, "lunar_month": r.lunar_month}
        for r in reminders
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def add_reminder(config_dir: Path, name_vi: str, lunar_day: int, lunar_month: int) -> None:
    """Thêm một nhắc giỗ mới + lưu lại ngay (idempotent theo tên — thêm lại
    tên đã có sẽ CẬP NHẬT ngày/tháng của mục đó, không tạo bản trùng)."""

    reminders = [r for r in load_reminders(config_dir) if r.name_vi != name_vi]
    reminders.append(CustomReminder(name_vi=name_vi, lunar_day=lunar_day, lunar_month=lunar_month))
    save_reminders(config_dir, reminders)


def remove_reminder(config_dir: Path, name_vi: str) -> None:
    """Xoá một nhắc giỗ theo tên (không raise nếu tên không tồn tại)."""

    reminders = [r for r in load_reminders(config_dir) if r.name_vi != name_vi]
    save_reminders(config_dir, reminders)


def reminder_defs(reminders: list[CustomReminder]) -> list[HolidayDef]:
    """Chuyển ``CustomReminder`` sang ``HolidayDef`` (``type="lunar"``,
    ``cong_lap=False``) để tái dùng chung logic ``upcoming_holidays``."""

    return [
        HolidayDef(
            id=f"custom:{r.name_vi}",
            name_vi=f"Giỗ {r.name_vi}",
            type="lunar",
            day=r.lunar_day,
            month=r.lunar_month,
            cong_lap=False,
        )
        for r in reminders
    ]
