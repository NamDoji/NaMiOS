"""Hợp đồng dữ liệu NaMiOS Essentials + Update Center — Phụ lục 11 (APP11-001..036).

TÁI DÙNG (import, KHÔNG fork):
  - ``namios_e08``: ``Provenance``/``provenance_ok`` cho nguồn gói native (hash +
    chữ ký + official — APP11-002/014/034); ``InstallResult`` cho giao dịch cập
    nhật (APP11-016, stage→sign/space/pin→snapshot→apply→health→commit/rollback).
  - ``namios_sys``: ``SourceTrust``/``authorize`` — nội dung trang web/log KHÔNG
    tin cậy, lệnh trong đó KHÔNG tự kích hoạt tool (APP11-026, data_authority).
  - ``namios_odc``: ``LifecycleRing`` (lab/pilot/stable, APP11-017) + ``CertState``/
    ``EvidenceKind``/``advance``/``can_publish``/``publish`` (state machine chứng
    nhận per-chức-năng, APP11-021/028) — KHÔNG dựng hệ trạng thái thứ hai.

Bất biến xuyên suốt (APP11 §1/§3): "Ứng dụng cài trên máy" ≠ "Dịch vụ web" ≠
"Ứng dụng Windows qua Wine"; manifest thiếu nguồn/giấy phép → ``is_shippable=False``;
dịch vụ web KHÔNG BAO GIỜ bịa ``installed_version``/``available_version``; chứng
nhận MỘT chức năng KHÔNG suy ra chức năng khác (xem video đạt ≠ DRM đạt, chat đạt
≠ call đạt).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from namios_e08 import InstallResult, Provenance
from namios_odc import CertState, LifecycleRing

__all__ = [
    "ESSENTIALS_SCHEMA_VERSION",
    # manifest (APP11-002)
    "DeliveryType",
    "TrademarkStatus",
    "EssentialsManifest",
    # labels (APP11-001/013)
    "DeliveryLabel",
    # update center (APP11-013/015/019/020/032)
    "UpdateChannel",
    "Urgency",
    "UpdateStatusBadge",
    "UpdateStatus",
    "ScheduleAction",
    "ScheduleDecision",
    # update txn (APP11-016)
    "EssentialsUpdateResult",
    # rings (APP11-017)
    "RingPromotionResult",
    # anti-impersonation (APP11-003/033)
    "DomainCheckResult",
    # smartai classify (APP11-026)
    "UpdateOrigin",
    "UpdateClassification",
    # cert workflow (APP11-021/028)
    "AppFunction",
    "AppCertProfile",
    # release gate (APP11-036)
    "ReleaseGateResult",
    # re-export tiện dùng cho caller (không fork, chỉ cùng một nguồn kiểu)
    "Provenance",
    "InstallResult",
    "LifecycleRing",
    "CertState",
]

#: Phiên bản hợp đồng Phụ lục 11. Đổi khi phá vỡ cấu trúc.
ESSENTIALS_SCHEMA_VERSION = "1"


# --------------------------------------------------------------------------- #
# APP11-002 — Manifest có nguồn                                                #
# --------------------------------------------------------------------------- #


class DeliveryType(str, Enum):
    """Ba hình thức tích hợp (Phụ lục 11 §1). KHÔNG có hình thức thứ tư ngầm —
    mọi app Essentials PHẢI khai đúng MỘT trong ba, không có giá trị lấp lửng."""

    INSTALLED_NATIVE = "installed_native"
    OFFICIAL_WEB = "official_web"
    WINE_OPTIONAL = "wine_optional"


class TrademarkStatus(str, Enum):
    """Trạng thái quyền logo/nhãn hiệu (APP11-033). ``PENDING`` hoặc thiếu hồ sơ
    quyền → hiển thị PHẢI thay bằng chữ (``replace_with_text``), không tự ý dùng
    logo chưa rõ quyền."""

    APPROVED = "approved"
    PENDING = "pending"
    REPLACE_WITH_TEXT = "replace_with_text"


@dataclass(frozen=True)
class EssentialsManifest:
    """Một mục trong NaMiOS Essentials (APP11-002). ``package_source`` (tái dùng
    ``namios_e08.Provenance``) dùng cho ``installed_native``; ``official_url``
    dùng cho ``official_web``/``wine_optional``. ``offline`` mặc định ``False`` —
    KHÔNG BAO GIỜ ngầm bật ``True`` cho web app trừ khi caller tự khai tường minh
    (APP11-001/007)."""

    id: str
    title: str
    publisher: str
    category: str
    delivery_type: DeliveryType
    official_url: str = ""
    package_source: Provenance | None = None
    license: str = ""
    trademark_status: TrademarkStatus = TrademarkStatus.PENDING
    icon_provenance: str = ""
    version_policy: str = ""
    update_channel: str = ""
    required_permissions: tuple[str, ...] = ()
    offline: bool = False
    support_matrix: Mapping[str, str] = field(default_factory=dict)
    owner: str = ""
    last_verified: str | None = None
    binary_bundled: bool = False


class DeliveryLabel(str, Enum):
    """Bốn nhãn phụ ĐÚNG hiển thị ở Launcher/App Center (APP11-001/013)."""

    INSTALLED = "cai_tren_may"
    WEB_SERVICE = "dich_vu_web"
    WINE_TESTED = "qua_wine_da_kiem_thu"
    NEEDS_CONNECTION = "can_ket_noi"


# --------------------------------------------------------------------------- #
# APP11-013/015/019/020/032 — NaMi Update Center                               #
# --------------------------------------------------------------------------- #


class UpdateChannel(str, Enum):
    """8 kênh cập nhật của bảng trạng thái Update Center (APP11-013), ĐÚNG tên
    nêu trong đặc tả: os/security/browser/office/ime/other_app/wine_recipe/
    web_shortcut."""

    OS = "os"
    SECURITY = "security"
    BROWSER = "browser"
    OFFICE = "office"
    IME = "ime"
    OTHER_APP = "other_app"
    WINE_RECIPE = "wine_recipe"
    WEB_SHORTCUT = "web_shortcut"


class Urgency(str, Enum):
    ROUTINE = "routine"
    IMPORTANT = "important"
    CRITICAL = "critical"


class UpdateStatusBadge(str, Enum):
    """Badge hiển thị (APP11-013/019/020). ``SERVICE_INCIDENT_OR_COMPAT`` dùng
    khi dịch vụ web hỏng — KHÔNG BAO GIỜ đổ lỗi "NaMiOS chưa cập nhật"
    (APP11-019, E11-03)."""

    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    VENDOR_MANAGED = "vendor_managed"
    WARNING = "warning"
    SERVICE_INCIDENT_OR_COMPAT = "service_incident_or_compat"
    UNSUPPORTED_EOL = "unsupported_eol"


@dataclass(frozen=True)
class UpdateStatus:
    """Một dòng bảng trạng thái Update Center (APP11-013). ``retest_required``
    = badge kiểm thử hết hiệu lực sau khi browser/OS đổi (E11-03), KHÔNG phải
    một badge enum riêng để tránh nổ số trạng thái."""

    channel: UpdateChannel
    installed_version: str | None = None
    available_version: str | None = None
    last_checked: str = ""
    urgency: Urgency = Urgency.ROUTINE
    badge: UpdateStatusBadge = UpdateStatusBadge.UP_TO_DATE
    retest_required: bool = False
    message_vi: str = ""


class ScheduleAction(str, Enum):
    """Hành động lịch cài (APP11-015). ``INSTALL_NOW`` KHÔNG BAO GIỜ được chọn
    khi có ngữ cảnh bận (tiết học/cuộc họp/ký hóa đơn) — xem
    ``update_center.schedule_update``."""

    INSTALL_NOW = "install_now"
    INSTALL_TONIGHT = "install_tonight"
    DEFER = "defer"
    REMIND_OVERDUE = "remind_overdue"


@dataclass(frozen=True)
class ScheduleDecision:
    action: ScheduleAction
    overdue: bool = False
    reason_vi: str = ""


# --------------------------------------------------------------------------- #
# APP11-016 — Cập nhật giao dịch (bọc namios_e08.install_txn)                   #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EssentialsUpdateResult:
    """Kết quả một giao dịch cập nhật Essentials (APP11-016). ``install`` TÁI
    DÙNG nguyên ``namios_e08.InstallResult`` — không khai lại field stage.
    ``user_data_touched`` LUÔN ``False`` theo cấu trúc: hàm dựng giá trị này
    (``update_txn.run_essentials_update_transaction``) không nhận bất kỳ tham
    số đường dẫn tài liệu người dùng nào, nên không có cách nào đụng vào đó."""

    channel: UpdateChannel
    install: InstallResult
    user_data_touched: bool = False
    recovery_message_vi: str = ""


# --------------------------------------------------------------------------- #
# APP11-017 — Update rings (lab/pilot/stable)                                  #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RingPromotionResult:
    """Kết quả xét thăng hạng ring (APP11-017). Khi ``blocked=True`` do một
    dịch vụ TRỌNG YẾU hỏng ở lab, ``retention_deadline`` PHẢI khác rỗng — giữ
    bản cũ CÓ THỜI HẠN, KHÔNG giữ vô hạn (xem ``rings.is_retention_expired``:
    hạn rỗng = coi như ĐÃ hết hạn ngay, không có đường "giữ mãi")."""

    target_ring: LifecycleRing
    blocked: bool
    retained_version: str | None = None
    retention_deadline: str = ""
    warning_vi: str = ""


# --------------------------------------------------------------------------- #
# APP11-003/033 — Chống mạo danh                                               #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DomainCheckResult:
    """Kết quả kiểm tên miền trước khi mở shortcut/cho phép nhập mật khẩu
    (APP11-003). ``impersonation_suspected`` = tên miền chứa thương hiệu đã
    biết nhưng KHÔNG nằm trong allowlist (vd ``whatsapp-login.example``)."""

    allowed: bool
    scheme_ok: bool
    domain: str
    reason_vi: str = ""
    impersonation_suspected: bool = False
    error_code: str | None = None


# --------------------------------------------------------------------------- #
# APP11-026 — SmartAI phân loại cập nhật                                       #
# --------------------------------------------------------------------------- #


class UpdateOrigin(str, Enum):
    """Phân loại nguồn gốc một "cập nhật" người dùng hỏi (APP11-026)."""

    VENDOR_WEB_SERVICE = "vendor_web_service"
    NAMIOS_BROWSER_MANIFEST = "namios_browser_manifest"
    NAMIOS_NATIVE_PACKAGE = "namios_native_package"
    WINE_RECIPE_PENDING_CERT = "wine_recipe_pending_cert"


@dataclass(frozen=True)
class UpdateClassification:
    """Kết quả phân loại câu hỏi cập nhật tự nhiên (APP11-026). ``action_allowed``
    = NaMiOS có được tự kích hoạt một tool thật cho yêu cầu này không (web
    vendor-managed / Wine chưa chứng nhận → luôn ``False``)."""

    origin: UpdateOrigin
    action_allowed: bool
    explanation_vi: str = ""


# --------------------------------------------------------------------------- #
# APP11-021/028 — Chứng nhận workflow per-chức-năng                            #
# --------------------------------------------------------------------------- #


class AppFunction(str, Enum):
    """Trục chức năng chứng nhận RIÊNG của một (app, version) (APP11-028).
    Không suy từ chức năng khác cùng app — xem video đạt KHÔNG suy ra DRM đạt;
    chat đạt KHÔNG suy ra call đạt."""

    OPEN = "open"
    LOGIN = "login"
    VIETNAMESE_TEXT = "vietnamese_text"
    UPLOAD = "upload"
    NOTIFICATION = "notification"
    CHAT = "chat"
    CALL_VIDEO = "call_video"
    WATCH_VIDEO = "watch_video"
    DRM_PLAYBACK = "drm_playback"
    PRINT_EXPORT = "print_export"


@dataclass(frozen=True)
class AppCertProfile:
    """Hồ sơ chứng nhận một (app, version, browser, OS, hardware) (APP11-028).
    Ghi đúng những trục đặc tả yêu cầu: "mở, đăng nhập, tiếng Việt, upload,
    notification, call/video khi phù hợp, in/file xuất". TÁI DÙNG state machine
    ``namios_odc`` (``CertState``/``advance``/``publish``) làm đơn vị trạng thái
    MỖI chức năng — KHÔNG dựng máy trạng thái thứ hai, chỉ đổi đơn vị chứng
    nhận từ "thiết bị" sang "app"."""

    app_id: str
    version: str
    browser: str = "unresolved"
    os_build: str = "unresolved"
    hardware: str = "unresolved"
    permission_scope: tuple[str, ...] = ()
    functions: Mapping[AppFunction, CertState] = field(default_factory=dict)
    test_dates: Mapping[AppFunction, str] = field(default_factory=dict)
    binary_hash: str = ""
    last_known_good_hash: str = ""


# --------------------------------------------------------------------------- #
# APP11-036 — Cổng phát hành                                                   #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ReleaseGateResult:
    """Kết quả cổng phát hành Essentials (APP11-036). ``shippable`` chỉ
    ``True`` khi KHÔNG còn blocker nào — rỗng ``blockers`` là điều kiện CẦN
    và ĐỦ, không có nhánh tắt."""

    shippable: bool
    blockers: tuple[str, ...] = ()
