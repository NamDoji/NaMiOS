"""Bounded Repair Search (SAI-010).

AI sinh giả thuyết; mỗi phép thử chạy trong BẢN SAO capsule (SAI-018) với ĐÚNG
MỘT thay đổi đo được + rollback. Có GIỚI HẠN (số phép thử/bước) và DỪNG CỨNG
khi: dữ liệu sai, thiếu license, lỗi bảo mật, cần vendor. Mọi ứng viên fail →
dừng nêu lý do, KHÔNG retry vô hạn (nghiệm thu SAI-010).

Bộ thực thi (``TrialExecutor``) được TIÊM vào — M2 dùng mock/mô phỏng tất định
(không cần Wine); sandbox Wine thật là cùng interface, mở khi có build host.
Kết quả phép thử là SỰ THẬT từ executor, KHÔNG từ lời AI.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import (
    Capsule,
    CompatibilityRecipe,
    RepairBudget,
    RepairOutcome,
    ToolResultStatus,
    Trial,
    TrialStopReason,
)
from namios_smartai.capsule import apply_change, make_capsule, rollback

__all__ = ["TrialExecutor", "bounded_repair", "HARD_STOPS"]

#: Lý do DỪNG CỨNG — không thử ứng viên tiếp (SAI-010).
HARD_STOPS: frozenset[TrialStopReason] = frozenset(
    {
        TrialStopReason.DATA_WRONG,
        TrialStopReason.MISSING_LICENSE,
        TrialStopReason.SECURITY,
        TrialStopReason.NEEDS_VENDOR,
    }
)


class TrialExecutor(Protocol):
    """Thực thi một giả thuyết trên capsule đã thay đổi → trả
    ``(outcome, measured_vi, hard_stop)``. ``hard_stop`` != NONE buộc dừng cứng."""

    def run(
        self, hypothesis: str, capsule: Capsule
    ) -> tuple[ToolResultStatus, str, TrialStopReason]: ...


def bounded_repair(
    base_id: str,
    candidates: Sequence[str],
    executor: TrialExecutor,
    *,
    budget: RepairBudget | None = None,
    recipe_factory: Callable[[str], CompatibilityRecipe] | None = None,
) -> RepairOutcome:
    """Chạy tìm-kiếm-sửa có giới hạn. Trả ``RepairOutcome`` với danh sách phép
    thử + lý do dừng; ``recipe_candidate`` chỉ khi một phép thử THÀNH CÔNG."""

    bud = budget or RepairBudget()
    trials: list[Trial] = []
    steps = 0

    for i, hypothesis in enumerate(candidates):
        if len(trials) >= bud.max_trials or steps >= bud.max_steps:
            return RepairOutcome(
                status=ToolResultStatus.BLOCKED,
                stop_reason=TrialStopReason.BUDGET_EXCEEDED,
                trials=tuple(trials),
                reason_vi=t("sai.repair.stop.budget_exceeded", lang=Lang.VI),
            )

        # Thử trên BẢN SAO: 1 thay đổi đo được, rồi LUÔN rollback (không đụng gốc).
        cap = make_capsule(base_id, capsule_id=f"cap-{i}", snapshot_id=f"snap-{i}")
        changed = apply_change(cap, hypothesis)
        outcome, measured, hard = executor.run(hypothesis, changed)
        rolled = rollback(changed)
        trials.append(
            Trial(
                trial_id=f"trial-{i}",
                hypothesis=hypothesis,
                precondition=cap.snapshot_id,
                change=hypothesis,
                expected="workflow hoàn thành đúng dữ liệu",
                measured=measured,
                outcome=outcome,
                rolled_back=rolled.rolled_back,
            )
        )
        steps += 1

        if hard in HARD_STOPS:
            return RepairOutcome(
                status=ToolResultStatus.BLOCKED,
                stop_reason=hard,
                trials=tuple(trials),
                reason_vi=t(f"sai.repair.stop.{hard.value}", lang=Lang.VI),
            )

        if outcome == ToolResultStatus.SUCCESS:
            candidate = recipe_factory(hypothesis) if recipe_factory is not None else None
            return RepairOutcome(
                status=ToolResultStatus.SUCCESS,
                stop_reason=TrialStopReason.SUCCESS,
                trials=tuple(trials),
                recipe_candidate=candidate,
                reason_vi=t("sai.repair.stop.success", lang=Lang.VI),
            )

    return RepairOutcome(
        status=ToolResultStatus.BLOCKED,
        stop_reason=TrialStopReason.ALL_CANDIDATES_FAILED,
        trials=tuple(trials),
        reason_vi=t("sai.repair.stop.all_candidates_failed", lang=Lang.VI),
    )
