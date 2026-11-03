"""Test COMP-028 (Phụ lục 03) cho ``namios_compat.classifier``.

Trọng tâm nghiệm thu: phân loại TĨNH (không thực thi binary) ra nhãn
phát hiện/suy đoán/chưa rõ — KHÔNG BAO GIỜ suy từ đuôi ``.exe``; mẫu
WinForms/WPF PHẢI phân loại KHÁC mẫu .NET hiện đại (cốt lõi nghiệm thu);
PE có Optional Header ``Subsystem`` = ``IMAGE_SUBSYSTEM_NATIVE`` (1) ⇒
``KERNEL_DRIVER`` + ``wine_blocker=True``; PE dị dạng/không phải PE ⇒
``UNKNOWN`` + ``confidence=UNKNOWN``, KHÔNG BAO GIỜ crash."""

from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

import pytest

from namios_compat._types import ClassificationConfidence, RuntimeKind
from namios_compat.classifier import classify_runtime
from namios_core.compat import AppMode
from namios_dotnet import DotnetAnalysisError, DotnetAnalyzer, PeKind

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURES_DOTNET_DIR = _REPO_ROOT / "fixtures" / "dotnet"

_PE_SIGNATURE = b"PE\x00\x00"
_OPTIONAL_MAGIC_PE32_PLUS = 0x20B
_MACHINE_AMD64 = 0x8664
#: Offset của Subsystem (2 byte) trong Optional Header — xem
#: ``namios_compat.classifier._SUBSYSTEM_OFFSET_IN_OPTIONAL_HEADER``.
_SUBSYSTEM_OFFSET = 68


def _fixture_path(name: str) -> str:
    return str(_FIXTURES_DOTNET_DIR / name)


def _build_minimal_pe32plus_with_subsystem(subsystem: int) -> bytes:
    """Lắp tay (KHÔNG thực thi, chỉ cấu trúc byte) một PE32+ tối thiểu,
    KHÔNG có CLR data directory (⇒ ``PeKind.NATIVE`` nếu được phân tích
    managed/native), với Optional Header ``Subsystem`` tuỳ chỉnh ở offset 68
    — đủ để test nhánh ``KERNEL_DRIVER`` của classifier (Subsystem==1
    ``IMAGE_SUBSYSTEM_NATIVE``) mà không cần phụ thuộc ``fixtures/dotnet/
    pe_builder.py`` (module đó không hỗ trợ tham số hoá Subsystem)."""

    e_lfanew = 64
    dos = bytearray(e_lfanew)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, e_lfanew)

    # IMAGE_OPTIONAL_HEADER64: Magic(2) @0, Subsystem(2) @68,
    # NumberOfRvaAndSizes(4) @108, DataDirectory[16] @112.. (đủ cho
    # namios_dotnet.pe_format đọc khi cần, không bắt buộc ở test này).
    data_directory_offset = 112
    number_of_rva_and_sizes = 16
    optional_size = data_directory_offset + number_of_rva_and_sizes * 8
    optional = bytearray(optional_size)
    struct.pack_into("<H", optional, 0, _OPTIONAL_MAGIC_PE32_PLUS)
    struct.pack_into("<H", optional, _SUBSYSTEM_OFFSET, subsystem)
    struct.pack_into("<I", optional, 108, number_of_rva_and_sizes)

    coff = struct.pack(
        "<HHIIIHH",
        _MACHINE_AMD64,
        0,  # NumberOfSections — không cần section nào cho test này
        0,  # TimeDateStamp
        0,  # PointerToSymbolTable
        0,  # NumberOfSymbols
        len(optional),  # SizeOfOptionalHeader
        0x0102,  # Characteristics (minh hoạ, không ảnh hưởng phân loại)
    )
    return bytes(dos) + _PE_SIGNATURE + coff + bytes(optional)


# --- DOTNET_MODERN vs WinForms/WPF (cốt lõi nghiệm thu COMP-028) ---------


