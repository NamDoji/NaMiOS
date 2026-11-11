"""Gợi ý khởi đầu ("starter suggestions") cho cửa sổ chat — vài câu hỏi mẫu
người dùng mới có thể bấm thay vì phải tự nghĩ ra câu hỏi đầu tiên (mục 4 "Chat
UX polish" của yêu cầu nâng cấp 11/11/2026).

NGUYÊN TẮC CHỐNG BỊA: câu gợi ý KHÔNG được tự soạn mới ở module này — lấy
NGUYÊN VĂN ``title_vi``/``title_en`` của một số entry ``kind="howto"`` đã có
thật trong KB (xem ``kb/starter_kb.json``), để nội dung gợi ý luôn khớp với
một câu trả lời KB thật sự tồn tại. Nếu một id trong ``STARTER_SUGGESTION_IDS``
không có trong KB đang nạp (vd operator thay bằng bộ KB riêng không có entry
đó) thì BỎ QUA ÊM id đó, không báo lỗi, không bịa thêm câu khác để lấp chỗ
trống — gợi ý ít hơn vẫn tốt hơn gợi ý sai."""

from __future__ import annotations

from namios_assistant.engine.knowledge_base import KnowledgeBase
from namios_i18n import Lang

__all__ = ["STARTER_SUGGESTION_IDS", "starter_suggestions"]

#: Id các entry "howto" chọn làm gợi ý khởi đầu — trải đều nhiều mảng hệ
#: thống hay gặp nhất (mạng/bộ gõ/in/máy chiếu/cập nhật/gỡ phần mềm) để người
#: dùng mới thấy ngay phạm vi Trợ lý có thể giúp, không chỉ "sửa lỗi".
STARTER_SUGGESTION_IDS: tuple[str, ...] = (
    "HOWTO-WIFI-CONNECT",
    "HOWTO-IME-SWITCH",
    "HOWTO-PRINTER-ADD",
    "HOWTO-PROJECTOR-CONNECT",
    "HOWTO-APP-UNINSTALL",
    "HOWTO-UPDATE-RUN",
)


def starter_suggestions(
    kb: KnowledgeBase, *, lang: Lang | str = Lang.VI, limit: int = 6
) -> tuple[str, ...]:
    """Trả về tối đa ``limit`` câu gợi ý (tiêu đề entry thật), theo đúng thứ
    tự ``STARTER_SUGGESTION_IDS``. ``limit <= 0`` -> rỗng (không phải lỗi, chỉ
    là caller không muốn gợi ý nào)."""

    if limit <= 0:
        return ()

    is_vi = lang == Lang.VI or str(lang).lower() == "vi"
    by_id = {entry.id: entry for entry in kb.entries}

    result: list[str] = []
    for suggestion_id in STARTER_SUGGESTION_IDS:
        entry = by_id.get(suggestion_id)
        if entry is None:
            continue
        result.append(entry.title_vi if is_vi else entry.title_en)
        if len(result) >= limit:
            break
    return tuple(result)
