"""Fixture dùng chung cho test WP10 (recipe). KHÔNG dữ liệu thật/secret."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from namios_core.validation import SemanticContext

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
CATALOG_RECIPES_DIR = os.path.join(REPO_ROOT, "catalog", "recipes")
FIXTURES_RECIPE_DIR = os.path.join(REPO_ROOT, "fixtures", "recipe")


def ctx(
    approved: frozenset[str] = frozenset({"vcrun2019-x64", "dotnet-48-x64"}),
    revoked: frozenset[str] = frozenset(),
) -> SemanticContext:
    return SemanticContext(
        approved_dependency_ids=approved,
        pinned_runner_hashes=frozenset(),
        revoked_ids=revoked,
    )


def step(action: str, params: Mapping[str, Any]) -> dict[str, Any]:
    return {"action": action, "params": dict(params)}
