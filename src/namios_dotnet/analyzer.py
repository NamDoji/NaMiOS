"""``DotnetAnalyzer`` — orchestrator NET-001/NET-002.

Kết hợp: parse PE/CLR tĩnh (``pe_format``) + sidecar
``.runtimeconfig.json``/``.deps.json`` (``sidecar``) → một
``DotnetAnalysisResult`` (confidence + evidence + unknown_deps +
suggested_mode). KHÔNG BAO GIỜ thực thi file đầu vào (NET-001). PE dị dạng
luôn trả về kết quả (``kind=MALFORMED``/``NOT_PE``, ``confidence=0.0``),
KHÔNG ném ngoại lệ ra ngoài — chỉ lỗi thao tác I/O/an toàn đường dẫn mới là
``DotnetAnalysisError`` (ném ra, caller map exit code)."""

from __future__ import annotations

import os

from namios_core.compat import AppMode
from namios_core.errors import ErrorCode
from namios_dotnet import pe_format
from namios_dotnet._errors import DotnetAnalysisError, MalformedPeError
from namios_dotnet._io import DEFAULT_MAX_PE_BYTES, read_bytes_capped
from namios_dotnet.sidecar import load_sidecar_info
from namios_dotnet.types import (
    ClrHeaderInfo,
    DotnetAnalysisResult,
    EvidenceItem,
    PeArchitecture,
    PeKind,
    SidecarInfo,
)

__all__ = ["DotnetAnalyzer"]

_MACHINE_TO_ARCH: dict[int, PeArchitecture] = {
    0x014C: PeArchitecture.X86,
    0x01C0: PeArchitecture.ARM,
    0x01C4: PeArchitecture.ARM,
    0xAA64: PeArchitecture.ARM64,
    0x0200: PeArchitecture.IA64,
    0x8664: PeArchitecture.X64,
}

_MACHINE_I386 = 0x014C
_OPTIONAL_MAGIC_PE32 = 0x10B


def _classify_architecture(
    machine: int, optional_header_magic: int, clr: ClrHeaderInfo | None
) -> PeArchitecture:
    base = _MACHINE_TO_ARCH.get(machine, PeArchitecture.UNKNOWN)
    if (
        clr is not None
        and machine == _MACHINE_I386
        and optional_header_magic == _OPTIONAL_MAGIC_PE32
        and clr.il_only
        and not clr.requires_32bit
    ):
        # Quy ước phổ biến của compiler .NET: Machine=I386 + PE32 + ILONLY
        # + KHÔNG 32BITREQUIRED ⇒ "AnyCPU" (bitness-agnostic). Đây là suy
        # luận heuristic dựa trên quy ước phát hành thực tế, KHÔNG phải một
        # trường tường minh "platform" trong PE — có thể sai nếu toolchain
        # khác quy ước.
        return PeArchitecture.ANY_CPU
    return base


