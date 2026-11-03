"""Catalog API (WP4 hiện thực — compat-catalog, UX-006). Xem
M1-INTERFACES.md §7.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from namios_core.manifest_types import Manifest


@dataclass(frozen=True)
class CatalogEntry:
    manifest: Manifest
    digest: str
    channel: str  # dev/alpha/pilot/stable


@dataclass(frozen=True)
class RevocationRecord:
    target_id: str
    reason: str
    revoked_at: str  # ISO 8601


class CatalogStore(Protocol):
    def add(self, entry: CatalogEntry) -> None: ...

    def get(self, app_id: str) -> CatalogEntry | None: ...

    def list(self, channel: str | None = None) -> tuple[CatalogEntry, ...]: ...

    def search(
        self, query: str, limit: int = 50
    ) -> tuple[CatalogEntry, ...]: ...  # accent-insensitive VN

    def is_revoked(self, app_id: str) -> bool: ...

    def revocations(self) -> tuple[RevocationRecord, ...]: ...
