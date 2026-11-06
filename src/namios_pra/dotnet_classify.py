"""Phân loại .NET + chọn tuyến chạy (PRA-022/023).

Nhận DẤU HIỆU quan sát được (từ manifest/dependency/log — tầng ``namios_dotnet``
lo phần đọc PE tĩnh an toàn) → phân loại ``DotnetKind`` + tuyến ``DotnetRoute``
TẤT ĐỊNH. Bất biến trung thực (nguồn Microsoft [3]): WPF/WinUI/WinForms gắn
Windows → KHÔNG native Linux; .NET hiện đại đa nền tảng (console/ASP.NET) → thử
native; thiếu metadata → ``UNKNOWN`` (không đoán). KHÔNG nhận "cài .NET Desktop
Runtime là WPF chạy native".
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_i18n import Lang, t
from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra._types import DotnetClassification, DotnetKind, DotnetRoute

__all__ = ["WINDOWS_ONLY_KINDS", "classify_dotnet"]

#: Kind GẮN Windows — không thể native Linux (PRA-023).
WINDOWS_ONLY_KINDS: frozenset[DotnetKind] = frozenset(
    {DotnetKind.WPF, DotnetKind.WINUI, DotnetKind.WINFORMS, DotnetKind.FRAMEWORK_LEGACY}
)

#: Kind đa nền tảng — thử native Linux (PRA-023).
_CROSS_PLATFORM_KINDS: frozenset[DotnetKind] = frozenset(
    {DotnetKind.MODERN, DotnetKind.CONSOLE, DotnetKind.ASPNET}
)

#: Trait GẮN Windows (chuẩn-hoá) — làm native không chắc → chỉ THỬ Wine (PRA-023).
_WINDOWS_TRAITS: frozenset[str] = frozenset({"com", "webview2"})


def _norm_traits(traits: Iterable[str]) -> frozenset[str]:
    """Chuẩn-hoá dấu hiệu quan sát (giống ``progress.py`` với chuỗi ngoài): trim +
    chữ-thường, bỏ rỗng. Fail-closed: biến thể hoa/khoảng-trắng của trait gắn-Windows
    (``"COM"``/`` com ``/``"WebView2"``) KHÔNG được lách phép so khớp → không bị
    coi là lành rồi nâng NATIVE_LINUX lạc quan (E_PRA_DOTNET_OVERCLAIM)."""

    return frozenset(s.strip().lower() for s in traits if s.strip())


def classify_dotnet(
    kind: DotnetKind,
    *,
    traits: Iterable[str] = (),
    arch: str = "unknown",
) -> DotnetClassification:
    """Phân loại + chọn tuyến. ``traits`` = dấu hiệu phụ (pinvoke/com/webview2/
    vcpp…) chỉ để GIẢI THÍCH, không tự nâng tuyến.

    - ``UNKNOWN`` → route UNKNOWN (thiếu bằng chứng, không đoán).
    - WPF/WinUI/WinForms/Framework-legacy → ``WINDOWS_ONLY`` (không native Linux).
    - modern/console/aspnet → ``NATIVE_LINUX`` thử trước; nếu có trait gắn-Windows
      (com/webview2) → hạ xuống ``WINE`` (chỉ thử, theo version) thay vì native.
    """

    tset = _norm_traits(traits)

    if kind == DotnetKind.UNKNOWN:
        return DotnetClassification(
            kind=kind,
            route=DotnetRoute.UNKNOWN,
            arch=arch,
            traits=tset,
            reason_vi=t("pra.dotnet.unknown", lang=Lang.VI),
        )

    if kind in WINDOWS_ONLY_KINDS:
        return DotnetClassification(
            kind=kind,
            route=DotnetRoute.WINDOWS_ONLY,
            arch=arch,
            traits=tset,
            reason_vi=t("pra.dotnet.windows_only", lang=Lang.VI, kind=kind.value),
        )

    if kind in _CROSS_PLATFORM_KINDS:
        # Trait gắn-Windows (COM/WebView2) làm native không chắc → chỉ THỬ Wine.
        windows_traits = tset & _WINDOWS_TRAITS
        if windows_traits:
            return DotnetClassification(
                kind=kind,
                route=DotnetRoute.WINE,
                arch=arch,
                traits=tset,
                reason_vi=t("pra.dotnet.wine", lang=Lang.VI, kind=kind.value),
            )
        return DotnetClassification(
            kind=kind,
            route=DotnetRoute.NATIVE_LINUX,
            arch=arch,
            traits=tset,
            reason_vi=t("pra.dotnet.native", lang=Lang.VI, kind=kind.value),
        )

    # fail-closed cho kind lạ (enum mới): UNKNOWN, không đoán native.
    return DotnetClassification(
        kind=kind,
        route=DotnetRoute.UNKNOWN,
        arch=arch,
        traits=tset,
        reason_vi=t("pra.dotnet.unknown", lang=Lang.VI),
    )
