"""N10-009 — điểm sẵn sàng chuyển đổi.

Bất biến then chốt: "kế toán không ký được hóa đơn = blocked dù mở được
Word/Zalo" — một công việc THIẾT YẾU bị chặn kéo CẢ MÁY xuống ``blocked``,
bất kể bao nhiêu app khác đã ``ready``.
"""

from __future__ import annotations

from namios_mig import (
    AppReadinessInput,
    CertState,
    CompatRoute,
    ReadinessLevel,
    WorkflowTestStatus,
    compute_machine_readiness,
)

WS = WorkflowTestStatus
CR = CompatRoute
CS = CertState


def _published_pass(
    app_id: str, *, essential: bool, route: CompatRoute = CR.NATIVE
) -> AppReadinessInput:
    return AppReadinessInput(
        app_id=app_id,
        essential=essential,
        route=route,
        workflow_status=WS.PASSED,
        cert_state=CS.PUBLISHED,
    )


def test_no_essential_declared_is_unknown() -> None:
    apps = [_published_pass("word", essential=False), _published_pass("zalo", essential=False)]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.UNKNOWN


def test_one_blocked_essential_blocks_whole_machine() -> None:
    # Fixture nghiệm thu N10-009: Word/Zalo ready (90% app khác chạy) nhưng
    # MISA ký hóa đơn (essential) FAILED → cả máy BLOCKED.
    apps = [
        _published_pass("ms.word", essential=False),
        _published_pass("zalo.pc", essential=True),
        AppReadinessInput(
            app_id="misa.invoice.sign",
            essential=True,
            route=CR.WINE,
            workflow_status=WS.FAILED,
            cert_state=CS.PILOT_VERIFIED,
        ),
    ]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.BLOCKED
    assert result.blocking_apps == ("misa.invoice.sign",)


def test_unsupported_route_on_essential_blocks() -> None:
    apps = [AppReadinessInput("drv.app", essential=True, route=CR.UNSUPPORTED)]
    assert compute_machine_readiness(apps).level is ReadinessLevel.BLOCKED


def test_needs_retest_on_essential_blocks() -> None:
    apps = [
        AppReadinessInput(
            "a",
            essential=True,
            route=CR.NATIVE,
            workflow_status=WS.PASSED,
            cert_state=CS.NEEDS_RETEST,
        )
    ]
    assert compute_machine_readiness(apps).level is ReadinessLevel.BLOCKED


def test_device_not_ready_on_essential_blocks() -> None:
    apps = [
        AppReadinessInput(
            "printer.workflow",
            essential=True,
            route=CR.NATIVE,
            workflow_status=WS.PASSED,
            cert_state=CS.PUBLISHED,
            device_ready=False,
        )
    ]
    assert compute_machine_readiness(apps).level is ReadinessLevel.BLOCKED


def test_untested_essential_is_unknown_not_ready() -> None:
    apps = [
        _published_pass("zalo.pc", essential=True),
        AppReadinessInput("tax.etax", essential=True, route=CR.WEB),
    ]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.UNKNOWN
    assert result.blocking_apps == ("tax.etax",)


def test_pilot_only_when_essential_not_published() -> None:
    apps = [
        AppReadinessInput(
            "misa.sme",
            essential=True,
            route=CR.WINE,
            workflow_status=WS.PASSED,
            cert_state=CS.PILOT_VERIFIED,
        )
    ]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.PILOT_ONLY


def test_ready_with_limits_for_partial_or_wine_route() -> None:
    apps = [
        AppReadinessInput(
            "office.docx",
            essential=True,
            route=CR.WINE,
            workflow_status=WS.PASSED,
            cert_state=CS.PUBLISHED,
        )
    ]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.READY_WITH_LIMITS


def test_fully_ready_machine() -> None:
    apps = [
        _published_pass("ms.word", essential=True, route=CR.NATIVE),
        _published_pass("zalo.pc", essential=True, route=CR.WEB),
    ]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.READY
    assert result.blocking_apps == ()


def test_blocked_dominates_over_unknown_and_pilot_only() -> None:
    # Thứ tự ưu tiên fail-closed: BLOCKED > UNKNOWN > PILOT_ONLY.
    apps = [
        AppReadinessInput(
            "not_tested_app", essential=True, route=CR.WINE
        ),  # NOT_TESTED → unknown-ish
        AppReadinessInput(
            "pilot_app",
            essential=True,
            route=CR.WINE,
            workflow_status=WS.PASSED,
            cert_state=CS.PILOT_VERIFIED,
        ),
        AppReadinessInput("blocked_app", essential=True, route=CR.UNSUPPORTED),
    ]
    result = compute_machine_readiness(apps)
    assert result.level is ReadinessLevel.BLOCKED
