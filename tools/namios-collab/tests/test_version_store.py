# -*- coding: utf-8 -*-
"""Test LocalVersionHistory (NaMiCollab Giai đoạn 1) — snapshot/list/restore
với verify hash, và nguyên tắc 'never overwrite without a snapshot'."""
from __future__ import annotations

import os

import pytest

from namios_collab.version_store import (
    LocalVersionHistory,
    RestoreVerificationError,
    VersionNotFoundError,
)
from namios_collab import _util


@pytest.fixture()
def target_file(tmp_path):
    p = tmp_path / "GiaoAnToan.odt"
    p.write_bytes(b"noi dung phien ban 1")
    return str(p)


@pytest.fixture()
def history():
    return LocalVersionHistory(mutex_timeout_seconds=2.0)


def test_snapshot_missing_file_raises(history, tmp_path):
    with pytest.raises(FileNotFoundError):
        history.snapshot(str(tmp_path / "khong_ton_tai.odt"))


def test_snapshot_and_list_roundtrip(history, target_file):
    entry = history.snapshot(target_file, label="ban dau")
    assert entry.version_id == "v1"
    assert entry.sha256 == _util.sha256_file(target_file)
    versions = history.list_versions(target_file)
    assert len(versions) == 1
    assert versions[0].label == "ban dau"


def test_multiple_snapshots_increment_version_id(history, target_file):
    history.snapshot(target_file, label="v1")
    with open(target_file, "ab") as fh:
        fh.write(b" - sua lan 2")
    history.snapshot(target_file, label="v2")
    with open(target_file, "ab") as fh:
        fh.write(b" - sua lan 3")
    history.snapshot(target_file, label="v3")

    versions = history.list_versions(target_file)
    assert [v.version_id for v in versions] == ["v1", "v2", "v3"]
    assert [v.label for v in versions] == ["v1", "v2", "v3"]
    # Mỗi version phải có hash khác nhau vì nội dung khác nhau.
    assert len({v.sha256 for v in versions}) == 3


def test_read_version_bytes_matches_snapshot_content(history, target_file):
    original = open(target_file, "rb").read()
    entry = history.snapshot(target_file)
    data = history.read_version_bytes(target_file, entry.version_id)
    assert data == original


def test_read_version_bytes_detects_corruption(history, target_file):
    entry = history.snapshot(target_file)
    history_dir = target_file + ".namihistory"
    snapshot_path = os.path.join(history_dir, entry.snapshot_file)
    with open(snapshot_path, "wb") as fh:
        fh.write(b"DU LIEU DA BI HONG TREN DIA")

    with pytest.raises(RestoreVerificationError):
        history.read_version_bytes(target_file, entry.version_id)


def test_get_version_unknown_id_raises(history, target_file):
    history.snapshot(target_file)
    with pytest.raises(VersionNotFoundError):
        history.get_version(target_file, "v999")


def test_restore_round_trip_with_hash_check(history, target_file):
    v1 = history.snapshot(target_file, label="ban goc")
    v1_bytes = open(target_file, "rb").read()

    # "Sửa" file thành phiên bản 2.
    with open(target_file, "wb") as fh:
        fh.write(b"noi dung phien ban 2 - da sua")
    history.snapshot(target_file, label="sau khi sua")

    # Phải khác nội dung v1 trước khi restore.
    assert open(target_file, "rb").read() != v1_bytes

    restored_entry, safety_entry = history.restore(target_file, v1.version_id)
    assert restored_entry.version_id == v1.version_id
    assert open(target_file, "rb").read() == v1_bytes
    assert _util.sha256_file(target_file) == v1.sha256

    # restore() phải tự chụp safety snapshot cho trạng thái trước khi ghi đè
    # (nguyên tắc 'never overwrite without a snapshot').
    assert safety_entry is not None
    assert safety_entry.reason == "pre-restore-safety"
    versions_after = history.list_versions(target_file)
    assert any(v.version_id == safety_entry.version_id for v in versions_after)


def test_restore_safety_snapshot_preserves_pre_restore_content(history, target_file):
    v1 = history.snapshot(target_file)
    pre_restore_bytes = b"noi dung bi mat neu khong co safety snapshot"
    with open(target_file, "wb") as fh:
        fh.write(pre_restore_bytes)

    _restored, safety_entry = history.restore(target_file, v1.version_id)
    assert safety_entry is not None
    # Nội dung ngay trước khi restore phải lấy lại được từ safety snapshot —
    # chứng minh KHÔNG mất dữ liệu dù restore đã ghi đè file.
    recovered = history.read_version_bytes(target_file, safety_entry.version_id)
    assert recovered == pre_restore_bytes


def test_restore_skips_safety_snapshot_when_current_already_matches_target(history, target_file):
    v1 = history.snapshot(target_file)
    # Không sửa gì — file hiện tại đã khớp đúng bản muốn restore.
    _restored, safety_entry = history.restore(target_file, v1.version_id)
    assert safety_entry is None  # không có gì để mất -> không chụp thêm bản trùng


def test_restore_unknown_version_raises(history, target_file):
    history.snapshot(target_file)
    with pytest.raises(VersionNotFoundError):
        history.restore(target_file, "v999")


def test_restore_detects_write_corruption(history, target_file, monkeypatch):
    v1 = history.snapshot(target_file)
    with open(target_file, "wb") as fh:
        fh.write(b"phien ban khac de co safety snapshot")
    history.snapshot(target_file)

    # Giả lập ghi bị hỏng: sau atomic_write_bytes, file trên đĩa không khớp
    # hash kỳ vọng (vd lỗi phần cứng/race ngoài tầm kiểm soát). Patch
    # sha256_file để lần gọi THỨ HAI (verify sau khi ghi) trả hash sai.
    real_sha256_file = _util.sha256_file
    calls = {"n": 0}

    def flaky_sha256_file(path):
        calls["n"] += 1
        # restore() gọi sha256_file đúng 2 lần: (1) kiểm current_hash để quyết
        # định có cần safety snapshot, (2) verify hash SAU khi ghi đè. Để
        # lần (1) trả hash thật (quyết định safety snapshot đúng logic bình
        # thường) và chỉ giả lập lỗi ở lần (2) — đúng chỗ verify cuối cùng.
        if calls["n"] >= 2:
            return "sha256:gia-tri-sai-gia-lap-loi-ghi"
        return real_sha256_file(path)

    monkeypatch.setattr(_util, "sha256_file", flaky_sha256_file)
    with pytest.raises(RestoreVerificationError):
        history.restore(target_file, v1.version_id)


def test_purge_history_removes_sidecar_dir(history, target_file):
    history.snapshot(target_file)
    history_dir = target_file + ".namihistory"
    assert os.path.isdir(history_dir)
    history.purge_history(target_file)
    assert not os.path.isdir(history_dir)
    assert not os.path.exists(target_file + ".namihistory.gate")
    # File gốc không bị động tới.
    assert os.path.isfile(target_file)
