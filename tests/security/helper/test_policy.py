"""SEC-01: mỗi method gắn một action Polkit riêng; caller không hợp lệ hoặc
Polkit deny → ``E_PERMISSION_DENIED`` (exit 5), KHÔNG đổi hệ thống."""

from __future__ import annotations

import pytest
from tests.security.helper._fixtures import (
    ACTIVE_ONLY_UID,
    ACTIVE_UID,
    ADMIN_UID,
    OTHER_UID,
    ROOT_UID,
    make_helper,
)

from namios_core.errors import ErrorCode, exit_code_for
from namios_core.helper_types import PackagePlanRequest
from namios_helper.caller import CallerIdentity
from namios_helper.errors import PermissionDeniedError
from namios_helper.policy import ACTION_AUTH_REQUIREMENT, METHOD_TO_ACTION, AuthRequirement


def test_moi_method_co_dung_1_action_polkit_rieng() -> None:
    assert set(METHOD_TO_ACTION) == {
        "GetSystemCapabilities",
        "PlanPackageInstall",
        "ApplyApprovedPackagePlan",
        "GetUpdateStatus",
    }
    # 4 method → 4 action riêng biệt, không trùng nhau.
    actions = list(METHOD_TO_ACTION.values())
    assert len(set(actions)) == len(actions) == 4
    for action in actions:
        assert action in ACTION_AUTH_REQUIREMENT


def test_get_capabilities_allow_active_no_auth_pass_khi_co_session() -> None:
    helper = make_helper()
    caller = CallerIdentity(uid=ACTIVE_UID)
    caps = helper.GetSystemCapabilities(caller)
    assert caps.os_build == "debian-12"


def test_get_capabilities_tu_choi_khi_khong_co_session_active() -> None:
    helper = make_helper()
    caller = CallerIdentity(uid=OTHER_UID)
    with pytest.raises(PermissionDeniedError) as exc_info:
        helper.GetSystemCapabilities(caller)
    assert exc_info.value.code == ErrorCode.E_PERMISSION_DENIED
    assert exit_code_for(exc_info.value.code) == 5


def test_plan_package_yeu_cau_auth_admin_keep() -> None:
    assert ACTION_AUTH_REQUIREMENT[METHOD_TO_ACTION["PlanPackageInstall"]] == (
        AuthRequirement.AUTH_ADMIN_KEEP
    )


def test_plan_package_tu_choi_khi_co_session_nhung_chua_xac_thuc_admin() -> None:
    helper = make_helper()
    # ACTIVE_ONLY_UID có session desktop active (đủ cho action đọc) nhưng
    # CHƯA xác thực admin — action nhạy (plan-package) PHẢI vẫn bị từ chối.
    caller = CallerIdentity(uid=ACTIVE_ONLY_UID)
    with pytest.raises(PermissionDeniedError):
        helper.PlanPackageInstall(caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1"))


def test_plan_package_pass_khi_da_xac_thuc_admin() -> None:
    helper = make_helper()
    caller = CallerIdentity(uid=ADMIN_UID)
    plan = helper.PlanPackageInstall(
        caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1")
    )
    assert plan.plan_id == "plan-misa-sme-connector-v1"


def test_apply_package_tu_choi_voi_caller_khong_hop_le_khong_thay_doi_he_thong() -> None:
    helper = make_helper()
    admin_caller = CallerIdentity(uid=ADMIN_UID)
    plan = helper.PlanPackageInstall(
        admin_caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1")
    )

    # Caller khác (không có quyền) cố apply plan vừa tạo → phải bị từ chối
    # ở TẦNG POLKIT, trước khi chạm tới allowlist/verify_plan.
    bad_caller = CallerIdentity(uid=OTHER_UID)
    with pytest.raises(PermissionDeniedError) as exc_info:
        helper.ApplyApprovedPackagePlan(bad_caller, plan)
    assert exc_info.value.code == ErrorCode.E_PERMISSION_DENIED


def test_root_khong_tu_dong_duoc_cap_quyen_chi_vi_la_root() -> None:
    # Bất biến quan trọng: InMemoryPolkitAuthority KHÔNG có "root bypass" —
    # quyền chỉ do allowlist uid tường minh quyết định. Nếu root chưa được
    # thêm vào active_session_uids/admin_authenticated_uids, root CŨNG bị
    # từ chối — tránh giả định ngầm "root luôn được phép".
    helper = make_helper()
    caller = CallerIdentity(uid=ROOT_UID)
    with pytest.raises(PermissionDeniedError):
        helper.GetSystemCapabilities(caller)
