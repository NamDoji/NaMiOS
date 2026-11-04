"""SAI-022 — Submission Idempotency: mất mạng → cần tra cứu, không tự gửi lại."""

from __future__ import annotations

from namios_smartai._types import SubmissionStatus as SS
from namios_smartai.idempotency import (
    begin_submission,
    confirm,
    is_complete,
    mark_ambiguous,
    should_auto_resend,
)


def test_network_loss_needs_lookup_no_resend() -> None:
    rec = begin_submission("corr-1", "vn.tax.sample_submission")
    amb = mark_ambiguous(rec)
    assert amb.status == SS.NEEDS_LOOKUP
    assert should_auto_resend(amb) is False  # KHÔNG tự gửi lại
    assert is_complete(amb) is False
    assert amb.note_vi  # "cần tra cứu"


def test_never_auto_resend_any_state() -> None:
    rec = begin_submission("c", "w")
    assert should_auto_resend(rec) is False
    assert should_auto_resend(mark_ambiguous(rec)) is False


def test_confirm_requires_receipt() -> None:
    rec = begin_submission("c", "w")
    assert confirm(rec, "").status != SS.CONFIRMED  # thiếu biên nhận → chưa xong
    done = confirm(rec, "RECEIPT-123")
    assert done.status == SS.CONFIRMED and is_complete(done)


def test_pending_is_not_complete() -> None:
    assert is_complete(begin_submission("c", "w")) is False
