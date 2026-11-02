"""Hiện thực ``namios_core.catalog_types.CatalogStore`` (WP4 — compat-catalog,
UX-006). Xem ``docs/specs/M1-INTERFACES.md`` §7.2.

Phạm vi M1: store trong bộ nhớ (per-process), đủ để hiện thực + kiểm thử
đúng hành vi tìm kiếm accent-insensitive + revocation theo Protocol. Việc
lưu bền (JSON trên đĩa dưới ``fixtures``/cache) là chi tiết bộ gọi (CLI/
tích hợp) — ``InMemoryCatalogStore`` không tự đọc/ghi file để giữ test
không phụ thuộc filesystem/race ngoài phạm vi sở hữu (path safety thuộc WP8).
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_catalog._fold import fold_vn
from namios_core.catalog_types import CatalogEntry, RevocationRecord

__all__ = ["InMemoryCatalogStore"]


class InMemoryCatalogStore:
    """Hiện thực cụ thể của ``CatalogStore`` Protocol.

    Index tìm kiếm được giữ chuẩn hóa (fold dấu + casefold) TRONG BỘ NHỚ,
    tách biệt hoàn toàn khỏi dữ liệu hiển thị (``entry.manifest.name`` giữ
    nguyên dấu/hoa-thường gốc — không bị ghi đè bởi bước fold).
    """

    def __init__(self) -> None:
        self._entries: dict[str, CatalogEntry] = {}
        # app_id -> haystack đã fold (name + id + publisher), để search() O(n)
        # không phải fold lại mỗi lần gọi.
        self._folded_haystack: dict[str, str] = {}
        self._revocations: dict[str, RevocationRecord] = {}

    # -- CatalogStore Protocol -------------------------------------------------

    def add(self, entry: CatalogEntry) -> None:
        app_id = entry.manifest.id
        self._entries[app_id] = entry
        haystack = " ".join(
            (entry.manifest.name, entry.manifest.id, entry.manifest.publisher)
        )
        self._folded_haystack[app_id] = fold_vn(haystack)

    def get(self, app_id: str) -> CatalogEntry | None:
        return self._entries.get(app_id)

    def list(self, channel: str | None = None) -> tuple[CatalogEntry, ...]:
        all_entries: Iterable[CatalogEntry] = self._entries.values()
        if channel is not None:
            all_entries = (e for e in all_entries if e.channel == channel)
        return tuple(all_entries)

    def search(self, query: str, limit: int = 50) -> tuple[CatalogEntry, ...]:
        if limit <= 0:
            return ()
        folded_query = fold_vn(query).strip()
        if not folded_query:
            return ()
        matches: list[CatalogEntry] = []
        for app_id, haystack in self._folded_haystack.items():
            if folded_query in haystack:
                matches.append(self._entries[app_id])
        # Thứ tự xác định (không phụ thuộc thứ tự dict/hash) — theo tên hiển
        # thị gốc rồi app_id, để kết quả test ổn định.
        matches.sort(key=lambda e: (e.manifest.name, e.manifest.id))
        return tuple(matches[:limit])

    def is_revoked(self, app_id: str) -> bool:
        return app_id in self._revocations

    def revocations(self) -> tuple[RevocationRecord, ...]:
        return tuple(self._revocations.values())

    # -- Mở rộng ngoài Protocol tối thiểu (owner được phép thêm — xem
    #    M1-INTERFACES §7: "owner có thể thêm method nội bộ nhưng KHÔNG đổi
    #    chữ ký public" của các method đã khai báo). Protocol KHÔNG có cách
    #    nào khác để nạp revocation, nên bổ sung ``revoke``/``unrevoke``. ---

    def revoke(self, record: RevocationRecord) -> None:
        """Thêm/ghi đè một bản ghi thu hồi cho ``record.target_id``."""

        self._revocations[record.target_id] = record

    def unrevoke(self, target_id: str) -> None:
        """Gỡ thu hồi (vd. phục hồi sau khi vá lỗi) — idempotent."""

        self._revocations.pop(target_id, None)
