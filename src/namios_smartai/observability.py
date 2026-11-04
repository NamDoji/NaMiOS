"""Observability — trace cấu trúc (SAI-034).

Mỗi mốc là ``TraceEvent`` chỉ gồm ID + nhãn + kết quả (plan/action/policy/tool/
evidence/correlation) — KHÔNG lưu prompt/nội dung tài liệu/credential mặc định.
``Trace.record`` redact trường ``note`` (phòng thủ). Phân biệt rõ NGUỒN lỗi
(model/policy/tool/vendor/portal) để người dùng/admin hiểu lý do gate từ chối.

Nghiệm thu SAI-034: phân biệt được 5 nguồn lỗi; không lộ credentials trong trace.
"""

from __future__ import annotations

import re
from dataclasses import replace

from namios_smartai._types import TraceErrorClass, TraceEvent
from namios_smartai.redaction import scrub_all

__all__ = ["Trace", "classify_error_source"]

#: Từ khoá → nguồn lỗi (SAI-034). Cụ thể trước chung.
_ERROR_SIGNALS: tuple[tuple[TraceErrorClass, tuple[str, ...]], ...] = (
    (TraceErrorClass.POLICY, ("policy", "deny", "consent", "capability", "risk")),
    (TraceErrorClass.TOOL, ("tool", "schema", "fail-closed", "scope", "unknown tool")),
    (TraceErrorClass.VENDOR, ("vendor", "sdk", "driver", "signing adapter")),
    (TraceErrorClass.PORTAL, ("portal", "plugin", "activex", "webview2")),
    (TraceErrorClass.MODEL, ("model", "json", "hallucinat", "provider", "timeout model")),
)

#: Khớp theo RANH GIỚI TỪ (``\b``), KHÔNG phải chuỗi-con — tránh "brisket"
#: khớp "risk" hay "horoscope" khớp "scope" làm sai nguồn lỗi (QA cross-cutting).
_ERROR_PATTERNS: tuple[tuple[TraceErrorClass, re.Pattern[str]], ...] = tuple(
    (
        klass,
        re.compile(r"\b(?:" + "|".join(re.escape(n) for n in needles) + r")\b", re.IGNORECASE),
    )
    for klass, needles in _ERROR_SIGNALS
)


def classify_error_source(signal: str) -> TraceErrorClass:
    """Phân loại nguồn lỗi tất định từ một tín hiệu ngắn, khớp theo RANH GIỚI
    TỪ. Không khớp → UNKNOWN (không đoán)."""

    if not (signal or "").strip():
        return TraceErrorClass.NONE
    for klass, pattern in _ERROR_PATTERNS:
        if pattern.search(signal):
            return klass
    return TraceErrorClass.UNKNOWN


class Trace:
    """Bộ ghi trace trong-bộ-nhớ. ``note`` mọi event được redact khi ghi — trace
    KHÔNG bao giờ chứa credential."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    def record(self, event: TraceEvent) -> None:
        self._events.append(replace(event, note=scrub_all(event.note)))

    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def reject_reasons(self) -> tuple[tuple[str, str, str], ...]:
        """Các mốc bị gate từ chối (``policy_decision == 'deny'``) → (action_id,
        error_class, note đã redact) để người dùng/admin xem lý do."""

        return tuple(
            (e.action_id, e.error_class.value, e.note)
            for e in self._events
            if e.policy_decision == "deny"
        )
