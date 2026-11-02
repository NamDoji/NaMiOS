"""ECO-022 — Coverage dashboard (phần tính toán; hiển thị là CLI/UI tương
lai, ngoài phạm vi module này).

Tính % ``workflow_verified``/``partial_workflow``/``blocked_external_dependency``
trên số WORKFLOW ĐÃ KHẢO SÁT (không phải trên tổng "phần mềm được liệt kê" —
FACT ECO-022: "Không lấy '100 phần mềm được liệt kê' làm '100 phần mềm chạy
được'"); tách riêng theo ``WindowsMode`` (web/wine/vm/remote/native).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from namios_eco.models import ServiceEntry
from namios_eco.status import PublishedStatus, WindowsMode, is_windows_free

__all__ = [
    "ModeCoverage",
    "CoverageReport",
    "compute_coverage",
    "listed_vs_working",
]


@dataclass(frozen=True)
class ModeCoverage:
    """Coverage breakdown cho MỘT ``WindowsMode`` cụ thể."""

    mode: WindowsMode
    total: int
    workflow_verified: int
    partial_workflow: int
    blocked_external_dependency: int
    not_yet_usable: (
        int  # not_inventoried + downloadable_only + launches_only + unsupported + revoked
    )


@dataclass(frozen=True)
class CoverageReport:
    """Coverage toàn catalog, trên số workflow ĐÃ KHẢO SÁT
    (``total_surveyed`` = ``len(entries)`` truyền vào — caller chịu trách
    nhiệm chỉ truyền các entry đã khảo sát thật, KHÔNG đưa "số phần mềm nêu
    tên nhưng chưa khảo sát" vào mẫu số)."""

    total_surveyed: int
    workflow_verified: int
    partial_workflow: int
    blocked_external_dependency: int
    not_yet_usable: int
    by_windows_mode: tuple[ModeCoverage, ...]
    windows_free_ratio: float  # tỉ lệ workflow KHÔNG phụ thuộc Windows (ECO-015 §4.4)

    def workflow_verified_ratio(self) -> float:
        if self.total_surveyed == 0:
            return 0.0
        return self.workflow_verified / self.total_surveyed

    def partial_ratio(self) -> float:
        if self.total_surveyed == 0:
            return 0.0
        return self.partial_workflow / self.total_surveyed

    def blocked_ratio(self) -> float:
        if self.total_surveyed == 0:
            return 0.0
        return self.blocked_external_dependency / self.total_surveyed


_NOT_YET_USABLE = frozenset(
    {
        PublishedStatus.NOT_INVENTORIED,
        PublishedStatus.DOWNLOADABLE_ONLY,
        PublishedStatus.LAUNCHES_ONLY,
        PublishedStatus.UNSUPPORTED,
        PublishedStatus.REVOKED,
    }
)


def _mode_coverage(mode: WindowsMode, entries: Sequence[ServiceEntry]) -> ModeCoverage:
    subset = tuple(e for e in entries if e.windows_mode == mode)
    return ModeCoverage(
        mode=mode,
        total=len(subset),
        workflow_verified=sum(
            1 for e in subset if e.published_status == PublishedStatus.WORKFLOW_VERIFIED
        ),
        partial_workflow=sum(
            1 for e in subset if e.published_status == PublishedStatus.PARTIAL_WORKFLOW
        ),
        blocked_external_dependency=sum(
            1 for e in subset if e.published_status == PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY
        ),
        not_yet_usable=sum(1 for e in subset if e.published_status in _NOT_YET_USABLE),
    )


def compute_coverage(entries: Sequence[ServiceEntry]) -> CoverageReport:
    """Tính coverage trên đúng ``entries`` truyền vào — mẫu số là
    ``len(entries)``, KHÔNG tự suy luận số "phần mềm được nêu tên" nào khác."""

    total = len(entries)
    by_mode = tuple(_mode_coverage(mode, entries) for mode in WindowsMode)
    windows_free = sum(1 for e in entries if is_windows_free(e.windows_mode))

    return CoverageReport(
        total_surveyed=total,
        workflow_verified=sum(
            1 for e in entries if e.published_status == PublishedStatus.WORKFLOW_VERIFIED
        ),
        partial_workflow=sum(
            1 for e in entries if e.published_status == PublishedStatus.PARTIAL_WORKFLOW
        ),
        blocked_external_dependency=sum(
            1 for e in entries if e.published_status == PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY
        ),
        not_yet_usable=sum(1 for e in entries if e.published_status in _NOT_YET_USABLE),
        by_windows_mode=by_mode,
        windows_free_ratio=(windows_free / total) if total else 0.0,
    )


def listed_vs_working(entries: Sequence[ServiceEntry]) -> tuple[int, int]:
    """Trả ``(listed, working)``: ``listed`` = tổng số entry trong catalog
    (có thể gồm cả chưa khảo sát xong); ``working`` = số entry
    ``workflow_verified`` thật. FACT ECO-022: hai số này KHÔNG được đánh
    đồng — "100 phần mềm được liệt kê" khác "100 phần mềm chạy được"."""

    listed = len(entries)
    working = sum(1 for e in entries if e.published_status == PublishedStatus.WORKFLOW_VERIFIED)
    return listed, working
