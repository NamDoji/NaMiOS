"""Perf nhẹ: index 1.000 record + tìm kiếm (PERF-02 TARGET ≤300ms, đo ở máy
tham chiếu — KHÔNG chặn unit theo M1-INTERFACES §7.2/M1-WORK-PACKAGES WP4).

Test này CHẠY ĐƯỢC tại host hiện tại và đo thời gian thật; ghi số đo thật
qua ``print`` (xem với ``pytest -s``) thay vì assert cứng 300ms (môi trường
CI/container không phải "máy tham chiếu" nên assert cứng sẽ flaky — chỉ
assert một ngưỡng rộng để bắt hồi quy thật sự nghiêm trọng, ví dụ O(n^2)
bùng nổ)."""

from __future__ import annotations

import time

from tests.unit.catalog._fixtures import make_entry

from namios_catalog.store import InMemoryCatalogStore

_RECORD_COUNT = 1000


def _build_bulk_store() -> InMemoryCatalogStore:
    store = InMemoryCatalogStore()
    vn_names = ["Đỗ Chí Cường", "Đỗ Bảo Nam", "Ứng Dụng Tiếng Việt", "Trình Soạn Thảo"]
    for i in range(_RECORD_COUNT):
        vn_name = vn_names[i % len(vn_names)]
        store.add(make_entry(f"app-{i:04d}", f"{vn_name} {i:04d}"))
    return store


def test_search_1000_records_correctness_and_timing() -> None:
    store = _build_bulk_store()
    assert len(store.list()) == _RECORD_COUNT

    expected_count = _RECORD_COUNT // 4  # 1 trong 4 tên lặp vòng

    start = time.perf_counter()
    results_accented = store.search("Đỗ Chí Cường", limit=expected_count)
    elapsed_accented = time.perf_counter() - start

    start = time.perf_counter()
    results_unaccented = store.search("do chi cuong", limit=expected_count)
    elapsed_unaccented = time.perf_counter() - start

    assert len(results_accented) == expected_count
    # query có dấu và không dấu PHẢI trả đúng cùng tập kết quả
    assert {r.manifest.id for r in results_accented} == {
        r.manifest.id for r in results_unaccented
    }

    elapsed_ms_accented = elapsed_accented * 1000
    elapsed_ms_unaccented = elapsed_unaccented * 1000
    print(
        f"[PERF-02] search() trên {_RECORD_COUNT} record: "
        f"có dấu={elapsed_ms_accented:.2f}ms, không dấu={elapsed_ms_unaccented:.2f}ms "
        f"(target TARGET tham chiếu ≤300ms; container này không phải máy tham chiếu)."
    )

    # Ngưỡng rộng (2s) chỉ để bắt hồi quy thuật toán nghiêm trọng (vd O(n^2)
    # fold lại toàn bộ index mỗi ký tự query) — KHÔNG phải ngưỡng PERF-02 thật.
    assert elapsed_ms_accented < 2000
    assert elapsed_ms_unaccented < 2000


def test_search_1000_records_limit_applies_before_returning() -> None:
    store = _build_bulk_store()
    results = store.search("Đỗ Chí Cường", limit=10)
    assert len(results) == 10
