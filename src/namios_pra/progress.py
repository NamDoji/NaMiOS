"""Theo dõi kết quả TRUNG THỰC (PRA-032).

Ngôn ngữ UI phân biệt rõ các mốc: "đã gửi hàng đợi in" ≠ "máy báo in xong" ≠
"người dùng xác nhận nhận bản in"; "đã ký" ≠ "đã nộp" ≠ "cổng đã trả biên nhận".
Trong mọi trường hợp mất kết nối/mơ hồ, KHÔNG báo hoàn thành chỉ vì bấm nút.
"""

from __future__ import annotations

from namios_i18n import Lang, t
from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra._types import PrintStage, SignSubmitStage

__all__ = [
    "print_stage_from_cups",
    "print_label",
    "print_received",
    "sign_label",
    "sign_submitted_done",
]

#: Ánh xạ trạng thái CUPS thô → PrintStage TRUNG THỰC. CUPS "completed" = máy xử
#: lý xong job, KHÔNG phải người dùng đã cầm bản in → MACHINE_DONE (không hơn).
_CUPS_MAP: dict[str, PrintStage] = {
    "queued": PrintStage.QUEUED,
    "pending": PrintStage.QUEUED,
    "held": PrintStage.QUEUED,
    "processing": PrintStage.PRINTING,
    "printing": PrintStage.PRINTING,
    "completed": PrintStage.MACHINE_DONE,
    "canceled": PrintStage.CANCELLED,
    "cancelled": PrintStage.CANCELLED,
    "aborted": PrintStage.FAILED,
    "stopped": PrintStage.FAILED,
}

_PRINT_KEY: dict[PrintStage, str] = {
    PrintStage.QUEUED: "pra.print.queued",
    PrintStage.PRINTING: "pra.print.printing",
    PrintStage.MACHINE_DONE: "pra.print.machine_done",
    PrintStage.USER_CONFIRMED: "pra.print.user_confirmed",
    PrintStage.FAILED: "pra.print.failed",
    PrintStage.CANCELLED: "pra.print.cancelled",
    PrintStage.UNKNOWN: "pra.print.unknown",
}

_SIGN_KEY: dict[SignSubmitStage, str] = {
    SignSubmitStage.PREPARED: "pra.sign.prepared",
    SignSubmitStage.SIGNED: "pra.sign.signed",
    SignSubmitStage.SUBMITTED: "pra.sign.submitted",
    SignSubmitStage.RECEIPT_VERIFIED: "pra.sign.receipt",
    SignSubmitStage.FAILED: "pra.sign.failed",
    SignSubmitStage.UNKNOWN: "pra.sign.unknown",
}


def print_stage_from_cups(cups_status: str) -> PrintStage:
    """Map trạng thái CUPS thô → PrintStage. Không khớp → ``UNKNOWN`` (cần tra
    cứu), KHÔNG mặc định 'xong'."""

    return _CUPS_MAP.get((cups_status or "").strip().lower(), PrintStage.UNKNOWN)


def print_label(stage: PrintStage) -> str:
    return t(_PRINT_KEY[stage], lang=Lang.VI)


def print_received(stage: PrintStage) -> bool:
    """CHỈ ``USER_CONFIRMED`` mới là "đã nhận bản in" — MACHINE_DONE/queued đều
    KHÔNG phải (PRA-032)."""

    return stage == PrintStage.USER_CONFIRMED


def sign_label(stage: SignSubmitStage) -> str:
    return t(_SIGN_KEY[stage], lang=Lang.VI)


def sign_submitted_done(stage: SignSubmitStage) -> bool:
    """CHỈ ``RECEIPT_VERIFIED`` mới là "nộp xong có biên nhận" — signed/submitted
    chưa phải (PRA-032/SAI-022)."""

    return stage == SignSubmitStage.RECEIPT_VERIFIED
