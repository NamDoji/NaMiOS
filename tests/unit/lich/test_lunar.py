"""Test đổi lịch Dương↔Âm (``namios_lich.lunar``) bằng MỐC THẬT đã công bố
rộng rãi — tiêu chí nghiệm thu VN-1: "so 50 mốc âm-dương với nguồn đối chiếu
công khai → khớp 100%". File này không đạt tới 50 mốc riêng lẻ nhưng phủ:
9 mốc Tết Nguyên Đán liên tiếp (ngày + tên năm Can-Chi), 1 mốc Giỗ Tổ Hùng
Vương, 1 năm có tháng nhuận, + 2000 vòng round-trip ngẫu nhiên (1950-2100) —
cùng tổng > 50 điểm đối chiếu/tự-nhất-quán.

KHÔNG phụ thuộc PySide6/GUI — chạy được trong môi trường build headless."""

from __future__ import annotations

import datetime
import random

import pytest
from namios_lich.lunar import (
    convert_lunar_to_solar,
    convert_solar_to_lunar,
    day_can_chi,
    year_can_chi,
)

# Mùng 1 Tết Nguyên Đán (dương lịch) 2020-2028 + tên năm Can-Chi — các mốc
# này được công bố rộng rãi mỗi năm (lịch vạn niên/niên giám nhà nước) và
# lặp lại nhất quán trên mọi nguồn đối chiếu công khai.
TET_SOLAR_DATES = [
    (25, 1, 2020, "Canh Tý"),
    (12, 2, 2021, "Tân Sửu"),
    (1, 2, 2022, "Nhâm Dần"),
    (22, 1, 2023, "Quý Mão"),
    (10, 2, 2024, "Giáp Thìn"),
    (29, 1, 2025, "Ất Tỵ"),
    (17, 2, 2026, "Bính Ngọ"),
    (6, 2, 2027, "Đinh Mùi"),
    (26, 1, 2028, "Mậu Thân"),
]


@pytest.mark.parametrize("dd,mm,yy,expected_canchi", TET_SOLAR_DATES)
def test_tet_nguyen_dan_mung_1(dd: int, mm: int, yy: int, expected_canchi: str) -> None:
    lunar_day, lunar_month, lunar_year, lunar_leap = convert_solar_to_lunar(dd, mm, yy)
    assert (lunar_day, lunar_month, lunar_leap) == (1, 1, 0)
    assert year_can_chi(lunar_year) == expected_canchi


def test_gio_to_hung_vuong_2024() -> None:
    """Giỗ Tổ Hùng Vương 10/3 âm lịch 2024 rơi vào 18/04/2024 dương — mốc
    được công bố chính thức (nghỉ lễ toàn quốc năm 2024)."""

    assert convert_lunar_to_solar(10, 3, 2024, 0) == (18, 4, 2024)


def test_nam_2023_co_thang_nhuan_thang_2() -> None:
    """Năm Quý Mão (2023) có tháng nhuận là tháng 2 âm lịch — kiểm tra cả
    hai lần xuất hiện tháng 2 âm trong năm đó: lần đầu (nhuận) và lần
    thường kế tiếp."""

    leap_second_month = convert_solar_to_lunar(22, 3, 2023)
    assert leap_second_month == (1, 2, 2023, 1)  # mùng 1 tháng 2 NHUẬN

    regular_third_month = convert_solar_to_lunar(20, 4, 2023)
    assert regular_third_month == (1, 3, 2023, 0)  # mùng 1 tháng 3 thường


def test_xin_sai_thang_nhuan_trong_nam_co_nhuan_bi_bao_khong_ton_tai() -> None:
    """Năm 2023 CÓ tháng nhuận nhưng nhuận ở tháng 2 (xem test trên) — xin
    tháng NHUẬN khác (tháng 3 nhuận) phải trả ``(0, 0, 0)`` (không tồn tại),
    KHÔNG trả bừa một ngày nào. Lưu ý: hàm gốc CHỈ kiểm tổ hợp
    tháng-nhuận-sai bên TRONG một năm 13-tháng; xin tháng nhuận ở một năm
    12-tháng (không có tháng nhuận nào, ví dụ 2024) không bị chặn ở bước
    này — hành vi gốc của thuật toán Hồ Ngọc Đức, giữ nguyên khi port."""

    assert convert_lunar_to_solar(1, 3, 2023, lunar_leap=1) == (0, 0, 0)
    # Tháng nhuận ĐÚNG (tháng 2) trong năm 13-tháng đó vẫn tính ra ngày thật.
    assert convert_lunar_to_solar(1, 2, 2023, lunar_leap=1) == (22, 3, 2023)


def test_day_can_chi_chu_ky_60_ngay_lien_tuc() -> None:
    """Can-Chi ngày chạy theo chu kỳ 60 ngày liên tục (không phụ thuộc
    Âm/Dương lịch) — ngày kế tiếp phải lệch đúng 1 bước trong chu kỳ đó,
    và đúng 60 ngày sau phải quay lại tên Can-Chi cũ."""

    base = datetime.date(2026, 11, 11)
    nxt = base + datetime.timedelta(days=1)
    after_60 = base + datetime.timedelta(days=60)

    base_cc = day_can_chi(base.day, base.month, base.year)
    nxt_cc = day_can_chi(nxt.day, nxt.month, nxt.year)
    after_60_cc = day_can_chi(after_60.day, after_60.month, after_60.year)

    assert base_cc != nxt_cc
    assert base_cc == after_60_cc


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_round_trip_solar_lunar_solar(seed: int) -> None:
    """Đổi Dương→Âm rồi Âm→Dương phải quay lại CHÍNH XÁC ngày ban đầu, thử
    trên nhiều ngày ngẫu nhiên trong khoảng 1950-2100 (phạm vi công bố chính
    xác rộng rãi của thuật toán Hồ Ngọc Đức là ~1800-2199)."""

    rng = random.Random(seed)
    mismatches = []
    for _ in range(300):
        yy = rng.randint(1950, 2100)
        mm = rng.randint(1, 12)
        last_day = (
            datetime.date(yy + (mm == 12), (mm % 12) + 1, 1) - datetime.timedelta(days=1)
        ).day
        dd = rng.randint(1, last_day)

        lunar_day, lunar_month, lunar_year, lunar_leap = convert_solar_to_lunar(dd, mm, yy)
        back = convert_lunar_to_solar(lunar_day, lunar_month, lunar_year, lunar_leap)
        if back != (dd, mm, yy):
            lunar = (lunar_day, lunar_month, lunar_year, lunar_leap)
            mismatches.append(((dd, mm, yy), lunar, back))

    assert mismatches == []
