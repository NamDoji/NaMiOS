"""NaMi Update Center — bảng trạng thái một nơi (APP11-013/019/020/032) + lịch
cài không phá việc đang làm (APP11-015).

Bất biến fail-closed:
  - ``WEB_SHORTCUT`` KHÔNG BAO GIỜ có ``installed_version``/``available_version``
    bịa ra — ``build_update_status`` XÓA mọi giá trị caller cố truyền cho kênh
    này, dù caller có vô tình hay cố ý truyền gì (APP11-013/019 nghiệm thu).
  - Chữ ký scanner quá hạn → badge ``WARNING`` NGAY CẢ KHI lần quét cuối "sạch"
    (APP11-011/020, E11-04) — hai tín hiệu (tuổi chữ ký, kết quả quét) được xét
    ĐỘC LẬP, không lấy cái này che cái kia.
  - Dịch vụ web hỏng → badge ``SERVICE_INCIDENT_OR_COMPAT`` với câu chữ "sự cố
    dịch vụ hoặc tương thích" — KHÔNG BAO GIỜ "NaMiOS chưa cập nhật" (APP11-019,
    E11-03).
  - ``schedule_update`` KHÔNG BAO GIỜ trả ``INSTALL_NOW`` khi có ngữ cảnh bận
    (tiết học/cuộc họp/ký hóa đơn) — kể cả bản vá khẩn (APP11-015, E11-08);
    bản khẩn quá hạn vẫn phải được NHẮC rõ, không âm thầm hoãn vô thời hạn.
  - ``recovery_guidance``: web service không rollback được ở phía NaMiOS — chỉ
    OS/app native mới có đường quay version (APP11-032).
"""

from __future__ import annotations

from namios_e08 import InstallResult
from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._types import (
    ScheduleAction,
    ScheduleDecision,
    UpdateChannel,
    UpdateStatus,
    UpdateStatusBadge,
    Urgency,
)
from namios_i18n import Lang, t

__all__ = [
    "build_update_status",
    "scanner_badge",
    "evaluate_web_shortcut",
    "schedule_update",
    "recovery_guidance",
]


def build_update_status(
    channel: UpdateChannel,
    *,
    installed_version: str | None = None,
    available_version: str | None = None,
    last_checked: str = "",
    urgency: Urgency = Urgency.ROUTINE,
) -> UpdateStatus:
    """Dựng một dòng bảng Update Center (APP11-013). ``WEB_SHORTCUT`` luôn bị
    ép ``installed_version=None``/``available_version=None`` bất kể caller
    truyền gì — dịch vụ web KHÔNG có "phiên bản cài trên máy" để báo cáo."""

    if channel is UpdateChannel.WEB_SHORTCUT:
        return UpdateStatus(
            channel=channel,
            installed_version=None,
            available_version=None,
            last_checked=last_checked,
            urgency=urgency,
            badge=UpdateStatusBadge.VENDOR_MANAGED,
            message_vi=t("essentials.update.vendor_managed", lang=Lang.VI),
        )

    badge = UpdateStatusBadge.UP_TO_DATE
    message = t("essentials.update.up_to_date", lang=Lang.VI)
    if available_version and available_version != installed_version:
        badge = UpdateStatusBadge.UPDATE_AVAILABLE
        message = t(
            "essentials.update.available",
            lang=Lang.VI,
            installed=installed_version or "?",
            available=available_version,
        )

    return UpdateStatus(
        channel=channel,
        installed_version=installed_version,
        available_version=available_version,
        last_checked=last_checked,
        urgency=urgency,
        badge=badge,
        message_vi=message,
    )


def scanner_badge(
    *,
    signature_age_days: int,
    max_age_days: int,
    last_scan_clean: bool,
    last_scan_at: str,
) -> UpdateStatus:
    """Chữ ký malware có vòng đời RIÊNG khỏi kết quả quét (APP11-011/020,
    E11-04). Chữ ký quá hạn (``signature_age_days > max_age_days``) → badge
    ``WARNING`` DÙ lần quét cuối "sạch" — không bao giờ nói "bảo vệ đầy đủ"
    khi dữ liệu nhận diện đã cũ. Ngày quét cuối LUÔN hiển thị, kể cả offline
    lâu ngày (không giấu/không coi là lỗi im lặng)."""

    expired = signature_age_days > max_age_days
    if expired:
        badge = UpdateStatusBadge.WARNING
        message = t(
            "essentials.scanner.signature_expired",
            lang=Lang.VI,
            last_scan_at=last_scan_at or "?",
            age=str(signature_age_days),
        )
    elif last_scan_clean:
        badge = UpdateStatusBadge.UP_TO_DATE
        message = t("essentials.scanner.clean_current", lang=Lang.VI, last_scan_at=last_scan_at)
    else:
        badge = UpdateStatusBadge.WARNING
        message = t("essentials.scanner.found_issue", lang=Lang.VI, last_scan_at=last_scan_at)

    return UpdateStatus(
        channel=UpdateChannel.SECURITY,
        last_checked=last_scan_at,
        urgency=Urgency.CRITICAL if expired else Urgency.ROUTINE,
        badge=badge,
        message_vi=message,
    )


