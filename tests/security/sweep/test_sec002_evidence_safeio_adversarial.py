"""SEC-002 + DoS adversarial — ``namios_evidence._safe_io.read_text_safe``.

Mục tiêu: xác nhận module này THỰC SỰ ủy quyền cho ``namios_security``
(FD-based) như docstring khai báo, chứ không tự chế một lớp yếu hơn — khác
với ``namios_manifest._safe_io`` và ``namios_welcome.migrate`` (xem file
finding riêng)."""

from __future__ import annotations

import os

import pytest

from namios_evidence._safe_io import PathUnsafeError, read_text_safe


def test_rejects_relative_path() -> None:
    with pytest.raises(PathUnsafeError):
        read_text_safe("relative/evidence.json")


def test_rejects_nul_byte_in_path(tmp_path) -> None:
    with pytest.raises(PathUnsafeError):
        read_text_safe(str(tmp_path / "evi\x00dence.json"))


def test_rejects_dotdot_traversal_escaping_allowed_root(tmp_path) -> None:
    allowed_root = tmp_path / "evidence_store"
    allowed_root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"leak": true}')

    traversal_path = str(allowed_root / ".." / "outside.json")
    with pytest.raises(PathUnsafeError):
        read_text_safe(traversal_path)


def test_rejects_leaf_symlink_pointing_outside_directory(tmp_path) -> None:
    directory = tmp_path / "evidence_store"
    directory.mkdir()
    outside = tmp_path / "secret_outside.json"
    outside.write_text('{"secret": "should not leak"}')
    link = directory / "report.json"
    os.symlink(outside, link)

    with pytest.raises(PathUnsafeError):
        read_text_safe(str(link))


def test_rejects_intermediate_symlink_directory(tmp_path) -> None:
    real_dir = tmp_path / "real_evidence"
    real_dir.mkdir()
    (real_dir / "report.json").write_text('{"ok": true}')

    evil_link_dir = tmp_path / "linked_evidence"
    os.symlink(real_dir, evil_link_dir)

    # Đọc THẲNG qua chính symlink thư mục (evidence dir gốc là symlink) —
    # realpath(base) != abspath(base) phải bị chặn.
    with pytest.raises(PathUnsafeError):
        read_text_safe(str(evil_link_dir / "report.json"))


def test_rejects_file_over_2mib_dos_guard(tmp_path) -> None:
    directory = tmp_path / "evidence_store"
    directory.mkdir()
    huge = directory / "huge_report.json"
    # 2 MiB + 1 byte — vượt đúng 1 byte so với giới hạn mặc định.
    huge.write_bytes(b"0" * (2 * 1024 * 1024 + 1))

    with pytest.raises(PathUnsafeError):
        read_text_safe(str(huge))


def test_accepts_file_exactly_at_2mib_limit(tmp_path) -> None:
    directory = tmp_path / "evidence_store"
    directory.mkdir()
    exact = directory / "exact_report.json"
    exact.write_bytes(b"0" * (2 * 1024 * 1024))

    content = read_text_safe(str(exact))
    assert len(content) == 2 * 1024 * 1024


def test_rejects_non_regular_file_fifo_without_hanging_process(tmp_path) -> None:
    directory = tmp_path / "evidence_store"
    directory.mkdir()
    fifo_path = directory / "pipe_report.json"
    os.mkfifo(fifo_path)

    script = (
        "import sys\n"
        "from namios_evidence._safe_io import PathUnsafeError, read_text_safe\n"
        "try:\n"
        "    read_text_safe(sys.argv[1])\n"
        "except PathUnsafeError:\n"
        "    print('REJECTED')\n"
        "else:\n"
        "    print('ACCEPTED-UNSAFE')\n"
    )
    import subprocess
    import sys

    try:
        # argv-only, shell=False, sys.executable + inline script co dinh
        # (khong noi chuoi tu input ben ngoai) -- chi fifo_path (do test tu
        # tao trong tmp_path) duoc truyen nhu mot argv rieng.
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", script, str(fifo_path)],
            capture_output=True,
            text=True,
            timeout=3.0,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            "VULNERABLE: mo FIFO qua open_within() treo vo han (DoS) thay vi "
            "bi tu choi nhanh nhu mot non-regular file."
        )
    assert (
        result.stdout.strip() == "REJECTED"
    ), f"VULNERABLE hoac loi khac: stdout={result.stdout!r} stderr={result.stderr!r}"


def test_rejects_invalid_utf8_content(tmp_path) -> None:
    directory = tmp_path / "evidence_store"
    directory.mkdir()
    bad = directory / "bad_encoding.json"
    bad.write_bytes(b"\xff\xfe\x00broken")

    with pytest.raises(PathUnsafeError):
        read_text_safe(str(bad))
