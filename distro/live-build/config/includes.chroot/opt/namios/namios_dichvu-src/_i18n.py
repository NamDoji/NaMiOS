"""Catalog song ngữ riêng của ``namios_dichvu`` — đăng ký qua
``namios_i18n.add_catalog`` khi import (đúng quy ước ``namios_assistant._i18n``/
``namios_antoan._i18n``). KHÔNG sửa trực tiếp ``namios_i18n/locale/{vi,en}.json``.

Chrome giao diện (nhãn nút/tiêu đề/legend) đi qua lớp dịch này. Dữ liệu NỘI
DUNG catalog dịch vụ (``services_vn.json``: tên/mô tả/lý do trạng thái từng
dịch vụ) có field ``_vi``/``_en`` SONG SONG ngay trong JSON — KHÔNG đi qua
``namios_i18n`` (cùng quy ước đã ghi ở ``namios_assistant._i18n`` cho
``kb/starter_kb.json``: dữ liệu nội dung khác với chrome UI)."""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    "dichvu.ui.window_title": "Cổng Dịch vụ Việt — Trung tâm Ký số",
    "dichvu.ui.header.title": "Cổng Dịch vụ Việt",
    "dichvu.ui.header.subtitle": (
        "Thuế · Bảo hiểm xã hội · Dịch vụ công · Hoá đơn điện tử · Ký số — một chỗ, "
        "nhãn trung thực, đi đúng cổng."
    ),
    "dichvu.ui.search.placeholder": "Tìm kiếm (gõ có dấu hoặc không dấu) — ví dụ: khai thue, bao hiem, ky so...",
    "dichvu.ui.category.all": "Tất cả",
    "dichvu.ui.category.count_suffix": "({count})",
    "dichvu.ui.envcheck.button": "Tự kiểm môi trường",
    "dichvu.ui.envcheck.dialog_title": "Tự kiểm môi trường (chỉ đọc)",
    "dichvu.ui.envcheck.section.browser": "Trình duyệt",
    "dichvu.ui.envcheck.browser.xdg_open_ok": "Máy này có xdg-open (công cụ mở link qua trình duyệt mặc định).",
    "dichvu.ui.envcheck.browser.xdg_open_missing": "Máy này KHÔNG có xdg-open — nút \"Mở web\" sẽ không dùng được. Cài gói xdg-utils để khắc phục.",
    "dichvu.ui.envcheck.browser.known_found": "Đã tìm thấy trình duyệt qua PATH: {names}.",
    "dichvu.ui.envcheck.browser.known_none": "Không tìm thấy trình duyệt phổ biến nào qua PATH (vẫn có thể có trình duyệt khác chưa dò).",
    "dichvu.ui.envcheck.section.signing": "Công cụ ký số có sẵn",
    "dichvu.ui.envcheck.signing.okular": "Okular (ký PDF): {status}",
    "dichvu.ui.envcheck.signing.libreoffice": "nOffice/LibreOffice (ký văn bản): {status}",
    "dichvu.ui.envcheck.signing.pkcs11": "Công cụ dò USB token (pkcs11-tool/opensc): {status}",
    "dichvu.ui.envcheck.status.present": "có",
    "dichvu.ui.envcheck.status.missing": "chưa có",
    "dichvu.ui.envcheck.section.clock": "Giờ hệ thống",
    "dichvu.ui.envcheck.clock.line": "Giờ hiện tại: {time} (múi giờ: {tz})",
    "dichvu.ui.envcheck.section.manual": "Cần bạn tự kiểm (NaMi không tự kiểm được từ mã)",
    "dichvu.ui.envcheck.footer": (
        "Tự kiểm này CHỈ đọc thông tin máy (PATH/giờ hệ thống) — không thu thập, không gửi đi đâu, "
        "không yêu cầu PIN/mật khẩu nào."
    ),
    "dichvu.ui.card.open_web": "Mở web",
    "dichvu.ui.card.open_web_disabled_no_url": "Chưa có URL chính thức",
    "dichvu.ui.card.open_web_error_no_tool": (
        "Không mở được trang web — máy này thiếu xdg-open (công cụ mở trình duyệt mặc định). "
        "Hãy cài gói xdg-utils rồi thử lại."
    ),
    "dichvu.ui.card.open_web_error_unsafe_url": (
        "Không mở được — liên kết (URL) trong dữ liệu dịch vụ không hợp lệ (thiếu http(s)). "
        "Đây là lỗi dữ liệu cài sẵn, không phải do bạn thao tác sai — hãy báo lại thông báo "
        "này cho đội NaMiOS."
    ),
    "dichvu.ui.card.open_app_error_no_tool": (
        "Không mở được {app} — ứng dụng này chưa được cài trên máy. Hãy cài {app} rồi thử lại."
    ),
    "dichvu.ui.card.provider_label": "Nhà cung cấp: {provider}",
    "dichvu.ui.card.published_status_label": "Trạng thái công bố gốc: {status}",
    "dichvu.ui.card.published_status_none": (
        "Trạng thái công bố gốc: chưa áp dụng (dịch vụ này không nằm trong danh mục có "
        "trạng thái công bố gốc)"
    ),
    "dichvu.ui.card.account_condition_label": "Điều kiện tài khoản: {condition}",
    "dichvu.ui.card.source_label": "Nguồn: {source}",
    "dichvu.ui.card.last_updated_label": "Cập nhật: {date}",
    "dichvu.ui.card.tested_label": "NaMi đã kiểm tra: {value}",
    "dichvu.ui.card.vendor_support_label": "Nhà cung cấp xác nhận hỗ trợ: {value}",
    "dichvu.ui.card.bool_yes": "có",
    "dichvu.ui.card.bool_no": "chưa",
    "dichvu.ui.card.recommended_badge": "Khuyến nghị",
    "dichvu.ui.card.guide_toggle": "Xem hướng dẫn",
    "dichvu.ui.card.probe_button": "Dò token USB (chỉ đọc)",
    "dichvu.ui.card.probe_result_title": "Kết quả dò PKCS#11",
    "dichvu.ui.status.works_web": "Chạy qua web",
    "dichvu.ui.status.works_native": "Chạy trực tiếp (có sẵn)",
    "dichvu.ui.status.wine_candidate": "Có thể chạy qua Wine (chưa kiểm)",
    "dichvu.ui.status.blocked": "Bị chặn",
    "dichvu.ui.kyso.banner_title": "Trung tâm Ký số — gợi ý thứ tự nên thử (tin cậy nhất trước)",
    "dichvu.ui.kyso.banner_body": (
        "1) Ký số TỪ XA (SmartCA/MySign) — web, không cần Wine, khuyến nghị thử trước. "
        "2) Ký PDF bằng chứng thư mềm .p12 qua Okular/LibreOffice — có sẵn, chạy trực tiếp "
        "trên máy (không cần Wine). "
        "3) USB token vật lý qua PKCS#11 — hiện BỊ CHẶN với 3 hãng CA lớn (chưa có middleware "
        "Linux chính hãng công khai); dò thử bằng nút \"Dò token USB\" nếu muốn tự kiểm."
    ),
    "dichvu.ui.footer.disclaimer": (
        "Nhãn trạng thái ở đây do NaMi tự phân loại dựa trên dữ liệu đã khảo sát, KHÔNG phải "
        "xác nhận của nhà cung cấp/cơ quan nhà nước. Toàn bộ thông tin này CHƯA được kiểm "
        "thử trên máy thật (phần cứng thật)."
    ),
    "dichvu.ui.empty_category_note_prefix": "Lưu ý: ",
    "dichvu.ui.no_results": "Không tìm thấy dịch vụ phù hợp — thử bỏ dấu hoặc gõ từ khác.",
    "dichvu.ui.load_error_title": "Không tải được dữ liệu dịch vụ",
    "dichvu.ui.dialog.close_button": "Đóng",
}

