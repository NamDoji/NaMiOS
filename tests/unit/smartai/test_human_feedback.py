"""SAI-029 — Human Feedback: phản hồi ≠ chứng nhận, chỉ gợi ý test case."""

from __future__ import annotations

from namios_smartai._types import Feedback, FeedbackVerdict, ReporterRole
from namios_smartai.human_feedback import FeedbackLedger, can_certify_from_feedback


def _fb(
    fid: str,
    verdict: FeedbackVerdict,
    *,
    role: ReporterRole = ReporterRole.USER,
    desc: str = "",
    wf: str = "w1",
    ver: str = "2024",
) -> Feedback:
    return Feedback(
        feedback_id=fid,
        workflow_id=wf,
        app_version=ver,
        reporter="u",
        role=role,
        verdict=verdict,
        description_vi=desc,
    )


def test_single_success_does_not_verify() -> None:
    # Nghiệm thu SAI-029: một lượt "đã giải quyết" KHÔNG nâng workflow_verified.
    led = FeedbackLedger()
    led.submit(_fb("f1", FeedbackVerdict.RESOLVED, desc="in được rồi"))
    assert led.would_promote_to_workflow_verified("w1") is False


def test_many_success_still_not_verify() -> None:
    led = FeedbackLedger()
    for i in range(20):
        led.submit(_fb(f"f{i}", FeedbackVerdict.RESOLVED, role=ReporterRole.IT, desc="ok"))
    assert led.would_promote_to_workflow_verified("w1") is False
    assert can_certify_from_feedback(led.all()) is False


def test_can_certify_always_false() -> None:
    assert can_certify_from_feedback() is False
    assert can_certify_from_feedback([_fb("x", FeedbackVerdict.RESOLVED)]) is False


def test_unresolved_yields_repro_suggestion() -> None:
    led = FeedbackLedger()
    led.submit(_fb("f1", FeedbackVerdict.UNRESOLVED, desc="lệch tổng tiền 1000đ"))
    sugg = led.suggested_test_cases("w1")
    assert len(sugg) == 1
    assert sugg[0].kind == "repro"
    assert "lệch tổng tiền" in sugg[0].summary_vi
    assert sugg[0].origin_feedback_id == "f1"


def test_resolved_yields_regression_suggestion() -> None:
    led = FeedbackLedger()
    led.submit(_fb("f1", FeedbackVerdict.RESOLVED, desc="đã sửa lỗi font"))
    sugg = led.suggested_test_cases("w1")
    assert len(sugg) == 1 and sugg[0].kind == "regression"


def test_unclear_or_empty_desc_no_suggestion() -> None:
    led = FeedbackLedger()
    led.submit(_fb("f1", FeedbackVerdict.UNCLEAR, desc="không rõ"))
    led.submit(_fb("f2", FeedbackVerdict.UNRESOLVED, desc=""))  # không mô tả
    assert led.suggested_test_cases("w1") == ()


def test_roles_evaluated_separately() -> None:
    # Phản hồi 'đã giải quyết' của người dùng KHÔNG gộp/không thay IT & nghiệp vụ.
    led = FeedbackLedger()
    led.submit(_fb("f1", FeedbackVerdict.RESOLVED, role=ReporterRole.USER))
    led.submit(_fb("f2", FeedbackVerdict.UNRESOLVED, role=ReporterRole.IT))
    by_role = led.verdicts_by_role("w1")
    assert by_role[ReporterRole.USER] == (FeedbackVerdict.RESOLVED,)
    assert by_role[ReporterRole.IT] == (FeedbackVerdict.UNRESOLVED,)


def test_for_workflow_isolation() -> None:
    led = FeedbackLedger()
    led.submit(_fb("f1", FeedbackVerdict.RESOLVED, wf="w1", desc="a"))
    led.submit(_fb("f2", FeedbackVerdict.RESOLVED, wf="w2", desc="b"))
    assert len(led.for_workflow("w1")) == 1
    assert {s.workflow_id for s in led.suggested_test_cases("w2")} == {"w2"}
