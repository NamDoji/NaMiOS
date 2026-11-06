"""N10-018 — Bộ phân tích PE an toàn: phân loại METADATA (struct input), KHÔNG
chạy file.

20 fixture đã gán nhãn (N10-018 nghiệm thu). Bất biến cứng: driver ``.sys``
KHÔNG BAO GIỜ bị phân loại là app user-mode, dù có installer/service marker
đi kèm; thiếu bằng chứng → ``unknown``.
"""

from __future__ import annotations

import pytest

from namios_mig import PeAnalysisResult, PeClassification, PeMetadataInput, PeSubsystem, classify_pe
from namios_pra import DotnetKind, DotnetRoute

PC = PeClassification
PS = PeSubsystem


def _meta(**kw: object) -> PeMetadataInput:
    base: dict[str, object] = {"file_name": "fixture.bin"}
    base.update(kw)
    return PeMetadataInput(**base)  # type: ignore[arg-type]


# 20 fixture (tên, input, nhãn mong đợi) — bao phủ driver/service/installer/
# .NET/user-mode/unknown + các trường hợp "lẫn dấu hiệu" để chứng minh thứ tự
# kiểm driver-trước-tiên không bị phá.
FIXTURES: list[tuple[str, PeMetadataInput, PeClassification]] = [
    ("driver_sys_extension", _meta(extension=".sys"), PC.KERNEL_DRIVER),
    (
        "driver_native_subsystem_no_sys_ext",
        _meta(extension=".exe", subsystem=PS.NATIVE),
        PC.KERNEL_DRIVER,
    ),
    (
        "driver_kernel_import_odd_extension",
        _meta(extension=".dll", imports=frozenset({"ntoskrnl.exe"})),
        PC.KERNEL_DRIVER,
    ),
    (
        "driver_hal_import",
        _meta(extension=".sys", imports=frozenset({"hal.dll"})),
        PC.KERNEL_DRIVER,
    ),
    (
        "driver_with_installer_marker_still_driver",
        # Bất biến cứng: dù có installer_markers, .sys vẫn PHẢI là driver.
        _meta(extension=".sys", installer_markers=frozenset({"msi"})),
        PC.KERNEL_DRIVER,
    ),
    (
        "driver_with_service_marker_still_driver",
        _meta(extension=".sys", service_markers=frozenset({"SERVICE_MAIN"})),
        PC.KERNEL_DRIVER,
    ),
    (
        "driver_with_dotnet_signal_still_driver",
        _meta(extension=".sys", dotnet_kind=DotnetKind.CONSOLE),
        PC.KERNEL_DRIVER,
    ),
    (
        "windows_service_exe",
        _meta(
            extension=".exe", service_markers=frozenset({"SERVICE_MAIN"}), subsystem=PS.WINDOWS_CUI
        ),
        PC.WINDOWS_SERVICE,
    ),
    (
        "msi_installer",
        _meta(extension=".msi", installer_markers=frozenset({"msi"})),
        PC.INSTALLER,
    ),
    (
        "nsis_installer_exe",
        _meta(extension=".exe", installer_markers=frozenset({"nsis"}), subsystem=PS.WINDOWS_GUI),
        PC.INSTALLER,
    ),
    (
        "innosetup_installer_exe",
        _meta(extension=".exe", installer_markers=frozenset({"innosetup"})),
        PC.INSTALLER,
    ),
    (
        "dotnet_console_native_candidate",
        _meta(extension=".exe", dotnet_kind=DotnetKind.CONSOLE, subsystem=PS.WINDOWS_CUI),
        PC.DOTNET_MANAGED,
    ),
    (
        "dotnet_winforms",
        _meta(extension=".exe", dotnet_kind=DotnetKind.WINFORMS, subsystem=PS.WINDOWS_GUI),
        PC.DOTNET_MANAGED,
    ),
    (
        "dotnet_wpf",
        _meta(extension=".exe", dotnet_kind=DotnetKind.WPF, subsystem=PS.WINDOWS_GUI),
        PC.DOTNET_MANAGED,
    ),
    (
        "dotnet_aspnet_with_com_trait_falls_to_wine",
        _meta(extension=".exe", dotnet_kind=DotnetKind.ASPNET, dotnet_traits=frozenset({"com"})),
        PC.DOTNET_MANAGED,
    ),
    (
        "plain_gui_app_exe",
        _meta(extension=".exe", subsystem=PS.WINDOWS_GUI),
        PC.USER_MODE_APP,
    ),
    (
        "plain_cui_app_exe",
        _meta(extension=".exe", subsystem=PS.WINDOWS_CUI),
        PC.USER_MODE_APP,
    ),
    (
        "plain_gui_app_no_extension",
        _meta(extension="", subsystem=PS.WINDOWS_GUI),
        PC.USER_MODE_APP,
    ),
    (
        "unknown_no_signals_at_all",
        _meta(),
        PC.UNKNOWN,
    ),
    (
        "unknown_dll_without_markers",
        # .dll GUI/CUI không áp dụng (subsystem chỉ có nghĩa cho EXE) → unknown.
        _meta(extension=".dll", subsystem=PS.UNKNOWN),
        PC.UNKNOWN,
    ),
]


@pytest.mark.parametrize("name,meta,expected", FIXTURES, ids=[f[0] for f in FIXTURES])
def test_pe_fixture_classification(
    name: str, meta: PeMetadataInput, expected: PeClassification
) -> None:
    result = classify_pe(meta)
    assert result.classification is expected, f"{name}: got {result.classification}"


def test_exactly_twenty_labeled_fixtures() -> None:
    # N10-018 nghiệm thu: "20 fixture đã gán nhãn".
    assert len(FIXTURES) == 20


def test_driver_never_classified_as_user_mode_app() -> None:
    # Bất biến cứng xuyên suốt toàn bộ fixture driver — quét lại để khẳng
    # định rõ ràng (không chỉ dựa vào tham số hoá ở trên).
    driver_fixtures = [f for f in FIXTURES if f[2] is PC.KERNEL_DRIVER]
    assert len(driver_fixtures) >= 5
    for _, meta, _expected in driver_fixtures:
        result = classify_pe(meta)
        assert result.classification is not PC.USER_MODE_APP


def test_unknown_marks_confidence_unknown_flag() -> None:
    result: PeAnalysisResult = classify_pe(_meta())
    assert result.classification is PC.UNKNOWN
    assert result.confidence_unknown is True


def test_known_classification_does_not_set_confidence_unknown() -> None:
    result = classify_pe(_meta(extension=".sys"))
    assert result.confidence_unknown is False


def test_dotnet_classification_carries_pra_route() -> None:
    # Tái dùng namios_pra.dotnet_classify.classify_dotnet — WPF gắn Windows,
    # KHÔNG native Linux (chạy qua Wine có kiểm/Windows có phép, không tự
    # nhận "native Linux" chỉ vì .NET hiện đại).
    result = classify_pe(
        _meta(extension=".exe", dotnet_kind=DotnetKind.WPF, subsystem=PS.WINDOWS_GUI)
    )
    assert result.dotnet is not None
    assert result.dotnet.route is DotnetRoute.WINDOWS_ONLY  # KHÔNG được NATIVE_LINUX
