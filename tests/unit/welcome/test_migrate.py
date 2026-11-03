"""Test logic ``WindowsDataMigrator`` — copy-with-report, không ghi đè,
conflict → rename có log, từ chối path traversal/symlink, từ chối volume
hibernated/lỗi. KHÔNG dùng GUI."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from namios_security import PathUnsafeError
from namios_welcome.migrate import WindowsDataMigrator, WindowsVolumeUnsafeError


def _make_source_profile(root: Path) -> Path:
    """Tạo cây thư mục giả lập profile Windows với 4 thư mục quen thuộc."""

    for name in ("Documents", "Desktop", "Downloads", "Pictures"):
        (root / name).mkdir(parents=True)
    (root / "Documents" / "bao-cao.docx").write_text("noi dung bao cao")
    (root / "Documents" / "con" / "phu").mkdir(parents=True)
    (root / "Documents" / "con" / "phu" / "ghi-chu.txt").write_text("ghi chu")
    (root / "Desktop" / "shortcut.txt").write_text("shortcut")
    (root / "Downloads" / "file.zip").write_bytes(b"\x00\x01\x02")
    (root / "Pictures" / "anh.jpg").write_bytes(b"\xff\xd8\xff")
    return root


# --- discover_folders ---------------------------------------------------


def test_discover_folders_finds_all_four_known_categories(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    migrator = WindowsDataMigrator(source)

    found = {f.category for f in migrator.discover_folders()}

    assert found == {"Documents", "Desktop", "Downloads", "Pictures"}


def test_discover_folders_falls_back_to_users_subdirectory(tmp_path: Path) -> None:
    drive_root = tmp_path / "mnt-windows"
    profile = drive_root / "Users" / "Cuong"
    _make_source_profile(profile)

    migrator = WindowsDataMigrator(drive_root)

    found = {f.category for f in migrator.discover_folders()}
    assert found == {"Documents", "Desktop", "Downloads", "Pictures"}


def test_discover_folders_returns_empty_when_nothing_found(tmp_path: Path) -> None:
    empty_root = tmp_path / "empty"
    empty_root.mkdir()

    migrator = WindowsDataMigrator(empty_root)

    assert migrator.discover_folders() == ()


def test_constructor_rejects_nonexistent_source_root(tmp_path: Path) -> None:
    with pytest.raises(WindowsVolumeUnsafeError):
        WindowsDataMigrator(tmp_path / "khong-ton-tai")


# --- migrate: copy-with-report -----------------------------------------


def test_migrate_copies_all_files_with_accurate_report(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    dest = tmp_path / "home" / "nguoidung"
    migrator = WindowsDataMigrator(source)

    report = migrator.migrate(dest)

    assert report.files_copied == 5
    assert report.bytes_copied == sum(e.size_bytes for e in report.copied_files)
    assert set(report.categories_found) == {"Documents", "Desktop", "Downloads", "Pictures"}
    assert (dest / "Documents" / "bao-cao.docx").read_text() == "noi dung bao cao"
    assert (dest / "Documents" / "con" / "phu" / "ghi-chu.txt").read_text() == "ghi chu"
    assert (dest / "Pictures" / "anh.jpg").read_bytes() == b"\xff\xd8\xff"
    assert report.skipped == ()
    assert report.conflicts == ()


def test_migrate_never_deletes_or_moves_source_files(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    dest = tmp_path / "home" / "nguoidung"
    migrator = WindowsDataMigrator(source)

    migrator.migrate(dest)

    assert (source / "Documents" / "bao-cao.docx").exists()
    assert (source / "Documents" / "bao-cao.docx").read_text() == "noi dung bao cao"
    assert (source / "Desktop" / "shortcut.txt").exists()


def test_migrate_filters_by_categories(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    dest = tmp_path / "home" / "nguoidung"
    migrator = WindowsDataMigrator(source)

    report = migrator.migrate(dest, categories=["Pictures"])

    assert report.categories_found == ("Pictures",)
    assert report.files_copied == 1
    assert not (dest / "Documents").exists()
    assert (dest / "Pictures" / "anh.jpg").exists()


def test_migrate_skips_bitlocker_recovery_key_filenames(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    (source / "Documents" / "BitLockerRecoveryKey12345.TXT").write_text("key content do not copy")
    (source / "Documents" / "secret.bek").write_bytes(b"bek-content")
    dest = tmp_path / "home" / "nguoidung"
    migrator = WindowsDataMigrator(source)

    report = migrator.migrate(dest)

    skipped_names = {e.relative_path for e in report.skipped}
    assert "BitLockerRecoveryKey12345.TXT" in skipped_names
    assert "secret.bek" in skipped_names
    assert not (dest / "Documents" / "BitLockerRecoveryKey12345.TXT").exists()
    assert not (dest / "Documents" / "secret.bek").exists()
    # Báo cáo không chứa nội dung file, chỉ tên quan hệ + lý do.
    for entry in report.skipped:
        assert "key content" not in entry.reason_vi
        assert "bek-content" not in str(entry)


# --- không ghi đè + conflict rename -------------------------------------


def test_migrate_does_not_overwrite_existing_destination_file(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    dest = tmp_path / "home" / "nguoidung"
    (dest / "Documents").mkdir(parents=True)
    (dest / "Documents" / "bao-cao.docx").write_text("DU LIEU CU CUA NGUOI DUNG - KHONG MAT")

    migrator = WindowsDataMigrator(source)
    report = migrator.migrate(dest)

    # File cũ của người dùng ở đích không bị ghi đè.
    kept_text = (dest / "Documents" / "bao-cao.docx").read_text()
    assert kept_text == "DU LIEU CU CUA NGUOI DUNG - KHONG MAT"
    # Nội dung mới từ Windows được giữ lại dưới tên đã đổi, có ghi log conflict.
    assert len(report.conflicts) == 1
    conflict = report.conflicts[0]
    assert conflict.relative_path == "bao-cao.docx"
    assert conflict.resolved_relative_path == "Documents/bao-cao (1).docx"
    renamed_path = dest / "Documents" / "bao-cao (1).docx"
    assert renamed_path.read_text() == "noi dung bao cao"
    assert report.files_copied == 5


# --- path traversal / symlink -------------------------------------------


def test_discover_folders_rejects_symlink_category(tmp_path: Path) -> None:
    source = tmp_path / "winprofile"
    source.mkdir()
    outside = tmp_path / "outside-secret"
    outside.mkdir()
    (outside / "nhay.txt").write_text("khong duoc doc")
    os.symlink(outside, source / "Documents")

    migrator = WindowsDataMigrator(source)

    found = migrator.discover_folders()
    assert found == ()


def test_migrate_skips_symlinked_file_inside_category(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    outside_secret = tmp_path / "ngoai-pham-vi.txt"
    outside_secret.write_text("khong duoc copy")
    os.symlink(outside_secret, source / "Documents" / "lien-ket.txt")

    dest = tmp_path / "home" / "nguoidung"
    migrator = WindowsDataMigrator(source)

    report = migrator.migrate(dest)

    assert not (dest / "Documents" / "lien-ket.txt").exists()
    assert "lien-ket.txt" not in {e.relative_path for e in report.copied_files}


def test_resolve_within_rejects_traversal_component_directly(tmp_path: Path) -> None:
    """``resolve_within`` (dùng nội bộ bởi migrate) từ chối '..' — chứng
    minh hành vi nền mà ``WindowsDataMigrator`` dựa vào."""

    with pytest.raises(PathUnsafeError):
        from namios_security import resolve_within

        resolve_within(str(tmp_path), "../etc/passwd")


# --- hibernated / Fast Startup / volume lỗi ------------------------------


def test_check_volume_safety_rejects_hiberfil_marker(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    (source / "hiberfil.sys").write_bytes(b"\x00" * 16)

    migrator = WindowsDataMigrator(source)

    with pytest.raises(WindowsVolumeUnsafeError, match="hiberfil"):
        migrator.check_volume_safety()


def test_migrate_refuses_when_hibernated_and_copies_nothing(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    (source / "hiberfil.sys").write_bytes(b"\x00" * 16)
    dest = tmp_path / "home" / "nguoidung"

    migrator = WindowsDataMigrator(source)
    with pytest.raises(WindowsVolumeUnsafeError):
        migrator.migrate(dest)

    assert not dest.exists() or list(dest.iterdir()) == []


def test_check_volume_safety_rejects_unreadable_volume_as_faulty(tmp_path: Path) -> None:
    source = _make_source_profile(tmp_path / "winprofile")
    migrator = WindowsDataMigrator(source)
    os.chmod(source, 0o000)
    try:
        with pytest.raises(WindowsVolumeUnsafeError, match="lỗi|truy cập"):
            migrator.check_volume_safety()
    finally:
        os.chmod(source, 0o700)
