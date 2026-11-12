"""``namios_assistant.engine`` — lớp lõi KHÔNG phụ thuộc GUI của NaMiOS Assistant.

Tách khỏi ``namios_assistant.ui`` (PySide6) để test/dùng được mà không cần
desktop/display (giống quy ước ``namios_welcome.firstrun``/``migrate``).

Luồng xử lý một câu hỏi của người dùng (xem ``backend.AssistantEngine.ask``):

    text (đã dán lỗi, hoặc đã OCR từ ảnh)
      -> classify.classify_subsystem()            # đoán mảng: mạng/in/wine/...
      -> app_catalog.resolve_catalog_lookup()      # ý định cài app/driver? (nếu có)
      -> offline_backend.OfflineKbBackend.answer() # LUÔN chạy trước, không cần mạng
      -> (nếu có cấu hình, VÀ không phải ý định cài đặt/driver)
         online_backend.OnlineLlmBackend.ask()
         thành công -> dùng câu trả lời online (nêu rõ tên model)
         lỗi/không cấu hình -> dùng câu trả lời offline đã có sẵn, KHÔNG bịa

``AssistantEngine.ask`` không bao giờ raise ra ngoài — luôn trả về
``AssistantAnswer`` đã gắn nhãn rõ ``source`` (``"offline_kb"``/``"online_llm"``)
để UI hiển thị trung thực, không bao giờ giả vờ là AI khi thực chất là KB.

``app_catalog``/``installer`` (App & Driver Concierge, thêm 11/11/2026): tra
"tôi muốn cài X"/"máy in Y không nhận driver" vào hai catalog TĨNH đã kiểm
duyệt (``data/software_catalog.json``/``data/driver_catalog.json``) — CHỈ
trả về entry có thật trong catalog, KHÔNG BAO GIỜ tự bịa URL/tên gói (xem
docstring ``engine/app_catalog.py``). ``installer.install_package``/
``installer.install_deb_from_url`` là NƠI DUY NHẤT trong gói này được phép
thay đổi hệ thống (pkexec + argv tĩnh; ``install_deb_from_url`` thêm domain
pin + xác minh magic bytes trước khi cài — xem docstring
``engine/installer.py``).

Thêm 12/11/2026: ``method == "deb_official"`` giờ map sang
``action_kind == "deb_install"`` (tự tải+cài, không chỉ mở trang — xem
``install_deb_from_url``); ``method == "pack"`` ("Dev Pack") map sang
``action_kind == "pack_install"`` và mang theo ``InstallPlan.members`` —
một danh sách ``InstallPlan`` con, mỗi cái cài theo ĐÚNG phương thức riêng
của nó."""

from __future__ import annotations

from namios_assistant.engine.app_catalog import (
    ActionKind,
    CatalogLookup,
    InstallPlan,
    all_apps,
    all_drivers,
    build_install_plan_for_app,
    build_install_plan_for_driver,
    resolve_app,
    resolve_catalog_lookup,
    resolve_driver,
)
from namios_assistant.engine.backend import AssistantAnswer, AssistantEngine
from namios_assistant.engine.classify import (
    SUBSYSTEM_DISPLAY_NAMES,
    SUBSYSTEM_KEYWORDS,
    CatalogIntent,
    classify_catalog_intent,
    classify_subsystem,
    subsystem_display_name,
)
from namios_assistant.engine.installer import (
    InstallResult,
    install_deb_from_url,
    install_package,
    is_official_https_url,
)
from namios_assistant.engine.knowledge_base import KBEntry, KBMatch, KnowledgeBase
from namios_assistant.engine.ocr import OcrResult, ocr_image
from namios_assistant.engine.offline_backend import OfflineAnswer, OfflineKbBackend
from namios_assistant.engine.online_backend import OnlineBackendError, OnlineLlmBackend
from namios_assistant.engine.related_tools import RelatedTool, resolve_related_tools
from namios_assistant.engine.suggestions import STARTER_SUGGESTION_IDS, starter_suggestions

__all__ = [
    "AssistantAnswer",
    "AssistantEngine",
    "classify_subsystem",
    "subsystem_display_name",
    "SUBSYSTEM_KEYWORDS",
    "SUBSYSTEM_DISPLAY_NAMES",
    "CatalogIntent",
    "classify_catalog_intent",
    "ActionKind",
    "InstallPlan",
    "CatalogLookup",
    "resolve_app",
    "resolve_driver",
    "build_install_plan_for_app",
    "build_install_plan_for_driver",
    "resolve_catalog_lookup",
    "all_apps",
    "all_drivers",
    "InstallResult",
    "install_package",
    "install_deb_from_url",
    "is_official_https_url",
    "KBEntry",
    "KBMatch",
    "KnowledgeBase",
    "OfflineAnswer",
    "OfflineKbBackend",
    "OnlineBackendError",
    "OnlineLlmBackend",
    "OcrResult",
    "ocr_image",
    "RelatedTool",
    "resolve_related_tools",
    "STARTER_SUGGESTION_IDS",
    "starter_suggestions",
]
