"""SAI-026 — Memory Scope: cách ly đa tenant."""

from __future__ import annotations

from namios_smartai._types import MemoryScope as MS
from namios_smartai.memory_scope import MemoryStore


def _store() -> MemoryStore:
    m = MemoryStore()
    m.put(MS.ORG, "ketoan", "recipe1", {"x": 1})
    m.put(MS.ORG, "truong", "recipe1", {"y": 2})
    m.put(MS.PUBLIC, "namios", "kb1", "public info")
    return m


def test_owner_reads_own() -> None:
    assert _store().get(MS.ORG, "ketoan", "recipe1", requester="ketoan") == {"x": 1}


def test_cross_tenant_denied() -> None:
    m = _store()
    assert m.get(MS.ORG, "ketoan", "recipe1", requester="truong") is None
    assert m.list_keys(MS.ORG, "ketoan", requester="truong") == ()


def test_public_readable_by_all() -> None:
    assert _store().get(MS.PUBLIC, "namios", "kb1", requester="anyone") == "public info"


def test_export_and_delete_self_service() -> None:
    m = _store()
    assert m.export_tenant("ketoan", requester="ketoan") == {"org/recipe1": {"x": 1}}
    assert m.delete_tenant("ketoan", requester="ketoan") == 1
    assert m.get(MS.ORG, "ketoan", "recipe1", requester="ketoan") is None
    # Xoá tenant này KHÔNG đụng tenant khác.
    assert m.get(MS.ORG, "truong", "recipe1", requester="truong") == {"y": 2}


def test_cross_tenant_cannot_export_or_delete() -> None:
    m = _store()
    # Tenant 'truong' KHÔNG xuất/xoá được dữ liệu của 'ketoan'.
    assert m.export_tenant("ketoan", requester="truong") == {}
    assert m.delete_tenant("ketoan", requester="truong") == 0
    assert m.get(MS.ORG, "ketoan", "recipe1", requester="ketoan") == {"x": 1}  # còn nguyên
