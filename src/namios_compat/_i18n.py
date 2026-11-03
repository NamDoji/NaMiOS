"""Lớp common song ngữ của Trung tâm tương thích (Phụ lục 03).

MỘT nơi duy nhất chứa mọi chuỗi ``compat.*`` (VN + EN) — đăng ký qua
``namios_i18n.add_catalog`` NGAY khi import module này (giống
``namios_cli.parser``), KHÔNG sửa trực tiếp ``namios_i18n/locale/*.json``
(để không vỡ test parity vốn chỉ soi 2 file JSON đó). "Sửa 1 chỗ dùng cả hệ
thống": đổi câu chữ ở đây là mọi module/CLI đổi theo.

Quy ước (giống ``namios_eco``/``namios_cli``): các trường DỮ LIỆU ``*_vi``
(``reasons_vi``/``message_vi``/``evidence_vi``/``notes_vi``) LUÔN tiếng Việt
— call-site ép ``lang=Lang.VI``. Chỉ lớp help/usage CLI mới đổi theo
``--lang``/``NAMIOS_LANG``. Bản EN tồn tại để giữ parity + phục vụ UI tương
lai.

Mọi module ``namios_compat`` gọi ``t("compat.*")`` PHẢI import module này để
bảo đảm catalog đã đăng ký: ``from namios_compat import _i18n as _i18n``
(``add_catalog`` idempotent — import nhiều lần vô hại).
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # --- resolver (COMP-025) ---
    "compat.resolver.reason.no_verified_route": (
        "Không có đường chạy nào đã kiểm chứng end-to-end cho workflow bắt buộc "
        "'{workflow_id}' — KHÔNG kết luận là chạy được."
    ),
    "compat.resolver.reason.recommended": (
        "Đề xuất mode '{mode}': đã workflow_verified và khả thi trong ngữ cảnh hiện tại."
    ),
    "compat.resolver.reason.cert_stale_app": (
        "Chứng nhận mất hiệu lực — phiên bản app '{got}' khác bản đã chứng nhận "
        "'{want}'; cần tái kiểm, KHÔNG giữ verified bằng metadata cũ."
    ),
    "compat.resolver.reason.cert_stale_token": (
        "Chứng nhận ký số mất hiệu lực — token '{token}' không thuộc model đã "
        "chứng nhận; cần tái kiểm."
    ),
    "compat.resolver.reason.mode_verified": "Mode '{mode}': đã workflow_verified.",
    "compat.resolver.reason.mode_partial": (
        "Mode '{mode}': mới partial_workflow — chưa đủ bằng chứng end-to-end."
    ),
    "compat.resolver.reason.mode_not_inventoried": "Mode '{mode}': chưa khảo sát.",
    "compat.resolver.reason.mode_blocked": "Mode '{mode}': bị chặn bởi phụ thuộc ngoài.",
    "compat.resolver.reason.mode_unsupported": "Mode '{mode}': đã xác định không hỗ trợ.",
    "compat.resolver.reason.mode_never_usable": (
        "Mode '{mode}': chỉ tải/mở được, KHÔNG tính là dùng được (GATE ECO-003)."
    ),
    "compat.resolver.reason.infeasible_license": (
        "Mode '{mode}' cần giấy phép Windows/ứng dụng hợp lệ — hiện chưa có."
    ),
    "compat.resolver.reason.infeasible_network": "Mode '{mode}' cần mạng — hiện đang offline.",
    "compat.resolver.reason.infeasible_policy": (
        "Mode '{mode}' (Windows từ xa/VM) cần đơn vị quản trị cho phép — chính sách chưa duyệt."
    ),
    "compat.resolver.reason.no_route_for_mode": (
        "Mode '{mode}': không có trong hồ sơ route của workflow."
    ),
    # --- schema (COMP-048) — dùng làm ValidationError.message_vi ---
    "compat.schema.error.schema_version": "schema_version phải là '{want}', nhận '{got}'.",
    "compat.schema.error.required_steps": (
        "required_steps phải đúng 7 nấc ECO-001 theo thứ tự chuẩn (discover→…→verify_result)."
    ),
    "compat.schema.error.enum_invalid": "Giá trị '{value}' không hợp lệ cho trường '{field}'.",
    "compat.schema.error.missing_field": "Thiếu trường bắt buộc '{field}'.",
    "compat.schema.error.type_invalid": "Trường '{field}' sai kiểu dữ liệu.",
    "compat.schema.error.cert_tested_at_missing": (
        "Chứng nhận tự nhận {claim} nhưng thiếu tested_at — không chấp nhận metadata trống."
    ),
    "compat.schema.error.cert_evidence_missing": (
        "Chứng nhận tự nhận {claim} nhưng thiếu evidence cho nấc bắt buộc: {missing}."
    ),
    "compat.schema.error.vendor_claim": (
        "vendor_support=supported nhưng không có bằng chứng — không tự nhận nhà cung cấp hỗ trợ."
    ),
    "compat.schema.error.cert_revoked_usable": (
        "Chứng nhận revoked nhưng route vẫn gán trạng thái dùng được — không hợp lệ."
    ),
    "compat.schema.error.cert_version_unpinned": (
        "Chứng nhận tự nhận {claim} nhưng app.version chưa chốt ('{version}') — "
        "không thể verified khi version chưa pin."
    ),
    "compat.schema.error.date_format": (
        "Trường '{field}' phải là ngày ISO-8601 hợp lệ (YYYY-MM-DD), nhận '{value}'."
    ),
    "compat.schema.error.pack_secret": (
        "Workflow pack chứa trường nhạy cảm bị cấm '{field}' (đăng nhập/cookie/PIN/secret)."
    ),
    "compat.schema.error.pack_executable": (
        "Workflow pack chứa khóa thực thi bị cấm '{field}' (command/argv/script…)."
    ),
    # --- evidence gate (COMP-049) ---
    "compat.evidence.reason.revoked": "Chứng nhận đã bị thu hồi (revoked) — không dùng được.",
    "compat.evidence.reason.business_unreviewed": (
        "Kỹ thuật đạt nhưng nghiệp vụ CHƯA duyệt → giữ ở partial_workflow (COMP-052)."
    ),
    "compat.evidence.reason.business_rejected": (
        "Nghiệp vụ TỪ CHỐI kết quả → không nâng workflow_verified."
    ),
    "compat.evidence.reason.cert_expired": (
        "Chứng nhận quá hạn tái kiểm ({recertify_by}) → needs_retest, giữ ở partial_workflow."
    ),
    "compat.evidence.error.missing_field": "Bằng chứng thiếu trường bắt buộc '{field}'.",
    "compat.evidence.error.production_needs_reviewer": (
        "Bằng chứng production cho nấc '{step}' phải có người vai-trò-nghiệp-vụ xác nhận."
    ),
    "compat.evidence.error.hash_format": (
        "fixture_hash phải dạng 'sha256:<hex>' — nhận '{value}'."
    ),
    # --- classifier (COMP-028) ---
    "compat.classifier.disclaimer": (
        "Phân loại TĨNH (không chạy binary); nhãn là phát hiện/suy đoán/chưa rõ, "
        "KHÔNG phải kết luận tương thích."
    ),
    "compat.classifier.evidence.kernel_driver": (
        "Dấu hiệu driver nhân Windows → KHÓA đường Wine (cần vendor hoặc VM/remote)."
    ),
    "compat.classifier.evidence.anticheat": ("Dấu hiệu anti-cheat/DRM cấp nhân → KHÓA đường Wine."),
    "compat.classifier.evidence.dotnet_modern": (
        "Dấu hiệu .NET đa nền tảng hiện đại (TFM net≥5) → có thể chạy native Linux."
    ),
    "compat.classifier.evidence.dotnet_framework": (
        "Dấu hiệu .NET Framework/desktop (WinForms/WPF) → chỉ Windows, thử Wine."
    ),
    "compat.classifier.evidence.native_win32": (
        "PE native Windows (không .NET) → thử Wine; KHÔNG suy từ đuôi .exe."
    ),
    "compat.classifier.evidence.webview2": (
        "Phụ thuộc WebView2 → cần runtime Windows/Edge, kiểm riêng."
    ),
    "compat.classifier.evidence.sqlserver_client": (
        "Phụ thuộc SQL Server client → cần cấu hình DB đúng phiên bản (COMP-038)."
    ),
    "compat.classifier.evidence.unknown": (
        "Không đủ dấu hiệu để phân loại chắc chắn — để 'chưa rõ'."
    ),
    # --- device registry (COMP-032/036) ---
    "compat.device.refuse_carryover": (
        "Model '{model}' chưa test riêng; không suy ra từ model khác cùng hãng '{vendor}'."
    ),
    "compat.device.refuse_untested_function": (
        "Chức năng '{function}' chưa được test trên model '{model}'."
    ),
    "compat.device.ok_tested": "Model '{model}': chức năng '{function}' đã test qua {protocol}.",
    # --- CLI help/usage (song ngữ theo --lang) ---
    "compat.cli.parser.cmd_help": (
        "Trung tâm tương thích: tra workflow, giải thích route, preflight, evidence, blocker."
    ),
    "compat.cli.parser.workflows_help": (
        "Liệt kê workflow tương thích đã khảo sát + trạng thái thật."
    ),
    "compat.cli.parser.route_help": "Giải thích đường chạy khả thi cho một workflow (resolver).",
    "compat.cli.parser.preflight_help": "Kiểm tra điều kiện trước khi chạy một workflow.",
    "compat.cli.parser.evidence_help": "Liệt kê bằng chứng (provenance) của một workflow.",
    "compat.cli.parser.blocker_help": "Liệt kê blocker cần vendor/đơn vị pilot của một workflow.",
    "compat.cli.parser.arg.workflow_id": "ID workflow (vd vn.tax.sample_submission).",
    "compat.cli.parser.arg.app_version": (
        "Phiên bản app trong ngữ cảnh hiện tại (kiểm mất-hiệu-lực chứng nhận)."
    ),
    "compat.cli.parser.arg.token_model": "Model token ký số đang dùng (nếu có).",
    # --- CLI messages (DỮ LIỆU message_vi/warnings — luôn VI) ---
    "compat.cli.error.workflow_not_found": (
        "Không tìm thấy workflow '{id}' trong catalog tương thích."
    ),
    "compat.cli.warning.no_verified_route": (
        "Workflow '{id}': CHƯA có đường chạy kiểm chứng end-to-end — không kết luận chạy được."
    ),
    "compat.cli.error.catalog_broken": "Catalog tương thích lỗi nội bộ: {reason}",
    "compat.cli.warning.workflows_summary": (
        "{count} workflow liệt kê; {verified} đã kiểm chứng end-to-end "
        "(phần còn lại chưa có host/vendor thật để test)."
    ),
    "compat.cli.note.blocker": (
        "Chứng nhận thật cần: ứng dụng/cổng thật của đơn vị pilot, bản quyền + bộ cài "
        "từ nhà phát hành, thiết bị/token/máy in thật, sandbox được cổng cho phép, máy "
        "Windows đối chứng (COMP §6)."
    ),
}

_EN: dict[str, str] = {
    "compat.resolver.reason.no_verified_route": (
        "No end-to-end verified route exists for the required workflow "
        "'{workflow_id}' — do NOT conclude it works."
    ),
    "compat.resolver.reason.recommended": (
        "Recommend mode '{mode}': workflow_verified and feasible in the current context."
    ),
    "compat.resolver.reason.cert_stale_app": (
        "Certification invalidated — app version '{got}' differs from the certified "
        "version '{want}'; retest required, do NOT keep verified from stale metadata."
    ),
    "compat.resolver.reason.cert_stale_token": (
        "Signing certification invalidated — token '{token}' is not among the "
        "certified models; retest required."
    ),
    "compat.resolver.reason.mode_verified": "Mode '{mode}': workflow_verified.",
    "compat.resolver.reason.mode_partial": (
        "Mode '{mode}': only partial_workflow — not enough end-to-end evidence."
    ),
    "compat.resolver.reason.mode_not_inventoried": "Mode '{mode}': not inventoried.",
    "compat.resolver.reason.mode_blocked": "Mode '{mode}': blocked by an external dependency.",
    "compat.resolver.reason.mode_unsupported": "Mode '{mode}': determined unsupported.",
    "compat.resolver.reason.mode_never_usable": (
        "Mode '{mode}': only downloadable/launches — NOT counted as usable (ECO-003 gate)."
    ),
    "compat.resolver.reason.infeasible_license": (
        "Mode '{mode}' needs a valid Windows/app license — none available."
    ),
    "compat.resolver.reason.infeasible_network": "Mode '{mode}' needs network — currently offline.",
    "compat.resolver.reason.infeasible_policy": (
        "Mode '{mode}' (remote Windows/VM) needs admin approval — policy not granted."
    ),
    "compat.resolver.reason.no_route_for_mode": (
        "Mode '{mode}': not present in the workflow's route profile."
    ),
    "compat.schema.error.schema_version": "schema_version must be '{want}', got '{got}'.",
    "compat.schema.error.required_steps": (
        "required_steps must be exactly the 7 ECO-001 steps in order (discover→…→verify_result)."
    ),
    "compat.schema.error.enum_invalid": "Value '{value}' is invalid for field '{field}'.",
    "compat.schema.error.missing_field": "Missing required field '{field}'.",
    "compat.schema.error.type_invalid": "Field '{field}' has the wrong data type.",
    "compat.schema.error.cert_tested_at_missing": (
        "Certification claims {claim} but tested_at is missing — empty metadata is rejected."
    ),
    "compat.schema.error.cert_evidence_missing": (
        "Certification claims {claim} but lacks evidence for required steps: {missing}."
    ),
    "compat.schema.error.vendor_claim": (
        "vendor_support=supported without evidence — a vendor-support claim is not self-asserted."
    ),
    "compat.schema.error.cert_revoked_usable": (
        "Certification is revoked yet a route still claims a usable status — invalid."
    ),
    "compat.schema.error.cert_version_unpinned": (
        "Certification claims {claim} but app.version is unpinned ('{version}') — "
        "cannot be verified without a pinned version."
    ),
    "compat.schema.error.date_format": (
        "Field '{field}' must be a valid ISO-8601 date (YYYY-MM-DD), got '{value}'."
    ),
    "compat.schema.error.pack_secret": (
        "Workflow pack contains a forbidden sensitive field '{field}' (login/cookie/PIN/secret)."
    ),
    "compat.schema.error.pack_executable": (
        "Workflow pack contains a forbidden executable key '{field}' (command/argv/script…)."
    ),
    "compat.evidence.reason.revoked": "Certification has been revoked — not usable.",
    "compat.evidence.reason.business_unreviewed": (
        "Technically passing but business NOT reviewed → held at partial_workflow (COMP-052)."
    ),
    "compat.evidence.reason.business_rejected": (
        "Business REJECTED the result → not elevated to workflow_verified."
    ),
    "compat.evidence.reason.cert_expired": (
        "Certification past its recertify-by date ({recertify_by}) → needs_retest, held at partial."
    ),
    "compat.evidence.error.missing_field": "Evidence is missing required field '{field}'.",
    "compat.evidence.error.production_needs_reviewer": (
        "Production evidence for step '{step}' must be confirmed by a business-role reviewer."
    ),
    "compat.evidence.error.hash_format": ("fixture_hash must be 'sha256:<hex>' — got '{value}'."),
    "compat.classifier.disclaimer": (
        "STATIC analysis (binary not executed); labels are detected/inferred/unknown, "
        "NOT a compatibility conclusion."
    ),
    "compat.classifier.evidence.kernel_driver": (
        "Windows kernel-driver signal → Wine route BLOCKED (needs vendor or VM/remote)."
    ),
    "compat.classifier.evidence.anticheat": (
        "Kernel-level anti-cheat/DRM signal → Wine route BLOCKED."
    ),
    "compat.classifier.evidence.dotnet_modern": (
        "Modern cross-platform .NET signal (TFM net≥5) → may run native on Linux."
    ),
    "compat.classifier.evidence.dotnet_framework": (
        "Windows .NET Framework/desktop signal (WinForms/WPF) → Windows-only, try Wine."
    ),
    "compat.classifier.evidence.native_win32": (
        "Native Windows PE (not .NET) → try Wine; do NOT infer from the .exe extension."
    ),
    "compat.classifier.evidence.webview2": (
        "WebView2 dependency → needs a Windows/Edge runtime, test separately."
    ),
    "compat.classifier.evidence.sqlserver_client": (
        "SQL Server client dependency → needs the correct DB version/config (COMP-038)."
    ),
    "compat.classifier.evidence.unknown": (
        "Not enough signal to classify confidently — left as 'unknown'."
    ),
    "compat.device.refuse_carryover": (
        "Model '{model}' has not been tested on its own; not inferred from another "
        "model of the same vendor '{vendor}'."
    ),
    "compat.device.refuse_untested_function": (
        "Function '{function}' has not been tested on model '{model}'."
    ),
    "compat.device.ok_tested": "Model '{model}': function '{function}' tested via {protocol}.",
    "compat.cli.parser.cmd_help": (
        "Compatibility center: list workflows, explain routes, preflight, evidence, blockers."
    ),
    "compat.cli.parser.workflows_help": "List inventoried compatibility workflows + real status.",
    "compat.cli.parser.route_help": "Explain the feasible routes for a workflow (resolver).",
    "compat.cli.parser.preflight_help": "Check preconditions before running a workflow.",
    "compat.cli.parser.evidence_help": "List the evidence (provenance) of a workflow.",
    "compat.cli.parser.blocker_help": "List blockers needing a vendor/pilot unit for a workflow.",
    "compat.cli.parser.arg.workflow_id": "Workflow id (e.g. vn.tax.sample_submission).",
    "compat.cli.parser.arg.app_version": (
        "App version in the current context (to check certification invalidation)."
    ),
    "compat.cli.parser.arg.token_model": "Signing token model in use (if any).",
    "compat.cli.error.workflow_not_found": (
        "Workflow '{id}' not found in the compatibility catalog."
    ),
    "compat.cli.warning.no_verified_route": (
        "Workflow '{id}': NO end-to-end verified route yet — do not conclude it works."
    ),
    "compat.cli.error.catalog_broken": "Compatibility catalog internal error: {reason}",
    "compat.cli.warning.workflows_summary": (
        "{count} workflows listed; {verified} end-to-end verified "
        "(the rest lack a real host/vendor to test against)."
    ),
    "compat.cli.note.blocker": (
        "Real certification needs: the pilot unit's real apps/portals, licensed installers "
        "from the publisher, real devices/token/printer, a portal-approved sandbox, and a "
        "reference Windows machine (COMP §6)."
    ),
}

# Đăng ký ngay khi import (giống namios_cli.parser). Parity VI/EN được canh
# bởi test ``tests/unit/compat/test_i18n_parity.py``.
add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
