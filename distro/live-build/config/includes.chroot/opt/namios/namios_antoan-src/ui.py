"""Cửa sổ Trung tâm An toàn PySide6 — CHỈ chạy trên desktop session thật,
KHÔNG chạy trong môi trường build/test headless (cùng ghi chú
``namios_assistant.ui``/``namios_welcome.ui``).

Mọi quyết định "trạng thái thật là gì"/"hành động làm gì" nằm ở
``namios_antoan.probes``/``namios_antoan.actions`` (Python thuần, test được
không cần GUI) — file này CHỈ lắp 5 "thẻ" (Cập nhật/Tường lửa/AppArmor/Quét
virus/Sao lưu) + chạy probe/action trong ``QThread`` riêng (tránh treo giao
diện khi gọi lệnh con có thể mất vài giây — vd ``apt list --upgradable``,
``clamscan``, hay chờ người dùng nhập mật khẩu polkit).

KHÔNG có logic an toàn/quyết định trạng thái tự chế ở tầng UI — mỗi nút chỉ
gọi đúng một hàm ``probes``/``actions`` rồi hiển thị kết quả nguyên văn."""

# mypy: ignore-errors
# PySide6 không có stub/không được cài trong môi trường build headless hiện
# tại — mypy coi mọi import Qt là ``Any``. File này KHÔNG chứa quyết định an
# toàn/business logic (chỉ lắp UI rồi gọi ``namios_antoan.probes``/
# ``actions``), nên tắt mypy riêng cho file này thay vì nới lỏng toàn cục
# (cùng quy ước ``namios_assistant.ui``).

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, Signal  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from namios_antoan import actions, probes
from namios_antoan.branding import (
    STATUS_OFF,
    STATUS_OK,
    STATUS_UNKNOWN,
    build_stylesheet,
)
from namios_i18n import Lang, resolve_lang, t

__all__ = ["AntoanWindow"]


