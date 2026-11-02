"""SEC-01: luồng end-to-end qua fake bus — mô phỏng một D-Bus call thật đi
từ "connection" (uid do bus cấp) tới adaptor xác thực tới service, KHÔNG
dùng D-Bus/polkitd thật (headless tại host build này)."""

from __future__ import annotations

import pytest
from tests.security.helper._fixtures import ACTIVE_UID, ADMIN_UID, OTHER_UID, make_helper

from namios_core.helper_types import PackagePlanRequest
from namios_helper.errors import PermissionDeniedError
from namios_helper.fakebus import FakeSystemBus


def test_goi_qua_fake_bus_dung_uid_cua_connection() -> None:
    bus = FakeSystemBus()
    bus.connect(":1.50", uid=ACTIVE_UID)
    helper = make_helper()

    caller = bus.call(":1.50", "GetSystemCapabilities")
    caps = helper.GetSystemCapabilities(caller)
    assert caps.has_kvm is False

    # call log ghi lại đúng method/sender — dùng được cho audit sau này.
    assert bus.call_log[-1][0] == ":1.50"
    assert bus.call_log[-1][1] == "GetSystemCapabilities"


def test_connection_khong_the_tu_nang_quyen_qua_tham_so_call() -> None:
    bus = FakeSystemBus()
    bus.connect(":1.60", uid=OTHER_UID)
    helper = make_helper()

    # Tham số call() cố ý nhồi "uid": 0 / "is_admin": True — bus KHÔNG đọc
    # các tham số này để suy ra danh tính, chỉ dùng uid của connection.
    caller = bus.call(
        ":1.60",
        "PlanPackageInstall",
        {"uid": 0, "is_admin": True, "allowlist_key": "misa-sme-connector-v1"},
    )
    assert caller.uid == OTHER_UID

    with pytest.raises(PermissionDeniedError):
        helper.PlanPackageInstall(caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1"))


def test_hai_connection_khac_nhau_co_quyen_khac_nhau() -> None:
    bus = FakeSystemBus()
    bus.connect(":1.70", uid=ADMIN_UID)
    bus.connect(":1.71", uid=OTHER_UID)
    helper = make_helper()

    admin_caller = bus.call(":1.70", "PlanPackageInstall")
    other_caller = bus.call(":1.71", "PlanPackageInstall")

    plan = helper.PlanPackageInstall(
        admin_caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1")
    )
    assert plan.plan_id

    with pytest.raises(PermissionDeniedError):
        helper.PlanPackageInstall(
            other_caller, PackagePlanRequest(allowlist_key="misa-sme-connector-v1")
        )


@pytest.mark.skip(
    reason=(
        "blocked_external_dependency: cần D-Bus system bus thật + polkitd chạy "
        "để test đăng ký object org.namios.SystemHelper1 lên bus thật và "
        "CheckAuthorization thật qua dbus-next/python-dbus; host build hiện "
        "tại headless, không có session bus/system bus/polkitd (xác nhận bởi "
        "docs/_m0_inventory_raw.md + CLAUDE.md mục Môi trường build). Phần "
        "logic policy/allowlist/caller-identity ĐÃ được test đầy đủ ở trên "
        "bằng fake bus — chỉ phần wiring D-Bus/polkitd thật là BLOCKED, "
        "thuộc tích hợp M3."
    )
)
def test_dbus_system_bus_that_blocked() -> None:  # pragma: no cover
    raise AssertionError("Không chạy — môi trường thiếu D-Bus/polkitd thật")
