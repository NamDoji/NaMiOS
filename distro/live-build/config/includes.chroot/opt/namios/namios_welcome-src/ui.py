"""Wizard PySide6 mỏng cho luồng đầu tiên (UI-005) — CHỈ chạy trên desktop
session thật, KHÔNG chạy trong môi trường build/test headless hiện tại.

5 bước: Chào mừng → Bộ gõ/Cỡ chữ → App mặc định → Chuyển dữ liệu từ Windows
→ Xong. Mọi logic thật (ghi config, quét/copy dữ liệu) nằm ở
``namios_welcome.firstrun``/``namios_welcome.migrate`` — file này chỉ lắp
widget rồi gọi, KHÔNG chứa quyết định an toàn nào của riêng nó (để test được
toàn bộ logic mà không cần PySide6/desktop — xem ``tests/unit/welcome/``).

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

from namios_welcome.firstrun import ConfigApplier, FirstRunChoices
from namios_welcome.migrate import WindowsDataMigrator


class _WelcomePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Chào mừng đến với NaMiOS")
        layout = QVBoxLayout()
        layout.addWidget(
            QLabel(
                "Vài bước nhỏ để thiết lập bộ gõ, cỡ chữ, phần mềm mở tài liệu và "
                "chuyển dữ liệu từ Windows (nếu có)."
            )
        )
        self.setLayout(layout)


class _ImeAndScalePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Bộ gõ và cỡ chữ")
        layout = QVBoxLayout()
        self.ime_combo = QComboBox()
        self.ime_combo.addItems(["telex", "vni"])
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100", "125", "150"])
        layout.addWidget(QLabel("Bộ gõ tiếng Việt:"))
        layout.addWidget(self.ime_combo)
        layout.addWidget(QLabel("Cỡ chữ (%):"))
        layout.addWidget(self.scale_combo)
        self.setLayout(layout)


class _DefaultAppsPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Phần mềm mặc định")
        layout = QVBoxLayout()
        self.docx_edit = QLineEdit("libreoffice-writer")
        self.xlsx_edit = QLineEdit("libreoffice-calc")
        self.pdf_edit = QLineEdit("okular")
        self.printer_edit = QLineEdit()
        for label_text, edit in (
            ("Mở file .docx:", self.docx_edit),
            ("Mở file .xlsx:", self.xlsx_edit),
            ("Mở file .pdf:", self.pdf_edit),
            ("Máy in mặc định (bỏ trống nếu chưa có):", self.printer_edit),
        ):
            layout.addWidget(QLabel(label_text))
            layout.addWidget(edit)
        self.setLayout(layout)


class _MigratePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Chuyển dữ liệu từ Windows (không bắt buộc)")
        layout = QVBoxLayout()
        self.source_edit = QLineEdit()
        browse_button = QPushButton("Chọn thư mục Windows đã mount…")
        browse_button.clicked.connect(self._browse)
        self.status_label = QLabel("Chỉ SAO CHÉP — không xóa/di chuyển gì ở phía Windows.")
        layout.addWidget(self.source_edit)
        layout.addWidget(browse_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục Windows đã mount")
        if directory:
            self.source_edit.setText(directory)


class _DonePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Xong")
        layout = QVBoxLayout()
        layout.addWidget(
            QLabel("Đã lưu lựa chọn. Bạn có thể đổi lại trong Cài đặt bất cứ lúc nào.")
        )
        self.setLayout(layout)


class WelcomeWizard(QWizard):
    """Wizard 5 bước. ``config_dir``/``dest_home`` được tiêm từ ngoài (không
    hardcode ``$HOME`` trong file UI) để nơi gọi (``__main__``) kiểm soát."""

    def __init__(self, config_dir: Path, dest_home: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chào mừng đến với NaMiOS")
        self._config_dir = config_dir
        self._dest_home = dest_home

        self._welcome_page = _WelcomePage()
        self._ime_scale_page = _ImeAndScalePage()
        self._apps_page = _DefaultAppsPage()
        self._migrate_page = _MigratePage()
        self._done_page = _DonePage()

        for page in (
            self._welcome_page,
            self._ime_scale_page,
            self._apps_page,
            self._migrate_page,
            self._done_page,
        ):
            self.addPage(page)

        self.accepted.connect(self._on_accepted)

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
