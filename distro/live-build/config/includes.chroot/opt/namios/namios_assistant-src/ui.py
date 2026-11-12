"""Cửa sổ chat PySide6 của NaMiOS Assistant — CHỈ chạy trên desktop session
thật, KHÔNG chạy trong môi trường build/test headless hiện tại (cùng ghi chú
``namios_welcome.ui``: import PySide6 bị trì hoãn tới ``__main__.main()``).

Mọi quyết định "có trả lời được không"/"nguồn trả lời là gì" nằm ở
``namios_assistant.engine`` (Python thuần, test được không cần GUI) — file
này CHỈ lắp widget + chạy ``AssistantEngine.ask``/``ocr_image`` trong một
``QThread`` riêng (tránh treo giao diện khi gọi model AI trực tuyến/OCR ảnh
lớn), rồi hiển thị kết quả. KHÔNG có logic an toàn/nội dung nào tự chế ở
tầng UI.

Mỗi câu trả lời hiển thị kèm ``AssistantAnswer.note`` (nhãn nguồn: KB ngoại
tuyến hay model AI trực tuyến nào) NGAY DƯỚI nội dung — bắt buộc theo "Honest
UX" (xem ``docs/SMARTAI-ASSISTANT.md``), không được bỏ qua field này."""

# mypy: ignore-errors
# PySide6 không có stub/không được cài trong môi trường build headless hiện
# tại — mypy coi mọi import Qt là ``Any``. File này KHÔNG chứa quyết định an
# toàn/business logic (chỉ lắp UI rồi gọi ``namios_assistant.engine``), nên
# tắt mypy riêng cho file này thay vì nới lỏng toàn cục (cùng quy ước
# ``namios_welcome.ui``).

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from PySide6.QtCore import (  # type: ignore[import-not-found]
    QEvent,
    QObject,
    QPoint,
    QProcess,
    Qt,
    QThread,
    QUrl,
    Signal,
)
from PySide6.QtGui import QDesktopServices, QGuiApplication  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from namios_assistant.branding import build_stylesheet
from namios_assistant.engine import (
    AssistantAnswer,
    AssistantEngine,
    InstallPlan,
    InstallResult,
    OcrResult,
    TaskPlan,
    install_deb_from_url,
    install_package,
    ocr_image,
)
from namios_assistant.engine.related_tools import RELATED_TOOLS, RelatedTool
from namios_assistant.engine.suggestions import starter_suggestions
from namios_core.paths import cache_dir
from namios_i18n import Lang, resolve_lang, t

__all__ = ["AssistantWindow"]

_MessageRole = Literal["you", "assistant", "system"]

_BUBBLE_OBJECT_NAME: dict[_MessageRole, str] = {
    "you": "BubbleYou",
    "assistant": "BubbleAssistant",
    "system": "BubbleSystem",
}

_BUBBLE_MAX_WIDTH_PX = 520


class _AskWorker(QObject):
    """Chạy ``AssistantEngine.ask`` trong ``QThread`` riêng — gọi model AI
    trực tuyến (nếu cấu hình) có thể mất vài giây, KHÔNG được treo UI."""

    finished = Signal(object)  # AssistantAnswer
    failed = Signal(str)

    def __init__(self, engine: AssistantEngine, text: str, lang: Lang) -> None:
        super().__init__()
        self._engine = engine
        self._text = text
        self._lang = lang

    def run(self) -> None:
        try:
            answer = self._engine.ask(self._text, lang=self._lang)
        except Exception as exc:  # noqa: BLE001 - phòng thủ kép; engine đã tự fail-safe
            self.failed.emit(str(exc))
            return
        self.finished.emit(answer)


class _OcrWorker(QObject):
    """Chạy ``ocr_image`` trong ``QThread`` riêng — tesseract trên ảnh lớn
    có thể mất vài giây."""

    finished = Signal(object)  # OcrResult

    def __init__(self, image_path: Path) -> None:
        super().__init__()
        self._image_path = image_path

    def run(self) -> None:
        try:
            result = ocr_image(self._image_path)
        except Exception as exc:  # noqa: BLE001 - OCR phải fail-safe tuyệt đối
            result = OcrResult(
                text=None, available=False, detail=f"Lỗi OCR không lường được: {exc}"
            )
        self.finished.emit(result)


class _InstallWorker(QObject):
    """Chạy ``installer.install_package`` (pkexec, có thể mất vài giây/chờ
    người dùng nhập mật khẩu polkit) trong luồng riêng — cùng khuôn
    ``_AskWorker``/``_OcrWorker`` ở trên (tránh treo UI khi chờ pkexec)."""

    finished = Signal(object)  # InstallResult

    def __init__(self, *, method: str, package_id: str) -> None:
        super().__init__()
        self._method = method
        self._package_id = package_id

    def run(self) -> None:
        try:
            result = install_package(method=self._method, package_id=self._package_id)
        except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring lớp
            result = InstallResult(success=False, message=f"Lỗi không lường được: {exc}")
        self.finished.emit(result)


