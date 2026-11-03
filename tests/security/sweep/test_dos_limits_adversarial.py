"""DoS adversarial — gioi han kich thuoc/do sau parser (NET-001/NET-004).
Pham vi: ``namios_dotnet`` (PE parser + read cap), ``namios_evidence``
(2 MiB cap — xem file rieng), ``namios_manifest`` (2 MiB cap — xem file
rieng ve TOCTOU, nhung cap duoc kiem o day doc lap voi finding TOCTOU)."""

from __future__ import annotations

import struct

import pytest

from namios_dotnet._errors import MalformedPeError
from namios_dotnet._io import read_bytes_capped
from namios_dotnet.analyzer import DotnetAnalyzer
from namios_dotnet.pe_format import (
    MAX_DATA_DIRECTORIES,
    MAX_SECTIONS,
    parse_coff_header,
    parse_dos_header,
    parse_optional_header,
)
from namios_manifest._safe_io import PathUnsafeError as ManifestPathUnsafeError
from namios_manifest._safe_io import read_text_safe as manifest_read_text_safe

# ---------------------------------------------------------------------------
# PE/COFF header — tu choi NumberOfSections/NumberOfRvaAndSizes gia mao cuc
# lon TRUOC khi vong lap/doc tiep (MAX_SECTIONS/MAX_DATA_DIRECTORIES).
# ---------------------------------------------------------------------------


def _build_minimal_pe_header(
    *, number_of_sections: int, size_of_optional_header: int = 224
) -> bytes:
    data = bytearray(b"\x00" * 4096)
    data[0:2] = b"MZ"
    e_lfanew = 0x80
    struct.pack_into("<I", data, 0x3C, e_lfanew)
    data[e_lfanew : e_lfanew + 4] = b"PE\x00\x00"
    coff_offset = e_lfanew + 4
    struct.pack_into(
        "<HHIIIHH",
        data,
        coff_offset,
        0x8664,  # machine AMD64
        number_of_sections,
        0,
        0,
        0,
        size_of_optional_header,
        0,
    )
    optional_offset = coff_offset + 20
    struct.pack_into("<H", data, optional_offset, 0x20B)  # PE32+
    return bytes(data)


def test_parse_coff_header_rejects_number_of_sections_above_max() -> None:
    data = _build_minimal_pe_header(number_of_sections=MAX_SECTIONS + 1)
    dos = parse_dos_header(data)
    with pytest.raises(MalformedPeError):
        parse_coff_header(data, dos.e_lfanew)


def test_parse_coff_header_accepts_number_of_sections_exactly_at_max() -> None:
    data = _build_minimal_pe_header(number_of_sections=MAX_SECTIONS)
    dos = parse_dos_header(data)
    coff = parse_coff_header(data, dos.e_lfanew)
    assert coff.number_of_sections == MAX_SECTIONS


def test_parse_coff_header_rejects_number_of_sections_at_uint16_max_without_hanging() -> None:
    """Gia mao gia tri lon nhat co the cho field unsigned short (65535) --
    PHAI bi chan boi MAX_SECTIONS, khong duoc chay vong lap 65535 lan."""

    data = _build_minimal_pe_header(number_of_sections=0xFFFF)
    dos = parse_dos_header(data)
    with pytest.raises(MalformedPeError):
        parse_coff_header(data, dos.e_lfanew)


def test_parse_optional_header_rejects_number_of_rva_and_sizes_above_max() -> None:
    data = bytearray(_build_minimal_pe_header(number_of_sections=1))
    dos = parse_dos_header(bytes(data))
    coff = parse_coff_header(bytes(data), dos.e_lfanew)
    rva_count_offset = coff.optional_header_offset + 108  # PE32+ offset
    struct.pack_into("<I", data, rva_count_offset, MAX_DATA_DIRECTORIES + 1)

    with pytest.raises(MalformedPeError):
        parse_optional_header(bytes(data), coff)


def test_parse_dos_header_rejects_e_lfanew_pointing_far_beyond_buffer() -> None:
    data = bytearray(b"MZ" + b"\x00" * 62)
    struct.pack_into("<I", data, 0x3C, 10_000_000)  # vuot xa kich thuoc buffer

    with pytest.raises(MalformedPeError):
        parse_dos_header(bytes(data))


def test_parse_dos_header_rejects_negative_looking_e_lfanew_wraparound() -> None:
    data = bytearray(b"MZ" + b"\x00" * 62)
    struct.pack_into("<I", data, 0x3C, 0xFFFFFFFF)  # unsigned wrap cho "-1"

    with pytest.raises(MalformedPeError):
        parse_dos_header(bytes(data))


# ---------------------------------------------------------------------------
# read_bytes_capped — file PE khong tin cay vuot gioi han bi cat, khong doc
# toan bo vao RAM.
# ---------------------------------------------------------------------------


def test_read_bytes_capped_truncates_oversized_file_instead_of_reading_all(tmp_path) -> None:
    huge = tmp_path / "huge.exe"
    huge.write_bytes(b"A" * (1024 * 1024))  # 1 MiB

    result = read_bytes_capped(str(huge), max_bytes=1024)
    assert len(result.data) == 1024
    assert result.truncated is True


def test_analyzer_handles_oversized_pe_without_reading_entire_file(tmp_path) -> None:
    """Gia mao file PE 'khong lo' (vuot DEFAULT_MAX_PE_BYTES) -- analyzer
    KHONG duoc crash/doc het, phai tra warning truncated va van tra ve mot
    ket qua (khong raise)."""

    huge = tmp_path / "huge_app.exe"
    pe_header = _build_minimal_pe_header(number_of_sections=1)
    # Lam file lon hon 8 MiB (DEFAULT_MAX_PE_BYTES) bang padding.
    huge.write_bytes(pe_header + b"\x00" * (9 * 1024 * 1024))

    analyzer = DotnetAnalyzer()
    result = analyzer.analyze(str(huge))
    assert any("vượt giới hạn đọc" in w for w in result.warnings_vi)


# ---------------------------------------------------------------------------
# namios_manifest._safe_io — gioi han kich thuoc doc (doc lap voi finding
# TOCTOU o file rieng; o day chi kiem cap/DoS).
# ---------------------------------------------------------------------------


def test_manifest_read_text_safe_rejects_file_over_2mib(tmp_path) -> None:
    huge = tmp_path / "huge.manifest.json"
    huge.write_bytes(b"{" + b"0" * (2 * 1024 * 1024 + 10) + b"}")

    with pytest.raises(ManifestPathUnsafeError):
        manifest_read_text_safe(str(huge))


def test_manifest_read_text_safe_accepts_file_exactly_at_limit(tmp_path) -> None:
    exact = tmp_path / "exact.manifest.json"
    exact.write_bytes(b"0" * (2 * 1024 * 1024))

    content = manifest_read_text_safe(str(exact))
    assert len(content) == 2 * 1024 * 1024
