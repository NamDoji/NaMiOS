"""Cửa sổ PySide6 của Cổng Dịch vụ Việt + Trung tâm Ký số — CHỈ chạy trên
desktop session thật, KHÔNG chạy trong môi trường build/test headless hiện
tại (cùng ghi chú ``namios_assistant.ui``: import PySide6 bị trì hoãn tới
``__main__.main()``).

Mọi dữ liệu/quyết định trạng thái nằm ở ``namios_dichvu.catalog`` +
``namios_dichvu.envcheck`` (Python thuần, test được không cần GUI) — file
này CHỈ lắp widget + gọi hai module đó + mở URL/app ngoài qua ``subprocess``
(argv cố định/tra PATH bằng ``shutil.which`` trước, KHÔNG ``shell=True``,
KHÔNG nội suy input người dùng vào argv). KHÔNG có logic phân loại
trạng thái/nội dung nào tự chế thêm ở tầng UI."""

# mypy: ignore-errors
# PySide6 không có stub trong môi trường build headless hiện tại — tắt mypy
# riêng cho file này (chỉ lắp UI, không chứa quyết định an toàn/business
# logic), cùng quy ước ``namios_assistant.ui``/``namios_antoan.ui``.

from __future__ import annotations

import shutil
import subprocess
from urllib.parse import urlsplit

from PySide6.QtCore import Qt  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from namios_dichvu.branding import STATUS_COLORS, build_stylesheet
from namios_dichvu.catalog import ServiceCatalog, ServiceEntry, filter_services, load_catalog
from namios_dichvu.envcheck import EnvCheckReport, probe_pkcs11_slots, run_env_check
from namios_i18n import Lang, resolve_lang, t

__all__ = ["DichVuWindow"]

_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})
_KYSO_CATEGORY_ID = "kyso"


def _is_safe_external_url(url: str) -> bool:
    """Kiểm trước khi mở — chỉ cho scheme http(s) + có domain. Đây là
    ``official_url`` do NaMiOS tự khai trong ``services_vn.json`` (không
    phải input người dùng/redirect động), nhưng vẫn kiểm một lớp phòng vệ
    rẻ trước khi gọi ra ngoài, không bao giờ mở một scheme lạ (``file://``,
    ``javascript:``...) dù dữ liệu JSON có bị hỏng/chèn sai thế nào."""

    parts = urlsplit(url.strip())
    return parts.scheme.lower() in _ALLOWED_URL_SCHEMES and bool(parts.netloc)


