"""APP11-013/015/019/020/032 — NaMi Update Center. Bám E11-03 (browser cập
nhật, Zalo QR đổi), E11-04 (signature scanner quá hạn), E11-08 (đang dạy
online, có update OS)."""

from __future__ import annotations

from namios_e08 import InstallResult, InstallStage
from namios_essentials import (
    ScheduleAction,
    UpdateChannel,
    UpdateStatusBadge,
    Urgency,
    build_update_status,
    evaluate_web_shortcut,
    recovery_guidance,
    scanner_badge,
    schedule_update,
)

UC = UpdateChannel
USB = UpdateStatusBadge


# --------------------------------------------------------------------------- #
# APP11-013/019 — web_shortcut KHÔNG bịa version cài trên máy                   #
# --------------------------------------------------------------------------- #


def test_web_shortcut_never_fabricates_installed_version() -> None:
    # Dù caller cố truyền version, kênh web_shortcut PHẢI bỏ qua (fail-closed).
    status = build_update_status(
        UC.WEB_SHORTCUT, installed_version="99.9", available_version="100.0"
    )
    assert status.installed_version is None
    assert status.available_version is None
    assert status.badge is USB.VENDOR_MANAGED
    assert "nhà cung cấp" in status.message_vi.lower() or "vendor" in status.message_vi.lower()


def test_installable_channel_reports_real_versions() -> None:
    status = build_update_status(UC.BROWSER, installed_version="120", available_version="121")
    assert status.installed_version == "120"
    assert status.available_version == "121"
    assert status.badge is USB.UPDATE_AVAILABLE


def test_installable_channel_up_to_date_when_no_newer_version() -> None:
    status = build_update_status(UC.OFFICE, installed_version="1.0", available_version="1.0")
    assert status.badge is USB.UP_TO_DATE


# --------------------------------------------------------------------------- #
# E11-04 — signature scanner quá hạn                                            #
# --------------------------------------------------------------------------- #


def test_e11_04_expired_signature_warns_even_if_last_scan_clean() -> None:
    status = scanner_badge(
        signature_age_days=10,
        max_age_days=3,
        last_scan_clean=True,
        last_scan_at="2026-10-28",
    )
    assert status.badge is USB.WARNING
    assert "2026-10-28" in status.message_vi
    assert "10" in status.message_vi  # tuổi chữ ký hiển thị rõ


def test_fresh_signature_and_clean_scan_is_up_to_date() -> None:
    status = scanner_badge(
        signature_age_days=1, max_age_days=3, last_scan_clean=True, last_scan_at="2026-11-06"
    )
    assert status.badge is USB.UP_TO_DATE


def test_fresh_signature_but_dirty_scan_warns() -> None:
    status = scanner_badge(
        signature_age_days=1, max_age_days=3, last_scan_clean=False, last_scan_at="2026-11-06"
    )
    assert status.badge is USB.WARNING


def test_offline_seven_days_still_shows_last_checked_date() -> None:
    # APP11-020 nghiệm thu: "offline 7 ngày hiện thời gian cập nhật cuối, vẫn
    # quét bằng dữ liệu sẵn có nhưng không báo bảo vệ đầy đủ."
    status = scanner_badge(
        signature_age_days=7, max_age_days=3, last_scan_clean=True, last_scan_at="2026-10-31"
    )
    assert status.last_checked == "2026-10-31"
    assert status.badge is USB.WARNING  # KHÔNG "bảo vệ đầy đủ"


# --------------------------------------------------------------------------- #
# E11-03 — browser cập nhật, Zalo QR đổi                                       #
# --------------------------------------------------------------------------- #


def test_e11_03_broken_web_service_is_service_incident_not_namios_outdated() -> None:
    status = evaluate_web_shortcut(
        reachable=True, smoke_test_passed=False, browser_just_updated=True
    )
    assert status.badge is USB.SERVICE_INCIDENT_OR_COMPAT
    assert status.retest_required is True
    lowered = status.message_vi.lower()
    assert "sự cố dịch vụ" in lowered or "tương thích" in lowered
    # APP11-019: PHẢI nói rõ đây KHÔNG phải lỗi "NaMiOS chưa cập nhật" — câu
    # phải mang nghĩa PHỦ ĐỊNH đó, không phải im lặng bỏ qua khả năng hiểu lầm.
    assert "không phải do namios chưa cập nhật" in lowered


def test_unreachable_web_service_is_also_service_incident() -> None:
    status = evaluate_web_shortcut(reachable=False, smoke_test_passed=True)
    assert status.badge is USB.SERVICE_INCIDENT_OR_COMPAT


def test_healthy_web_service_is_vendor_managed() -> None:
    status = evaluate_web_shortcut(reachable=True, smoke_test_passed=True)
    assert status.badge is USB.VENDOR_MANAGED
    assert status.retest_required is False


# --------------------------------------------------------------------------- #
# E11-08 — đang dạy online, có update OS                                       #
# --------------------------------------------------------------------------- #


def test_e11_08_busy_context_never_installs_now_even_if_critical() -> None:
    decision = schedule_update(urgency=Urgency.CRITICAL, busy_context=True)
    assert decision.action is not ScheduleAction.INSTALL_NOW
    assert decision.action is ScheduleAction.INSTALL_TONIGHT


def test_busy_context_routine_update_also_defers_to_tonight() -> None:
    decision = schedule_update(urgency=Urgency.ROUTINE, busy_context=True)
    assert decision.action is ScheduleAction.INSTALL_TONIGHT


def test_critical_update_with_no_busy_context_may_install_now() -> None:
    decision = schedule_update(urgency=Urgency.CRITICAL, busy_context=False)
    assert decision.action is ScheduleAction.INSTALL_NOW


def test_overdue_patch_always_reminds_even_if_busy() -> None:
    decision = schedule_update(urgency=Urgency.CRITICAL, busy_context=True, deadline_days_left=-2)
    assert decision.action is ScheduleAction.REMIND_OVERDUE
    assert decision.overdue is True


def test_routine_update_not_busy_defers() -> None:
    decision = schedule_update(urgency=Urgency.ROUTINE, busy_context=False)
    assert decision.action is ScheduleAction.DEFER


# --------------------------------------------------------------------------- #
# APP11-032 — khôi phục khi cập nhật hỏng                                      #
# --------------------------------------------------------------------------- #


def test_web_shortcut_recovery_points_to_vendor_not_rollback() -> None:
    msg = recovery_guidance(UC.WEB_SHORTCUT).lower()
    assert "không rollback" in msg
    assert "vendor" in msg or "trình duyệt" in msg or "trang chính thức" in msg


def test_office_rollback_recovery_message() -> None:
    rolled_back = InstallResult(
        committed=False, rolled_back=True, final_stage=InstallStage.ROLLBACK
    )
    msg = recovery_guidance(UC.OFFICE, rolled_back)
    assert "rollback" in msg.lower() or "trước" in msg.lower()
