"""WP10 — Recipe engine declarative allowlist + dry-run.

Xem ``docs/specs/M1-INTERFACES.md`` §7.6 và ``docs/specs/M1-WORK-PACKAGES.md``
WP10. Hiện thực ``namios_core.recipe_types.RecipeEngine``.

M1: chỉ ``dry_run`` (không thực thi gì, không tạo prefix Wine thật — M2
BLOCKED tại host này, không có Wine/qemu/kvm).
"""

from __future__ import annotations

from namios_recipe._dry_run import dry_run_steps
from namios_recipe._errors import RecipeParseError
from namios_recipe._parse import ALLOWED_ACTIONS, parse_recipe_steps
from namios_recipe.engine import RecipeEngineImpl
from namios_recipe.loader import load_recipe_steps_from_file

__all__ = [
    "RecipeEngineImpl",
    "RecipeParseError",
    "ALLOWED_ACTIONS",
    "parse_recipe_steps",
    "dry_run_steps",
    "load_recipe_steps_from_file",
]
