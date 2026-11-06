"""PRA-022/023 — .NET classifier + route (WPF/WinUI không native Linux)."""

from __future__ import annotations

import pytest

from namios_pra import DotnetKind, DotnetRoute, classify_dotnet

K = DotnetKind
R = DotnetRoute


@pytest.mark.parametrize("kind", [K.WPF, K.WINUI, K.WINFORMS, K.FRAMEWORK_LEGACY])
def test_windows_only_kinds_never_native(kind: DotnetKind) -> None:
    # Nghiệm thu PRA-023: WPF/WinUI/WinForms/Framework-legacy KHÔNG native Linux.
    c = classify_dotnet(kind)
    assert c.route is R.WINDOWS_ONLY
    assert c.route is not R.NATIVE_LINUX


@pytest.mark.parametrize("kind", [K.MODERN, K.CONSOLE, K.ASPNET])
def test_cross_platform_kinds_native(kind: DotnetKind) -> None:
    assert classify_dotnet(kind).route is R.NATIVE_LINUX


def test_unknown_is_unknown_not_guessed() -> None:
    c = classify_dotnet(K.UNKNOWN)
    assert c.route is R.UNKNOWN
    assert "unknown" in c.reason_vi.lower() or "không đoán" in c.reason_vi


def test_cross_platform_with_windows_trait_downgrades_to_wine() -> None:
    # modern nhưng có COM/WebView2 → không native chắc, chỉ THỬ Wine.
    c = classify_dotnet(K.MODERN, traits=["com"])
    assert c.route is R.WINE
    c2 = classify_dotnet(K.CONSOLE, traits=["webview2"])
    assert c2.route is R.WINE


def test_benign_traits_keep_native() -> None:
    c = classify_dotnet(K.MODERN, traits=["pinvoke", "vcpp"])
    assert c.route is R.NATIVE_LINUX  # pinvoke/vcpp không ép windows-only ở đây
    assert "pinvoke" in c.traits
