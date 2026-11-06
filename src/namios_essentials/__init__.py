"""NaMiOS — Phụ lục 11 (APP11-001..036): NaMiOS Essentials + Trung tâm cập nhật.

Lõi honest-core (data/logic thuần) cho bộ ứng dụng thiết yếu tích hợp sẵn
(Office/Browser/IME/Security Center/Zalo/YouTube/Maps/...) và NaMi Update
Center. TÁI DÙNG (import, KHÔNG fork): ``namios_e08`` (``Provenance``/
``provenance_ok`` cho nguồn gói native, ``run_install_transaction`` cho giao
dịch cập nhật), ``namios_sys`` (``SourceTrust``/``authorize`` — nội dung web
không tin cậy không tự kích hoạt tool), ``namios_odc`` (``LifecycleRing``
lab/pilot/stable, ``CertState``/``advance``/``can_publish``/``publish`` cho
chứng nhận per-chức-năng).

Bất biến xuyên suốt (Phụ lục 11 §1/§3): "Ứng dụng cài trên máy" ≠ "Dịch vụ
web" ≠ "Ứng dụng Windows qua Wine" — UI/Update Center không BAO GIỜ trộn ba
hình thức; manifest thiếu nguồn/giấy phép → không xuất hiện ở ảnh cài chính
thức; dịch vụ web KHÔNG bịa version cài trên máy; chứng nhận MỘT chức năng
không suy ra chức năng khác; tên miền gần giống bị chặn TRƯỚC khi nhập mật
khẩu; ring giữ bản cũ PHẢI có hạn, không giữ vô hạn.

Phần cần Launcher/App Center UI thật, trình duyệt/PWA thật, máy pilot thật,
PKI ký manifest thật (APP11-001/004/006/010/012/018/022/023/024/025/029/030/
031/034 SBOM-thật/035) = BLOCKED — xem
``docs/specs/PHU-LUC-11-APP11-MAPPING.md``.

Package tự được ``[tool.setuptools.packages.find] where=["src"]`` nhận diện.
"""

from __future__ import annotations

from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_essentials._errors import EssentialsErrorCode
from namios_essentials._types import (
    ESSENTIALS_SCHEMA_VERSION,
    AppCertProfile,
    AppFunction,
    CertState,
    DeliveryLabel,
    DeliveryType,
    DomainCheckResult,
    EssentialsManifest,
    EssentialsUpdateResult,
    InstallResult,
    LifecycleRing,
    Provenance,
    ReleaseGateResult,
    RingPromotionResult,
    ScheduleAction,
    ScheduleDecision,
    TrademarkStatus,
    UpdateChannel,
    UpdateClassification,
    UpdateOrigin,
    UpdateStatus,
    UpdateStatusBadge,
    Urgency,
)
from namios_essentials.anti_impersonation import (
    BRAND_TOKENS,
    OFFICIAL_DOMAIN_ALLOWLIST,
    check_official_url,
    effective_trademark_status,
    may_render_login_form,
)
from namios_essentials.cert_workflow import (
    advance_function,
    can_publish_function,
    function_state,
    is_function_supported,
    on_binary_hash_change,
    publish_function,
    with_needs_retest,
)
from namios_essentials.labels import (
    delivery_label,
    label_text,
    needs_connection,
    web_label_is_honest,
)
from namios_essentials.manifest import is_shippable, may_bundle_binary, validate_manifest
from namios_essentials.release_gate import (
    P0_GATE_KEYS,
    REQUIRED_WEB_SERVICES,
    evaluate_release_gate,
)
from namios_essentials.rings import evaluate_ring_promotion, is_retention_expired
from namios_essentials.smartai_classify import (
    classify_update_question,
    webpage_instruction_authorized,
)
from namios_essentials.update_center import (
    build_update_status,
    evaluate_web_shortcut,
    recovery_guidance,
    scanner_badge,
    schedule_update,
)
from namios_essentials.update_txn import run_essentials_update_transaction

__all__ = [
    "ESSENTIALS_SCHEMA_VERSION",
    "EssentialsErrorCode",
    # types
    "DeliveryType",
    "TrademarkStatus",
    "EssentialsManifest",
    "DeliveryLabel",
    "UpdateChannel",
    "Urgency",
    "UpdateStatusBadge",
    "UpdateStatus",
    "ScheduleAction",
    "ScheduleDecision",
    "EssentialsUpdateResult",
    "RingPromotionResult",
    "DomainCheckResult",
    "UpdateOrigin",
    "UpdateClassification",
    "AppFunction",
    "AppCertProfile",
    "ReleaseGateResult",
    "Provenance",
    "InstallResult",
    "LifecycleRing",
    "CertState",
    # manifest (APP11-002/034)
    "validate_manifest",
    "is_shippable",
    "may_bundle_binary",
    # labels (APP11-001/013)
    "delivery_label",
    "label_text",
    "needs_connection",
    "web_label_is_honest",
    # anti-impersonation (APP11-003/033)
    "OFFICIAL_DOMAIN_ALLOWLIST",
    "BRAND_TOKENS",
    "check_official_url",
    "may_render_login_form",
    "effective_trademark_status",
    # update center (APP11-013/015/019/020/032)
    "build_update_status",
    "scanner_badge",
    "evaluate_web_shortcut",
    "schedule_update",
    "recovery_guidance",
    # update txn (APP11-016)
    "run_essentials_update_transaction",
    # rings (APP11-017)
    "evaluate_ring_promotion",
    "is_retention_expired",
    # smartai classify (APP11-026)
    "classify_update_question",
    "webpage_instruction_authorized",
    # cert workflow (APP11-021/028)
    "function_state",
    "is_function_supported",
    "with_needs_retest",
    "on_binary_hash_change",
    "advance_function",
    "can_publish_function",
    "publish_function",
    # release gate (APP11-036)
    "P0_GATE_KEYS",
    "REQUIRED_WEB_SERVICES",
    "evaluate_release_gate",
]
