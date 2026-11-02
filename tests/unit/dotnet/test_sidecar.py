"""Unit test ``namios_dotnet.sidecar`` — đọc ``.runtimeconfig.json``/
``.deps.json`` đi kèm, an toàn với JSON dị dạng/thiếu trường."""

from __future__ import annotations

import json

from namios_dotnet.sidecar import load_sidecar_info


def test_no_sidecar_returns_none(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")

    assert load_sidecar_info(str(pe)) is None


def test_runtimeconfig_only_parses_tfm_and_framework(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
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

    info = load_sidecar_info(str(pe))

    assert info is not None
    assert info.target_framework_moniker == "net8.0"
    assert info.framework_names == ("Microsoft.NETCore.App",)
    assert info.has_windows_desktop_framework is False
    assert info.parse_warnings_vi == ()


def test_runtimeconfig_frameworks_array_detects_windows_desktop(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
    (tmp_path / "app.runtimeconfig.json").write_text(
        json.dumps(
            {
                "runtimeOptions": {
                    "tfm": "net8.0",
                    "framework": {"name": "Microsoft.NETCore.App"},
                    "frameworks": [{"name": "Microsoft.WindowsDesktop.App"}],
                }
            }
        ),
        encoding="utf-8",
    )

    info = load_sidecar_info(str(pe))

    assert info is not None
    assert info.has_windows_desktop_framework is True


def test_malformed_runtimeconfig_json_reports_warning_not_crash(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
    (tmp_path / "app.runtimeconfig.json").write_text("{ this is not valid json", encoding="utf-8")

    info = load_sidecar_info(str(pe))

    assert info is not None
    assert info.target_framework_moniker is None
    assert any("không parse được" in w for w in info.parse_warnings_vi)


def test_deps_json_unknown_dependency_detected(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
    (tmp_path / "app.deps.json").write_text(
        json.dumps(
            {
                "libraries": {
                    "Microsoft.NETCore.App/8.0.0": {},
                    "SomeThirdParty.Package/1.0.0": {},
                }
            }
        ),
        encoding="utf-8",
    )

    info = load_sidecar_info(str(pe))

    assert info is not None
    assert "SomeThirdParty.Package" in info.unknown_dependency_ids
    assert "Microsoft.NETCore.App" not in info.unknown_dependency_ids


def test_deps_json_windows_desktop_library_detected(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
    (tmp_path / "app.deps.json").write_text(
        json.dumps({"libraries": {"Microsoft.WindowsDesktop.App.WindowsForms/8.0.0": {}}}),
        encoding="utf-8",
    )

    info = load_sidecar_info(str(pe))

    assert info is not None
    assert info.has_windows_desktop_framework is True


def test_deps_json_not_an_object_reports_warning(tmp_path) -> None:
    pe = tmp_path / "app.dll"
    pe.write_bytes(b"MZ")
    (tmp_path / "app.deps.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    info = load_sidecar_info(str(pe))

    assert info is not None
    assert any("không phải object" in w for w in info.parse_warnings_vi)
