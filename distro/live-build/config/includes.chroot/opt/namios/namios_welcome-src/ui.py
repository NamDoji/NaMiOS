"""Wizard PySide6 mỏng cho luồng đầu tiên (UI-005) — CHỈ chạy trên desktop
session thật, KHÔNG chạy trong môi trường build/test headless hiện tại.

5 bước: Chào mừng → Bộ gõ/Cỡ chữ → App mặc định → Chuyển dữ liệu từ Windows
→ Xong. Mọi logic thật (ghi config, quét/copy dữ liệu) nằm ở
``namios_welcome.firstrun``/``namios_welcome.migrate`` — file này chỉ lắp
widget rồi gọi, KHÔNG chứa quyết định an toàn nào của riêng nó (để test được
toàn bộ logic mà không cần PySide6/desktop — xem ``tests/unit/welcome/``).

Song ngữ (đợt nâng cấp i18n 03/11/2026): mọi tiêu đề/label hiển thị đi qua
``namios_i18n.t`` (nhóm key ``welcome.ui.*``, VI/EN đã seed) — khác với
``namios_cli``/``namios_eco`` (nơi các trường dữ liệu ``message_vi``/
``reason_vi`` PHẢI luôn tiếng Việt theo hợp đồng liên-WP), wizard này KHÔNG
phải một hợp đồng dữ liệu liên-module — ngôn ngữ hiệu lực phân giải MỘT lần
lúc dựng wizard qua ``namios_i18n.resolve_lang()`` (biến môi trường
``NAMIOS_LANG`` > VI mặc định), không có cờ CLI riêng ở đây (wizard chạy từ
desktop session, không phải subprocess ``namios``).

``verified_on_boot: NO`` — bố cục/hành vi dưới đây chưa được xác nhận bằng
mắt trên một desktop KDE thật (container này không có display); chỉ xác
nhận được khi boot ISO thật (xem ADR 0011).
"""

# mypy: ignore-errors
# PySide6 không có stub/không được cài trong môi trường build headless hiện
# tại (FACT 02/11/2026) — mypy coi mọi import Qt là ``Any``. File này KHÔNG
# chứa quyết định an toàn/business logic (chỉ lắp UI rồi gọi
# ``namios_welcome.firstrun``/``namios_welcome.migrate``, nơi mypy strict
# vẫn áp dụng đầy đủ), nên tắt mypy riêng cho file này thay vì nới lỏng toàn
# cục. Bỏ dòng này khi desktop thật có PySide6 + stub để kiểm tra lại.

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl  # type: ignore[import-not-found]
from PySide6.QtGui import QDesktopServices  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from namios_i18n import Lang, resolve_lang, t
from namios_welcome.firstrun import ConfigApplier, FirstRunChoices, WelcomeDoneMarker
from namios_welcome.migrate import WindowsDataMigrator

#: Đường dẫn "Hướng dẫn nhanh cho người quen dùng Windows" trên ảnh đã build —
#: PHẢI khớp đúng ``Exec=`` của
#: ``usr/share/applications/namios-huong-dan.desktop`` (cùng một file HTML,
#: cùng một nguồn sự thật — xem ``docs/huong-dan/HUONG-DAN-NHANH-WINDOWS.md``
#: cho bản nguồn Markdown). Không tồn tại thì nút chỉ im lặng không mở được gì
#: (``QDesktopServices.openUrl`` trả ``False``) — KHÔNG crash wizard.
QUICK_GUIDE_HTML_PATH = "/usr/share/namios/huong-dan-nhanh.html"


class _WelcomePage(QWizardPage):
    def __init__(self, lang: Lang) -> None:
        super().__init__()
        self.setTitle(t("welcome.ui.welcome.title", lang=lang))
        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("welcome.ui.welcome.body", lang=lang)))
        self.setLayout(layout)


class _ImeAndScalePage(QWizardPage):
    def __init__(self, lang: Lang) -> None:
        super().__init__()
        self.setTitle(t("welcome.ui.ime_scale.title", lang=lang))
        layout = QVBoxLayout()
        self.ime_combo = QComboBox()
        self.ime_combo.addItems(["telex", "vni"])
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100", "125", "150"])
        layout.addWidget(QLabel(t("welcome.ui.ime_scale.ime_label", lang=lang)))
        layout.addWidget(self.ime_combo)
        layout.addWidget(QLabel(t("welcome.ui.ime_scale.scale_label", lang=lang)))
        layout.addWidget(self.scale_combo)
        self.setLayout(layout)


class _DefaultAppsPage(QWizardPage):
    def __init__(self, lang: Lang) -> None:
        super().__init__()
        self.setTitle(t("welcome.ui.default_apps.title", lang=lang))
        layout = QVBoxLayout()
        self.docx_edit = QLineEdit("libreoffice-writer")
        self.xlsx_edit = QLineEdit("libreoffice-calc")
        self.pdf_edit = QLineEdit("okular")
        self.printer_edit = QLineEdit()
        for label_key, edit in (
            ("welcome.ui.default_apps.docx_label", self.docx_edit),
            ("welcome.ui.default_apps.xlsx_label", self.xlsx_edit),
            ("welcome.ui.default_apps.pdf_label", self.pdf_edit),
            ("welcome.ui.default_apps.printer_label", self.printer_edit),
        ):
            layout.addWidget(QLabel(t(label_key, lang=lang)))
            layout.addWidget(edit)
        self.setLayout(layout)


