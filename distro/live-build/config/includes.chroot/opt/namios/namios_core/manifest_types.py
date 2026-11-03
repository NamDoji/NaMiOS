"""Manifest + Validator API (WP2 hiện thực — COMP-004, §11.1). Xem
M1-INTERFACES.md §7.1.

Các dataclass section ánh xạ 1-1 ``contracts/app-manifest.schema.json``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from namios_core.recipe_types import RecipeStep
from namios_core.validation import SemanticContext, ValidationError

__all__ = [
    "AppSection",
    "LicenseSection",
    "SourceSection",
    "RuntimeSection",
    "FilesystemPermission",
    "PermissionsSection",
    "CompatSection",
    "Manifest",
    "SchemaResult",
    "SemanticResult",
    "ValidationError",
    "SemanticContext",
    "ManifestValidator",
]


@dataclass(frozen=True)
class AppSection:
    version: str | None
    build: str | None
    architecture: Literal["x86", "x86_64", "any", "unknown"]
    installer_sha256: str | None


@dataclass(frozen=True)
class LicenseSection:
    kind: Literal["open_source", "freeware", "commercial", "unknown"]
    spdx_expression: str | None
    user_entitlement_required: bool
    redistribution: Literal["allowed_with_conditions", "not_included", "unknown"]
    terms_url: str | None


@dataclass(frozen=True)
class SourceSection:
    acquisition: Literal[
        "distribution_repository",
        "official_download",
        "user_provided",
        "official_web",
        "existing_environment",
    ]
    official_url: str | None
    allowed_hosts: tuple[str, ...]
    automatic_download: bool


@dataclass(frozen=True)
class RuntimeSection:
    runner_id: str | None
    runner_sha256: str | None
    prefix_architecture: Literal["win32", "win64", "not_applicable", "unknown"]
    wow64_strategy: Literal["new_wow64", "multiarch_i386", "not_applicable", "unknown"]
    dependency_profile_ids: tuple[str, ...]


@dataclass(frozen=True)
class FilesystemPermission:
    scope: Literal["app_data", "user_selected_files", "user_selected_directory"]
    access: Literal["read", "read_write"]


@dataclass(frozen=True)
class PermissionsSection:
    filesystem: tuple[FilesystemPermission, ...]
    network: Literal["deny", "allow_with_user_consent"]
    audio: bool
    microphone: bool
    camera: bool
    printing: bool
    clipboard: Literal["deny", "user_mediated", "session_shared"]
    display: Literal["wayland", "xwayland", "x11", "none", "unknown"]
    isolation: Literal["required", "not_applicable", "lab_unconfined"]
    exceptions: tuple[str, ...]


@dataclass(frozen=True)
class CompatSection:
    status: Literal["untested", "experimental", "task_verified", "blocked", "revoked"]
    vendor_support: Literal["officially_supported", "not_officially_supported", "unknown"]
    required_task_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    last_tested: str | None
    evidence_id: str | None


@dataclass(frozen=True)
class Manifest:
    """Ánh xạ 1-1 ``contracts/app-manifest.schema.json``."""

    schema_version: str
    id: str
    name: str
    publisher: str
    mode: Literal["native", "web", "wine", "vm", "remote"]
    application: AppSection
    license: LicenseSection
    source: SourceSection
    runtime: RuntimeSection
    permissions: PermissionsSection
    recipe: tuple[RecipeStep, ...]
    compatibility: CompatSection


@dataclass(frozen=True)
class SchemaResult:
    ok: bool
    errors: tuple[ValidationError, ...]


@dataclass(frozen=True)
class SemanticResult:
    ok: bool
    errors: tuple[ValidationError, ...]
    install_ready: bool


class ManifestValidator(Protocol):
    """Validation 2 tầng (FACT §11.1/COMP-004): "schema hợp lệ" ≠ "an toàn
    để chạy"."""

    def load(self, path: str) -> Manifest: ...  # dùng resolve_within + safe read

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult: ...

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult: ...
