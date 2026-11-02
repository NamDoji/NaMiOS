"""Test tầng ``DotnetAnalyzer`` (NET-001/NET-002) trên fixtures tĩnh của
``fixtures/dotnet/`` — phân loại managed/native + architecture + confidence
+ evidence + unknown_deps + suggested_mode, và các bất biến an toàn bắt
buộc (không crash trên PE dị dạng, không vượt giới hạn đọc, WinForms/WPF
không bị gọi là Linux native)."""

from __future__ import annotations

import shutil

import pytest

from namios_core.compat import AppMode
from namios_dotnet import DotnetAnalysisError, DotnetAnalyzer, PeArchitecture, PeKind

from ._fixtures import fixture_path


def test_native_pe32plus_minimal_classified_native_no_clr() -> None:
    result = DotnetAnalyzer().analyze(fixture_path("native_pe32plus_minimal.bin"))

    assert result.kind == PeKind.NATIVE
    assert result.architecture == PeArchitecture.X64
    assert result.confidence >= 0.8
    assert result.sidecar is None
    assert result.suggested_mode == AppMode.WINE  # native Win64 PE ⇒ cần Wine
    assert any(e.signal == "pe.no_clr_data_directory" for e in result.evidence)
    assert "KHÔNG phải chứng nhận" in result.disclaimer_vi


def test_managed_anycpu_minimal_classified_managed_with_sidecar_netcore() -> None:
    result = DotnetAnalyzer().analyze(fixture_path("managed_anycpu_minimal.dll"))

    assert result.kind == PeKind.MANAGED
    assert result.architecture == PeArchitecture.ANY_CPU
    assert result.confidence >= 0.8
    assert result.sidecar is not None
    assert result.sidecar.target_framework_moniker == "net8.0"
    assert result.sidecar.has_windows_desktop_framework is False
    # TFM net8.0 (>=5), không desktop ⇒ chạy được native trên .NET Linux (NET-004).
    assert result.suggested_mode == AppMode.NATIVE
    assert any(e.signal == "pe.clr_data_directory_present" for e in result.evidence)
    assert any(e.signal == "pe.clr_header_parsed" for e in result.evidence)


def test_managed_anycpu_minimal_reports_unknown_dependency_from_deps_json() -> None:
    result = DotnetAnalyzer().analyze(fixture_path("managed_anycpu_minimal.dll"))

    assert "Newtonsoft.Json" in result.unknown_dependencies
    assert "Microsoft.NETCore.App" not in result.unknown_dependencies


def test_managed_winforms_minimal_never_classified_as_linux_native() -> None:
    """Bất biến bắt buộc (NET-01/NET-04 test matrix): app có dấu hiệu
    WinForms/WPF qua sidecar KHÔNG BAO GIỜ được gợi ý ``native``, dù TFM là
    net8.0 (hiện đại)."""

    result = DotnetAnalyzer().analyze(fixture_path("managed_winforms_minimal.dll"))

    assert result.kind == PeKind.MANAGED
    assert result.sidecar is not None
    assert result.sidecar.has_windows_desktop_framework is True
    assert result.sidecar.target_framework_moniker == "net8.0"
    assert result.suggested_mode == AppMode.WINE
    assert result.suggested_mode != AppMode.NATIVE
    assert any(e.signal == "sidecar.windows_desktop_requires_wine" for e in result.evidence)


def test_managed_without_sidecar_does_not_guess_mode(tmp_path) -> None:
    shutil.copy(fixture_path("managed_anycpu_minimal.dll"), tmp_path / "no_sidecar.dll")

    result = DotnetAnalyzer().analyze(str(tmp_path / "no_sidecar.dll"))

    assert result.kind == PeKind.MANAGED
    assert result.sidecar is None
    assert result.suggested_mode is None  # không đủ bằng chứng ⇒ không đoán


def test_truncated_mz_is_malformed_not_crash() -> None:
    result = DotnetAnalyzer().analyze(fixture_path("truncated_mz.bin"))

    assert result.kind == PeKind.MALFORMED
    assert result.confidence == 0.0
    assert result.suggested_mode is None
    assert any(e.signal == "pe.malformed" for e in result.evidence)


def test_not_a_pe_file_is_not_pe_not_crash() -> None:
    result = DotnetAnalyzer().analyze(fixture_path("not_a_pe.bin"))

    assert result.kind == PeKind.NOT_PE
    assert result.confidence == 0.0
    assert result.suggested_mode is None


def test_empty_file_is_not_pe_not_crash(tmp_path) -> None:
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")

    result = DotnetAnalyzer().analyze(str(empty))

    assert result.kind == PeKind.NOT_PE
    assert result.confidence == 0.0


def test_file_exceeding_max_pe_bytes_truncated_not_crash(tmp_path) -> None:
    big = tmp_path / "huge.bin"
    # 'MZ' + nhiều byte rác, vượt giới hạn max_pe_bytes nhỏ ta đặt cho test.
    big.write_bytes(b"MZ" + b"\x00" * (64 * 1024))

    analyzer = DotnetAnalyzer(max_pe_bytes=4096)
    result = analyzer.analyze(str(big))

    assert any("vượt giới hạn đọc" in w for w in result.warnings_vi)


def test_analyze_rejects_relative_path() -> None:
    with pytest.raises(DotnetAnalysisError):
        DotnetAnalyzer().analyze("relative/path/app.exe")


def test_analyze_rejects_nonexistent_file(tmp_path) -> None:
    with pytest.raises(DotnetAnalysisError):
        DotnetAnalyzer().analyze(str(tmp_path / "does_not_exist.exe"))


def test_analyze_rejects_symlink_target(tmp_path) -> None:
    real = tmp_path / "real.dll"
    real.write_bytes(pe_builder_bytes())
    link = tmp_path / "link.dll"
    link.symlink_to(real)

    with pytest.raises(DotnetAnalysisError):
        DotnetAnalyzer().analyze(str(link))


def test_analyze_rejects_directory_as_target(tmp_path) -> None:
    sub = tmp_path / "somedir.dll"
    sub.mkdir()

    with pytest.raises(DotnetAnalysisError):
        DotnetAnalyzer().analyze(str(sub))


def _import_pe_builder():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "fixtures" / "dotnet"))
    import pe_builder  # type: ignore[import-not-found]

    return pe_builder


def pe_builder_bytes() -> bytes:
    return _import_pe_builder().build_native_pe32plus_minimal()


def test_mixed_mode_pe_classified_managed_mixed_suggests_wine(tmp_path) -> None:
    pe_builder = _import_pe_builder()
    data = pe_builder.build_managed_pe32_mixed_mode_minimal()
    path = tmp_path / "mixed.dll"
    path.write_bytes(data)

    result = DotnetAnalyzer().analyze(str(path))

    assert result.kind == PeKind.MANAGED_MIXED
    assert result.suggested_mode == AppMode.WINE


def test_managed_32bit_required_is_not_classified_any_cpu(tmp_path) -> None:
    pe_builder = _import_pe_builder()
    data = pe_builder.build_managed_pe32_32bit_required_minimal()
    path = tmp_path / "x86only.dll"
    path.write_bytes(data)

    result = DotnetAnalyzer().analyze(str(path))

    assert result.kind == PeKind.MANAGED
    assert result.architecture == PeArchitecture.X86
    assert result.architecture != PeArchitecture.ANY_CPU
