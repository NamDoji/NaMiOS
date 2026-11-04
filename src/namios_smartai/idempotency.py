"""External Submission Idempotency (SAI-022).

Mỗi giao dịch gửi có correlation ID nội bộ. Nếu timeout hoặc phản hồi mơ hồ →
trạng thái ``needs_lookup`` ("cần tra cứu"), **KHÔNG tự gửi lại**. Chỉ coi
``confirmed`` khi có biên nhận/đầu ra ĐƯỢC KIỂM.

Nghiệm thu: mô phỏng mất mạng NGAY sau nút gửi → không tạo giao dịch thứ hai
(``should_auto_resend`` luôn ``False``; bản ghi chuyển ``needs_lookup``).
"""

from __future__ import annotations

from dataclasses import replace

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import SubmissionRecord, SubmissionStatus

__all__ = [
    "begin_submission",
    "mark_ambiguous",
    "confirm",
    "should_auto_resend",
    "is_complete",
]


def begin_submission(correlation_id: str, workflow_id: str) -> SubmissionRecord:
    """Mở một giao dịch gửi (trạng thái ``pending``)."""

    return SubmissionRecord(
        correlation_id=correlation_id,
        workflow_id=workflow_id,
        status=SubmissionStatus.PENDING,
    )


def mark_ambiguous(record: SubmissionRecord) -> SubmissionRecord:
    """Timeout/mơ hồ → ``needs_lookup`` (cần tra cứu), KHÔNG tự gửi lại."""

    return replace(
        record,
        status=SubmissionStatus.NEEDS_LOOKUP,
        note_vi=t("sai.submission.needs_lookup", lang=Lang.VI),
    )


def confirm(record: SubmissionRecord, receipt: str) -> SubmissionRecord:
    """Chỉ ``confirmed`` khi có biên nhận ĐƯỢC KIỂM (receipt không rỗng);
    thiếu receipt → giữ nguyên + ghi chú chưa hoàn thành."""

    if not (receipt or "").strip():
        return replace(record, note_vi=t("sai.submission.not_confirmed", lang=Lang.VI))
    return replace(record, status=SubmissionStatus.CONFIRMED, receipt=receipt, note_vi="")


def should_auto_resend(record: SubmissionRecord) -> bool:
    """LUÔN ``False`` — không bao giờ tự gửi lại (SAI-022). Người dùng phải tra
    cứu biên nhận rồi tự quyết."""

    return False


def is_complete(record: SubmissionRecord) -> bool:
    """Hoàn thành CHỈ khi ``confirmed`` + có biên nhận."""

    return record.status == SubmissionStatus.CONFIRMED and bool(record.receipt)
