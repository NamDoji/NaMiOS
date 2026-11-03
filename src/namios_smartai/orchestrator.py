"""Orchestrator SmartAI M0 (SAI-003/038/002).

Chạy một ``Task`` qua các bước plan một cách TẤT ĐỊNH:
  policy gate (SAI-039) → tool broker (SAI-040) → cập nhật trạng thái TỪ
  ``ToolResult`` (SAI-003, không từ văn bản AI). Dừng ở bước đầu tiên bị
  deny/não-success; không bao giờ tự nhảy tới ``completed`` khi tool chưa
  ``success``. Trạng thái bền + serialize được để checkpoint/resume (SAI-038).

Model ngôn ngữ CHỈ xuất hiện ở bước hiểu ý định (``intent``) — orchestrator
này không gọi model, mọi quyết định là mã tất định.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import (
    CapabilityToken,
    ConsentRecord,
    PlanStep,
    PolicyContext,
    PolicyEffect,
    PolicyRule,
    Task,
    TaskStatus,
    ToolCall,
)
from namios_smartai.injection import guard_untrusted
from namios_smartai.policy import DEFAULT_RULES, evaluate
from namios_smartai.state_machine import apply_tool_result, is_terminal
from namios_smartai.tools import ToolRegistry

__all__ = ["run_plan", "task_to_dict", "task_from_dict"]

#: Hành động giao dịch THẬT (R4) — M0 KHÔNG thực thi/mock (SAI-022: không bịa
#: biên nhận). Cần cổng/sandbox thật (M3). Dù policy cho phép (đã xác nhận giao
#: dịch), orchestrator vẫn dừng trung thực ở đây thay vì gọi tool giả.
_EXTERNAL_TRANSACTION_TOOLS: frozenset[str] = frozenset(
    {"submit_filing", "submit", "sign", "pay", "issue_invoice"}
)

#: Ánh xạ tool → pha task mục tiêu khi bước thành công (SAI-003).
_PHASE: dict[str, TaskStatus] = {
    "inspect_app": TaskStatus.PREFLIGHTING,
    "check_source": TaskStatus.PREFLIGHTING,
    "preflight": TaskStatus.PREFLIGHTING,
    "open_official_url": TaskStatus.PREFLIGHTING,
    "request_vendor_help": TaskStatus.PREFLIGHTING,
    "run_test": TaskStatus.TESTING,
    "compare_artifacts": TaskStatus.VERIFYING,
    "capture_sanitized_log": TaskStatus.TESTING,
    "create_capsule": TaskStatus.APPLYING,
    "install_test": TaskStatus.APPLYING,
    "submit": TaskStatus.APPLYING,
    "rollback": TaskStatus.ROLLED_BACK,
}


def run_plan(
    task: Task,
    registry: ToolRegistry,
    *,
    consent: ConsentRecord | None = None,
    capability: CapabilityToken | None = None,
    rules: Sequence[PolicyRule] = DEFAULT_RULES,
    now: str | None = None,
    untrusted_inputs: Sequence[str] = (),
) -> Task:
    """Chạy plan của ``task`` tất định. Trả ``Task`` mới (frozen) với trạng
    thái/được cập nhật từ kết quả tool + bước đã chạy.

    Nếu ``task`` đang chờ input (``AWAITING_INPUT``) → không chạy gì (cần người
    dùng bổ sung). Dữ liệu không tin cậy (``untrusted_inputs``) được quét
    injection TRƯỚC (SAI-019); dính → block, KHÔNG thực thi."""

    # Không tự chạy lại task đang chờ input, đã chốt (terminal) hoặc đang bị
    # chặn — resume phải qua đường rõ ràng (bổ sung input / reset / consent).
    # Tránh "chạy lại BLOCKED → PARTIAL" gây hiểu nhầm (QA SAI nêu).
    if (
        task.status == TaskStatus.AWAITING_INPUT
        or is_terminal(task.status)
        or (task.status == TaskStatus.BLOCKED)
    ):
        return task

    for probe in untrusted_inputs:
        blocked = guard_untrusted(probe)
        if blocked is not None:
            return replace(
                task,
                status=TaskStatus.BLOCKED,
                blockers=(*task.blockers, blocked.message_vi),
                next_action=None,
            )

    target = task.app_id or ""
    new_steps: list[PlanStep] = []
    evidence: list[str] = list(task.evidence_ids)
    blockers: list[str] = list(task.blockers)
    stopped = False
    final_status: TaskStatus = task.status

    for step in task.steps:
        if stopped:
            new_steps.append(step)
            continue

        decision = evaluate(
            PolicyContext(
                action=step.tool,
                risk=step.risk,
                target=target,
                capability=capability,
                consent=consent,
                workflow_stage=final_status.value,
                now=now,
            ),
            rules,
        )
        if decision.effect == PolicyEffect.DENY:
            # Deny do thiếu consent → AWAITING_CONSENT; deny khác → BLOCKED.
            if step.consent_required and consent is None:
                final_status = TaskStatus.AWAITING_CONSENT
            else:
                final_status = TaskStatus.BLOCKED
            blockers.append(decision.reason_vi)
            new_steps.append(replace(step, status=final_status))
            stopped = True
            continue

        # Giao dịch thật R4: policy đã cho phép (có xác nhận giao dịch) nhưng
        # M0 TUYỆT ĐỐI không thực thi/mock — dừng trung thực (SAI-022).
        if step.tool in _EXTERNAL_TRANSACTION_TOOLS:
            final_status = TaskStatus.BLOCKED
            blockers.append(t("sai.orchestrator.external_transaction", lang=Lang.VI))
            new_steps.append(replace(step, status=TaskStatus.BLOCKED))
            stopped = True
            continue

        on_success = _PHASE.get(step.tool, TaskStatus.TESTING)
        # M0 là harness MOCK: tự điền tham số-bắt-buộc bằng placeholder tất định
        # để chạy được luồng; M1 sẽ nối OUTPUT THẬT của bước trước vào input
        # bước sau (vd source_hash từ check_source). Không ảnh hưởng fail-closed
        # ở tầng registry (test gọi invoke trực tiếp vẫn chặn khi thiếu param).
        spec = registry.get(step.tool)
        params: dict[str, Any] = {}
        if spec is not None:
            for required in spec.required_params:
                params[required] = f"mock:{required}"
        result = registry.invoke(
            ToolCall(tool=step.tool, params=params, target=target, risk=step.risk),
            capability=capability,
            now=now,
        )
        next_status = apply_tool_result(final_status, on_success, result)
        if result.evidence_id:
            evidence.append(result.evidence_id)
        new_steps.append(replace(step, status=next_status))
        final_status = next_status
        if next_status in (TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.PARTIAL):
            blockers.append(result.message_vi)
            stopped = True

    # Nếu chạy hết mà bước cuối ở VERIFYING và không có lỗi → hoàn tất.
    if not stopped and final_status == TaskStatus.VERIFYING:
        final_status = TaskStatus.COMPLETED

    return replace(
        task,
        status=final_status,
        steps=tuple(new_steps),
        evidence_ids=tuple(evidence),
        blockers=tuple(blockers),
    )


def task_to_dict(task: Task) -> dict[str, Any]:
    """Serialize ``Task`` → dict JSON-able (SAI-038 durable state)."""

    return {
        "task_id": task.task_id,
        "intent": task.intent,
        "status": task.status.value,
        "workflow_id": task.workflow_id,
        "app_id": task.app_id,
        "app_version": task.app_version,
        "steps": [
            {
                "step_id": s.step_id,
                "tool": s.tool,
                "risk": s.risk.value,
                "expected_vi": s.expected_vi,
                "status": s.status.value,
                "consent_required": s.consent_required,
            }
            for s in task.steps
        ],
        "evidence_ids": list(task.evidence_ids),
        "route_mode": task.route_mode,
        "blockers": list(task.blockers),
        "next_action": task.next_action,
    }


def task_from_dict(data: dict[str, Any]) -> Task:
    """Khôi phục ``Task`` từ dict (SAI-038 resume)."""

    from namios_smartai._types import RiskTier

    steps = tuple(
        PlanStep(
            step_id=str(s["step_id"]),
            tool=str(s["tool"]),
            risk=RiskTier(s["risk"]),
            expected_vi=str(s.get("expected_vi", "")),
            status=TaskStatus(s.get("status", "proposed")),
            consent_required=bool(s.get("consent_required", False)),
        )
        for s in data.get("steps", [])
    )
    return Task(
        task_id=str(data["task_id"]),
        intent=str(data.get("intent", "")),
        status=TaskStatus(data.get("status", "proposed")),
        workflow_id=data.get("workflow_id"),
        app_id=data.get("app_id"),
        app_version=data.get("app_version"),
        steps=steps,
        evidence_ids=tuple(data.get("evidence_ids", [])),
        route_mode=data.get("route_mode"),
        blockers=tuple(data.get("blockers", [])),
        next_action=data.get("next_action"),
    )
