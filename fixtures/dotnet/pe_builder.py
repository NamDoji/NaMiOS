"""Builder PE/.NET fixtures cho WP .NET static analyzer — TẠO BẰNG CODE,
KHÔNG tải binary thật từ mạng, KHÔNG dùng binary Windows có bản quyền.

Chỉ dùng kiến thức định dạng file PE/COFF công khai (đặc tả Microsoft
PE/COFF) để lắp cấu trúc byte tối thiểu đủ cho test parser trong
``namios_dotnet``. KHÔNG phải mã máy thật — các section/CLR header chỉ có
cấu trúc, không có code thực thi nào, và NaMiOS KHÔNG BAO GIỜ thực thi các
file này (chỉ parse tĩnh).

Chạy ``python fixtures/dotnet/pe_builder.py`` để (tái) sinh các file tĩnh
trong thư mục này. Test đọc file tĩnh đã sinh (không gọi lại builder khi
chạy test, giống quy ước ``fixtures/recipe``/``fixtures/evidence``), nhưng
các hàm ở đây public nên test cũng có thể gọi trực tiếp nếu cần biến thể.
"""

from __future__ import annotations

import json
import os
import struct

__all__ = [
    "COMIMAGE_FLAGS_ILONLY",
    "COMIMAGE_FLAGS_32BITREQUIRED",
    "MACHINE_I386",
    "MACHINE_AMD64",
    "build_dos_header",
    "build_coff_header",
    "build_optional_header",
    "build_section_header",
    "build_native_pe32plus_minimal",
    "build_managed_pe32_anycpu_minimal",
    "build_managed_pe32_winforms_minimal",
    "build_truncated_mz",
    "build_not_a_pe",
    "runtimeconfig_json_netcore",
    "runtimeconfig_json_windowsdesktop",
    "deps_json_with_unknown_dependency",
]

_PE_SIGNATURE = b"PE\x00\x00"
MACHINE_I386 = 0x014C
MACHINE_AMD64 = 0x8664
_OPTIONAL_MAGIC_PE32 = 0x10B
_OPTIONAL_MAGIC_PE32_PLUS = 0x20B
IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR = 14
COMIMAGE_FLAGS_ILONLY = 0x00000001
COMIMAGE_FLAGS_32BITREQUIRED = 0x00000002

_DOS_HEADER_SIZE = 64
_COFF_HEADER_SIZE = 20
_SECTION_HEADER_SIZE = 40
_COR20_HEADER_SIZE = 24  # chỉ 24 byte đầu — đủ cho parser namios_dotnet đọc


def build_dos_header(e_lfanew: int) -> bytes:
    buf = bytearray(_DOS_HEADER_SIZE)
    buf[0:2] = b"MZ"
    struct.pack_into("<I", buf, 0x3C, e_lfanew)
    return bytes(buf)


def build_coff_header(
    *, machine: int, number_of_sections: int, size_of_optional_header: int
) -> bytes:
    return struct.pack(
        "<HHIIIHH",
        machine,
        number_of_sections,
        0,  # TimeDateStamp — không quan trọng cho parser
        0,  # PointerToSymbolTable
        0,  # NumberOfSymbols
        size_of_optional_header,
        0x0102,  # Characteristics: EXECUTABLE_IMAGE | 32BIT_MACHINE (giá trị minh hoạ)
    )


def build_optional_header(*, is_pe32_plus: bool, data_directories: list[tuple[int, int]]) -> bytes:
    """Chỉ điền ``Magic`` + ``NumberOfRvaAndSizes`` + ``DataDirectory[]`` ở
    đúng offset mà ``namios_dotnet.pe_format`` đọc; phần còn lại để 0 (test
    parser không cần các trường Windows-cụ-thể khác)."""

    magic = _OPTIONAL_MAGIC_PE32_PLUS if is_pe32_plus else _OPTIONAL_MAGIC_PE32
    num_rva_offset = 108 if is_pe32_plus else 92
    dd_offset = 112 if is_pe32_plus else 96
    number_of_rva_and_sizes = 16
    size = dd_offset + number_of_rva_and_sizes * 8
    buf = bytearray(size)
    struct.pack_into("<H", buf, 0, magic)
    struct.pack_into("<I", buf, num_rva_offset, number_of_rva_and_sizes)
    for i in range(number_of_rva_and_sizes):
        va, sz = data_directories[i] if i < len(data_directories) else (0, 0)
        struct.pack_into("<II", buf, dd_offset + i * 8, va, sz)
    return bytes(buf)


