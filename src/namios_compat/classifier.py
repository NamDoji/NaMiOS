"""Bộ phân loại runtime Windows tĩnh (COMP-028, Phụ lục 03).

Kết hợp kết quả ``namios_dotnet.DotnetAnalyzer`` (managed/native + sidecar
``.runtimeconfig.json``/``.deps.json``) với một phép đọc nhỏ, độc lập, bị
giới hạn kích thước cho trường ``Subsystem`` của Optional Header PE —
``namios_dotnet.pe_format`` hiện KHÔNG expose trường này (chỉ đọc tới
``Magic``/``NumberOfRvaAndSizes``/``DataDirectory[]``) nên module này tự đọc
thêm, dùng cùng công thức offset theo đặc tả PE/COFF công khai của Microsoft:
``Subsystem`` nằm ở offset 68 tính từ đầu Optional Header, GIỐNG NHAU cho cả
PE32 và PE32+ (chênh lệch ``ImageBase`` 4↔8 byte bù đúng cho trường
``BaseOfData`` chỉ tồn tại ở PE32, nằm trước offset đó).

Nhãn trả về LUÔN là phát hiện/suy đoán/chưa rõ (``ClassificationConfidence``)
— KHÔNG BAO GIỜ suy từ đuôi file (``.exe``/``.dll``/``.sys``), chỉ từ cấu
trúc nhị phân + sidecar đã phân tích tĩnh. KHÔNG BAO GIỜ thực thi file đầu
vào (kế thừa bất biến NET-001 của ``namios_dotnet``).

``wine_blocker`` chỉ được suy ra từ tập nhãn đã xác định có mặt trong
``WINE_BLOCKER_KINDS`` (COMP-028) — hiện tại CHỈ ``KERNEL_DRIVER`` được gán
tĩnh ở đây (``ANTICHEAT_DRM`` chưa có tín hiệu tĩnh đáng tin cậy ở Pha A;
không bịa chữ ký)."""

from __future__ import annotations

import struct

from namios_compat import _i18n as _i18n  # noqa: F401
from namios_compat._types import (
    WINE_BLOCKER_KINDS,
    ClassificationConfidence,
    RuntimeClassification,
    RuntimeKind,
)
from namios_core.compat import AppMode
from namios_dotnet import DotnetAnalysisResult, DotnetAnalyzer, PeKind
from namios_i18n import Lang, t

__all__ = ["classify_runtime"]

#: IMAGE_SUBSYSTEM_NATIVE (đặc tả PE/COFF công khai của Microsoft) — ảnh PE
#: nhắm tới subsystem "native" (kernel-mode driver, không có user-mode
#: subsystem Windows/Console thông thường) ⇒ KHÓA đường Wine (Wine không
#: phải Windows kernel, không nạp được driver nhân).
_IMAGE_SUBSYSTEM_NATIVE = 1

#: Offset (byte) của trường ``Subsystem`` (2 byte, little-endian) TÍNH TỪ
#: ĐẦU Optional Header — giống nhau cho IMAGE_OPTIONAL_HEADER32 (PE32) và
#: IMAGE_OPTIONAL_HEADER64 (PE32+).
_SUBSYSTEM_OFFSET_IN_OPTIONAL_HEADER = 68

_DOS_E_LFANEW_OFFSET = 0x3C
_PE_SIGNATURE = b"PE\x00\x00"
_OPTIONAL_MAGIC_PE32 = 0x10B
_OPTIONAL_MAGIC_PE32_PLUS = 0x20B

#: Giới hạn đọc riêng cho dò ``Subsystem`` — chỉ cần vùng header đầu file
#: (DOS+COFF+Optional header nằm trong vài trăm byte đầu với mọi PE thật),
#: KHÔNG cần đọc toàn bộ nội dung (DoS-safe trên file đầu vào không tin cậy,
#: cùng chừng mực với ``namios_dotnet._io.DEFAULT_MAX_PE_BYTES`` nhưng nhỏ
#: hơn nhiều vì chỉ cần header).
_MAX_HEADER_PROBE_BYTES = 64 * 1024

