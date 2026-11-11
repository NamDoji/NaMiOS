"""``namios_assistant.engine`` — lớp lõi KHÔNG phụ thuộc GUI của NaMiOS Assistant.

Tách khỏi ``namios_assistant.ui`` (PySide6) để test/dùng được mà không cần
desktop/display (giống quy ước ``namios_welcome.firstrun``/``migrate``).

Luồng xử lý một câu hỏi của người dùng (xem ``backend.AssistantEngine.ask``):

    text (đã dán lỗi, hoặc đã OCR từ ảnh)
      -> classify.classify_subsystem()            # đoán mảng: mạng/in/wine/...
      -> offline_backend.OfflineKbBackend.answer() # LUÔN chạy trước, không cần mạng
      -> (nếu có cấu hình) online_backend.OnlineLlmBackend.ask()
         thành công -> dùng câu trả lời online (nêu rõ tên model)
         lỗi/không cấu hình -> dùng câu trả lời offline đã có sẵn, KHÔNG bịa

``AssistantEngine.ask`` không bao giờ raise ra ngoài — luôn trả về
``AssistantAnswer`` đã gắn nhãn rõ ``source`` (``"offline_kb"``/``"online_llm"``)
để UI hiển thị trung thực, không bao giờ giả vờ là AI khi thực chất là KB.
"""

from __future__ import annotations

from namios_assistant.engine.backend import AssistantAnswer, AssistantEngine
from namios_assistant.engine.classify import SUBSYSTEM_KEYWORDS, classify_subsystem
from namios_assistant.engine.knowledge_base import KBEntry, KBMatch, KnowledgeBase
from namios_assistant.engine.ocr import OcrResult, ocr_image
from namios_assistant.engine.offline_backend import OfflineAnswer, OfflineKbBackend
from namios_assistant.engine.online_backend import OnlineBackendError, OnlineLlmBackend

__all__ = [
    "AssistantAnswer",
    "AssistantEngine",
    "classify_subsystem",
    "SUBSYSTEM_KEYWORDS",
    "KBEntry",
    "KBMatch",
    "KnowledgeBase",
    "OfflineAnswer",
    "OfflineKbBackend",
    "OnlineBackendError",
    "OnlineLlmBackend",
    "OcrResult",
    "ocr_image",
]
