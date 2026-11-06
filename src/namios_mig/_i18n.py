"""Lớp common song ngữ của ``namios_mig`` (Phụ lục 10) — đăng ký qua
``namios_i18n.add_catalog`` khi import. Trường dữ liệu ``*_vi`` luôn tiếng Việt.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # schema.py — validator (N10-007/012/019/026/043)
    "mig.schema.app_no_id": "Thiếu app_id — không khớp được app nào.",
    "mig.schema.usage_no_optin": (
        "Chưa opt-in nhưng vẫn khai 'đã dùng 30 ngày' — PHẢI loại trường này (N10-007)."
    ),
    "mig.schema.device_no_id": "Thiếu device_id.",
    "mig.schema.recipe_no_app": "Recipe thiếu app_id.",
    "mig.schema.recipe_no_version": "Recipe thiếu version.",
    "mig.schema.recipe_no_runner": (
        "Tuyến Wine PHẢI pin một wine_runner cụ thể — không để 'wine' chung chung (N10-019)."
    ),
    "mig.schema.recipe_publish_no_test": "Công bố recipe nhưng chưa có test case nào.",
    "mig.schema.recipe_publish_no_owner": "Công bố recipe nhưng chưa có owner chịu trách nhiệm.",
    "mig.schema.workflow_no_evidence": "status=passed nhưng chưa có evidence nào.",
    "mig.schema.workflow_no_tested_at": "status=passed nhưng chưa ghi ngày kiểm (tested_at).",
    "mig.schema.evidence_empty": "Evidence record thiếu id hoặc không mang tín hiệu nào.",
    "mig.schema.inventory_no_machine": "Hồ sơ khảo sát thiếu machine_id.",
    "mig.recipe.needs_retest": (
        "App đổi hash/version so với recipe đã ký → cần kiểm lại, không kế thừa nhãn cũ (N10-026)."
    ),
    # readiness.py (N10-009)
    "mig.readiness.no_essential": (
        "Chưa khai công việc thiết yếu nào — không đủ dữ liệu để kết luận sẵn sàng."
    ),
    "mig.readiness.blocked": (
        "Công việc thiết yếu bị chặn: {apps} — máy chuyển đổi BLOCKED dù app khác có chạy."
    ),
    "mig.readiness.unknown": "Công việc thiết yếu chưa kiểm: {apps} — chưa đủ bằng chứng.",
    "mig.readiness.pilot_only": (
        "Công việc thiết yếu mới kiểm ở mức pilot, chưa công bố rộng: {apps}."
    ),
    "mig.readiness.limits": "Công việc thiết yếu chạy được nhưng có hạn chế: {apps}.",
    "mig.readiness.ready": "Mọi công việc thiết yếu đã kiểm đạt, route sạch.",
    # compat_broker.py (N10-017/027)
    "mig.route.vendor_native": "Vendor có bản Linux native — ưu tiên tuyến này.",
    "mig.route.vendor_web": "Vendor có bản web chính thức — ưu tiên tuyến này.",
    "mig.route.blocked_kernel_windows": (
        "Phụ thuộc phần cứng/vendor khóa-Windows (driver/token) bị chặn — Wine không thể thay thế."
    ),
    "mig.route.needs_confirmation": "Cần xác nhận thêm trước khi coi là đạt.",
    "mig.route.blocked_unsupported": (
        "Chưa có tuyến đạt cho tác vụ này — ghi unsupported, không bịa."
    ),
    "mig.route.degraded": "Phụ thuộc bắt buộc chưa ổn (down/missing/unknown) — chưa đủ bằng chứng.",
    "mig.route.wine_ok": "Phụ thuộc bắt buộc đã ổn và Wine đã được kiểm cho đúng bản này.",
    "mig.route.remote_windows_ok": "Phụ thuộc bắt buộc đã ổn, dùng Windows có phép.",
    # pe_analyzer.py (N10-018)
    "mig.pe.driver": (
        "Dấu hiệu driver kernel (.sys/subsystem native/import kernel) — không phải app."
    ),
    "mig.pe.service": "Có dấu hiệu đăng ký Windows service.",
    "mig.pe.installer": "Có dấu hiệu installer (msi/nsis/innosetup…).",
    "mig.pe.user_mode": "PE user-mode GUI/CUI thông thường.",
    "mig.pe.unknown": "Thiếu bằng chứng để phân loại — không đoán.",
    # workflow_verdict.py (N10-043)
    "mig.workflow.evidence_negative": "Có bằng chứng cho thấy THẤT BẠI (vd giấy trắng) — FAILED.",
    "mig.workflow.evidence_insufficient": (
        "Chỉ có bằng chứng yếu (exit-code/spool một mình) — CHƯA đủ để coi là xong."
    ),
    "mig.workflow.dep_blocked": "Phụ thuộc kỹ thuật bắt buộc bị chặn — chưa dùng được.",
    "mig.workflow.dep_partial": "Phụ thuộc kỹ thuật chưa ổn — hạ về partial, không nhận PASSED.",
    "mig.workflow.dep_unknown": "Chưa rõ phụ thuộc kỹ thuật — hạ về partial, không tự nhận PASSED.",
}

_EN: dict[str, str] = {
    "mig.schema.app_no_id": "Missing app_id — cannot match any app.",
    "mig.schema.usage_no_optin": (
        "No opt-in but '30-day usage' was declared — this field MUST be dropped (N10-007)."
    ),
    "mig.schema.device_no_id": "Missing device_id.",
    "mig.schema.recipe_no_app": "Recipe is missing app_id.",
    "mig.schema.recipe_no_version": "Recipe is missing version.",
    "mig.schema.recipe_no_runner": (
        "A Wine route MUST pin a specific wine_runner — no generic 'wine' (N10-019)."
    ),
    "mig.schema.recipe_publish_no_test": "Publishing a recipe with no test cases.",
    "mig.schema.recipe_publish_no_owner": "Publishing a recipe with no responsible owner.",
    "mig.schema.workflow_no_evidence": "status=passed but no evidence recorded.",
    "mig.schema.workflow_no_tested_at": "status=passed but no tested_at date recorded.",
    "mig.schema.evidence_empty": "Evidence record missing id or carries no signal at all.",
    "mig.schema.inventory_no_machine": "Assessment inventory is missing machine_id.",
    "mig.recipe.needs_retest": (
        "App hash/version changed vs the signed recipe → retest required, "
        "the old label is NOT inherited (N10-026)."
    ),
    "mig.readiness.no_essential": (
        "No essential task declared — not enough data to conclude readiness."
    ),
    "mig.readiness.blocked": (
        "Essential task(s) blocked: {apps} — the machine is BLOCKED even if other apps run."
    ),
    "mig.readiness.unknown": "Essential task(s) not tested yet: {apps} — not enough evidence.",
    "mig.readiness.pilot_only": (
        "Essential task(s) only verified at pilot level, not yet published: {apps}."
    ),
    "mig.readiness.limits": "Essential task(s) work but with limitations: {apps}.",
    "mig.readiness.ready": "Every essential task passed and routes are clean.",
    "mig.route.vendor_native": "Vendor has an official Linux native build — prefer this route.",
    "mig.route.vendor_web": "Vendor has an official web app — prefer this route.",
    "mig.route.blocked_kernel_windows": (
        "Hardware/vendor Windows-only dependency (driver/token) is blocked — "
        "Wine cannot replace it."
    ),
    "mig.route.needs_confirmation": "Needs further confirmation before counting as passing.",
    "mig.route.blocked_unsupported": "No working route for this task yet — record unsupported.",
    "mig.route.degraded": "A required dependency is not OK yet (down/missing/unknown).",
    "mig.route.wine_ok": "Required dependencies are OK and Wine was tested for this exact build.",
    "mig.route.remote_windows_ok": "Required dependencies are OK, using licensed Windows.",
    "mig.pe.driver": "Kernel driver signal (.sys/native subsystem/kernel import) — not an app.",
    "mig.pe.service": "Windows service registration signal detected.",
    "mig.pe.installer": "Installer signal detected (msi/nsis/innosetup...).",
    "mig.pe.user_mode": "Ordinary user-mode GUI/CUI PE.",
    "mig.pe.unknown": "Not enough evidence to classify — no guessing.",
    "mig.workflow.evidence_negative": "Evidence shows FAILURE (e.g. blank page) — FAILED.",
    "mig.workflow.evidence_insufficient": (
        "Only weak evidence (exit-code/spool alone) — NOT enough to call it done."
    ),
    "mig.workflow.dep_blocked": "A required technical dependency is blocked — not usable yet.",
    "mig.workflow.dep_partial": (
        "A required technical dependency is not OK — downgraded to partial."
    ),
    "mig.workflow.dep_unknown": "Technical dependency unknown — downgraded to partial.",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
