"""Unit test ``namios_catalog.store.InMemoryCatalogStore`` — hiện thực
``namios_core.catalog_types.CatalogStore`` (§7.2). Bao gồm negative cases."""

from __future__ import annotations

import json
from pathlib import Path

from tests.unit.catalog._fixtures import make_entry, make_manifest

from namios_catalog.store import InMemoryCatalogStore
from namios_core.catalog_types import CatalogEntry, RevocationRecord

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "catalog" / "vn-accent-entries.json"
)


def _load_vn_fixture_entries() -> list[CatalogEntry]:
    raw = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return [
        make_entry(item["app_id"], item["name"], item["publisher"], item["channel"])
        for item in raw
    ]


# -- add/get/list -------------------------------------------------------------


def test_add_then_get_returns_same_entry() -> None:
    store = InMemoryCatalogStore()
    entry = make_entry("demo-app", "Demo App")
    store.add(entry)

    fetched = store.get("demo-app")
    assert fetched is not None
    assert fetched.manifest.name == "Demo App"
    assert fetched.digest == entry.digest


def test_get_unknown_app_id_returns_none() -> None:
    store = InMemoryCatalogStore()
    assert store.get("khong-ton-tai") is None


def test_list_without_channel_returns_all_entries() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("a", "App A", channel="dev"))
    store.add(make_entry("b", "App B", channel="stable"))

    listed = store.list()
    assert {e.manifest.id for e in listed} == {"a", "b"}


def test_list_filters_by_channel() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("a", "App A", channel="dev"))
    store.add(make_entry("b", "App B", channel="stable"))

    listed = store.list(channel="stable")
    assert [e.manifest.id for e in listed] == ["b"]


def test_list_unknown_channel_returns_empty_tuple() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("a", "App A", channel="dev"))

    assert store.list(channel="pilot") == ()


def test_add_overwrites_existing_entry_with_same_app_id() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("demo-app", "Demo App v1", digest="1" * 64))
    store.add(make_entry("demo-app", "Demo App v2", digest="2" * 64))

    fetched = store.get("demo-app")
    assert fetched is not None
    assert fetched.manifest.name == "Demo App v2"
    assert fetched.digest == "2" * 64
    # không nhân bản entry cũ trong list()
    assert len(store.list()) == 1


# -- search: accent-insensitive + case-insensitive (UX-006) ------------------


def test_search_accented_query_matches_accented_entry() -> None:
    store = InMemoryCatalogStore()
    for e in _load_vn_fixture_entries():
        store.add(e)

    results = store.search("Đỗ Chí Cường")
    assert [r.manifest.id for r in results] == ["vn-demo-app-cuong"]


def test_search_unaccented_query_matches_same_accented_entry() -> None:
    store = InMemoryCatalogStore()
    for e in _load_vn_fixture_entries():
        store.add(e)

    results = store.search("do chi cuong")
    assert [r.manifest.id for r in results] == ["vn-demo-app-cuong"]


def test_search_is_case_insensitive_regardless_of_accents() -> None:
    store = InMemoryCatalogStore()
    for e in _load_vn_fixture_entries():
        store.add(e)

    lower = store.search("do chi cuong")
    upper = store.search("DO CHI CUONG")
    mixed_accented = store.search("đỖ cHí cƯỜng")
    assert {r.manifest.id for r in lower} == {"vn-demo-app-cuong"}
    assert {r.manifest.id for r in upper} == {"vn-demo-app-cuong"}
    assert {r.manifest.id for r in mixed_accented} == {"vn-demo-app-cuong"}


def test_search_does_not_mutate_display_name_or_app_id() -> None:
    store = InMemoryCatalogStore()
    for e in _load_vn_fixture_entries():
        store.add(e)

    results = store.search("do chi cuong")
    assert results[0].manifest.name == "Đỗ Chí Cường Studio"  # tên hiển thị giữ dấu gốc
    assert results[0].manifest.id == "vn-demo-app-cuong"  # app_id/tên file gốc không đổi


def test_search_partial_substring_match() -> None:
    store = InMemoryCatalogStore()
    for e in _load_vn_fixture_entries():
        store.add(e)

    results = store.search("tieng viet")
    assert [r.manifest.id for r in results] == ["vn-demo-app-vietnamese"]