_EN: dict[str, str] = {
    "dichvu.ui.window_title": "nServices — Digital Signing Center",
    "dichvu.ui.header.title": "nServices",
    "dichvu.ui.header.subtitle": (
        "Tax · Social insurance · Public administration · e-Invoice · Digital signing — one "
        "place, honest labels, the right door."
    ),
    "dichvu.ui.search.placeholder": "Search (with or without accents) — e.g. khai thue, bao hiem, ky so...",
    "dichvu.ui.category.all": "All",
    "dichvu.ui.category.count_suffix": "({count})",
    "dichvu.ui.envcheck.button": "Self-check environment",
    "dichvu.ui.envcheck.dialog_title": "Environment self-check (read-only)",
    "dichvu.ui.envcheck.section.browser": "Browser",
    "dichvu.ui.envcheck.browser.xdg_open_ok": "xdg-open (opens links in the default browser) is present on this machine.",
    "dichvu.ui.envcheck.browser.xdg_open_missing": "xdg-open is NOT present on this machine — \"Open web\" buttons will not work.",
    "dichvu.ui.envcheck.browser.known_found": "Browsers found on PATH: {names}.",
    "dichvu.ui.envcheck.browser.known_none": "No common browser found on PATH (another browser may still be present but was not probed).",
    "dichvu.ui.envcheck.section.signing": "Available signing tools",
    "dichvu.ui.envcheck.signing.okular": "Okular (sign PDF): {status}",
    "dichvu.ui.envcheck.signing.libreoffice": "nOffice/LibreOffice (sign document): {status}",
    "dichvu.ui.envcheck.signing.pkcs11": "USB token probe tool (pkcs11-tool/opensc): {status}",
    "dichvu.ui.envcheck.status.present": "present",
    "dichvu.ui.envcheck.status.missing": "missing",
    "dichvu.ui.envcheck.section.clock": "System clock",
    "dichvu.ui.envcheck.clock.line": "Current time: {time} (timezone: {tz})",
    "dichvu.ui.envcheck.section.manual": "Needs your own check (NaMi cannot verify this from code)",
    "dichvu.ui.envcheck.footer": (
        "This self-check ONLY reads local machine info (PATH/system clock) — nothing is "
        "collected or sent anywhere, no PIN/password is requested."
    ),
    "dichvu.ui.card.open_web": "Open web",
    "dichvu.ui.card.open_web_disabled_no_url": "No official URL yet",
    "dichvu.ui.card.open_web_error_no_tool": "Could not open — xdg-open is missing on this machine.",
    "dichvu.ui.card.open_web_error_unsafe_url": "Not opened — the data URL is invalid (missing http(s)).",
    "dichvu.ui.card.open_app_error_no_tool": "Could not open — {app} is not installed.",
    "dichvu.ui.card.provider_label": "Provider: {provider}",
    "dichvu.ui.card.published_status_label": "Original published status: {status}",
    "dichvu.ui.card.published_status_none": (
        "Original published status: not applicable (this service is outside the"
        " published-status catalog)"
    ),
    "dichvu.ui.card.account_condition_label": "Account requirement: {condition}",
    "dichvu.ui.card.source_label": "Source: {source}",
    "dichvu.ui.card.last_updated_label": "Updated: {date}",
    "dichvu.ui.card.tested_label": "Tested by NaMi: {value}",
    "dichvu.ui.card.vendor_support_label": "Vendor-confirmed support: {value}",
    "dichvu.ui.card.bool_yes": "yes",
    "dichvu.ui.card.bool_no": "not yet",
    "dichvu.ui.card.recommended_badge": "Recommended",
    "dichvu.ui.card.guide_toggle": "Show guide",
    "dichvu.ui.card.probe_button": "Probe USB token (read-only)",
    "dichvu.ui.card.probe_result_title": "PKCS#11 probe result",
    "dichvu.ui.status.works_web": "Works via web",
    "dichvu.ui.status.works_native": "Works natively (built in)",
    "dichvu.ui.status.wine_candidate": "Wine candidate (untested)",
    "dichvu.ui.status.blocked": "Blocked",
    "dichvu.ui.kyso.banner_title": "Digital Signing Center — the most reliable order to try",
    "dichvu.ui.kyso.banner_body": (
        "1) Remote signing (SmartCA/MySign) — web, no Wine, recommended to try first. "
        "2) Sign a PDF with a soft .p12 certificate via Okular/LibreOffice — already built in, "
        "runs natively. 3) Physical USB token via PKCS#11 — currently BLOCKED for the three "
        "major CAs (no publicly known official Linux middleware); use the \"Probe USB token\" "
        "button if you want to check for yourself."
    ),
    "dichvu.ui.footer.disclaimer": (
        "Status labels here are NaMi's own classification based on surveyed data, NOT a "
        "vendor/government confirmation. None of this has been tested on real hardware yet."
    ),
    "dichvu.ui.empty_category_note_prefix": "Note: ",
    "dichvu.ui.no_results": "No matching service found — try removing accents or a different word.",
    "dichvu.ui.load_error_title": "Could not load service data",
    "dichvu.ui.dialog.close_button": "Close",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
