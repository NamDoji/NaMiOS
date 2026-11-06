"""Mục tiêu → kết quả, kết luận TRUNG THỰC (SYS-030).

Người dùng nói "in bảng lương" → xác định tài nguyên cần (app/tệp/máy in/trang/
người nhận/kết-quả-cần-chứng-minh); thiếu → HỎI lại. Workflow KHÔNG kết thúc ở
nút Print: chỉ coi là xong khi có bằng chứng (job status) + (nếu nghiệp vụ đòi)
người dùng xác nhận bản in. Máy in offline → ``partial/blocked``, KHÔNG "đã in xong".

TÁI DÙNG ``ActionStatus``/``RunState`` của ``namios_sys._types`` — không tạo
trạng thái song song.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from namios_i18n import Lang, t
from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_sys._types import ActionStatus, GoalPlan, RunState

__all__ = ["plan_goal", "goal_outcome"]


def plan_goal(
    intent: str,
    *,
    required: Sequence[str],
    provided: Mapping[str, str] | None = None,
) -> GoalPlan:
    """Lập kế hoạch: tài nguyên nào CẦN, cái nào đã có, cái nào THIẾU (phải hỏi).
    ``ready`` chỉ True khi không thiếu gì — SmartAI không tự đoán phần thiếu."""

    have = dict(provided or {})
    resolved = {r: have[r] for r in required if (have.get(r) or "").strip()}
    missing = tuple(r for r in required if not (have.get(r) or "").strip())
    return GoalPlan(
        intent=intent,
        required=tuple(required),
        resolved=resolved,
        missing=missing,
        ready=not missing,
    )


def goal_outcome(
    intent: str,
    step_results: Sequence[ActionStatus],
    *,
    evidence_ids: Sequence[str] = (),
    business_requires_confirm: bool = False,
    user_confirmed: bool = False,
) -> tuple[RunState, str]:
    """Kết luận TRUNG THỰC một mục tiêu từ kết quả các bước (SYS-030).

    Thứ tự an toàn (fail-honest):
    - chưa có bước nào → ``PROPOSED``.
    - có bước FAILED → ``FAILED``.
    - có bước BLOCKED (vd máy in offline) → ``BLOCKED`` (KHÔNG "đã xong").
    - có bước PARTIAL → ``PARTIAL``.
    - tất cả SUCCESS nhưng THIẾU bằng chứng non-blank → ``PARTIAL`` (mở ≠ hoàn thành).
    - tất cả SUCCESS + có bằng chứng, nghiệp vụ đòi xác nhận mà chưa xác nhận → ``PARTIAL``.
    - đủ cả → ``VERIFIED``.
    """

    results = tuple(step_results)
    if not results:
        return RunState.PROPOSED, t("sys.goal.need_info", lang=Lang.VI, intent=intent, missing="—")

    if any(r == ActionStatus.FAILED for r in results):
        return RunState.FAILED, t("sys.goal.failed", lang=Lang.VI, intent=intent)

    if any(r == ActionStatus.DENIED for r in results):
        # Bước bị CHẶN bởi chính sách/quyền = KHÔNG hoàn thành (tuyệt đối không verified).
        return RunState.BLOCKED, t(
            "sys.goal.blocked", lang=Lang.VI, intent=intent, reason="bị từ chối (chính sách/quyền)"
        )

    if any(r == ActionStatus.BLOCKED for r in results):
        return RunState.BLOCKED, t(
            "sys.goal.blocked", lang=Lang.VI, intent=intent, reason="thiết bị/bước chưa sẵn sàng"
        )

    if any(r == ActionStatus.PARTIAL for r in results):
        return RunState.PARTIAL, t(
            "sys.goal.blocked", lang=Lang.VI, intent=intent, reason="mới hoàn thành một phần"
        )

    # Fail-closed: chỉ đi tiếp khi MỌI bước đều SUCCESS. Bất kỳ trạng thái nào
    # khác (kể cả enum mới sau này) → PARTIAL, KHÔNG để lọt vào verified.
    if not all(r == ActionStatus.SUCCESS for r in results):
        return RunState.PARTIAL, t(
            "sys.goal.blocked", lang=Lang.VI, intent=intent, reason="có bước chưa thành công"
        )

    has_evidence = any((e or "").strip() for e in evidence_ids)
    if not has_evidence:
        return RunState.PARTIAL, t("sys.goal.partial_evidence", lang=Lang.VI, intent=intent)

    if business_requires_confirm and not user_confirmed:
        return RunState.PARTIAL, t("sys.goal.need_confirm", lang=Lang.VI, intent=intent)

    return RunState.VERIFIED, t("sys.goal.done", lang=Lang.VI, intent=intent)
