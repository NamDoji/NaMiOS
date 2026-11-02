"""Hiện thực ``namios_core.recipe_types.RecipeEngine`` (Protocol, §7.6).

``parse``: chặn action/param ngoài allowlist, field shell/eval/url-script/
template nội suy — raise ``RecipeParseError`` (tuple ``ValidationError``)
nếu BẤT KỲ bước nào sai, KHÔNG build một phần.

``dry_run``: KHÔNG thực thi gì (M1 gate). Liệt kê hành động dự kiến +
kiểm runtime/semantic (dependency đã duyệt, argv-only, sha256/registry hợp
lệ). Thực thi thật (tạo prefix Wine, chạy installer) là M2 — BLOCKED tại
host này (không có Wine/qemu/kvm).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from namios_core.recipe_types import DryRunResult, RecipeStep
from namios_core.validation import SemanticContext
from namios_recipe._dry_run import dry_run_steps
from namios_recipe._parse import parse_recipe_steps

__all__ = ["RecipeEngineImpl"]


class RecipeEngineImpl:
    """Hiện thực đơn giản, không trạng thái (stateless) của ``RecipeEngine``."""

    def parse(self, raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
        return parse_recipe_steps(raw_steps)

    def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
        return dry_run_steps(steps, ctx)