#: Tiền tố TFM .NET (Core) hiện đại, đa nền tảng (NET-004/"net≥5") — KHÔNG
#: gồm các TFM .NET Framework cổ dạng "net4x"/"net48" (vẫn bắt đầu bằng
#: "net4", không khớp tiền tố nào dưới đây).
_MODERN_TFM_PREFIXES: tuple[str, ...] = (
    "net5",
    "net6",
    "net7",
    "net8",
    "net9",
    "net10",
    "netcoreapp",
)

#: Chuỗi con (so khớp không phân biệt hoa/thường) cho biết phụ thuộc SQL
#: Server client — cần cấu hình DB đúng phiên bản (COMP-038), không đổi
#: suggested_mode (additive).
_SQLSERVER_MARKERS: tuple[str, ...] = (
    "sqlclient",
    "sql server",
    "system.data.sqlclient",
    "microsoft.data.sqlclient",
)


def _detect_native_subsystem(path: str) -> bool:
    """``True`` nếu Optional Header ``Subsystem`` == ``IMAGE_SUBSYSTEM_NATIVE``
    (driver/native subsystem — tín hiệu kernel driver tĩnh duy nhất của Pha
    A). Đọc TỐI THIỂU (chỉ vùng header), bounds-checked bằng ``struct``,
    KHÔNG BAO GIỜ ném ngoại lệ: mọi lỗi mở file/offset vượt giới hạn/PE dị
    dạng/cụt được coi là "không có tín hiệu kernel driver" (trả ``False``),
    KHÔNG chặn luồng phân loại chính (caller vẫn tiếp tục dùng
    ``DotnetAnalysisResult`` đã có).

    ĐỘC LẬP với ``namios_dotnet.pe_format``: module đó hiện chỉ parse tới
    ``Magic``/``NumberOfRvaAndSizes``/``DataDirectory[]`` của Optional
    Header, KHÔNG expose ``Subsystem`` — nên hàm này tự đọc lại DOS/COFF/
    Optional header bằng một phép ``struct.unpack_from`` nhỏ, không chỉnh
    sửa/mở rộng module ``namios_dotnet`` (ngoài phạm vi sở hữu module này)."""

    try:
        with open(path, "rb") as fh:
            data = fh.read(_MAX_HEADER_PROBE_BYTES)
    except OSError:
        return False

    if len(data) < 2 or data[:2] != b"MZ":
        return False

    try:
        (e_lfanew,) = struct.unpack_from("<I", data, _DOS_E_LFANEW_OFFSET)
        if data[e_lfanew : e_lfanew + 4] != _PE_SIGNATURE:
            return False
        coff_offset = e_lfanew + 4
        (
            _machine,
            _number_of_sections,
            _time_date_stamp,
            _ptr_symtab,
            _num_symbols,
            size_of_optional_header,
            _characteristics,
        ) = struct.unpack_from("<HHIIIHH", data, coff_offset)
        optional_offset = coff_offset + 20
        if size_of_optional_header < _SUBSYSTEM_OFFSET_IN_OPTIONAL_HEADER + 2:
            return False
        (magic,) = struct.unpack_from("<H", data, optional_offset)
        if magic not in (_OPTIONAL_MAGIC_PE32, _OPTIONAL_MAGIC_PE32_PLUS):
            return False
        (subsystem,) = struct.unpack_from(
            "<H", data, optional_offset + _SUBSYSTEM_OFFSET_IN_OPTIONAL_HEADER
        )
    except struct.error:
        return False

    return bool(subsystem == _IMAGE_SUBSYSTEM_NATIVE)


def _is_modern_tfm(tfm_lower: str) -> bool:
    """``True`` nếu TFM (đã lowercase) là .NET (Core) hiện đại net≥5/
    netcoreapp — KHÔNG gồm TFM .NET Framework cổ ("net4x"/"net48"/
    ``.NETFramework``)."""

    return any(tfm_lower.startswith(prefix) for prefix in _MODERN_TFM_PREFIXES)


