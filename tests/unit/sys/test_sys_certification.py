"""SYS-013 — chứng nhận 3 trục: GUI/tải/cài KHÔNG đủ; cần kỹ thuật+nghiệp vụ+ngoài."""

from __future__ import annotations

import pytest

from namios_sys import PublishedStatus, end_to_end_status, is_overclaim

PS = PublishedStatus


@pytest.mark.parametrize("tech", [PS.DOWNLOADABLE_ONLY, PS.LAUNCHES_ONLY, PS.UNSUPPORTED])
def test_download_launch_never_verified(tech: PublishedStatus) -> None:
    # Dù "đủ" nghiệp vụ + ngoài, mức tải/mở/unsupported KHÔNG BAO GIỜ thành verified.
    res = end_to_end_status(tech, business_approved=True, external_complete=True)
    assert res.status is tech
    assert res.status is not PS.WORKFLOW_VERIFIED


def test_technical_verified_needs_business() -> None:
    res = end_to_end_status(PS.WORKFLOW_VERIFIED, business_approved=False, external_complete=True)
    assert res.status is PS.PARTIAL_WORKFLOW


def test_technical_verified_needs_external() -> None:
    res = end_to_end_status(PS.WORKFLOW_VERIFIED, business_approved=True, external_complete=False)
    assert res.status is PS.BLOCKED_EXTERNAL_DEPENDENCY


def test_all_three_axes_verified() -> None:
    res = end_to_end_status(PS.WORKFLOW_VERIFIED, business_approved=True, external_complete=True)
    assert res.status is PS.WORKFLOW_VERIFIED


def test_partial_technical_stays_partial() -> None:
    res = end_to_end_status(PS.PARTIAL_WORKFLOW, business_approved=True, external_complete=True)
    assert res.status is PS.PARTIAL_WORKFLOW


def test_is_overclaim() -> None:
    assert (
        is_overclaim(PS.WORKFLOW_VERIFIED, business_approved=True, external_complete=False) is True
    )
    assert (
        is_overclaim(PS.WORKFLOW_VERIFIED, business_approved=True, external_complete=True) is False
    )
    assert (
        is_overclaim(PS.PARTIAL_WORKFLOW, business_approved=False, external_complete=False) is False
    )
