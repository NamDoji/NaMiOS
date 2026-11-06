"""SYS-038 — danh mục khả năng: chặn overclaim; tách tải/mở/đã-kiểm; chưa-kiểm."""

from __future__ import annotations

import pytest

from namios_sys import CapabilityCatalog, CapabilityRow, PublishedStatus, validate_capability_row

PS = PublishedStatus


def _row(
    status: PublishedStatus, *, test_date: str = "", workflow: str = "in-chung-tu"
) -> CapabilityRow:
    return CapabilityRow(
        app_id="misa",
        version="2024",
        workflow=workflow,
        published_status=status,
        test_date=test_date,
    )


def test_overclaim_usable_without_testdate_blocked() -> None:
    # workflow_verified mà không có ngày test = tự nhận quá mức → chặn.
    errs = validate_capability_row(_row(PS.WORKFLOW_VERIFIED))
    assert errs and errs[0].code.endswith("CAPABILITY_OVERCLAIM")
    with pytest.raises(ValueError):
        CapabilityCatalog().add(_row(PS.WORKFLOW_VERIFIED))


def test_verified_with_testdate_ok() -> None:
    cat = CapabilityCatalog()
    cat.add(_row(PS.WORKFLOW_VERIFIED, test_date="2026-11-01"))
    assert cat.lookup("misa", "2024") is not None


def test_download_launch_rows_need_no_testdate() -> None:
    cat = CapabilityCatalog()
    cat.add(_row(PS.DOWNLOADABLE_ONLY))
    cat.add(_row(PS.LAUNCHES_ONLY, workflow="mo-app"))
    assert len(cat.rows()) == 2  # mức chưa-dùng-được không bị đòi ngày test


def test_lookup_miss_is_untested() -> None:
    cat = CapabilityCatalog()
    assert cat.lookup("khong-co", "9") is None
    assert "chưa kiểm" in cat.untested_message("khong-co", "9").lower()


def test_summary_separates_levels() -> None:
    cat = CapabilityCatalog()
    cat.add(_row(PS.DOWNLOADABLE_ONLY))
    cat.add(_row(PS.LAUNCHES_ONLY, workflow="w2"))
    cat.add(_row(PS.WORKFLOW_VERIFIED, test_date="2026-11-01", workflow="w3"))
    s = cat.summary()
    assert s["available_to_download"] == 1 and s["launches"] == 1 and s["workflow_verified"] == 1


def test_lookup_normalizes_case_and_space() -> None:
    cat = CapabilityCatalog()
    cat.add(_row(PS.WORKFLOW_VERIFIED, test_date="2026-11-01"))
    assert cat.lookup("  MISA ", "2024") is not None
