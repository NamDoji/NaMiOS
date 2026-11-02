"""SEC-01: introspection — KHÔNG tồn tại method kiểu ``RunCommand`` ở bất kỳ
tầng public nào của WP7; danh sách method công khai khớp CHÍNH XÁC §7.5."""

from __future__ import annotations

import inspect

from namios_core.helper_types import SystemHelper
from namios_helper import dbus_interface
from namios_helper.authenticated import AuthenticatedSystemHelper
from namios_helper.service import PUBLIC_METHOD_NAMES, SystemHelperService


def _public_method_names(cls: type) -> set[str]:
    return {
        name
        for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def test_system_helper_protocol_chi_dung_4_method() -> None:
    expected = {
        "GetSystemCapabilities",
        "PlanPackageInstall",
        "ApplyApprovedPackagePlan",
        "GetUpdateStatus",
    }
    assert _public_method_names(SystemHelper) == expected


def test_service_khong_co_runcommand_hay_method_la() -> None:
    names = _public_method_names(SystemHelperService)
    assert names == set(PUBLIC_METHOD_NAMES)
    for forbidden in dbus_interface.FORBIDDEN_METHOD_NAMES:
        assert forbidden not in names


def test_authenticated_wrapper_cung_khong_co_runcommand() -> None:
    names = _public_method_names(AuthenticatedSystemHelper)
    assert names == set(PUBLIC_METHOD_NAMES)
    for forbidden in dbus_interface.FORBIDDEN_METHOD_NAMES:
        assert forbidden not in names


def test_dbus_method_signatures_khong_chua_mang_lenh() -> None:
    # KHÔNG có chữ ký nào dùng "as" (array of string) cho tham số VÀO —
    # nghĩa là không method nào nhận danh sách argv/lệnh tùy ý làm input.
    for method_name, (in_sig, _out_sig) in dbus_interface.METHOD_SIGNATURES.items():
        assert "as" not in in_sig, f"{method_name} nhận mảng chuỗi làm input — vi phạm CLI-004"
    assert dbus_interface.ALLOWED_METHOD_NAMES == set(PUBLIC_METHOD_NAMES)
    for forbidden in dbus_interface.FORBIDDEN_METHOD_NAMES:
        assert forbidden not in dbus_interface.ALLOWED_METHOD_NAMES
