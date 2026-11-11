"""``namios_manchieu`` — "Máy chiếu & Màn hình ngoài": bộ chọn nhanh 1-chạm
4 chế độ hiển thị (Nhân đôi/Mở rộng/Chỉ màn hình này/Chỉ màn hình ngoài),
tương đương Win+P của Windows. KDE Plasma đã có Cài đặt Hiển thị đầy đủ
(``kcm_kscreen``, mở qua ``namios-control-panel --category display`` —
xem ``do_display()``) nhưng KHÔNG có đường tắt 1-chạm/phím tắt cho 4 chế độ
phổ biến nhất — module này là lối THAM NHANH, KCM vẫn là lối chỉnh chi tiết
(hai công cụ không thay thế nhau).

Cùng quy ước ``namios_antoan``/``namios_lich``: ``display`` (phân tích
output ``kscreen-doctor`` + dựng lệnh) và ``backend`` (gọi lệnh thật qua
``run_argv``) là Python THUẦN, test được không cần PySide6/display thật —
xem ``tests/unit/manchieu/``. ``ui``/``__main__`` CHỈ chạy trên desktop
session thật có PySide6 + ``kscreen-doctor`` (gói ``libkscreen-bin``, do gói
``kscreen`` đã khai ở ``0100-desktop-kde.list.chroot`` kéo theo qua Depends
cứng — xem comment trong hook 0311 để biết cách đã xác nhận điều này).

TRUNG THỰC BẮT BUỘC: module này KHÔNG BAO GIỜ giả vờ "đã tìm thấy máy
chiếu"/"đã áp dụng xong" khi thực tế không đúng — khi chỉ có 1 màn hình kết
nối, hiển thị đúng câu hướng dẫn cắm cáp (xem
``namios_manchieu.display.NO_EXTERNAL_MESSAGE``), KHÔNG tự chế kết quả
thành công giả."""

from __future__ import annotations

from namios_manchieu.display import (
    ALL_MODES,
    MODE_EXTEND,
    MODE_EXTERNAL_ONLY,
    MODE_INTERNAL_ONLY,
    MODE_LABELS_VI,
    MODE_MIRROR,
    DisplayError,
    DisplayPlan,
    ModeInfo,
    OutputInfo,
)

__all__ = [
    "ALL_MODES",
    "MODE_MIRROR",
    "MODE_EXTEND",
    "MODE_INTERNAL_ONLY",
    "MODE_EXTERNAL_ONLY",
    "MODE_LABELS_VI",
    "ModeInfo",
    "OutputInfo",
    "DisplayError",
    "DisplayPlan",
]