def test_search_no_match_returns_empty_tuple() -> None:
    store = InMemoryCatalogStore()
    for e in _load_vn_fixture_entries():
        store.add(e)

    assert store.search("khong-co-app-nao-ten-nhu-vay") == ()


def test_search_empty_query_returns_empty_tuple() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("a", "App A"))

    assert store.search("") == ()
    assert store.search("   ") == ()


def test_search_respects_limit() -> None:
    store = InMemoryCatalogStore()
    for i in range(5):
        store.add(make_entry(f"app-{i}", f"Demo App {i}"))

    results = store.search("demo app", limit=2)
    assert len(results) == 2


def test_search_limit_zero_or_negative_returns_empty_tuple() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("a", "App A"))

    assert store.search("app", limit=0) == ()
    assert store.search("app", limit=-1) == ()


def test_search_result_order_is_deterministic() -> None:
    store = InMemoryCatalogStore()
    # thêm theo thứ tự ngược với thứ tự mong đợi để xác nhận search() không
    # phụ thuộc thứ tự chèn/hash dict.
    store.add(make_entry("c", "Charlie App"))
    store.add(make_entry("a", "Alpha App"))
    store.add(make_entry("b", "Bravo App"))

    results = store.search("app")
    assert [r.manifest.id for r in results] == ["a", "b", "c"]


# -- revocation ----------------------------------------------------------------


def test_is_revoked_false_by_default() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("demo-app", "Demo App"))

    assert store.is_revoked("demo-app") is False


def test_is_revoked_true_after_revoke() -> None:
    store = InMemoryCatalogStore()
    store.add(make_entry("demo-app", "Demo App"))
    store.revoke(
        RevocationRecord(target_id="demo-app", reason="hash sai", revoked_at="2026-11-02T00:00:00Z")
    )

    assert store.is_revoked("demo-app") is True


def test_is_revoked_for_unknown_app_id_is_false_not_error() -> None:
    store = InMemoryCatalogStore()
    assert store.is_revoked("khong-ton-tai") is False


def test_revocations_lists_all_records() -> None:
    store = InMemoryCatalogStore()
    store.revoke(RevocationRecord(target_id="a", reason="r1", revoked_at="2026-11-01T00:00:00Z"))
    store.revoke(RevocationRecord(target_id="b", reason="r2", revoked_at="2026-11-02T00:00:00Z"))

    records = store.revocations()
    assert {r.target_id for r in records} == {"a", "b"}


def test_revoked_entry_remains_gettable_but_flagged_revoked() -> None:
    """Revocation KHÔNG xoá dữ liệu — caller (CLI/manifest semantic) phải tự
    kiểm ``is_revoked()`` trước khi coi entry là "cài được" (FACT
    M1-INTERFACES §7.1: ``SemanticContext.revoked_ids`` tách biệt khỏi
    catalog data)."""

    store = InMemoryCatalogStore()
    store.add(make_entry("demo-app", "Demo App"))
    store.revoke(
        RevocationRecord(
            target_id="demo-app", reason="mat du lieu", revoked_at="2026-11-02T00:00:00Z"
        )
    )

    entry = store.get("demo-app")
    assert entry is not None  # dữ liệu vẫn còn
    assert store.is_revoked("demo-app") is True  # nhưng bị đánh dấu revoked


def test_unrevoke_clears_revoked_flag() -> None:
    store = InMemoryCatalogStore()
    store.revoke(RevocationRecord(target_id="a", reason="r", revoked_at="2026-11-01T00:00:00Z"))
    assert store.is_revoked("a") is True

    store.unrevoke("a")
    assert store.is_revoked("a") is False


def test_unrevoke_unknown_target_id_is_noop() -> None:
    store = InMemoryCatalogStore()
    store.unrevoke("khong-ton-tai")  # không raise
    assert store.is_revoked("khong-ton-tai") is False


# -- entry hiển thị tên gốc dù app_id/publisher có dấu ------------------------


def test_manifest_fixture_name_is_not_folded_in_place() -> None:
    manifest = make_manifest("demo", "Đỗ Chí Cường")
    assert manifest.name == "Đỗ Chí Cường"
