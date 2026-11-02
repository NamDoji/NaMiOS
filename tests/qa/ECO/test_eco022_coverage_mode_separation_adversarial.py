"""ECO-022 — GATE đối kháng: coverage PHẢI tách riêng theo
``WindowsMode`` (web/wine/vm/remote/native) — không có đường nào trộn các
mode vào một con số tổng duy nhất mà làm mất khả năng truy vết theo mode,
và "số liệt kê" (listed) không được đánh đồng với "số chạy được" (working).
"""

from __future__ import annotations

from namios_eco.coverage import ModeCoverage, compute_coverage, listed_vs_working
from namios_eco.models import ServiceEntry
from namios_eco.status import PublishedStatus, WindowsMode


def _entry(entry_id: str, status: PublishedStatus, mode: WindowsMode) -> ServiceEntry:
    return ServiceEntry(
        id=entry_id,
        provider="QA Tester",
        agency=None,
        purpose="Workflow giả định dùng cho test coverage.",
        official_url="https://example.gov.vn/",
        source_check="test",
        version=None,
        license="test",
        published_os=(),
        dependencies=(),
        account_condition="test",
        service_cost="free",
        data_sensitivity="cong_khai",
        test_profile="qa",
        last_updated="2026-11-02",
        evidence_source="https://example.gov.vn/",
        published_status=status,
        windows_mode=mode,
        tested_by_namios=False,
        officially_supported_by_vendor=False,
    )


def _mixed_mode_entries() -> tuple[ServiceEntry, ...]:
    """10 entry trộn đủ 5 mode, cố ý số lượng khác nhau mỗi mode để một bug
    "gộp nhầm" sẽ lộ ra qua tổng sai, không chỉ qua việc thiếu field."""

    return (
        _entry("w1", PublishedStatus.WORKFLOW_VERIFIED, WindowsMode.WEB_LINUX),
        _entry("w2", PublishedStatus.PARTIAL_WORKFLOW, WindowsMode.WEB_LINUX),
        _entry("w3", PublishedStatus.NOT_INVENTORIED, WindowsMode.WEB_LINUX),
        _entry("wine1", PublishedStatus.WORKFLOW_VERIFIED, WindowsMode.WINE),
        _entry("wine2", PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY, WindowsMode.WINE),
        _entry("vm1", PublishedStatus.DOWNLOADABLE_ONLY, WindowsMode.WINDOWS_VM),
        _entry("remote1", PublishedStatus.WORKFLOW_VERIFIED, WindowsMode.REMOTE_WINDOWS),
        _entry("remote2", PublishedStatus.LAUNCHES_ONLY, WindowsMode.REMOTE_WINDOWS),
        _entry("native1", PublishedStatus.WORKFLOW_VERIFIED, WindowsMode.NATIVE_LINUX),
        _entry("native2", PublishedStatus.UNSUPPORTED, WindowsMode.NATIVE_LINUX),
    )


def test_by_windows_mode_totals_sum_exactly_to_overall_total_no_double_count_no_loss() -> None:
    """Tấn công "trộn lẫn": tổng của 5 ``ModeCoverage.total`` PHẢI bằng
    đúng ``total_surveyed`` — nếu một entry bị tính 2 lần (vd do so sánh
    mode lỏng) hoặc bị bỏ sót (vd do thiếu một giá trị enum trong vòng
    lặp), tổng sẽ lệch."""

    entries = _mixed_mode_entries()
    report = compute_coverage(entries)
    assert sum(m.total for m in report.by_windows_mode) == report.total_surveyed == len(entries)


def test_by_windows_mode_workflow_verified_sums_match_overall_not_blended() -> None:
    entries = _mixed_mode_entries()
    report = compute_coverage(entries)
    assert sum(m.workflow_verified for m in report.by_windows_mode) == report.workflow_verified
    assert report.workflow_verified == 4  # w1, wine1, remote1, native1


def test_each_windows_mode_enum_value_has_its_own_mode_coverage_entry() -> None:
    """Không có mode nào bị gộp chung với mode khác — mỗi giá trị
    ``WindowsMode`` có đúng MỘT ``ModeCoverage`` tương ứng trong kết quả."""

    report = compute_coverage(_mixed_mode_entries())
    modes_present = [m.mode for m in report.by_windows_mode]
    assert sorted(modes_present, key=lambda m: m.value) == sorted(
        WindowsMode, key=lambda m: m.value
    )
    assert len(set(modes_present)) == len(WindowsMode)  # không trùng mode


def test_wine_vm_remote_do_not_leak_into_native_or_web_counts() -> None:
    """Dò cụ thể: wine/vm/remote (phụ thuộc Windows) không được cộng nhầm
    vào native_linux/web_linux (không phụ thuộc Windows)."""

    report = compute_coverage(_mixed_mode_entries())
    by_mode = {m.mode: m for m in report.by_windows_mode}

    assert by_mode[WindowsMode.WEB_LINUX].total == 3
    assert by_mode[WindowsMode.WINE].total == 2
    assert by_mode[WindowsMode.WINDOWS_VM].total == 1
    assert by_mode[WindowsMode.REMOTE_WINDOWS].total == 2
    assert by_mode[WindowsMode.NATIVE_LINUX].total == 2

    # web_linux không được "mượn" workflow_verified của wine/remote/native
    assert by_mode[WindowsMode.WEB_LINUX].workflow_verified == 1


def test_listed_vs_working_never_equal_when_catalog_has_unverified_entries() -> None:
    """FACT ECO-022: '100 phần mềm được liệt kê' != '100 phần mềm chạy
    được' — kiểm bằng dữ liệu trộn mode thật (không chỉ bằng dữ liệu đơn
    giản 1-2 phần tử)."""

    entries = _mixed_mode_entries()
    listed, working = listed_vs_working(entries)
    assert listed == 10
    assert working == 4
    assert listed != working


def test_mode_coverage_dataclass_fields_are_disjoint_categories_summing_to_total() -> None:
    """Trong MỘT ``ModeCoverage``, 4 nhóm (verified/partial/blocked/
    not_yet_usable) phải phủ đúng toàn bộ entry của mode đó, không chồng
    lắp, không thiếu (mỗi entry rơi vào ĐÚNG MỘT nhóm)."""

    report = compute_coverage(_mixed_mode_entries())
    for mode_cov in report.by_windows_mode:
        assert isinstance(mode_cov, ModeCoverage)
        covered = (
            mode_cov.workflow_verified
            + mode_cov.partial_workflow
            + mode_cov.blocked_external_dependency
            + mode_cov.not_yet_usable
        )
        assert covered == mode_cov.total, (
            f"Mode {mode_cov.mode.value}: tổng 4 nhóm ({covered}) != total "
            f"({mode_cov.total}) — có entry bị đếm trùng hoặc bị bỏ sót."
        )