def build_section_header(
    *,
    name: bytes,
    virtual_size: int,
    virtual_address: int,
    size_of_raw_data: int,
    pointer_to_raw_data: int,
) -> bytes:
    name8 = name[:8].ljust(8, b"\x00")
    return struct.pack(
        "<8sIIIIIIHHI",
        name8,
        virtual_size,
        virtual_address,
        size_of_raw_data,
        pointer_to_raw_data,
        0,  # PointerToRelocations
        0,  # PointerToLinenumbers
        0,  # NumberOfRelocations
        0,  # NumberOfLinenumbers
        0x60000020,  # Characteristics: CNT_CODE | MEM_EXECUTE | MEM_READ (minh hoạ)
    )


def build_native_pe32plus_minimal() -> bytes:
    """(a) PE32+ native tối thiểu — KHÔNG có CLR data directory."""

    e_lfanew = _DOS_HEADER_SIZE
    optional = build_optional_header(is_pe32_plus=True, data_directories=[(0, 0)] * 16)
    coff = build_coff_header(
        machine=MACHINE_AMD64,
        number_of_sections=1,
        size_of_optional_header=len(optional),
    )
    header_block = build_dos_header(e_lfanew) + _PE_SIGNATURE + coff + optional
    section_header_offset = len(header_block)
    pointer_to_raw_data = section_header_offset + _SECTION_HEADER_SIZE
    raw_data = b"\x90" * 64  # NOP filler — KHÔNG phải code thật được thực thi bởi NaMiOS
    section_header = build_section_header(
        name=b".text",
        virtual_size=len(raw_data),
        virtual_address=0x1000,
        size_of_raw_data=len(raw_data),
        pointer_to_raw_data=pointer_to_raw_data,
    )
    return header_block + section_header + raw_data


def _build_managed_pe32(*, flags: int, machine: int = MACHINE_I386) -> bytes:
    e_lfanew = _DOS_HEADER_SIZE
    clr_va = 0x2000
    clr_size = _COR20_HEADER_SIZE
    data_dirs = [(0, 0)] * 16
    data_dirs[IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR] = (clr_va, clr_size)
    optional = build_optional_header(is_pe32_plus=False, data_directories=data_dirs)
    coff = build_coff_header(
        machine=machine,
        number_of_sections=1,
        size_of_optional_header=len(optional),
    )
    header_block = build_dos_header(e_lfanew) + _PE_SIGNATURE + coff + optional
    section_header_offset = len(header_block)
    pointer_to_raw_data = section_header_offset + _SECTION_HEADER_SIZE

    section_virtual_address = 0x1000
    raw_size = 0x1200  # đủ chứa CLR header (delta 0x1000) + MetaData giả (delta 0x1100)
    raw_data = bytearray(raw_size)

    metadata_rva = 0x2100
    metadata_size = 16
    cor20 = struct.pack(
        "<IHHIIII",
        _COR20_HEADER_SIZE,  # cb
        2,  # MajorRuntimeVersion
        5,  # MinorRuntimeVersion
        metadata_rva,
        metadata_size,
        flags,
        0x06000001,  # EntryPointToken (giả — không trỏ tới metadata thật)
    )
    clr_delta = clr_va - section_virtual_address
    raw_data[clr_delta : clr_delta + len(cor20)] = cor20

    metadata_delta = metadata_rva - section_virtual_address
    # Nội dung "metadata" chỉ là filler — parser namios_dotnet chỉ kiểm tra
    # MetaDataRVA ánh xạ được tới offset file hợp lệ, KHÔNG decode metadata
    # CLR thật (đó là phạm vi engine .NET thật, không phải static analyzer).
    raw_data[metadata_delta : metadata_delta + metadata_size] = b"\x00" * metadata_size

    section_header = build_section_header(
        name=b".cctext",
        virtual_size=len(raw_data),
        virtual_address=section_virtual_address,
        size_of_raw_data=len(raw_data),
        pointer_to_raw_data=pointer_to_raw_data,
    )
    return header_block + section_header + bytes(raw_data)


def build_managed_pe32_anycpu_minimal() -> bytes:
    """(b) "Managed-like": PE32 + CLR data directory set, ``ILONLY`` (AnyCPU,
    không ép 32-bit)."""

    return _build_managed_pe32(flags=COMIMAGE_FLAGS_ILONLY)


