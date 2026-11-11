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
    Signal,
)
from PySide6.QtGui import QGuiApplication  # type: ignore[import-not-found]
from PySide6.QtWidgets import (  # type: ignore[import-not-found]
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from namios_assistant.branding import build_stylesheet
from namios_assistant.engine import AssistantAnswer, AssistantEngine, OcrResult, ocr_image
from namios_assistant.engine.related_tools import RelatedTool
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
        tool_buttons = [
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
        self._append_bubble(
            "assistant", answer.text, note=answer.note, buttons=tool_buttons or None
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