class DichVuWindow(QMainWindow):
    def __init__(
        self,
        *,
        catalog: ServiceCatalog | None = None,
        lang: Lang | str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._lang = resolve_lang(lang)
        self._catalog = catalog if catalog is not None else load_catalog()
        self._selected_category: str | None = None  # None = "Tất cả"

        self.setWindowTitle(t("dichvu.ui.window_title", lang=self._lang))
        self.resize(980, 720)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()
        self._refresh_cards()

    # ------------------------------------------------------------------
    # Lắp widget
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("DichVuRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        if self._catalog.load_error_vi:
            error_banner = QLabel(
                f"{t('dichvu.ui.load_error_title', lang=self._lang)}: {self._catalog.load_error_vi}"
            )
            error_banner.setObjectName("CardReason")
            error_banner.setWordWrap(True)
            error_banner.setContentsMargins(12, 8, 12, 8)
            root_layout.addWidget(error_banner)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_card_area())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 740])
        root_layout.addWidget(splitter, stretch=1)

        footer = QLabel(t("dichvu.ui.footer.disclaimer", lang=self._lang))
        footer.setObjectName("FooterDisclaimer")
        footer.setWordWrap(True)
        footer.setContentsMargins(12, 6, 12, 6)
        root_layout.addWidget(footer)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        layout = QHBoxLayout(header)

        title_box = QVBoxLayout()
        title = QLabel(t("dichvu.ui.header.title", lang=self._lang))
        title.setObjectName("HeaderTitle")
        subtitle = QLabel(t("dichvu.ui.header.subtitle", lang=self._lang))
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box, stretch=1)

        env_check_button = QPushButton(t("dichvu.ui.envcheck.button", lang=self._lang))
        env_check_button.setObjectName("EnvCheckButton")
        env_check_button.clicked.connect(self._show_env_check_dialog)
        layout.addWidget(env_check_button, alignment=Qt.AlignmentFlag.AlignTop)

        return header

    def _build_sidebar(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        self._search_box = QLineEdit()
        self._search_box.setObjectName("SearchBox")
        self._search_box.setPlaceholderText(t("dichvu.ui.search.placeholder", lang=self._lang))
        self._search_box.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_box)

        self._category_list = QListWidget()
        self._category_list.setObjectName("CategoryList")
        self._populate_categories()
        self._category_list.currentItemChanged.connect(self._on_category_changed)
        layout.addWidget(self._category_list, stretch=1)

        return container

    def _populate_categories(self) -> None:
        count_suffix = t("dichvu.ui.category.count_suffix", lang=self._lang, count=len(self._catalog.services))
        all_item = QListWidgetItem(f"{t('dichvu.ui.category.all', lang=self._lang)} {count_suffix}")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        self._category_list.addItem(all_item)

        for category in self._catalog.categories:
            count = sum(1 for s in self._catalog.services if s.category == category.id)
            label = category.label(lang=self._lang.value)
            suffix = t("dichvu.ui.category.count_suffix", lang=self._lang, count=count)
            item = QListWidgetItem(f"{label} {suffix}")
            item.setData(Qt.ItemDataRole.UserRole, category.id)
            self._category_list.addItem(item)

        self._category_list.setCurrentRow(0)

    def _build_card_area(self) -> QWidget:
        self._card_scroll = QScrollArea()
        self._card_scroll.setObjectName("CardScroll")
        self._card_scroll.setWidgetResizable(True)

        self._card_container = QWidget()
        self._card_container.setObjectName("CardScrollContent")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(12, 12, 12, 12)
        self._card_layout.setSpacing(10)
        self._card_layout.addStretch(1)

        self._card_scroll.setWidget(self._card_container)
        return self._card_scroll

    # ------------------------------------------------------------------
    # Lọc + hiển thị danh sách thẻ
    # ------------------------------------------------------------------

    def _on_category_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        self._selected_category = current.data(Qt.ItemDataRole.UserRole) if current is not None else None
        # ``_build_sidebar()`` runs BEFORE ``_build_card_area()`` in ``_build_ui()``
        # (sidebar needs to exist first for the splitter) — populating the category
        # list calls ``setCurrentRow(0)``, which fires THIS signal immediately,
        # before ``self._card_layout`` exists yet. Guard + bail out quietly; the
        # explicit ``self._refresh_cards()`` call at the end of ``__init__`` does
        # the real first render once the whole UI is built.
        if not hasattr(self, "_card_layout"):
            return
        self._refresh_cards()

    def _on_search_changed(self, _text: str) -> None:
        self._refresh_cards()

    def _clear_cards(self) -> None:
        while self._card_layout.count() > 1:  # giữ lại addStretch(1) cuối cùng
            item = self._card_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_cards(self) -> None:
        self._clear_cards()
        query = self._search_box.text() if hasattr(self, "_search_box") else ""
        results = filter_services(
            self._catalog.services, category_id=self._selected_category, query=query
        )

        insert_at = self._card_layout.count() - 1  # chèn TRƯỚC addStretch(1)

        if self._selected_category == _KYSO_CATEGORY_ID and not query.strip():
            banner = self._build_kyso_banner()
            self._card_layout.insertWidget(insert_at, banner)
            insert_at += 1

        empty_note = self._catalog.empty_category_notes.get(self._selected_category or "")
        if empty_note and not results:
            note_text = empty_note.get(self._lang.value) or empty_note.get("vi", "")
            note_label = QLabel(f"{t('dichvu.ui.empty_category_note_prefix', lang=self._lang)}{note_text}")
            note_label.setObjectName("CardReason")
            note_label.setWordWrap(True)
            self._card_layout.insertWidget(insert_at, note_label)
            insert_at += 1

        if not results and not empty_note:
            no_results = QLabel(t("dichvu.ui.no_results", lang=self._lang))
            no_results.setObjectName("CardReason")
            self._card_layout.insertWidget(insert_at, no_results)
            insert_at += 1

        for entry in results:
            card = self._build_service_card(entry)
            self._card_layout.insertWidget(insert_at, card)
            insert_at += 1

    def _build_kyso_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("KysoBanner")
        layout = QVBoxLayout(banner)
        title = QLabel(t("dichvu.ui.kyso.banner_title", lang=self._lang))
        title.setObjectName("KysoBannerTitle")
        body = QLabel(t("dichvu.ui.kyso.banner_body", lang=self._lang))
        body.setObjectName("KysoBannerBody")
        body.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(body)
        return banner

    # ------------------------------------------------------------------
    # Thẻ dịch vụ
    # ------------------------------------------------------------------

    def _build_service_card(self, entry: ServiceEntry) -> QFrame:
        card = QFrame()
        card.setObjectName("ServiceCard")
        layout = QVBoxLayout(card)

        top_row = QHBoxLayout()
        title = QLabel(entry.name(lang=self._lang.value))
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        top_row.addWidget(title, stretch=1)

        if entry.recommended:
            rec_badge = QLabel(t("dichvu.ui.card.recommended_badge", lang=self._lang))
            rec_badge.setObjectName("RecommendedBadge")
            top_row.addWidget(rec_badge, alignment=Qt.AlignmentFlag.AlignTop)

        status_badge = QLabel(self._status_label(entry.realistic_status))
        status_badge.setObjectName("StatusBadge")
        status_badge.setStyleSheet(
            f"background-color: {STATUS_COLORS.get(entry.realistic_status, '#8A8A8A')};"
        )
        top_row.addWidget(status_badge, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top_row)

        if entry.provider:
            provider_label = QLabel(
                t("dichvu.ui.card.provider_label", lang=self._lang, provider=entry.provider)
            )
            provider_label.setObjectName("CardProvider")
            provider_label.setWordWrap(True)
            layout.addWidget(provider_label)

        purpose_label = QLabel(entry.purpose_vi)
        purpose_label.setObjectName("CardPurpose")
        purpose_label.setWordWrap(True)
        layout.addWidget(purpose_label)

        reason_label = QLabel(entry.status_reason(lang=self._lang.value))
        reason_label.setObjectName("CardReason")
        reason_label.setWordWrap(True)
        layout.addWidget(reason_label)

        if entry.published_status:
            pub_label = QLabel(
                t(
                    "dichvu.ui.card.published_status_label",
                    lang=self._lang,
                    status=entry.published_status,
                )
            )
        else:
            pub_label = QLabel(t("dichvu.ui.card.published_status_none", lang=self._lang))
        pub_label.setObjectName("CardMeta")
        pub_label.setWordWrap(True)
        layout.addWidget(pub_label)

        meta_bits: list[str] = []
        if entry.account_condition_vi and self._lang == Lang.VI:
            meta_bits.append(
                t(
                    "dichvu.ui.card.account_condition_label",
                    lang=self._lang,
                    condition=entry.account_condition_vi,
                )
            )
        meta_bits.append(
            t(
                "dichvu.ui.card.tested_label",
                lang=self._lang,
                value=t(
                    "dichvu.ui.card.bool_yes" if entry.tested_by_namios else "dichvu.ui.card.bool_no",
                    lang=self._lang,
                ),
            )
        )
        meta_bits.append(
            t(
                "dichvu.ui.card.vendor_support_label",
                lang=self._lang,
                value=t(
                    "dichvu.ui.card.bool_yes"
                    if entry.officially_supported_by_vendor
                    else "dichvu.ui.card.bool_no",
                    lang=self._lang,
                ),
            )
        )
        if entry.source:
            meta_bits.append(t("dichvu.ui.card.source_label", lang=self._lang, source=entry.source))
        if entry.last_updated:
            meta_bits.append(
                t("dichvu.ui.card.last_updated_label", lang=self._lang, date=entry.last_updated)
            )
        meta_label = QLabel(" · ".join(meta_bits))
        meta_label.setObjectName("CardMeta")
        meta_label.setWordWrap(True)
        layout.addWidget(meta_label)

        guide_text = entry.guide(lang=self._lang.value)
        if guide_text:
            guide_box = QTextEdit()
            guide_box.setObjectName("CardReason")
            guide_box.setReadOnly(True)
            guide_box.setPlainText(guide_text)
            guide_box.setMaximumHeight(90)
            guide_box.setVisible(False)
            toggle_button = QPushButton(t("dichvu.ui.card.guide_toggle", lang=self._lang))
            toggle_button.clicked.connect(lambda _checked=False, box=guide_box: box.setVisible(not box.isVisible()))
            layout.addWidget(toggle_button)
            layout.addWidget(guide_box)

        layout.addLayout(self._build_card_actions(entry))
        return card

    def _status_label(self, realistic_status: str) -> str:
        key = {
            "works-web": "dichvu.ui.status.works_web",
            "works-native": "dichvu.ui.status.works_native",
            "wine-candidate": "dichvu.ui.status.wine_candidate",
            "blocked": "dichvu.ui.status.blocked",
        }.get(realistic_status, "dichvu.ui.status.blocked")
        return t(key, lang=self._lang)

    def _build_card_actions(self, entry: ServiceEntry) -> QHBoxLayout:
        actions_row = QHBoxLayout()

        if entry.action == "open_web":
            button = QPushButton(t("dichvu.ui.card.open_web", lang=self._lang))
            button.setObjectName("PrimaryButton")
            if not entry.official_url:
                button.setEnabled(False)
                button.setToolTip(t("dichvu.ui.card.open_web_disabled_no_url", lang=self._lang))
            else:
                button.clicked.connect(lambda _checked=False, url=entry.official_url: self._open_web(url))
            actions_row.addWidget(button)

        elif entry.action == "open_app":
            for option in entry.app_options:
                app_button = QPushButton(option.label(lang=self._lang.value))
                app_button.clicked.connect(
                    lambda _checked=False, cmd=option.app_command, label=option.label(lang=self._lang.value): self._open_app(cmd, label)
                )
                actions_row.addWidget(app_button)

        elif entry.action == "probe_pkcs11":
            probe_button = QPushButton(t("dichvu.ui.card.probe_button", lang=self._lang))
            probe_button.setObjectName("PrimaryButton")
            probe_button.clicked.connect(self._run_pkcs11_probe)
            actions_row.addWidget(probe_button)

        actions_row.addStretch(1)
        return actions_row

    # ------------------------------------------------------------------
    # Mở URL/app ngoài — argv cố định, tra PATH trước, KHÔNG shell=True
    # ------------------------------------------------------------------

    def _open_web(self, url: str) -> None:
        if not _is_safe_external_url(url):
            self._show_message(t("dichvu.ui.card.open_web_error_unsafe_url", lang=self._lang))
            return
        tool_path = shutil.which("xdg-open")
        if tool_path is None:
            self._show_message(t("dichvu.ui.card.open_web_error_no_tool", lang=self._lang))
            return
        try:
            subprocess.Popen([tool_path, url], shell=False)  # noqa: S603 - argv cố định, shell=False
        except OSError as exc:
            self._show_message(f"{t('dichvu.ui.card.open_web_error_no_tool', lang=self._lang)} ({exc})")

    def _open_app(self, app_command: str, label: str) -> None:
        tool_path = shutil.which(app_command)
        if tool_path is None:
            self._show_message(
                t("dichvu.ui.card.open_app_error_no_tool", lang=self._lang, app=label)
            )
            return
        try:
            subprocess.Popen([tool_path], shell=False)  # noqa: S603 - argv cố định, shell=False
        except OSError as exc:
            self._show_message(
                f"{t('dichvu.ui.card.open_app_error_no_tool', lang=self._lang, app=label)} ({exc})"
            )

    def _run_pkcs11_probe(self) -> None:
        result = probe_pkcs11_slots()
        note = result.note_vi if self._lang == Lang.VI else result.note_en
        text = note if not result.raw_output else f"{note}\n\n{result.raw_output}"
        dialog = QDialog(self)
        dialog.setWindowTitle(t("dichvu.ui.card.probe_result_title", lang=self._lang))
        layout = QVBoxLayout(dialog)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setPlainText(text)
        layout.addWidget(box)
        close_button = QPushButton(t("dichvu.ui.dialog.close_button", lang=self._lang))
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        dialog.resize(480, 320)
        dialog.exec()

    def _show_message(self, text: str) -> None:
        QMessageBox.information(self, t("dichvu.ui.window_title", lang=self._lang), text)

    # ------------------------------------------------------------------
    # Tự kiểm môi trường (ECO-008)
    # ------------------------------------------------------------------

    def _show_env_check_dialog(self) -> None:
        report = run_env_check()
        dialog = QDialog(self)
        dialog.setWindowTitle(t("dichvu.ui.envcheck.dialog_title", lang=self._lang))
        layout = QVBoxLayout(dialog)

        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setPlainText(self._format_env_check(report))
        layout.addWidget(box)

        close_button = QPushButton(t("dichvu.ui.dialog.close_button", lang=self._lang))
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.resize(560, 420)
        dialog.exec()

    def _format_env_check(self, report: EnvCheckReport) -> str:
        lang = self._lang
        present = t("dichvu.ui.envcheck.status.present", lang=lang)
        missing = t("dichvu.ui.envcheck.status.missing", lang=lang)

        lines: list[str] = []
        lines.append(f"-- {t('dichvu.ui.envcheck.section.browser', lang=lang)} --")
        lines.append(
            t(
                "dichvu.ui.envcheck.browser.xdg_open_ok"
                if report.browser.xdg_open_present
                else "dichvu.ui.envcheck.browser.xdg_open_missing",
                lang=lang,
            )
        )
        if report.browser.known_browser_present:
            lines.append(
                t(
                    "dichvu.ui.envcheck.browser.known_found",
                    lang=lang,
                    names=", ".join(report.browser.known_browser_present),
                )
            )
        else:
            lines.append(t("dichvu.ui.envcheck.browser.known_none", lang=lang))

        lines.append("")
        lines.append(f"-- {t('dichvu.ui.envcheck.section.signing', lang=lang)} --")
        lines.append(
            t(
                "dichvu.ui.envcheck.signing.okular",
                lang=lang,
                status=present if report.signing_tools.okular_present else missing,
            )
        )
        lines.append(
            t(
                "dichvu.ui.envcheck.signing.libreoffice",
                lang=lang,
                status=present if report.signing_tools.libreoffice_present else missing,
            )
        )
        lines.append(
            t(
                "dichvu.ui.envcheck.signing.pkcs11",
                lang=lang,
                status=present if report.signing_tools.opensc_pkcs11_tool_present else missing,
            )
        )

        lines.append("")
        lines.append(f"-- {t('dichvu.ui.envcheck.section.clock', lang=lang)} --")
        lines.append(
            t(
                "dichvu.ui.envcheck.clock.line",
                lang=lang,
                time=report.clock.local_time_iso,
                tz=report.clock.timezone_name or "?",
            )
        )

        lines.append("")
        lines.append(f"-- {t('dichvu.ui.envcheck.section.manual', lang=lang)} --")
        reminders = (
            report.manual_check_reminders_vi if lang == Lang.VI else report.manual_check_reminders_en
        )
        for reminder in reminders:
            lines.append(f"- {reminder}")

        lines.append("")
        lines.append(t("dichvu.ui.envcheck.footer", lang=lang))
        return "\n".join(lines)