def _parse_pe_structure(
    data: bytes,
) -> tuple[int, int, ClrHeaderInfo | None, list[EvidenceItem]]:
    """Trả ``(machine, optional_header_magic, clr_info, evidence)``. Ném
    ``MalformedPeError`` nếu cấu trúc PE/COFF cơ bản không đọc được."""

    evidence: list[EvidenceItem] = []

    dos = pe_format.parse_dos_header(data)
    evidence.append(EvidenceItem("pe.dos_signature_mz", "Có chữ ký DOS 'MZ' hợp lệ"))

    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    machine_name = pe_format.MACHINE_NAMES.get(coff.machine, f"0x{coff.machine:x}")
    evidence.append(
        EvidenceItem(
            "pe.coff_signature_valid",
            f"Chữ ký PE 'PE\\0\\0' hợp lệ, Machine={machine_name}, "
            f"NumberOfSections={coff.number_of_sections}",
        )
    )

    optional = pe_format.parse_optional_header(data, coff)
    evidence.append(
        EvidenceItem(
            "pe.optional_header_magic",
            f"OptionalHeader.Magic=0x{optional.magic:x} "
            f"({'PE32+' if optional.is_pe32_plus else 'PE32'})",
        )
    )

    clr_entry = pe_format.parse_data_directory(
        data, optional, pe_format.IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR
    )
    clr_info: ClrHeaderInfo | None = None
    if clr_entry is None or clr_entry.virtual_address == 0 or clr_entry.size == 0:
        evidence.append(
            EvidenceItem(
                "pe.no_clr_data_directory",
                "Không có data directory #14 (CLR Runtime Header) được khai báo",
            )
        )
    else:
        evidence.append(
            EvidenceItem(
                "pe.clr_data_directory_present",
                f"Data directory #14 (CLR) có VA=0x{clr_entry.virtual_address:x}, "
                f"Size={clr_entry.size}",
            )
        )
        sections = pe_format.parse_section_table(data, coff)
        file_offset = pe_format.rva_to_file_offset(sections, clr_entry.virtual_address)
        if file_offset is None:
            evidence.append(
                EvidenceItem(
                    "pe.clr_header_rva_unmapped",
                    "RVA của CLR header không ánh xạ được tới section nào "
                    "(không xác minh thêm được, nhưng data directory vẫn tồn tại)",
                )
            )
        else:
            try:
                raw_clr = pe_format.parse_clr_header(data, file_offset)
            except MalformedPeError:
                evidence.append(
                    EvidenceItem(
                        "pe.clr_header_unreadable",
                        "Có data directory CLR nhưng không đọc được IMAGE_COR20_HEADER "
                        "đầy đủ tại offset đã ánh xạ",
                    )
                )
            else:
                il_only = bool(raw_clr.flags & pe_format.COMIMAGE_FLAGS_ILONLY)
                requires_32bit = bool(raw_clr.flags & pe_format.COMIMAGE_FLAGS_32BITREQUIRED)
                native_entrypoint = bool(raw_clr.flags & pe_format.COMIMAGE_FLAGS_NATIVE_ENTRYPOINT)
                metadata_offset = pe_format.rva_to_file_offset(sections, raw_clr.metadata_rva)
                clr_info = ClrHeaderInfo(
                    major_runtime_version=raw_clr.major_runtime_version,
                    minor_runtime_version=raw_clr.minor_runtime_version,
                    il_only=il_only,
                    requires_32bit=requires_32bit,
                    native_entrypoint=native_entrypoint,
                    metadata_rva=raw_clr.metadata_rva,
                    metadata_size=raw_clr.metadata_size,
                    metadata_mapped=metadata_offset is not None,
                )
                evidence.append(
                    EvidenceItem(
                        "pe.clr_header_parsed",
                        f"IMAGE_COR20_HEADER đọc được: runtime "
                        f"{raw_clr.major_runtime_version}.{raw_clr.minor_runtime_version}, "
                        f"ILONLY={il_only}, 32BITREQUIRED={requires_32bit}, "
                        f"metadata_mapped={metadata_offset is not None}",
                    )
                )

    return coff.machine, optional.magic, clr_info, evidence


def _suggest_mode(kind: PeKind, sidecar: SidecarInfo | None) -> AppMode | None:
    """Gợi ý mode theo NET-002 — CHỈ gợi ý khi có đủ tín hiệu, không đoán
    liều. Quy tắc bắt buộc (test matrix NET-01/NET-04): app có dấu hiệu
    WinForms/WPF (từ sidecar) KHÔNG BAO GIỜ được gợi ý ``native``, bất kể
    TargetFrameworkMoniker có vẻ hiện đại (net6.0+) hay không — vì API
    desktop Windows vẫn cần Wine, không chạy "Linux native" thuần."""

    if kind == PeKind.NATIVE:
        return AppMode.WINE
    if kind == PeKind.MANAGED_MIXED:
        return AppMode.WINE  # có code native (IJW/C++-CLI) ⇒ cần Wine
    if kind == PeKind.MANAGED:
        if sidecar is not None and sidecar.has_windows_desktop_framework:
            return AppMode.WINE
        if sidecar is not None and sidecar.target_framework_moniker is not None:
            tfm = sidecar.target_framework_moniker.lower()
            # .NET (Core) hiện đại, dạng "net5.0".."netN.0" (không phải
            # "net4x" cổ của .NET Framework) ⇒ runtime .NET Linux chạy được
            # trực tiếp, không cần Wine (NET-004 test matrix NET-02).
            if tfm.startswith("net") and not tfm.startswith("netframework"):
                digits = tfm[3:].split("-", 1)[0].split(".", 1)[0]
                if digits.isdigit() and int(digits) >= 5:
                    return AppMode.NATIVE
            return AppMode.WINE  # TFM dạng net4x/.NET Framework cổ ⇒ Wine
        # MANAGED nhưng không có sidecar để biết rõ TFM/desktop framework:
        # chưa đủ bằng chứng để gợi ý Wine hay Native một cách chắc chắn.
        return None
    return None  # NOT_PE / MALFORMED: không gợi ý gì


def _confidence_for(
    kind: PeKind, clr_info: ClrHeaderInfo | None, sidecar: SidecarInfo | None
) -> float:
    if kind in (PeKind.NOT_PE, PeKind.MALFORMED):
        return 0.0
    if kind == PeKind.NATIVE:
        score = 0.9
    elif clr_info is not None and clr_info.metadata_mapped:
        score = 0.9
    elif clr_info is not None:
        score = 0.6  # có CLR header đọc được nhưng MetaData RVA chưa ánh xạ được
    else:
        score = 0.5  # có data directory CLR nhưng không đọc được header
    if sidecar is not None and sidecar.target_framework_moniker is not None:
        score = min(1.0, score + 0.05)
    return score


