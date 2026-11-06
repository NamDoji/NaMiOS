"""Lớp common song ngữ của ``namios_essentials`` (Phụ lục 11) — đăng ký qua
``namios_i18n.add_catalog`` khi import. Trường dữ liệu ``*_vi`` luôn tiếng Việt.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # labels (APP11-001/013)
    "essentials.label.cai_tren_may": "Cài trên máy",
    "essentials.label.dich_vu_web": "Dịch vụ web",
    "essentials.label.qua_wine_da_kiem_thu": "Qua Wine (đã kiểm thử)",
    "essentials.label.can_ket_noi": "Cần kết nối",
    # anti-impersonation (APP11-003/033)
    "essentials.domain.allowed": (
        "Tên miền '{domain}' nằm trong allowlist chính thức, HTTPS hợp lệ."
    ),
    "essentials.domain.impersonation": (
        "Tên miền '{domain}' KHÔNG nằm trong allowlist nhưng chứa tên thương hiệu đã"
        " biết — nghi mạo danh, đã chặn trước khi hiển thị form đăng nhập."
    ),
    "essentials.domain.not_allowlisted": (
        "Tên miền '{domain}' không nằm trong allowlist chính thức hoặc thiếu HTTPS —"
        " đã chặn, không mở shortcut."
    ),
    # update center (APP11-013/019/020)
    "essentials.update.vendor_managed": (
        "Được nhà cung cấp cập nhật trực tuyến — NaMiOS không có phiên bản cài" " trên máy để báo."
    ),
    "essentials.update.up_to_date": "Đã ở phiên bản mới nhất theo lần kiểm gần nhất.",
    "essentials.update.available": "Có bản cập nhật: đang cài {installed} → mới {available}.",
    "essentials.update.service_incident": (
        "Sự cố dịch vụ hoặc tương thích — KHÔNG phải do NaMiOS chưa cập nhật."
        " Theo dõi phía vendor và kiểm lại khi có thay đổi."
    ),
    "essentials.scanner.signature_expired": (
        "Chữ ký nhận diện mã độc đã quá hạn (cập nhật lần cuối {last_scan_at},"
        " {age} ngày trước) — mức bảo vệ GIẢM dù lần quét gần nhất 'sạch'."
    ),
    "essentials.scanner.clean_current": (
        "Chữ ký còn hiệu lực, lần quét cuối ({last_scan_at}) sạch."
    ),
    "essentials.scanner.found_issue": (
        "Chữ ký còn hiệu lực, lần quét cuối ({last_scan_at}) phát hiện vấn đề."
    ),
    # schedule (APP11-015)
    "essentials.schedule.overdue": "Bản vá đã quá hạn cài — cần nhắc rõ, không thể hoãn thêm.",
    "essentials.schedule.busy_defer_tonight": (
        "Đang trong tiết học/cuộc họp — không tự khởi động lại; đề xuất 'Cài tối nay'."
    ),
    "essentials.schedule.critical_now": "Bản vá khẩn, không có ngữ cảnh bận — có thể cài ngay.",
    "essentials.schedule.routine_defer": "Cập nhật thường — hoãn theo lịch người dùng chọn.",
    # recovery (APP11-032)
    "essentials.recovery.web_not_rollbackable": (
        "Dịch vụ web không rollback được từ phía NaMiOS — mở trang chính thức/trình"
        " duyệt khác đã kiểm, hoặc báo vendor."
    ),
    "essentials.recovery.no_attempt": "Chưa có lần cập nhật nào được ghi nhận cho kênh này.",
    "essentials.recovery.rolled_back": (
        "Cập nhật lỗi — đã rollback về bản trước, tài liệu người dùng không mất."
    ),
    "essentials.recovery.ok": "Cập nhật thành công và đã commit.",
    "essentials.recovery.failed_untouched": (
        "Cập nhật không thực hiện được — hệ thống chưa bị đụng tới."
    ),
    # update txn (APP11-016/019)
    "essentials.update_txn.web_shortcut_not_installable": (
        "Dịch vụ web không có gói để cài/rollback phía NaMiOS — không chạy giao dịch."
    ),
    # rings (APP11-017)
    "essentials.ring.retained_with_deadline": (
        "Dịch vụ trọng yếu hỏng ở lab ({services}) — stable giữ bản cũ đến {deadline},"
        " kèm cảnh báo rủi ro bảo mật, KHÔNG giữ vô hạn."
    ),
    "essentials.ring.no_deadline": "CHƯA ĐẶT HẠN (vi phạm — phải đặt hạn trước khi giữ bản cũ)",
    # smartai classify (APP11-026)
    "essentials.smartai.wine_pending_cert": (
        "App Windows qua Wine chưa chứng nhận bản mới — chưa cập nhật, cần qua" " lab/retest trước."
    ),
    "essentials.smartai.wine_certified_update": (
        "App Windows qua Wine đã chứng nhận bản mới — có thể cập nhật recipe/runner."
    ),
    "essentials.smartai.vendor_web_service": (
        "Đây là dịch vụ web — nhà cung cấp tự cập nhật trên server của họ. NaMiOS chỉ"
        " cập nhật browser, manifest tích hợp và kiểm tương thích phía mình."
    ),
    "essentials.smartai.browser_manifest": (
        "NaMiOS cập nhật được: trình duyệt/engine + manifest tích hợp."
    ),
    "essentials.smartai.native_package": (
        "Coi là gói native NaMiOS/distro — kiểm nguồn/chữ ký rồi cập nhật qua" " Update Center."
    ),
}

_EN: dict[str, str] = {
    "essentials.label.cai_tren_may": "Installed on device",
    "essentials.label.dich_vu_web": "Web service",
    "essentials.label.qua_wine_da_kiem_thu": "Via Wine (tested)",
    "essentials.label.can_ket_noi": "Needs connection",
    "essentials.domain.allowed": "Domain '{domain}' is on the official allowlist, valid HTTPS.",
    "essentials.domain.impersonation": (
        "Domain '{domain}' is NOT on the allowlist but contains a known brand name —"
        " impersonation suspected, blocked before any login form is shown."
    ),
    "essentials.domain.not_allowlisted": (
        "Domain '{domain}' is not on the official allowlist or is missing HTTPS —"
        " blocked, shortcut not opened."
    ),
    "essentials.update.vendor_managed": (
        "Updated online by the vendor — NaMiOS has no on-device version to report."
    ),
    "essentials.update.up_to_date": "Already up to date as of the last check.",
    "essentials.update.available": "Update available: installed {installed} -> new {available}.",
    "essentials.update.service_incident": (
        "Service incident or compatibility issue — NOT because NaMiOS is outdated."
        " Monitor the vendor side and recheck when it changes."
    ),
    "essentials.scanner.signature_expired": (
        "Malware signatures are stale (last updated {last_scan_at}, {age} days ago) —"
        " protection level is REDUCED even though the last scan was clean."
    ),
    "essentials.scanner.clean_current": (
        "Signatures current, last scan ({last_scan_at}) was clean."
    ),
    "essentials.scanner.found_issue": (
        "Signatures current, last scan ({last_scan_at}) found an issue."
    ),
    "essentials.schedule.overdue": (
        "This patch is overdue — must be surfaced clearly, cannot be deferred further."
    ),
    "essentials.schedule.busy_defer_tonight": (
        "A class/meeting is in progress — no forced restart; suggest 'install tonight'."
    ),
    "essentials.schedule.critical_now": "Critical patch, no busy context — can install now.",
    "essentials.schedule.routine_defer": "Routine update — defer per the user's schedule.",
    "essentials.recovery.web_not_rollbackable": (
        "Web services cannot be rolled back from NaMiOS — open the official page/"
        "another tested browser, or report to the vendor."
    ),
    "essentials.recovery.no_attempt": "No update attempt has been recorded for this channel yet.",
    "essentials.recovery.rolled_back": (
        "Update failed — rolled back to the previous version, user documents are safe."
    ),
    "essentials.recovery.ok": "Update succeeded and was committed.",
    "essentials.recovery.failed_untouched": "Update could not run — the system was never touched.",
    "essentials.update_txn.web_shortcut_not_installable": (
        "Web services have no package to install/rollback on the NaMiOS side —"
        " no transaction run."
    ),
    "essentials.ring.retained_with_deadline": (
        "A critical service broke in lab ({services}) — stable keeps the old version"
        " until {deadline}, with a security-risk warning; NOT held indefinitely."
    ),
    "essentials.ring.no_deadline": (
        "NO DEADLINE SET (violation — a deadline must be set before retaining an old" " version)"
    ),
    "essentials.smartai.wine_pending_cert": (
        "The Windows app via Wine has not been certified for the new build yet — not"
        " updated until it passes lab/retest."
    ),
    "essentials.smartai.wine_certified_update": (
        "The Windows app via Wine is certified for the new build — recipe/runner" " can be updated."
    ),
    "essentials.smartai.vendor_web_service": (
        "This is a web service — the vendor updates it on their own server. NaMiOS"
        " only updates its own browser, integration manifest, and compatibility checks."
    ),
    "essentials.smartai.browser_manifest": (
        "NaMiOS can update: browser/engine + integration manifest."
    ),
    "essentials.smartai.native_package": (
        "Treated as a NaMiOS/distro native package — verify source/signature, then"
        " update via the Update Center."
    ),
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
