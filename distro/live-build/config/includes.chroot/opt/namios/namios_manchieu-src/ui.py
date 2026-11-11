"""Cửa sổ PySide6 "Máy chiếu & Màn hình ngoài" — CHỈ chạy trên desktop
session thật (cần PySide6 + ``kscreen-doctor``), KHÔNG chạy trong môi trường
build/test headless hiện tại (xem ``__main__.py``).

Mọi quyết định "chế độ nào làm gì"/"máy nào là trong, máy nào là ngoài" nằm
ở ``namios_manchieu.display`` (Python thuần, test được — xem
``tests/unit/manchieu/``); mọi lệnh gọi ``kscreen-doctor`` thật nằm ở
``namios_manchieu.backend``. File này CHỈ lắp UI (4 nút to + dòng trạng thái
+ Làm mới) rồi gọi hai module đó, chạy trong ``QThread`` riêng để không treo
giao diện khi gọi lệnh con (có thể chậm vài giây trên máy yếu).

``verified_on_host: NO`` — bố cục/hành vi CHƯA được xác nhận bằng mắt trên
một desktop KDE Plasma thật có nhiều màn hình (container này không có
display/kscreen-doctor); chỉ xác nhận logic ``display``/``backend`` bằng
test thuần Python."""

# mypy: ignore-errors
# PySide6 không có stub/không được cài trong môi trường build headless hiện
# tại — mypy coi mọi import Qt là ``Any``. File này KHÔNG chứa quyết định
# "chế độ nào làm gì" (chỉ lắp UI rồi gọi namios_manchieu.display/backend,
# nơi mypy strict vẫn áp dụng đầy đủ) — tắt mypy riêng cho file này, cùng quy
# ước ``namios_antoan.ui``/``namios_lich.ui``.

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from namios_manchieu import backend, display
from namios_manchieu.branding import build_stylesheet
from PySide6.QtCore import QObject, QThread, Signal  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

__all__ = ["ManChieuWindow"]


