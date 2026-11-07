"""Bộ phân tích PE an toàn (N10-018) — phân loại METADATA đã bóc tách, KHÔNG
chạy file.

Nhận ``PeMetadataInput`` — một STRUCT dữ liệu caller đã trích xuất an toàn từ
đâu đó (installer/PE thật, form khảo sát thủ công…) — tuyệt đối không mở/
thực thi file trong module này. BẤT BIẾN cứng (N10-018 nghiệm thu): một PE có
đuôi ``.sys``, subsystem ``native``, hoặc import gắn kernel (``ntoskrnl.exe``…)
LUÔN được phân loại ``kernel_driver`` — KIỂM TRA NÀY CHẠY TRƯỚC MỌI nhánh
khác, nên không có dấu hiệu nào (installer/service/.NET) có thể khiến driver
bị gán nhầm "app user-mode". Thiếu bằng chứng → ``unknown``, không đoán.

TÁI DÙNG ``namios_pra.dotnet_classify.classify_dotnet`` cho nhánh .NET
(N10-025) — không viết lại bộ phân loại WPF/WinForms/console thứ hai.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from namios_i18n import Lang, t
from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra import DotnetClassification, DotnetKind
from namios_pra.dotnet_classify import classify_dotnet

__all__ = [
    "PeSubsystem",
    "PeClassification",
    "PeMetadataInput",
    "PeAnalysisResult",
    "classify_pe",
]


class PeSubsystem(str, Enum):
    """Windows subsystem quan sát được (N10-018). ``NATIVE`` = không GUI/CUI —
    đặc trưng driver/thành phần hệ thống, KHÔNG phải app người dùng chạy trực
    tiếp."""

    NATIVE = "native"
    WINDOWS_GUI = "windows_gui"
    WINDOWS_CUI = "windows_cui"
    UNKNOWN = "unknown"


class PeClassification(str, Enum):
    """Kết luận phân loại một PE/installer (N10-018)."""

    USER_MODE_APP = "user_mode_app"
    INSTALLER = "installer"
    KERNEL_DRIVER = "kernel_driver"
    WINDOWS_SERVICE = "windows_service"
    DOTNET_MANAGED = "dotnet_managed"
    UNKNOWN = "unknown"


#: Import quan sát được gắn chặt với kernel-mode (N10-018) — bất kỳ cái nào
#: xuất hiện cũng đủ để coi là driver, bất kể đuôi file/subsystem khai gì.
_KERNEL_IMPORT_MARKERS: frozenset[str] = frozenset(
    {"ntoskrnl.exe", "hal.dll", "wdfldr.sys", "wdf01000.sys"}
)


@dataclass(frozen=True)
class PeMetadataInput:
    """Metadata ĐÃ BÓC TÁCH an toàn của một PE/installer (N10-018) — KHÔNG
    phải bytes thực thi; caller chịu trách nhiệm trích xuất các trường này an
    toàn (vd đọc header tĩnh, không chạy). ``dotnet_kind``/``dotnet_traits``
    TÁI DÙNG ``namios_pra.DotnetKind`` khi caller đã nhận diện được tín hiệu
    .NET (sidecar ``.runtimeconfig.json``/``.deps.json`` hoặc tương đương)."""

    file_name: str
    extension: str = ""  # vd ".exe" / ".sys" / ".dll" / ".msi"
    architecture: str = "unknown"  # x86/x86_64/arm/arm64/any_cpu/unknown
    subsystem: PeSubsystem = PeSubsystem.UNKNOWN
    imports: frozenset[str] = frozenset()
    is_signed: bool = False
    certificate_subject: str = ""
    installer_markers: frozenset[str] = frozenset()  # vd "msi", "nsis", "innosetup"
    service_markers: frozenset[str] = frozenset()  # vd "SERVICE_MAIN", đăng ký làm Windows service
    dotnet_kind: DotnetKind = DotnetKind.UNKNOWN
    dotnet_traits: frozenset[str] = frozenset()


@dataclass(frozen=True)
class PeAnalysisResult:
    """Kết quả phân loại (N10-018). ``confidence_unknown=True`` khi KHÔNG đủ
    bằng chứng để kết luận gì hơn ``UNKNOWN`` — không đoán liều."""

    file_name: str
    classification: PeClassification
    dotnet: DotnetClassification | None = None
    reasons_vi: tuple[str, ...] = ()
    confidence_unknown: bool = False


def _looks_like_kernel_driver(meta: PeMetadataInput) -> bool:
    ext = meta.extension.strip().lower().lstrip(".")
    name = meta.file_name.strip().lower()
    imports_lower = frozenset(i.strip().lower() for i in meta.imports)
    return (
        ext == "sys"
        # Suy cả từ TÊN FILE: 'evil.sys' với extension rỗng (mặc định) vẫn là
        # driver — không để driver kernel lọt thành app user-mode vì thiếu ext.
        or name.endswith(".sys")
        or name.endswith(".drv")
        or meta.subsystem is PeSubsystem.NATIVE
        or bool(imports_lower & _KERNEL_IMPORT_MARKERS)
    )


def classify_pe(meta: PeMetadataInput) -> PeAnalysisResult:
    """Phân loại một PE/installer từ metadata ĐÃ BÓC TÁCH (N10-018), KHÔNG
    chạy file. Thứ tự kiểm TUYỆT ĐỐI (bất biến nghiệm thu, không đổi):

    1. Driver kernel (đuôi ``.sys`` ở extension HOẶC tên file kết thúc
       ``.sys``/``.drv`` / subsystem ``native`` / import kernel) →
       ``KERNEL_DRIVER``, BẤT KỂ có installer/service marker đi kèm hay không.
    2. Windows service marker → ``WINDOWS_SERVICE``.
    3. Installer marker → ``INSTALLER``.
    4. Có tín hiệu .NET (``dotnet_kind`` ≠ ``UNKNOWN``) → ``DOTNET_MANAGED``,
       TÁI DÙNG ``classify_dotnet`` để suy tuyến chạy.
    5. Subsystem GUI/CUI với đuôi ``.exe``/rỗng → ``USER_MODE_APP``.
    6. Còn lại → ``UNKNOWN`` (thiếu bằng chứng, không đoán).
    """

    if _looks_like_kernel_driver(meta):
        return PeAnalysisResult(
            meta.file_name,
            PeClassification.KERNEL_DRIVER,
            reasons_vi=(t("mig.pe.driver", lang=Lang.VI),),
        )

    if meta.service_markers:
        return PeAnalysisResult(
            meta.file_name,
            PeClassification.WINDOWS_SERVICE,
            reasons_vi=(t("mig.pe.service", lang=Lang.VI),),
        )

    if meta.installer_markers:
        return PeAnalysisResult(
            meta.file_name,
            PeClassification.INSTALLER,
            reasons_vi=(t("mig.pe.installer", lang=Lang.VI),),
        )

    if meta.dotnet_kind is not DotnetKind.UNKNOWN:
        classification = classify_dotnet(
            meta.dotnet_kind, traits=meta.dotnet_traits, arch=meta.architecture
        )
        return PeAnalysisResult(
            meta.file_name,
            PeClassification.DOTNET_MANAGED,
            dotnet=classification,
            reasons_vi=(classification.reason_vi,),
        )

    ext = meta.extension.strip().lower().lstrip(".")
    if meta.subsystem in (PeSubsystem.WINDOWS_GUI, PeSubsystem.WINDOWS_CUI) and ext in ("exe", ""):
        return PeAnalysisResult(
            meta.file_name,
            PeClassification.USER_MODE_APP,
            reasons_vi=(t("mig.pe.user_mode", lang=Lang.VI),),
        )

    return PeAnalysisResult(
        meta.file_name,
        PeClassification.UNKNOWN,
        confidence_unknown=True,
        reasons_vi=(t("mig.pe.unknown", lang=Lang.VI),),
    )
