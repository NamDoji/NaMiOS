"""Backend NGOẠI TUYẾN (offline KB) — luôn chạy được, không cần mạng, không
cần cấu hình gì (xem ``docs/SMARTAI-ASSISTANT.md`` cho "sự thật ship offline
vs cần khoá"). Đây là đường trả lời MẶC ĐỊNH; ``AssistantEngine`` chỉ thay
bằng kết quả online khi backend online được cấu hình VÀ gọi thành công.

Đợt nâng cấp 11/11/2026 ("chatbot mạnh hơn, khác biệt") thêm 3 việc vào
``answer()``/``_format_entry()`` so với bản gốc:

1. **Tách "đã phát hiện" khỏi "có thể do"** (honest UX): dòng "Đã phát hiện"
   báo sự THẬT khách quan (mảng hệ thống đoán được từ từ khoá/mẫu khớp trong
   chính văn bản người dùng gửi) — khác hẳn "Có thể do" (``cause_vi``/
   ``cause_en`` của entry KB, một GIẢ THUYẾT biên soạn trước, không chắc đúng
   100% cho mọi ca). Gộp chung hai thứ này từng là điểm mơ hồ nhất của bản
   gốc: người dùng không phân biệt được đâu là Trợ lý "biết chắc" và đâu là
   "đoán theo kinh nghiệm".
2. **Entry hai HÌNH DẠNG** (``kind="error"`` vs ``"howto"``) dùng nhãn khác
   nhau (xem ``KBEntry.kind``) — "howto" không có khái niệm "nguyên nhân",
   chỉ có mô tả ngắn + các bước + lưu ý.
3. **Mã tham khảo + công cụ liên quan**: mỗi entry hiển thị ``id`` dạng code
   (copy được, dùng khi cần báo lỗi/tìm thêm) và — nếu có — tên công cụ
   NaMiOS thật nên mở (``engine/related_tools.py``); UI (``ui.py``) dùng
   ``OfflineAnswer.related_tools`` để vẽ nút bấm thật, dòng text ở đây chỉ là
   bản ghi-chú-được (đọc được cả khi copy text thuần/đọc màn hình)."""

from __future__ import annotations

from dataclasses import dataclass

from namios_assistant.engine.classify import classify_subsystem, subsystem_display_name
from namios_assistant.engine.knowledge_base import KBMatch, KnowledgeBase
from namios_assistant.engine.related_tools import (
    RelatedTool,
    resolve_related_tool_for_subsystem,
    resolve_related_tools,
)
from namios_i18n import Lang, resolve_lang, t

__all__ = ["OfflineAnswer", "OfflineKbBackend"]


@dataclass(frozen=True)
class OfflineAnswer:
    """Kết quả một lần tra KB ngoại tuyến."""

    text: str
    subsystem: str | None
    kb_match_ids: tuple[str, ...]
    matched: bool
    related_tools: tuple[RelatedTool, ...] = ()


def _format_entry(match: KBMatch, *, lang: Lang) -> str:
    entry = match.entry
    is_vi = lang == Lang.VI
    title = entry.title_vi if is_vi else entry.title_en
    cause = entry.cause_vi if is_vi else entry.cause_en
    steps = entry.fix_steps_vi if is_vi else entry.fix_steps_en
    rollback = entry.rollback_vi if is_vi else entry.rollback_en
    is_howto = entry.kind == "howto"

    lines = [f"## {title}", ""]

    if is_howto:
        lines.append(t("assistant.engine.offline.howto_intro_label", lang=lang, cause=cause))
    else:
        lines.append(t("assistant.engine.offline.cause_label", lang=lang, cause=cause))

    if steps:
        lines.append("")
        steps_key = (
            "assistant.engine.offline.howto_steps_label"
            if is_howto
            else "assistant.engine.offline.steps_label"
        )
        lines.append(t(steps_key, lang=lang))
        for index, step in enumerate(steps, start=1):
            lines.append(f"{index}. {step}")

    if rollback:
        lines.append("")
        rollback_key = (
            "assistant.engine.offline.howto_note_label"
            if is_howto
            else "assistant.engine.offline.rollback_label"
        )
        lines.append(t(rollback_key, lang=lang, rollback=rollback))

    lines.append("")
    lines.append(t("assistant.engine.offline.ref_code_label", lang=lang, ref_id=entry.id))

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
            # Không khớp entry nào KHÔNG có nghĩa là không nói được gì: nếu
            # phân loại được mảng hệ thống, nói rõ điều ĐÃ phát hiện được +
            # (nếu có) vẫn gợi ý mở đúng công cụ liên quan tới mảng đó — hữu
            # ích hơn một câu "không tìm thấy" chung chung, mà vẫn trung thực
            # (không bịa thêm bước sửa nào không có trong KB).
            display_name = subsystem_display_name(subsystem, lang_vi=resolved == Lang.VI)
            if display_name is not None:
                fallback = t(
                    "assistant.engine.offline.no_match_with_subsystem",
                    lang=resolved,
                    subsystem=display_name,
                )
            else:
                fallback = t("assistant.engine.offline.no_match", lang=resolved)
            related = (
                (resolve_related_tool_for_subsystem(subsystem),)
                if resolve_related_tool_for_subsystem(subsystem) is not None
                else ()
            )
            return OfflineAnswer(
                text=fallback,
                subsystem=subsystem,
                kb_match_ids=(),
                matched=False,
                related_tools=related,
            )

        entries_body = "\n\n---\n\n".join(_format_entry(match, lang=resolved) for match in matches)
        display_name = subsystem_display_name(subsystem, lang_vi=resolved == Lang.VI)
        if display_name is not None:
            detected_line = t(
                "assistant.engine.offline.detected_subsystem",
                lang=resolved,
                subsystem=display_name,
            )
            body = f"{detected_line}\n\n{entries_body}"
        else:
            body = entries_body
        match_ids = tuple(match.entry.id for match in matches)
        related_tools = resolve_related_tools(
            [match.entry for match in matches], subsystem_hint=subsystem
        )
        return OfflineAnswer(
            text=body,
            subsystem=subsystem,
            kb_match_ids=match_ids,
            matched=True,
            related_tools=related_tools,
        )
