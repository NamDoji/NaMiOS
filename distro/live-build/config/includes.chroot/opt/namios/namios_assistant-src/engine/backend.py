"""``AssistantEngine`` — điều phối offline KB + online LLM (tuỳ chọn).

Hợp đồng DUY NHẤT caller (``namios_assistant.ui``) cần biết: gọi
``engine.ask(text)``, luôn nhận về một ``AssistantAnswer`` — KHÔNG BAO GIỜ
raise, KHÔNG BAO GIỜ trả lời "từ AI" khi thực chất là KB ngoại tuyến (và
ngược lại). Đây là bất biến quan trọng nhất của module này."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from namios_assistant.config import AssistantConfig, load_config
from namios_assistant.engine.knowledge_base import KnowledgeBase
from namios_assistant.engine.offline_backend import OfflineKbBackend
from namios_assistant.engine.online_backend import OnlineBackendError, OnlineLlmBackend
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
    bỏ qua field này (xem ``docs/SMARTAI-ASSISTANT.md`` "Honest UX")."""

    text: str
    source: AnswerSource
    subsystem: str | None
    kb_match_ids: tuple[str, ...]
    note: str


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

    def ask(self, text: str, *, lang: Lang | str | None = None) -> AssistantAnswer:
        resolved = resolve_lang(lang)

        offline_result = self._offline.answer(text, lang=resolved)
        offline_note = t("assistant.engine.note.offline_kb", lang=resolved)
        offline_answer = AssistantAnswer(
            text=offline_result.text,
            source="offline_kb",
            subsystem=offline_result.subsystem,
            kb_match_ids=offline_result.kb_match_ids,
            note=offline_note,
        )

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
        )
