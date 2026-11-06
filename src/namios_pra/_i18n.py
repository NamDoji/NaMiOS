"""Lớp common song ngữ của ``namios_pra`` (Phụ lục 06) — đăng ký qua
``namios_i18n.add_catalog`` khi import. Trường DỮ LIỆU ``*_vi`` luôn tiếng Việt.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # thiết bị (PRA-001)
    "pra.device.untested": "Chưa kiểm chức năng '{func}' của thiết bị '{model}'.",
    "pra.device.no_copy_infer": (
        "In được + scan được KHÔNG tự thành 'copy được' — copy là chức năng riêng, "
        "phải kiểm độc lập."
    ),
    # Office route (PRA-016)
    "pra.office.native": "Dùng bộ Office native Linux (offline) — báo độ đúng DOCX/XLSX/PPTX.",
    "pra.office.web": "Dùng Microsoft 365 web — cần mạng + tài khoản; tính năng web khác desktop.",
    "pra.office.windows_needed": (
        "Nhu cầu ({needs}) cần Office desktop Windows (VM/remote có phép) — còn phụ thuộc Windows."
    ),
    "pra.office.macro_not_web": (
        "File cần MACRO/COM/add-in — KHÔNG gán được Office web (VBA không chạy trên web); "
        "phải Windows VM/remote."
    ),
    "pra.office.viewer": "Chỉ xem (read-only) bằng trình xem có phép — chưa phải sửa/ký được.",
    "pra.office.blocked": "Chưa có tuyến Office đạt cho nhu cầu này — ghi blocker, không bịa.",
    # fidelity (PRA-017)
    "pra.fidelity.blocking": (
        "Khác biệt NGHĨA so bản gốc ({fields}) — CHẶN lưu/in tới khi đúng (mở được ≠ đúng dữ liệu)."
    ),
    "pra.fidelity.ok": "Không có khác biệt nghĩa — chỉ khác hiển thị nhỏ (nếu có).",
    # .NET (PRA-022/023)
    "pra.dotnet.native": ".NET hiện đại đa nền tảng ({kind}) — thử chạy native Linux.",
    "pra.dotnet.wine": "App .NET chỉ-Windows ({kind}) — chỉ THỬ Wine theo đúng version + license.",
    "pra.dotnet.windows_only": (
        "{kind} gắn Windows (WPF/WinUI/WinForms/driver) — KHÔNG native Linux; "
        "cần Windows VM/remote."
    ),
    "pra.dotnet.unknown": "Thiếu metadata/manifest — để 'unknown', không đoán tuyến.",
    # tiến độ (PRA-032)
    "pra.print.queued": "Đã gửi tới hàng đợi in — ĐANG CHỜ, chưa in.",
    "pra.print.printing": "Máy đang in…",
    "pra.print.machine_done": "Máy báo in xong job — CHƯA xác nhận người dùng đã cầm bản in.",
    "pra.print.user_confirmed": "Người dùng xác nhận đã nhận bản in.",
    "pra.print.failed": "In thất bại.",
    "pra.print.cancelled": "Đã hủy job in.",
    "pra.print.unknown": "Chưa rõ trạng thái in — cần tra cứu, không báo đã xong.",
    "pra.sign.prepared": "Đã chuẩn bị hồ sơ ký — CHƯA ký.",
    "pra.sign.signed": "Đã ký — CHƯA nộp.",
    "pra.sign.submitted": "Đã nộp — CHƯA có biên nhận từ cổng.",
    "pra.sign.receipt": "Cổng đã trả biên nhận hợp lệ.",
    "pra.sign.failed": "Ký/nộp thất bại.",
    "pra.sign.unknown": "Chưa rõ trạng thái ký/nộp — cần tra cứu.",
}

_EN: dict[str, str] = {
    "pra.device.untested": "Function '{func}' of device '{model}' is not tested yet.",
    "pra.device.no_copy_infer": (
        "Print-ok + scan-ok does NOT imply 'copy-ok' — copy is a separate function, "
        "must be tested independently."
    ),
    "pra.office.native": "Use native Linux Office (offline) — report DOCX/XLSX/PPTX fidelity.",
    "pra.office.web": "Use Microsoft 365 web — needs network + account; web features differ.",
    "pra.office.windows_needed": (
        "Needs ({needs}) require Office desktop on Windows (licensed VM/remote) — "
        "still Windows-dependent."
    ),
    "pra.office.macro_not_web": (
        "File needs MACRO/COM/add-in — CANNOT use Office web (VBA does not run on web); "
        "needs Windows VM/remote."
    ),
    "pra.office.viewer": "Read-only via a licensed viewer — not yet editable/signable.",
    "pra.office.blocked": "No adequate Office route for this need — record a blocker, do not fake.",
    "pra.fidelity.blocking": (
        "MEANINGFUL difference from the original ({fields}) — BLOCK save/print until correct "
        "(opening ≠ correct data)."
    ),
    "pra.fidelity.ok": "No meaningful difference — only minor rendering differences (if any).",
    "pra.dotnet.native": "Modern cross-platform .NET ({kind}) — try running native on Linux.",
    "pra.dotnet.wine": (
        "Windows-only .NET app ({kind}) — only TRY Wine for the exact version + license."
    ),
    "pra.dotnet.windows_only": (
        "{kind} is Windows-bound (WPF/WinUI/WinForms/driver) — NOT native Linux; "
        "needs Windows VM/remote."
    ),
    "pra.dotnet.unknown": "Missing metadata/manifest — leave 'unknown', do not guess a route.",
    "pra.print.queued": "Sent to the print queue — WAITING, not printed.",
    "pra.print.printing": "Printer is printing…",
    "pra.print.machine_done": "Printer reports the job done — user has NOT confirmed receiving it.",
    "pra.print.user_confirmed": "User confirmed receiving the printout.",
    "pra.print.failed": "Printing failed.",
    "pra.print.cancelled": "Print job cancelled.",
    "pra.print.unknown": "Print status unknown — look it up, do not report done.",
    "pra.sign.prepared": "Signing package prepared — NOT signed.",
    "pra.sign.signed": "Signed — NOT submitted.",
    "pra.sign.submitted": "Submitted — NO portal receipt yet.",
    "pra.sign.receipt": "Portal returned a valid receipt.",
    "pra.sign.failed": "Signing/submission failed.",
    "pra.sign.unknown": "Signing/submission status unknown — look it up.",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
