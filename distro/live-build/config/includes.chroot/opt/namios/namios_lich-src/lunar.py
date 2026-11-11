"""Thuật toán đổi lịch Dương ↔ Âm lịch Việt Nam — lõi tính toán THUẦN PYTHON,
KHÔNG phụ thuộc thư viện ngoài, KHÔNG phụ thuộc PySide6 (test được không cần
desktop/GUI — xem ``tests/unit/lich/test_lunar.py`` ở repo gốc).

**Nguồn thuật toán (BẮT BUỘC ghi rõ — VN-1 yêu cầu "chính xác là tiêu chí
nghiệm thu"):** đây là bản port trực tiếp thuật toán công khai của
**Hồ Ngọc Đức** (Đại học Leipzig, Đức), "Thuật toán tính lịch Âm lịch Việt
Nam dựa trên vị trí thực của Mặt Trời/Mặt Trăng" —
https://www.informatik.uni-leipzig.de/~duc/amlich/calrules.html — thuật toán
này (xấp xỉ thiên văn: thời điểm Sóc/New Moon qua chuỗi Meeus rút gọn + hoàng
kinh Mặt Trời để xác định tháng 11 âm lịch chứa Đông Chí + tháng nhuận) là
NGUỒN được dùng rộng rãi nhất cho lịch âm Việt Nam hiện nay (bản JS gốc của
tác giả đã được port sang hàng chục ngôn ngữ — PHP/Java/Python/C — và là cơ
sở của hầu hết lịch âm lịch trên web/app Việt Nam). NaMiOS **KHÔNG tự chế**
thuật toán thiên văn riêng (rủi ro sai tháng nhuận/Tết rất cao) — chỉ port
lại công thức đã công bố, giữ nguyên hằng số/logic.

**Múi giờ:** cố định ``TIME_ZONE = 7.0`` (UTC+7, múi giờ Việt Nam từ 1967 đến
nay). Thuật toán gốc của Hồ Ngọc Đức dùng múi giờ UTC+8 cho các năm TRƯỚC
1967 (Việt Nam đổi múi giờ năm 1967) — module này KHÔNG xử lý nhánh đó vì
NaMiLịch chỉ phục vụ ngày hiện tại/tương lai + lịch sử gần (sau 1967); ngày
âm lịch trước 1967 tính bằng module này có thể SAI 1 ngày so với sử liệu.
Phạm vi chính xác đã công bố rộng rãi của bản thân thuật toán: khoảng năm
1800–2199 dương lịch.

**Đã tự kiểm chứng (chạy thật trong môi trường này, KHÔNG suy đoán — xem
``tests/unit/lich/test_lunar.py``):**
  - Mùng 1 Tết 9 năm 2020–2028 (ngày + tên năm Can-Chi) khớp 100% với ngày Tết
    Nguyên Đán được công bố rộng rãi (Canh Tý 25/01/2020 … Mậu Thân 26/01/2028).
  - Giỗ Tổ Hùng Vương 10/3 âm 2024 → 18/04/2024 dương (khớp công bố chính thức).
  - Năm Quý Mão 2023 có tháng nhuận (nhuận tháng 2) — thuật toán nhận diện
    đúng cờ ``leap=1`` cho tháng 2 âm lịch thứ hai (22/03/2023), và
    ``leap=0`` cho tháng 3 thường kế tiếp (20/04/2023).
  - Round-trip Dương→Âm→Dương trên 2000 ngày ngẫu nhiên (1950–2100): 0 lệch.

Hạn chế đã biết: KHÔNG tính giờ Hoàng đạo/Hắc đạo, KHÔNG tính "ngày tốt/xấu"
phong thủy (ngoài phạm vi VN-1 — chỉ cần ngày/tháng/năm âm + Can-Chi + lễ).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

#: Múi giờ Việt Nam hiện hành (UTC+7) — xem docstring module.
TIME_ZONE = 7.0

#: Hệ số góc một vòng tròn đầy (radian) — dùng để chuẩn hoá hoàng kinh.
_PI2 = 2 * math.pi

CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = [
    "Tý",
    "Sửu",
    "Dần",
    "Mão",
    "Thìn",
    "Tỵ",
    "Ngọ",
    "Mùi",
    "Thân",
    "Dậu",
    "Tuất",
    "Hợi",
]


def _int(x: float) -> int:
    """``INT()`` trong bản gốc = floor (KHÔNG phải truncate) — quan trọng với
    số âm (ví dụ ``k`` âm khi tính lùi về trước epoch)."""

    return math.floor(x)


def jd_from_date(dd: int, mm: int, yy: int) -> int:
    """Ngày thứ tự Julian (Julian Day Number) cho một ngày Dương lịch.

    Công thức chuẩn Fliegel & Van Flandern (1968) — xử lý đúng ranh giới
    chuyển từ lịch Julius sang Gregory (15/10/1582)."""

    a = _int((14 - mm) / 12)
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jd = (
        dd
        + _int((153 * m + 2) / 5)
        + 365 * y
        + _int(y / 4)
        - _int(y / 100)
        + _int(y / 400)
        - 32045
    )
    if jd < 2299161:
        jd = dd + _int((153 * m + 2) / 5) + 365 * y + _int(y / 4) - 32083
    return int(jd)


def jd_to_date(jd: int) -> tuple[int, int, int]:
    """Đảo ngược ``jd_from_date`` — trả ``(dd, mm, yy)`` Dương lịch."""

    if jd > 2299160:
        a = jd + 32044
        b = _int((4 * a + 3) / 146097)
        c = a - _int((146097 * b) / 4)
    else:
        b = 0
        c = jd + 32082
    d = _int((4 * c + 3) / 1461)
    e = c - _int((1461 * d) / 4)
    m = _int((5 * e + 2) / 153)
    day = e - _int((153 * m + 2) / 5) + 1
    month = m + 3 - 12 * _int(m / 10)
    year = b * 100 + d - 4800 + _int(m / 10)
    return (int(day), int(month), int(year))


def _new_moon(k: float) -> float:
    """Thời điểm (Julian Day, giờ GMT) của kỳ trăng non thứ ``k`` tính từ kỳ
    trăng non gần 1/1/1900 — xấp xỉ rút gọn từ chuỗi Meeus."""

    t = k / 1236.85
    t2 = t * t
    t3 = t2 * t
    dr = math.pi / 180
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * t2 - 0.000000155 * t3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * t - 0.009173 * t2) * dr)
    m = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3
    mpr = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3
    f = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3
    c1 = (0.1734 - 0.000393 * t) * math.sin(m * dr) + 0.0021 * math.sin(2 * dr * m)
    c1 = c1 - 0.4068 * math.sin(mpr * dr) + 0.0161 * math.sin(dr * 2 * mpr)
    c1 = c1 - 0.0004 * math.sin(dr * 3 * mpr)
    c1 = c1 + 0.0104 * math.sin(dr * 2 * f) - 0.0051 * math.sin(dr * (m + mpr))
    c1 = c1 - 0.0074 * math.sin(dr * (m - mpr)) + 0.0004 * math.sin(dr * (2 * f + m))
    c1 = c1 - 0.0004 * math.sin(dr * (2 * f - m)) - 0.0006 * math.sin(dr * (2 * f + mpr))
    c1 = c1 + 0.0010 * math.sin(dr * (2 * f - mpr)) + 0.0005 * math.sin(dr * (2 * mpr + m))
    if t < -11:
        deltat = 0.001 + 0.000839 * t + 0.0002261 * t2 - 0.00000845 * t3 - 0.000000081 * t * t3
    else:
        deltat = -0.000278 + 0.000265 * t + 0.000262 * t2
    return jd1 + c1 - deltat


def _sun_longitude(jdn: float) -> float:
    """Hoàng kinh (ecliptic longitude, radian, 0..2π) của Mặt Trời tại thời
    điểm Julian Day ``jdn`` — xấp xỉ rút gọn từ chuỗi Meeus."""

    t = (jdn - 2451545.0) / 36525
    t2 = t * t
    dr = math.pi / 180
    m = 357.52910 + 35999.05030 * t - 0.0001559 * t2 - 0.00000048 * t * t2
    l0 = 280.46645 + 36000.76983 * t + 0.0003032 * t2
    dl = (1.914600 - 0.004817 * t - 0.000014 * t2) * math.sin(dr * m)
    dl = dl + (0.019993 - 0.000101 * t) * math.sin(dr * 2 * m) + 0.000290 * math.sin(dr * 3 * m)
    longitude = (l0 + dl) * dr
    return longitude - _PI2 * _int(longitude / _PI2)


def _get_sun_longitude(day_number: float, time_zone: float) -> int:
    """Chỉ số "cung hoàng kinh" (0..11, mỗi cung 30°) của Mặt Trời lúc nửa
    đêm địa phương tại ``day_number`` — dùng để xác định tháng chứa Đông Chí
    (cung 9, tức ``sunLong >= 9`` nghĩa là Mặt Trời đã qua cung chứa Đông Chí)."""

    return _int(_sun_longitude(day_number - 0.5 - time_zone / 24) / math.pi * 6)


def _get_new_moon_day(k: float, time_zone: float) -> int:
    """Julian Day (số nguyên, theo giờ địa phương) của kỳ trăng non thứ ``k``."""

    return _int(_new_moon(k) + 0.5 + time_zone / 24)


def _get_lunar_month_11(yy: int, time_zone: float) -> int:
    """Julian Day của ngày bắt đầu tháng 11 âm lịch (tháng CHỨA Đông Chí) của
    năm dương lịch ``yy`` — mốc neo để đếm các tháng âm lịch khác."""

    off = jd_from_date(31, 12, yy) - 2415021.076998695
    k = _int(off / 29.530588853)
    nm = _get_new_moon_day(k, time_zone)
    sun_long = _get_sun_longitude(nm, time_zone)
    if sun_long >= 9:
        nm = _get_new_moon_day(k - 1, time_zone)
    return nm


def _get_leap_month_offset(a11: int, time_zone: float) -> int:
    """Số thứ tự (offset tính từ tháng 11 âm lịch năm trước) của tháng
    NHUẬN trong năm âm lịch bắt đầu từ ``a11``, nếu năm đó có 13 tháng."""

    k = _int((a11 - 2415021.076998695) / 29.530588853 + 0.5)
    i = 1
    arc = _get_sun_longitude(_get_new_moon_day(k + i, time_zone), time_zone)
    while True:
        last = arc
        i += 1
        arc = _get_sun_longitude(_get_new_moon_day(k + i, time_zone), time_zone)
        if arc == last or i >= 14:
            break
    return i - 1


def convert_solar_to_lunar(
    dd: int, mm: int, yy: int, time_zone: float = TIME_ZONE
) -> tuple[int, int, int, int]:
    """Đổi một ngày Dương lịch ``(dd, mm, yy)`` sang Âm lịch.

    Trả ``(lunar_day, lunar_month, lunar_year, lunar_leap)`` — ``lunar_leap``
    là ``1`` nếu đây là THÁNG NHUẬN (năm 13 tháng âm), ngược lại ``0``."""

    day_number = jd_from_date(dd, mm, yy)
    k = _int((day_number - 2415021.076998695) / 29.530588853)
    month_start = _get_new_moon_day(k + 1, time_zone)
    if month_start > day_number:
        month_start = _get_new_moon_day(k, time_zone)
    a11 = _get_lunar_month_11(yy, time_zone)
    b11 = a11
    if a11 >= month_start:
        lunar_year = yy
        a11 = _get_lunar_month_11(yy - 1, time_zone)
    else:
        lunar_year = yy + 1
        b11 = _get_lunar_month_11(yy + 1, time_zone)
    lunar_day = day_number - month_start + 1
    diff = _int((month_start - a11) / 29)
    lunar_leap = 0
    lunar_month = diff + 11
    if b11 - a11 > 365:
        leap_month_diff = _get_leap_month_offset(a11, time_zone)
        if diff >= leap_month_diff:
            lunar_month = diff + 10
            if diff == leap_month_diff:
                lunar_leap = 1
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1
    return (int(lunar_day), int(lunar_month), int(lunar_year), int(lunar_leap))


def convert_lunar_to_solar(
    lunar_day: int,
    lunar_month: int,
    lunar_year: int,
    lunar_leap: int = 0,
    time_zone: float = TIME_ZONE,
) -> tuple[int, int, int]:
    """Đổi một ngày Âm lịch sang Dương lịch. Trả ``(dd, mm, yy)``.

    Trả ``(0, 0, 0)`` khi năm âm lịch đó CÓ 13 tháng (có tháng nhuận) nhưng
    ``lunar_leap=1`` được xin cho một tháng KHÁC tháng nhuận thật của năm đó
    (ví dụ xin "tháng 3 nhuận" trong năm 2023 — năm 2023 có 13 tháng nhưng
    tháng nhuận thật là tháng 2, không phải tháng 3 — xem
    ``test_xin_sai_thang_nhuan_trong_nam_co_nhuan_bi_bao_khong_ton_tai``).

    **Hạn chế đã biết của bản gốc (giữ nguyên khi port):** nếu năm âm lịch
    đó CHỈ có 12 tháng (không tháng nhuận nào), hàm KHÔNG kiểm ``lunar_leap``
    — gọi với ``lunar_leap=1`` ở một năm 12-tháng vẫn trả về một ngày (tính
    như ``lunar_leap=0``), không báo lỗi/không trả ``(0, 0, 0)``. Caller cần
    tự biết năm nào có tháng nhuận trước khi hỏi tháng nhuận (hoặc gọi
    ``convert_solar_to_lunar`` theo chiều ngược để lấy đúng cờ ``leap``)."""

    if lunar_month < 11:
        a11 = _get_lunar_month_11(lunar_year - 1, time_zone)
        b11 = _get_lunar_month_11(lunar_year, time_zone)
    else:
        a11 = _get_lunar_month_11(lunar_year, time_zone)
        b11 = _get_lunar_month_11(lunar_year + 1, time_zone)
    k = _int(0.5 + (a11 - 2415021.076998695) / 29.530588853)
    off = lunar_month - 11
    if off < 0:
        off += 12
    if b11 - a11 > 365:
        leap_off = _get_leap_month_offset(a11, time_zone)
        leap_month = leap_off - 2
        if leap_month < 0:
            leap_month += 12
        if lunar_leap != 0 and lunar_month != leap_month:
            return (0, 0, 0)
        elif lunar_leap != 0 or off >= leap_off:
            off += 1
    month_start = _get_new_moon_day(k + off, time_zone)
    return jd_to_date(month_start + lunar_day - 1)


def year_can_chi(lunar_year: int) -> str:
    """Tên Can-Chi của một NĂM âm lịch (ví dụ 2024 → "Giáp Thìn")."""

    return f"{CAN[(lunar_year + 6) % 10]} {CHI[(lunar_year + 8) % 12]}"


def month_can_chi(lunar_month: int, lunar_year: int) -> str:
    """Tên Can-Chi của một THÁNG âm lịch."""

    return f"{CAN[(lunar_year * 12 + lunar_month + 3) % 10]} {CHI[(lunar_month + 1) % 12]}"


def day_can_chi(dd: int, mm: int, yy: int) -> str:
    """Tên Can-Chi của một NGÀY (tính theo ngày Dương lịch, vì Can-Chi ngày
    chạy theo chu kỳ 60 ngày liên tục, không phụ thuộc Âm/Dương lịch)."""

    jd = jd_from_date(dd, mm, yy)
    return f"{CAN[(jd + 9) % 10]} {CHI[(jd + 1) % 12]}"


@dataclass(frozen=True)
class LunarDate:
    """Một ngày Âm lịch đầy đủ — bọc 4 số thô ``convert_solar_to_lunar`` trả
    về thành kiểu có tên, kèm tiện ích format/can-chi."""

    day: int
    month: int
    year: int
    leap: bool

    @property
    def month_label(self) -> str:
        return f"{self.month:02d}{'(N)' if self.leap else ''}"

    def format_vi(self) -> str:
        leap_note = " (tháng nhuận)" if self.leap else ""
        return f"{self.day:02d}/{self.month:02d} âm lịch{leap_note} — năm {year_can_chi(self.year)}"

    def to_solar(self) -> date | None:
        dd, mm, yy = convert_lunar_to_solar(self.day, self.month, self.year, int(self.leap))
        if (dd, mm, yy) == (0, 0, 0):
            return None
        return date(yy, mm, dd)


def solar_date_to_lunar(d: date) -> LunarDate:
    """Tiện ích: nhận một ``datetime.date`` Dương lịch, trả ``LunarDate``."""

    ld, lm, ly, leap = convert_solar_to_lunar(d.day, d.month, d.year)
    return LunarDate(day=ld, month=lm, year=ly, leap=bool(leap))


def day_can_chi_for_date(d: date) -> str:
    """Tiện ích: Can-Chi ngày cho một ``datetime.date``."""

    return day_can_chi(d.day, d.month, d.year)
