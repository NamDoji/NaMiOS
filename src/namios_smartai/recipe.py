"""Compatibility Recipe schema + validator (SAI-011/041).

Công thức AI đề xuất mặc định ``experimental`` — chỉ promotion gate (SAI-012)
mới nâng. Bất biến publish (nghiệm thu SAI-041): thiếu ``source_url``/
``app_hash``, hoặc recipe ĐỔI HỆ THỐNG mà thiếu ``rollback`` → KHÔNG publish
được; recipe kiến trúc x86 KHÔNG tự áp cho x64.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from namios_core.validation import ValidationError
from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import CompatibilityRecipe, RecipeState

__all__ = [
    "validate_recipe_publishable",
    "arch_applies",
    "new_candidate",
    "recipe_from_dict",
]


def validate_recipe_publishable(recipe: CompatibilityRecipe) -> list[ValidationError]:
    """Kiểm điều kiện CẤU TRÚC để được publish (SAI-041). Rỗng = đủ điều kiện
    cấu trúc (còn trạng thái thật do promotion gate + evidence quyết)."""

    errors: list[ValidationError] = []
    if not (recipe.source_url or "").strip():
        errors.append(
            ValidationError(
                code=SaiErrorCode.E_SAI_RECIPE_UNPUBLISHABLE.value,
                path="source_url",
                message_vi=t("sai.recipe.error.missing_source", lang=Lang.VI),
            )
        )
    if not (recipe.app_hash or "").strip():
        errors.append(
            ValidationError(
                code=SaiErrorCode.E_SAI_RECIPE_UNPUBLISHABLE.value,
                path="app_hash",
                message_vi=t("sai.recipe.error.missing_hash", lang=Lang.VI),
            )
        )
    if recipe.changes_system and not (recipe.rollback or "").strip():
        errors.append(
            ValidationError(
                code=SaiErrorCode.E_SAI_RECIPE_UNPUBLISHABLE.value,
                path="rollback",
                message_vi=t("sai.recipe.error.missing_rollback", lang=Lang.VI),
            )
        )
    return errors


def arch_applies(recipe: CompatibilityRecipe, target_arch: str) -> bool:
    """Recipe CHỈ áp đúng kiến trúc đã chứng nhận (SAI-041: x86 không tự áp
    x64). So khớp chính xác (chuẩn hoá hoa/thường/khoảng trắng)."""

    return recipe.architecture.strip().lower() == (target_arch or "").strip().lower()


def new_candidate(
    recipe_id: str,
    *,
    publisher: str,
    source_url: str,
    app_id: str,
    app_version: str,
    app_hash: str,
    architecture: str,
    runner: str,
    runtime: str,
    rollback: str | None = None,
    changes_system: bool = True,
) -> CompatibilityRecipe:
    """Dựng ứng viên công thức — LUÔN bắt đầu ở ``experimental`` (SAI-011)."""

    return CompatibilityRecipe(
        recipe_id=recipe_id,
        publisher=publisher,
        source_url=source_url,
        app_id=app_id,
        app_version=app_version,
        app_hash=app_hash,
        architecture=architecture,
        runner=runner,
        runtime=runtime,
        rollback=rollback,
        changes_system=changes_system,
        state=RecipeState.EXPERIMENTAL,
    )


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return ()


def recipe_from_dict(raw: Mapping[str, Any]) -> CompatibilityRecipe:
    """Dựng ``CompatibilityRecipe`` từ dict (JSON). Trường thiếu → mặc định
    an toàn (rỗng); ``state`` luôn về ``experimental`` khi nạp từ ngoài (không
    tin nhãn tự khai — promotion gate mới quyết)."""

    return CompatibilityRecipe(
        recipe_id=str(raw.get("recipe_id", "")),
        publisher=str(raw.get("publisher", "")),
        source_url=str(raw.get("source_url", "")),
        app_id=str(raw.get("app_id", "")),
        app_version=str(raw.get("app_version", "")),
        app_hash=str(raw.get("app_hash", "")),
        architecture=str(raw.get("architecture", "unknown")),
        runner=str(raw.get("runner", "")),
        runtime=str(raw.get("runtime", "")),
        preconditions=_str_tuple(raw.get("preconditions")),
        actions=_str_tuple(raw.get("actions")),
        expected_outputs=_str_tuple(raw.get("expected_outputs")),
        tests=_str_tuple(raw.get("tests")),
        license_notes=str(raw.get("license_notes", "")),
        reviewers=_str_tuple(raw.get("reviewers")),
        verified_scope=str(raw.get("verified_scope", "")),
        retest_on=_str_tuple(raw.get("retest_on")),
        rollback=raw.get("rollback"),
        signature=raw.get("signature"),
        changes_system=bool(raw.get("changes_system", True)),
        state=RecipeState.EXPERIMENTAL,
    )
