"""SYS-037 — validator hợp đồng: route thiếu nguồn/version; bước completed thiếu evidence."""

from __future__ import annotations

from namios_sys import (
    ActionStatus,
    AppRoute,
    RunState,
    WindowsMode,
    WorkflowRun,
    WorkflowStepRun,
    app_route_from_dict,
    validate_app_route,
    validate_workflow_run,
    workflow_run_from_dict,
)
from namios_sys._errors import SysErrorCode


def test_route_missing_version_rejected() -> None:
    errs = validate_app_route(AppRoute(app_id="misa", version="", publisher="MISA"))
    assert any(e.code == SysErrorCode.E_SYS_ROUTE_NO_VERSION.value for e in errs)


def test_wine_route_missing_source_rejected() -> None:
    r = AppRoute(
        app_id="misa", version="2024", publisher="", installer_hash=None, mode=WindowsMode.WINE
    )
    errs = validate_app_route(r)
    assert any(e.code == SysErrorCode.E_SYS_ROUTE_NO_SOURCE.value for e in errs)


def test_wine_route_with_hash_ok() -> None:
    r = AppRoute(app_id="misa", version="2024", installer_hash="sha256:aa", mode=WindowsMode.WINE)
    assert validate_app_route(r) == []


def test_native_route_without_source_ok() -> None:
    # Native/web không cần bộ cài → không đòi nguồn.
    r = AppRoute(app_id="libreoffice", version="24.8", mode=WindowsMode.NATIVE_LINUX)
    assert validate_app_route(r) == []


def test_step_success_without_evidence_rejected() -> None:
    run = WorkflowRun(
        task_id="t",
        user_intent="in bảng lương",
        steps=(WorkflowStepRun(step_id="print", name="print", status=ActionStatus.SUCCESS),),
    )
    errs = validate_workflow_run(run)
    assert any(e.code == SysErrorCode.E_SYS_STEP_NO_EVIDENCE.value for e in errs)


def test_step_success_with_evidence_ok() -> None:
    run = WorkflowRun(
        task_id="t",
        user_intent="in bảng lương",
        steps=(
            WorkflowStepRun("print", "print", ActionStatus.SUCCESS, evidence_ids=("ev1",)),
            WorkflowStepRun(
                "blocked_step", "scan", ActionStatus.BLOCKED
            ),  # blocked ko cần evidence
        ),
    )
    assert validate_workflow_run(run) == []


def test_from_dict_never_trusts_state() -> None:
    # Nạp dict tự khai state=verified → LUÔN về proposed (gate mới quyết).
    run = workflow_run_from_dict({"task_id": "t", "user_intent": "x", "state": "verified"})
    assert run.state is RunState.PROPOSED


def test_from_dict_bad_enum_safe_default() -> None:
    r = app_route_from_dict(
        {"app_id": "a", "version": "1", "mode": "quantum", "license_status": "???"}
    )
    assert r.mode is WindowsMode.NATIVE_LINUX  # enum lạ → mặc định bảo thủ
