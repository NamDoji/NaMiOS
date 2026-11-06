"""Adversarial QA cho tầng K0 trung thực ``namios_sys`` (Phụ lục 05).

Mục tiêu: PHÁ các bất biến trung thực (A..G). Mỗi test cố tạo một lối thoát
(bịa SUCCESS, auto-run .exe, qua mặt gate evidence, tự khai verified...). QA bắt
2 LỖ THẬT (B: dấu-chấm-cuối lách guard .exe; D: evidence rỗng qua mặt gate) — đã
VÁ ở ``src/namios_sys`` + khoá bằng 2 test regression (``_regression_``) ở đây.

Không mạng, không sleep, chỉ assert chuẩn.
"""

from __future__ import annotations

import pytest

from namios_sys import (
    ActionBroker,
    ActionKind,
    ActionRequest,
    ActionResult,
    ActionStatus,
    AppRoute,
    CapabilityCatalog,
    CapabilityRow,
    LicenseStatus,
    PublishedStatus,
    RunState,
    WindowsMode,
    WorkflowRun,
    WorkflowStepRun,
    app_route_from_dict,
    end_to_end_status,
    is_overclaim,
    validate_app_route,
    validate_capability_row,
    validate_workflow_run,
    workflow_run_from_dict,
)
from namios_sys._errors import SysErrorCode

# --------------------------------------------------------------------------- #
# Handlers giả dùng chung
# --------------------------------------------------------------------------- #


class _SuccessHandler:
    """Handler THẬT trả SUCCESS + đếm lần gọi (chứng minh broker không tự bịa)."""

    def __init__(self) -> None:
        self.calls = 0
        self.seen: list[ActionRequest] = []

    def execute(self, request: ActionRequest, action_id: str) -> ActionResult:
        self.calls += 1
        self.seen.append(request)
        return ActionResult(
            action_id=action_id,
            action=request.action,
            status=ActionStatus.SUCCESS,
            permission_ok=True,
            message_vi="ok",
        )


# =========================================================================== #
# A. ActionBroker KHÔNG BAO GIỜ SUCCESS khi chưa có handler thật.
# =========================================================================== #


@pytest.mark.parametrize("kind", list(ActionKind))
def test_A_no_handler_every_kind_blocks_honestly(kind: ActionKind) -> None:
    res = ActionBroker().dispatch(ActionRequest(action=kind, target="x"))
    assert res.status is ActionStatus.BLOCKED
    assert res.error_code == SysErrorCode.E_SYS_NO_HANDLER.value
    assert res.permission_ok is True  # không phải bị-chặn-quyền, chỉ chưa nối
    assert res.action_id.startswith("act-")
    assert res.status is not ActionStatus.SUCCESS


@pytest.mark.parametrize("kind", list(ActionKind))
def test_A_allow_all_policy_still_blocks_without_handler(kind: ActionKind) -> None:
    # Policy CHO PHÉP tất cả vẫn KHÔNG được biến thành SUCCESS khi thiếu handler.
    b = ActionBroker(policy=lambda req: True)
    res = b.dispatch(ActionRequest(action=kind, target="x"))
    assert res.status is ActionStatus.BLOCKED
    assert res.status is not ActionStatus.SUCCESS


def test_A_weird_params_mode_empty_target_still_blocks() -> None:
    # Tham số lạ / mode đặt sẵn / target rỗng đều KHÔNG mở được đường tới SUCCESS.
    weird = ActionRequest(
        action=ActionKind.PRINT,
        target="",
        params={"copies": 9999, "evil": object()},
        mode=WindowsMode.REMOTE_WINDOWS,
        requested_by="attacker",
    )
    res = ActionBroker().dispatch(weird)
    assert res.status is ActionStatus.BLOCKED
    assert res.route_mode is WindowsMode.REMOTE_WINDOWS  # mode phản chiếu trung thực


def test_A_non_enum_action_fails_closed_not_success() -> None:
    # Action là chuỗi thô (không phải enum) → FAILED fail-closed, tuyệt đối không SUCCESS.
    res = ActionBroker().dispatch(ActionRequest(action="open_file"))  # type: ignore[arg-type]
    assert res.status is ActionStatus.FAILED
    assert res.error_code == SysErrorCode.E_SYS_ACTION_UNKNOWN.value
    assert res.status is not ActionStatus.SUCCESS


