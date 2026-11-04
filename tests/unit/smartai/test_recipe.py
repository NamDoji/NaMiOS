"""SAI-011/041 — recipe schema + validator."""

from __future__ import annotations

from namios_smartai._types import RecipeState
from namios_smartai.recipe import arch_applies, new_candidate, validate_recipe_publishable


def _good() -> object:
    return new_candidate(
        "r1",
        publisher="p",
        source_url="https://misa.vn/x.exe",
        app_id="misa",
        app_version="2024",
        app_hash="sha256:aa",
        architecture="x86_64",
        runner="wine",
        runtime="net48",
        rollback="snapshot",
    )


def test_candidate_default_experimental() -> None:
    assert _good().state == RecipeState.EXPERIMENTAL


def test_publishable_ok() -> None:
    assert validate_recipe_publishable(_good()) == []


def test_missing_source_hash_rollback_block_publish() -> None:
    bad = new_candidate(
        "r2",
        publisher="p",
        source_url="",
        app_id="a",
        app_version="1",
        app_hash="",
        architecture="x86",
        runner="wine",
        runtime="net",
        rollback=None,
        changes_system=True,
    )
    paths = {e.path for e in validate_recipe_publishable(bad)}
    assert paths == {"source_url", "app_hash", "rollback"}


def test_non_system_recipe_needs_no_rollback() -> None:
    r = new_candidate(
        "r3",
        publisher="p",
        source_url="https://x/y",
        app_id="a",
        app_version="1",
        app_hash="sha256:bb",
        architecture="x86_64",
        runner="web",
        runtime="browser",
        rollback=None,
        changes_system=False,
    )
    assert validate_recipe_publishable(r) == []  # không đổi hệ thống → không bắt buộc rollback


def test_arch_does_not_cross_apply() -> None:
    r = _good()  # x86_64
    assert arch_applies(r, "x86_64")
    assert not arch_applies(r, "x86")
