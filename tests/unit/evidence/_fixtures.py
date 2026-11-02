"""Đường dẫn fixture dùng chung cho test WP9 (evidence)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_FIXTURES_DIR = _REPO_ROOT / "fixtures" / "evidence"
CONTRACTS_DIR = _REPO_ROOT / "contracts"


def fixture_path(name: str) -> str:
    return str(EVIDENCE_FIXTURES_DIR / name)


def contract_sample_path(name: str) -> str:
    return str(CONTRACTS_DIR / name)


def load_raw(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
