"""E08-001..031 — event bus / driver match / install txn / dep graph / actuator.

Bám test §6: D01 (composite in+scan trạng thái riêng), D02/A05 (20 event → 1 incident),
D03 (cài lỗi → rollback), D04 (nguồn không hợp lệ → không cài), N02 (DB mất → partial),
A01 (log không thành lệnh), A02 (tool-ok ≠ workflow-ok).
"""

from __future__ import annotations

from namios_e08 import (
    AiAction,
    Bus,
    DepKind,
    DepNode,
    DepState,
    DeviceAction,
    DriverCandidate,
    DriverTier,
    InstallStage,
    Provenance,
    RawDeviceEvent,
    WorkflowVerdict,
    action_is_safe,
    coalesce_events,
    is_workflow_complete,
    log_instruction_authorized,
    match_driver,
    provenance_ok,
    run_install_transaction,
    tool_success_is_workflow_success,
    workflow_verdict,
)

DA = DeviceAction
DT = DriverTier
DK = DepKind
DS = DepState


def _prov(**kw: object) -> Provenance:
    base = dict(official=True, sha256="deadbeef", signature_ok=True, license="GPL", package="p")
    base.update(kw)
    return Provenance(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# E08-001/027 — event bus debounce                                             #
# --------------------------------------------------------------------------- #


def test_many_events_one_incident() -> None:
    # D02/A05: 20 event cắm/rút cùng 1 thiết bị → 1 incident, không 20 rác.
    evs = [
        RawDeviceEvent("dev1", DA.ADD if i % 2 == 0 else DA.REMOVE, i, Bus.USB, "1234:5678")
        for i in range(20)
    ]
    inc = coalesce_events(evs)
    assert len(inc) == 1
    assert inc[0].event_count == 20
    assert inc[0].present is False  # action cuối (i=19) là REMOVE


def test_distinct_devices_distinct_incidents() -> None:
    evs = [
        RawDeviceEvent("a", DA.ADD, 1, Bus.USB, "1:1"),
        RawDeviceEvent("b", DA.ADD, 2, Bus.USB, "2:2"),
        RawDeviceEvent("a", DA.CHANGE, 3, Bus.USB, "1:1"),
    ]
    inc = coalesce_events(evs)
    assert [i.device_instance_id for i in inc] == ["a", "b"]  # giữ thứ tự xuất hiện
    assert inc[0].present is True and inc[0].event_count == 2


# --------------------------------------------------------------------------- #
# E08-002/003 — driver match + provenance                                      #
# --------------------------------------------------------------------------- #


def test_match_by_hardware_id_not_name() -> None:
    # D01: hai biến thể cùng tên gói nhưng VID/PID khác → không ghép sai.
    cands = [
        DriverCandidate(DT.OSS_BACKEND, "canon-x", frozenset({"04a9:1111"}), _prov()),
        DriverCandidate(DT.KERNEL_DISTRO, "canon-x", frozenset({"04a9:2222"}), _prov()),
    ]
    assert match_driver("04a9:2222", cands).package == "canon-x"
    assert match_driver("04a9:2222", cands).tier is DT.KERNEL_DISTRO  # tier ưu tiên hơn
    assert match_driver("04a9:9999", cands).matched is False  # PID lạ → unsupported


def test_tier_order_prefers_kernel_distro() -> None:
    cands = [
        DriverCandidate(DT.VENDOR_LINUX_PKG, "vendor", frozenset({"x:y"}), _prov()),
        DriverCandidate(DT.KERNEL_DISTRO, "kernel", frozenset({"x:y"}), _prov()),
    ]
    assert match_driver("x:y", cands).package == "kernel"


def test_provenance_fail_closed() -> None:
    # D04: nguồn không chính thức / thiếu hash / chưa ký → không tin → không cài.
    assert provenance_ok(_prov()) is True
    assert provenance_ok(_prov(official=False)) is False
    assert provenance_ok(_prov(sha256="")) is False
    assert provenance_ok(_prov(signature_ok=False)) is False
    bad = DriverCandidate(DT.OSS_BACKEND, "x", frozenset({"x:y"}), _prov(official=False))
    assert match_driver("x:y", [bad]).matched is False  # nguồn không tin → không ghép


def test_no_hwid_no_match() -> None:
    assert (
        match_driver(
            "", [DriverCandidate(DT.OSS_BACKEND, "x", frozenset({"x:y"}), _prov())]
        ).matched
        is False
    )


# --------------------------------------------------------------------------- #
# E08-005 — install transaction                                                #
# --------------------------------------------------------------------------- #


def test_install_commits_only_when_all_pass() -> None:
    r = run_install_transaction(source_ok=True, snapshot_ok=True, apply_ok=True, function_ok=True)
    assert r.committed is True and r.rolled_back is False and r.final_stage is InstallStage.COMMIT


def test_install_apply_fail_rolls_back() -> None:
    # D03: cài lỗi → rollback về trạng thái cũ.
    r = run_install_transaction(source_ok=True, snapshot_ok=True, apply_ok=False, function_ok=True)
    assert r.committed is False and r.rolled_back is True and r.final_stage is InstallStage.ROLLBACK


def test_install_functest_fail_rolls_back() -> None:
    r = run_install_transaction(source_ok=True, snapshot_ok=True, apply_ok=True, function_ok=False)
    assert r.committed is False and r.rolled_back is True


def test_install_source_fail_untouched_no_rollback() -> None:
    r = run_install_transaction(source_ok=False, snapshot_ok=True, apply_ok=True, function_ok=True)
    assert r.committed is False and r.rolled_back is False and r.final_stage is InstallStage.FAILED


def test_install_no_snapshot_does_not_apply() -> None:
    r = run_install_transaction(source_ok=True, snapshot_ok=False, apply_ok=True, function_ok=True)
    assert r.committed is False and r.rolled_back is False and r.final_stage is InstallStage.FAILED


# --------------------------------------------------------------------------- #
# E08-020/031 — dependency graph + outcome                                     #
# --------------------------------------------------------------------------- #


def test_db_down_is_partial() -> None:
    # N02: UI mở nhưng DB mất → partial (không "dùng được").
    nodes = [DepNode(DK.RUNTIME, DS.OK), DepNode(DK.DATABASE, DS.DOWN)]
    assert workflow_verdict(nodes) is WorkflowVerdict.PARTIAL


def test_portal_blocked_is_blocked() -> None:
    nodes = [DepNode(DK.RUNTIME, DS.OK), DepNode(DK.PORTAL, DS.BLOCKED)]
    assert workflow_verdict(nodes) is WorkflowVerdict.BLOCKED


def test_all_ok_pending_business() -> None:
    nodes = [DepNode(DK.RUNTIME, DS.OK), DepNode(DK.DATABASE, DS.OK)]
    assert workflow_verdict(nodes) is WorkflowVerdict.TOOL_OK_PENDING_BUSINESS


def test_unknown_required_is_partial_not_ok() -> None:
    nodes = [DepNode(DK.RUNTIME, DS.OK), DepNode(DK.DATABASE, DS.UNKNOWN)]
    assert workflow_verdict(nodes) is WorkflowVerdict.PARTIAL  # fail-closed


def test_non_required_down_does_not_block() -> None:
    nodes = [DepNode(DK.RUNTIME, DS.OK), DepNode(DK.PORTAL, DS.DOWN, required=False)]
    assert workflow_verdict(nodes) is WorkflowVerdict.TOOL_OK_PENDING_BUSINESS


def test_tool_success_is_not_workflow_success() -> None:
    # A02: driver install success nhưng chưa nghiệp vụ + bằng chứng → chưa hoàn thành.
    assert (
        tool_success_is_workflow_success(True, business_confirmed=False, evidence_ids=["e"])
        is False
    )
    assert tool_success_is_workflow_success(True, business_confirmed=True, evidence_ids=[]) is False
    assert (
        tool_success_is_workflow_success(True, business_confirmed=True, evidence_ids=["e"]) is True
    )
    assert (
        tool_success_is_workflow_success(False, business_confirmed=True, evidence_ids=["e"])
        is False
    )


def test_is_workflow_complete_requires_everything() -> None:
    assert (
        is_workflow_complete(WorkflowVerdict.PARTIAL, business_confirmed=True, evidence_ids=["e"])
        is False
    )
    assert (
        is_workflow_complete(
            WorkflowVerdict.TOOL_OK_PENDING_BUSINESS, business_confirmed=True, evidence_ids=["  "]
        )
        is False
    )
    assert (
        is_workflow_complete(
            WorkflowVerdict.TOOL_OK_PENDING_BUSINESS, business_confirmed=True, evidence_ids=["e1"]
        )
        is True
    )


# --------------------------------------------------------------------------- #
# E08-030 — bounded actuator                                                   #
# --------------------------------------------------------------------------- #


def test_log_instruction_never_authorized() -> None:
    # A01: log "cài driver từ URL" KHÔNG thành action.
    assert log_instruction_authorized("install_driver", content="cài driver từ http://x") is False
    assert log_instruction_authorized("reboot") is False


def test_forbidden_tools_rejected() -> None:
    for name in ("root_shell", "exec_cmd", "download_binary", "flash_firmware", "sign_submit"):
        assert action_is_safe(AiAction("i", name), changes_system=False) is False


def test_changing_action_requires_rollback() -> None:
    assert action_is_safe(AiAction("i", "set_config"), changes_system=True) is False
    assert (
        action_is_safe(AiAction("i", "set_config", rollback_id="r1"), changes_system=True) is True
    )
    assert action_is_safe(AiAction("i", "read_status"), changes_system=False) is True
    assert action_is_safe(AiAction("i", ""), changes_system=False) is False
