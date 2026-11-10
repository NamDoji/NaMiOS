# -*- coding: utf-8 -*-
"""Test LockManager (NaMiCollab Giai đoạn 1) — exclusive/shared, stale-lock,
và hai 'người dùng' giành khóa đồng thời (mô phỏng race bằng threading)."""
from __future__ import annotations

import os
import threading
import time

import pytest

from namios_collab.lock_manager import (
    LockConflictError,
    LockHolder,
    LockManager,
    LockMode,
    LockNotHeldError,
)
from namios_collab import _util


@pytest.fixture()
def target_file(tmp_path):
    p = tmp_path / "BaoCaoThuChi.odt"
    p.write_bytes(b"noi dung ban dau")
    return str(p)


@pytest.fixture()
def mgr():
    return LockManager(mutex_timeout_seconds=2.0)


def test_exclusive_blocks_exclusive(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE)
    with pytest.raises(LockConflictError) as exc:
        mgr.acquire(target_file, "giaovien_b", LockMode.EXCLUSIVE)
    assert exc.value.requested_mode is LockMode.EXCLUSIVE
    assert exc.value.holders[0].owner == "giaovien_a"
    mgr.release(handle_a)


def test_exclusive_blocks_shared(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE)
    with pytest.raises(LockConflictError):
        mgr.acquire(target_file, "giaovien_b", LockMode.SHARED)
    mgr.release(handle_a)


def test_shared_allows_multiple_shared_readers(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.SHARED)
    handle_b = mgr.acquire(target_file, "giaovien_b", LockMode.SHARED)
    status = mgr.status(target_file)
    assert status.is_locked
    assert not status.is_exclusive
    assert {h.owner for h in status.holders} == {"giaovien_a", "giaovien_b"}
    mgr.release(handle_a)
    mgr.release(handle_b)
    assert not mgr.status(target_file).is_locked


def test_shared_blocks_exclusive(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.SHARED)
    with pytest.raises(LockConflictError):
        mgr.acquire(target_file, "giaovien_b", LockMode.EXCLUSIVE)
    mgr.release(handle_a)
    # Sau khi trả shared duy nhất, exclusive mới phải lấy được.
    handle_c = mgr.acquire(target_file, "giaovien_c", LockMode.EXCLUSIVE)
    mgr.release(handle_c)


def test_release_frees_lock_for_next_acquirer(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE)
    mgr.release(handle_a)
    handle_b = mgr.acquire(target_file, "giaovien_b", LockMode.EXCLUSIVE)
    assert handle_b.owner == "giaovien_b"
    mgr.release(handle_b)


def test_release_with_wrong_token_raises(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE)
    forged = handle_a.__class__(
        path=handle_a.path,
        token="token-gia-mao-0000",
        owner=handle_a.owner,
        mode=handle_a.mode,
        acquired_ns=handle_a.acquired_ns,
        lease_seconds=handle_a.lease_seconds,
    )
    with pytest.raises(LockNotHeldError):
        mgr.release(forged)
    mgr.release(handle_a)  # token thật vẫn release được


def test_double_release_raises(mgr, target_file):
    handle_a = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE)
    mgr.release(handle_a)
    with pytest.raises(LockNotHeldError):
        mgr.release(handle_a)


def test_stale_lock_by_dead_pid_is_auto_broken_on_acquire(mgr, target_file):
    """Craft một holder 'mồ côi': cùng host, pid chắc chắn không tồn tại,
    lease còn hạn (chưa hết lease) — vẫn phải bị coi là stale và dọn, vì
    tiêu chí stale là OR giữa 'lease hết hạn' và 'cùng host + pid chết'."""
    dead_pid = 2**30 - 1  # PID cực lớn, không tồn tại trên hệ thống thật
    sidecar = target_file + ".namilock.json"
    orphan = LockHolder(
        token="orphan-token",
        owner="giaovien_crash",
        mode=LockMode.EXCLUSIVE,
        acquired_ns=_util.now_ns(),
        lease_seconds=600.0,  # lease vẫn còn hạn theo thời gian
        pid=dead_pid,
        hostname=_util.hostname(),
    )
    _util.atomic_write_json(sidecar, {"path": target_file, "holders": [orphan.to_dict()]})

    status_before = mgr.status(target_file, drop_stale=False)
    assert status_before.is_locked  # sidecar có holder (chưa dọn)

    # acquire mới phải thành công vì holder cũ là stale (pid chết)
    handle_new = mgr.acquire(target_file, "giaovien_moi", LockMode.EXCLUSIVE)
    assert handle_new.owner == "giaovien_moi"
    mgr.release(handle_new)