# ---------------------------------------------------------------------------
# Chạy ``fn()`` nền trong QThread riêng — bản GỌN của khuôn
# ``namios_antoan.ui._Job``/``_AsyncSlot`` (ở đó cần tái dùng cho 5 thẻ × tới
# 3 hành động; ở đây chỉ có đúng 2 việc nền: đọc output + áp chế độ, nên gộp
# lại một lớp, KHÔNG cần tách slot riêng theo "thẻ").
# ---------------------------------------------------------------------------
class _Job(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem _Job của namios_antoan
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


class ManChieuWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Máy chiếu & Màn hình ngoài")
        self.resize(560, 420)
        self.setStyleSheet(build_stylesheet())
        self._thread: QThread | None = None
        self._worker: _Job | None = None
        self._latest_outputs: tuple[display.OutputInfo, ...] = ()
        self._mode_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self.refresh()

    def closeEvent(self, event) -> None:  # noqa: N802 (tên override của Qt)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Lắp widget
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("ManChieuRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 14, 16, 14)
        body_layout.setSpacing(12)

        body_layout.addWidget(self._build_status_bar())

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(12)
        specs = [
            (display.MODE_MIRROR, "🪞 Nhân đôi", "Cùng nội dung trên cả hai màn hình", 0, 0),
            (display.MODE_EXTEND, "🖥️ Mở rộng", "Màn ngoài ở bên phải màn trong", 0, 1),
            (display.MODE_INTERNAL_ONLY, "💻 Chỉ màn hình này", "Tắt màn hình ngoài", 1, 0),
            (display.MODE_EXTERNAL_ONLY, "📽️ Chỉ màn hình ngoài", "Dùng cho máy chiếu", 1, 1),
        ]
        for mode, label, hint, row, col in specs:
            cell = QVBoxLayout()
            btn = QPushButton(f"{label}\n{hint}")
            btn.setObjectName("ModeButton")
            btn.setMinimumHeight(90)
            btn.clicked.connect(lambda _checked=False, m=mode: self._on_mode_clicked(m))
            self._mode_buttons[mode] = btn
            cell.addWidget(btn)
            grid.addLayout(cell, row, col)
        body_layout.addWidget(grid_widget, stretch=1)

        footer = QLabel(
            "Muốn chỉnh chi tiết hơn (độ phân giải, xoay màn hình...): mở Cài đặt → "
            "Hiển thị. Đổi chế độ sẽ áp dụng NGAY trên máy — không có nút hoàn tác, "
            "bấm chế độ khác để đổi lại."
        )
        footer.setObjectName("FooterDisclaimer")
        footer.setWordWrap(True)
        body_layout.addWidget(footer)

        root_layout.addWidget(body, stretch=1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(2)
        title = QLabel("Máy chiếu & Màn hình ngoài")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel(
            "Chọn nhanh cách hiển thị khi cắm máy chiếu/màn hình ngoài — kiểu Win+P của Windows"
        )
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_status_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("StatusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 10, 12, 10)
        self._status_label = QLabel("Đang kiểm tra màn hình...")
        self._status_label.setObjectName("StatusLabel")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label, stretch=1)
        self._refresh_btn = QPushButton("Làm mới")
        self._refresh_btn.setObjectName("RefreshButton")
        self._refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self._refresh_btn)
        return bar

    # ------------------------------------------------------------------
    # Làm mới trạng thái — chạy nền.
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        if self._thread is not None:
            return  # đang có việc nền chạy — chặn double-click (Làm mới hoặc 1 chế độ).
        self._set_busy(True, "Đang kiểm tra màn hình...")
        self._start_job(backend.read_outputs, self._on_refresh_done, self._on_job_failed)

    def _on_refresh_done(self, result: backend.BackendResult) -> None:
        self._set_busy(False)
        self._latest_outputs = result.outputs
        if not result.success:
            self._status_label.setText(result.message)
            self._set_mode_buttons_enabled(False)
            return
        self._status_label.setText(self._format_status(result.outputs))
        self._update_mode_buttons_enabled(result.outputs)

    @staticmethod
    def _format_status(outputs: tuple[display.OutputInfo, ...]) -> str:
        parts: list[str] = []
        for o in outputs:
            if not o.connected:
                continue
            kind_label = {
                "internal": "Màn hình trong",
                "external": "Màn hình ngoài",
                "unknown": "Không rõ",
            }[o.kind]
            state = "đang bật" if o.enabled else "đang tắt"
            parts.append(f"{kind_label}: {o.name} ({state})")
        return " | ".join(parts) if parts else "Không có màn hình nào đang kết nối."

    def _update_mode_buttons_enabled(self, outputs: tuple[display.OutputInfo, ...]) -> None:
        try:
            display.pick_displays(outputs)
            enabled = True
        except display.DisplayError:
            enabled = False
        self._set_mode_buttons_enabled(enabled)

    def _set_mode_buttons_enabled(self, enabled: bool) -> None:
        for btn in self._mode_buttons.values():
            btn.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Bấm 1 trong 4 chế độ — xác nhận trước khi đổi THẬT.
    # ------------------------------------------------------------------
    def _on_mode_clicked(self, mode: str) -> None:
        try:
            display_plan = display.plan(mode, self._latest_outputs)
        except display.DisplayError as exc:
            QMessageBox.information(self, "Máy chiếu & Màn hình ngoài", exc.message)
            self.refresh()
            return

        confirmed = QMessageBox.question(
            self,
            display.MODE_LABELS_VI[mode],
            display_plan.description_vi + "\n\nTiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return

        if self._thread is not None:
            return
        self._set_busy(True, f"Đang áp dụng '{display.MODE_LABELS_VI[mode]}'...")
        self._start_job(lambda: backend.apply_mode(mode), self._on_apply_done, self._on_job_failed)

    def _on_apply_done(self, result: backend.BackendResult) -> None:
        self._set_busy(False)
        self._latest_outputs = result.outputs
        box = QMessageBox(self)
        box.setWindowTitle("Máy chiếu & Màn hình ngoài")
        box.setIcon(QMessageBox.Icon.Information if result.success else QMessageBox.Icon.Warning)
        box.setText(result.message or "(không có nội dung)")
        box.exec()
        self.refresh()

    def _on_job_failed(self, message: str) -> None:
        self._set_busy(False)
        title = "Máy chiếu & Màn hình ngoài"
        QMessageBox.warning(
            self,
            title,
            "Không thực hiện được thao tác vừa rồi do gặp lỗi ngoài dự kiến. "
            "Hãy bấm 'Làm mới' để kiểm tra lại màn hình, hoặc thử lại thao tác đó.\n"
            f"Chi tiết kỹ thuật: {message}",
        )

    def _set_busy(self, busy: bool, status_text: str | None = None) -> None:
        self._refresh_btn.setEnabled(not busy)
        if busy:
            self._set_mode_buttons_enabled(False)
        if status_text is not None:
            self._status_label.setText(status_text)

    def _start_job(
        self,
        fn: Callable[[], Any],
        on_done: Callable[[Any], None],
        on_fail: Callable[[str], None],
    ) -> None:
        worker = _Job(fn)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(on_done)
        worker.failed.connect(on_fail)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(self._clear_job)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _clear_job(self) -> None:
        self._thread = None
        self._worker = None
