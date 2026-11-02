"""Kiểu dữ liệu công khai của ``namios_dotnet`` (NET-001/NET-002).

Chỉ dataclass/enum — không business logic (giống phong cách
``namios_core``). Xem ``analyzer.py`` cho logic suy luận thật."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from namios_core.compat import AppMode

__all__ = [
    "PeArchitecture",
    "PeKind",
    "ClrHeaderInfo",
    "SidecarInfo",
    "EvidenceItem",
    "DotnetAnalysisResult",
    "STATIC_ANALYSIS_DISCLAIMER_VI",
]

#: Nhắc bắt buộc đi kèm MỌI kết quả (NET-002/NET-001): phân tích tĩnh chỉ là
#: gợi ý nhận diện, KHÔNG phải chứng nhận ứng dụng chạy được; không có bước
#: nào trong pipeline này thực thi file nhị phân.
STATIC_ANALYSIS_DISCLAIMER_VI = (
    "Phân tích tĩnh (không thực thi file) chỉ là GỢI Ý nhận diện (NET-002); "
    "KHÔNG phải chứng nhận ứng dụng chạy được. Chứng nhận thật đòi hỏi bằng "
    "chứng chạy + QA phê duyệt độc lập (xem task_verified, M1-INTERFACES §5)."
)


class PeArchitecture(str, Enum):
    """Kiến trúc suy ra từ ``IMAGE_FILE_HEADER.Machine`` (+ tinh chỉnh bằng
    cờ CLR cho AnyCPU)."""

    X86 = "x86"
    X64 = "x86_64"
    ARM = "arm"
    ARM64 = "arm64"
    IA64 = "ia64"
    #: Assembly managed thuần IL, không ép 32-bit → chạy được trên bất kỳ
    #: kiến trúc JIT hỗ trợ (suy từ Machine=I386 + PE32 + ILONLY +
    #: KHÔNG 32BITREQUIRED — quy ước phổ biến của compiler .NET).
    ANY_CPU = "any_cpu"
    UNKNOWN = "unknown"


class PeKind(str, Enum):
    """Phân loại managed/native (NET-001)."""

    NATIVE = "native"
    #: Managed thuần IL (``COMIMAGE_FLAGS_ILONLY`` set).
    MANAGED = "managed"
    #: Mixed-mode (có cả code native lẫn CLR header — vd C++/CLI, IJW):
    #: ILONLY KHÔNG set dù có CLR data directory.
    MANAGED_MIXED = "managed_mixed"
    #: Không phải PE hợp lệ (thiếu chữ ký MZ/PE) — không phải lỗi phân tích,
    #: chỉ là "tệp này không phải PE".
    NOT_PE = "not_pe"
    #: Có chữ ký MZ nhưng cấu trúc phía sau dị dạng/cụt/offset vô lý.
    MALFORMED = "malformed"


@dataclass(frozen=True)
class ClrHeaderInfo:
    """Trường rút gọn từ ``IMAGE_COR20_HEADER`` hữu ích cho phân loại."""

    major_runtime_version: int
    minor_runtime_version: int
    il_only: bool
    requires_32bit: bool
    native_entrypoint: bool
    metadata_rva: int
    metadata_size: int
    #: ``True`` nếu RVA của MetaData ánh xạ được tới offset file hợp lệ qua
    #: bảng section (xác minh thêm, không chỉ tin con số trong CLR header).
    metadata_mapped: bool


@dataclass(frozen=True)
class SidecarInfo:
    """Dữ liệu đọc được từ ``.runtimeconfig.json``/``.deps.json`` ĐI KÈM
    (cùng thư mục) — tuỳ chọn, ``None`` nếu không có sidecar nào."""

    runtimeconfig_path: str | None
    target_framework_moniker: str | None  # vd "net8.0", "net48"
    framework_names: tuple[str, ...]  # vd ("Microsoft.NETCore.App",)
    #: Tín hiệu desktop Windows từ framework.name/frameworks[] hoặc
    #: deps.json libraries — yêu cầu bắt buộc: KHÔNG được gọi WinForms/WPF là
    #: "Linux native" (NET-001/004 test matrix NET-01/NET-04).
    has_windows_desktop_framework: bool
    deps_json_path: str | None
    declared_library_ids: tuple[str, ...]
    unknown_dependency_ids: tuple[str, ...]
    parse_warnings_vi: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvidenceItem:
    """Một bằng chứng nhận diện cụ thể (NET-002 "evidence")."""

    signal: str  # mã ngắn ổn định, vd "pe.clr_data_directory_present"
    detail_vi: str


@dataclass(frozen=True)
class DotnetAnalysisResult:
    """Kết quả phân tích tĩnh một file PE (NET-001/NET-002).

    ``suggested_mode=None`` nghĩa là CHƯA ĐỦ bằng chứng để gợi ý mode —
    tuyệt đối không đoán liều. ``confidence`` trong [0.0, 1.0], chỉ là ước
    lượng heuristic, KHÔNG phải xác suất đã kiểm định."""

    path: str
    kind: PeKind
    architecture: PeArchitecture
    confidence: float
    evidence: tuple[EvidenceItem, ...]
    unknown_dependencies: tuple[str, ...]
    suggested_mode: AppMode | None
    sidecar: SidecarInfo | None
    warnings_vi: tuple[str, ...]
    disclaimer_vi: str = STATIC_ANALYSIS_DISCLAIMER_VI
