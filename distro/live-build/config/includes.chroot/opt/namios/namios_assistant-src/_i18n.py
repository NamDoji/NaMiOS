"""Catalog song ngữ riêng của ``namios_assistant`` — đăng ký qua
``namios_i18n.add_catalog`` khi import (đúng quy ước các module khác, xem
vd ``namios_essentials/_i18n.py``). KHÔNG sửa trực tiếp ``namios_i18n/locale/
{vi,en}.json`` (sở hữu bởi ``namios_i18n`` — xem docstring
``namios_i18n.translator.Translator.add_catalog``).

Nhóm key:
  - ``assistant.engine.*``  : chuỗi do lớp ``engine`` sinh ra (nhãn nguồn/
    bước sửa/hoàn tác, nối vào nội dung KB — xem ``engine/offline_backend.py``,
    ``engine/backend.py``).
  - ``assistant.ui.*``       : chrome giao diện PySide6 (``ui.py``).

Dữ liệu NỘI DUNG KB (tiêu đề/nguyên nhân/bước sửa của từng lỗi cụ thể) nằm
trong ``kb/starter_kb.json`` dạng field ``_vi``/``_en`` song song — KHÔNG đi
qua lớp dịch này (cùng quy ước ``message_vi``/``reason_vi`` dùng ở nơi khác
trong repo: dữ liệu nội dung khác với chrome UI)."""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # --- engine: nhãn ghép vào nội dung câu trả lời KB ngoại tuyến ---
    "assistant.engine.offline.detected_subsystem": (
        "**Đã phát hiện:** nội dung bạn gửi liên quan tới mảng *{subsystem}* "
        "(dựa trên từ khoá/mẫu khớp trong chính văn bản — một phép đoán đơn "
        "giản, không phải chẩn đoán chắc chắn)."
    ),
    "assistant.engine.offline.cause_label": "**Có thể do:** {cause}",
    "assistant.engine.offline.steps_label": "**Các bước thử:**",
    "assistant.engine.offline.rollback_label": "**Hoàn tác/an toàn:** {rollback}",
    "assistant.engine.offline.howto_intro_label": "{cause}",
    "assistant.engine.offline.howto_steps_label": "**Các bước:**",
    "assistant.engine.offline.howto_note_label": "**Lưu ý:** {rollback}",
    "assistant.engine.offline.ref_code_label": "**Mã tham khảo:** `{ref_id}`",
    "assistant.engine.offline.no_match": (
        "Chưa tìm thấy hướng dẫn phù hợp trong KB ngoại tuyến cho nội dung này. "
        "Hãy thử: (1) dán NGUYÊN VĂN dòng thông báo lỗi (không tóm tắt lại), "
        "(2) nói rõ việc gì đang làm thì lỗi xảy ra, hoặc (3) nếu có cấu hình "
        "AI trực tuyến, bật nó lên để được giải thích sâu hơn. Đây KHÔNG phải "
        "câu trả lời từ AI — chỉ là KB ngoại tuyến chưa có ca khớp."
    ),
    "assistant.engine.offline.no_match_with_subsystem": (
        "**Đã phát hiện:** nội dung liên quan tới mảng *{subsystem}*, nhưng "
        "KB ngoại tuyến CHƯA có hướng dẫn cụ thể khớp đúng ca này — Trợ lý "
        "không bịa thêm bước sửa khi chưa chắc. Hãy thử mô tả chi tiết hơn "
        "(dán nguyên văn thông báo lỗi nếu có), hoặc mở công cụ liên quan bên "
        "dưới (nếu có) để xem trực tiếp, hoặc bật cấu hình AI trực tuyến nếu "
        "cần giải thích sâu hơn."
    ),
    "assistant.engine.offline.unexpected_error": (
        "Có lỗi nội bộ khi tra cứu KB ngoại tuyến — không liên quan tới máy "
        "của bạn. Hãy thử lại, hoặc mô tả lỗi theo cách khác."
    ),
    "assistant.engine.note.offline_kb": (
        "Trả lời từ KB ngoại tuyến (không cần mạng) — KHÔNG phải mô hình AI."
    ),
    "assistant.engine.note.online_llm": "Trả lời từ model AI trực tuyến ({model}).",
    "assistant.engine.note.online_fallback": (
        "Backend AI trực tuyến không trả lời được ({reason}) — đang hiển thị "
        "KB ngoại tuyến thay thế."
    ),
    # --- engine: App & Driver Concierge (catalog cài đặt/driver đã kiểm duyệt) ---
    "assistant.engine.catalog.found_app": (
        "Đã tìm thấy trong kho đã kiểm duyệt của NaMi: **{title}**. Xem "
        "phương án cài đặt bên dưới."
    ),
    "assistant.engine.catalog.found_driver": (
        "Đã tìm thấy trong kho đã kiểm duyệt của NaMi: **{title}**. Xem "
        "phương án driver bên dưới."
    ),
    "assistant.engine.catalog.no_match": (
        "Chưa có trong kho đã kiểm duyệt của NaMi cho yêu cầu này. Trợ lý "
        "KHÔNG tự đoán một đường link tải để tránh rủi ro — hãy thử mở nStore "
        "(Trung tâm phần mềm) hoặc tìm trong Cài đặt → Ứng dụng."
    ),
    # --- ui: chrome giao diện ---
    "assistant.ui.window_title": "Trợ lý",
    "assistant.ui.header.title": "Trợ lý",
    "assistant.ui.header.subtitle": (
        "Dán thông báo lỗi hoặc ảnh chụp màn hình — nhận hướng dẫn phân loại "
        "theo mảng hệ thống (mạng/máy in/wine/văn phòng/màn hình/…)."
    ),
    "assistant.ui.status.offline_only": (
        "Chế độ: KB ngoại tuyến (không cần mạng). Chưa cấu hình model AI trực tuyến."
    ),
    "assistant.ui.status.online_configured": (
        "Chế độ: Model AI trực tuyến ({model}) + KB ngoại tuyến dự phòng nếu model lỗi."
    ),
    "assistant.ui.footer.disclaimer": (
        "Trợ lý này chỉ ĐỌC/GIẢI THÍCH — không tự thay đổi cấu hình hay cài/gỡ "
        "gì trên máy bạn."
    ),
    "assistant.ui.greeting": (
        "Chào bạn! Dán một thông báo lỗi, đính kèm ảnh chụp màn hình, hoặc "
        "bấm một gợi ý bên dưới để bắt đầu. Mọi câu trả lời đều ghi rõ nguồn "
        "(KB ngoại tuyến hay model AI trực tuyến) ngay bên dưới."
    ),
    "assistant.ui.suggestions.heading": "Gợi ý nhanh:",
    "assistant.ui.thinking": "Trợ lý đang suy nghĩ…",
    "assistant.ui.button.open_related_tool": "Mở {tool}",
    "assistant.ui.system.related_tool_launch_failed": (
        "Không mở được \"{tool}\" trên máy này ({reason}) — hãy tự mở từ menu "
        "ứng dụng."
    ),
    "assistant.ui.input.placeholder": "Dán thông báo lỗi vào đây, hoặc mô tả sự cố…",
    "assistant.ui.button.paste_error": "Dán lỗi",
    "assistant.ui.button.attach_image": "Đính kèm ảnh",
    "assistant.ui.button.send": "Gửi",
    "assistant.ui.button.sending": "Đang xử lý…",
    "assistant.ui.attach.menu.paste_clipboard_image": "Dán ảnh từ bộ nhớ tạm",
    "assistant.ui.attach.menu.choose_file": "Chọn tệp ảnh…",
    "assistant.ui.attach.dialog_title": "Chọn ảnh chụp màn hình lỗi",
    "assistant.ui.attach.image_filter": "Ảnh (*.png *.jpg *.jpeg *.bmp *.webp)",
    "assistant.ui.transcript.you_label": "Bạn",
    "assistant.ui.transcript.assistant_label": "Trợ lý",
    "assistant.ui.transcript.system_label": "Hệ thống",
    "assistant.ui.system.ocr_running": "Đang nhận dạng chữ từ ảnh (OCR)…",
    "assistant.ui.system.ocr_text_inserted": (
        "Đã nhận dạng chữ từ ảnh và điền vào ô nhập — xem lại rồi bấm \"Gửi\"."
    ),
    "assistant.ui.system.clipboard_text_empty": "Bộ nhớ tạm hiện không có văn bản để dán.",
    "assistant.ui.system.no_image_source": (
        "Bộ nhớ tạm không có ảnh nào — hãy chụp màn hình lỗi rồi thử lại, hoặc chọn tệp ảnh."
    ),
    "assistant.ui.system.empty_input": "Hãy nhập hoặc dán nội dung lỗi trước khi gửi.",
    "assistant.ui.error.engine_unexpected": (
        "Có lỗi không lường được khi xử lý câu hỏi — đã ghi lại, không ảnh "
        "hưởng tới máy của bạn. Hãy thử lại."
    ),
    # --- ui: thẻ App & Driver Concierge (dưới câu trả lời) ---
    "assistant.ui.install_plan.domain_label": "Miền chính thức: {domain}",
    "assistant.ui.install_plan.alt_label": "Giải pháp thay thế: {alt}",
    "assistant.ui.install_plan.wine_hint": (
        "Đây là phần mềm Windows — mở \"{tool}\" để thử chạy (không đảm bảo "
        "chạy mượt trên mọi máy)."
    ),
    "assistant.ui.button.install_one_click": "Cài 1 chạm",
    "assistant.ui.button.open_official_page": "Mở trang tải chính thức",
    "assistant.ui.install.running": "Đang cài…",
    "assistant.ui.install.dialog.title_ok": "Cài đặt thành công",
    "assistant.ui.install.dialog.title_fail": "Cài đặt không thành công",
    "assistant.ui.open_url.failed": (
        "Không mở được trang \"{domain}\" trên máy này — hãy tự dán địa chỉ "
        "này vào trình duyệt."
    ),
}

