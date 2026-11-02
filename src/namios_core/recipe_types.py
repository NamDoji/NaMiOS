"""Recipe action types + engine (WP10 hiện thực — COMP-004). Xem
M1-INTERFACES.md §7.6.

6 action khai báo (FACT contract recipe.enum). Params typed; KHÔNG
``shell``/``eval``/url-script/template nội suy; dùng argv array.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from namios_core.validation import SemanticContext, ValidationError


@dataclass(frozen=True)
class CreatePrefix:
    prefix_architecture: Literal["win32", "win64"]


@dataclass(frozen=True)
class InstallDependency:
    dependency_profile_id: str  # PHẢI ∈ approved_dependency_ids


@dataclass(frozen=True)
class SetRegistryValue:
    key: str
    value_name: str
    value_type: Literal["REG_SZ", "REG_DWORD"]
    value: str


@dataclass(frozen=True)
class RunInstaller:
    installer_ref: str
    argv: tuple[str, ...]  # installer do người dùng cấp; argv-only


@dataclass(frozen=True)
class VerifyFile:
    path_label: str
    sha256: str


@dataclass(frozen=True)
class CreateLauncher:
    app_id: str
    profile_id: str  # KHÔNG nhúng mật khẩu/URL-1-lần/lệnh (COMP-006)


RecipeStep = (
    CreatePrefix | InstallDependency | SetRegistryValue | RunInstaller | VerifyFile | CreateLauncher
)


@dataclass(frozen=True)
class DryRunResult:
    ok: bool
    planned_actions: tuple[str, ...]
    rejected: tuple[ValidationError, ...]


class RecipeEngine(Protocol):
    """M1: chỉ ``dry_run`` (không cài thật — FACT M1 gate). Thực thi thật là
    M2 (BLOCKED)."""

    def parse(
        self, raw_steps: Sequence[Mapping[str, Any]]
    ) -> tuple[RecipeStep, ...]: ...  # reject action/param lạ

    def dry_run(
        self, steps: Sequence[RecipeStep], ctx: SemanticContext
    ) -> DryRunResult: ...  # KHÔNG thực thi gì
