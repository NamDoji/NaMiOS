"""Hiện thực ``ManifestValidator`` (namios_core.manifest_types, §7.1).

Validation 2 tầng:
  - Tầng 1 (``validate_schema``): JSON Schema draft 2020-12 — tập con tự
    diễn giải ở ``_schema_engine`` (không có ``jsonschema`` lib trong venv
    host này; không được ``pip install`` — xem CLAUDE.md môi trường build).
    ``additionalProperties: false`` → khóa lạ fail ngay tầng này
    (``E_INPUT_UNKNOWN_KEY``).
  - Tầng 2 (``validate_semantic``): chặn TBD/null bắt buộc, runner chưa
    pin, dependency chưa duyệt, revoked, ``task_verified`` thiếu evidence
    (``_semantic``). "Schema hợp lệ" ≠ "an toàn để chạy" — ``SchemaResult.ok``
    và ``SemanticResult.install_ready`` là HAI cờ độc lập.

``load()`` đọc file qua lớp an toàn tạm (``_safe_io`` — chờ ``namios_security``
của WP8), chạy tầng 1, rồi build Manifest (bước build cũng chặn recipe
ngoài allowlist/shell — xem ``_recipe_build``).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from namios_core.errors import ErrorCode
from namios_core.manifest_types import Manifest, SchemaResult, SemanticResult
from namios_core.validation import SemanticContext, ValidationError
from namios_manifest._builder import build_manifest
from namios_manifest._errors import ManifestLoadError
from namios_manifest._safe_io import PathUnsafeError, read_text_safe
from namios_manifest._schema_engine import validate_instance
from namios_manifest._semantic import validate_semantic

__all__ = ["ManifestValidatorImpl", "ManifestLoadError", "PathUnsafeError"]

#: ``contracts/app-manifest.schema.json`` nằm ở gốc repo, hai cấp trên
#: package này (``src/namios_manifest/validator.py`` → ``src`` → gốc repo).
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts" / "app-manifest.schema.json"

_schema_cache: Mapping[str, Any] | None = None


def _load_schema() -> Mapping[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        text = _SCHEMA_PATH.read_text(encoding="utf-8")
        _schema_cache = json.loads(text)
    return _schema_cache


class ManifestValidatorImpl:
    """Hiện thực cụ thể khớp ``namios_core.manifest_types.ManifestValidator``."""

    def load(self, path: str) -> Manifest:
        text = read_text_safe(path)
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ManifestLoadError(
                (
                    ValidationError(
                        code=ErrorCode.E_INPUT_SCHEMA.value,
                        path="$",
                        message_vi=f"Nội dung manifest không phải JSON hợp lệ: {exc.msg}.",
                    ),
                )
            ) from exc

        schema_result = self.validate_schema(raw)
        if not schema_result.ok:
            raise ManifestLoadError(schema_result.errors)

        return build_manifest(raw)

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        schema = _load_schema()
        violations = validate_instance(schema, raw, path="$")
        errors = tuple(
            ValidationError(
                code=(
                    ErrorCode.E_INPUT_UNKNOWN_KEY.value
                    if v.kind == "unknown_key"
                    else ErrorCode.E_INPUT_SCHEMA.value
                ),
                path=v.path,
                message_vi=v.message_vi,
            )
            for v in violations
        )
        return SchemaResult(ok=len(errors) == 0, errors=errors)

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult:
        return validate_semantic(m, ctx)
