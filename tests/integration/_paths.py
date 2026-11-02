"""Đường dẫn fixture dùng chung cho test tích hợp (WIRING) — KHÔNG phải test
case (không được pytest thu thập)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

#: Fixtures manifest riêng của test tích hợp (CLI đọc path tuyệt đối thật —
#: khác với ``tests/unit/manifest/_fixtures.py`` chỉ dựng dict trong RAM).
MANIFEST_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "manifest"

#: Fixtures evidence CHUNG của repo (WP9 — ``fixtures/evidence/**``), dùng lại
#: nguyên trạng, không copy/sửa.
EVIDENCE_FIXTURES_DIR = _REPO_ROOT / "fixtures" / "evidence"


def manifest_fixture_path(name: str) -> str:
    return str(MANIFEST_FIXTURES_DIR / name)


def evidence_fixture_path(name: str) -> str:
    return str(EVIDENCE_FIXTURES_DIR / name)
