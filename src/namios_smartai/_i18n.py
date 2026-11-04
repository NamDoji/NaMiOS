"""Lớp common song ngữ của SmartAI (Phụ lục 04) — đăng ký qua
``namios_i18n.add_catalog`` khi import (giống ``namios_compat._i18n``).

Trường DỮ LIỆU ``*_vi`` luôn tiếng Việt (call-site ép ``lang=Lang.VI``); chỉ
help/usage CLI đổi theo ``--lang``. Module dùng ``t("sai.*")`` phải import
module này: ``from namios_smartai import _i18n as _i18n``.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # state machine (SAI-003)
    "sai.state.error.invalid_transition": ("Chuyển trạng thái không hợp lệ: '{frm}' → '{to}'."),
    "sai.state.error.from_terminal": (
        "Task đã ở trạng thái cuối '{frm}' — không chuyển tiếp được."
    ),
    # policy-as-code (SAI-039 / SAI-017)
    "sai.policy.allow.default": "Cho phép: {action} (bậc {risk}).",
    "sai.policy.deny.rule": "Bị chặn bởi luật '{rule_id}': {action}.",
    "sai.policy.deny.default": "Mặc định chặn: {action} (không có luật cho phép).",
    "sai.policy.deny.r4_needs_transaction": (
        "Hành động R4 (ký/nộp/thanh toán) PHẢI có xác nhận GIAO DỊCH cụ thể "
        "(nội dung + chủ thể) — một câu 'cứ làm đi' không thay thế được."
    ),
    "sai.policy.deny.consent_required": (
        "Hành động '{action}' (bậc {risk}) cần sự chấp thuận người dùng theo phạm vi."
    ),
    "sai.policy.deny.risk_exceeds_consent": (
        "Bậc rủi ro {risk} vượt quá phạm vi đã được chấp thuận."
    ),
    "sai.policy.deny.target_changed": (
        "Mục tiêu đã đổi so với lúc cấp phép → sự chấp thuận cũ vô hiệu, cần xác nhận lại."
    ),
    "sai.policy.deny.capability_missing": (
        "Thiếu capability token cho hành động ghi/thực thi '{action}'."
    ),
    # tool broker (SAI-015/040/016)
    "sai.tool.error.unknown": "Tool '{tool}' không có trong Tool Registry — từ chối.",
    "sai.tool.error.schema": "Tham số tool '{tool}' ngoài schema / thiếu: {detail}.",
    "sai.tool.error.scope": "Tool '{tool}' truy cập ngoài phạm vi cho phép: {detail}.",
    "sai.tool.error.cap_expired": "Capability token hết hạn / đã thu hồi / đã dùng (one-time).",
    "sai.tool.error.cap_scope": "Capability token không phủ phạm vi yêu cầu: {detail}.",
    "sai.tool.ok": "Tool '{tool}' chạy xong (mock M0).",
    # injection defense (SAI-019)
    "sai.injection.blocked": (
        "Nội dung không tin cậy chứa mưu đồ điều khiển (prompt-injection) — coi là "
        "DỮ LIỆU, không thực thi: {detail}."
    ),
    # orchestrator — giao dịch thật R4 (SAI-022)
    "sai.orchestrator.external_transaction": (
        "Hành động giao dịch thật (ký/nộp/thanh toán) cần cổng/sandbox chính thức — "
        "Giai đoạn M3. M0 KHÔNG thực thi và KHÔNG sinh biên nhận giả; đã dừng an toàn."
    ),
    # intent (SAI-001)
    "sai.intent.need_info": ("Chưa đủ thông tin để thực hiện an toàn — cần làm rõ: {unknowns}."),
    "sai.intent.low_confidence": (
        "Mức chắc chắn thấp khi hiểu yêu cầu — xin xác nhận lại mục tiêu."
    ),
    # M1 — triage lỗi (SAI-009) — nhãn DỮ LIỆU (VI)
    "sai.triage.cat.missing_runtime": "Thiếu runtime/thư viện (vd .dll/.NET/VC++).",
    "sai.triage.cat.unsupported_api": "Gọi API Windows chưa hỗ trợ (Wine/nền tảng).",
    "sai.triage.cat.db_unreachable": "Không kết nối được cơ sở dữ liệu/dịch vụ.",
    "sai.triage.cat.device_missing": "Thiếu thiết bị/driver (máy in/scanner/token).",
    "sai.triage.cat.portal_plugin": "Cổng/web cần plugin/middleware chỉ-Windows.",
    "sai.triage.cat.license": "Vấn đề giấy phép/kích hoạt bản quyền.",
    "sai.triage.cat.data_mismatch": "Dữ liệu đầu ra sai lệch (số tiền/trang/định dạng).",
    "sai.triage.cat.unknown": "Chưa đủ dấu hiệu để phân loại — để 'chưa rõ'.",
    # M1 — chẩn đoán tổng hợp (SAI-006/007/008)
    "sai.diagnose.execute_blocked": (
        "Bước execute BỊ CHẶN: phụ thuộc bắt buộc chưa sẵn sàng ({blockers}) — "
        "KHÔNG coi là hoàn thành."
    ),
    "sai.diagnose.no_verified_route": (
        "Workflow '{workflow_id}': chưa có đường chạy kiểm chứng — không kết luận chạy được."
    ),
    "sai.diagnose.suggested.vendor": (
        "Chuẩn bị gói báo cáo vendor (thiếu SDK/driver/plugin Linux) — chờ người duyệt gửi."
    ),
    "sai.diagnose.suggested.route": "Đề xuất điều tra mode '{mode}' (có chứng cứ khả thi).",
    "sai.diagnose.suggested.gather": "Cần bổ sung thông tin/môi trường thật trước khi kết luận.",
    # M2 — tự sửa có giới hạn (SAI-010/011/012)
    "sai.repair.stop.success": "Tìm được cách sửa (ứng viên công thức, mặc định experimental).",
    "sai.repair.stop.data_wrong": "DỪNG: phép thử làm sai dữ liệu — không tiếp tục.",
    "sai.repair.stop.missing_license": ("DỪNG: thiếu giấy phép hợp lệ — cần người/đơn vị cấp."),
    "sai.repair.stop.security": "DỪNG: phát hiện rủi ro bảo mật — không tiếp tục.",
    "sai.repair.stop.needs_vendor": (
        "DỪNG: cần nhà cung cấp (SDK/driver/API) — vượt phạm vi tự sửa."
    ),
    "sai.repair.stop.budget_exceeded": "DỪNG: vượt ngân sách (số phép thử/bước) — dừng an toàn.",
    "sai.repair.stop.all_candidates_failed": (
        "DỪNG: mọi ứng viên đều fail — không retry vô hạn, nêu lý do."
    ),
    "sai.promotion.denied.no_evidence": (
        "Không nâng trạng thái: thiếu bằng chứng tool hợp lệ (SAI-012)."
    ),
    "sai.promotion.denied.ai_label": (
        "Không nâng trạng thái: AI sửa nhãn trong output KHÔNG nâng được (SAI-012/030)."
    ),
    "sai.promotion.denied.business": (
        "Không publish: tác vụ kế toán/thuế/BHXH cần xác nhận nghiệp vụ + end-to-end (ECO/COMP)."
    ),
    "sai.promotion.denied.reviewer": "Không publish: thiếu người thẩm quyền duyệt.",
    "sai.promotion.needs_retest": (
        "Chuyển needs_retest: thành phần đổi / evidence quá hạn / nguồn không hợp lệ (SAI-033/042)."
    ),
    "sai.recipe.error.missing_source": "Recipe thiếu source_url chính thức — không thể publish.",
    "sai.recipe.error.missing_hash": "Recipe thiếu app_hash — không thể publish.",
    "sai.recipe.error.missing_rollback": (
        "Recipe đổi hệ thống nhưng thiếu rollback — không thể publish."
    ),
    "sai.recipe.error.arch_mismatch": (
        "Recipe kiến trúc '{recipe_arch}' KHÔNG tự áp cho '{target_arch}'."
    ),
    # M3/M4 — quản trị & kiểm soát an toàn (SAI-014/022/035/037)
    "sai.killswitch.off": "{target} đang bị TẮT (kill switch) — hành động bị chặn an toàn.",
    "sai.killswitch.release_blocked": (
        "Phát hiện sai dữ liệu/ghi file/chữ ký → TỰ CHẶN phát hành kế tiếp (SAI-035)."
    ),
    "sai.admin.denied_policy": "Không có quyền sửa chính sách của đơn vị '{unit}'.",
    "sai.admin.denied_logs": "Không có quyền đọc log của đơn vị '{unit}'.",
    "sai.vendorpack.secret_blocked": (
        "Gói vendor sẽ chứa secret/dữ liệu sản xuất — CHẶN tạo (SAI-014)."
    ),
    "sai.submission.needs_lookup": (
        "Mất mạng/phản hồi mơ hồ sau khi gửi — CẦN TRA CỨU biên nhận, KHÔNG tự gửi lại (SAI-022)."
    ),
    "sai.submission.not_confirmed": "Chưa có biên nhận được kiểm — chưa coi là hoàn thành.",
    # Knowledge Base có nguồn (SAI-025) — nhãn DỮ LIỆU (VI)
    "sai.kb.verified": (
        "Đã kiểm (chứng nhận NaMiOS): {app} {version} — workflow chạy đúng (ngày {as_of})."
    ),
    "sai.kb.partial": (
        "Đã kiểm (chứng nhận NaMiOS): {app} {version} — chạy MỘT PHẦN, còn hạn chế (ngày {as_of})."
    ),
    "sai.kb.failed": (
        "Đã kiểm (chứng nhận NaMiOS): {app} {version} — KHÔNG chạy đúng (ngày {as_of})."
    ),
    "sai.kb.untested": (
        "Chưa kiểm: NaMiOS chưa kiểm chứng {app} {version} — không kết luận chạy được."
    ),
    "sai.kb.untested_doc": (
        "Chưa kiểm trên NaMiOS: {app} {version} mới chỉ có tài liệu chính thức tham khảo "
        "(ngày {as_of}) — chưa chạy thử để kết luận."
    ),
    "sai.kb.untested_community": (
        "Chưa kiểm: {app} {version} chỉ có ghi nhận cộng đồng CHƯA kiểm — tham khảo, "
        "KHÔNG dùng để cài driver hay kết luận chạy được."
    ),
    "sai.kb.untested_ai": (
        "Chưa kiểm: {app} {version} mới chỉ có suy luận AI — KHÔNG phải sự thật, cần kiểm chứng."
    ),
    "sai.kb.stale_suffix": " (thông tin có thể đã cũ — nên kiểm lại).",
    # Human Feedback (SAI-029)
    "sai.feedback.not_certification": (
        "Phản hồi người dùng KHÔNG phải chứng nhận — chỉ gợi ý test case, "
        "KHÔNG nâng trạng thái workflow_verified."
    ),
    "sai.feedback.suggest.repro": (
        "Gợi ý test case tái hiện: '{summary}' (workflow {workflow_id}, bản {version}) "
        "— từ phản hồi chưa giải quyết."
    ),
    "sai.feedback.suggest.regression": (
        "Gợi ý test case hồi quy: xác nhận '{summary}' thực sự ổn "
        "(workflow {workflow_id}, bản {version})."
    ),
    # CLI (song ngữ theo --lang)
    "sai.cli.parser.cmd_help": (
        "SmartAI: biến yêu cầu tiếng Việt thành kế hoạch có kiểm soát (plan/policy/tool)."
    ),
    "sai.cli.parser.plan_help": "Lập kế hoạch cho một yêu cầu tiếng Việt (chưa thực thi).",
    "sai.cli.parser.arg.intent": "Mô tả việc muốn làm bằng tiếng Việt.",
    "sai.cli.parser.tools_help": "Liệt kê các tool đã đăng ký + bậc rủi ro + phạm vi.",
    "sai.cli.parser.diagnose_help": (
        "Chẩn đoán một lỗi tương thích (phân loại + redact secret + đề xuất) — chưa sửa."
    ),
    "sai.cli.parser.arg.symptom": "Mô tả lỗi/triệu chứng (log, exit code, bước gặp lỗi).",
    "sai.cli.parser.recipecheck_help": (
        "Kiểm một recipe tương thích đã đủ điều kiện publish chưa (SAI-041) — chưa publish."
    ),
    "sai.cli.parser.arg.recipe_path": "Đường dẫn file recipe JSON.",
    "sai.cli.error.recipe_load": "Không đọc được recipe JSON '{path}': {reason}.",
}

_EN: dict[str, str] = {
    "sai.state.error.invalid_transition": "Invalid status transition: '{frm}' → '{to}'.",
    "sai.state.error.from_terminal": (
        "Task is already in terminal status '{frm}' — cannot transition further."
    ),
    "sai.policy.allow.default": "Allow: {action} (tier {risk}).",
    "sai.policy.deny.rule": "Blocked by rule '{rule_id}': {action}.",
    "sai.policy.deny.default": "Default deny: {action} (no allow rule matched).",
    "sai.policy.deny.r4_needs_transaction": (
        "An R4 action (sign/submit/pay) MUST have a specific TRANSACTION confirmation "
        "(content + subject) — a blanket 'just do it' does not substitute."
    ),
    "sai.policy.deny.consent_required": (
        "Action '{action}' (tier {risk}) needs scoped user consent."
    ),
    "sai.policy.deny.risk_exceeds_consent": "Risk tier {risk} exceeds the consented scope.",
    "sai.policy.deny.target_changed": (
        "Target changed since consent was granted → old consent is void, reconfirm needed."
    ),
    "sai.policy.deny.capability_missing": (
        "Missing capability token for the write/execute action '{action}'."
    ),
    "sai.tool.error.unknown": "Tool '{tool}' is not in the Tool Registry — refused.",
    "sai.tool.error.schema": "Tool '{tool}' params out of schema / missing: {detail}.",
    "sai.tool.error.scope": "Tool '{tool}' accessed outside the allowed scope: {detail}.",
    "sai.tool.error.cap_expired": "Capability token expired / revoked / already used (one-time).",
    "sai.tool.error.cap_scope": "Capability token does not cover the requested scope: {detail}.",
    "sai.tool.ok": "Tool '{tool}' finished (M0 mock).",
    "sai.injection.blocked": (
        "Untrusted content contains control directives (prompt-injection) — treated as "
        "DATA, not executed: {detail}."
    ),
    "sai.orchestrator.external_transaction": (
        "A real transaction (sign/submit/pay) needs an official portal/sandbox — Phase M3. "
        "M0 does NOT execute it and does NOT fabricate a receipt; stopped safely."
    ),
    "sai.intent.need_info": "Not enough information to proceed safely — clarify: {unknowns}.",
    "sai.intent.low_confidence": "Low confidence understanding the request — please reconfirm.",
    "sai.triage.cat.missing_runtime": "Missing runtime/library (e.g. .dll/.NET/VC++).",
    "sai.triage.cat.unsupported_api": "Unsupported Windows API call (Wine/platform).",
    "sai.triage.cat.db_unreachable": "Cannot reach the database/service.",
    "sai.triage.cat.device_missing": "Missing device/driver (printer/scanner/token).",
    "sai.triage.cat.portal_plugin": "Portal/web needs a Windows-only plugin/middleware.",
    "sai.triage.cat.license": "License/activation problem.",
    "sai.triage.cat.data_mismatch": "Output data mismatch (amount/pages/format).",
    "sai.triage.cat.unknown": "Not enough signal to classify — left as 'unknown'.",
    "sai.diagnose.execute_blocked": (
        "Execute step BLOCKED: required dependency not ready ({blockers}) — NOT complete."
    ),
    "sai.diagnose.no_verified_route": (
        "Workflow '{workflow_id}': no verified route yet — do not conclude it works."
    ),
    "sai.diagnose.suggested.vendor": (
        "Prepare a vendor report pack (missing Linux SDK/driver/plugin) — await reviewer to send."
    ),
    "sai.diagnose.suggested.route": "Suggest investigating mode '{mode}' (has feasible evidence).",
    "sai.diagnose.suggested.gather": "Gather more info / a real environment before concluding.",
    "sai.repair.stop.success": "Found a fix (recipe candidate, default experimental).",
    "sai.repair.stop.data_wrong": "STOP: a trial corrupted data — do not continue.",
    "sai.repair.stop.missing_license": (
        "STOP: missing a valid license — needs a person/unit to grant."
    ),
    "sai.repair.stop.security": "STOP: a security risk was detected — do not continue.",
    "sai.repair.stop.needs_vendor": "STOP: needs the vendor (SDK/driver/API) — beyond self-repair.",
    "sai.repair.stop.budget_exceeded": "STOP: budget exceeded (trials/steps) — stopped safely.",
    "sai.repair.stop.all_candidates_failed": (
        "STOP: all candidates failed — no infinite retry, reason stated."
    ),
    "sai.promotion.denied.no_evidence": "Not promoted: missing valid tool evidence (SAI-012).",
    "sai.promotion.denied.ai_label": (
        "Not promoted: an AI label edit in the output CANNOT promote (SAI-012/030)."
    ),
    "sai.promotion.denied.business": (
        "Not published: accounting/tax/social-insurance tasks need business + end-to-end "
        "confirmation (ECO/COMP)."
    ),
    "sai.promotion.denied.reviewer": "Not published: missing an authorized reviewer.",
    "sai.promotion.needs_retest": (
        "Set needs_retest: a component changed / evidence expired / source invalid (SAI-033/042)."
    ),
    "sai.recipe.error.missing_source": "Recipe missing an official source_url — cannot publish.",
    "sai.recipe.error.missing_hash": "Recipe missing app_hash — cannot publish.",
    "sai.recipe.error.missing_rollback": (
        "Recipe changes the system but has no rollback — cannot publish."
    ),
    "sai.recipe.error.arch_mismatch": (
        "Recipe architecture '{recipe_arch}' does NOT auto-apply to '{target_arch}'."
    ),
    "sai.killswitch.off": "{target} is TURNED OFF (kill switch) — action blocked safely.",
    "sai.killswitch.release_blocked": (
        "Bad data/file-write/signature detected → AUTO-BLOCK the next release (SAI-035)."
    ),
    "sai.admin.denied_policy": "No permission to edit unit '{unit}' policy.",
    "sai.admin.denied_logs": "No permission to read unit '{unit}' logs.",
    "sai.vendorpack.secret_blocked": (
        "The vendor pack would contain secrets/production data — creation BLOCKED (SAI-014)."
    ),
    "sai.submission.needs_lookup": (
        "Network loss/ambiguous response after submit — LOOK UP the receipt, do NOT auto-resend "
        "(SAI-022)."
    ),
    "sai.submission.not_confirmed": "No verified receipt yet — not counted as complete.",
    "sai.kb.verified": (
        "Tested (NaMiOS certification): {app} {version} — workflow runs correctly (as of {as_of})."
    ),
    "sai.kb.partial": (
        "Tested (NaMiOS certification): {app} {version} — runs PARTIALLY, with limits "
        "(as of {as_of})."
    ),
    "sai.kb.failed": (
        "Tested (NaMiOS certification): {app} {version} — does NOT run correctly (as of {as_of})."
    ),
    "sai.kb.untested": (
        "Not tested: NaMiOS has not certified {app} {version} — cannot conclude it works."
    ),
    "sai.kb.untested_doc": (
        "Not tested on NaMiOS: {app} {version} only has official reference docs (as of {as_of}) "
        "— not yet run to conclude."
    ),
    "sai.kb.untested_community": (
        "Not tested: {app} {version} only has UNVERIFIED community notes — for reference, "
        "do NOT use to install drivers or conclude it works."
    ),
    "sai.kb.untested_ai": (
        "Not tested: {app} {version} only has AI inference — NOT ground truth, needs verification."
    ),
    "sai.kb.stale_suffix": " (info may be stale — recommend re-testing).",
    "sai.feedback.not_certification": (
        "User feedback is NOT a certification — it only suggests test cases, "
        "it does NOT raise the workflow_verified status."
    ),
    "sai.feedback.suggest.repro": (
        "Repro test-case suggestion: '{summary}' (workflow {workflow_id}, build {version}) "
        "— from unresolved feedback."
    ),
    "sai.feedback.suggest.regression": (
        "Regression test-case suggestion: confirm '{summary}' truly holds "
        "(workflow {workflow_id}, build {version})."
    ),
    "sai.cli.parser.cmd_help": (
        "SmartAI: turn a Vietnamese request into a controlled plan (plan/policy/tool)."
    ),
    "sai.cli.parser.plan_help": "Plan a Vietnamese request (no execution).",
    "sai.cli.parser.arg.intent": "Describe the task you want, in Vietnamese.",
    "sai.cli.parser.tools_help": "List registered tools + risk tier + scope.",
    "sai.cli.parser.diagnose_help": (
        "Diagnose a compatibility error (classify + redact secrets + suggest) — no fix."
    ),
    "sai.cli.parser.arg.symptom": "Describe the error/symptom (log, exit code, failing step).",
    "sai.cli.parser.recipecheck_help": (
        "Check whether a compatibility recipe is publishable (SAI-041) — does not publish."
    ),
    "sai.cli.parser.arg.recipe_path": "Path to a recipe JSON file.",
    "sai.cli.error.recipe_load": "Could not read recipe JSON '{path}': {reason}.",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