class _DebInstallWorker(QObject):
    """Chạy ``installer.install_deb_from_url`` (tải ``.deb`` từ domain chính
    chủ đã kiểm duyệt rồi ``pkexec apt-get install`` — có thể mất vài giây
    tải mạng + chờ người dùng nhập mật khẩu polkit) trong luồng riêng — cùng
    khuôn ``_InstallWorker`` ở trên, chỉ khác hàm gọi (Vendor .deb
    auto-install, thêm 12/11/2026, xem ``engine/installer.py``)."""

    finished = Signal(object)  # InstallResult

    def __init__(self, *, url: str, verify_domain: str) -> None:
        super().__init__()
        self._url = url
        self._verify_domain = verify_domain

    def run(self) -> None:
        try:
            result = install_deb_from_url(self._url, self._verify_domain)
        except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring lớp
            result = InstallResult(success=False, message=f"Lỗi không lường được: {exc}")
        self.finished.emit(result)


class _PackInstallWorker(QObject):
    """Chạy LẦN LƯỢT từng ``InstallPlan`` con trong ``InstallPlan.members``
    ("Dev Pack" — ``method == "pack"``, thêm 12/11/2026, xem
    ``engine/app_catalog.py``) — mỗi gói con cài qua ĐÚNG phương thức riêng
    của nó (``pkg_install`` -> ``install_package``, ``deb_install`` ->
    ``install_deb_from_url``); module này KHÔNG tự chế một phương thức cài
    "gộp" nào khác. Phát ``progress`` TRƯỚC mỗi bước (để UI cập nhật nút
    "đang cài X/Y: <tên>") rồi ``finished`` với TOÀN BỘ kết quả khi xong hết
    (một hộp thoại kết quả tổng hợp, không phải N hộp thoại rời cho N gói
    con)."""

    progress = Signal(int, int, str)  # (chỉ số 1-based, tổng số, tên gói con)
    finished = Signal(list)  # list[tuple[str, InstallResult]]

    def __init__(self, members: tuple[InstallPlan, ...]) -> None:
        super().__init__()
        self._members = members

    def run(self) -> None:
        results: list[tuple[str, InstallResult]] = []
        total = len(self._members)
        for index, member in enumerate(self._members, start=1):
            self.progress.emit(index, total, member.title)
            try:
                if member.action_kind == "pkg_install":
                    result = install_package(
                        method=member.method, package_id=member.action_payload
                    )
                elif member.action_kind == "deb_install":
                    result = install_deb_from_url(member.action_payload, member.verify_domain)
                else:
                    # Gói con khai báo method lạ/không tự cài được (vd
                    # "wine"/"none"/"open_url") — KHÔNG đoán cách cài khác,
                    # báo rõ để người dùng tự xử lý món đó riêng.
                    result = InstallResult(
                        success=False,
                        message=(
                            f"Phương thức cài '{member.method}' của \"{member.title}\" "
                            "không tự cài được trong bộ — hãy hỏi riêng Trợ lý về món này."
                        ),
                    )
            except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring lớp
                result = InstallResult(success=False, message=f"Lỗi không lường được: {exc}")
            results.append((member.title, result))
        self.finished.emit(results)


