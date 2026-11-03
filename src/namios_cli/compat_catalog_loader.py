"""Loader cho catalog tương thích (COMP-025/048, ``catalog/compat/*.json``)
dùng bởi subcommand ``namios compat`` — WP3 + vai trò ``namios_compat``.

Giống ``service_catalog_loader``: catalog là dữ liệu TĨNH đóng gói trong repo
(không phải input runtime), nên không qua ``resolve_within``; mỗi file PHẢI
qua validator chống-metadata-giả (``namios_compat.schema.validate_workflow_entry``)
trước khi dựng ``WorkflowEntry``. File hỏng = LỖI NỘI BỘ (dữ liệu đã validate
khi build), caller chuẩn hoá về ``E_INTERNAL``. KHÔNG lặng lẽ bỏ entry hỏng.
"""

from __future__ import annotations

import json
from pathlib import Path

from namios_compat._types import WorkflowEntry
from namios_compat.schema import build_workflow_entry, validate_workflow_entry

__all__ = [
    "CATALOG_COMPAT_DIR",
    "CompatCatalogLoadError",
    "load_compat_catalog",
]

#: ``<repo_root>/catalog/compat`` (src/namios_cli/x.py → parents[2] = gốc repo).
CATALOG_COMPAT_DIR = Path(__file__).resolve().parents[2] / "catalog" / "compat"


class CompatCatalogLoadError(Exception):
    """Catalog tương thích đóng gói cùng repo không đọc/thẩm định được — LỖI
    NỘI BỘ (không phải input runtime của người dùng)."""


def load_compat_catalog(directory: Path | None = None) -> tuple[WorkflowEntry, ...]:
    """Đọc + thẩm định mọi ``*.json`` dưới ``directory`` (mặc định
    ``CATALOG_COMPAT_DIR``), trả tuple ``WorkflowEntry`` ổn định thứ tự theo
    tên file. Raise :class:`CompatCatalogLoadError` ngay khi file đầu hỏng."""

    base = directory if directory is not None else CATALOG_COMPAT_DIR
    if not base.is_dir():
        return ()

    entries: list[WorkflowEntry] = []
    for path in sorted(base.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CompatCatalogLoadError(
                f"Không đọc được file catalog tương thích '{path.name}': {type(exc).__name__}."
            ) from exc
        result = validate_workflow_entry(raw)
        if not result.ok:
            first = result.errors[0]
            raise CompatCatalogLoadError(
                f"{path.name}: lỗi schema tại '{first.path}': {first.message_vi}"
            )
        entries.append(build_workflow_entry(raw))

    return tuple(entries)
