"""SAI-033 — regression matrix: đổi thành phần → needs_retest."""

from __future__ import annotations

from namios_smartai._types import RecipeState, RegressionKey
from namios_smartai.recipe import new_candidate
from namios_smartai.regression import apply_regression, changed_components


def _recipe() -> object:
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


def test_wine_change_marks_needs_retest() -> None:
    old = RegressionKey(wine_runtime="wine-9.0", workflow_id="w")
    new = RegressionKey(wine_runtime="wine-10.0", workflow_id="w")
    assert "wine_runtime" in changed_components(old, new)
    assert apply_regression(_recipe(), old=old, new=new).state == RecipeState.NEEDS_RETEST


def test_no_change_keeps_state() -> None:
    k = RegressionKey(wine_runtime="wine-9.0", app_version="2024")
    r = _recipe()
    assert changed_components(k, k) == ()
    assert apply_regression(r, old=k, new=k).state == r.state


def test_multiple_component_changes_listed() -> None:
    old = RegressionKey(app_version="1", device="hp-1")
    new = RegressionKey(app_version="2", device="hp-2")
    changed = changed_components(old, new)
    assert "app_version" in changed and "device" in changed
