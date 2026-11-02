"""Load recipe JSON (danh sách bước ``{action, params}``) từ đĩa an toàn,
dùng ``namios_security.resolve_within`` (WP8) — KHÔNG tự chế lại path safety
(FACT M1-INTERFACES §7.8/§0: WP10 phụ thuộc WP8).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from namios_core.recipe_types import RecipeStep
from namios_recipe._errors import RecipeParseError
from namios_recipe._parse import parse_recipe_steps
from namios_security import open_within

__all__ = ["load_recipe_steps_from_file"]


def load_recipe_steps_from_file(base_dir: str, relative_path: str) -> tuple[RecipeStep, ...]:
    """Đọc file JSON recipe ``relative_path`` bên trong ``base_dir`` (chống
    traversal/symlink/TOCTOU qua ``open_within``), rồi parse thành
    ``RecipeStep`` typed. Raise ``RecipeParseError``/``PathUnsafeError`` nếu
    không hợp lệ/không an toàn — KHÔNG đọc ngoài ``base_dir``."""

    with open_within(base_dir, relative_path, "rb") as fh:
        raw_bytes = fh.read()

    raw: Any = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        from namios_core.errors import ErrorCode
        from namios_core.validation import ValidationError

        raise RecipeParseError(
            (
                ValidationError(
                    code=ErrorCode.E_SEMANTIC_RECIPE.value,
                    path="",
                    message_vi="File recipe phải chứa một JSON array ở cấp cao nhất.",
                ),
            )
        )
    raw_steps: Sequence[Mapping[str, Any]] = raw
    return parse_recipe_steps(raw_steps)