def test_A_handler_failed_partial_passes_through_truthfully() -> None:
    # Handler trả FAILED/PARTIAL → broker KHÔNG nâng khống thành SUCCESS.
    class _FailHandler:
        def execute(self, request: ActionRequest, action_id: str) -> ActionResult:
            return ActionResult(action_id, request.action, ActionStatus.FAILED)

    b = ActionBroker()
    b.register(ActionKind.SCAN, _FailHandler())
    res = b.dispatch(ActionRequest(action=ActionKind.SCAN, target="scanner0"))
    assert res.status is ActionStatus.FAILED


def test_A_registered_handler_success_is_allowed() -> None:
    # Ngược chiều: CÓ handler thật trả SUCCESS thì SUCCESS là trung thực.
    h = _SuccessHandler()
    b = ActionBroker()
    b.register(ActionKind.PRINT, h)
    res = b.dispatch(ActionRequest(action=ActionKind.PRINT, target="bc.pdf"))
    assert res.status is ActionStatus.SUCCESS
    assert h.calls == 1


# =========================================================================== #
# B. .exe/.msi/.bat/.cmd/.com/.scr trên OPEN_FILE KHÔNG được giữ OPEN_FILE.
# =========================================================================== #

_EXE_TARGETS = [
    "setup.exe",
    "/media/usb/installer.MSI",
    "run.bat",
    "go.CMD",
    "legacy.com",
    "saver.scr",
    "A.EXE ",  # trailing space + hoa
    "x.ExE",  # hoa/thường trộn
    "a.docx.exe",  # double-extension: phải bắt theo đuôi cuối
    "  padded.exe  ",
]


@pytest.mark.parametrize("target", _EXE_TARGETS)
def test_B_executable_open_file_becomes_open_app(target: str) -> None:
    res = ActionBroker().dispatch(ActionRequest(action=ActionKind.OPEN_FILE, target=target))
    assert res.action is ActionKind.OPEN_APP  # không còn OPEN_FILE chạy ngầm
    assert res.status is ActionStatus.BLOCKED  # chưa handler → vẫn không chạy


@pytest.mark.parametrize(
    "target",
    [
        "report.exemplar.pdf",  # ".exe" nằm giữa tên, KHÔNG phải đuôi
        "hop-dong.docx",
        "anh.jpeg",
        "executable_notes.txt",
        "exe",  # không có dấu chấm đuôi
        "scripts/readme.md",
    ],
)
def test_B_non_executable_names_not_misclassified(target: str) -> None:
    res = ActionBroker().dispatch(ActionRequest(action=ActionKind.OPEN_FILE, target=target))
    assert res.action is ActionKind.OPEN_FILE  # giữ nguyên, không cảnh báo nhầm


def test_B_exe_not_routed_to_file_opener_handler() -> None:
    # Nếu có handler OPEN_FILE (trình mở tệp có thể shell-exec), .exe KHÔNG được
    # chạm tới nó: phải bị tái phân loại sang OPEN_APP (ở đây: BLOCKED vì không
    # có handler OPEN_APP). Chứng minh .exe không auto-run qua đường mở tệp.
    opener = _SuccessHandler()
    b = ActionBroker()
    b.register(ActionKind.OPEN_FILE, opener)
    res = b.dispatch(ActionRequest(action=ActionKind.OPEN_FILE, target="virus.exe"))
    assert res.action is ActionKind.OPEN_APP
    assert res.status is ActionStatus.BLOCKED
    assert opener.calls == 0  # trình mở tệp KHÔNG được gọi với .exe


@pytest.mark.parametrize("target", ["virus.exe.", "setup.bat.", "x.exe. ", "run.cmd..", "s.scr."])
def test_B_regression_trailing_dot_cannot_bypass_exe_guard(target: str) -> None:
    # ĐÃ VÁ (HOLE B): _is_executable_target rstrip('. ') theo chuẩn hoá Windows/Wine
    # → 'virus.exe.' == 'virus.exe' → OPEN_APP, KHÔNG chạm handler mở tệp.
    opener = _SuccessHandler()
    b = ActionBroker()
    b.register(ActionKind.OPEN_FILE, opener)
    res = b.dispatch(ActionRequest(action=ActionKind.OPEN_FILE, target=target))
    assert res.action is ActionKind.OPEN_APP, f"{target!r} auto-chạy như OPEN_FILE"
    assert opener.calls == 0


# =========================================================================== #
# C. Policy DENY phải xảy ra TRƯỚC khi gọi handler (side-effect = 0).
# =========================================================================== #


