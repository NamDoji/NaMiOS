"""SAI-018/020 — capsule: bản gốc bất biến + rollback + supply-chain."""

from __future__ import annotations

import pytest

from namios_smartai.capsule import apply_change, check_supply_chain, make_capsule, rollback


def test_original_capsule_immutable() -> None:
    base = make_capsule("misa", capsule_id="c0", snapshot_id="s0")
    changed = apply_change(base, "set win10 mode")
    assert base.mutations == ()  # bản gốc KHÔNG đổi
    assert changed.mutations == ("set win10 mode",)
    assert changed is not base


def test_rollback_restores_and_blocks_further_change() -> None:
    base = make_capsule("misa", capsule_id="c0", snapshot_id="s0")
    changed = apply_change(base, "a")
    rolled = rollback(changed)
    assert rolled.rolled_back is True
    assert rolled.mutations == ()
    with pytest.raises(ValueError):
        apply_change(rolled, "b")  # không thử tiếp trên capsule đã rollback


def test_supply_chain_flags_http_and_missing_hash() -> None:
    probs = check_supply_chain("http://evil.example/x.exe", "")
    assert probs  # http + thiếu hash → có vấn đề
    assert (
        check_supply_chain("https://misa.vn/x.exe", "sha256:aa", official_hosts=("misa.vn",)) == []
    )


def test_supply_chain_rejects_unofficial_domain() -> None:
    probs = check_supply_chain(
        "https://evil.example/x.exe", "sha256:aa", official_hosts=("misa.vn",)
    )
    assert any("miền" in p for p in probs)
