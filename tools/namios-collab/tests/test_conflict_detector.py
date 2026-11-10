# -*- coding: utf-8 -*-
"""Test Conflict Detector (NaMiCollab Giai đoạn 1) — base-hash vs current
hash trên một 'file chia sẻ' (mô phỏng SMB/WebDAV mount bằng tmp_path)."""
from __future__ import annotations

from namios_collab.conflict_detector import (
    ConflictStatus,
    compute_hash,
    detect,
    detect_from_disk,
    is_mergeable_format,
)
from namios_collab import _util


def test_is_mergeable_format():
    assert is_mergeable_format("GiaoAn.md") is True
    assert is_mergeable_format("GiaoAn.MD") is True  # không phân biệt hoa/thường
    assert is_mergeable_format("so_lieu.csv") is True
    assert is_mergeable_format("BaiGiang.docx") is False
    assert is_mergeable_format("BangTinh.xlsx") is False
    assert is_mergeable_format("HinhVe.png") is False


def test_clean_when_base_equals_current():
    report = detect("notes/giaoan.md", base_hash="sha256:aaa", current_hash="sha256:aaa")
    assert report.status is ConflictStatus.CLEAN
    assert "base == current" in report.detail


def test_clean_when_new_already_matches_current():
    """Hai người lưu cùng một nội dung mới -> không phải xung đột thật,
    chỉ là đổi đã được áp dụng rồi."""
    report = detect(
        "notes/giaoan.md",
        base_hash="sha256:aaa",
        current_hash="sha256:bbb",
        new_hash="sha256:bbb",
    )
    assert report.status is ConflictStatus.CLEAN


def test_needs_merge_for_text_like_formats():
    report = detect(
        "notes/giaoan.md",
        base_hash="sha256:aaa",
        current_hash="sha256:bbb",
        new_hash="sha256:ccc",
    )
    assert report.status is ConflictStatus.NEEDS_MERGE
    assert report.mergeable_format is True


def test_conflict_for_binary_office_container():
    report = detect(
        "hoadon/BaoCaoThang.xlsx",
        base_hash="sha256:aaa",
        current_hash="sha256:bbb",
        new_hash="sha256:ccc",
    )
    assert report.status is ConflictStatus.CONFLICT
    assert report.mergeable_format is False
    assert "container nhị phân" in report.detail


def test_conflict_when_shared_file_deleted():
    report = detect("hoadon/BaoCaoThang.xlsx", base_hash="sha256:aaa", current_hash=None)
    assert report.status is ConflictStatus.CONFLICT
    assert "xóa" in report.detail


def test_detect_from_disk_clean_roundtrip(tmp_path):
    shared = tmp_path / "GhiChuLop.md"
    shared.write_text("Buoi 1: on tap", encoding="utf-8")
    base_hash = compute_hash(str(shared))

    report = detect_from_disk(str(shared), base_hash)
    assert report.status is ConflictStatus.CLEAN


def test_detect_from_disk_needs_merge_after_concurrent_edit(tmp_path):
    shared = tmp_path / "GhiChuLop.md"
    shared.write_text("Buoi 1: on tap", encoding="utf-8")
    base_hash = compute_hash(str(shared))

    # "Người khác" sửa file trên kho chia sẻ sau khi mình đã checkout base.
    shared.write_text("Buoi 1: on tap\nBuoi 2: kiem tra 15 phut", encoding="utf-8")

    my_new_content = b"Buoi 1: on tap\nGhi chu rieng cua minh"
    my_new_hash = _util.sha256_bytes(my_new_content)

    report = detect_from_disk(str(shared), base_hash, my_new_hash)
    assert report.status is ConflictStatus.NEEDS_MERGE
    assert report.current_hash == compute_hash(str(shared))


def test_detect_from_disk_conflict_for_binary_after_concurrent_edit(tmp_path):
    shared = tmp_path / "BaoCaoThang.xlsx"
    shared.write_bytes(b"PK\x03\x04-fake-xlsx-bytes-v1")
    base_hash = compute_hash(str(shared))

    shared.write_bytes(b"PK\x03\x04-fake-xlsx-bytes-v2-tu-nguoi-khac")

    report = detect_from_disk(str(shared), base_hash, new_hash="sha256:gia-tri-cua-toi")
    assert report.status is ConflictStatus.CONFLICT


def test_detect_from_disk_missing_file_is_conflict(tmp_path):
    missing = tmp_path / "KhongTonTai.docx"
    report = detect_from_disk(str(missing), base_hash="sha256:aaa")
    assert report.status is ConflictStatus.CONFLICT
    assert report.current_hash is None
