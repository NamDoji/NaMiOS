"""Test ``namios_smartai.planner`` (SAI-002, Phụ lục 04).

Nghiệm thu chính: khi ``unknowns`` còn phần tử, kế hoạch KHÔNG có bước nào
bậc R2/R3/R4 (không tự cài/áp dụng); ``install_app``/``submit_filing`` đủ
thông tin thì có bước nguy hiểm đúng bậc + ``consent_required=True``;
``build_task`` không bao giờ tự đặt trạng thái như đã xong/đang áp dụng.
"""

from __future__ import annotations

from namios_smartai._types import IntentResult, RiskTier, Task, TaskStatus
from namios_smartai.planner import build_task

_RISK_ORDER: dict[RiskTier, int] = {
    RiskTier.R0: 0,
    RiskTier.R1: 1,
    RiskTier.R2: 2,
    RiskTier.R3: 3,
    RiskTier.R4: 4,
}


def _max_risk(task: Task) -> int:
    if not task.steps:
        return -1
    return max(_RISK_ORDER[step.risk] for step in task.steps)


def test_unknowns_con_thi_awaiting_input_va_khong_co_buoc_nguy_hiem() -> None:
    intent = IntentResult(
        intent="install_app",
        target_app="misa",
        unknowns=("version", "license"),
        confidence=0.6,
    )

    task = build_task(intent, task_id="t1")

    assert task.status == TaskStatus.AWAITING_INPUT
    assert _max_risk(task) <= _RISK_ORDER[RiskTier.R1]
    assert all(step.risk not in (RiskTier.R2, RiskTier.R3, RiskTier.R4) for step in task.steps)
    assert task.next_action is not None and task.next_action != ""


def test_unknowns_con_khong_co_buoc_cai_hay_ap_dung_du_intent_la_gi() -> None:
    for intent_name in ("install_app", "submit_filing", "open_app", "print_document", "unknown"):
        intent = IntentResult(intent=intent_name, unknowns=("version",))
        task = build_task(intent, task_id="t-unknowns")

        assert task.status == TaskStatus.AWAITING_INPUT
        assert all(step.tool != "install_test" for step in task.steps)
        assert all(step.tool != "submit_filing" for step in task.steps)


def test_install_app_du_thong_tin_co_capsule_va_install_test_r2_consent() -> None:
    intent = IntentResult(
        intent="install_app",
        target_app="misa",
        required_outcome="cài MISA bản 2024 đã có license",
        unknowns=(),
        confidence=0.9,
    )

    task = build_task(intent, task_id="t2")

    assert task.status == TaskStatus.PROPOSED
    by_tool = {step.tool: step for step in task.steps}
    assert by_tool["create_capsule"].risk == RiskTier.R2
    assert by_tool["create_capsule"].consent_required is True
    assert by_tool["install_test"].risk == RiskTier.R2
    assert by_tool["install_test"].consent_required is True


def test_submit_filing_du_thong_tin_co_buoc_r4_consent_va_khong_tu_hoan_thanh() -> None:
    intent = IntentResult(
        intent="submit_filing",
        required_outcome="nộp tờ khai thuế GTGT cho công ty X, số tiền 5.000.000đ",
        unknowns=(),
        confidence=0.9,
    )

    task = build_task(intent, task_id="t3")

    r4_steps = [step for step in task.steps if step.risk == RiskTier.R4]
    assert len(r4_steps) == 1
    assert r4_steps[0].consent_required is True
    assert task.status not in (TaskStatus.COMPLETED, TaskStatus.APPLYING)


def test_open_app_va_print_document_chi_r0_r1_khong_can_consent() -> None:
    for intent_name in ("open_app", "print_document"):
        intent = IntentResult(intent=intent_name, target_app="word", unknowns=(), confidence=0.9)
        task = build_task(intent, task_id=f"t-{intent_name}")

        assert task.status == TaskStatus.PROPOSED
        assert task.steps
        assert all(step.risk in (RiskTier.R0, RiskTier.R1) for step in task.steps)
        assert all(step.consent_required is False for step in task.steps)


def test_intent_unknown_la_awaiting_input_voi_buoc_giai_thich() -> None:
    intent = IntentResult(intent="unknown", unknowns=(), confidence=0.2)

    task = build_task(intent, task_id="t4")

    assert task.status == TaskStatus.AWAITING_INPUT
    assert len(task.steps) == 1
    assert task.steps[0].risk == RiskTier.R0
    assert task.steps[0].consent_required is False


def test_moi_plan_step_co_expected_vi_khong_rong_va_r2_tro_len_co_consent() -> None:
    cases = (
        IntentResult(intent="install_app", target_app="misa", unknowns=(), confidence=0.9),
        IntentResult(intent="submit_filing", unknowns=(), confidence=0.9),
        IntentResult(intent="open_app", target_app="zalo", unknowns=(), confidence=0.9),
        IntentResult(intent="print_document", target_app="word", unknowns=(), confidence=0.9),
        IntentResult(intent="unknown", unknowns=(), confidence=0.2),
        IntentResult(intent="install_app", unknowns=("version", "license"), confidence=0.6),
    )

    for index, intent in enumerate(cases):
        task = build_task(intent, task_id=f"t-expected-{index}")
        assert task.steps, "mọi task phải có ít nhất một bước"
        for step in task.steps:
            assert step.expected_vi.strip() != ""
            if _RISK_ORDER[step.risk] >= _RISK_ORDER[RiskTier.R2]:
                assert step.consent_required is True


def test_build_task_khong_tu_thuc_thi_giu_app_id_tu_intent() -> None:
    intent = IntentResult(intent="open_app", target_app="zalo", unknowns=(), confidence=0.9)

    task = build_task(intent, task_id="t5")

    assert task.app_id == "zalo"
    assert task.intent == "open_app"
    assert task.task_id == "t5"
    # build_task không tự tạo bằng chứng/consent — đó là việc của orchestrator.
    assert task.evidence_ids == ()
    assert task.consent is None