def evaluate_web_shortcut(
    *,
    reachable: bool,
    smoke_test_passed: bool,
    browser_just_updated: bool = False,
) -> UpdateStatus:
    """Trạng thái một dịch vụ web (APP11-019, E11-03). Hỏng (không vào được
    HOẶC smoke test fail) → ``SERVICE_INCIDENT_OR_COMPAT`` với câu chữ "sự cố
    dịch vụ hoặc tương thích" — KHÔNG BAO GIỜ đổ lỗi "NaMiOS chưa cập nhật".
    ``browser_just_updated=True`` cùng lúc fail → ``retest_required=True``
    (badge kiểm thử hết hiệu lực, cần chạy lại smoke test/regression)."""

    if not reachable or not smoke_test_passed:
        return UpdateStatus(
            channel=UpdateChannel.WEB_SHORTCUT,
            badge=UpdateStatusBadge.SERVICE_INCIDENT_OR_COMPAT,
            retest_required=browser_just_updated,
            message_vi=t("essentials.update.service_incident", lang=Lang.VI),
        )
    return UpdateStatus(
        channel=UpdateChannel.WEB_SHORTCUT,
        badge=UpdateStatusBadge.VENDOR_MANAGED,
        message_vi=t("essentials.update.vendor_managed", lang=Lang.VI),
    )


def schedule_update(
    *,
    urgency: Urgency,
    busy_context: bool,
    deadline_days_left: int | None = None,
) -> ScheduleDecision:
    """Quyết định lịch cài (APP11-015, E11-08). ``busy_context=True`` (đang
    dạy/họp/ký hóa đơn) → KHÔNG BAO GIỜ ``INSTALL_NOW`` (không tự reboot giữa
    việc đang làm), kể cả ``urgency=CRITICAL``. Bản khẩn quá hạn
    (``deadline_days_left < 0``) luôn được NHẮC rõ (``REMIND_OVERDUE``), không
    âm thầm hoãn vô thời hạn."""

    overdue = deadline_days_left is not None and deadline_days_left < 0

    if overdue:
        return ScheduleDecision(
            action=ScheduleAction.REMIND_OVERDUE,
            overdue=True,
            reason_vi=t("essentials.schedule.overdue", lang=Lang.VI),
        )

    if busy_context:
        return ScheduleDecision(
            action=ScheduleAction.INSTALL_TONIGHT,
            overdue=False,
            reason_vi=t("essentials.schedule.busy_defer_tonight", lang=Lang.VI),
        )

    if urgency is Urgency.CRITICAL:
        return ScheduleDecision(
            action=ScheduleAction.INSTALL_NOW,
            overdue=False,
            reason_vi=t("essentials.schedule.critical_now", lang=Lang.VI),
        )

    return ScheduleDecision(
        action=ScheduleAction.DEFER,
        overdue=False,
        reason_vi=t("essentials.schedule.routine_defer", lang=Lang.VI),
    )


def recovery_guidance(channel: UpdateChannel, result: InstallResult | None = None) -> str:
    """Hướng khôi phục khi cập nhật hỏng (APP11-032). ``WEB_SHORTCUT`` KHÔNG
    thể rollback server phía NaMiOS — chỉ hướng người dùng mở trang chính
    thức/trình duyệt khác hoặc báo vendor; OS/app native có rollback thật qua
    ``install_txn``."""

    if channel is UpdateChannel.WEB_SHORTCUT:
        return t("essentials.recovery.web_not_rollbackable", lang=Lang.VI)
    if result is None:
        return t("essentials.recovery.no_attempt", lang=Lang.VI)
    if result.rolled_back:
        return t("essentials.recovery.rolled_back", lang=Lang.VI)
    if result.committed:
        return t("essentials.recovery.ok", lang=Lang.VI)
    return t("essentials.recovery.failed_untouched", lang=Lang.VI)