def test_C_deny_before_handler_no_side_effect() -> None:
    h = _SuccessHandler()
    b = ActionBroker(policy=lambda req: False)
    b.register(ActionKind.SHARE, h)
    res = b.dispatch(ActionRequest(action=ActionKind.SHARE, target="secret.pdf"))
    assert res.status is ActionStatus.DENIED
    assert res.error_code == SysErrorCode.E_SYS_ACTION_DENIED.value
    assert res.permission_ok is False
    assert h.calls == 0  # handler TUYỆT ĐỐI không được gọi khi bị từ chối


def test_C_deny_sees_reclassified_app_not_raw_exe() -> None:
    # Policy được kiểm trên request ĐÃ tái phân loại; .exe OPEN_FILE → OPEN_APP
    # trước khi tới policy. Handler OPEN_APP không bao giờ chạy khi bị deny.
    seen_actions: list[ActionKind] = []

    def policy(req: ActionRequest) -> bool:
        seen_actions.append(req.action)
        return False

    h = _SuccessHandler()
    b = ActionBroker(policy=policy)
    b.register(ActionKind.OPEN_APP, h)
    res = b.dispatch(ActionRequest(action=ActionKind.OPEN_FILE, target="setup.exe"))
    assert res.status is ActionStatus.DENIED
    assert seen_actions == [ActionKind.OPEN_APP]
    assert h.calls == 0


# =========================================================================== #
# D. schema: version bắt buộc; installer-mode cần nguồn; step done cần evidence.
# =========================================================================== #


@pytest.mark.parametrize("version", ["", "   ", "\t\n"])
def test_D_missing_or_blank_version_rejected(version: str) -> None:
    errs = validate_app_route(AppRoute(app_id="a", version=version))
    codes = [e.code for e in errs]
    assert SysErrorCode.E_SYS_ROUTE_NO_VERSION.value in codes


@pytest.mark.parametrize(
    "mode", [WindowsMode.WINE, WindowsMode.WINDOWS_VM, WindowsMode.REMOTE_WINDOWS]
)
def test_D_installer_mode_requires_real_source(mode: WindowsMode) -> None:
    # Không nguồn → lỗi; khoảng-trắng KHÔNG được tính là nguồn.
    errs = validate_app_route(
        AppRoute(app_id="a", version="1", publisher="  ", installer_hash="  ", mode=mode)
    )
    assert SysErrorCode.E_SYS_ROUTE_NO_SOURCE.value in [e.code for e in errs]


@pytest.mark.parametrize(
    "mode", [WindowsMode.WINE, WindowsMode.WINDOWS_VM, WindowsMode.REMOTE_WINDOWS]
)
def test_D_installer_mode_ok_with_any_real_source(mode: WindowsMode) -> None:
    errs = validate_app_route(
        AppRoute(app_id="a", version="1", installer_hash="sha256:abc", mode=mode)
    )
    assert SysErrorCode.E_SYS_ROUTE_NO_SOURCE.value not in [e.code for e in errs]


@pytest.mark.parametrize("mode", [WindowsMode.NATIVE_LINUX, WindowsMode.WEB_LINUX])
def test_D_native_web_need_no_source(mode: WindowsMode) -> None:
    errs = validate_app_route(AppRoute(app_id="a", version="1", mode=mode))
    assert errs == []


@pytest.mark.parametrize("status", [ActionStatus.SUCCESS, ActionStatus.PARTIAL])
def test_D_completed_step_without_evidence_rejected(status: ActionStatus) -> None:
    run = WorkflowRun(
        task_id="t",
        user_intent="x",
        steps=(WorkflowStepRun(step_id="s1", name="submit", status=status, evidence_ids=()),),
    )
    assert SysErrorCode.E_SYS_STEP_NO_EVIDENCE.value in [e.code for e in validate_workflow_run(run)]


@pytest.mark.parametrize("status", [ActionStatus.BLOCKED, ActionStatus.DENIED, ActionStatus.FAILED])
def test_D_non_completed_step_needs_no_evidence(status: ActionStatus) -> None:
    run = WorkflowRun(
        task_id="t",
        user_intent="x",
        steps=(WorkflowStepRun(step_id="s1", name="x", status=status, evidence_ids=()),),
    )
    assert validate_workflow_run(run) == []


