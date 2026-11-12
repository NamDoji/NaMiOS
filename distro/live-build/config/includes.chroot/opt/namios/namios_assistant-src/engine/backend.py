"""``AssistantEngine`` — điều phối offline KB + online LLM (tuỳ chọn).

Hợp đồng DUY NHẤT caller (``namios_assistant.ui``) cần biết: gọi
``engine.ask(text)``, luôn nhận về một ``AssistantAnswer`` — KHÔNG BAO GIỜ
raise, KHÔNG BAO GIỜ trả lời "từ AI" khi thực chất là KB ngoại tuyến (và
ngược lại). Đây là bất biến quan trọng nhất của module này."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from namios_assistant.config import AssistantConfig, load_config
from namios_assistant.engine.app_catalog import (
    CatalogLookup,
    InstallPlan,
    resolve_catalog_lookup,
)
from namios_assistant.engine.knowledge_base import KnowledgeBase
from namios_assistant.engine.task_catalog import (
    OPEN_SETTINGS_FALLBACK,
    TaskLookup,
    TaskPlan,
    resolve_task_lookup,
)
from namios_assistant.engine.offline_backend import OfflineKbBackend
from namios_assistant.engine.online_backend import OnlineBackendError, OnlineLlmBackend
from namios_assistant.engine.related_tools import RelatedTool
from namios_i18n import Lang, resolve_lang, t
from namios_security import redact_text

__all__ = ["AssistantAnswer", "AssistantEngine"]

AnswerSource = Literal["offline_kb", "online_llm"]


@dataclass(frozen=True)
class AssistantAnswer:
    """Câu trả lời cuối cùng trả cho UI hiển thị.

    ``note`` là nhãn MINH BẠCH bắt buộc hiển thị cạnh ``text`` (vd "Trả lời
    từ KB ngoại tuyến (không cần mạng)." hay "Trả lời từ model AI trực tuyến
    (gpt-4o-mini)." hoặc lý do rơi về offline khi online lỗi) — UI KHÔNG được
    bỏ qua field này (xem ``docs/SMARTAI-ASSISTANT.md`` "Honest UX").

    ``related_tools`` (thêm 11/11/2026): công cụ NaMiOS thật nên gợi ý mở cho
    mảng/ca này (xem ``engine/related_tools.py``) — LUÔN tính từ kết quả
    phân loại/tra KB NGOẠI TUYẾN (``offline_result``), giữ nguyên bất kể
    ``source`` cuối cùng là ``"offline_kb"`` hay ``"online_llm"``, vì việc
    "mảng nào liên quan" là một sự thật về NỘI DUNG câu hỏi, không phụ thuộc
    ai (KB hay model) soạn ra câu trả lời.

    ``install_plan`` (thêm cho App & Driver Concierge, 11/11/2026): phương án
    cài đặt/driver đã kiểm duyệt (xem ``engine/app_catalog.py``) khi câu hỏi
    là ý định cài phần mềm/driver (``engine.classify.classify_catalog_intent``).
    Cùng lý do với ``related_tools``: đây là sự thật về NỘI DUNG câu hỏi
    ("app/driver nào được yêu cầu, có trong kho đã kiểm duyệt hay không"),
    không phụ thuộc backend nào soạn câu trả lời — XEM ``ask()`` cho lý do ý
    định cài đặt/driver KHÔNG BAO GIỜ giao tiếp tiếp cho model AI trực tuyến
    (tránh model tự diễn giải/bịa thêm một đường link khác ngoài danh sách đã
    kiểm duyệt).

    ``task_plan`` (thêm cho Task Concierge, 12/11/2026): tác vụ desktop đã
    kiểm duyệt (xem ``engine/task_catalog.py``) khi câu hỏi là "làm sao để…/
    tôi muốn…" một việc trên máy (đổi giao diện, kết nối Wi-Fi…). Cùng lý do
    với ``install_plan``: đây là sự thật về NỘI DUNG câu hỏi, và vì chống bịa,
    một câu hỏi tác vụ đã khớp (hoặc rõ là how-to) KHÔNG BAO GIỜ giao tiếp
    tiếp cho model AI trực tuyến — nút hành động CHỈ chạy ``exec`` tĩnh có
    trong catalog (xem ``ask()``)."""

    text: str
    source: AnswerSource
    subsystem: str | None
    kb_match_ids: tuple[str, ...]
    note: str
    related_tools: tuple[RelatedTool, ...] = ()
    install_plan: InstallPlan | None = None
    task_plan: TaskPlan | None = None


class AssistantEngine:
    def __init__(
        self,
        *,
        config: AssistantConfig | None = None,
        knowledge_base: KnowledgeBase | None = None,
    ) -> None:
        self._config = config if config is not None else load_config()
        self._offline = OfflineKbBackend(knowledge_base)
        self._online = OnlineLlmBackend(self._config)

    @property
    def online_configured(self) -> bool:
        return self._online.is_configured

    @property
    def online_model_name(self) -> str | None:
        return self._config.model

    @property
    def offline_knowledge_base(self) -> KnowledgeBase:
        """KB ngoại tuyến đang dùng — UI đọc để dựng gợi ý khởi đầu (xem
        ``engine/suggestions.py::starter_suggestions``), KHÔNG dùng để tự tra
        cứu riêng (mọi câu hỏi vẫn phải qua ``ask()`` để đi đúng luồng
        classify -> offline -> online)."""

        return self._offline.knowledge_base

    @staticmethod
    def _resolve_catalog(text: str) -> CatalogLookup | None:
        """Bọc ``resolve_catalog_lookup`` fail-safe tuyệt đối (cùng nguyên
        tắc toàn module, xem docstring lớp) — một lỗi không lường được ở
        tầng catalog (vd file dữ liệu hỏng theo cách không ngờ, dù
        ``app_catalog``/``knowledge_base`` đã tự fail-safe ở tầng đọc file)
        rơi về ``None`` (coi như không có ý định cài đặt/driver), KHÔNG được
        làm sập luồng hỏi-đáp chính."""

        try:
            return resolve_catalog_lookup(text)
        except Exception:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring hàm
            return None

    @staticmethod
    def _resolve_task(text: str) -> TaskLookup | None:
        """Bọc ``resolve_task_lookup`` fail-safe tuyệt đối (cùng nguyên tắc
        ``_resolve_catalog``) — một lỗi không lường được ở tầng task-catalog
        rơi về ``None`` (coi như không có ý định tác vụ), KHÔNG được làm sập
        luồng hỏi-đáp chính."""

        try:
            return resolve_task_lookup(text)
        except Exception:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring hàm
            return None

    def ask(self, text: str, *, lang: Lang | str | None = None) -> AssistantAnswer:
        resolved = resolve_lang(lang)

        offline_result = self._offline.answer(text, lang=resolved)
        offline_note = t("assistant.engine.note.offline_kb", lang=resolved)

        # App & Driver Concierge: nếu câu hỏi là ý định cài phần mềm/driver,
        # catalog đã kiểm duyệt (``engine/app_catalog.py``) quyết định TOÀN
        # BỘ phần "cài gì/link nào" — ghi đè văn bản KB chung chung (nếu có)
        # bằng một câu xác nhận ngắn + đính kèm ``InstallPlan`` cho UI vẽ thẻ
        # hành động; không khớp catalog -> thông báo trung thực, KHÔNG bịa.
        catalog_lookup = self._resolve_catalog(text)
        answer_text = offline_result.text
        install_plan: InstallPlan | None = None
        task_plan: TaskPlan | None = None
        # Task Concierge chỉ chạy khi KHÔNG phải ý định cài đặt/driver (catalog
        # được ưu tiên trước: "cài X"/máy-in-cụ-thể cụ thể hơn một tác vụ cài
        # đặt chung) — gộp vào if/elif để hai Concierge không bao giờ ghi đè
        # nhau trong cùng một câu trả lời.
        task_lookup: TaskLookup | None = None
        if catalog_lookup is not None:
            install_plan = catalog_lookup.plan
            if install_plan is not None:
                found_key = (
                    "assistant.engine.catalog.found_driver"
                    if catalog_lookup.intent == "driver_request"
                    else "assistant.engine.catalog.found_app"
                )
                answer_text = t(found_key, lang=resolved, title=install_plan.title)
            else:
                answer_text = t("assistant.engine.catalog.no_match", lang=resolved)
        else:
            # Task Concierge: "làm sao để thay đổi giao diện?"/"tôi muốn kết
            # nối Wi-Fi" -> tra kho TÁC VỤ đã kiểm duyệt (``task_catalog``),
            # ghi đè văn bản KB chung bằng một câu xác nhận ngắn + đính kèm
            # ``TaskPlan`` cho UI vẽ hướng dẫn + nút bấm-là-chạy. Rõ là how-to
            # nhưng không khớp tác vụ nào -> thông báo trung thực + nút mở
            # ``systemsettings`` (``OPEN_SETTINGS_FALLBACK``), KHÔNG bịa lệnh.
            task_lookup = self._resolve_task(text)
            if task_lookup is not None:
                if task_lookup.plan is not None:
                    task_plan = task_lookup.plan
                    answer_text = t(
                        "assistant.engine.task.found",
                        lang=resolved,
                        title=task_plan.title_vi,
                    )
                else:
                    task_plan = OPEN_SETTINGS_FALLBACK
                    answer_text = t("assistant.engine.task.no_match", lang=resolved)

        offline_answer = AssistantAnswer(
            text=answer_text,
            source="offline_kb",
            subsystem=offline_result.subsystem,
            kb_match_ids=offline_result.kb_match_ids,
            note=offline_note,
            related_tools=offline_result.related_tools,
            install_plan=install_plan,
            task_plan=task_plan,
        )

        if catalog_lookup is not None:
            # Ý định cài đặt/driver: KHÔNG giao tiếp cho model AI trực tuyến
            # viết lại câu trả lời — model không biết về catalog đã kiểm
            # duyệt, có thể diễn giải/bịa thêm một đường link/tên gói khác
            # ngoài danh sách đã duyệt, vi phạm nguyên tắc KHÔNG BAO GIỜ bịa
            # URL (xem docstring ``engine/app_catalog.py`` + ``AssistantAnswer``).
            # ``install_plan``/``related_tools`` đã gắn sẵn ở trên, đủ để UI
            # vẽ nút hành động — cả hai trường hợp khớp lẫn không khớp.
            return offline_answer

        if task_lookup is not None:
            # Ý định "làm sao để…/tôi muốn…": cùng lý do với catalog — KHÔNG
            # giao tiếp cho model AI trực tuyến (nút hành động CHỈ chạy ``exec``
            # tĩnh có trong task-catalog, model không được chế lệnh). Đã gắn
            # ``task_plan`` (tác vụ khớp HOẶC ``OPEN_SETTINGS_FALLBACK``).
            return offline_answer

        if not self._online.is_configured:
            return offline_answer

        try:
            online_text = self._online.ask(
                text, subsystem=offline_result.subsystem
            )
        except OnlineBackendError as exc:
            fallback_note = t(
                "assistant.engine.note.online_fallback",
                lang=resolved,
                reason=redact_text(str(exc)),
            )
            return replace(offline_answer, note=fallback_note)
        except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring module
            fallback_note = t(
                "assistant.engine.note.online_fallback",
                lang=resolved,
                reason=redact_text(f"lỗi không lường được: {exc}"),
            )
            return replace(offline_answer, note=fallback_note)

        online_note = t(
            "assistant.engine.note.online_llm",
            lang=resolved,
            model=self._config.model or "",
        )
        return AssistantAnswer(
            text=online_text,
            source="online_llm",
            subsystem=offline_result.subsystem,
            kb_match_ids=(),
            note=online_note,
            related_tools=offline_result.related_tools,
            install_plan=None,
            task_plan=None,
        )
