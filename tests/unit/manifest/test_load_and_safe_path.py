"""``ManifestValidatorImpl.load()`` — đọc file an toàn + pipeline đủ 2 tầng.
Negative case: symlink/traversal/không phải file thường/relative path."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from namios_manifest import ManifestLoadError, ManifestValidatorImpl, PathUnsafeError
from namios_manifest._safe_io import read_text_safe

from ._fixtures import deep_copy, valid_raw_manifest


def _write_manifest(path: Path, raw: dict) -> None:
    path.write_text(json.dumps(raw), encoding="utf-8")


def test_load_valid_manifest_file(tmp_path: Path) -> None:
    raw = valid_raw_manifest()
    manifest_path = tmp_path / "demo.json"
    _write_manifest(manifest_path, raw)

    validator = ManifestValidatorImpl()
    m = validator.load(str(manifest_path))

    assert m.id == "demo-app"
    assert m.mode == "native"


def test_load_rejects_unknown_key_with_manifest_load_error(tmp_path: Path) -> None:
    raw = deep_copy(valid_raw_manifest())
    raw["not_a_real_field"] = True
    manifest_path = tmp_path / "bad.json"
    _write_manifest(manifest_path, raw)

    validator = ManifestValidatorImpl()
    with pytest.raises(ManifestLoadError) as exc_info:
        validator.load(str(manifest_path))

    assert any(e.code == "E_INPUT_UNKNOWN_KEY" for e in exc_info.value.errors)


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    manifest_path = tmp_path / "broken.json"
    manifest_path.write_text("{not valid json", encoding="utf-8")

    validator = ManifestValidatorImpl()
    with pytest.raises(ManifestLoadError):
        validator.load(str(manifest_path))


def test_load_rejects_symlink_leaf(tmp_path: Path) -> None:
    raw = valid_raw_manifest()
    real_path = tmp_path / "real.json"
    _write_manifest(real_path, raw)
    link_path = tmp_path / "link.json"
    os.symlink(real_path, link_path)

    validator = ManifestValidatorImpl()
    with pytest.raises(PathUnsafeError):
        validator.load(str(link_path))


def test_load_rejects_parent_dir_symlink_traversal(tmp_path: Path) -> None:
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    raw = valid_raw_manifest()
    outside_manifest = outside_dir / "secret.json"
    _write_manifest(outside_manifest, raw)

    inside_dir = tmp_path / "inside"
    inside_dir.mkdir()
    traversal_link = inside_dir / "escape"
    os.symlink(outside_dir, traversal_link)

    validator = ManifestValidatorImpl()
    with pytest.raises(PathUnsafeError):
        validator.load(str(traversal_link / "secret.json"))


def test_load_rejects_relative_path() -> None:
    validator = ManifestValidatorImpl()
    with pytest.raises(PathUnsafeError):
        validator.load("relative/path/manifest.json")


def test_load_rejects_nonexistent_path(tmp_path: Path) -> None:
    validator = ManifestValidatorImpl()
    with pytest.raises(PathUnsafeError):
        validator.load(str(tmp_path / "does-not-exist.json"))


def test_load_rejects_oversized_file(tmp_path: Path) -> None:
    big_path = tmp_path / "huge.json"
    big_path.write_text("x" * 10, encoding="utf-8")

    with pytest.raises(PathUnsafeError):
        read_text_safe(str(big_path), max_bytes=5)


def test_load_rejects_fifo_not_regular_file(tmp_path: Path) -> None:
    fifo_path = tmp_path / "pipe"
    os.mkfifo(fifo_path)

    with pytest.raises(PathUnsafeError):
        read_text_safe(str(fifo_path))