# ---------------------------------------------------------------------------
# Hạ tầng chạy bất đồng bộ dùng chung cho mọi thẻ — generalize đúng khuôn
# ``_AskWorker``/``_OcrWorker`` của ``namios_assistant.ui`` (QObject chạy
# trong QThread riêng, finished/failed signal) thành MỘT lớp tái dùng cho cả
# probe (đọc trạng thái) và action (bật/quét/mở), vì cả hai đều chỉ là "gọi
# một hàm không tham số, trả 1 kết quả, có thể lỗi" — tránh viết lại cùng
# 15 điểm gọi (5 thẻ × tới 3 hành động mỗi thẻ).
# ---------------------------------------------------------------------------
class _Job(QObject):
    """Chạy ``fn()`` (không tham số) trong luồng riêng. Bắt MỌI ``Exception``
    thành ``failed`` — fail-safe tuyệt đối, một lỗi không lường được ở
    ``probes``/``actions`` không bao giờ làm sập cửa sổ."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring lớp
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


class _AsyncSlot:
    """Giữ (QThread, _Job) đang chạy cho MỘT nút/hành động của một thẻ —
    chặn double-click khi đang chạy (``start`` trả ``False``), tự dọn khi
    xong (cùng khuôn dọn ``_thread``/``_worker`` của
    ``namios_assistant.ui.AssistantWindow``, tách thành lớp tiện ích thay vì
    lặp lại ở 5 thẻ)."""

    def __init__(self, owner: QObject) -> None:
        self._owner = owner
        self._thread: QThread | None = None
        self._worker: _Job | None = None

    @property
    def busy(self) -> bool:
        return self._thread is not None

    def start(
        self,
        fn: Callable[[], Any],
        on_done: Callable[[Any], None],
        on_fail: Callable[[str], None],
    ) -> bool:
        if self.busy:
            return False
        worker = _Job(fn)
        thread = QThread(self._owner)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(on_done)
        worker.failed.connect(on_fail)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(self._clear)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()
        return True

    def _clear(self) -> None:
        self._thread = None
        self._worker = None


def _status_dot_color(installed: bool, ok: bool | None) -> str:
    if not installed:
        return STATUS_UNKNOWN
    if ok is True:
        return STATUS_OK
    if ok is False:
        return STATUS_OFF
    return STATUS_UNKNOWN


def _show_result(parent: QWidget, *, success: bool, message: str, lang: Lang) -> None:
    """Hộp thoại kết quả DÙNG CHUNG cho mọi hành động (enable/scan/update
    chữ ký/xem chi tiết) — hiển thị nguyên văn ``ActionResult.message``
    (KHÔNG diễn giải lại/KHÔNG tô vẽ thành "đã an toàn")."""

    title_key = "antoan.ui.dialog.result.title_ok" if success else "antoan.ui.dialog.result.title_fail"
    box = QMessageBox(parent)
    box.setWindowTitle(t(title_key, lang=lang))
    box.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning)
    if len(message) > 600:
        box.setText(message[:600] + "\n\n[... xem đầy đủ ở 'Show Details' ...]")
        box.setDetailedText(message)
    else:
        box.setText(message or "(không có nội dung)")
    box.exec()


# ---------------------------------------------------------------------------
# Lớp cơ sở cho mỗi "thẻ" trạng thái — lắp khung chung (chấm màu + tiêu đề +
# nút Làm mới + headline + detail + hàng nút hành động riêng của thẻ con),
# chạy probe trong QThread. Thẻ con chỉ cần cung cấp ``probe_fn`` +
# ``_build_actions`` (hàng nút riêng).
# ---------------------------------------------------------------------------
class _StatusCardBase(QFrame):
    def __init__(
        self,
        *,
        title_key: str,
        probe_fn: Callable[[], probes.CardStatus],
        lang: Lang,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatusCard")
        self._probe_fn = probe_fn
        self._lang = lang
        self._probe_slot = _AsyncSlot(self)
        self._action_slot = _AsyncSlot(self)
        self._latest_status: probes.CardStatus | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self._dot = QLabel()
        self._dot.setFixedSize(14, 14)
        self._set_dot_color(STATUS_UNKNOWN)
        title_label = QLabel(t(title_key, lang=lang))
        title_label.setObjectName("CardTitle")
        self._refresh_btn = QPushButton(t("antoan.ui.button.refresh", lang=lang))
        self._refresh_btn.clicked.connect(self.refresh)
        top_row.addWidget(self._dot)
        top_row.addSpacing(6)
        top_row.addWidget(title_label)
        top_row.addStretch(1)
        top_row.addWidget(self._refresh_btn)
        layout.addLayout(top_row)

        self._headline_label = QLabel(t("antoan.ui.status.checking", lang=lang))
        self._headline_label.setObjectName("CardHeadline")
        self._headline_label.setWordWrap(True)
        layout.addWidget(self._headline_label)

        self._detail_label = QLabel("")
        self._detail_label.setObjectName("CardDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        self._actions_row = QHBoxLayout()
        layout.addLayout(self._actions_row)
        self._build_actions(self._actions_row)

    # ------------------------------------------------------------------
    # Hook cho thẻ con — override để thêm nút hành động riêng.
    # ------------------------------------------------------------------
    def _build_actions(self, row: QHBoxLayout) -> None:
        return

    def _on_status_rendered(self, status: probes.CardStatus) -> None:
        return

    # ------------------------------------------------------------------
    # Probe (đọc trạng thái) — chạy trong QThread, KHÔNG chặn UI.
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        if not self._probe_slot.start(self._probe_fn, self._on_probe_done, self._on_probe_failed):
            return
        self._refresh_btn.setEnabled(False)
        self._headline_label.setText(t("antoan.ui.status.checking", lang=self._lang))

    def _on_probe_done(self, status: probes.CardStatus) -> None:
        self._refresh_btn.setEnabled(True)
        self._latest_status = status
        self._set_dot_color(_status_dot_color(status.installed, status.ok))
        if not status.installed:
            headline = t("antoan.ui.card.not_installed_prefix", lang=self._lang) + status.headline
            detail = status.detail
            if status.install_hint:
                detail = (
                    detail
                    + ("\n" if detail else "")
                    + t("antoan.ui.card.install_hint_prefix", lang=self._lang)
                    + status.install_hint
                )
        else:
            headline = status.headline
            detail = status.detail
        self._headline_label.setText(headline)
        self._detail_label.setText(detail)
        self._on_status_rendered(status)

    def _on_probe_failed(self, message: str) -> None:
        self._refresh_btn.setEnabled(True)
        self._set_dot_color(STATUS_UNKNOWN)
        self._headline_label.setText("Có lỗi không lường được khi kiểm tra trạng thái.")
        self._detail_label.setText(message)

    def _set_dot_color(self, color: str) -> None:
        self._dot.setStyleSheet(f"border-radius:7px; background-color:{color};")

    # ------------------------------------------------------------------
    # Action (có thể thay đổi hệ thống/mở công cụ khác) — chạy trong QThread
    # riêng với action-slot RIÊNG của probe (bật tường lửa không chặn nút
    # Làm mới của thẻ khác/cùng thẻ).
    # ------------------------------------------------------------------
    def _run_action(
        self,
        fn: Callable[[], actions.ActionResult],
        on_done: Callable[[actions.ActionResult], None],
    ) -> bool:
        return self._action_slot.start(fn, on_done, self._on_action_failed)

    def _on_action_failed(self, message: str) -> None:
        _show_result(self, success=False, message=message, lang=self._lang)


# ---------------------------------------------------------------------------
# 1) Cập nhật — chỉ MỞ Trung tâm cập nhật (Discover qua Control Panel) — mở
#    app độc lập, không cần luồng riêng (trả về ngay, không chờ tiến trình
#    con kết thúc).
# ---------------------------------------------------------------------------
class _UpdateCard(_StatusCardBase):
    def __init__(self, lang: Lang, parent: QWidget | None = None) -> None:
        super().__init__(
            title_key="antoan.ui.card.update.title",
            probe_fn=probes.probe_update,
            lang=lang,
            parent=parent,
        )

    def _build_actions(self, row: QHBoxLayout) -> None:
        self._open_btn = QPushButton(t("antoan.ui.card.update.button.open", lang=self._lang))
        self._open_btn.clicked.connect(self._on_open_clicked)
        row.addWidget(self._open_btn)
        row.addStretch(1)

    def _on_open_clicked(self) -> None:
        result = actions.open_update_center()
        if not result.success:
            _show_result(self, success=False, message=result.message, lang=self._lang)


# ---------------------------------------------------------------------------
# 2) Tường lửa (UFW) — Bật (pkexec, hỏi xác nhận trước) + Xem chi tiết luật
#    (pkexec).
# ---------------------------------------------------------------------------
class _FirewallCard(_StatusCardBase):
    def __init__(self, lang: Lang, parent: QWidget | None = None) -> None:
        super().__init__(
            title_key="antoan.ui.card.firewall.title",
            probe_fn=probes.probe_firewall,
            lang=lang,
            parent=parent,
        )

    def _build_actions(self, row: QHBoxLayout) -> None:
        self._enable_btn = QPushButton(t("antoan.ui.card.firewall.button.enable", lang=self._lang))
        self._enable_btn.clicked.connect(self._on_enable_clicked)
        self._detail_btn = QPushButton(t("antoan.ui.card.firewall.button.detail", lang=self._lang))
        self._detail_btn.clicked.connect(self._on_detail_clicked)
        row.addWidget(self._enable_btn)
        row.addWidget(self._detail_btn)
        row.addStretch(1)

    def _on_enable_clicked(self) -> None:
        confirmed = QMessageBox.question(
            self,
            t("antoan.ui.card.firewall.title", lang=self._lang),
            t("antoan.ui.card.firewall.confirm_enable", lang=self._lang),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return
        self._enable_btn.setEnabled(False)
        if not self._run_action(actions.enable_firewall, self._on_enable_done):
            self._enable_btn.setEnabled(True)

    def _on_enable_done(self, result: actions.ActionResult) -> None:
        self._enable_btn.setEnabled(True)
        _show_result(self, success=result.success, message=result.message, lang=self._lang)
        self.refresh()

    def _on_detail_clicked(self) -> None:
        self._detail_btn.setEnabled(False)
        if not self._run_action(actions.view_firewall_detail, self._on_detail_done):
            self._detail_btn.setEnabled(True)

    def _on_detail_done(self, result: actions.ActionResult) -> None:
        self._detail_btn.setEnabled(True)
        _show_result(self, success=result.success, message=result.message, lang=self._lang)


# ---------------------------------------------------------------------------
# 3) AppArmor — CHỈ xem chi tiết hồ sơ đang nạp (pkexec). KHÔNG có nút "bật"
#    (enforce LSM cần tham số kernel + reboot, xem probes.probe_apparmor).
# ---------------------------------------------------------------------------
class _ApparmorCard(_StatusCardBase):
    def __init__(self, lang: Lang, parent: QWidget | None = None) -> None:
        super().__init__(
            title_key="antoan.ui.card.apparmor.title",
            probe_fn=probes.probe_apparmor,
            lang=lang,
            parent=parent,
        )

    def _build_actions(self, row: QHBoxLayout) -> None:
        self._detail_btn = QPushButton(t("antoan.ui.card.apparmor.button.detail", lang=self._lang))
        self._detail_btn.clicked.connect(self._on_detail_clicked)
        row.addWidget(self._detail_btn)
        row.addStretch(1)

    def _on_detail_clicked(self) -> None:
        self._detail_btn.setEnabled(False)
        if not self._run_action(actions.view_apparmor_detail, self._on_detail_done):
            self._detail_btn.setEnabled(True)

    def _on_detail_done(self, result: actions.ActionResult) -> None:
        self._detail_btn.setEnabled(True)
        _show_result(self, success=result.success, message=result.message, lang=self._lang)


# ---------------------------------------------------------------------------
# 4) Quét virus (ClamAV) — "Quét thư mục này" (KHÔNG cần quyền quản trị) +
#    "Cập nhật chữ ký" (freshclam, CẦN quyền quản trị).
# ---------------------------------------------------------------------------
class _AntivirusCard(_StatusCardBase):
    def __init__(self, lang: Lang, parent: QWidget | None = None) -> None:
        super().__init__(
            title_key="antoan.ui.card.antivirus.title",
            probe_fn=probes.probe_antivirus,
            lang=lang,
            parent=parent,
        )

    def _build_actions(self, row: QHBoxLayout) -> None:
        self._scan_btn = QPushButton(t("antoan.ui.card.antivirus.button.scan", lang=self._lang))
        self._scan_btn.clicked.connect(self._on_scan_clicked)
        self._sig_btn = QPushButton(t("antoan.ui.card.antivirus.button.update_sig", lang=self._lang))
        self._sig_btn.clicked.connect(self._on_sig_clicked)
        row.addWidget(self._scan_btn)
        row.addWidget(self._sig_btn)
        row.addStretch(1)

    def _on_scan_clicked(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            t("antoan.ui.card.antivirus.dialog_title", lang=self._lang),
            str(Path.home()),
        )
        if not folder:
            return
        self._scan_btn.setEnabled(False)
        self._headline_label.setText(t("antoan.ui.card.antivirus.scanning", lang=self._lang))
        if not self._run_action(lambda: actions.run_clamav_scan(folder), self._on_scan_done):
            self._scan_btn.setEnabled(True)

    def _on_scan_done(self, result: actions.ActionResult) -> None:
        self._scan_btn.setEnabled(True)
        _show_result(self, success=result.success, message=result.message, lang=self._lang)
        self.refresh()

    def _on_sig_clicked(self) -> None:
        self._sig_btn.setEnabled(False)
        if not self._run_action(actions.update_clamav_signatures, self._on_sig_done):
            self._sig_btn.setEnabled(True)

    def _on_sig_done(self, result: actions.ActionResult) -> None:
        self._sig_btn.setEnabled(True)
        _show_result(self, success=result.success, message=result.message, lang=self._lang)
        self.refresh()


# ---------------------------------------------------------------------------
# 5) Sao lưu (Kup) — chỉ MỞ cài đặt Sao lưu (không cần quyền quản trị, KCM
#    tự xử lý nếu cần — không trùng lặp với ``namios-mo-sao-luu`` đã có).
# ---------------------------------------------------------------------------
class _BackupCard(_StatusCardBase):
    def __init__(self, lang: Lang, parent: QWidget | None = None) -> None:
        super().__init__(
            title_key="antoan.ui.card.backup.title",
            probe_fn=probes.probe_backup,
            lang=lang,
            parent=parent,
        )

    def _build_actions(self, row: QHBoxLayout) -> None:
        self._open_btn = QPushButton(t("antoan.ui.card.backup.button.open", lang=self._lang))
        self._open_btn.clicked.connect(self._on_open_clicked)
        row.addWidget(self._open_btn)
        row.addStretch(1)

    def _on_open_clicked(self) -> None:
        result = actions.open_backup_settings()
        if not result.success:
            _show_result(self, success=False, message=result.message, lang=self._lang)


# ---------------------------------------------------------------------------
# Cửa sổ chính — header + nút Làm mới tất cả/Giới thiệu + 5 thẻ cuộn được +
# chân trang với câu trung thực ngắn (luôn hiển thị, không cần mở "Giới
# thiệu" mới thấy).
# ---------------------------------------------------------------------------
class AntoanWindow(QMainWindow):
    def __init__(
        self,
        *,
        lang: Lang | str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._lang = resolve_lang(lang)
        self.setWindowTitle(t("antoan.ui.window_title", lang=self._lang))
        self.resize(780, 820)
        self.setStyleSheet(build_stylesheet())
        self._cards: list[_StatusCardBase] = []
        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # Lắp widget
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AntoanRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())
        root_layout.addLayout(self._build_toolbar())

        scroll = QScrollArea()
        scroll.setObjectName("CardScroll")
        scroll.setWidgetResizable(True)

        content = QWidget()
        content.setObjectName("CardScrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(12)

        self._cards = [
            _UpdateCard(self._lang),
            _FirewallCard(self._lang),
            _ApparmorCard(self._lang),
            _AntivirusCard(self._lang),
            _BackupCard(self._lang),
        ]
        for card in self._cards:
            content_layout.addWidget(card)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        footer = QLabel(t("antoan.ui.footer.disclaimer", lang=self._lang))
        footer.setObjectName("FooterDisclaimer")
        footer.setWordWrap(True)
        footer.setContentsMargins(16, 6, 16, 10)
        root_layout.addWidget(footer)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(2)
        title = QLabel(t("antoan.ui.header.title", lang=self._lang))
        title.setObjectName("HeaderTitle")
        subtitle = QLabel(t("antoan.ui.header.subtitle", lang=self._lang))
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 10, 16, 0)
        self._refresh_all_btn = QPushButton(t("antoan.ui.button.refresh_all", lang=self._lang))
        self._refresh_all_btn.setObjectName("RefreshAllButton")
        self._refresh_all_btn.clicked.connect(self.refresh_all)
        about_btn = QPushButton(t("antoan.ui.button.about", lang=self._lang))
        about_btn.clicked.connect(self._show_about)
        toolbar.addWidget(self._refresh_all_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(about_btn)
        return toolbar

    # ------------------------------------------------------------------
    # Hành vi
    # ------------------------------------------------------------------
    def refresh_all(self) -> None:
        for card in self._cards:
            card.refresh()

    def _show_about(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(t("antoan.ui.about.title", lang=self._lang))
        dialog.resize(640, 580)
        layout = QVBoxLayout(dialog)
        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(t("antoan.ui.about.body", lang=self._lang))
        layout.addWidget(body)
        close_btn = QPushButton(t("antoan.ui.about.close", lang=self._lang))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()
