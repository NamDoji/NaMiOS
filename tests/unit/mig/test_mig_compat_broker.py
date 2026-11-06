"""N10-017/023/027 — Compatibility Broker route theo TÁC VỤ.

Bất biến nghiệm thu N10-017: cùng app mở GUI được nhưng tác vụ ký số thất bại
(token/middleware chỉ-Windows BLOCKED) phải nhận route KHÁC cho tác vụ ký,
KHÔNG được coi là ready; kernel driver/token-chỉ-Windows KHÔNG BAO GIỜ route
Wine dù ``wine_tested=True``.
"""

from __future__ import annotations

from namios_mig import (
    CompatRoute,
    DepKind,
    DepNode,
    DepState,
    office_document_route,
    office_task_route,
    proposed_action_is_safe,
    resolve_task_route,
)
from namios_odc import DocumentMetadata, OfficeMode
from namios_pra import OfficeNeed, OfficeRoute

DK = DepKind
DS = DepState


def test_gui_open_ok_but_sign_task_blocked_gets_different_route() -> None:
    # N10-017 nghiệm thu literal: app mở GUI OK (ít dependency, không token),
    # nhưng tác vụ KÝ phụ thuộc PRINTER_TOKEN đã BLOCKED (chỉ-Windows) → route
    # khác, task_ready=False — dù wine_tested=True cho chính app đó.
    gui_nodes = [DepNode(DK.RUNTIME, DS.OK)]
    gui_result = resolve_task_route("open", gui_nodes, gui_opens=True, wine_tested=True)
    assert gui_result.route is CompatRoute.WINE
    assert gui_result.task_ready is True

    sign_nodes = [DepNode(DK.RUNTIME, DS.OK), DepNode(DK.PRINTER_TOKEN, DS.BLOCKED)]
    sign_result = resolve_task_route("sign_invoice", sign_nodes, gui_opens=True, wine_tested=True)
    assert sign_result.route != gui_result.route or sign_result.task_ready is False
    assert sign_result.route is not CompatRoute.WINE  # KHÔNG BAO GIỜ wine cho token-blocked
    assert sign_result.task_ready is False
    assert sign_result.gui_openable is True  # vẫn mở được GUI — chỉ tác vụ ký chặn


def test_kernel_token_blocker_never_routes_wine_even_with_windows_available() -> None:
    nodes = [DepNode(DK.PRINTER_TOKEN, DS.BLOCKED)]
    result = resolve_task_route(
        "sign", nodes, gui_opens=True, wine_tested=True, windows_licensed_available=True
    )
    assert result.route is CompatRoute.REMOTE_WINDOWS
    assert result.task_ready is False


def test_kernel_token_blocker_with_no_windows_is_unsupported() -> None:
    nodes = [DepNode(DK.PRINTER_TOKEN, DS.BLOCKED)]
    result = resolve_task_route("sign", nodes, gui_opens=True, wine_tested=True)
    assert result.route is CompatRoute.UNSUPPORTED
    assert result.task_ready is False


def test_vendor_native_or_web_always_preferred() -> None:
    nodes = [DepNode(DK.PRINTER_TOKEN, DS.BLOCKED)]  # dù có blocker, vendor route vẫn thắng
    native = resolve_task_route("x", nodes, gui_opens=True, vendor_linux_native=True)
    assert native.route is CompatRoute.NATIVE
    assert native.task_ready is True

    web = resolve_task_route("x", nodes, gui_opens=True, vendor_web=True)
    assert web.route is CompatRoute.WEB
    assert web.task_ready is True


def test_degraded_dependency_not_ready_even_if_wine_tested() -> None:
    nodes = [DepNode(DK.DATABASE, DS.DOWN)]
    result = resolve_task_route("open", nodes, gui_opens=True, wine_tested=True)
    assert result.route is CompatRoute.WINE
    assert result.task_ready is False  # DB mất → chưa đủ bằng chứng, dù route wine


def test_no_required_nodes_all_ok_is_ready() -> None:
    result = resolve_task_route("open", [], gui_opens=True, wine_tested=True)
    assert result.route is CompatRoute.WINE
    assert result.task_ready is True


def test_office_task_route_reuses_pra_office_route() -> None:
    # Macro/add-in KHÔNG bao giờ ra web (tái dùng namios_pra.office_route).
    macro_result = office_task_route(
        [OfficeNeed.MACRO], has_native_support=False, web_available=True
    )
    assert macro_result.route is OfficeRoute.WINDOWS_VM
    assert macro_result.windows_dependent is True


def test_office_document_route_reuses_odc_route_matrix() -> None:
    # Tái dùng namios_odc.route_matrix.resolve_document_route trực tiếp.
    metadata = DocumentMetadata(needs=frozenset({OfficeNeed.READ}))
    result = office_document_route(metadata, bundled_supported=True)
    assert result.mode is OfficeMode.BUNDLED_OFFICE
    assert result.openable is True


def test_proposed_action_rejects_download_crack() -> None:
    # N10-027 nghiệm thu: prompt "tải crack để chạy MISA" bị từ chối.
    assert proposed_action_is_safe("download_binary_from_forum", changes_system=True) is False
    assert proposed_action_is_safe("root_shell", changes_system=False) is False


def test_proposed_action_requires_rollback_for_system_changes() -> None:
    assert proposed_action_is_safe("install_recipe", changes_system=True, rollback_id="") is False
    assert proposed_action_is_safe("install_recipe", changes_system=True, rollback_id="r1") is True
    assert proposed_action_is_safe("read_status", changes_system=False) is True
