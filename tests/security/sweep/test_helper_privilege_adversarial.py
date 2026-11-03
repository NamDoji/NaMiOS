"""Helper privilege adversarial — SEC-001/CLI-004. Khong RunCommand/path
tuy y; caller gia danh khong leo thang; deny o BAT KY buoc nao thi KHONG
duoc co side-effect xuong tang nghiep vu."""

from __future__ import annotations

import inspect

import pytest

from namios_core.helper_types import ApprovedPackagePlan, PackagePlanRequest
from namios_helper.allowlist import ApprovedPlanEntry, PackagePlanAllowlist
from namios_helper.authenticated import AuthenticatedSystemHelper
from namios_helper.caller import CallerIdentity, identity_from_untrusted_request
from namios_helper.errors import PermissionDeniedError, StalePlanError, UnknownAllowlistKeyError
from namios_helper.policy import InMemoryPolkitAuthority
from namios_helper.service import PUBLIC_METHOD_NAMES, SystemHelperService

# ---------------------------------------------------------------------------
# Khong co RunCommand / method nhan argv-arbitrary nao trong interface cong khai.
# ---------------------------------------------------------------------------


def _make_service() -> SystemHelperService:
    from namios_core.helper_types import SystemCapabilities, UpdateStatus

    allowlist = PackagePlanAllowlist()
    allowlist.register(
        ApprovedPlanEntry(
            allowlist_key="misa-connector-v1",
            plan_id="plan-001",
            package_refs=("misa-sme-connector",),
        )
    )
    return SystemHelperService(
        allowlist=allowlist,
        capabilities_provider=lambda: SystemCapabilities(
            os_build="namios-1.0",
            kernel="6.1",
            session_type="wayland",
            sandbox_mode="bwrap",
            has_kvm=False,
        ),
        update_status_provider=lambda: UpdateStatus(pending=(), reboot_required=False),
    )


def test_system_helper_service_has_no_run_command_method() -> None:
    service = _make_service()
    public_methods = {name for name in dir(service) if not name.startswith("_")}
    forbidden_substrings = ("runcommand", "run_command", "exec", "shell", "spawn")
    for name in public_methods:
        lowered = name.lower()
        for bad in forbidden_substrings:
            assert bad not in lowered, f"method cong khai nghi ngo chay lenh tuy y: {name}"


def test_system_helper_service_public_methods_match_declared_allowlist_exactly() -> None:
    service = _make_service()
    actual_public = {
        name
        for name, member in inspect.getmembers(service)
        if not name.startswith("_") and inspect.ismethod(member)
    }
    assert actual_public == set(PUBLIC_METHOD_NAMES)


def test_plan_package_install_rejects_arbitrary_package_name_not_in_allowlist() -> None:
    service = _make_service()
    with pytest.raises(UnknownAllowlistKeyError):
        bogus_key = "apt-get install anything-i-want"
        service.PlanPackageInstall(PackagePlanRequest(allowlist_key=bogus_key))


def test_plan_package_install_rejects_path_traversal_as_allowlist_key() -> None:
    service = _make_service()
    with pytest.raises(UnknownAllowlistKeyError):
        service.PlanPackageInstall(PackagePlanRequest(allowlist_key="../../etc/passwd"))


def test_apply_approved_package_plan_rejects_forged_plan_with_fake_digest() -> None:
    service = _make_service()
    forged = ApprovedPackagePlan(plan_id="plan-001", signed_digest="0" * 64)
    with pytest.raises(StalePlanError):
        service.ApplyApprovedPackagePlan(forged)


def test_apply_approved_package_plan_rejects_plan_id_that_was_never_issued() -> None:
    service = _make_service()
    forged = ApprovedPackagePlan(plan_id="never-issued-plan", signed_digest="0" * 64)
    with pytest.raises(StalePlanError):
        service.ApplyApprovedPackagePlan(forged)


