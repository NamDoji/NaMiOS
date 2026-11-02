"""Unit test tầng ``pe_format`` — struct parsing thuần, không I/O
(NET-001). Dùng ``fixtures/dotnet/pe_builder.py`` để dựng byte trực tiếp
trong test (không cần đọc file) + test riêng các hàm bounds/limit."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "fixtures" / "dotnet"))
import pe_builder  # type: ignore[import-not-found]  # noqa: E402

from namios_dotnet import MalformedPeError, pe_format


def test_parse_dos_header_valid() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    assert dos.e_lfanew == 64


def test_parse_dos_header_missing_mz_signature() -> None:
    with pytest.raises(MalformedPeError):
        pe_format.parse_dos_header(b"\x00\x00not MZ at all")


def test_parse_dos_header_truncated_before_e_lfanew() -> None:
    with pytest.raises(MalformedPeError):
        pe_format.parse_dos_header(pe_builder.build_truncated_mz())


def test_parse_dos_header_rejects_e_lfanew_beyond_buffer() -> None:
    buf = bytearray(pe_builder.build_dos_header(e_lfanew=10_000_000))
    with pytest.raises(MalformedPeError):
        pe_format.parse_dos_header(bytes(buf))


def test_parse_coff_header_native_pe32plus() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    assert coff.machine == pe_builder.MACHINE_AMD64
    assert coff.number_of_sections == 1


def test_parse_coff_header_missing_pe_signature() -> None:
    data = pe_builder.build_dos_header(e_lfanew=64) + b"NOTAPE00" + b"\x00" * 40
    with pytest.raises(MalformedPeError):
        pe_format.parse_coff_header(data, 64)


def test_parse_coff_header_rejects_absurd_number_of_sections() -> None:
    data = (
        pe_builder.build_dos_header(e_lfanew=64)
        + b"PE\x00\x00"
        + struct.pack("<HHIIIHH", pe_builder.MACHINE_I386, 60000, 0, 0, 0, 0, 0)
    )
    with pytest.raises(MalformedPeError):
        pe_format.parse_coff_header(data, 64)


def test_parse_optional_header_pe32_plus_magic() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    optional = pe_format.parse_optional_header(data, coff)
    assert optional.is_pe32_plus is True
    assert optional.number_of_rva_and_sizes == 16


def test_parse_optional_header_unknown_magic_is_malformed() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    mutated = bytearray(data)
    struct.pack_into("<H", mutated, coff.optional_header_offset, 0xDEAD)
    with pytest.raises(MalformedPeError):
        pe_format.parse_optional_header(bytes(mutated), coff)


def test_parse_optional_header_rejects_absurd_number_of_rva_and_sizes() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    mutated = bytearray(data)
    struct.pack_into("<I", mutated, coff.optional_header_offset + 108, 999_999)
    with pytest.raises(MalformedPeError):
        pe_format.parse_optional_header(bytes(mutated), coff)


def test_data_directory_absent_when_number_of_rva_and_sizes_too_small() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    optional = pe_format.parse_optional_header(data, coff)
    mutated_optional = pe_format.OptionalHeaderInfo(
        magic=optional.magic,
        is_pe32_plus=optional.is_pe32_plus,
        number_of_rva_and_sizes=2,
        data_directory_offset=optional.data_directory_offset,
    )
    entry = pe_format.parse_data_directory(data, mutated_optional, 14)
    assert entry is None


def test_native_pe_has_no_clr_data_directory() -> None:
    data = pe_builder.build_native_pe32plus_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    optional = pe_format.parse_optional_header(data, coff)
    entry = pe_format.parse_data_directory(
        data, optional, pe_format.IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR
    )
    assert entry is not None
    assert entry.virtual_address == 0
    assert entry.size == 0


def test_managed_pe_has_clr_data_directory_mapped_to_section() -> None:
    data = pe_builder.build_managed_pe32_anycpu_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    optional = pe_format.parse_optional_header(data, coff)
    entry = pe_format.parse_data_directory(
        data, optional, pe_format.IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR
    )
    assert entry is not None
    assert entry.virtual_address != 0
    assert entry.size != 0

    sections = pe_format.parse_section_table(data, coff)
    assert len(sections) == 1
    file_offset = pe_format.rva_to_file_offset(sections, entry.virtual_address)
    assert file_offset is not None

    clr = pe_format.parse_clr_header(data, file_offset)
    assert clr.flags & pe_format.COMIMAGE_FLAGS_ILONLY
    assert not (clr.flags & pe_format.COMIMAGE_FLAGS_32BITREQUIRED)

    metadata_offset = pe_format.rva_to_file_offset(sections, clr.metadata_rva)
    assert metadata_offset is not None


def test_rva_to_file_offset_returns_none_for_unmapped_rva() -> None:
    data = pe_builder.build_managed_pe32_anycpu_minimal()
    dos = pe_format.parse_dos_header(data)
    coff = pe_format.parse_coff_header(data, dos.e_lfanew)
    sections = pe_format.parse_section_table(data, coff)
    assert pe_format.rva_to_file_offset(sections, 0xFFFF_FFF0) is None


def test_parse_clr_header_malformed_when_truncated() -> None:
    with pytest.raises(MalformedPeError):
        pe_format.parse_clr_header(b"\x00" * 4, 0)


def test_parse_section_table_rejects_too_many_sections_at_coff_stage() -> None:
    data = (
        pe_builder.build_dos_header(e_lfanew=64)
        + b"PE\x00\x00"
        + struct.pack(
            "<HHIIIHH", pe_builder.MACHINE_I386, pe_format.MAX_SECTIONS + 1, 0, 0, 0, 0, 0
        )
    )
    with pytest.raises(MalformedPeError):
        pe_format.parse_coff_header(data, 64)
