"""WP4 — Catalog store + tìm kiếm tiếng Việt accent-insensitive + revocation.

Xem ``docs/specs/M1-INTERFACES.md`` §7.2 và ``docs/specs/M1-WORK-PACKAGES.md``
WP4. Hiện thực ``namios_core.catalog_types.CatalogStore``.
"""

from __future__ import annotations

from namios_catalog._fold import fold_vn
from namios_catalog.store import InMemoryCatalogStore

__all__ = ["InMemoryCatalogStore", "fold_vn"]
