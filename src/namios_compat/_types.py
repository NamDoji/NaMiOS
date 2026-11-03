"""Hợp đồng dữ liệu DÙNG CHUNG của Trung tâm tương thích (Phụ lục 03).

Đóng băng mọi enum + dataclass + hằng số để các module con (resolver,
classifier, device_registry, workflow_pack, schema, evidence) và CLI tham
chiếu MỘT nguồn sự thật — không tự định nghĩa lại (tránh trôi contract như
các đợt fan-out trước).

TÁI DÙNG, KHÔNG dựng lại:
- 5 chế độ chạy: ``namios_eco.status.WindowsMode`` (native_linux/web_linux/
  wine/remote_windows/windows_vm) — COMP-025 dùng đúng 5 mode này.
- Trạng thái công bố + GATE trung thực: ``namios_eco.status.PublishedStatus``
  + ``derive_published_status`` (ECO-003) — COMP-048 "workflow_verified chỉ
  khi đủ evidence" đã do gate đó canh.
- 7 nấc quy trình: ``namios_eco.workflow.WorkflowStepName`` + ``WORKFLOW_STEP_ORDER``.
- ``AppMode`` gợi ý từ phân tích .NET: ``namios_core.compat.AppMode``.

Các enum/dataclass dưới đây là phần MỚI của Phụ lục 03 (chứng nhận nhiều
trục, phân loại runtime, thiết bị, gói ngành, provenance) — bổ sung, không
chồng lấn các contract đã có.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from namios_core.compat import AppMode
from namios_eco.status import WindowsMode
from namios_eco.workflow import StepOutcome, WorkflowStepName

__all__ = [
    "SCHEMA_VERSION",
    "UNRESOLVED_VERSIONS",
    "MODE_INVESTIGATION_ORDER",
    "WINE_BLOCKER_KINDS",
    "TechnicalStatus",
    "BusinessStatus",
    "EndToEndStatus",
    "VendorSupport",
    "RuntimeKind",
    "ClassificationConfidence",
    "DeviceClass",
    "DeviceProtocol",
    "Sector",
    "EvidenceEnvironment",
    "AppRef",
    "Route",
    "Certification",
    "WorkflowEntry",
    "DeviceEntry",
    "WorkflowPackStep",
    "WorkflowPack",
    "CompatEvidence",
    "RuntimeClassification",
    "ResolveInput",
    "RouteCandidate",
    "RouteResolution",
]

#: Phiên bản hợp đồng schema hiện hành (COMP-048). Chuỗi ổn định; đổi là
#: breaking change cần migrate có version + ngày hiệu lực.
SCHEMA_VERSION = "1.0"

#: Giá trị version/app coi là "chưa chốt" — KHÔNG đủ cụ thể để pin chứng nhận.
#: Một chứng nhận tự nhận verified mà app.version thuộc tập này là KHÔNG hợp lệ
#: (schema từ chối) và KHÔNG bao giờ được miễn nhiễm kiểm tra drift (resolver).
UNRESOLVED_VERSIONS: frozenset[str] = frozenset({"", "unresolved", "unknown"})

#: Thứ tự ĐIỀU TRA mặc định (COMP-025 §3.1 + §1): native_linux → web_linux →
#: wine → remote_windows → windows_vm. ĐÂY LÀ THỨ TỰ THỬ, KHÔNG phải cam kết
#: "mode đầu luôn tốt hơn" — resolver chỉ đề xuất mode có bằng chứng
#: workflow_verified, feasible; không có thì trả ``no_verified_route``.
MODE_INVESTIGATION_ORDER: tuple[WindowsMode, ...] = (
    WindowsMode.NATIVE_LINUX,
    WindowsMode.WEB_LINUX,
    WindowsMode.WINE,
    WindowsMode.REMOTE_WINDOWS,
    WindowsMode.WINDOWS_VM,
)


class TechnicalStatus(str, Enum):
    """Trạng thái KỸ THUẬT quan sát được của một route/chứng nhận (COMP-048).

    Độc lập với ``BusinessStatus`` (nghiệp vụ) và ``EndToEndStatus`` (đầu-cuối)
    — ba cột tách nhau theo COMP-052 (pass kỹ thuật ≠ pass nghiệp vụ ≠ pass
    đầu-cuối)."""

    NOT_INVENTORIED = "not_inventoried"
    PARTIAL = "partial"
    VERIFIED = "verified"
    BLOCKED = "blocked"
    FAILED = "failed"


class BusinessStatus(str, Enum):
    """Trạng thái NGHIỆP VỤ: người có vai trò nghiệp vụ đã duyệt kết quả chưa
    (COMP-049/052). ``approved`` là điều kiện cần để nâng lên workflow_verified."""

    UNREVIEWED = "unreviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class EndToEndStatus(str, Enum):
    """Trạng thái ĐẦU–CUỐI độc lập (COMP-052): toàn bộ bước bắt buộc đã chạy
    trọn và đúng dữ liệu chưa."""

    UNTESTED = "untested"
    PARTIAL = "partial"
    PASS = "pass"
    FAIL = "fail"


class VendorSupport(str, Enum):
    """Mức hỗ trợ CHÍNH THỨC của nhà cung cấp (COMP-048). ``supported`` chỉ
    hợp lệ khi có bằng chứng — không tự nhận."""

    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class RuntimeKind(str, Enum):
    """Phân loại runtime Windows (COMP-028). Nhãn, KHÔNG suy từ đuôi ``.exe``.

    Phân biệt rõ .NET đa nền tảng hiện đại với .NET Framework/WinForms/WPF/
    WinUI (chỉ Windows), và các loại chặn Wine (driver kernel, anti-cheat/DRM)."""

    DOTNET_MODERN = "dotnet_modern"
    DOTNET_FRAMEWORK = "dotnet_framework"
    WINFORMS = "winforms"
    WPF = "wpf"
    WINUI = "winui"
    VCPP_RUNTIME = "vcpp_runtime"
    JAVA = "java"
    COM_OLE = "com_ole"
    ACTIVEX = "activex"
    WEBVIEW2 = "webview2"
    WINDOWS_SERVICE = "windows_service"
    SQLSERVER_CLIENT = "sqlserver_client"
    ANTICHEAT_DRM = "anticheat_drm"
    KERNEL_DRIVER = "kernel_driver"
    NATIVE_WIN32 = "native_win32"
    UNKNOWN = "unknown"


#: Loại runtime KHÓA đường Wine (COMP-028 nghiệm thu: app cần kernel driver bị
#: đánh blocker cho Wine). Wine không phải Windows kernel → không nạp được
#: driver nhân; anti-cheat/DRM thường cũng cần driver nhân/kiểm tra nền tảng.
WINE_BLOCKER_KINDS: frozenset[RuntimeKind] = frozenset(
    {RuntimeKind.KERNEL_DRIVER, RuntimeKind.ANTICHEAT_DRM}
)


class ClassificationConfidence(str, Enum):
    """Độ tin của phân loại (COMP-028 "phát hiện/suy đoán/chưa rõ")."""

    DETECTED = "detected"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class DeviceClass(str, Enum):
    """Nhóm thiết bị (COMP-032/036). Tách in/quét/token và thiết bị chuyên ngành."""

    PRINTER = "printer"
    SCANNER = "scanner"
    SIGNING_TOKEN = "signing_token"
    BARCODE_READER = "barcode_reader"
    LABEL_PRINTER = "label_printer"
    CARD_READER = "card_reader"
    TIMEKEEPER = "timekeeper"
    MEDICAL = "medical"
    OTHER = "other"


class DeviceProtocol(str, Enum):
    """Giao thức/cơ chế chuẩn Linux (COMP-032). IPP-over-USB cho phép driverless
    với thiết bị HỖ TRỢ — không suy ra mọi máy in USB dùng được."""

    IPP = "ipp"
    CUPS = "cups"
    IPP_OVER_USB = "ipp_over_usb"
    ESCL = "escl"
    SANE = "sane"
    PKCS11 = "pkcs11"
    VENDOR_DRIVER = "vendor_driver"
    HID = "hid"
    SERIAL = "serial"
    NETWORK = "network"
    API = "api"
    UNKNOWN = "unknown"


class Sector(str, Enum):
    """Nhóm ngành cho Workflow Pack (COMP-031): thuế, kế toán, BHXH, giáo dục,
    hành chính công, ngành dọc."""

    TAX = "tax"
    ACCOUNTING = "accounting"
    SOCIAL_INSURANCE = "social_insurance"
    EDUCATION = "education"
    PUBLIC_ADMIN = "public_admin"
    VERTICAL = "vertical"


class EvidenceEnvironment(str, Enum):
    """Nhãn môi trường của một bằng chứng (COMP-049): test sandbox/lab và test
    production có nhãn KHÁC nhau — không trộn."""

    SANDBOX = "sandbox"
    LAB = "lab"
    PRODUCTION = "production"


@dataclass(frozen=True)
class AppRef:
    """Định danh ứng dụng + phiên bản + kiến trúc + giấy phép (COMP-025/026).

    ``version``/``architecture`` là thành phần chứng nhận: đổi là mất hiệu lực
    chứng nhận cũ (COMP-025)."""

    id: str
    version: str
    architecture: str = "unknown"
    license: str = "verify_with_vendor"


@dataclass(frozen=True)
class Route:
    """Một đường chạy khả thi (mode) + trạng thái công bố + blocker (COMP-025).

    ``status`` dùng ``PublishedStatus`` (ECO-003) — cùng từ vựng gate trung
    thực với danh bạ ECO, không chế thêm bộ trạng thái song song."""

    mode: WindowsMode
    status: str  # PublishedStatus.value — giữ str để serialize JSON phẳng
    blockers: tuple[str, ...] = ()
    reason_vi: str = ""


@dataclass(frozen=True)
class Certification:
    """Hồ sơ chứng nhận nhiều trục (COMP-048 §4). Ba cột trạng thái tách nhau
    + mức vendor + hạn tái kiểm + cờ thu hồi.

    GATE (COMP-048): ``technical_status=verified`` hoặc ``end_to_end_status=pass``
    hoặc ``vendor_support=supported`` đều PHẢI có ``tested_at`` + ``evidence_ids``
    tương ứng — schema.py từ chối metadata trống."""

    os_build: str | None = None
    browser_or_runner: str | None = None
    device_models: tuple[str, ...] = ()
    tested_at: str | None = None
    evidence_ids: tuple[str, ...] = ()
    technical_status: TechnicalStatus = TechnicalStatus.NOT_INVENTORIED
    business_status: BusinessStatus = BusinessStatus.UNREVIEWED
    end_to_end_status: EndToEndStatus = EndToEndStatus.UNTESTED
    vendor_support: VendorSupport = VendorSupport.UNKNOWN
    recertify_by: str | None = None
    revoked: bool = False


@dataclass(frozen=True)
class WorkflowEntry:
    """Mục catalog tương thích cho một workflow (COMP-025/048 §4).

    ``workflow_id`` = ID ổn định. ``required_steps`` = đúng 7 nấc ECO-001.
    ``routes`` = các mode đã khảo sát + trạng thái; ``certification`` gắn với
    ``app`` (đổi version/arch → chứng nhận mất hiệu lực, resolver canh)."""

    schema_version: str
    workflow_id: str
    sector: Sector
    provider_id: str
    region_scope: str
    app: AppRef
    required_steps: tuple[WorkflowStepName, ...]
    requires: tuple[str, ...]
    routes: tuple[Route, ...]
    certification: Certification
    last_updated: str
    service_url: str | None = None
    source: str = ""


@dataclass(frozen=True)
class DeviceEntry:
    """Mục đăng ký năng lực thiết bị (COMP-032/036). KHÔNG ghi "hỗ trợ máy in"
    chung chung — ghi VID/PID/model/firmware/giao thức + CHỨC NĂNG đã test
    riêng theo từng model.

    Thiết bị cùng hãng khác ``model`` KHÔNG tự được công nhận
    (``capability_for`` ở device_registry từ chối suy diễn chéo model)."""

    device_id: str
    device_class: DeviceClass
    vendor: str
    model: str
    protocol: DeviceProtocol
    linux_mechanism: str
    tested_functions: tuple[str, ...] = ()
    vid: str | None = None
    pid: str | None = None
    firmware: str | None = None
    version: str | None = None
    permission_condition: str = ""
    status: TechnicalStatus = TechnicalStatus.NOT_INVENTORIED
    evidence_ids: tuple[str, ...] = ()
    notes_vi: str = ""


@dataclass(frozen=True)
class WorkflowPackStep:
    """Một bước trong Workflow Pack ngành (COMP-031). ``stop_before_real_transaction``
    = điểm DỪNG trước giao dịch/ký/nộp thật."""

    name: WorkflowStepName
    role: str
    expected_artifact: str
    inputs: tuple[str, ...] = ()
    stop_before_real_transaction: bool = False


@dataclass(frozen=True)
class WorkflowPack:
    """Gói workflow theo ngành (COMP-031): metadata + test plan, DỮ LIỆU GIẢ.

    Pack KHÔNG chứa đăng nhập/cookie/PIN/dữ liệu thật (schema.py quét secret).
    ``pack_version`` độc lập bản OS. Cổng/nhà cung cấp/địa phương chưa khảo sát
    ghi ``unknown``/``unresolved``."""

    pack_version: str
    sector: Sector
    workflow_id: str
    title_vi: str
    provider_id: str
    gateway: str
    steps: tuple[WorkflowPackStep, ...]
    devices: tuple[str, ...] = ()
    notes_vi: str = ""


@dataclass(frozen=True)
class CompatEvidence:
    """Bằng chứng + provenance (COMP-049). Mỗi evidence truy vết được tới
    case/fixture/expected-actual/người-duyệt/thời điểm/phiên bản môi trường.

    Log nhạy cảm tách khỏi báo cáo chia sẻ (COMP-045 — redaction ở lớp CLI/
    diagnostics). ``environment`` phân biệt sandbox/lab/production."""

    evidence_id: str
    workflow_id: str
    step: WorkflowStepName
    test_case_id: str
    fixture_hash: str
    expected: str
    actual: str
    outcome: StepOutcome
    timestamp: str
    environment: EvidenceEnvironment
    os_version: str
    app_version: str
    runner_version: str
    confirmed_by_role: str | None = None
    device_version: str | None = None
    note_vi: str = ""


@dataclass(frozen=True)
class RuntimeClassification:
    """Kết quả phân loại runtime (COMP-028). ``wine_blocker`` = có loại khóa
    Wine (driver nhân/anti-cheat). ``suggested_mode`` chỉ là GỢI Ý điều tra."""

    path: str
    kinds: tuple[RuntimeKind, ...]
    confidence: ClassificationConfidence
    wine_blocker: bool
    suggested_mode: AppMode | None
    evidence_vi: tuple[str, ...] = ()
    disclaimer_vi: str = ""


@dataclass(frozen=True)
class ResolveInput:
    """Đầu vào resolver (COMP-025 §3.1): ngữ cảnh runtime thực tế để chọn mode.

    ``app_version``/``token_model`` khác với chứng nhận đã lưu → resolver làm
    MẤT HIỆU LỰC chứng nhận tương ứng (không giữ verified bằng metadata cũ)."""

    workflow_id: str
    app_id: str
    app_version: str
    cpu_arch: str = "x86_64"
    os_build: str = "unknown"
    license_ok: bool = False
    required_devices: tuple[str, ...] = ()
    network_online: bool = True
    org_policy_allows_remote: bool = False
    token_model: str | None = None


@dataclass(frozen=True)
class RouteCandidate:
    """Một mode sau khi resolver đánh giá feasibility + trạng thái hiệu lực."""

    mode: WindowsMode
    feasible: bool
    status: str  # PublishedStatus.value SAU khi áp dụng mất-hiệu-lực
    reason_vi: str
    dependencies: tuple[str, ...] = ()
    limits_vi: tuple[str, ...] = ()
    untested_steps: tuple[str, ...] = ()


@dataclass(frozen=True)
class RouteResolution:
    """Kết quả COMP-025: danh sách mode theo thứ tự điều tra + mode đề xuất.

    ``no_verified_route=True`` khi KHÔNG mode nào đạt workflow_verified khả thi
    cho tác vụ bắt buộc — resolver trả thẳng, KHÔNG đoán "chạy được"."""

    workflow_id: str
    candidates: tuple[RouteCandidate, ...]
    recommended: WindowsMode | None
    no_verified_route: bool
    reasons_vi: tuple[str, ...] = field(default_factory=tuple)
