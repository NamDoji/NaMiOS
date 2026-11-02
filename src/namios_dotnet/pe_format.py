"""Parser PE/COFF + CLR header THUẦN STRUCT — KHÔNG thực thi, KHÔNG dùng thư
viện thực thi (NET-001). Chỉ đọc cấu trúc nhị phân đã có trong bộ nhớ
(``bytes``) bằng ``struct.unpack_from``.

An toàn (NET-001/NET-004):

- Toàn bộ hàm nhận một buffer ``bytes`` ĐÃ bị giới hạn kích thước từ trước
  (xem ``namios_dotnet._io``) — không có hàm nào tự mở file.
- ``struct.unpack_from`` tự kiểm tra ``offset + size <= len(buffer)`` và ném
  ``struct.error`` nếu thiếu dữ liệu — KHÔNG đọc ra ngoài buffer (Python an
  toàn bộ nhớ nội tại); ta bắt lỗi này và quy về ``MalformedPeError`` thống
  nhất, không để ngoại lệ lạ rò ra ngoài.
- Số lượng section / data directory được CHẶN TRÊN bằng hằng số
  ``MAX_SECTIONS``/``MAX_DATA_DIRECTORIES`` để tránh một trường giả mạo
  cực lớn khiến vòng lặp chạy quá lâu/quá sâu (độ sâu bị giới hạn), dù buffer
  hữu hạn đã tự chặn việc đọc vượt giới hạn.
- KHÔNG có nhánh nào gọi ``exec``/``subprocess``/``importlib``/``eval`` trên
  nội dung PE. File đầu vào bị coi là KHÔNG tin cậy tuyệt đối.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from namios_dotnet._errors import MalformedPeError

__all__ = [
    "MAX_SECTIONS",
    "MAX_DATA_DIRECTORIES",
    "IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR",
    "COMIMAGE_FLAGS_ILONLY",
    "COMIMAGE_FLAGS_32BITREQUIRED",
    "COMIMAGE_FLAGS_NATIVE_ENTRYPOINT",
    "MACHINE_NAMES",
    "DosHeader",
    "CoffHeader",
    "OptionalHeaderInfo",
    "DataDirectoryEntry",
    "SectionHeader",
    "ClrHeaderRaw",
    "parse_dos_header",
    "parse_coff_header",
    "parse_optional_header",
    "parse_section_table",
    "parse_data_directory",
    "rva_to_file_offset",
    "parse_clr_header",
]

# --- Hằng số định dạng PE/COFF (đặc tả công khai Microsoft PE/COFF — chỉ
# kiến thức định dạng file, KHÔNG phải nội dung có bản quyền/binary). ---

_DOS_MAGIC = b"MZ"
_DOS_E_LFANEW_OFFSET = 0x3C
_PE_SIGNATURE = b"PE\x00\x00"

_MACHINE_I386 = 0x014C
_MACHINE_ARM = 0x01C0
_MACHINE_ARMNT = 0x01C4
_MACHINE_ARM64 = 0xAA64
_MACHINE_IA64 = 0x0200
_MACHINE_AMD64 = 0x8664

MACHINE_NAMES: dict[int, str] = {
    0x0000: "UNKNOWN",
    _MACHINE_I386: "I386",
    _MACHINE_ARM: "ARM",
    _MACHINE_ARMNT: "ARMNT",
    _MACHINE_ARM64: "ARM64",
    _MACHINE_IA64: "IA64",
    _MACHINE_AMD64: "AMD64",
}

_OPTIONAL_MAGIC_PE32 = 0x10B
_OPTIONAL_MAGIC_PE32_PLUS = 0x20B

# Offset (tương đối optional header) tới NumberOfRvaAndSizes + nơi
# DataDirectory[] bắt đầu — khác nhau giữa PE32 và PE32+ vì các trường
# ImageBase/Stack/Heap 4-byte (PE32) hay 8-byte (PE32+).
_PE32_NUMBER_OF_RVA_AND_SIZES_OFFSET = 92
_PE32_DATA_DIRECTORY_OFFSET = 96
_PE32PLUS_NUMBER_OF_RVA_AND_SIZES_OFFSET = 108
_PE32PLUS_DATA_DIRECTORY_OFFSET = 112

#: Chỉ số data directory #14 = "CLR Runtime Header" (COM Descriptor) —
#: dấu hiệu quyết định managed vs native (NET-001/002).
IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR = 14

#: Cờ ``IMAGE_COR20_HEADER.Flags`` liên quan (COMIMAGE_FLAGS_*).
COMIMAGE_FLAGS_ILONLY = 0x00000001
COMIMAGE_FLAGS_32BITREQUIRED = 0x00000002
COMIMAGE_FLAGS_NATIVE_ENTRYPOINT = 0x00000010

#: Chặn trên số section/data-directory để giới hạn thời gian/độ sâu vòng lặp
#: dù buffer đã hữu hạn (phòng trường giả mạo cực lớn — NET-001/004).
MAX_SECTIONS = 96
MAX_DATA_DIRECTORIES = 32


def _unpack(fmt: str, data: bytes, offset: int, what: str) -> tuple[object, ...]:
    try:
        return struct.unpack_from(fmt, data, offset)
    except struct.error as exc:
        raise MalformedPeError(
            reason_vi=f"thiếu dữ liệu để đọc {what} tại offset {offset}"
        ) from exc


@dataclass(frozen=True)
class DosHeader:
    e_lfanew: int


def parse_dos_header(data: bytes) -> DosHeader:
    """Đọc ``IMAGE_DOS_HEADER`` tối thiểu: chữ ký ``MZ`` + ``e_lfanew``.

    Ném ``MalformedPeError`` nếu thiếu chữ ký/dữ liệu hoặc ``e_lfanew`` âm
    hay vượt kích thước hợp lý (chặn offset vô lý, không đi tiếp)."""

    if len(data) < 2 or data[:2] != _DOS_MAGIC:
        raise MalformedPeError(reason_vi="thiếu chữ ký DOS 'MZ' ở đầu file")
    (e_lfanew,) = _unpack("<I", data, _DOS_E_LFANEW_OFFSET, "e_lfanew")
    assert isinstance(e_lfanew, int)
    if e_lfanew < 0 or e_lfanew > len(data):
        raise MalformedPeError(reason_vi=f"e_lfanew={e_lfanew} vượt ngoài kích thước buffer đã đọc")
    return DosHeader(e_lfanew=e_lfanew)


@dataclass(frozen=True)
class CoffHeader:
    machine: int
    number_of_sections: int
    size_of_optional_header: int
    characteristics: int
    optional_header_offset: int
    section_table_offset: int


def parse_coff_header(data: bytes, pe_header_offset: int) -> CoffHeader:
    """Đọc chữ ký ``PE\\0\\0`` + ``IMAGE_FILE_HEADER`` (20 byte) tại
    ``pe_header_offset`` (= ``e_lfanew``)."""

    sig = data[pe_header_offset : pe_header_offset + 4]
    if sig != _PE_SIGNATURE:
        raise MalformedPeError(
            reason_vi=f"thiếu chữ ký PE 'PE\\0\\0' tại offset {pe_header_offset}"
        )
    coff_offset = pe_header_offset + 4
    (
        machine,
        number_of_sections,
        _time_date_stamp,
        _ptr_symtab,
        _num_symbols,
        size_of_optional_header,
        characteristics,
    ) = _unpack("<HHIIIHH", data, coff_offset, "IMAGE_FILE_HEADER")
    assert isinstance(machine, int)
    assert isinstance(number_of_sections, int)
    assert isinstance(size_of_optional_header, int)
    assert isinstance(characteristics, int)
    if number_of_sections > MAX_SECTIONS:
        raise MalformedPeError(
            reason_vi=f"NumberOfSections={number_of_sections} vượt giới hạn {MAX_SECTIONS}"
        )
    optional_header_offset = coff_offset + 20
    section_table_offset = optional_header_offset + size_of_optional_header
    return CoffHeader(
        machine=machine,
        number_of_sections=number_of_sections,
        size_of_optional_header=size_of_optional_header,
        characteristics=characteristics,
        optional_header_offset=optional_header_offset,
        section_table_offset=section_table_offset,
    )


@dataclass(frozen=True)
class OptionalHeaderInfo:
    magic: int
    is_pe32_plus: bool
    number_of_rva_and_sizes: int
    data_directory_offset: int


def parse_optional_header(data: bytes, coff: CoffHeader) -> OptionalHeaderInfo:
    """Đọc ``Magic`` + ``NumberOfRvaAndSizes`` của optional header. Chỉ hỗ
    trợ ``Magic`` PE32 (0x10B) hoặc PE32+ (0x20B); giá trị khác → dị dạng."""

    if coff.size_of_optional_header < 2:
        raise MalformedPeError(reason_vi="SizeOfOptionalHeader quá nhỏ để có Magic")
    (magic,) = _unpack("<H", data, coff.optional_header_offset, "OptionalHeader.Magic")
    assert isinstance(magic, int)

    if magic == _OPTIONAL_MAGIC_PE32:
        is_pe32_plus = False
        rva_count_offset = coff.optional_header_offset + _PE32_NUMBER_OF_RVA_AND_SIZES_OFFSET
        dd_offset = coff.optional_header_offset + _PE32_DATA_DIRECTORY_OFFSET
    elif magic == _OPTIONAL_MAGIC_PE32_PLUS:
        is_pe32_plus = True
        rva_count_offset = coff.optional_header_offset + _PE32PLUS_NUMBER_OF_RVA_AND_SIZES_OFFSET
        dd_offset = coff.optional_header_offset + _PE32PLUS_DATA_DIRECTORY_OFFSET
    else:
        raise MalformedPeError(reason_vi=f"OptionalHeader.Magic=0x{magic:x} không nhận diện được")

    (number_of_rva_and_sizes,) = _unpack(
        "<I", data, rva_count_offset, "OptionalHeader.NumberOfRvaAndSizes"
    )
    assert isinstance(number_of_rva_and_sizes, int)
    if number_of_rva_and_sizes > MAX_DATA_DIRECTORIES:
        raise MalformedPeError(
            reason_vi=(
                f"NumberOfRvaAndSizes={number_of_rva_and_sizes} vượt giới hạn "
                f"{MAX_DATA_DIRECTORIES}"
            )
        )
    return OptionalHeaderInfo(
        magic=magic,
        is_pe32_plus=is_pe32_plus,
        number_of_rva_and_sizes=number_of_rva_and_sizes,
        data_directory_offset=dd_offset,
    )


@dataclass(frozen=True)
class DataDirectoryEntry:
    virtual_address: int
    size: int


def parse_data_directory(
    data: bytes, optional_header: OptionalHeaderInfo, index: int
) -> DataDirectoryEntry | None:
    """Đọc entry data directory thứ ``index``. Trả ``None`` nếu
    ``NumberOfRvaAndSizes`` không đủ lớn để có entry này (hợp lệ — PE cũ/tối
    giản có thể không khai báo đủ 16 entry)."""

    if index >= optional_header.number_of_rva_and_sizes:
        return None
    entry_offset = optional_header.data_directory_offset + index * 8
    virtual_address, size = _unpack("<II", data, entry_offset, f"DataDirectory[{index}]")
    assert isinstance(virtual_address, int)
    assert isinstance(size, int)
    return DataDirectoryEntry(virtual_address=virtual_address, size=size)


@dataclass(frozen=True)
class SectionHeader:
    virtual_address: int
    virtual_size: int
    size_of_raw_data: int
    pointer_to_raw_data: int


def parse_section_table(data: bytes, coff: CoffHeader) -> tuple[SectionHeader, ...]:
    """Đọc bảng section (40 byte/section). Số section đã bị chặn trên bởi
    ``MAX_SECTIONS`` khi đọc COFF header."""

    sections: list[SectionHeader] = []
    for i in range(coff.number_of_sections):
        off = coff.section_table_offset + i * 40
        (
            _name,
            virtual_size,
            virtual_address,
            size_of_raw_data,
            pointer_to_raw_data,
            _reloc_ptr,
            _line_ptr,
            _num_reloc,
            _num_line,
            _characteristics,
        ) = _unpack("<8sIIIIIIHHI", data, off, f"IMAGE_SECTION_HEADER[{i}]")
        assert isinstance(virtual_size, int)
        assert isinstance(virtual_address, int)
        assert isinstance(size_of_raw_data, int)
        assert isinstance(pointer_to_raw_data, int)
        sections.append(
            SectionHeader(
                virtual_address=virtual_address,
                virtual_size=virtual_size,
                size_of_raw_data=size_of_raw_data,
                pointer_to_raw_data=pointer_to_raw_data,
            )
        )
    return tuple(sections)


def rva_to_file_offset(sections: tuple[SectionHeader, ...], rva: int) -> int | None:
    """Ánh xạ RVA → offset trong file qua bảng section. Trả ``None`` nếu
    không section nào chứa ``rva`` (không ném lỗi — caller tự quyết định
    coi là "không xác minh được" thay vì crash)."""

    for sec in sections:
        span = max(sec.virtual_size, sec.size_of_raw_data)
        if sec.virtual_address <= rva < sec.virtual_address + span:
            delta = rva - sec.virtual_address
            return sec.pointer_to_raw_data + delta
    return None


@dataclass(frozen=True)
class ClrHeaderRaw:
    major_runtime_version: int
    minor_runtime_version: int
    metadata_rva: int
    metadata_size: int
    flags: int
    entry_point_token: int


def parse_clr_header(data: bytes, offset: int) -> ClrHeaderRaw:
    """Đọc 24 byte đầu ``IMAGE_COR20_HEADER`` (đủ cho phân loại NET-001/002:
    phiên bản runtime, vùng MetaData, cờ ILONLY/32BITREQUIRED)."""

    (
        _cb,
        major_runtime_version,
        minor_runtime_version,
        metadata_rva,
        metadata_size,
        flags,
        entry_point_token,
    ) = _unpack("<IHHIIII", data, offset, "IMAGE_COR20_HEADER")
    assert isinstance(major_runtime_version, int)
    assert isinstance(minor_runtime_version, int)
    assert isinstance(metadata_rva, int)
    assert isinstance(metadata_size, int)
    assert isinstance(flags, int)
    assert isinstance(entry_point_token, int)
    return ClrHeaderRaw(
        major_runtime_version=major_runtime_version,
        minor_runtime_version=minor_runtime_version,
        metadata_rva=metadata_rva,
        metadata_size=metadata_size,
        flags=flags,
        entry_point_token=entry_point_token,
    )
