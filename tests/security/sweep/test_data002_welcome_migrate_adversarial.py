"""DATA-002 + SEC-002 adversarial — ``namios_welcome.migrate``.

Positive (phong thu phai giu — DATA-002 P0):
  - KHONG ghi de file dich da ton tai (doi ten "(n)").
  - KHONG xoa/di chuyen nguon (luon la BAN SAO).
  - Chan doc khi phan vung co ``hiberfil.sys`` (hibernated/Fast Startup).
  - Khong sao chep file ten khop mau khoa khoi phuc BitLocker.

FINDING (SEC-002, giu lam bang chung — xem cuoi file):
  - ``migrate()`` dung ``resolve_within()`` CHI de tinh ``source_abs`` (mot
    chuoi path), roi mo THAT bang ``open(source_abs, "rb")`` (builtin, theo
    symlink mac dinh, khong phai ``open_within`` FD-based cua chinh module
    nay dung o PHIA DICH). Day la cua so TOCTOU kinh dien: ke tan cong
    thang race giua hai buoc co the doi file nguon thanh symlink tro ra
    NGOAI ``source_root``, khien ``migrate()`` sao chep du lieu tuy y
    (vd ``~/.ssh/id_rsa``, token trinh duyet) vao home nguoi dung duoi mot
    ten muc "Documents" trong khi nguoi dung tin la import Windows thong
    thuong."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from namios_welcome.migrate import WindowsDataMigrator, WindowsVolumeUnsafeError

# ---------------------------------------------------------------------------
# Positive — phong thu phai giu
# ---------------------------------------------------------------------------


def test_migrate_never_overwrites_existing_destination_file(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    (source_root / "Documents").mkdir(parents=True)
    (source_root / "Documents" / "report.txt").write_text("noi dung MOI tu Windows")

    dest_home = tmp_path / "dest"
    (dest_home / "Documents").mkdir(parents=True)
    (dest_home / "Documents" / "report.txt").write_text("noi dung CU da co tren NaMiOS")

    migrator = WindowsDataMigrator(source_root)
    report = migrator.migrate(dest_home)

    # File goc KHONG bi ghi de.
    assert (dest_home / "Documents" / "report.txt").read_text() == "noi dung CU da co tren NaMiOS"
    # Noi dung moi duoc luu voi ten khac, ghi nhan conflict.
    assert len(report.conflicts) == 1
    renamed = dest_home / "Documents" / report.conflicts[0].resolved_relative_path.split("/")[-1]
    assert renamed.exists()
    assert renamed.read_text() == "noi dung MOI tu Windows"


def test_migrate_never_deletes_or_moves_source_file(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    (source_root / "Desktop").mkdir(parents=True)
    source_file = source_root / "Desktop" / "shortcut.txt"
    source_file.write_text("van con o day")

    dest_home = tmp_path / "dest"
    migrator = WindowsDataMigrator(source_root)
    migrator.migrate(dest_home)

    assert source_file.exists()
    assert source_file.read_text() == "van con o day"


def test_migrate_rejects_hibernated_volume_and_copies_nothing(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    (source_root / "Documents").mkdir(parents=True)
    (source_root / "Documents" / "secret.txt").write_text("khong duoc doc")
    (source_root / "hiberfil.sys").write_bytes(b"\x00" * 16)

    dest_home = tmp_path / "dest"
    migrator = WindowsDataMigrator(source_root)

    with pytest.raises(WindowsVolumeUnsafeError):
        migrator.migrate(dest_home)

    assert not dest_home.exists() or not any(dest_home.rglob("*"))


def test_migrate_skips_bitlocker_recovery_key_filenames_without_copying_content(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    (source_root / "Documents").mkdir(parents=True)
    bek = source_root / "Documents" / "BitLockerRecoveryKey12345.txt"
    bek.write_text("RECOVERY-KEY-DO-NOT-LEAK")
    normal = source_root / "Documents" / "normal.txt"
    normal.write_text("ok to copy")

    dest_home = tmp_path / "dest"
    migrator = WindowsDataMigrator(source_root)
    report = migrator.migrate(dest_home)

    assert not (dest_home / "Documents" / "BitLockerRecoveryKey12345.txt").exists()
    assert (dest_home / "Documents" / "normal.txt").exists()
    assert any("khoi phuc" in s.reason_vi or "BitLocker" in s.reason_vi for s in report.skipped)


def test_migrate_does_not_follow_symlinked_files_inside_category(tmp_path: Path) -> None:
    """File (khong phai thu muc trung gian) la symlink ben trong category —
    ``_iter_category_files`` chu dong bo qua (``is_symlink()``), phong thu
    nay RIENG vẫn giu (khac voi finding TOCTOU ben duoi, noi file goc la
    file THUONG luc duyet roi bi doi SAU khi resolve)."""

    source_root = tmp_path / "src"
    (source_root / "Documents").mkdir(parents=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("khong duoc copy qua symlink tinh")
    link = source_root / "Documents" / "link.txt"
    os.symlink(outside, link)

    dest_home = tmp_path / "dest"
    migrator = WindowsDataMigrator(source_root)
    report = migrator.migrate(dest_home)

    assert report.files_copied == 0
    assert not (dest_home / "Documents" / "link.txt").exists()


# ---------------------------------------------------------------------------
# FINDING — xem docstring dau file.
# ---------------------------------------------------------------------------


def test_migrate_toctou_source_file_swapped_to_symlink_leaks_outside_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import namios_welcome.migrate as migrate_mod

    source_root = tmp_path / "src"
    dest_home = tmp_path / "dest"
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("ATTACKER CONTROLLED SECRET CONTENT")

    (source_root / "Documents").mkdir(parents=True)
    victim_file = source_root / "Documents" / "report.txt"
    victim_file.write_text("original safe content")

    migrator = migrate_mod.WindowsDataMigrator(source_root)

    orig_resolve = migrate_mod.resolve_within

    def evil_resolve_within(base, candidate):
        result = orig_resolve(base, candidate)
        if candidate == "report.txt":
            # Attacker thang race NGAY SAU khi resolve_within() xac nhan an
            # toan nhung TRUOC khi migrate.py mo file thuc su bang open().
            os.remove(result)
            os.symlink(str(outside), result)
        return result

    monkeypatch.setattr(migrate_mod, "resolve_within", evil_resolve_within)

    report = migrator.migrate(dest_home)
    copied = dest_home / "Documents" / "report.txt"

    assert not copied.exists() or copied.read_text() != "ATTACKER CONTROLLED SECRET CONTENT", (
        "VULNERABLE: migrate() da sao chep noi dung tu NGOAI source_root "
        f"qua TOCTOU symlink-swap. report={report}"
    )