def test_stale_lock_by_expired_lease_is_broken_explicitly(mgr, target_file):
    sidecar = target_file + ".namilock.json"
    expired = LockHolder(
        token="expired-token",
        owner="giaovien_het_han",
        mode=LockMode.EXCLUSIVE,
        acquired_ns=_util.now_ns() - int(3600 * 1e9),  # 1 giờ trước
        lease_seconds=1.0,  # lease 1s -> đã hết hạn từ lâu
        pid=_util.pid(),  # pid HIỆN TẠI còn sống, chỉ lease hết hạn mới tính stale
        hostname=_util.hostname(),
    )
    _util.atomic_write_json(sidecar, {"path": target_file, "holders": [expired.to_dict()]})

    broken = mgr.break_stale(target_file)
    assert len(broken) == 1
    assert broken[0].owner == "giaovien_het_han"
    assert not mgr.status(target_file).is_locked


def test_two_users_race_exactly_one_exclusive_winner(mgr, target_file):
    """Mô phỏng hai 'người dùng' (hai luồng) cùng bấm 'mở để sửa' (exclusive)
    trên CÙNG một file ở gần như cùng thời điểm. Gate mutex O_CREAT|O_EXCL
    trong LockManager phải đảm bảo CHỈ MỘT thắng, không có tình trạng cả
    hai đều tưởng mình đã giành khóa (double-grant)."""
    results: dict[str, object] = {}
    start_barrier = threading.Barrier(2)

    def try_acquire(owner: str):
        start_barrier.wait()
        try:
            handle = mgr.acquire(target_file, owner, LockMode.EXCLUSIVE)
            results[owner] = handle
        except LockConflictError as exc:
            results[owner] = exc

    threads = [
        threading.Thread(target=try_acquire, args=("giaovien_a",)),
        threading.Thread(target=try_acquire, args=("giaovien_b",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    winners = [v for v in results.values() if not isinstance(v, Exception)]
    losers = [v for v in results.values() if isinstance(v, Exception)]
    assert len(winners) == 1, f"phải đúng 1 người thắng, thực tế: {results}"
    assert len(losers) == 1
    assert isinstance(losers[0], LockConflictError)

    # Dọn để không rò khóa sang test khác.
    mgr.release(winners[0])


def test_many_racing_shared_acquirers_all_succeed(mgr, target_file):
    """Nhiều 'người xem' (shared) cùng lúc không được chặn lẫn nhau."""
    n = 8
    handles: list = []
    lock = threading.Lock()
    start_barrier = threading.Barrier(n)

    def try_acquire(idx: int):
        start_barrier.wait()
        h = mgr.acquire(target_file, f"doc_vien_{idx}", LockMode.SHARED)
        with lock:
            handles.append(h)

    threads = [threading.Thread(target=try_acquire, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(handles) == n
    status = mgr.status(target_file)
    assert len(status.holders) == n
    assert not status.is_exclusive
    for h in handles:
        mgr.release(h)
    assert not mgr.status(target_file).is_locked


def test_sidecar_path_is_next_to_target_file(mgr, target_file):
    handle = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE)
    assert os.path.exists(target_file + ".namilock.json")
    mgr.release(handle)
    # Sidecar bị dọn khi không còn holder nào (không rò file rác).
    assert not os.path.exists(target_file + ".namilock.json")


def test_lease_seconds_override(mgr, target_file):
    handle = mgr.acquire(target_file, "giaovien_a", LockMode.EXCLUSIVE, lease_seconds=0.05)
    time.sleep(0.2)
    # Lease đã hết hạn -> người khác giành được ngay, không cần release thủ công.
    handle_b = mgr.acquire(target_file, "giaovien_b", LockMode.EXCLUSIVE)
    assert handle_b.owner == "giaovien_b"
    mgr.release(handle_b)
    with pytest.raises(LockNotHeldError):
        mgr.release(handle)  # token cũ đã bị dọn khỏi sidecar từ lâu
