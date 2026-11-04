"""SAI-035 — Kill Switch: tắt độc lập + wildcard + chặn phát hành."""

from __future__ import annotations

from namios_smartai._types import SwitchTarget as ST
from namios_smartai.kill_switch import WILDCARD, KillSwitch


def test_disable_single_target() -> None:
    ks = KillSwitch()
    assert ks.is_enabled(ST.RECIPE, "r1")
    ks.disable(ST.RECIPE, "r1")
    assert ks.guard(ST.RECIPE, "r1") is not None  # bị chặn
    assert ks.guard(ST.RECIPE, "r2") is None  # recipe khác vẫn chạy


def test_wildcard_disables_whole_class() -> None:
    ks = KillSwitch()
    ks.disable(ST.AUTO_REPAIR, WILDCARD)
    assert not ks.is_enabled(ST.AUTO_REPAIR, "anything")
    assert ks.guard(ST.AUTO_REPAIR, "x") is not None


def test_enable_reverts() -> None:
    ks = KillSwitch()
    ks.disable(ST.TOOL, "run_test")
    ks.enable(ST.TOOL, "run_test")
    assert ks.is_enabled(ST.TOOL, "run_test")


def test_release_block_on_bad_result() -> None:
    ks = KillSwitch()
    assert not ks.release_blocked()
    ks.block_release("sai tổng tiền")
    assert ks.release_blocked()
    assert ks.release_block_reason()


def test_revoke_pilot_recipe_before_new_task() -> None:
    # SAI-035 nghiệm thu: thu hồi recipe đang pilot → tác vụ mới dùng nó bị chặn.
    ks = KillSwitch()
    ks.disable(ST.RECIPE, "pilot-recipe")
    assert ks.guard(ST.RECIPE, "pilot-recipe") is not None
