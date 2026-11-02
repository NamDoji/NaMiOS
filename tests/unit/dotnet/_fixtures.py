"""Đường dẫn fixture dùng chung cho test WP .NET (``namios_dotnet``)."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DOTNET_DIR = _REPO_ROOT / "fixtures" / "dotnet"


def fixture_path(name: str) -> str:
    return str(FIXTURES_DOTNET_DIR / name)
