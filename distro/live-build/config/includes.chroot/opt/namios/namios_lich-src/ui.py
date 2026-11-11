"""Cửa sổ PySide6 cho NaMiLịch — CHỈ chạy trên desktop session thật, KHÔNG
chạy trong môi trường build/test headless hiện tại (xem ``__main__.py``).

Mọi logic tính toán thật (đổi lịch, tìm lễ sắp tới, lưu nhắc giỗ) nằm ở
``namios_lich.lunar``/``namios_lich.holidays`` — file này CHỈ lắp widget rồi
gọi, KHÔNG chứa quyết định tính toán nào của riêng nó (để test được toàn bộ
logic mà không cần PySide6/desktop — xem ``tests/unit/lich/``).

Bố cục: (1) panel "Hôm nay" (dương + âm + Can-Chi + lễ sắp tới), (2) lưới
tháng (dương lịch to, âm lịch nhỏ dưới mỗi ngày, tô màu lễ/hôm nay), (3) nút
thêm/xoá nhắc giỗ theo âm lịch (lặp hằng năm).

``verified_on_host: NO`` — bố cục/hành vi dưới đây CHƯA được xác nhận bằng
mắt trên một desktop KDE thật (container này không có display); chỉ xác
nhận logic lịch/dữ liệu bằng test thuần Python (``tests/unit/lich/``)."""

# mypy: ignore-errors
# PySide6 không có stub/không được cài trong môi trường build headless hiện
# tại — mypy coi mọi import Qt là ``Any``. File này KHÔNG chứa quyết định
# tính toán (chỉ lắp UI rồi gọi namios_lich.lunar/holidays, nơi mypy strict
# vẫn áp dụng đầy đủ), nên tắt mypy riêng cho file này thay vì nới lỏng toàn
# cục — cùng cách namios_welcome/ui.py đã làm.

from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

from namios_lich.holidays import (
    add_reminder,
    holidays_on_date,
    load_holiday_defs,
    load_reminders,
    reminder_defs,
    remove_reminder,
    upcoming_holidays,
)
from namios_lich.lunar import day_can_chi_for_date, month_can_chi, solar_date_to_lunar, year_can_chi
from PySide6.QtCore import Qt  # type: ignore[import-not-found]
from PySide6.QtGui import QColor, QFont  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

#: Màu thương hiệu NaMiOS v3 "Đông Sơn" (navy/gold/vermilion) — mapped từ
#: fallback "Sen Việt" v2.0 cũ, cập nhật 11/11/2026; chép giá trị từ
#: ``usr/share/namios-branding/logo/brand.json`` (xem hàm ``_load_brand_colors``
#: cố gắng đọc file đó trước; đây là giá trị fallback TĨNH nếu ảnh không có
#: gói branding ở đúng đường dẫn — KHÔNG để UI vỡ vì thiếu 1 file JSON).
#: Ở đây "canh"/"canh_dark" dùng để tô viền/nổi bật ngày hôm nay + lễ chính
#: thức trong lịch -> vai trò "signature accent/highlight" => map sang GOLD
#: (khác với namios_antoan/namios_dichvu, nơi "canh" tô header/nút hành động
#: => map sang VERMILION ở 2 module đó).
_FALLBACK_COLORS = {
    "canh": "#DEA93E",
    "canh_dark": "#DEA93E",
    "vang_tam": "#DEA93E",
    "vang_nuoc": "#DEA93E",
    "muc_dem": "#092D4F",
    "chu_muc": "#092D4F",
}

_BRAND_JSON_PATH = Path("/usr/share/namios-branding/logo/brand.json")

#: Tên thứ trong tuần tiếng Việt, bắt đầu từ Thứ Hai (``calendar`` chuẩn
#: Python cũng coi Thứ Hai = 0).
_WEEKDAY_NAMES_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
_WEEKDAY_SHORT_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

_MONTH_NAMES_VI = [
    "",
    "Tháng Một",
    "Tháng Hai",
    "Tháng Ba",
    "Tháng Tư",
    "Tháng Năm",
    "Tháng Sáu",
    "Tháng Bảy",
    "Tháng Tám",
    "Tháng Chín",
    "Tháng Mười",
    "Tháng Mười Một",
    "Tháng Mười Hai",
]