def test_modern_dotnet_fixture_classified_dotnet_modern_native() -> None:
    result = classify_runtime(_fixture_path("managed_anycpu_minimal.dll"))

    assert result.kinds == (RuntimeKind.DOTNET_MODERN,)
    assert result.confidence == ClassificationConfidence.DETECTED
    assert result.suggested_mode == AppMode.NATIVE
    assert result.wine_blocker is False


def test_winforms_fixture_classified_as_windows_desktop_dotnet() -> None:
    result = classify_runtime(_fixture_path("managed_winforms_minimal.dll"))

    assert RuntimeKind.DOTNET_FRAMEWORK in result.kinds
    assert result.suggested_mode == AppMode.WINE
    assert result.wine_blocker is False
    assert result.confidence == ClassificationConfidence.DETECTED


def test_winforms_classified_differently_from_modern_dotnet() -> None:
    """Nghiệm thu cốt lõi COMP-028: WinForms/WPF KHÔNG BAO GIỜ trộn nhãn với
    .NET hiện đại đa nền tảng, dù cả hai cùng TFM net8.0 trong sidecar."""

    modern = classify_runtime(_fixture_path("managed_anycpu_minimal.dll"))
    winforms = classify_runtime(_fixture_path("managed_winforms_minimal.dll"))

    assert modern.kinds != winforms.kinds
    assert RuntimeKind.DOTNET_MODERN not in winforms.kinds
    assert RuntimeKind.DOTNET_FRAMEWORK not in modern.kinds
    assert modern.suggested_mode != winforms.suggested_mode


def test_managed_without_sidecar_is_inferred_not_detected(tmp_path: Path) -> None:
    shutil.copy(_fixture_path("managed_anycpu_minimal.dll"), tmp_path / "no_sidecar.dll")

    result = classify_runtime(str(tmp_path / "no_sidecar.dll"))

    assert result.confidence == ClassificationConfidence.INFERRED
    assert result.suggested_mode is None  # DotnetAnalyzer cũng không đoán liều
    assert result.kinds == (RuntimeKind.UNKNOWN,)


# --- Native (non-.NET) PE -------------------------------------------------


def test_native_pe_fixture_classified_native_win32() -> None:
    result = classify_runtime(_fixture_path("native_pe32plus_minimal.bin"))

    assert result.kinds == (RuntimeKind.NATIVE_WIN32,)
    assert result.suggested_mode == AppMode.WINE
    assert result.confidence == ClassificationConfidence.DETECTED
    assert result.wine_blocker is False


def test_normal_native_fixture_has_no_kernel_driver_signal() -> None:
    """Dò Subsystem phải trả 'không có tín hiệu' trên PE native bình thường
    (Subsystem để 0 trong fixture này) — không báo nhầm KERNEL_DRIVER."""

    result = classify_runtime(_fixture_path("native_pe32plus_minimal.bin"))

    assert RuntimeKind.KERNEL_DRIVER not in result.kinds


# --- Kernel driver / native subsystem ------------------------------------


def test_native_subsystem_pe_classified_kernel_driver_wine_blocker(tmp_path: Path) -> None:
    data = _build_minimal_pe32plus_with_subsystem(subsystem=1)  # IMAGE_SUBSYSTEM_NATIVE
    path = tmp_path / "driver.sys"
    path.write_bytes(data)

    result = classify_runtime(str(path))

    assert result.kinds == (RuntimeKind.KERNEL_DRIVER,)
    assert result.wine_blocker is True
    assert result.confidence == ClassificationConfidence.DETECTED
    assert result.suggested_mode is None


def test_non_native_subsystem_pe_not_classified_kernel_driver(tmp_path: Path) -> None:
    data = _build_minimal_pe32plus_with_subsystem(subsystem=2)  # IMAGE_SUBSYSTEM_WINDOWS_GUI
    path = tmp_path / "app.exe"
    path.write_bytes(data)

    result = classify_runtime(str(path))

    assert RuntimeKind.KERNEL_DRIVER not in result.kinds
    assert result.wine_blocker is False


