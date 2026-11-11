"""``namios_assistant`` — NaMiOS Assistant: chatbot ĐỌC/GIẢI THÍCH lỗi cho
người dùng cuối (khác với ``namios_smartai`` — engine điều phối tác vụ có
quyền thay đổi hệ thống qua Tool Broker, xem ``docs/adr/ADR-0018``/``0021``.
Module NÀY không bao giờ tự thực thi hành động hệ thống nào).

Người dùng dán một thông báo lỗi (hoặc ảnh chụp màn hình, OCR qua
``engine.ocr``) — ``engine.backend.AssistantEngine`` phân loại về một MẢNG hệ
thống (``engine.classify``), tra KB ngoại tuyến (``engine.knowledge_base`` +
``kb/starter_kb.json``, luôn chạy được không cần mạng), và NẾU đã cấu hình
đủ ``api_key``/``model``/``base_url`` (``config.load_config``) thì thử gọi
thêm một model AI trực tuyến (``engine.online_backend``) — lỗi/thiếu cấu
hình ở backend online LUÔN rơi về KB ngoại tuyến, KHÔNG BAO GIỜ làm sập app.

``ui`` (PySide6) + ``__main__`` CHỈ chạy trên desktop session thật có display
— tách khỏi ``engine``/``config`` (Python thuần, test được không cần GUI),
cùng quy ước ``namios_welcome``."""

from __future__ import annotations

from namios_assistant import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_assistant.config import AssistantConfig, load_config
from namios_assistant.engine import AssistantAnswer, AssistantEngine

__all__ = [
    "AssistantConfig",
    "load_config",
    "AssistantAnswer",
    "AssistantEngine",
]
