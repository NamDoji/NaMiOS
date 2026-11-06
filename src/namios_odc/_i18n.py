"""Lớp common song ngữ của ``namios_odc`` (Phụ lục 07) — đăng ký qua
``namios_i18n.add_catalog`` khi import. Trường dữ liệu ``*_vi`` luôn tiếng Việt.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # Office route matrix (ODC-008)
    "odc.route.macro_windows": "Cần chạy macro/COM → Windows có phép (VM/remote); macro chạy được.",
    "odc.route.wine_experimental": "Tuyến Wine chỉ THỬ theo đúng bản app + license.",
    "odc.route.macro_unverified": "Macro trên Wine CHƯA được chứng minh — không gán macro-pass.",
    "odc.route.macro_blocked": (
        "File cần macro nhưng chưa có Windows có phép → phần macro BỊ CHẶN; hiện chỉ xem được."
    ),
    "odc.route.bundled_view": "Xem bằng bộ Office cài sẵn.",
    "odc.route.viewer": "Xem read-only bằng trình xem có phép (chưa phải sửa/ký được).",
    "odc.route.bundled_edit": "Sửa bằng bộ Office cài sẵn — độ đúng đã đo cho định dạng này.",
    "odc.route.bundled_edit_unverified": (
        "Sửa bằng bộ Office cài sẵn — mở được NHƯNG chưa đo độ đúng (chưa dám nhận sửa/in đúng)."
    ),
    "odc.route.web": (
        "Dùng Office web chính thức — cần mạng + tài khoản; tính năng web khác desktop."
    ),
    "odc.route.web_sensitive": (
        "File nhạy cảm: KHÔNG tự upload lên web — cần bạn xác nhận rõ trước khi đưa lên."
    ),
    "odc.route.no_edit_route": "Chưa có tuyến sửa đạt cho file này — ghi blocker, không bịa.",
}

_EN: dict[str, str] = {
    "odc.route.macro_windows": "Macro/COM needed → licensed Windows (VM/remote); macros can run.",
    "odc.route.wine_experimental": (
        "Wine route is EXPERIMENTAL for the exact app version + license."
    ),
    "odc.route.macro_unverified": "Macros on Wine are UNVERIFIED — do not label macro-pass.",
    "odc.route.macro_blocked": (
        "File needs macros but no licensed Windows → the macro part is BLOCKED; view-only for now."
    ),
    "odc.route.bundled_view": "View with the bundled Office suite.",
    "odc.route.viewer": "Read-only via a licensed viewer (not yet editable/signable).",
    "odc.route.bundled_edit": "Edit with the bundled Office — fidelity measured for this format.",
    "odc.route.bundled_edit_unverified": (
        "Edit with the bundled Office — opens BUT fidelity not measured "
        "(can't claim faithful save/print)."
    ),
    "odc.route.web": "Use official Office web — needs network + account; web features differ.",
    "odc.route.web_sensitive": (
        "Sensitive file: NOT auto-uploaded to web — explicit confirmation needed before upload."
    ),
    "odc.route.no_edit_route": (
        "No adequate edit route for this file — record a blocker, do not fake."
    ),
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