# --- Not-a-PE / malformed → UNKNOWN, no crash ----------------------------


def test_not_a_pe_is_unknown_no_crash() -> None:
    result = classify_runtime(_fixture_path("not_a_pe.bin"))

    assert result.kinds == (RuntimeKind.UNKNOWN,)
    assert result.confidence == ClassificationConfidence.UNKNOWN
    assert result.wine_blocker is False
    assert result.suggested_mode is None


def test_truncated_mz_is_unknown_no_crash() -> None:
    result = classify_runtime(_fixture_path("truncated_mz.bin"))

    assert result.kinds == (RuntimeKind.UNKNOWN,)
    assert result.confidence == ClassificationConfidence.UNKNOWN
    assert result.suggested_mode is None


# --- Dependency signals (additive) ---------------------------------------


def test_webview2_and_sqlclient_dependencies_are_additive(tmp_path: Path) -> None:
    shutil.copy(_fixture_path("managed_anycpu_minimal.dll"), tmp_path / "app.dll")
    (tmp_path / "app.runtimeconfig.json").write_text(
        json.dumps(
            {
                "runtimeOptions": {
                    "tfm": "net8.0",
                    "framework": {"name": "Microsoft.NETCore.App", "version": "8.0.0"},
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "app.deps.json").write_text(
        json.dumps(
            {
                "libraries": {
                    "Microsoft.NETCore.App/8.0.0": {"type": "runtime"},
                    "Microsoft.Web.WebView2/1.0.2210.55": {"type": "package"},
                    "System.Data.SqlClient/4.8.5": {"type": "package"},
                }
            }
        ),
        encoding="utf-8",
    )

    result = classify_runtime(str(tmp_path / "app.dll"))

    assert RuntimeKind.DOTNET_MODERN in result.kinds
    assert RuntimeKind.WEBVIEW2 in result.kinds
    assert RuntimeKind.SQLSERVER_CLIENT in result.kinds
    # Additive: không đổi suggested_mode đã suy ra từ TFM hiện đại.
    assert result.suggested_mode == AppMode.NATIVE


# --- disclaimer_vi --------------------------------------------------------


def test_disclaimer_vi_is_non_empty_vietnamese() -> None:
    result = classify_runtime(_fixture_path("managed_anycpu_minimal.dll"))

    assert result.disclaimer_vi
    assert "TĨNH" in result.disclaimer_vi or "tĩnh" in result.disclaimer_vi


# --- caller contract: path errors propagate, kinds never empty ----------


def test_relative_path_raises_dotnet_analysis_error() -> None:
    with pytest.raises(DotnetAnalysisError):
        classify_runtime("relative/path/app.exe")


def test_classify_runtime_accepts_explicit_analyzer() -> None:
    result = classify_runtime(
        _fixture_path("native_pe32plus_minimal.bin"), analyzer=DotnetAnalyzer()
    )

    assert result.kinds == (RuntimeKind.NATIVE_WIN32,)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "managed_anycpu_minimal.dll",
        "managed_winforms_minimal.dll",
        "native_pe32plus_minimal.bin",
        "not_a_pe.bin",
        "truncated_mz.bin",
    ],
)
def test_kinds_is_never_empty(fixture_name: str) -> None:
    result = classify_runtime(_fixture_path(fixture_name))

    assert len(result.kinds) >= 1


def test_malformed_pe_kind_matches_analyzer_malformed_classification() -> None:
    # Bất biến chéo: khi DotnetAnalyzer tự xếp một fixture là MALFORMED,
    # classifier PHẢI vẫn trả UNKNOWN (không crash, không đoán liều).
    analyzer_result = DotnetAnalyzer().analyze(_fixture_path("truncated_mz.bin"))
    assert analyzer_result.kind == PeKind.MALFORMED

    result = classify_runtime(_fixture_path("truncated_mz.bin"))
    assert result.kinds == (RuntimeKind.UNKNOWN,)