_EN: dict[str, str] = {
    "assistant.engine.offline.detected_subsystem": (
        "**Detected:** your message relates to the *{subsystem}* area (based "
        "on keyword/pattern matches in the text itself — a simple heuristic, "
        "not a certain diagnosis)."
    ),
    "assistant.engine.offline.cause_label": "**Possibly caused by:** {cause}",
    "assistant.engine.offline.steps_label": "**Steps to try:**",
    "assistant.engine.offline.rollback_label": "**Rollback/safety:** {rollback}",
    "assistant.engine.offline.howto_intro_label": "{cause}",
    "assistant.engine.offline.howto_steps_label": "**Steps:**",
    "assistant.engine.offline.howto_note_label": "**Note:** {rollback}",
    "assistant.engine.offline.ref_code_label": "**Reference code:** `{ref_id}`",
    "assistant.engine.offline.no_match": (
        "No matching guidance was found in the offline KB for this. Try: (1) "
        "paste the EXACT error line (don't summarize it), (2) describe what "
        "you were doing when it happened, or (3) if an online AI backend is "
        "configured, enable it for a deeper explanation. This is NOT an AI "
        "answer — just the offline KB having no matching case."
    ),
    "assistant.engine.offline.no_match_with_subsystem": (
        "**Detected:** your message relates to the *{subsystem}* area, but "
        "the offline KB does NOT have a specific guide matching this exact "
        "case yet — the Assistant won't invent fix steps it isn't sure about. "
        "Try describing it in more detail (paste the exact error message if "
        "you have one), open the related tool below (if any) to look "
        "directly, or enable the online AI backend for a deeper explanation."
    ),
    "assistant.engine.offline.unexpected_error": (
        "An internal error occurred while searching the offline KB — unrelated "
        "to your machine. Please try again, or describe the error differently."
    ),
    "assistant.engine.note.offline_kb": "Answer from the offline KB (no network needed) — NOT an AI model.",
    "assistant.engine.note.online_llm": "Answer from the online AI model ({model}).",
    "assistant.engine.note.online_fallback": (
        "The online AI backend could not answer ({reason}) — showing the offline KB instead."
    ),
    "assistant.engine.catalog.found_app": (
        "Found in NaMi's curated catalog: **{title}**. See the install plan below."
    ),
    "assistant.engine.catalog.found_driver": (
        "Found in NaMi's curated catalog: **{title}**. See the driver plan below."
    ),
    "assistant.engine.catalog.no_match": (
        "This isn't in NaMi's curated catalog yet. The Assistant will NOT guess a "
        "download link — try opening nStore (the software center) or searching in "
        "Settings → Apps."
    ),
    "assistant.ui.window_title": "nAssistant",
    "assistant.ui.header.title": "nAssistant",
    "assistant.ui.header.subtitle": (
        "Paste an error message or a screenshot — get guidance classified by "
        "subsystem (network/printing/wine/office/display/…)."
    ),
    "assistant.ui.status.offline_only": (
        "Mode: offline KB (no network needed). No online AI model configured."
    ),
    "assistant.ui.status.online_configured": (
        "Mode: online AI model ({model}) + offline KB fallback if the model fails."
    ),
    "assistant.ui.footer.disclaimer": (
        "This assistant only READS/EXPLAINS — it never changes settings or "
        "installs/removes anything on your machine."
    ),
    "assistant.ui.greeting": (
        "Hi! Paste an error message, attach a screenshot, or click a "
        "suggestion below to get started. Every answer shows its source "
        "(offline KB or online AI model) right underneath."
    ),
    "assistant.ui.suggestions.heading": "Quick suggestions:",
    "assistant.ui.thinking": "nAssistant is thinking…",
    "assistant.ui.button.open_related_tool": "Open {tool}",
    "assistant.ui.system.related_tool_launch_failed": (
        "Could not open \"{tool}\" on this machine ({reason}) — open it "
        "manually from the application menu."
    ),
    "assistant.ui.input.placeholder": "Paste the error message here, or describe the issue…",
    "assistant.ui.button.paste_error": "Paste error",
    "assistant.ui.button.attach_image": "Attach image",
    "assistant.ui.button.send": "Send",
    "assistant.ui.button.sending": "Working…",
    "assistant.ui.attach.menu.paste_clipboard_image": "Paste image from clipboard",
    "assistant.ui.attach.menu.choose_file": "Choose image file…",
    "assistant.ui.attach.dialog_title": "Choose a screenshot of the error",
    "assistant.ui.attach.image_filter": "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
    "assistant.ui.transcript.you_label": "You",
    "assistant.ui.transcript.assistant_label": "nAssistant",
    "assistant.ui.transcript.system_label": "System",
    "assistant.ui.system.ocr_running": "Reading text from the image (OCR)…",
    "assistant.ui.system.ocr_text_inserted": (
        "Text recognized from the image and inserted below — review it, then click \"Send\"."
    ),
    "assistant.ui.system.clipboard_text_empty": "The clipboard currently has no text to paste.",
    "assistant.ui.system.no_image_source": (
        "No image found on the clipboard — take a screenshot of the error and try again, "
        "or choose an image file."
    ),
    "assistant.ui.system.empty_input": "Type or paste the error content before sending.",
    "assistant.ui.error.engine_unexpected": (
        "An unexpected error occurred while processing your question — logged, your "
        "machine is unaffected. Please try again."
    ),
    "assistant.ui.install_plan.domain_label": "Official domain: {domain}",
    "assistant.ui.install_plan.alt_label": "Alternative: {alt}",
    "assistant.ui.install_plan.wine_hint": (
        "This is Windows software — open \"{tool}\" to try running it (not "
        "guaranteed to work smoothly on every machine)."
    ),
    "assistant.ui.button.install_one_click": "One-click install",
    "assistant.ui.button.open_official_page": "Open official download page",
    "assistant.ui.install.running": "Installing…",
    "assistant.ui.install.dialog.title_ok": "Install succeeded",
    "assistant.ui.install.dialog.title_fail": "Install failed",
    "assistant.ui.open_url.failed": (
        "Could not open \"{domain}\" on this machine — paste this address into "
        "your browser manually."
    ),
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
