"""Fixtures/test doubles riêng của WP6 (planner).

KHÔNG import từ ``tests/unit/manifest`` (thư mục test của WP2) — mỗi WP tự
dựng fixture của mình theo Protocol/dataclass công khai trong
``namios_core``, tránh phụ thuộc chéo giữa test suite của các WP (đúng
nguyên tắc chống giẫm chân M1-WORK-PACKAGES.md).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    FilesystemPermission,
    LicenseSection,
    Manifest,
    PermissionsSection,
    RuntimeSection,
    SourceSection,
)
from namios_core.recipe_types import CreatePrefix, DryRunResult, RecipeStep
from namios_core.validation import SemanticContext, ValidationError

__all__ = [
    "make_manifest",
    "make_semantic_context",
    "FakeRecipeEngine",
    "RejectingRecipeEngine",
]


def make_manifest(
    *,
    app_id: str = "app.vi.vinaapp",
    name: str = "VinaApp",
    recipe: tuple[RecipeStep, ...] | None = None,
    installer_sha256: str | None = "a" * 64,
) -> Manifest:
    """Dựng một ``Manifest`` hợp lệ tối thiểu cho test planner (không đi qua
    ``ManifestValidator`` — planner nhận ``Manifest`` đã có sẵn theo
    Protocol, không chịu trách nhiệm validate lại)."""

    if recipe is None:
        recipe = (CreatePrefix(prefix_architecture="win64"),)

    return Manifest(
        schema_version="1.0",
        id=app_id,
        name=name,
        publisher="Nhà phát hành thử nghiệm",
        mode="wine",
        application=AppSection(
            version="1.2.3",
            build="1.2.3+100",
            architecture="x86_64",
            installer_sha256=installer_sha256,
        ),
        license=LicenseSection(
            kind="commercial",
            spdx_expression=None,
            user_entitlement_required=True,
            redistribution="not_included",
            terms_url=None,
        ),
        source=SourceSection(
            acquisition="user_provided",
            official_url=None,
            allowed_hosts=(),
            automatic_download=False,
        ),
        runtime=RuntimeSection(
            runner_id="wine-ge-8.0",
            runner_sha256="b" * 64,
            prefix_architecture="win64",
            wow64_strategy="new_wow64",
            dependency_profile_ids=("dotnet48",),
        ),
        permissions=PermissionsSection(
            filesystem=(FilesystemPermission(scope="app_data", access="read_write"),),
            network="deny",
            audio=False,
            microphone=False,
            camera=False,
            printing=False,
            clipboard="deny",
            display="xwayland",
            isolation="required",
            exceptions=(),
        ),
        recipe=recipe,
        compatibility=CompatSection(
            status="untested",
            vendor_support="unknown",
            required_task_ids=(),
            limitations=(),
            last_tested=None,
            evidence_id=None,
        ),
    )


def make_semantic_context(
    *,
    approved_dependency_ids: frozenset[str] = frozenset({"dotnet48"}),
    pinned_runner_hashes: frozenset[str] = frozenset({"b" * 64}),
    revoked_ids: frozenset[str] = frozenset(),
) -> SemanticContext:
    return SemanticContext(
        approved_dependency_ids=approved_dependency_ids,
        pinned_runner_hashes=pinned_runner_hashes,
        revoked_ids=revoked_ids,
    )


@dataclass
class FakeRecipeEngine:
    """Fake khớp ``namios_core.recipe_types.RecipeEngine`` — trả
    ``DryRunResult`` thành công cố định, KHÔNG thực thi gì (đúng Protocol
    M1). Dùng để test planner KHÔNG phụ thuộc hiện thực thật của WP10 (chưa
    có trong repo tại thời điểm viết)."""

    planned_actions: tuple[str, ...] = ("create_prefix(win64)",)

    def parse(self, raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
        raise NotImplementedError("FakeRecipeEngine không cần parse() cho test planner")

    def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
        return DryRunResult(ok=True, planned_actions=self.planned_actions, rejected=())


@dataclass
class RejectingRecipeEngine:
    """Fake trả ``DryRunResult(ok=False, ...)`` — mô phỏng recipe bị tầng
    ngữ nghĩa từ chối (vd. dependency chưa duyệt)."""

    error: ValidationError

    def parse(self, raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
        raise NotImplementedError("RejectingRecipeEngine không cần parse() cho test planner")

    def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
        return DryRunResult(ok=False, planned_actions=(), rejected=(self.error,))
