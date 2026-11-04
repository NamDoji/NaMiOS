"""SAI-010 — bounded repair: gate M2 (1 ca pass / 1 ca phải dừng), dừng cứng,
giới hạn ngân sách, không retry vô hạn, không đụng bản gốc."""

from __future__ import annotations

from namios_smartai._types import Capsule, RepairBudget
from namios_smartai._types import ToolResultStatus as TS
from namios_smartai._types import TrialStopReason as SR
from namios_smartai.recipe import new_candidate
from namios_smartai.repair import bounded_repair


class _PassOnXp:
    """App A: giả thuyết chứa 'winxp' → SUCCESS, còn lại FAIL."""

    def run(self, h: str, cap: Capsule) -> tuple[TS, str, SR]:
        return (TS.SUCCESS, "ok", SR.NONE) if "winxp" in h else (TS.FAILED, "fail", SR.NONE)


class _AlwaysFail:
    def run(self, h: str, cap: Capsule) -> tuple[TS, str, SR]:
        return (TS.FAILED, "fail", SR.NONE)


class _DataWrong:
    def run(self, h: str, cap: Capsule) -> tuple[TS, str, SR]:
        return (TS.FAILED, "sai tổng tiền", SR.DATA_WRONG)


def _rf(h: str) -> object:
    return new_candidate(
        "r",
        publisher="p",
        source_url="https://x/y",
        app_id="a",
        app_version="1",
        app_hash="sha256:aa",
        architecture="x86_64",
        runner="wine",
        runtime="net",
        rollback="snap",
    )


def test_m2_gate_one_pass_one_stop() -> None:
    # Ca PASS: tìm được cách sửa → recipe candidate (experimental).
    ok = bounded_repair("appA", ["win10", "winxp", "win7"], _PassOnXp(), recipe_factory=_rf)
    assert ok.stop_reason == SR.SUCCESS
    assert ok.recipe_candidate is not None and ok.recipe_candidate.state.value == "experimental"
    assert len(ok.trials) == 2  # dừng ngay khi thành công, không thử win7

    # Ca PHẢI DỪNG: mọi ứng viên fail → dừng nêu lý do, không recipe.
    stop = bounded_repair("appB", ["a", "b", "c"], _AlwaysFail())
    assert stop.stop_reason == SR.ALL_CANDIDATES_FAILED
    assert stop.recipe_candidate is None


def test_hard_stop_data_wrong_immediate() -> None:
    out = bounded_repair("appC", ["x", "y", "z"], _DataWrong())
    assert out.stop_reason == SR.DATA_WRONG
    assert len(out.trials) == 1  # dừng CỨNG ngay phép thử đầu, không thử tiếp


def test_budget_caps_trials() -> None:
    out = bounded_repair(
        "z", [f"h{i}" for i in range(10)], _AlwaysFail(), budget=RepairBudget(max_trials=3)
    )
    assert len(out.trials) <= 3
    assert out.stop_reason in (SR.ALL_CANDIDATES_FAILED, SR.BUDGET_EXCEEDED)


def test_every_trial_rolled_back() -> None:
    out = bounded_repair("z", ["a", "b"], _AlwaysFail())
    assert all(tr.rolled_back for tr in out.trials)  # mọi phép thử đều rollback


def test_no_candidates_fails_closed() -> None:
    out = bounded_repair("z", [], _AlwaysFail())
    assert out.stop_reason == SR.ALL_CANDIDATES_FAILED
    assert out.recipe_candidate is None
