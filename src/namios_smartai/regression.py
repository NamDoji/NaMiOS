"""Regression Matrix (SAI-033).

Khóa theo ``(OS build, model version, planner version, tool schema, recipe,
Wine/runtime, app version, device, workflow)``. Đổi BẤT KỲ thành phần nào →
recipe/workflow liên quan chuyển ``needs_retest`` TRƯỚC khi stable (nghiệm thu:
đổi Wine làm badge workflow thành ``needs_retest``).
"""

from __future__ import annotations

from dataclasses import fields, replace

from namios_smartai._types import CompatibilityRecipe, RecipeState, RegressionKey

__all__ = ["changed_components", "apply_regression"]


def changed_components(old: RegressionKey, new: RegressionKey) -> tuple[str, ...]:
    """Tên các thành phần khác nhau giữa hai khóa hồi quy (thứ tự ổn định)."""

    return tuple(
        f.name for f in fields(RegressionKey) if getattr(old, f.name) != getattr(new, f.name)
    )


def apply_regression(
    recipe: CompatibilityRecipe, *, old: RegressionKey, new: RegressionKey
) -> CompatibilityRecipe:
    """Nếu có thành phần đổi → trả recipe với ``state=needs_retest`` (an toàn,
    buộc tái kiểm trước stable). Không đổi → giữ nguyên recipe."""

    if changed_components(old, new):
        return replace(recipe, state=RecipeState.NEEDS_RETEST)
    return recipe
