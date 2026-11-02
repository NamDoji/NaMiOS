"""Unit test ``namios_dotnet._io`` — giới hạn kích thước đọc + an toàn path
(symlink/traversal/không tồn tại), dựa trên ``namios_security`` (SEC-002)."""

from __future__ import annotations

import pytest

from namios_dotnet._errors import DotnetAnalysisError
from namios_dotnet._io import read_bytes_capped, read_sidecar_if_present


def test_read_bytes_capped_reads_full_small_file(tmp_path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"abcdef")

    result = read_bytes_capped(str(f), max_bytes=1024)

    assert result.data == b"abcdef"
    assert result.truncated is False


def test_read_bytes_capped_truncates_large_file(tmp_path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"x" * 100)

    result = read_bytes_capped(str(f), max_bytes=10)

    assert len(result.data) == 10
    assert result.truncated is True


def test_read_bytes_capped_rejects_relative_path() -> None:
    with pytest.raises(DotnetAnalysisError):
        read_bytes_capped("relative/file.bin", max_bytes=10)


def test_read_bytes_capped_rejects_nonexistent_file(tmp_path) -> None:
    with pytest.raises(DotnetAnalysisError):
        read_bytes_capped(str(tmp_path / "missing.bin"), max_bytes=10)


def test_read_bytes_capped_rejects_symlink(tmp_path) -> None:
    real = tmp_path / "real.bin"
    real.write_bytes(b"data")
    link = tmp_path / "link.bin"
    link.symlink_to(real)

    with pytest.raises(DotnetAnalysisError):
        read_bytes_capped(str(link), max_bytes=10)


def test_read_sidecar_if_present_returns_none_when_missing(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")

    assert read_sidecar_if_present(str(pe), ".runtimeconfig.json") is None


def test_read_sidecar_if_present_reads_existing_sidecar(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
    (tmp_path / "app.runtimeconfig.json").write_bytes(b'{"runtimeOptions": {}}')

    found = read_sidecar_if_present(str(pe), ".runtimeconfig.json")

    assert found is not None
    sidecar_path, result = found
    assert sidecar_path.endswith("app.runtimeconfig.json")
    assert result.data == b'{"runtimeOptions": {}}'
