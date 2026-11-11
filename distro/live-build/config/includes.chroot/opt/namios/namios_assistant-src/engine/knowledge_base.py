"""KB ngoại tuyến (offline knowledge base) — lỗi thường gặp -> nguyên nhân ->
cách sửa, cho NaMiOS Assistant. Chạy HOÀN TOÀN không cần mạng.

Nguồn dữ liệu: file JSON tĩnh (``kb/starter_kb.json`` đóng gói cùng module,
hoặc một bộ KB khác do operator/package sau này cung cấp qua đường dẫn
``/usr/share/namios/assistant/kb/*.json`` — xem ``KnowledgeBase.load_default``).
Mỗi entry là DỮ LIỆU thuần (title/cause/fix/rollback) có cặp field ``_vi``/
``_en`` song song (cùng quy ước ``message_vi``/``reason_vi`` dùng ở
``namios_welcome``/``namios_eco`` — dữ liệu nội dung, KHÔNG đi qua
``namios_i18n.t()``), không phải chuỗi UI chrome.

File KB hỏng/thiếu field KHÔNG được làm sập app: entry lỗi bị BỎ QUA (skip),
không phải toàn bộ KB rỗng vì một entry sai cú pháp.

Đợt nâng cấp 11/11/2026 (Wave "chatbot mạnh hơn") thêm HAI field tuỳ chọn,
giữ 100% tương thích ngược với KB cũ (entry thiếu field này vẫn parse đúng
như trước):

- ``kind`` (``"error"`` mặc định, hoặc ``"howto"``): phân biệt entry CHẨN
  ĐOÁN LỖI (có "nguyên nhân có khả năng") với entry HƯỚNG DẪN TÁC VỤ ("làm
  sao làm X") — hai hình dạng câu trả lời khác nhau, xem cách dùng ở
  ``engine/offline_backend.py::_format_entry``. Giá trị lạ/thiếu -> coi là
  ``"error"`` (an toàn, không làm hỏng việc hiển thị).
- ``related_tool_id`` (``str | None``): id tra trong
  ``engine/related_tools.py::RELATED_TOOLS`` — công cụ NaMiOS thật nên gợi ý
  mở cho đúng entry này. KHÔNG validate ở đây (tránh ``knowledge_base.py``
  phải biết về registry công cụ) — id lạ chỉ đơn giản không resolve được gì ở
  tầng ``related_tools``, KHÔNG làm hỏng việc parse entry."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["KBEntry", "KBMatch", "KnowledgeBase", "KB_SEARCH_PATHS", "KB_ENTRY_KINDS"]

#: Giá trị hợp lệ cho ``KBEntry.kind`` — xem docstring module.
KB_ENTRY_KINDS: frozenset[str] = frozenset({"error", "howto"})
_DEFAULT_ENTRY_KIND = "error"

#: Thư mục KB đã cài đặt (vd operator/package khác muốn bổ sung bộ KB riêng
#: không cần sửa mã nguồn) — quét TRƯỚC bộ KB mặc định đóng gói cùng module.
#: Thư mục không tồn tại (ảnh build chưa cài gì ở đây) -> bỏ qua êm, dùng
#: starter KB đóng gói cùng ``namios_assistant`` làm nguồn duy nhất.
KB_SEARCH_PATHS: tuple[Path, ...] = (Path("/usr/share/namios/assistant/kb"),)

#: KB đóng gói CÙNG module (luôn có mặt, không phụ thuộc cài đặt gì thêm) —
#: dùng làm fallback cuối cùng + nguồn cho môi trường dev/test không chạy
#: trong ảnh NaMiOS đã build.
_BUNDLED_KB_PATH = Path(__file__).resolve().parent.parent / "kb" / "starter_kb.json"

_REQUIRED_STR_FIELDS = (
    "id",
    "subsystem",
    "title_vi",
    "title_en",
    "cause_vi",
    "cause_en",
)


@dataclass(frozen=True)
class KBEntry:
    """Một mục KB: lỗi -> nguyên nhân -> cách sửa (song ngữ)."""

    id: str
    subsystem: str
    keywords_vi: tuple[str, ...]
    keywords_en: tuple[str, ...]
    patterns: tuple[str, ...]
    title_vi: str
    title_en: str
    cause_vi: str
    cause_en: str
    fix_steps_vi: tuple[str, ...]
    fix_steps_en: tuple[str, ...]
    rollback_vi: str | None
    rollback_en: str | None
    kind: str = _DEFAULT_ENTRY_KIND
    related_tool_id: str | None = None

    def compiled_patterns(self) -> tuple[re.Pattern[str], ...]:
        """Biên dịch ``patterns`` (regex) — gọi mỗi lần match thay vì cache
        trên ``frozen dataclass`` để giữ entry bất biến/dễ test; chi phí nhỏ
        (KB khởi điểm vài chục entry, không phải hot loop)."""

        compiled: list[re.Pattern[str]] = []
        for raw in self.patterns:
            try:
                compiled.append(re.compile(raw, re.IGNORECASE))
            except re.error:
                # Regex hỏng trong 1 entry KHÔNG được làm cả entry/toàn KB
                # mất tác dụng — bỏ qua riêng pattern đó, giữ keyword match.
                continue
        return tuple(compiled)


@dataclass(frozen=True)
class KBMatch:
    """Một entry KB khớp với văn bản người dùng, kèm điểm xếp hạng."""

    entry: KBEntry
    score: int


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _as_optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _as_entry_kind(value: Any) -> str:
    """Trả ``"howto"`` CHỈ KHI khai báo đúng chữ, mọi giá trị khác (thiếu/
    sai kiểu/chuỗi lạ) rơi về ``"error"`` — KHÔNG raise, một ``kind`` lạ
    không được làm hỏng việc parse cả entry (xem docstring module)."""

    if isinstance(value, str) and value.strip() in KB_ENTRY_KINDS:
        return value.strip()
    return _DEFAULT_ENTRY_KIND


def _parse_entry(raw: Any) -> KBEntry | None:
    """Parse MỘT entry thô (``dict`` từ JSON) thành ``KBEntry``. Trả ``None``
    (bỏ qua entry) nếu thiếu field bắt buộc hoặc sai kiểu — KHÔNG raise, để
    một entry hỏng không làm mất toàn bộ KB (xem docstring module)."""

    if not isinstance(raw, dict):
        return None
    for field_name in _REQUIRED_STR_FIELDS:
        if not isinstance(raw.get(field_name), str) or not raw[field_name].strip():
            return None
    try:
        return KBEntry(
            id=raw["id"],
            subsystem=raw["subsystem"],
            keywords_vi=_as_str_tuple(raw.get("keywords_vi")),
            keywords_en=_as_str_tuple(raw.get("keywords_en")),
            patterns=_as_str_tuple(raw.get("patterns")),
            title_vi=raw["title_vi"],
            title_en=raw["title_en"],
            cause_vi=raw["cause_vi"],
            cause_en=raw["cause_en"],
            fix_steps_vi=_as_str_tuple(raw.get("fix_steps_vi")),
            fix_steps_en=_as_str_tuple(raw.get("fix_steps_en")),
            rollback_vi=_as_optional_str(raw.get("rollback_vi")),
            rollback_en=_as_optional_str(raw.get("rollback_en")),
            kind=_as_entry_kind(raw.get("kind")),
            related_tool_id=_as_optional_str(raw.get("related_tool_id")),
        )
    except (KeyError, TypeError):
        return None


def _load_entries_from_file(path: Path) -> tuple[KBEntry, ...]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return ()
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, dict):
        return ()
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        return ()

    parsed: list[KBEntry] = []
    for raw_entry in raw_entries:
        entry = _parse_entry(raw_entry)
        if entry is not None:
            parsed.append(entry)
    return tuple(parsed)


class KnowledgeBase:
    """Tập hợp các ``KBEntry`` đã nạp + logic tìm/xếp hạng theo văn bản."""

    def __init__(self, entries: Sequence[KBEntry]) -> None:
        self._entries: tuple[KBEntry, ...] = tuple(entries)

    @property
    def entries(self) -> tuple[KBEntry, ...]:
        return self._entries

    @classmethod
    def load_default(cls) -> "KnowledgeBase":
        """Nạp KB theo thứ tự ưu tiên: mọi file ``*.json`` hợp lệ dưới
        ``KB_SEARCH_PATHS`` (gộp lại, cho phép bổ sung KB mà không cần sửa
        mã nguồn) CỘNG THÊM KB đóng gói cùng module (``kb/starter_kb.json``)
        — luôn có mặt, kể cả khi chưa cài gì ở ``/usr/share/namios/assistant/
        kb``. Trùng ``id`` giữa các nguồn: giữ bản nạp ĐẦU TIÊN (KB cài đặt
        riêng ưu tiên hơn starter KB đóng gói, cho phép ghi đè/bổ sung)."""

        seen_ids: set[str] = set()
        merged: list[KBEntry] = []

        search_files: list[Path] = []
        for directory in KB_SEARCH_PATHS:
            if directory.is_dir():
                search_files.extend(sorted(directory.glob("*.json")))
        search_files.append(_BUNDLED_KB_PATH)

        for path in search_files:
            for entry in _load_entries_from_file(path):
                if entry.id in seen_ids:
                    continue
                seen_ids.add(entry.id)
                merged.append(entry)

        return cls(merged)

    def all_subsystems(self) -> frozenset[str]:
        return frozenset(entry.subsystem for entry in self._entries)

    def find_matches(
        self,
        text: str,
        *,
        subsystem_hint: str | None = None,
        limit: int = 3,
    ) -> tuple[KBMatch, ...]:
        """Xếp hạng entry theo mức khớp với ``text`` (so khớp không phân
        biệt hoa/thường). Điểm = số từ khoá khớp (substring, trọng số 1) +
        số regex ``patterns`` khớp (trọng số 3 — pattern cụ thể hơn từ khoá
        đơn) + 2 nếu ``entry.subsystem == subsystem_hint``. Entry điểm 0 bị
        loại (không trả kết quả "khớp" giả khi thực ra không liên quan gì)."""

        if not text:
            return ()
        lowered = text.lower()

        scored: list[KBMatch] = []
        for entry in self._entries:
            score = 0
            for keyword in (*entry.keywords_vi, *entry.keywords_en):
                if keyword and keyword.lower() in lowered:
                    score += 1
            for pattern in entry.compiled_patterns():
                if pattern.search(text):
                    score += 3
            if subsystem_hint is not None and entry.subsystem == subsystem_hint:
                score += 2
            if score > 0:
                scored.append(KBMatch(entry=entry, score=score))

        scored.sort(key=lambda match: match.score, reverse=True)
        return tuple(scored[: max(limit, 0)])
