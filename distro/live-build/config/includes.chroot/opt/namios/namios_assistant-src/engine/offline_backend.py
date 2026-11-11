"""Backend NGOẠI TUYẾN (offline KB) — luôn chạy được, không cần mạng, không
cần cấu hình gì (xem ``docs/SMARTAI-ASSISTANT.md`` cho "sự thật ship offline
vs cần khoá"). Đây là đường trả lời MẶC ĐỊNH; ``AssistantEngine`` chỉ thay
bằng kết quả online khi backend online được cấu hình VÀ gọi thành công."""

from __future__ import annotations

from dataclasses import dataclass

from namios_assistant.engine.classify import classify_subsystem
from namios_assistant.engine.knowledge_base import KBMatch, KnowledgeBase
from namios_i18n import Lang, resolve_lang, t

__all__ = ["OfflineAnswer", "OfflineKbBackend"]


@dataclass(frozen=True)
class OfflineAnswer:
    """Kết quả một lần tra KB ngoại tuyến."""

    text: str
    subsystem: str | None
    kb_match_ids: tuple[str, ...]
    matched: bool


def _format_entry(match: KBMatch, *, lang: Lang) -> str:
    entry = match.entry
    is_vi = lang == Lang.VI
    title = entry.title_vi if is_vi else entry.title_en
    cause = entry.cause_vi if is_vi else entry.cause_en
    steps = entry.fix_steps_vi if is_vi else entry.fix_steps_en
    rollback = entry.rollback_vi if is_vi else entry.rollback_en

    lines = [f"## {title}", "", t("assistant.engine.offline.cause_label", lang=lang, cause=cause)]
    if steps:
        lines.append("")
        lines.append(t("assistant.engine.offline.steps_label", lang=lang))
        for index, step in enumerate(steps, start=1):
            lines.append(f"{index}. {step}")
    if rollback:
        lines.append("")
        lines.append(t("assistant.engine.offline.rollback_label", lang=lang, rollback=rollback))
    return "\n".join(lines)


class OfflineKbBackend:
    """Tra ``KnowledgeBase`` theo văn bản người dùng, hoàn toàn offline."""

    def __init__(self, kb: KnowledgeBase | None = None) -> None:
        self._kb = kb if kb is not None else KnowledgeBase.load_default()

    @property
    def knowledge_base(self) -> KnowledgeBase:
        return self._kb

    def answer(self, text: str, *, lang: Lang | str | None = None) -> OfflineAnswer:
        """KHÔNG BAO GIỜ raise: lỗi phân loại/tra cứu bất ngờ rơi về một câu
        trả lời chung chung thay vì làm sập luồng hỏi-đáp (fail-safe, cùng
        nguyên tắc ``apply_runtime_desktop_settings`` ở ``namios_welcome``)."""

        resolved = resolve_lang(lang)
        try:
            subsystem = classify_subsystem(text)
            matches = self._kb.find_matches(text, subsystem_hint=subsystem, limit=2)
        except Exception:  # noqa: BLE001 - fail-safe tuyệt đối, xem docstring
            fallback = t("assistant.engine.offline.unexpected_error", lang=resolved)
            return OfflineAnswer(text=fallback, subsystem=None, kb_match_ids=(), matched=False)

        if not matches:
            fallback = t("assistant.engine.offline.no_match", lang=resolved)
            return OfflineAnswer(text=fallback, subsystem=subsystem, kb_match_ids=(), matched=False)

        body = "\n\n---\n\n".join(_format_entry(match, lang=resolved) for match in matches)
        match_ids = tuple(match.entry.id for match in matches)
        return OfflineAnswer(text=body, subsystem=subsystem, kb_match_ids=match_ids, matched=True)