def test_apply_approved_package_plan_rejects_replayed_plan_after_allowlist_entry_removed() -> None:
    """Mo phong thu hoi: plan duoc issue hop le, sau do entry bi go khoi
    allowlist (vd thu hoi do bao mat) -- apply lai PHAI bi chan, khong duoc
    coi digest cu van hop le mai mai."""

    service = _make_service()
    plan = service.PlanPackageInstall(PackagePlanRequest(allowlist_key="misa-connector-v1"))
    service._allowlist.entries.clear()  # mo phong thu hoi packaging-time

    with pytest.raises(StalePlanError):
        service.ApplyApprovedPackagePlan(plan)


# ---------------------------------------------------------------------------
# CallerIdentity — PID tu khai KHONG duoc dung de suy ra quyen/uid.
# ---------------------------------------------------------------------------


def test_caller_identity_ignores_pid_claim_pretending_to_be_root() -> None:
    identity = identity_from_untrusted_request(trusted_uid=1000, requested_pid_claim=1)
    assert identity.uid == 1000
    assert identity.is_root() is False


def test_caller_identity_is_root_only_for_real_trusted_uid_zero() -> None:
    identity = identity_from_untrusted_request(trusted_uid=0)
    assert identity.is_root() is True


# ---------------------------------------------------------------------------
# AuthenticatedSystemHelper — deny PHAI xay ra TRUOC khi co side-effect
# xuong SystemHelperService (khong RunCommand-equivalent nao duoc thuc hien
# truoc khi qua het kiem tra).
# ---------------------------------------------------------------------------


def test_unauthenticated_caller_denied_before_any_service_side_effect() -> None:
    service = _make_service()
    authority = InMemoryPolkitAuthority()  # tu choi tat ca (mac dinh an toan)
    helper = AuthenticatedSystemHelper(service, authority)
    attacker = CallerIdentity(uid=1001)

    with pytest.raises(PermissionDeniedError):
        helper.PlanPackageInstall(attacker, PackagePlanRequest(allowlist_key="misa-connector-v1"))

    # Khong co plan nao duoc issue boi side-effect truoc khi tu choi.
    assert service._allowlist._issued_digests == {}


def test_caller_with_read_only_authorization_cannot_apply_package_plan() -> None:
    """Leo thang chieu ngang: caller duoc cap allow_active (doc) nhung
    KHONG duoc cap auth_admin_keep (ghi) -- goi method ghi van phai bi
    tu choi, du co session active."""

    service = _make_service()
    authority = InMemoryPolkitAuthority(active_session_uids=frozenset({2000}))
    helper = AuthenticatedSystemHelper(service, authority)
    caller = CallerIdentity(uid=2000)

    helper.GetSystemCapabilities(caller)  # duoc phep (doc)

    with pytest.raises(PermissionDeniedError):
        helper.PlanPackageInstall(caller, PackagePlanRequest(allowlist_key="misa-connector-v1"))


def test_admin_authorization_for_one_uid_does_not_grant_another_uid() -> None:
    service = _make_service()
    authority = InMemoryPolkitAuthority(admin_authenticated_uids=frozenset({3000}))
    helper = AuthenticatedSystemHelper(service, authority)
    impostor = CallerIdentity(uid=3001)

    with pytest.raises(PermissionDeniedError):
        helper.PlanPackageInstall(impostor, PackagePlanRequest(allowlist_key="misa-connector-v1"))


def test_permission_denied_error_details_do_not_leak_allowlist_key_value_structure() -> None:
    """``details`` cua PermissionDeniedError chi nen chua method/action/uid
    (metadata on dinh), KHONG nen echo lai noi dung request nhay cam neu co
    (o day request khong co gi nhay cam, nhung xac nhan khong co khoa
    'allowlist_key' hay payload request bi nhung thang vao details)."""

    service = _make_service()
    authority = InMemoryPolkitAuthority()
    helper = AuthenticatedSystemHelper(service, authority)
    attacker = CallerIdentity(uid=9999)

    request = PackagePlanRequest(allowlist_key="secret-internal-key-x")
    with pytest.raises(PermissionDeniedError) as exc_info:
        helper.PlanPackageInstall(attacker, request)

    details = exc_info.value.details or {}
    assert "allowlist_key" not in details
    assert set(details.keys()) <= {"method", "action", "uid"}
