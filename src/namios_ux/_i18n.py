"""Lớp common song ngữ của tầng UX (Phụ lục 12) — đăng ký qua
``namios_i18n.add_catalog`` khi import (giống ``namios_sys._i18n``).

Chứa HAI loại chuỗi:
  - thông điệp human-facing (``ux.shortcut.*``/``ux.wallpaper.*``/``ux.token.*``)
    dùng qua ``t()`` tại call-site, ép ``lang=Lang.VI`` cho trường dữ liệu;
  - glossary tiếng Việt chính thức (``ux.glossary.*`` — UX12-037): đây LÀ nguồn
    thuật ngữ duy nhất mà ``namios_ux.glossary`` tra cứu, KHÔNG tự dựng kho từ
    vựng song song hay đọc file ``design/*.json`` ngoài repo.

Module dùng ``t("ux.*")``/``has_key("ux.glossary.*")`` phải import module này:
``from namios_ux import _i18n as _i18n``.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # Registry phím tắt (UX12-019/021/024)
    "ux.shortcut.conflict": (
        "Hai phím tắt '{a}' và '{b}' cùng tổ hợp '{combo}' trong phạm vi giao "
        "nhau — xung đột (UX12-019)."
    ),
    "ux.shortcut.p0_system_conflict": (
        "Xung đột P0 cấp HỆ THỐNG giữa '{a}' và '{b}' (tổ hợp '{combo}') — "
        "CHẶN phát hành theo CI (UX12-019)."
    ),
    "ux.shortcut.unknown_action": (
        "Không tìm thấy action '{action}' trong registry phím tắt — không đổi được."
    ),
    "ux.shortcut.not_overridable": ("Phím tắt '{action}' không cho phép đổi (overridable=False)."),
    "ux.shortcut.claimed_by_app": (
        "Tổ hợp '{combo}' đã bị ứng dụng '{owner}' chiếm (phạm vi app) — "
        "không thể gán cho '{action}'."
    ),
    "ux.shortcut.combo_taken": (
        "Tổ hợp '{combo}' đã được dùng bởi '{owner}' trong phạm vi giao nhau — "
        "không thể gán cho '{action}'."
    ),
    "ux.shortcut.override_ok": "Đã đổi phím tắt của '{action}' sang tổ hợp '{combo}'.",
    "ux.shortcut.unsafe_action": (
        "Phím tắt gắn hành động '{command}' có dấu hiệu vượt quyền (root/shell/"
        "gửi tệp/bỏ bảo vệ/ký nộp) — chặn (UX12-024)."
    ),
    # Hình nền (UX12-025..032/046)
    "ux.wallpaper.missing_title": "Hình nền '{title}' thiếu tiêu đề — chưa đủ metadata.",
    "ux.wallpaper.missing_location": "Hình nền '{title}' thiếu địa danh — chưa đủ metadata.",
    "ux.wallpaper.missing_author": "Hình nền '{title}' thiếu tác giả — chưa đủ metadata.",
    "ux.wallpaper.missing_license": (
        "Hình nền '{title}' thiếu giấy phép — KHÔNG được đóng gói (UX12-026)."
    ),
    "ux.wallpaper.missing_rights_evidence": (
        "Hình nền '{title}' thiếu bằng chứng quyền sử dụng — KHÔNG được đóng " "gói (UX12-026)."
    ),
    "ux.wallpaper.missing_sha256": (
        "Hình nền '{title}' thiếu sha256 — KHÔNG được đóng gói (UX12-026)."
    ),
    "ux.wallpaper.missing_variants": (
        "Hình nền '{title}' chưa có biến thể xuất bản nào — chưa đủ metadata."
    ),
    "ux.wallpaper.ai_undisclosed": (
        "Hình nền '{title}' do AI tạo/sửa nhưng CHƯA khai rõ trong credit/nguồn "
        "— chặn (UX12-031)."
    ),
    # Design token / tương phản màu
    "ux.token.contrast_fail": (
        "Cặp màu chữ/nền '{fg}'/'{bg}' có tỉ lệ tương phản {ratio} — DƯỚI "
        "ngưỡng WCAG (UX12 §3.2 [4])."
    ),
    "ux.token.invalid_hex": "Giá trị màu '{value}' không phải mã hex hợp lệ (vd '#223344').",
    # Glossary tiếng Việt (UX12-037) — nguồn DUY NHẤT, namios_ux.glossary tra qua đây.
    "ux.glossary.tep": "Tệp",
    "ux.glossary.thu_muc": "Thư mục",
    "ux.glossary.ung_dung": "Ứng dụng",
    "ux.glossary.may_in": "Máy in",
    "ux.glossary.cap_nhat": "Cập nhật",
    "ux.glossary.khoi_phuc": "Khôi phục",
    "ux.glossary.bo_go": "Bộ gõ",
    "ux.glossary.trinh_dieu_khien": "Trình điều khiển (driver)",
    "ux.glossary.missing_term": (
        "Thiếu thuật ngữ bắt buộc '{term}' trong glossary tiếng Việt (UX12-037)."
    ),
}

_EN: dict[str, str] = {
    "ux.shortcut.conflict": (
        "Shortcuts '{a}' and '{b}' share combo '{combo}' in overlapping scope "
        "— conflict (UX12-019)."
    ),
    "ux.shortcut.p0_system_conflict": (
        "P0 SYSTEM-scope conflict between '{a}' and '{b}' (combo '{combo}') — "
        "blocks release per CI (UX12-019)."
    ),
    "ux.shortcut.unknown_action": (
        "Action '{action}' not found in the shortcut registry — cannot change it."
    ),
    "ux.shortcut.not_overridable": "Shortcut '{action}' cannot be changed (overridable=False).",
    "ux.shortcut.claimed_by_app": (
        "Combo '{combo}' is already claimed by app '{owner}' (app scope) — "
        "cannot assign it to '{action}'."
    ),
    "ux.shortcut.combo_taken": (
        "Combo '{combo}' is already used by '{owner}' in an overlapping scope "
        "— cannot assign it to '{action}'."
    ),
    "ux.shortcut.override_ok": "Changed shortcut for '{action}' to combo '{combo}'.",
    "ux.shortcut.unsafe_action": (
        "Shortcut bound to action '{command}' looks like it exceeds allowed "
        "scope (root/shell/send-file/disable-protection/sign-submit) — "
        "blocked (UX12-024)."
    ),
    "ux.wallpaper.missing_title": "Wallpaper '{title}' is missing a title — metadata incomplete.",
    "ux.wallpaper.missing_location": (
        "Wallpaper '{title}' is missing a location — metadata incomplete."
    ),
    "ux.wallpaper.missing_author": (
        "Wallpaper '{title}' is missing an author — metadata incomplete."
    ),
    "ux.wallpaper.missing_license": (
        "Wallpaper '{title}' is missing a license — MUST NOT be packaged (UX12-026)."
    ),
    "ux.wallpaper.missing_rights_evidence": (
        "Wallpaper '{title}' is missing rights evidence — MUST NOT be packaged (UX12-026)."
    ),
    "ux.wallpaper.missing_sha256": (
        "Wallpaper '{title}' is missing a sha256 — MUST NOT be packaged (UX12-026)."
    ),
    "ux.wallpaper.missing_variants": (
        "Wallpaper '{title}' has no published variants yet — metadata incomplete."
    ),
    "ux.wallpaper.ai_undisclosed": (
        "Wallpaper '{title}' is AI generated/edited but NOT disclosed in "
        "credit/source — blocked (UX12-031)."
    ),
    "ux.token.contrast_fail": (
        "Text/surface color pair '{fg}'/'{bg}' has contrast ratio {ratio} — "
        "BELOW the WCAG threshold (UX12 §3.2 [4])."
    ),
    "ux.token.invalid_hex": "Color value '{value}' is not a valid hex color (e.g. '#223344').",
    "ux.glossary.tep": "File",
    "ux.glossary.thu_muc": "Folder",
    "ux.glossary.ung_dung": "Application",
    "ux.glossary.may_in": "Printer",
    "ux.glossary.cap_nhat": "Update",
    "ux.glossary.khoi_phuc": "Restore",
    "ux.glossary.bo_go": "Input method (IME)",
    "ux.glossary.trinh_dieu_khien": "Driver",
    "ux.glossary.missing_term": (
        "Missing required term '{term}' in the Vietnamese glossary (UX12-037)."
    ),
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