@pytest.mark.parametrize("evidence", [("",), ("   ",), ("", ""), ("\t",)])
def test_D_regression_blank_evidence_does_not_count(evidence: tuple[str, ...]) -> None:
    # ĐÃ VÁ (HOLE D): validate_workflow_run đòi ÍT NHẤT MỘT evidence id non-blank
    # → evidence toàn rỗng/khoảng-trắng vẫn bị chặn (không bịa hoàn thành).
    run = WorkflowRun(
        task_id="t",
        user_intent="x",
        steps=(
            WorkflowStepRun(
                step_id="s1", name="submit", status=ActionStatus.SUCCESS, evidence_ids=evidence
            ),
        ),
    )
    # KỲ VỌNG TRUNG THỰC: evidence toàn rỗng/khoảng-trắng KHÔNG phải bằng chứng.
    assert SysErrorCode.E_SYS_STEP_NO_EVIDENCE.value in [e.code for e in validate_workflow_run(run)]


# =========================================================================== #
# E. from_dict không tin nhãn tự khai; enum lạ fallback an toàn.
# =========================================================================== #


@pytest.mark.parametrize("declared", ["verified", "running", "failed", "VERIFIED", "proposed", ""])
def test_E_workflow_run_from_dict_always_proposed(declared: str) -> None:
    run = workflow_run_from_dict(
        {
            "task_id": "t",
            "user_intent": "nộp thuế",
            "state": declared,  # tự khai — PHẢI bị bỏ qua
            "business_approval": "approved",
            "steps": [{"step_id": "s1", "name": "submit", "status": "success", "evidence_ids": []}],
        }
    )
    assert run.state is RunState.PROPOSED


def test_E_workflow_run_from_dict_bogus_step_status_safe() -> None:
    run = workflow_run_from_dict(
        {"task_id": "t", "user_intent": "x", "steps": [{"step_id": "s1", "status": "god_mode"}]}
    )
    # Trạng thái bước lạ → mặc định BLOCKED (bảo thủ), không nâng khống.
    assert run.steps[0].status is ActionStatus.BLOCKED


def test_E_app_route_from_dict_bogus_enums_fall_back_safe() -> None:
    route = app_route_from_dict(
        {"app_id": "a", "version": "1", "mode": "root_everything", "license_status": "pirated_ok"}
    )
    # Không crash; fallback về giá trị KHÔNG đặc quyền (native/unknown).
    assert route.mode is WindowsMode.NATIVE_LINUX
    assert route.license_status is LicenseStatus.UNKNOWN
    assert route.mode not in (
        WindowsMode.WINE,
        WindowsMode.WINDOWS_VM,
        WindowsMode.REMOTE_WINDOWS,
    )
    assert route.license_status is not LicenseStatus.LICENSED


def test_E_app_route_from_dict_valid_enums_preserved() -> None:
    route = app_route_from_dict({"app_id": "a", "version": "1", "mode": "wine"})
    assert route.mode is WindowsMode.WINE


# =========================================================================== #
# F. certification: không-dùng-được không bao giờ verified; verified cần đủ 3 trục.
# =========================================================================== #

_NON_VERIFIABLE_TECH = [
    PublishedStatus.DOWNLOADABLE_ONLY,
    PublishedStatus.LAUNCHES_ONLY,
    PublishedStatus.UNSUPPORTED,
    PublishedStatus.REVOKED,
    PublishedStatus.NOT_INVENTORIED,
    PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
]


@pytest.mark.parametrize("tech", _NON_VERIFIABLE_TECH)
def test_F_non_usable_technical_never_verified(tech: PublishedStatus) -> None:
    res = end_to_end_status(tech, business_approved=True, external_complete=True)
    assert res.status is not PublishedStatus.WORKFLOW_VERIFIED
    assert res.status is tech  # giữ nguyên, không tự nâng


def test_F_partial_technical_never_auto_verified() -> None:
    # Kỹ thuật mới PARTIAL → dù business+external đủ cũng KHÔNG nâng thành verified.
    res = end_to_end_status(
        PublishedStatus.PARTIAL_WORKFLOW, business_approved=True, external_complete=True
    )
    assert res.status is PublishedStatus.PARTIAL_WORKFLOW


def test_F_verified_requires_both_business_and_external() -> None:
    assert (
        end_to_end_status(
            PublishedStatus.WORKFLOW_VERIFIED, business_approved=True, external_complete=True
        ).status
        is PublishedStatus.WORKFLOW_VERIFIED
    )
    assert (
        end_to_end_status(
            PublishedStatus.WORKFLOW_VERIFIED, business_approved=False, external_complete=True
        ).status
        is PublishedStatus.PARTIAL_WORKFLOW
    )
    assert (
        end_to_end_status(
            PublishedStatus.WORKFLOW_VERIFIED, business_approved=True, external_complete=False
        ).status
        is PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY
    )
    assert (
        end_to_end_status(
            PublishedStatus.WORKFLOW_VERIFIED, business_approved=False, external_complete=False
        ).status
        is not PublishedStatus.WORKFLOW_VERIFIED
    )