def _load_brand_colors() -> dict[str, str]:
    """Đọc màu thương hiệu từ ``brand.json`` nếu có trên máy; nếu không (dev
    checkout chưa cài gói branding, hoặc file hỏng) dùng ``_FALLBACK_COLORS``
    đã chép sẵn — KHÔNG bao giờ raise, KHÔNG làm UI vỡ vì thiếu branding."""

    import json

    try:
        raw = json.loads(_BRAND_JSON_PATH.read_text(encoding="utf-8"))
        colors = raw.get("colors", {})
        if isinstance(colors, dict) and colors:
            merged = dict(_FALLBACK_COLORS)
            merged.update({k: v for k, v in colors.items() if isinstance(v, str)})
            return merged
    except (OSError, ValueError, AttributeError):
        pass
    return dict(_FALLBACK_COLORS)


class _AddReminderDialog(QDialog):
    """Hộp thoại nhỏ: thêm một nhắc giỗ lặp hằng năm theo ngày ÂM lịch."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Thêm nhắc giỗ (âm lịch)")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Tên (ví dụ: Ông Nội, Bà Ngoại...):"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        day_row = QHBoxLayout()
        day_row.addWidget(QLabel("Ngày âm:"))
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 30)
        self.day_spin.setValue(1)
        day_row.addWidget(self.day_spin)
        day_row.addWidget(QLabel("Tháng âm:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(1)
        day_row.addWidget(self.month_spin)
        layout.addLayout(day_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def values(self) -> tuple[str, int, int]:
        return self.name_edit.text().strip(), self.day_spin.value(), self.month_spin.value()


class _ManageRemindersDialog(QDialog):
    """Hộp thoại: xem danh sách nhắc giỗ đã thêm và XOÁ mục không cần nữa
    (dùng backend ``holidays.load_reminders``/``remove_reminder`` đã có test)."""

    def __init__(self, config_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config_dir = config_dir
        self._reminders: list = []
        self.setWindowTitle("Quản lý nhắc giỗ")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Nhắc giỗ đã thêm — chọn một mục rồi bấm Xoá:"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        row = QHBoxLayout()
        self.remove_button = QPushButton("Xoá mục đã chọn")
        self.remove_button.clicked.connect(self._on_remove)
        row.addWidget(self.remove_button)
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.accept)
        row.addWidget(close_button)
        layout.addLayout(row)

        self.setLayout(layout)
        self._reload()

    def _reload(self) -> None:
        self.list_widget.clear()
        self._reminders = load_reminders(self._config_dir)
        for r in self._reminders:
            self.list_widget.addItem(
                QListWidgetItem(f"{r.name_vi} — {r.lunar_day}/{r.lunar_month} âm lịch")
            )
        self.remove_button.setEnabled(bool(self._reminders))

    def _on_remove(self) -> None:
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self._reminders):
            QMessageBox.information(self, "Lịch", "Hãy chọn một nhắc giỗ để xoá.")
            return
        name_vi = self._reminders[idx].name_vi
        remove_reminder(self._config_dir, name_vi)
        self._reload()


class _DayCell(QFrame):
    """Một ô ngày trong lưới tháng — dương lịch to, âm lịch nhỏ bên dưới."""

    def __init__(self, colors: dict[str, str]) -> None:
        super().__init__()
        self._colors = colors
        self.setFrameShape(QFrame.Box)
        self.setMinimumSize(72, 56)
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)
        self.solar_label = QLabel("")
        self.solar_label.setAlignment(Qt.AlignCenter)
        solar_font = QFont()
        solar_font.setPointSize(11)
        solar_font.setBold(True)
        self.solar_label.setFont(solar_font)
        self.lunar_label = QLabel("")
        self.lunar_label.setAlignment(Qt.AlignCenter)
        lunar_font = QFont()
        lunar_font.setPointSize(8)
        self.lunar_label.setFont(lunar_font)
        layout.addWidget(self.solar_label)
        layout.addWidget(self.lunar_label)
        self.setLayout(layout)
        self.set_empty()

    def set_empty(self) -> None:
        self.solar_label.setText("")
        self.lunar_label.setText("")
        self.setStyleSheet("")

    def set_day(self, d: date, is_today: bool, is_weekend: bool, holiday_names: list[str]) -> None:
        lunar = solar_date_to_lunar(d)
        self.solar_label.setText(str(d.day))
        lunar_text = f"{lunar.day}/{lunar.month}" + ("N" if lunar.leap else "")
        self.lunar_label.setText(lunar_text)

        bg = "transparent"
        border = "#888888"
        fg = "#dd3333" if is_weekend else "palette(text)"
        if holiday_names:
            bg = self._colors["vang_tam"]
            fg = self._colors["muc_dem"]
        if is_today:
            border = self._colors["canh"]
            bg = self._colors.get("canh_light", self._colors["canh"])
        tooltip = d.strftime("%d/%m/%Y") + f" — âm lịch {lunar.format_vi()}"
        if holiday_names:
            tooltip += "\nLễ: " + ", ".join(holiday_names)
        self.setToolTip(tooltip)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 2px solid {border}; border-radius: 4px; }}"
            f"QLabel {{ color: {fg}; background: transparent; border: none; }}"
        )


class NaMiLichWindow(QMainWindow):
    """Cửa sổ chính NaMiLịch — panel 'Hôm nay' + lưới tháng điều hướng được."""

    def __init__(self, config_dir: Path, today_fn=date.today) -> None:
        super().__init__()
        self._config_dir = config_dir
        self._today_fn = today_fn
        self._colors = _load_brand_colors()
        self._holiday_defs = load_holiday_defs()
        self._view_year = self._today_fn().year
        self._view_month = self._today_fn().month

        self.setWindowTitle("Lịch — Âm lịch Việt Nam")
        self.resize(640, 560)

        central = QWidget()
        root = QVBoxLayout()
        central.setLayout(root)
        self.setCentralWidget(central)

        root.addWidget(self._build_today_panel())

        nav_row = QHBoxLayout()
        self.prev_button = QPushButton("◀ Tháng trước")
        self.prev_button.clicked.connect(self._on_prev_month)
        self.month_label = QLabel("")
        self.month_label.setAlignment(Qt.AlignCenter)
        month_font = QFont()
        month_font.setPointSize(13)
        month_font.setBold(True)
        self.month_label.setFont(month_font)
        self.next_button = QPushButton("Tháng sau ▶")
        self.next_button.clicked.connect(self._on_next_month)
        self.today_button = QPushButton("Hôm nay")
        self.today_button.clicked.connect(self._on_go_today)
        nav_row.addWidget(self.prev_button)
        nav_row.addWidget(self.month_label, stretch=1)
        nav_row.addWidget(self.next_button)
        nav_row.addWidget(self.today_button)
        root.addLayout(nav_row)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        self.grid_widget.setLayout(self.grid_layout)
        root.addWidget(self.grid_widget)

        self._weekday_labels: list[QLabel] = []
        for i, name in enumerate(_WEEKDAY_SHORT_VI):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            bold = QFont()
            bold.setBold(True)
            lbl.setFont(bold)
            self.grid_layout.addWidget(lbl, 0, i)
            self._weekday_labels.append(lbl)

        self._cells: list[_DayCell] = []
        for row in range(1, 7):
            for col in range(7):
                cell = _DayCell(self._colors)
                self.grid_layout.addWidget(cell, row, col)
                self._cells.append(cell)

        reminder_row = QHBoxLayout()
        self.add_reminder_button = QPushButton("+ Thêm nhắc giỗ (âm lịch)")
        self.add_reminder_button.clicked.connect(self._on_add_reminder)
        reminder_row.addWidget(self.add_reminder_button)
        self.manage_reminder_button = QPushButton("Quản lý nhắc giỗ")
        self.manage_reminder_button.clicked.connect(self._on_manage_reminders)
        reminder_row.addWidget(self.manage_reminder_button)
        root.addLayout(reminder_row)

        self._refresh_month_grid()

    # -- Panel "Hôm nay" ----------------------------------------------------

    def _build_today_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout()
        panel.setLayout(layout)

        left = QVBoxLayout()
        today = self._today_fn()
        lunar = solar_date_to_lunar(today)
        weekday_name = _WEEKDAY_NAMES_VI[today.weekday()]
        self.today_solar_label = QLabel(f"{weekday_name}, {today.strftime('%d/%m/%Y')}")
        big_font = QFont()
        big_font.setPointSize(16)
        big_font.setBold(True)
        self.today_solar_label.setFont(big_font)
        self.today_lunar_label = QLabel(
            f"Âm lịch: {lunar.day}/{lunar.month}"
            + ("  (tháng nhuận)" if lunar.leap else "")
            + f"  —  Năm {year_can_chi(lunar.year)}"
        )
        self.today_canchi_label = QLabel(
            f"Ngày {day_can_chi_for_date(today)}  ·  Tháng {month_can_chi(lunar.month, lunar.year)}"
        )
        left.addWidget(self.today_solar_label)
        left.addWidget(self.today_lunar_label)
        left.addWidget(self.today_canchi_label)
        layout.addLayout(left, stretch=1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Lễ sắp tới:"))
        self.upcoming_list = QListWidget()
        right.addWidget(self.upcoming_list)
        layout.addLayout(right, stretch=1)
        self._refresh_upcoming()

        return panel

    def _refresh_upcoming(self) -> None:
        """Dựng lại danh sách "Lễ sắp tới" (hợp nhất lễ chính thức + nhắc giỗ
        người dùng). Gọi khi mở app VÀ sau khi thêm/xoá nhắc giỗ để danh sách
        cập nhật NGAY, không phải đóng-mở lại app."""

        self.upcoming_list.clear()
        today = self._today_fn()
        reminders = load_reminders(self._config_dir)
        all_defs = self._holiday_defs + reminder_defs(reminders)
        for item in upcoming_holidays(today, all_defs, count=5):
            when = "Hôm nay" if item.days_remaining == 0 else f"còn {item.days_remaining} ngày"
            text = f"{item.solar_date.strftime('%d/%m/%Y')} — {item.name_vi} ({when})"
            list_item = QListWidgetItem(text)
            if item.cong_lap:
                list_item.setForeground(QColor(self._colors["canh_dark"]))
            self.upcoming_list.addItem(list_item)

    # -- Lưới tháng -----------------------------------------------------------

    def _refresh_month_grid(self) -> None:
        self.month_label.setText(f"{_MONTH_NAMES_VI[self._view_month]} {self._view_year}")
        today = self._today_fn()
        reminders = load_reminders(self._config_dir)
        all_defs = self._holiday_defs + reminder_defs(reminders)

        cal = calendar.Calendar(firstweekday=0)  # 0 = Thứ Hai
        month_days = list(cal.itermonthdates(self._view_year, self._view_month))
        # itermonthdates luôn trả đủ số tuần (có thể lẹm ngày tháng trước/sau)
        # -- giữ nguyên, chỉ làm mờ ngày không thuộc tháng hiện tại.
        for idx, cell in enumerate(self._cells):
            if idx >= len(month_days):
                cell.set_empty()
                continue
            d = month_days[idx]
            if d.month != self._view_month:
                cell.set_empty()
                continue
            holiday_names = [h.name_vi for h in holidays_on_date(d, all_defs)]
            is_weekend = d.weekday() == 6  # Chủ Nhật — quy ước đỏ phổ biến
            cell.set_day(
                d, is_today=(d == today), is_weekend=is_weekend, holiday_names=holiday_names
            )

    def _on_prev_month(self) -> None:
        if self._view_month == 1:
            self._view_month = 12
            self._view_year -= 1
        else:
            self._view_month -= 1
        self._refresh_month_grid()

    def _on_next_month(self) -> None:
        if self._view_month == 12:
            self._view_month = 1
            self._view_year += 1
        else:
            self._view_month += 1
        self._refresh_month_grid()

    def _on_go_today(self) -> None:
        today = self._today_fn()
        self._view_year = today.year
        self._view_month = today.month
        self._refresh_month_grid()

    # -- Nhắc giỗ -------------------------------------------------------------

    def _on_add_reminder(self) -> None:
        dialog = _AddReminderDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        name_vi, lunar_day, lunar_month = dialog.values()
        if not name_vi:
            QMessageBox.warning(self, "Lịch", "Cần nhập tên trước khi thêm nhắc giỗ.")
            return
        add_reminder(self._config_dir, name_vi, lunar_day, lunar_month)
        self._refresh_month_grid()
        self._refresh_upcoming()
        QMessageBox.information(
            self,
            "Lịch",
            f"Đã thêm nhắc giỗ '{name_vi}' ngày {lunar_day}/{lunar_month} âm lịch (lặp hằng năm).",
        )

    def _on_manage_reminders(self) -> None:
        dialog = _ManageRemindersDialog(self._config_dir, self)
        dialog.exec()
        # Sau khi có thể đã xoá vài mục → cập nhật lại lưới tháng + lễ sắp tới.
        self._refresh_month_grid()
        self._refresh_upcoming()