def build_managed_pe32_winforms_minimal() -> bytes:
    """Managed PE32 dùng kèm sidecar khai báo framework desktop Windows —
    để test "WinForms/WPF KHÔNG bị gọi là Linux native" (NET-01/NET-04)."""

    return _build_managed_pe32(flags=COMIMAGE_FLAGS_ILONLY)


def build_managed_pe32_32bit_required_minimal() -> bytes:
    """Managed PE32, ``ILONLY`` + ``32BITREQUIRED`` ⇒ KHÔNG phải AnyCPU dù
    cùng Machine=I386/PE32 (test tinh chỉnh architecture)."""

    return _build_managed_pe32(flags=COMIMAGE_FLAGS_ILONLY | COMIMAGE_FLAGS_32BITREQUIRED)


def build_managed_pe32_mixed_mode_minimal() -> bytes:
    """Mixed-mode (vd C++/CLI, IJW): có CLR data directory nhưng KHÔNG set
    ``ILONLY`` (có code native bên trong) ⇒ phải phân loại
    ``managed_mixed``, không phải ``managed`` thuần IL."""

    return _build_managed_pe32(flags=0)


def build_truncated_mz() -> bytes:
    """(c) Có chữ ký 'MZ' nhưng cụt — không đủ byte để đọc ``e_lfanew``."""

    return b"MZ" + b"\x00" * 10  # < 0x40 byte, _unpack("<I", ..., 0x3C, ...) sẽ thiếu dữ liệu


def build_not_a_pe() -> bytes:
    """(d) File hoàn toàn không phải PE (không có chữ ký 'MZ')."""

    return b"Day khong phai file PE. Chi la van ban thuong de test NET-001.\n"


def runtimeconfig_json_netcore(*, tfm: str = "net8.0") -> dict[str, object]:
    """(e) runtimeconfig.json mẫu — app .NET (Core) hiện đại, không có
    framework desktop ⇒ gợi ý chạy ``native`` trên Linux (NET-004)."""

    return {
        "runtimeOptions": {
            "tfm": tfm,
            "framework": {"name": "Microsoft.NETCore.App", "version": "8.0.0"},
        }
    }


def runtimeconfig_json_windowsdesktop(*, tfm: str = "net8.0") -> dict[str, object]:
    """runtimeconfig.json mẫu có framework desktop Windows (WinForms/WPF) —
    PHẢI gợi ý ``wine``, KHÔNG BAO GIỜ ``native``, dù TFM là net8.0."""

    return {
        "runtimeOptions": {
            "tfm": tfm,
            "framework": {"name": "Microsoft.NETCore.App", "version": "8.0.0"},
            "frameworks": [{"name": "Microsoft.WindowsDesktop.App", "version": "8.0.0"}],
        }
    }


def deps_json_with_unknown_dependency() -> dict[str, object]:
    """deps.json mẫu có 1 dependency chính thức + 1 dependency bên thứ ba
    "chưa rõ" (NET-002 ``unknown_deps``)."""

    return {
        "libraries": {
            "Microsoft.NETCore.App/8.0.0": {"type": "runtime"},
            "Newtonsoft.Json/13.0.3": {"type": "package"},
        }
    }


def _write(path: str, data: bytes) -> None:
    with open(path, "wb") as fh:
        fh.write(data)


def _write_json(path: str, doc: dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def generate_all(out_dir: str) -> None:
    _write(
        os.path.join(out_dir, "native_pe32plus_minimal.bin"),
        build_native_pe32plus_minimal(),
    )
    _write(
        os.path.join(out_dir, "managed_anycpu_minimal.dll"),
        build_managed_pe32_anycpu_minimal(),
    )
    _write_json(
        os.path.join(out_dir, "managed_anycpu_minimal.runtimeconfig.json"),
        runtimeconfig_json_netcore(),
    )
    _write_json(
        os.path.join(out_dir, "managed_anycpu_minimal.deps.json"),
        deps_json_with_unknown_dependency(),
    )
    _write(
        os.path.join(out_dir, "managed_winforms_minimal.dll"),
        build_managed_pe32_winforms_minimal(),
    )
    _write_json(
        os.path.join(out_dir, "managed_winforms_minimal.runtimeconfig.json"),
        runtimeconfig_json_windowsdesktop(),
    )
    _write(os.path.join(out_dir, "truncated_mz.bin"), build_truncated_mz())
    _write(os.path.join(out_dir, "not_a_pe.bin"), build_not_a_pe())


if __name__ == "__main__":
    generate_all(os.path.dirname(os.path.abspath(__file__)))
    print("Đã sinh fixtures .NET vào", os.path.dirname(os.path.abspath(__file__)))