class _MigratePage(QWizardPage):
    def __init__(self, lang: Lang) -> None:
        super().__init__()
        self._lang = lang
        self.setTitle(t("welcome.ui.migrate.title", lang=lang))
        layout = QVBoxLayout()
        self.source_edit = QLineEdit()
        browse_button = QPushButton(t("welcome.ui.migrate.browse_button", lang=lang))
        browse_button.clicked.connect(self._browse)
        self.status_label = QLabel(t("welcome.ui.migrate.status_label", lang=lang))
        layout.addWidget(self.source_edit)
        layout.addWidget(browse_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, t("welcome.ui.migrate.dialog_title", lang=self._lang)
        )
        if directory:
            self.source_edit.setText(directory)


class _DonePage(QWizardPage):
    def __init__(self, lang: Lang) -> None:
        super().__init__()
        self.setTitle(t("welcome.ui.done.title", lang=lang))
        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("welcome.ui.done.body", lang=lang)))
        guide_button = QPushButton(t("welcome.ui.done.quick_guide_button", lang=lang))
        guide_button.clicked.connect(self._open_quick_guide)
        layout.addWidget(guide_button)
        self.setLayout(layout)

    @staticmethod
    def _open_quick_guide() -> None:
        # Mở file HTML tĩnh đã đóng gói sẵn trong ảnh (KHÔNG tải mạng, KHÔNG
        # eval) — cùng file mà namios-huong-dan.desktop đã trỏ tới. Trả
        # ``False`` nếu thiếu file/không có trình xem mặc định — bỏ qua lặng
        # lẽ, không chặn luồng "Xong".
        QDesktopServices.openUrl(QUrl.fromLocalFile(QUICK_GUIDE_HTML_PATH))


class WelcomeWizard(QWizard):
    """Wizard 5 bước. ``config_dir``/``dest_home`` được tiêm từ ngoài (không
    hardcode ``$HOME`` trong file UI) để nơi gọi (``__main__``) kiểm soát.

    ``lang`` chọn ngôn ngữ hiển thị (``None`` ⇒ phân giải qua
    ``namios_i18n.resolve_lang()`` — biến môi trường ``NAMIOS_LANG`` > VI
    mặc định, xem NOTE i18n ở đầu module)."""

    def __init__(
        self,
        config_dir: Path,
        dest_home: Path,
        parent: QWidget | None = None,
        *,
        lang: Lang | str | None = None,
    ) -> None:
        super().__init__(parent)
        resolved_lang = resolve_lang(lang)
        self.setWindowTitle(t("welcome.ui.window_title", lang=resolved_lang))
        self._config_dir = config_dir
        self._dest_home = dest_home

        self._welcome_page = _WelcomePage(resolved_lang)
        self._ime_scale_page = _ImeAndScalePage(resolved_lang)
        self._apps_page = _DefaultAppsPage(resolved_lang)
        self._migrate_page = _MigratePage(resolved_lang)
        self._done_page = _DonePage(resolved_lang)

        for page in (
            self._welcome_page,
            self._ime_scale_page,
            self._apps_page,
            self._migrate_page,
            self._done_page,
        ):
            self.addPage(page)

        self.accepted.connect(self._on_accepted)
        # `finished(int)` (QDialog) bắn cho CẢ hai nhánh — bấm "Hoàn tất"
        # (accepted) lẫn "Hủy"/đóng cửa sổ (rejected) — nên dùng đây thay vì
        # nối riêng accepted+rejected. Ý định: đã CHO XEM wizard một lần là
        # không tự mở lại nữa, kể cả khi người dùng bấm Hủy giữa chừng (Phụ
        # lục 13 §6 "tiếp cận nhẹ nhàng" — không ép phải hoàn tất mới thôi
        # làm phiền). Muốn làm lại, người dùng tự gọi lệnh `namios-welcome`.
        self.finished.connect(self._mark_welcome_done)

    def _mark_welcome_done(self) -> None:
        WelcomeDoneMarker(self._config_dir).mark_done()

    def _on_accepted(self) -> None:
        choices = FirstRunChoices(
            ime_method=self._ime_scale_page.ime_combo.currentText(),  # type: ignore[arg-type]
            ui_scale_percent=int(self._ime_scale_page.scale_combo.currentText()),  # type: ignore[arg-type]
            default_app_docx=self._apps_page.docx_edit.text(),
            default_app_xlsx=self._apps_page.xlsx_edit.text(),
            default_app_pdf=self._apps_page.pdf_edit.text(),
            default_printer=self._apps_page.printer_edit.text() or None,
        )
        ConfigApplier(self._config_dir).apply(choices)

        source_text = self._migrate_page.source_edit.text().strip()
        if source_text:
            migrator = WindowsDataMigrator(source_text)
            migrator.migrate(self._dest_home)
