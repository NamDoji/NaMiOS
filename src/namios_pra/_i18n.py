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
    # Device Doctor (PRA-028)
    "pra.dev.healthy.cause": "Thiết bị phản hồi bình thường, chưa thấy lỗi.",
    "pra.dev.healthy.next": "Thử lại tác vụ; nếu vẫn lỗi, mô tả hiện tượng cụ thể hơn.",
    "pra.dev.offline.cause": "Máy không phản hồi (mất điện/rút cáp/rớt mạng).",
    "pra.dev.offline.next": "Kiểm tra nguồn + cáp USB/mạng của máy, bật lại rồi thử.",
    "pra.dev.out_of_paper.cause": "Máy báo hết giấy ở khay.",
    "pra.dev.out_of_paper.next": (
        "Nạp giấy đúng khổ vào khay rồi in lại — job vẫn còn trong hàng đợi."
    ),
    "pra.dev.job_jammed.cause": "Kẹt giấy/kẹt trang giữa chừng.",
    "pra.dev.job_jammed.next": (
        "Lấy giấy kẹt theo hướng dẫn trên máy; các trang ĐÃ xử lý được giữ, không mất."
    ),
    "pra.dev.mdns_blocked.cause": (
        "Máy có trên mạng nhưng VLAN/firewall chặn mDNS nên không tự thấy."
    ),
    "pra.dev.mdns_blocked.next": (
        "Cần IT bật mDNS reflector/đúng VLAN, hoặc thêm máy in theo IP/hàng đợi được cấp."
    ),
    "pra.dev.scan_backend_missing.cause": "Thiếu backend scan (eSCL/SANE) cho model này.",
    "pra.dev.scan_backend_missing.next": (
        "Cần cài backend/driver scan hợp lệ từ repo/vendor; in vẫn dùng được bình thường."
    ),
    "pra.dev.function_absent.cause": (
        "Chức năng '{func}' chưa được kiểm (hoặc máy không có) — KHÔNG kết luận là hỏng."
    ),
    "pra.dev.function_absent.next": (
        "Nếu là copy: dùng nút copy trên máy (NaMiOS không điều khiển); "
        "hoặc kiểm chức năng này trước."
    ),
    "pra.dev.unknown.cause": "Chưa đủ dấu hiệu để kết luận nguyên nhân.",
    "pra.dev.unknown.next": "Thu thêm thông tin (model, kết nối, chức năng đang lỗi) rồi chẩn lại.",
    # Network Doctor (PRA-029)
    "pra.net.healthy.cause": "Mạng phản hồi bình thường.",
    "pra.net.healthy.next": "Thử lại tác vụ cần mạng.",
    "pra.net.ssid_not_found.cause": "Không thấy mạng Wi‑Fi (SSID) trong danh sách quét.",
    "pra.net.ssid_not_found.next": "Lại gần điểm phát; kiểm 2.4/5GHz; bật lại Wi‑Fi rồi quét lại.",
    "pra.net.wrong_password.cause": "Sai mật khẩu / xác thực Wi‑Fi thất bại.",
    "pra.net.wrong_password.next": "Nhập lại đúng mật khẩu (hoặc hồ sơ 802.1X) rồi kết nối.",
    "pra.net.no_ip.cause": "Kết nối được nhưng không nhận địa chỉ IP (DHCP lỗi).",
    "pra.net.no_ip.next": "Cần IT kiểm DHCP/đặt IP tĩnh; thử quên mạng rồi vào lại.",
    "pra.net.captive_portal.cause": "Mạng yêu cầu đăng nhập qua trang cổng (captive portal).",
    "pra.net.captive_portal.next": "Mở trình duyệt, đăng nhập trang cổng để được cấp Internet.",
    "pra.net.dns_error.cause": "Có IP nhưng phân giải tên miền (DNS) lỗi.",
    "pra.net.dns_error.next": "Cần IT kiểm cấu hình DNS/proxy; thử đổi DNS được tổ chức cho phép.",
    "pra.net.proxy_vpn.cause": "Cần proxy/VPN nhưng chưa cấu hình đúng.",
    "pra.net.proxy_vpn.next": "Cần IT cấp hồ sơ proxy/VPN đúng chính sách rồi kết nối lại.",
    "pra.net.no_internet.cause": "Có IP + DNS nội bộ nhưng không ra được Internet.",
    "pra.net.no_internet.next": (
        "Cần IT/nhà mạng kiểm tuyến ra Internet (không chỉ khởi động router)."
    ),
    "pra.net.printer_off_network.cause": "Máy in không cùng mạng con với máy tính.",
    "pra.net.printer_off_network.next": (
        "Nối máy tính + máy in về cùng mạng/VLAN, hoặc thêm theo IP được cấp."
    ),
    "pra.net.unknown.cause": "Chưa đủ dấu hiệu để xác định lỗi mạng.",
    "pra.net.unknown.next": "Thu thêm trạng thái (SSID, IP, DNS, cổng) rồi chẩn lại.",
    # Office Doctor (PRA-030)
    "pra.officedoc.macro_web_blocked": (
        "File cần macro/add-in: KHÔNG dùng được Office web (VBA không chạy trên web)."
    ),
    "pra.officedoc.sensitive_no_upload": (
        "File có dữ liệu nhạy cảm: KHÔNG tự đẩy lên cloud — cần bạn xác nhận rõ nếu muốn dùng web."
    ),
    "pra.officedoc.windows_dep": "Tuyến này còn phụ thuộc Windows (VM/remote có phép).",
    # Windows App Doctor (PRA-031)
    "pra.appdoc.partial_db": (
        "App mở được GUI nhưng KHÔNG kết nối được CSDL → chỉ 'một phần' (partial_workflow), "
        "chưa phải 'dùng được'; không cho sửa dữ liệu thật."
    ),
    "pra.appdoc.partial_db.next": "Khôi phục kết nối CSDL/mạng rồi kiểm lại quy trình đầy đủ.",
    "pra.appdoc.portal_blocker": (
        "Token/thiết bị nhận được, nhưng cổng cần plugin/khóa-Windows → cả quy trình vẫn BLOCKED."
    ),
    "pra.appdoc.portal_blocker.next": (
        "Cần vendor/CA hỗ trợ Linux hoặc dùng Windows VM/remote có phép."
    ),
    "pra.appdoc.terminal": (
        "Đã thử {n}/{max} giả thuyết đều không đạt → DỪNG (không thử vô hạn); "
        "chuyển người xử lý phù hợp."
    ),
    "pra.appdoc.terminal.next": "Gửi gói lỗi đã che dữ liệu cho IT/vendor theo blocker cụ thể.",
    "pra.appdoc.need_rollback": "Giả thuyết thiếu bước hoàn tác (rollback) → không được áp dụng.",
    # Permission (PRA-034)
    "pra.perm.untrusted": (
        "Nguồn không tin cậy (tài liệu/web/log) KHÔNG cấp được quyền mới cho AI — bỏ qua yêu cầu."
    ),
    "pra.perm.transact_confirm": (
        "Việc ký/nộp/thanh toán cần BẠN xác nhận hành động cụ thể (không cấp quyền chung)."
    ),
    "pra.perm.granted": "Đã cấp quyền '{scope}' cho hành động '{action}' (có thời hạn + hoàn tác).",
    "pra.perm.policy_deny": "Chính sách tổ chức không cho phép '{action}'.",
    # Offline (PRA-035)
    "pra.offline.print": "In tài liệu",
    "pra.offline.scan": "Quét tài liệu",
    "pra.offline.wifi": "Kết nối Wi‑Fi/mạng",
    "pra.offline.open_offline_app": "Mở app offline (Office native, trình duyệt)",
    "pra.offline.local_catalog": "Tra danh mục + checklist cục bộ",
    "pra.offline.local_diag": "Chẩn đoán cơ bản bằng metadata cục bộ",
    "pra.offline.cloud_reasoning": "Trợ lý AI suy luận nâng cao (cần model cloud)",
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
    # Device Doctor (PRA-028)
    "pra.dev.healthy.cause": "Device responds normally, no fault seen.",
    "pra.dev.healthy.next": (
        "Retry the task; if it still fails, describe the symptom more specifically."
    ),
    "pra.dev.offline.cause": "Device does not respond (power/cable/network lost).",
    "pra.dev.offline.next": (
        "Check the device's power + USB/network cable, power-cycle, then retry."
    ),
    "pra.dev.out_of_paper.cause": "Device reports the paper tray is empty.",
    "pra.dev.out_of_paper.next": (
        "Load the correct paper size and reprint — the job stays in the queue."
    ),
    "pra.dev.job_jammed.cause": "Paper/page jam mid-job.",
    "pra.dev.job_jammed.next": (
        "Clear the jam per the on-device guide; already-processed pages are kept."
    ),
    "pra.dev.mdns_blocked.cause": (
        "Device is on the network but VLAN/firewall blocks mDNS discovery."
    ),
    "pra.dev.mdns_blocked.next": (
        "IT must enable an mDNS reflector/correct VLAN, or add the printer by IP/assigned queue."
    ),
    "pra.dev.scan_backend_missing.cause": "Missing scan backend (eSCL/SANE) for this model.",
    "pra.dev.scan_backend_missing.next": (
        "Install a valid scan backend/driver from repo/vendor; printing still works."
    ),
    "pra.dev.function_absent.cause": (
        "Function '{func}' is not tested (or the device lacks it) — do NOT conclude it is broken."
    ),
    "pra.dev.function_absent.next": (
        "For copy: use the copy button on the device (NaMiOS does not drive it); "
        "or test this function first."
    ),
    "pra.dev.unknown.cause": "Not enough signals to conclude a cause.",
    "pra.dev.unknown.next": (
        "Gather more info (model, connection, failing function) and re-diagnose."
    ),
    # Network Doctor (PRA-029)
    "pra.net.healthy.cause": "Network responds normally.",
    "pra.net.healthy.next": "Retry the network task.",
    "pra.net.ssid_not_found.cause": "Wi‑Fi network (SSID) not found in the scan.",
    "pra.net.ssid_not_found.next": "Move closer; check 2.4/5GHz; toggle Wi‑Fi and rescan.",
    "pra.net.wrong_password.cause": "Wrong password / Wi‑Fi authentication failed.",
    "pra.net.wrong_password.next": (
        "Re-enter the correct password (or 802.1X profile) and connect."
    ),
    "pra.net.no_ip.cause": "Associated but got no IP address (DHCP failure).",
    "pra.net.no_ip.next": "IT should check DHCP/assign a static IP; try forgetting and rejoining.",
    "pra.net.captive_portal.cause": "The network requires sign-in via a captive portal.",
    "pra.net.captive_portal.next": "Open a browser and sign in to the portal to get Internet.",
    "pra.net.dns_error.cause": "Has an IP but domain-name resolution (DNS) fails.",
    "pra.net.dns_error.next": "IT should check DNS/proxy config; try an org-approved DNS.",
    "pra.net.proxy_vpn.cause": "A proxy/VPN is required but not configured correctly.",
    "pra.net.proxy_vpn.next": "IT should provision the correct proxy/VPN profile, then reconnect.",
    "pra.net.no_internet.cause": "Has IP + internal DNS but no route out to the Internet.",
    "pra.net.no_internet.next": (
        "IT/ISP should check the Internet uplink (not just restart the router)."
    ),
    "pra.net.printer_off_network.cause": "The printer is not on the same subnet as the computer.",
    "pra.net.printer_off_network.next": (
        "Put computer + printer on the same network/VLAN, or add by assigned IP."
    ),
    "pra.net.unknown.cause": "Not enough signals to determine the network fault.",
    "pra.net.unknown.next": "Gather more status (SSID, IP, DNS, gateway) and re-diagnose.",
    # Office Doctor (PRA-030)
    "pra.officedoc.macro_web_blocked": (
        "File needs macro/add-in: Office web is NOT usable (VBA does not run on the web)."
    ),
    "pra.officedoc.sensitive_no_upload": (
        "File has sensitive data: it is NOT auto-uploaded to cloud — "
        "explicit confirmation needed for web."
    ),
    "pra.officedoc.windows_dep": "This route is still Windows-dependent (licensed VM/remote).",
    # Windows App Doctor (PRA-031)
    "pra.appdoc.partial_db": (
        "App launches its GUI but CANNOT connect to the database → only 'partial_workflow', "
        "not 'usable'; do not edit real data."
    ),
    "pra.appdoc.partial_db.next": (
        "Restore the database/network connection, then re-check the full workflow."
    ),
    "pra.appdoc.portal_blocker": (
        "Token/device detected, but the portal needs a Windows-locked plugin → "
        "the whole workflow is BLOCKED."
    ),
    "pra.appdoc.portal_blocker.next": (
        "Need vendor/CA Linux support, or use a licensed Windows VM/remote."
    ),
    "pra.appdoc.terminal": (
        "Tried {n}/{max} hypotheses, none worked → STOP (no infinite retry); "
        "hand off to the right role."
    ),
    "pra.appdoc.terminal.next": (
        "Send the redacted error bundle to IT/vendor per the specific blocker."
    ),
    "pra.appdoc.need_rollback": "Hypothesis lacks a rollback step → it must not be applied.",
    # Permission (PRA-034)
    "pra.perm.untrusted": (
        "Untrusted sources (document/web/log) CANNOT grant the AI new permissions — "
        "request ignored."
    ),
    "pra.perm.transact_confirm": (
        "Signing/submitting/paying needs YOUR specific action confirmation (no blanket grant)."
    ),
    "pra.perm.granted": (
        "Granted '{scope}' permission for action '{action}' (time-bound + undoable)."
    ),
    "pra.perm.policy_deny": "Org policy does not allow '{action}'.",
    # Offline (PRA-035)
    "pra.offline.print": "Print documents",
    "pra.offline.scan": "Scan documents",
    "pra.offline.wifi": "Connect Wi‑Fi/network",
    "pra.offline.open_offline_app": "Open offline apps (native Office, browser)",
    "pra.offline.local_catalog": "Browse local catalog + checklists",
    "pra.offline.local_diag": "Basic diagnosis via local metadata",
    "pra.offline.cloud_reasoning": "Advanced AI reasoning assistant (needs cloud model)",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
