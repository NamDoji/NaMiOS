"""Unit test WP8 — ``namios_security.safe_path`` (SEC-02, SEC-03)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from namios_security import PathUnsafeError, SafePathImpl, open_within, resolve_within


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    base = tmp_path / "base"
    base.mkdir()
    return base


def test_resolve_within_happy_path_simple_file(base_dir: Path) -> None:
    (base_dir / "ok.txt").write_text("hello")
    result = resolve_within(str(base_dir), "ok.txt")
    assert result == str((base_dir / "ok.txt").resolve())


def test_resolve_within_nested_dirs(base_dir: Path) -> None:
    (base_dir / "a" / "b").mkdir(parents=True)
    (base_dir / "a" / "b" / "c.txt").write_text("x")
    result = resolve_within(str(base_dir), "a/b/c.txt")
    assert result == str((base_dir / "a" / "b" / "c.txt").resolve())


def test_resolve_within_nonexistent_leaf_ok_for_future_create(base_dir: Path) -> None:
    (base_dir / "sub").mkdir()
    result = resolve_within(str(base_dir), "sub/new-file.txt")
    assert result == str(base_dir / "sub" / "new-file.txt")


# --- Negative: traversal -------------------------------------------------


def test_resolve_within_rejects_parent_traversal(base_dir: Path) -> None:
    with pytest.raises(PathUnsafeError) as exc_info:
        resolve_within(str(base_dir), "../outside.txt")
    assert exc_info.value.code.value == "E_PATH_UNSAFE"


def test_resolve_within_rejects_deep_parent_traversal(base_dir: Path) -> None:
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "a/../../outside.txt")


def test_resolve_within_rejects_absolute_candidate(base_dir: Path, tmp_path: Path) -> None:
    outside = tmp_path / "etc-passwd-like"
    outside.write_text("secret")
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), str(outside))


def test_resolve_within_rejects_empty_candidate(base_dir: Path) -> None:
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "")
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), ".")


# --- Negative: symlink escape -------------------------------------------


def test_resolve_within_rejects_symlink_leaf_escaping_base(base_dir: Path, tmp_path: Path) -> None:
    outside_secret = tmp_path / "outside-secret.txt"
    outside_secret.write_text("top secret")
    evil_link = base_dir / "evil-link.txt"
    evil_link.symlink_to(outside_secret)

    with pytest.raises(PathUnsafeError) as exc_info:
        resolve_within(str(base_dir), "evil-link.txt")
    assert exc_info.value.code.value == "E_PATH_UNSAFE"


def test_resolve_within_rejects_symlink_intermediate_dir_escaping_base(
    base_dir: Path, tmp_path: Path
) -> None:
    outside_dir = tmp_path / "outside-dir"
    outside_dir.mkdir()
    (outside_dir / "secret.txt").write_text("leak")

    evil_dir_link = base_dir / "evil-dir"
    evil_dir_link.symlink_to(outside_dir)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "evil-dir/secret.txt")


def test_open_within_rejects_symlink_leaf(base_dir: Path, tmp_path: Path) -> None:
    outside_secret = tmp_path / "outside-secret-2.txt"
    outside_secret.write_text("top secret")
    evil_link = base_dir / "evil-link-2.txt"
    evil_link.symlink_to(outside_secret)

    with pytest.raises(PathUnsafeError):
        open_within(str(base_dir), "evil-link-2.txt", "rb")


def test_open_within_toctou_symlink_swap_after_walk_still_blocked(
    base_dir: Path, tmp_path: Path
) -> None:
    """Mô phỏng TOCTOU: thư mục trung gian hợp lệ lúc đầu, bị đổi thành
    symlink trỏ ra ngoài NGAY TRƯỚC lần mở — ``open_within`` làm lại toàn bộ
    walk mỗi lần gọi (không cache path string), nên vẫn bị chặn ở bước mở
    thành phần đó với ``O_NOFOLLOW``."""

    real_sub = base_dir / "sub"
    real_sub.mkdir()
    (real_sub / "file.txt").write_text("a")

    # Lần gọi đầu hợp lệ.
    assert open_within(str(base_dir), "sub/file.txt", "rb").read() == b"a"

    # Kẻ tấn công đổi 'sub' thành symlink ra ngoài.
    outside_dir = tmp_path / "outside-swap"
    outside_dir.mkdir()
    (outside_dir / "file.txt").write_text("evil")

    import shutil

    shutil.rmtree(real_sub)
    (base_dir / "sub").symlink_to(outside_dir)

    with pytest.raises(PathUnsafeError):
        open_within(str(base_dir), "sub/file.txt", "rb")


# --- Negative: hardlink defense (write only) -----------------------------


def test_open_within_write_rejects_existing_file_with_extra_hardlink(
    base_dir: Path, tmp_path: Path
) -> None:
    target = base_dir / "shared.txt"
    target.write_text("data")
    # Tạo hardlink thứ hai trỏ cùng inode (ngoài base) — nlink sẽ > 1.
    other_link = tmp_path / "shared-hardlink.txt"
    os.link(target, other_link)

    with pytest.raises(PathUnsafeError) as exc_info:
        open_within(str(base_dir), "shared.txt", "wb")
    assert "hardlink" in exc_info.value.reason_vi


def test_open_within_write_allows_fresh_file_without_hardlink(base_dir: Path) -> None:
    f = open_within(str(base_dir), "fresh.txt", "wb")
    f.write(b"abc")
    f.close()
    assert (base_dir / "fresh.txt").read_bytes() == b"abc"


def test_open_within_read_write_roundtrip(base_dir: Path) -> None:
    with open_within(str(base_dir), "roundtrip.txt", "wb") as f:
        f.write(b"roundtrip-data")
    with open_within(str(base_dir), "roundtrip.txt", "rb") as f:
        assert f.read() == b"roundtrip-data"


def test_open_within_rejects_unsupported_mode(base_dir: Path) -> None:
    with pytest.raises(PathUnsafeError):
        open_within(str(base_dir), "x.txt", "rw")


def test_safe_path_protocol_class_delegates(base_dir: Path) -> None:
    impl = SafePathImpl()
    (base_dir / "p.txt").write_text("p")
    assert impl.resolve_within(str(base_dir), "p.txt") == str((base_dir / "p.txt").resolve())
    with impl.open_within(str(base_dir), "p.txt", "rb") as f:
        assert f.read() == b"p"


def test_base_not_absolute_rejected(tmp_path: Path) -> None:
    with pytest.raises(PathUnsafeError):
        resolve_within("relative/base", "x.txt")
