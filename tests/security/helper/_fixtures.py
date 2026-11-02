"""Fixture dùng chung cho test WP7 (``namios_helper``)."""

from __future__ import annotations

from namios_core.helper_types import SystemCapabilities, UpdateStatus
from namios_helper.allowlist import ApprovedPlanEntry, PackagePlanAllowlist
from namios_helper.authenticated import AuthenticatedSystemHelper
from namios_helper.policy import InMemoryPolkitAuthority
from namios_helper.service import SystemHelperService

ACTIVE_UID = 1000
ADMIN_UID = 1000  # cùng user, đã xác thực admin riêng cho action nhạy
ACTIVE_ONLY_UID = 1500  # có session active nhưng CHƯA xác thực admin
OTHER_UID = 2000  # không có session active, không có quyền admin
ROOT_UID = 0


def make_allowlist() -> PackagePlanAllowlist:
    allowlist = PackagePlanAllowlist()
    allowlist.register(
        ApprovedPlanEntry(
            allowlist_key="misa-sme-connector-v1",
            plan_id="plan-misa-sme-connector-v1",
            package_refs=("misa-sme-connector",),
        )
    )
    return allowlist


def make_capabilities() -> SystemCapabilities:
    return SystemCapabilities(
        os_build="debian-12",
        kernel="5.14.0-333.el9.x86_64",
        session_type="headless",
        sandbox_mode="none",
        has_kvm=False,
    )


def make_update_status() -> UpdateStatus:
    return UpdateStatus(pending=(), reboot_required=False)


def make_authority() -> InMemoryPolkitAuthority:
    return InMemoryPolkitAuthority(
        active_session_uids=frozenset({ACTIVE_UID, ACTIVE_ONLY_UID}),
        admin_authenticated_uids=frozenset({ADMIN_UID}),
    )


def make_helper() -> AuthenticatedSystemHelper:
    service = SystemHelperService(
        allowlist=make_allowlist(),
        capabilities_provider=make_capabilities,
        update_status_provider=make_update_status,
    )
    return AuthenticatedSystemHelper(service, make_authority())
