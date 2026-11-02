"""System-helper typed API (WP7 hiện thực — SEC-001, CLI-004). Xem
M1-INTERFACES.md §7.5.

KHÔNG có ``RunCommand``. KHÔNG cho caller truyền repository/key/package tùy ý
ngoài allowlist đã phát hành. Thao tác phân vùng KHÔNG qua helper này.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SystemCapabilities:
    os_build: str
    kernel: str
    session_type: str
    sandbox_mode: str
    has_kvm: bool


@dataclass(frozen=True)
class PackagePlanRequest:
    allowlist_key: str  # KHÓA trỏ tới plan đã duyệt, KHÔNG phải tên package tự do


@dataclass(frozen=True)
class ApprovedPackagePlan:
    plan_id: str
    signed_digest: str


@dataclass(frozen=True)
class UpdateStatus:
    pending: tuple[str, ...]
    reboot_required: bool


class SystemHelper(Protocol):
    def GetSystemCapabilities(self) -> SystemCapabilities: ...

    def PlanPackageInstall(self, req: PackagePlanRequest) -> ApprovedPackagePlan: ...

    def ApplyApprovedPackagePlan(self, plan: ApprovedPackagePlan) -> UpdateStatus: ...

    def GetUpdateStatus(self) -> UpdateStatus: ...
