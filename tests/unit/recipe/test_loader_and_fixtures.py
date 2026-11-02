"""Load recipe JSON an toàn (WP8 ``resolve_within``/``open_within``) từ
``catalog/recipes/`` (mẫu vô hại) và ``fixtures/recipe/`` (mẫu tấn công);
chứng minh end-to-end parse+dry_run trên recipe thật trong repo."""

from __future__ import annotations

import pytest

from namios_core.errors import ErrorCode
from namios_recipe import RecipeEngineImpl, RecipeParseError, load_recipe_steps_from_file
from namios_security import PathUnsafeError

from ._fixtures import CATALOG_RECIPES_DIR, FIXTURES_RECIPE_DIR, ctx


def test_load_catalog_sample_notepad_plusplus_parses_and_dry_runs_ok() -> None:
    steps = load_recipe_steps_from_file(CATALOG_RECIPES_DIR, "sample-notepad-plusplus.json")
    assert len(steps) == 6

    engine = RecipeEngineImpl()
    result = engine.dry_run(
        steps,
        ctx(approved=frozenset({"vcrun2019-x64"})),
    )
    assert result.ok is True
    assert len(result.planned_actions) == 6


def test_load_fixture_harmless_valid_recipe_parses_ok() -> None:
    steps = load_recipe_steps_from_file(FIXTURES_RECIPE_DIR, "harmless_valid_recipe.json")
    assert len(steps) == 3


@pytest.mark.parametrize(
    "filename",
    [
        "malicious_shell_param.json",
        "malicious_unknown_action.json",
        "malicious_url_script_argv.json",
        "malicious_template_interpolation.json",
    ],
)
def test_load_malicious_fixtures_all_rejected_at_parse(filename: str) -> None:
    with pytest.raises(RecipeParseError) as exc_info:
        load_recipe_steps_from_file(FIXTURES_RECIPE_DIR, filename)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_loader_rejects_path_traversal_outside_fixtures_dir() -> None:
    with pytest.raises(PathUnsafeError):
        load_recipe_steps_from_file(FIXTURES_RECIPE_DIR, "../../pyproject.toml")


def test_loader_rejects_absolute_candidate_path() -> None:
    with pytest.raises(PathUnsafeError):
        load_recipe_steps_from_file(FIXTURES_RECIPE_DIR, "/etc/passwd")