class DotnetAnalyzer:
    """Phân tích tĩnh một file PE + sidecar đi kèm (NET-001/NET-002)."""

    def __init__(self, *, max_pe_bytes: int = DEFAULT_MAX_PE_BYTES) -> None:
        self._max_pe_bytes = max_pe_bytes

    def analyze(self, path: str) -> DotnetAnalysisResult:
        """Phân tích ``path`` (đường dẫn tuyệt đối). Ném
        ``DotnetAnalysisError`` chỉ khi KHÔNG mở được file an toàn (path
        không hợp lệ/symlink/không tồn tại/không phải file thường) — mọi
        vấn đề về NỘI DUNG PE (dị dạng/cụt) trả về kết quả, không ném."""

        if not path or not os.path.isabs(path):
            raise DotnetAnalysisError(
                code=ErrorCode.E_PATH_UNSAFE, reason_vi="đường dẫn phải tuyệt đối"
            )

        read_result = read_bytes_capped(path, max_bytes=self._max_pe_bytes)
        warnings: list[str] = []
        if read_result.truncated:
            warnings.append(
                f"file vượt giới hạn đọc {self._max_pe_bytes} byte; chỉ phân tích phần đầu "
                "(NET-001 — giới hạn kích thước parser)"
            )
        data = read_result.data

        if len(data) < 2 or data[:2] != b"MZ":
            return DotnetAnalysisResult(
                path=path,
                kind=PeKind.NOT_PE,
                architecture=PeArchitecture.UNKNOWN,
                confidence=0.0,
                evidence=(
                    EvidenceItem(
                        "pe.missing_dos_signature",
                        "File không có chữ ký DOS 'MZ' — không phải PE",
                    ),
                ),
                unknown_dependencies=(),
                suggested_mode=None,
                sidecar=None,
                warnings_vi=tuple(warnings),
            )

        try:
            machine, optional_magic, clr_info, evidence_list = _parse_pe_structure(data)
        except MalformedPeError as exc:
            return DotnetAnalysisResult(
                path=path,
                kind=PeKind.MALFORMED,
                architecture=PeArchitecture.UNKNOWN,
                confidence=0.0,
                evidence=(EvidenceItem("pe.malformed", f"PE dị dạng/cụt: {exc.reason_vi}"),),
                unknown_dependencies=(),
                suggested_mode=None,
                sidecar=None,
                warnings_vi=tuple(warnings),
            )

        evidence: tuple[EvidenceItem, ...] = tuple(evidence_list)

        if clr_info is None:
            kind = PeKind.NATIVE
        elif clr_info.il_only:
            kind = PeKind.MANAGED
        else:
            kind = PeKind.MANAGED_MIXED

        architecture = _classify_architecture(machine, optional_magic, clr_info)

        sidecar: SidecarInfo | None = None
        try:
            sidecar = load_sidecar_info(path)
        except DotnetAnalysisError as exc:
            warnings.append(f"không đọc được sidecar an toàn: {exc.reason_vi}")

        if sidecar is not None:
            evidence = evidence + (
                EvidenceItem(
                    (
                        "sidecar.runtimeconfig_present"
                        if sidecar.runtimeconfig_path
                        else "sidecar.deps_json_present"
                    ),
                    f"Đọc được sidecar đi kèm: tfm={sidecar.target_framework_moniker}, "
                    f"frameworks={list(sidecar.framework_names)}, "
                    f"windows_desktop={sidecar.has_windows_desktop_framework}",
                ),
            )
            if sidecar.has_windows_desktop_framework and kind == PeKind.MANAGED:
                evidence = evidence + (
                    EvidenceItem(
                        "sidecar.windows_desktop_requires_wine",
                        "Phát hiện framework desktop Windows (WinForms/WPF) qua sidecar — "
                        "KHÔNG coi là 'Linux native' dù TargetFramework hiện đại",
                    ),
                )
            warnings.extend(sidecar.parse_warnings_vi)

        unknown_dependencies = sidecar.unknown_dependency_ids if sidecar is not None else ()
        confidence = _confidence_for(kind, clr_info, sidecar)
        suggested_mode = _suggest_mode(kind, sidecar)

        return DotnetAnalysisResult(
            path=path,
            kind=kind,
            architecture=architecture,
            confidence=confidence,
            evidence=evidence,
            unknown_dependencies=unknown_dependencies,
            suggested_mode=suggested_mode,
            sidecar=sidecar,
            warnings_vi=tuple(warnings),
        )
