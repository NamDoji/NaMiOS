"""Hợp đồng dữ liệu O0 — Phụ lục 07 (ODC-001..048).

Office tích hợp sẵn + chứng nhận thiết bị. TÁI DÙNG (không fork):
``namios_pra`` (OfficeNeed/route/fidelity + DeviceFunction/status + Doctor),
``namios_sys`` (SourceTrust/data_authority), ``namios_smartai`` (promotion
pattern). Nguyên tắc trung thực xuyên suốt: "mở được" ≠ "sửa đúng" ≠ "in đúng" ≠
"chạy macro"; nội dung tài liệu KHÔNG cấp quyền/đổi app/upload; "thấy thiết bị" ≠
"in được"; catalog ≠ đã-hỗ-trợ.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from namios_pra import DeviceFunctionStatus, OfficeNeed

__all__ = [
    "ODC_SCHEMA_VERSION",
    # Office route matrix (ODC-008)
    "OfficeMode",
    "DocRouteResult",
    # Document broker (ODC-007)
    "DocFormat",
    "DocSensitivity",
    "DocumentMetadata",
    # lifecycle (ODC-001/020/033)
    "Component",
    "LifecycleRing",
    "PackageRelease",
    # device cert (ODC-022/047)
    "CertFunction",
    "CertState",
    "EvidenceKind",
    "DeviceCert",
    # metrics (ODC-048)
    "CoverageMetrics",
    # re-export tiện dùng
    "OfficeNeed",
    "DeviceFunctionStatus",
]

ODC_SCHEMA_VERSION = "1"


# --------------------------------------------------------------------------- #
# ODC-008 — Office Route Matrix                                                 #
# --------------------------------------------------------------------------- #


class OfficeMode(str, Enum):
    """6 tuyến xử lý tài liệu (ODC-008). ``BUNDLED_OFFICE`` = bộ Office cài sẵn
    (engine mã nguồn mở); ``BLOCKED`` = chưa có tuyến đạt."""

    BUNDLED_OFFICE = "bundled_office"
    OFFICIAL_WEB = "official_web"
    TESTED_WINE = "tested_wine"
    LICENSED_WINDOWS_REMOTE = "licensed_windows_remote"
    LICENSED_WINDOWS_VM = "licensed_windows_vm"
    READ_ONLY_VIEWER = "read_only_viewer"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class DocRouteResult:
    """Kết quả chọn tuyến tài liệu (ODC-008). TÁCH RÕ 4 trục trung thực: mở được
    ≠ sửa đúng ≠ in đúng ≠ chạy macro. ``auto_upload`` LUÔN False (ODC-017)."""

    mode: OfficeMode
    openable: bool  # xem/mở được
    edit_faithful: bool  # sửa + lưu giữ đúng dữ liệu nghĩa (cần fidelity evidence)
    print_faithful: bool  # in ra giấy đúng
    macro_capable: bool  # chạy được macro/COM/add-in
    windows_dependent: bool = False
    needs_explicit_consent: bool = False  # tuyến web + file nhạy cảm
    auto_upload: bool = False
    reasons_vi: tuple[str, ...] = ()


# --------------------------------------------------------------------------- #
# ODC-007 — Document Broker                                                     #
# --------------------------------------------------------------------------- #


class DocFormat(str, Enum):
    """Định dạng tài liệu quan sát được (ODC-007)."""

    DOCX = "docx"
    XLSX = "xlsx"
    XLSM = "xlsm"  # Excel có macro
    PPTX = "pptx"
    DOCM = "docm"  # Word có macro
    ODF = "odf"
    PDF = "pdf"
    UNKNOWN = "unknown"


class DocSensitivity(str, Enum):
    """Độ nhạy tài liệu (ODC-017). ``SENSITIVE`` (hợp đồng/bảng lương/PII) → KHÔNG
    tự đưa lên web/model ngoài."""

    NORMAL = "normal"
    SENSITIVE = "sensitive"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DocumentMetadata:
    """Metadata ĐO được của một tài liệu (ODC-007). Phân tích an toàn với file dị
    dạng (chỉ nhận dấu hiệu đã bóc, không thực thi). ``needs`` = nhu cầu người
    dùng (OfficeNeed). ``source_is_trusted`` phản ánh nguồn mở file (nội dung
    KHÔNG tin cậy — ODC-007/017)."""

    doc_format: DocFormat = DocFormat.UNKNOWN
    needs: frozenset[OfficeNeed] = frozenset()
    has_macros: bool = False
    has_signature: bool = False
    encrypted_or_irm: bool = False
    missing_fonts: tuple[str, ...] = ()
    external_links: bool = False
    sensitivity: DocSensitivity = DocSensitivity.UNKNOWN


# --------------------------------------------------------------------------- #
# ODC-001/020/033 — Tách gói + vòng đời + recheck                              #
# --------------------------------------------------------------------------- #


class Component(str, Enum):
    """Thành phần có vòng đời RIÊNG (ODC-020). Đổi 1 thành phần chỉ invalid
    evidence vùng ảnh hưởng (ODC-033), KHÔNG hạ toàn hệ."""

    OFFICE = "office"
    TEMPLATES = "templates"
    EXTENSION = "extension"
    FONT = "font"
    AI_MODEL = "ai_model"
    OS_KERNEL = "os_kernel"
    FIRMWARE = "firmware"
    PRINT_STACK = "print_stack"  # CUPS/SANE/Printer App
    NETWORK_STACK = "network_stack"  # NetworkManager
    BLUETOOTH_STACK = "bluetooth_stack"  # BlueZ/audio
    DEVICE_MODEL = "device_model"


class LifecycleRing(str, Enum):
    """Ring phát hành (ODC-020)."""

    LAB = "lab"
    PILOT = "pilot"
    STABLE = "stable"


@dataclass(frozen=True)
class PackageRelease:
    """Một bản phát hành gói Office/extension/… (ODC-001). Có version + nguồn +
    rollback RIÊNG; cập nhật KHÔNG đụng kernel/desktop."""

    name: str
    version: str
    component: Component
    ring: LifecycleRing = LifecycleRing.LAB
    source: str = ""  # repo/vendor có nguồn
    rollback_to: str = ""  # version quay lại được; rỗng = chưa có rollback


# --------------------------------------------------------------------------- #
# ODC-022/047 — Chứng nhận thiết bị per-function + state machine               #
# --------------------------------------------------------------------------- #


class CertFunction(str, Enum):
    """Trục chức năng chứng nhận RIÊNG của một model (ODC-022). Không suy từ model
    cùng hãng."""

    PRINT = "print"
    SCAN = "scan"
    COPY_VIA_PC = "copy_via_pc"  # Scan→Print qua NaMiOS
    COPY_ON_DEVICE = "copy_on_device"  # nút copy trên máy (NaMiOS không điều khiển)
    FAX = "fax"
    DUPLEX = "duplex"
    ADF = "adf"
    SECURE_RELEASE = "secure_release"
    USB = "usb"
    NETWORK = "network"


class CertState(str, Enum):
    """Vòng đời chứng nhận một chức năng (ODC-047). Tiến tuyến tính; chỉ bằng
    chứng THẬT nâng, bình luận cộng đồng/model KHÔNG nâng."""

    REPORTED = "reported"  # người dùng/cộng đồng báo — CHƯA kiểm
    LAB_TESTED = "lab_tested"  # đội tự kiểm trong lab, có evidence
    PILOT_VERIFIED = "pilot_verified"  # người nghiệp vụ pilot xác nhận
    PUBLISHED = "published"  # công bố hỗ trợ
    NEEDS_RETEST = "needs_retest"  # trigger đổi → phải kiểm lại


class EvidenceKind(str, Enum):
    """Nguồn bằng chứng khi nâng cert (ODC-047)."""

    COMMUNITY_REPORT = "community_report"  # "máy tôi in được" — KHÔNG nâng
    AI_GUESS = "ai_guess"  # KHÔNG nâng
    LAB_TEST = "lab_test"  # đội kiểm, có testcase + ảnh bản in che dữ liệu
    PILOT_SIGNOFF = "pilot_signoff"  # người nghiệp vụ duyệt


@dataclass(frozen=True)
class DeviceCert:
    """Hồ sơ chứng nhận một model (ODC-022/047). Mỗi chức năng một state + ngày
    + evidence RIÊNG."""

    model: str
    firmware: str = "unknown"
    functions: Mapping[CertFunction, CertState] = field(default_factory=dict)
    test_dates: Mapping[CertFunction, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# ODC-048 — Chỉ số thành công                                                   #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CoverageMetrics:
    """Chỉ số độ phủ TRUNG THỰC (ODC-048). BÁO RIÊNG từng số + mẫu số; KHÔNG lấy
    'số model trong catalog' làm 'số model đã hỗ trợ'."""

    user_weighted_device_coverage: float  # người pilot đủ workflow thiết bị / tổng pilot
    pilot_users_total: int
    workflow_coverage: float  # workflow bắt buộc có tuyến verified / tổng
    office_fidelity_pass: float  # fixture fidelity pass / tổng fixture đã đo
    windows_dependency: float  # workflow cần Windows fallback / tổng
    models_surveyed: int  # model khảo sát (catalog) — KHÁC đã-hỗ-trợ
    models_published: int  # model có ít nhất 1 chức năng PUBLISHED
    data_loss_incidents: int