class AssistantWindow(QMainWindow):
    def __init__(
        self,
        *,
        engine: AssistantEngine | None = None,
        lang: Lang | str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._lang = resolve_lang(lang)
        self._engine = engine if engine is not None else AssistantEngine()
        self._thread: QThread | None = None
        self._worker: QObject | None = None
        self._install_thread: QThread | None = None
        self._install_worker: QObject | None = None

        self.setWindowTitle(t("assistant.ui.window_title", lang=self._lang))
        self.resize(760, 680)
        self.setStyleSheet(build_stylesheet())
        self._build_ui()

    # ------------------------------------------------------------------
    # Lắp widget
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AssistantRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        status_text = (
            t(
                "assistant.ui.status.online_configured",
                lang=self._lang,
                model=self._engine.online_model_name or "",
            )
            if self._engine.online_configured
            else t("assistant.ui.status.offline_only", lang=self._lang)
        )
        status_banner = QLabel(status_text)
        status_banner.setObjectName("StatusBanner")
        root_layout.addWidget(status_banner)

        self._transcript = QListWidget()
        self._transcript.setObjectName("Transcript")
        self._transcript.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._transcript.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._transcript.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(self._transcript, stretch=1)

        root_layout.addWidget(self._build_input_row())

        footer = QLabel(t("assistant.ui.footer.disclaimer", lang=self._lang))
        footer.setObjectName("FooterDisclaimer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(True)
        root_layout.addWidget(footer)

        self._show_intro()

    def _show_intro(self) -> None:
        """Lời chào + vài gợi ý khởi đầu bấm-được (lấy NGUYÊN VĂN tiêu đề entry
        "howto" thật trong KB qua ``starter_suggestions`` — không bịa câu gợi ý
        mới). Bấm một gợi ý = điền vào ô nhập rồi gửi luôn, để người dùng mới
        thấy ngay Trợ lý giúp được gì mà không phải tự nghĩ câu hỏi đầu tiên."""

        self._append_bubble("assistant", t("assistant.ui.greeting", lang=self._lang))
        try:
            suggestions = starter_suggestions(
                self._engine.offline_knowledge_base, lang=self._lang
            )
        except Exception:  # noqa: BLE001 - gợi ý là tiện ích phụ, lỗi không được treo UI
            suggestions = ()
        if suggestions:
            buttons = [
                (text, (lambda checked=False, value=text: self._use_suggestion(value)))
                for text in suggestions
            ]
            self._append_bubble(
                "system",
                t("assistant.ui.suggestions.heading", lang=self._lang),
                buttons=buttons,
            )

    def _use_suggestion(self, text: str) -> None:
        if self._thread is not None:
            return  # đang xử lý một yêu cầu khác — bỏ qua, không chạy chồng
        self._input_box.setPlainText(text)
        self._on_send_clicked()

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        layout = QVBoxLayout(header)
        title = QLabel(t("assistant.ui.header.title", lang=self._lang))
        title.setObjectName("HeaderTitle")
        subtitle = QLabel(t("assistant.ui.header.subtitle", lang=self._lang))
        subtitle.setObjectName("HeaderSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_input_row(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        self._input_box = QPlainTextEdit()
        self._input_box.setObjectName("InputBox")
        self._input_box.setPlaceholderText(t("assistant.ui.input.placeholder", lang=self._lang))
        self._input_box.setFixedHeight(90)
        self._input_box.installEventFilter(self)
        layout.addWidget(self._input_box)

        buttons_row = QHBoxLayout()
        self._paste_button = QPushButton(t("assistant.ui.button.paste_error", lang=self._lang))
        self._paste_button.clicked.connect(self._on_paste_error_clicked)
        self._attach_button = QPushButton(t("assistant.ui.button.attach_image", lang=self._lang))
        self._attach_button.clicked.connect(self._on_attach_image_clicked)
        self._send_button = QPushButton(t("assistant.ui.button.send", lang=self._lang))
        self._send_button.setObjectName("SendButton")
        self._send_button.clicked.connect(self._on_send_clicked)

        buttons_row.addWidget(self._paste_button)
        buttons_row.addWidget(self._attach_button)
        buttons_row.addStretch(1)
        buttons_row.addWidget(self._send_button)
        layout.addLayout(buttons_row)

        return container

    # ------------------------------------------------------------------
    # Nhập liệu
    # ------------------------------------------------------------------

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - tên API Qt
        if watched is self._input_box and event.type() == QEvent.Type.KeyPress:
            is_enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            if is_enter and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._on_send_clicked()
                return True
        return super().eventFilter(watched, event)

    def _on_paste_error_clicked(self) -> None:
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text() if clipboard is not None else ""
        if not text or not text.strip():
            self._append_system(t("assistant.ui.system.clipboard_text_empty", lang=self._lang))
            return
        current = self._input_box.toPlainText()
        if current.strip():
            self._input_box.setPlainText(f"{current.rstrip()}\n{text}")
        else:
            self._input_box.setPlainText(text)

    def _on_attach_image_clicked(self) -> None:
        menu = QMenu(self)
        paste_action = menu.addAction(
            t("assistant.ui.attach.menu.paste_clipboard_image", lang=self._lang)
        )
        file_action = menu.addAction(t("assistant.ui.attach.menu.choose_file", lang=self._lang))
        chosen = menu.exec(
            self._attach_button.mapToGlobal(QPoint(0, self._attach_button.height()))
        )
        if chosen is paste_action:
            self._attach_from_clipboard()
        elif chosen is file_action:
            self._attach_from_file()

    def _attach_from_clipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        image = clipboard.image() if clipboard is not None else None
        if image is None or image.isNull():
            self._append_system(t("assistant.ui.system.no_image_source", lang=self._lang))
            return
        try:
            directory = cache_dir() / "assistant" / "clipboard-images"
            directory.mkdir(parents=True, exist_ok=True)
            image_path = directory / f"clip-{uuid.uuid4().hex}.png"
            image.save(str(image_path), "PNG")
        except OSError as exc:
            self._append_system(
                f"Không lưu được ảnh từ bộ nhớ tạm để OCR: {exc}"
            )
            return
        self._start_ocr(image_path)

    def _attach_from_file(self) -> None:
        path_str, _selected_filter = QFileDialog.getOpenFileName(
            self,
            t("assistant.ui.attach.dialog_title", lang=self._lang),
            str(Path.home()),
            t("assistant.ui.attach.image_filter", lang=self._lang),
        )
        if not path_str:
            return
        self._start_ocr(Path(path_str))

    # ------------------------------------------------------------------
    # Gửi câu hỏi / chạy OCR ở luồng nền (không treo UI)
    # ------------------------------------------------------------------

    def _on_send_clicked(self) -> None:
        if self._thread is not None:
            return  # đã có 1 yêu cầu đang xử lý — bỏ qua bấm thêm, không chạy chồng
        text = self._input_box.toPlainText().strip()
        if not text:
            self._append_system(t("assistant.ui.system.empty_input", lang=self._lang))
            return
        self._append_bubble("you", text)
        self._input_box.clear()
        self._set_busy(True)

        worker = _AskWorker(self._engine, text, self._lang)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_ask_finished)
        worker.failed.connect(self._on_ask_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(self._clear_worker_refs)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_ask_finished(self, answer: AssistantAnswer) -> None:
        # Khi có ``task_plan`` (Task Concierge), nút hành động của tác vụ ĐÃ là
        # công cụ liên quan nhất rồi — bỏ các nút "công cụ liên quan" chung để
        # tránh hai nút trùng ý (vd tác vụ Wi-Fi mở nConnect, mà related-tool
        # cũng là nConnect). Các câu trả lời khác giữ nguyên nút công cụ.
        tool_buttons = (
            [
                (
                    t(
                        "assistant.ui.button.open_related_tool",
                        lang=self._lang,
                        tool=(tool.label_vi if self._lang == Lang.VI else tool.label_en),
                    ),
                    (lambda checked=False, value=tool: self._launch_related_tool(value)),
                )
                for tool in answer.related_tools
            ]
            if answer.task_plan is None
            else []
        )
        if answer.install_plan is not None:
            extra_widget = self._build_install_plan_widget(answer.install_plan)
        elif answer.task_plan is not None:
            extra_widget = self._build_task_plan_widget(answer.task_plan)
        else:
            extra_widget = None
        self._append_bubble(
            "assistant",
            answer.text,
            note=answer.note,
            buttons=tool_buttons or None,
            extra_widget=extra_widget,
        )
        self._set_busy(False)

    def _launch_related_tool(self, tool: RelatedTool) -> None:
        """Mở công cụ NaMiOS thật bằng ``QProcess.startDetached`` (argv TĨNH từ
        registry — KHÔNG qua shell, KHÔNG nội suy input người dùng; xem
        ``engine/related_tools.py``). Mở thất bại thì báo rõ + nhắc tự mở từ
        trình đơn, KHÔNG nuốt lỗi im lặng."""

        program = tool.exec_argv[0]
        arguments = list(tool.exec_argv[1:])
        label = tool.label_vi if self._lang == Lang.VI else tool.label_en
        try:
            started = QProcess.startDetached(program, arguments)
        except Exception as exc:  # noqa: BLE001 - mở công cụ ngoài phải fail-safe
            started = False
            reason = str(exc)
        else:
            reason = "startDetached=false"
        if not started:
            self._append_system(
                t(
                    "assistant.ui.system.related_tool_launch_failed",
                    lang=self._lang,
                    tool=label,
                    reason=reason,
                )
            )

    # ------------------------------------------------------------------
    # Task Concierge — thẻ hướng dẫn nhanh + nút mở ĐÚNG trang Cài đặt/công cụ
    # dưới câu trả lời. CHỈ hiển thị dữ liệu lấy từ ``TaskPlan`` (đã kiểm duyệt
    # ở ``engine/task_catalog.py``) — nút chạy ĐÚNG ``action_exec`` tĩnh có
    # trong catalog, KHÔNG tự chế lệnh nào ở tầng UI (xem HARD RULE ở module đó).
    # ------------------------------------------------------------------
    def _build_task_plan_widget(self, plan: TaskPlan) -> QFrame:
        card = QFrame()
        card.setObjectName("InstallPlanCard")
        layout = QVBoxLayout(card)

        title_label = QLabel(plan.title_vi)
        title_label.setObjectName("InstallPlanTitle")
        bold_font = title_label.font()
        bold_font.setBold(True)
        title_label.setFont(bold_font)
        layout.addWidget(title_label)

        if plan.steps_vi:
            steps_heading = QLabel(t("assistant.ui.task_plan.steps_heading", lang=self._lang))
            steps_heading.setObjectName("BubbleNote")
            layout.addWidget(steps_heading)
            # Đánh số các bước ở tầng hiển thị (catalog lưu bước KHÔNG kèm số
            # để dễ sửa/sắp lại) — ghép thành một nhãn nhiều dòng.
            steps_text = "\n".join(
                f"{index}. {step}" for index, step in enumerate(plan.steps_vi, start=1)
            )
            steps_label = QLabel(steps_text)
            steps_label.setWordWrap(True)
            layout.addWidget(steps_label)

        if plan.action_exec and plan.action_label_vi:
            action_btn = QPushButton(plan.action_label_vi)
            action_btn.setObjectName("BubbleActionButton")
            action_btn.clicked.connect(
                lambda checked=False, p=plan: self._launch_task_action(p)
            )
            layout.addWidget(action_btn)

        return card

    def _launch_task_action(self, plan: TaskPlan) -> None:
        """Chạy ``plan.action_exec`` bằng ``QProcess.startDetached`` (argv TĨNH
        từ task-catalog đã kiểm duyệt — KHÔNG qua shell, KHÔNG nội suy input
        người dùng; cùng cơ chế an toàn ``_launch_related_tool``). Mở thất bại
        thì báo rõ, KHÔNG nuốt lỗi im lặng."""

        if not plan.action_exec:
            return
        program = plan.action_exec[0]
        arguments = list(plan.action_exec[1:])
        try:
            started = QProcess.startDetached(program, arguments)
        except Exception as exc:  # noqa: BLE001 - mở công cụ ngoài phải fail-safe
            started = False
            reason = str(exc)
        else:
            reason = "startDetached=false"
        if not started:
            self._append_system(
                t(
                    "assistant.ui.system.task_action_launch_failed",
                    lang=self._lang,
                    tool=plan.action_label_vi or program,
                    reason=reason,
                )
            )

    # ------------------------------------------------------------------
    # App & Driver Concierge — thẻ phương án cài đặt/driver dưới câu trả lời.
    # CHỈ hiển thị dữ liệu lấy từ ``InstallPlan`` (đã kiểm duyệt ở
    # ``engine/app_catalog.py``) — KHÔNG tự thêm bất kỳ đường link/tên gói
    # nào khác ở tầng UI này (xem HARD RULE ở docstring module đó).
    # ------------------------------------------------------------------
    def _build_install_plan_widget(self, plan: InstallPlan) -> QFrame:
        card = QFrame()
        card.setObjectName("InstallPlanCard")
        layout = QVBoxLayout(card)

        title_label = QLabel(plan.title)
        title_label.setObjectName("InstallPlanTitle")
        bold_font = title_label.font()
        bold_font.setBold(True)
        title_label.setFont(bold_font)
        layout.addWidget(title_label)

        if plan.note_vi:
            note_label = QLabel(plan.note_vi)
            note_label.setWordWrap(True)
            layout.addWidget(note_label)

        if plan.action_kind == "pkg_install":
            install_btn = QPushButton(t("assistant.ui.button.install_one_click", lang=self._lang))
            install_btn.setObjectName("BubbleActionButton")
            install_btn.clicked.connect(
                lambda checked=False, p=plan, b=install_btn: self._on_install_clicked(p, b)
            )
            layout.addWidget(install_btn)
        elif plan.action_kind == "open_url":
            if plan.verify_domain:
                domain_label = QLabel(
                    t(
                        "assistant.ui.install_plan.domain_label",
                        lang=self._lang,
                        domain=plan.verify_domain,
                    )
                )
                domain_label.setObjectName("BubbleNote")
                layout.addWidget(domain_label)
            open_btn = QPushButton(t("assistant.ui.button.open_official_page", lang=self._lang))
            open_btn.setObjectName("BubbleActionButton")
            open_btn.clicked.connect(
                lambda checked=False, p=plan: self._on_open_official_url_clicked(p)
            )
            layout.addWidget(open_btn)
        elif plan.action_kind == "deb_install":
            # Vendor .deb auto-install (thêm 12/11/2026) — nút CHÍNH "Cài 1
            # chạm" THỰC SỰ tải+cài (xem ``installer.install_deb_from_url``);
            # vẫn hiện domain chính chủ để người dùng thấy rõ nguồn được tin
            # (cùng cách ``open_url`` hiện domain_label ở trên), kèm nút PHỤ
            # "Mở trang chính thức" dự phòng khi domain chính chủ KHÔNG trả
            # về một liên kết .deb tải trực tiếp (vd trang hướng dẫn cài qua
            # kho riêng) — tải/cài tự động sẽ thất bại trung thực ở bước
            # kiểm magic bytes trong trường hợp đó, không giả vờ thành công.
            if plan.verify_domain:
                domain_label = QLabel(
                    t(
                        "assistant.ui.install_plan.domain_label",
                        lang=self._lang,
                        domain=plan.verify_domain,
                    )
                )
                domain_label.setObjectName("BubbleNote")
                layout.addWidget(domain_label)
            install_btn = QPushButton(t("assistant.ui.button.install_one_click", lang=self._lang))
            install_btn.setObjectName("BubbleActionButton")
            install_btn.clicked.connect(
                lambda checked=False, p=plan, b=install_btn: self._on_deb_install_clicked(p, b)
            )
            layout.addWidget(install_btn)
            open_btn = QPushButton(t("assistant.ui.button.open_official_page", lang=self._lang))
            open_btn.setObjectName("BubbleActionButton")
            open_btn.clicked.connect(
                lambda checked=False, p=plan: self._on_open_official_url_clicked(p)
            )
            layout.addWidget(open_btn)
        elif plan.action_kind == "pack_install":
            # Dev Pack (thêm 12/11/2026) — một nút cài TUẦN TỰ từng app con
            # trong ``plan.members`` (xem ``_PackInstallWorker``). Liệt kê
            # tên các món trong bộ TRƯỚC khi bấm, để người dùng biết chính
            # xác sẽ cài gì (không có gì "ẩn" trong một cái tên gộp chung).
            if plan.members:
                members_label = QLabel(
                    t(
                        "assistant.ui.install_plan.pack_members_label",
                        lang=self._lang,
                        members=", ".join(member.title for member in plan.members),
                    )
                )
                members_label.setWordWrap(True)
                layout.addWidget(members_label)
            pack_btn = QPushButton(t("assistant.ui.button.install_pack", lang=self._lang))
            pack_btn.setObjectName("BubbleActionButton")
            pack_btn.clicked.connect(
                lambda checked=False, p=plan, b=pack_btn: self._on_pack_install_clicked(p, b)
            )
            layout.addWidget(pack_btn)
        elif plan.action_kind == "wine":
            nwine = RELATED_TOOLS.get("nwine")
            if nwine is not None:
                tool_label = nwine.label_vi if self._lang == Lang.VI else nwine.label_en
                wine_hint = QLabel(
                    t("assistant.ui.install_plan.wine_hint", lang=self._lang, tool=tool_label)
                )
                wine_hint.setWordWrap(True)
                layout.addWidget(wine_hint)
                wine_btn = QPushButton(
                    t("assistant.ui.button.open_related_tool", lang=self._lang, tool=tool_label)
                )
                wine_btn.setObjectName("BubbleActionButton")
                wine_btn.clicked.connect(
                    lambda checked=False, tool=nwine: self._launch_related_tool(tool)
                )
                layout.addWidget(wine_btn)
        # action_kind == "none": không có hành động nào an toàn để gợi ý mở
        # (xem docstring module) — chỉ note_vi/alt_vi (đã/sẽ hiển thị).

        if plan.alt_vi:
            alt_label = QLabel(
                t("assistant.ui.install_plan.alt_label", lang=self._lang, alt=plan.alt_vi)
            )
            alt_label.setObjectName("BubbleNote")
            alt_label.setWordWrap(True)
            layout.addWidget(alt_label)

        return card

    def _on_install_clicked(self, plan: InstallPlan, button: QPushButton) -> None:
        if self._install_thread is not None:
            return  # đang cài một thứ khác — chặn double-click, không chạy chồng
        button.setEnabled(False)
        button.setText(t("assistant.ui.install.running", lang=self._lang))

        worker = _InstallWorker(method=plan.method, package_id=plan.action_payload)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(
            lambda result, b=button: self._on_install_finished(result, b)
        )
        worker.finished.connect(thread.quit)
        thread.finished.connect(self._clear_install_worker_refs)
        thread.finished.connect(thread.deleteLater)
        self._install_thread = thread
        self._install_worker = worker
        thread.start()

    def _on_install_finished(self, result: InstallResult, button: QPushButton) -> None:
        button.setEnabled(True)
        button.setText(t("assistant.ui.button.install_one_click", lang=self._lang))
        self._show_result_dialog(ok=result.success, message=result.message)

    def _on_deb_install_clicked(self, plan: InstallPlan, button: QPushButton) -> None:
        """Nút "Cài 1 chạm" của ``action_kind == "deb_install"`` (Vendor
        .deb auto-install) — cùng khuôn ``_on_install_clicked`` ở trên, chỉ
        khác worker/hàm gọi dưới (``installer.install_deb_from_url`` thay
        ``install_package``, xem docstring ``_DebInstallWorker``)."""

        if self._install_thread is not None:
            return  # đang cài một thứ khác — chặn double-click, không chạy chồng
        button.setEnabled(False)
        button.setText(t("assistant.ui.install.running", lang=self._lang))

        worker = _DebInstallWorker(url=plan.action_payload, verify_domain=plan.verify_domain)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(
            lambda result, b=button: self._on_install_finished(result, b)
        )
        worker.finished.connect(thread.quit)
        thread.finished.connect(self._clear_install_worker_refs)
        thread.finished.connect(thread.deleteLater)
        self._install_thread = thread
        self._install_worker = worker
        thread.start()

    def _on_pack_install_clicked(self, plan: InstallPlan, button: QPushButton) -> None:
        """Nút "Cài cả bộ (Dev Pack)" (``action_kind == "pack_install"``) —
        cài TUẦN TỰ từng ``InstallPlan`` con trong ``plan.members`` qua
        ``_PackInstallWorker``, cập nhật nhãn nút theo tiến độ
        (``_on_pack_progress``), rồi hiện MỘT hộp thoại kết quả tổng hợp
        khi xong hết (``_on_pack_finished``) — không phải N hộp thoại rời."""

        if self._install_thread is not None:
            return  # đang cài một thứ khác — chặn double-click, không chạy chồng
        if not plan.members:
            self._append_system(t("assistant.ui.system.pack_empty", lang=self._lang))
            return
        button.setEnabled(False)
        button.setText(t("assistant.ui.install.running", lang=self._lang))

        worker = _PackInstallWorker(plan.members)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(
            lambda index, total, title, b=button: self._on_pack_progress(b, index, total, title)
        )
        worker.finished.connect(lambda results, b=button: self._on_pack_finished(results, b))
        worker.finished.connect(thread.quit)
        thread.finished.connect(self._clear_install_worker_refs)
        thread.finished.connect(thread.deleteLater)
        self._install_thread = thread
        self._install_worker = worker
        thread.start()

    def _on_pack_progress(self, button: QPushButton, index: int, total: int, title: str) -> None:
        button.setText(
            t(
                "assistant.ui.install.pack_running",
                lang=self._lang,
                done=index,
                total=total,
                title=title,
            )
        )

    def _on_pack_finished(
        self, results: list[tuple[str, InstallResult]], button: QPushButton
    ) -> None:
        button.setEnabled(True)
        button.setText(t("assistant.ui.button.install_pack", lang=self._lang))

        ok_count = sum(1 for _title, result in results if result.success)
        total = len(results)
        lines = [
            t(
                "assistant.ui.install.pack_item_line",
                lang=self._lang,
                status=("OK" if result.success else "FAIL"),
                title=title,
                message=result.message,
            )
            for title, result in results
        ]
        summary = t("assistant.ui.install.pack_summary", lang=self._lang, ok=ok_count, total=total)
        message = summary + "\n\n" + "\n\n".join(lines)
        self._show_result_dialog(ok=(ok_count == total), message=message)

    def _show_result_dialog(self, *, ok: bool, message: str) -> None:
        """Hộp thoại kết quả cài đặt dùng chung — cho CẢ cài đơn
        (``_on_install_finished``) lẫn cài cả bộ (``_on_pack_finished``), để
        hai luồng không có hai cách hiển thị khác nhau cho cùng một ý
        nghĩa (thành công/thất bại + chi tiết dài bị cắt)."""

        title_key = "assistant.ui.install.dialog.title_ok" if ok else "assistant.ui.install.dialog.title_fail"
        box = QMessageBox(self)
        box.setWindowTitle(t(title_key, lang=self._lang))
        box.setIcon(QMessageBox.Icon.Information if ok else QMessageBox.Icon.Warning)
        message = message or "(không có nội dung)"
        if len(message) > 600:
            box.setText(message[:600] + "\n\n[... bấm nút hiện chi tiết bên dưới để xem đầy đủ ...]")
            box.setDetailedText(message)
        else:
            box.setText(message)
        box.exec()

    def _clear_install_worker_refs(self) -> None:
        self._install_thread = None
        self._install_worker = None

    def _on_open_official_url_clicked(self, plan: InstallPlan) -> None:
        """Mở ``plan.action_payload`` — URL lấy TRỰC TIẾP từ catalog đã kiểm
        duyệt (``engine/app_catalog.py``, KHÔNG đường nào khác được phép ở
        đây) — bằng trình duyệt mặc định của hệ thống (``QDesktopServices.
        openUrl``, cùng cách ``namios_welcome.ui`` mở file hướng dẫn cục bộ)."""

        opened = QDesktopServices.openUrl(QUrl(plan.action_payload))
        if not opened:
            self._append_system(
                t(
                    "assistant.ui.open_url.failed",
                    lang=self._lang,
                    domain=plan.verify_domain or plan.action_payload,
                )
            )

    def _on_ask_failed(self, message: str) -> None:
        self._append_system(t("assistant.ui.error.engine_unexpected", lang=self._lang))
        self._set_busy(False)

    def _start_ocr(self, image_path: Path) -> None:
        if self._thread is not None:
            return
        self._append_system(t("assistant.ui.system.ocr_running", lang=self._lang))
        self._set_busy(True)

        worker = _OcrWorker(image_path)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_ocr_finished)
        worker.finished.connect(thread.quit)
        thread.finished.connect(self._clear_worker_refs)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_ocr_finished(self, result: OcrResult) -> None:
        if result.text:
            current = self._input_box.toPlainText()
            combined = f"{current.rstrip()}\n{result.text}" if current.strip() else result.text
            self._input_box.setPlainText(combined)
            self._append_system(t("assistant.ui.system.ocr_text_inserted", lang=self._lang))
        else:
            # ``result.detail`` đã là một câu hoàn chỉnh dễ hiểu (xem
            # ``namios_assistant.engine.ocr``) — hiển thị nguyên văn, KHÔNG
            # giả vờ đã đọc được chữ từ ảnh khi thực ra không.
            self._append_system(result.detail)
        self._set_busy(False)

    def _clear_worker_refs(self) -> None:
        self._thread = None
        self._worker = None

    def _set_busy(self, busy: bool) -> None:
        self._send_button.setDisabled(busy)
        self._paste_button.setDisabled(busy)
        self._attach_button.setDisabled(busy)
        self._send_button.setText(
            t("assistant.ui.button.sending", lang=self._lang)
            if busy
            else t("assistant.ui.button.send", lang=self._lang)
        )

    # ------------------------------------------------------------------
    # Transcript (danh sách tin nhắn dạng bong bóng chat)
    # ------------------------------------------------------------------

    def _append_system(self, text: str) -> None:
        self._append_bubble("system", text)

    def _append_bubble(
        self,
        role: _MessageRole,
        text: str,
        *,
        note: str | None = None,
        buttons: list[tuple[str, Callable[..., None]]] | None = None,
        extra_widget: QWidget | None = None,
    ) -> None:
        sender_label_text = {
            "you": t("assistant.ui.transcript.you_label", lang=self._lang),
            "assistant": t("assistant.ui.transcript.assistant_label", lang=self._lang),
            "system": t("assistant.ui.transcript.system_label", lang=self._lang),
        }[role]

        bubble = QFrame()
        bubble.setObjectName(_BUBBLE_OBJECT_NAME[role])
        bubble.setMaximumWidth(_BUBBLE_MAX_WIDTH_PX)
        bubble_layout = QVBoxLayout(bubble)

        sender_label = QLabel(sender_label_text)
        sender_font = sender_label.font()
        sender_font.setBold(True)
        sender_label.setFont(sender_font)
        bubble_layout.addWidget(sender_label)

        body_label = QLabel()
        body_label.setWordWrap(True)
        body_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        # "you" = văn bản người dùng dán nguyên văn -> KHÔNG diễn giải markdown
        # (tránh dòng log có "**"/"#" bị hiểu nhầm thành định dạng). KB/model
        # trả lời ("assistant"/"system") dùng Markdown (Qt >= 5.14 hỗ trợ sẵn
        # trong QLabel) vì nội dung KB dùng cú pháp "**đậm**"/danh sách số.
        body_label.setTextFormat(
            Qt.TextFormat.PlainText if role == "you" else Qt.TextFormat.MarkdownText
        )
        body_label.setText(text)
        bubble_layout.addWidget(body_label)

        if note:
            note_label = QLabel(note)
            note_label.setObjectName("BubbleNote")
            note_label.setWordWrap(True)
            bubble_layout.addWidget(note_label)

        if buttons:
            # Xếp dọc (mỗi nút một dòng) để không tràn chiều ngang bong bóng khi
            # có nhiều nút (vd danh sách gợi ý khởi đầu) — cùng một cơ chế dùng
            # cho cả "công cụ liên quan" (dưới câu trả lời) lẫn "gợi ý nhanh".
            for button_text, on_click in buttons:
                button = QPushButton(button_text)
                button.setObjectName("BubbleActionButton")
                button.clicked.connect(on_click)
                bubble_layout.addWidget(button)

        if extra_widget is not None:
            bubble_layout.addWidget(extra_widget)

        container = QWidget()
        outer_layout = QHBoxLayout(container)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        if role == "you":
            outer_layout.addStretch(1)
            outer_layout.addWidget(bubble)
        else:
            outer_layout.addWidget(bubble)
            outer_layout.addStretch(1)

        item = QListWidgetItem()
        item.setSizeHint(container.sizeHint())
        self._transcript.addItem(item)
        self._transcript.setItemWidget(item, container)
        self._transcript.scrollToBottom()