def _collect_dependency_strings(result: DotnetAnalysisResult) -> tuple[str, ...]:
    """Tập hợp (lowercase) mọi chuỗi phụ thuộc đã biết từ kết quả phân tích:
    ``sidecar.declared_library_ids`` + ``sidecar.unknown_dependency_ids`` +
    ``result.unknown_dependencies`` — dùng cho tín hiệu bổ sung (WebView2/SQL
    Server client), KHÔNG đổi ``suggested_mode``."""

    values: list[str] = list(result.unknown_dependencies)
    if result.sidecar is not None:
        values.extend(result.sidecar.declared_library_ids)
        values.extend(result.sidecar.unknown_dependency_ids)
    return tuple(v.lower() for v in values)


def _dedupe_kinds(kinds: list[RuntimeKind]) -> tuple[RuntimeKind, ...]:
    """Khử trùng lặp GIỮ THỨ TỰ xuất hiện đầu tiên (tất định) — ``kinds``
    không bao giờ rỗng: dùng ``(UNKNOWN,)`` làm sàn khi danh sách đầu vào
    rỗng."""

    seen: set[RuntimeKind] = set()
    ordered: list[RuntimeKind] = []
    for kind in kinds:
        if kind not in seen:
            seen.add(kind)
            ordered.append(kind)
    if not ordered:
        return (RuntimeKind.UNKNOWN,)
    return tuple(ordered)


