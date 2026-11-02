"""ECO-022 — coverage tính trên workflow ĐÃ KHẢO SÁT, tách theo WindowsMode;
"listed != working"."""

from __future__ import annotations

from tests.unit.eco._fixtures import make_entry

from namios_eco.coverage import compute_coverage, listed_vs_working
from namios_eco.status import PublishedStatus, WindowsMode


def _entries() -> tuple:
    return (
        make_entry(
            id="a.one",
            published_status=PublishedStatus.WORKFLOW_VERIFIED,
            windows_mode=WindowsMode.WEB_LINUX,
        ),
        make_entry(
            id="a.two",
            published_status=PublishedStatus.WORKFLOW_VERIFIED,
            windows_mode=WindowsMode.WINE,
        ),
        make_entry(
            id="a.three",
            published_status=PublishedStatus.PARTIAL_WORKFLOW,
            windows_mode=WindowsMode.WEB_LINUX,
        ),
        make_entry(
            id="a.four",
            published_status=PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            windows_mode=WindowsMode.REMOTE_WINDOWS,
        ),
        make_entry(
            id="a.five",
            published_status=PublishedStatus.DOWNLOADABLE_ONLY,
            windows_mode=WindowsMode.WEB_LINUX,
        ),
        make_entry(
            id="a.six",
            published_status=PublishedStatus.NOT_INVENTORIED,
            windows_mode=WindowsMode.NATIVE_LINUX,
        ),
    )


def test_compute_coverage_totals() -> None:
    report = compute_coverage(_entries())
    assert report.total_surveyed == 6
    assert report.workflow_verified == 2
    assert report.partial_workflow == 1
    assert report.blocked_external_dependency == 1
    assert report.not_yet_usable == 2  # downloadable_only + not_inventoried


def test_compute_coverage_empty_is_safe() -> None:
    report = compute_coverage(())
    assert report.total_surveyed == 0
    assert report.workflow_verified_ratio() == 0.0
    assert report.windows_free_ratio == 0.0


def test_workflow_verified_ratio() -> None:
    report = compute_coverage(_entries())
    assert report.workflow_verified_ratio() == 2 / 6


def test_by_windows_mode_breakdown_separates_modes() -> None:
    report = compute_coverage(_entries())
    by_mode = {m.mode: m for m in report.by_windows_mode}
    assert by_mode[WindowsMode.WEB_LINUX].total == 3
    assert by_mode[WindowsMode.WEB_LINUX].workflow_verified == 1
    assert by_mode[WindowsMode.WINE].workflow_verified == 1
    assert by_mode[WindowsMode.REMOTE_WINDOWS].blocked_external_dependency == 1
    assert by_mode[WindowsMode.WINDOWS_VM].total == 0


def test_windows_free_ratio_excludes_wine_vm_remote() -> None:
    report = compute_coverage(_entries())
    # 6 entries: web_linux x3, native_linux x1 (free) = 4/6 free
    assert report.windows_free_ratio == 4 / 6


def test_listed_vs_working_not_conflated() -> None:
    """FACT ECO-022: '100 phần mềm được liệt kê' != '100 phần mềm chạy được'."""

    listed, working = listed_vs_working(_entries())
    assert listed == 6
    assert working == 2
    assert listed != working
