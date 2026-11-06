"""PRA-032 — theo dõi kết quả trung thực: queued ≠ in xong ≠ đã nhận; ký ≠ nộp ≠ biên nhận."""

from __future__ import annotations

from namios_pra import (
    PrintStage,
    SignSubmitStage,
    print_label,
    print_received,
    print_stage_from_cups,
    sign_label,
    sign_submitted_done,
)

PS = PrintStage
SS = SignSubmitStage


def test_cups_completed_is_machine_done_not_received() -> None:
    # Nghiệm thu PRA-032: CUPS 'completed' = máy xử lý xong job, KHÔNG phải đã nhận.
    st = print_stage_from_cups("completed")
    assert st is PS.MACHINE_DONE
    assert print_received(st) is False
    assert "CHƯA xác nhận" in print_label(st)


def test_queued_is_waiting_not_printed() -> None:
    st = print_stage_from_cups("queued")
    assert st is PS.QUEUED
    assert "ĐANG CHỜ" in print_label(st)
    assert print_received(st) is False


def test_only_user_confirmed_is_received() -> None:
    assert print_received(PS.USER_CONFIRMED) is True
    for st in (PS.QUEUED, PS.PRINTING, PS.MACHINE_DONE, PS.FAILED, PS.UNKNOWN):
        assert print_received(st) is False


def test_unknown_cups_status_is_unknown() -> None:
    assert print_stage_from_cups("blah") is PS.UNKNOWN
    assert print_stage_from_cups("") is PS.UNKNOWN


def test_sign_stages_separated() -> None:
    # ký ≠ nộp ≠ biên nhận: chỉ RECEIPT_VERIFIED mới là "nộp xong".
    assert sign_submitted_done(SS.SIGNED) is False
    assert sign_submitted_done(SS.SUBMITTED) is False
    assert sign_submitted_done(SS.RECEIPT_VERIFIED) is True
    assert "CHƯA nộp" in sign_label(SS.SIGNED)
    assert "CHƯA có biên nhận" in sign_label(SS.SUBMITTED)