def classify_runtime(path: str, *, analyzer: DotnetAnalyzer | None = None) -> RuntimeClassification:
    """Phân loại runtime Windows tĩnh của file tại ``path`` (COMP-028).

    Chạy ``DotnetAnalyzer.analyze(path)`` (tạo analyzer mặc định nếu
    ``analyzer`` không truyền) rồi suy ra nhãn ``RuntimeKind`` theo các quy
    tắc Phụ lục 03 §COMP-028. Ném ``DotnetAnalysisError`` NGUYÊN VẸN (không
    bắt/biến đổi) nếu ``analyzer.analyze`` không mở được ``path`` an toàn —
    caller xử lý lỗi đường dẫn, hàm này chỉ xử lý KẾT QUẢ phân tích hợp lệ
    (kể cả PE dị dạng, vốn vẫn trả kết quả thay vì ném lỗi)."""

    active_analyzer = analyzer if analyzer is not None else DotnetAnalyzer()
    result = active_analyzer.analyze(path)

    disclaimer_vi = t("compat.classifier.disclaimer", lang=Lang.VI)

    if result.kind in (PeKind.NOT_PE, PeKind.MALFORMED):
        return RuntimeClassification(
            path=path,
            kinds=(RuntimeKind.UNKNOWN,),
            confidence=ClassificationConfidence.UNKNOWN,
            wine_blocker=False,
            suggested_mode=None,
            evidence_vi=(t("compat.classifier.evidence.unknown", lang=Lang.VI),),
            disclaimer_vi=disclaimer_vi,
        )

    # Kernel-driver / native-subsystem: tín hiệu ĐỘC LẬP với managed/native,
    # kiểm TRƯỚC các nhánh managed/native (COMP-028 §3 ưu tiên blocker).
    if _detect_native_subsystem(path):
        return RuntimeClassification(
            path=path,
            kinds=(RuntimeKind.KERNEL_DRIVER,),
            confidence=ClassificationConfidence.DETECTED,
            wine_blocker=True,
            suggested_mode=None,
            evidence_vi=(t("compat.classifier.evidence.kernel_driver", lang=Lang.VI),),
            disclaimer_vi=disclaimer_vi,
        )

    kinds: list[RuntimeKind] = []
    evidence: list[str] = []
    confidence = ClassificationConfidence.UNKNOWN
    suggested_mode: AppMode | None = None
    sidecar = result.sidecar

    if result.kind in (PeKind.MANAGED, PeKind.MANAGED_MIXED):
        if sidecar is not None and sidecar.has_windows_desktop_framework:
            # .NET desktop Windows (WinForms/WPF) — không thể phân biệt tĩnh
            # chắc chắn WinForms vs WPF, đưa CẢ HAI làm ứng viên "suy đoán".
            kinds = [RuntimeKind.DOTNET_FRAMEWORK, RuntimeKind.WINFORMS, RuntimeKind.WPF]
            evidence = [t("compat.classifier.evidence.dotnet_framework", lang=Lang.VI)]
            confidence = ClassificationConfidence.DETECTED
            suggested_mode = AppMode.WINE
        elif sidecar is not None and sidecar.target_framework_moniker is not None:
            tfm_lower = sidecar.target_framework_moniker.lower()
            if _is_modern_tfm(tfm_lower):
                kinds = [RuntimeKind.DOTNET_MODERN]
                evidence = [t("compat.classifier.evidence.dotnet_modern", lang=Lang.VI)]
                confidence = ClassificationConfidence.DETECTED
                suggested_mode = AppMode.NATIVE
            else:
                # TFM dạng "net4x"/.NETFramework cổ (hoặc không nhận diện
                # được là hiện đại) ⇒ coi là .NET Framework, thử Wine.
                kinds = [RuntimeKind.DOTNET_FRAMEWORK]
                evidence = [t("compat.classifier.evidence.dotnet_framework", lang=Lang.VI)]
                confidence = ClassificationConfidence.DETECTED
                suggested_mode = AppMode.WINE
        else:
            # MANAGED/MANAGED_MIXED không có sidecar hữu ích (hoặc TFM mập
            # mờ): chưa đủ chắc để DETECTED, nhưng vẫn RÕ là managed .NET
            # nào đó — dùng suggested_mode mà DotnetAnalyzer TỰ suy luận
            # (NET-002, không đoán liều hơn những gì analyzer đã có).
            suggested_mode = result.suggested_mode
            confidence = ClassificationConfidence.INFERRED
            if suggested_mode == AppMode.NATIVE:
                kinds = [RuntimeKind.DOTNET_MODERN]
                evidence = [t("compat.classifier.evidence.dotnet_modern", lang=Lang.VI)]
            elif suggested_mode == AppMode.WINE:
                kinds = [RuntimeKind.DOTNET_FRAMEWORK]
                evidence = [t("compat.classifier.evidence.dotnet_framework", lang=Lang.VI)]
            else:
                kinds = [RuntimeKind.UNKNOWN]
                evidence = [t("compat.classifier.evidence.unknown", lang=Lang.VI)]
    elif result.kind == PeKind.NATIVE:
        kinds = [RuntimeKind.NATIVE_WIN32]
        evidence = [t("compat.classifier.evidence.native_win32", lang=Lang.VI)]
        confidence = ClassificationConfidence.DETECTED
        suggested_mode = AppMode.WINE
    else:  # pragma: no cover - PeKind chỉ còn NOT_PE/MALFORMED, đã trả sớm.
        kinds = [RuntimeKind.UNKNOWN]
        evidence = [t("compat.classifier.evidence.unknown", lang=Lang.VI)]
        confidence = ClassificationConfidence.UNKNOWN

    # Tín hiệu phụ thuộc BỔ SUNG (additive) — KHÔNG đổi suggested_mode.
    dependency_strings = _collect_dependency_strings(result)
    if any("webview2" in dep for dep in dependency_strings):
        kinds.append(RuntimeKind.WEBVIEW2)
        evidence.append(t("compat.classifier.evidence.webview2", lang=Lang.VI))
    if any(marker in dep for dep in dependency_strings for marker in _SQLSERVER_MARKERS):
        kinds.append(RuntimeKind.SQLSERVER_CLIENT)
        evidence.append(t("compat.classifier.evidence.sqlserver_client", lang=Lang.VI))

    deduped_kinds = _dedupe_kinds(kinds)
    wine_blocker = any(kind in WINE_BLOCKER_KINDS for kind in deduped_kinds)

    return RuntimeClassification(
        path=path,
        kinds=deduped_kinds,
        confidence=confidence,
        wine_blocker=wine_blocker,
        suggested_mode=suggested_mode,
        evidence_vi=tuple(evidence),
        disclaimer_vi=disclaimer_vi,
    )