@pytest.mark.parametrize(
    ("biz", "ext", "expected"),
    [
        (True, True, False),
        (False, True, True),
        (True, False, True),
        (False, False, True),
    ],
)
def test_F_is_overclaim_exact_for_verified_claim(biz: bool, ext: bool, expected: bool) -> None:
    assert (
        is_overclaim(
            PublishedStatus.WORKFLOW_VERIFIED, business_approved=biz, external_complete=ext
        )
        is expected
    )


@pytest.mark.parametrize(
    "claimed", [s for s in PublishedStatus if s is not PublishedStatus.WORKFLOW_VERIFIED]
)
def test_F_is_overclaim_false_for_non_verified_claim(claimed: PublishedStatus) -> None:
    # Chỉ claim 'workflow_verified' mới có thể là overclaim.
    assert is_overclaim(claimed, business_approved=False, external_complete=False) is False


# =========================================================================== #
# G. capability_catalog: add chặn overclaim; lookup miss None; summary không gộp.
# =========================================================================== #


@pytest.mark.parametrize(
    "status", [PublishedStatus.WORKFLOW_VERIFIED, PublishedStatus.PARTIAL_WORKFLOW]
)
@pytest.mark.parametrize("date", ["", "   ", "\t"])
def test_G_add_rejects_usable_row_without_test_date(status: PublishedStatus, date: str) -> None:
    cat = CapabilityCatalog()
    row = CapabilityRow(
        app_id="a", version="1", workflow="w", published_status=status, test_date=date
    )
    assert validate_capability_row(row)  # có lỗi overclaim
    with pytest.raises(ValueError):
        cat.add(row)
    assert cat.rows() == ()  # KHÔNG được lọt vào kho


@pytest.mark.parametrize(
    "status", [PublishedStatus.DOWNLOADABLE_ONLY, PublishedStatus.LAUNCHES_ONLY]
)
def test_G_download_launch_rows_need_no_date(status: PublishedStatus) -> None:
    cat = CapabilityCatalog()
    cat.add(
        CapabilityRow(app_id="a", version="1", workflow="w", published_status=status, test_date="")
    )
    assert len(cat.rows()) == 1


def test_G_lookup_miss_returns_none() -> None:
    cat = CapabilityCatalog()
    cat.add(
        CapabilityRow(
            app_id="MISA",
            version="2024",
            workflow="xuat-hoa-don",
            published_status=PublishedStatus.WORKFLOW_VERIFIED,
            test_date="2026-10-01",
        )
    )
    assert cat.lookup("khong-ton-tai", "9.9") is None
    assert cat.lookup("MISA", "2023") is None  # sai version → miss
    assert cat.lookup("misa", "2024") is not None  # khớp không phân biệt hoa/thường
    assert cat.lookup("MISA", "2024", workflow="workflow-khac") is None  # sai workflow → miss


def test_G_summary_does_not_conflate_levels() -> None:
    cat = CapabilityCatalog()
    cat.add(
        CapabilityRow(
            app_id="d",
            version="1",
            workflow="w",
            published_status=PublishedStatus.DOWNLOADABLE_ONLY,
            test_date="",
        )
    )
    cat.add(
        CapabilityRow(
            app_id="l",
            version="1",
            workflow="w",
            published_status=PublishedStatus.LAUNCHES_ONLY,
            test_date="",
        )
    )
    cat.add(
        CapabilityRow(
            app_id="v",
            version="1",
            workflow="w",
            published_status=PublishedStatus.WORKFLOW_VERIFIED,
            test_date="2026-10-01",
        )
    )
    cat.add(
        CapabilityRow(
            app_id="p",
            version="1",
            workflow="w",
            published_status=PublishedStatus.PARTIAL_WORKFLOW,
            test_date="2026-10-01",
        )
    )
    cat.add(
        CapabilityRow(
            app_id="n",
            version="1",
            workflow="w",
            published_status=PublishedStatus.NOT_INVENTORIED,
            test_date="",
        )
    )
    s = cat.summary()
    # Mỗi mức đếm RIÊNG: partial & not_inventoried KHÔNG được bơm vào 'workflow_verified'.
    assert s["available_to_download"] == 1
    assert s["launches"] == 1
    assert s["workflow_verified"] == 1
    assert s["other"] == 2
    assert sum(s.values()) == len(cat.rows())
