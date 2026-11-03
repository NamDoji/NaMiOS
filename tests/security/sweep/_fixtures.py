"""Helper dựng dữ liệu tối thiểu cho SEC-SWEEP — KHÔNG phải test case (không
có hàm ``test_*`` nên pytest không thu thập). Tự đứng riêng (không import
``tests/unit/**/_fixtures.py`` hay ``tests/qa/**`` của dev/QA khác) để giữ
tính độc lập của vai trò rà soát bảo mật."""

from __future__ import annotations

import copy
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
from namios_core.recipe_types import RecipeStep


def raw_manifest_dict(**overrides: Any) -> dict[str, Any]:
    """Raw dict (schema + semantic hợp lệ tối thiểu) cho test tầng JSON/dict."""

    base: dict[str, Any] = {
        "schema_version": "1.0",
        "id": "sweep-app",
        "name": "Sweep Demo App",
        "publisher": "Sweep Publisher",
        "mode": "native",
        "application": {
            "version": "1.0.0",
            "build": "2026.11.03",
            "architecture": "x86_64",
            "installer_sha256": "a" * 64,
        },
        "license": {
            "kind": "open_source",
            "spdx_expression": "MIT",
            "user_entitlement_required": False,
            "redistribution": "allowed_with_conditions",
            "terms_url": "https://example.test/terms",
        },
        "source": {
            "acquisition": "distribution_repository",
            "official_url": "https://example.test/download",
            "allowed_hosts": ["example.test"],
            "automatic_download": False,
        },
        "runtime": {
            "runner_id": None,
            "runner_sha256": None,
            "prefix_architecture": "not_applicable",
            "wow64_strategy": "not_applicable",
            "dependency_profile_ids": [],
        },
        "permissions": {
            "filesystem": [{"scope": "app_data", "access": "read_write"}],
            "network": "deny",
            "audio": False,
            "microphone": False,
            "camera": False,
            "printing": False,
            "clipboard": "deny",
            "display": "wayland",
            "isolation": "not_applicable",
            "exceptions": [],
        },
        "recipe": [],
        "compatibility": {
            "status": "untested",
            "vendor_support": "unknown",
            "required_task_ids": [],
            "limitations": [],
            "last_tested": None,
            "evidence_id": None,
        },
    }
    merged = copy.deepcopy(base)
    merged.update(overrides)
    return merged


def minimal_manifest(*, app_id: str = "sweep-app", recipe: tuple[RecipeStep, ...] = ()) -> Manifest:
    """``Manifest`` typed tối thiểu, mode ``native`` (không cần runner) —
    dùng cho test không cần đi qua tầng JSON/schema."""

    return Manifest(
        schema_version="1.0",
        id=app_id,
        name="Sweep Demo App",
        publisher="Sweep Publisher",
        mode="native",
        application=AppSection(
            version="1.0.0", build="2026.11.03", architecture="x86_64", installer_sha256="a" * 64
        ),
        license=LicenseSection(
            kind="open_source",
            spdx_expression="MIT",
            user_entitlement_required=False,
            redistribution="allowed_with_conditions",
            terms_url=None,
        ),
        source=SourceSection(
            acquisition="distribution_repository",
            official_url="https://example.test/download",
            allowed_hosts=("example.test",),
            automatic_download=False,
        ),
        runtime=RuntimeSection(
            runner_id=None,
            runner_sha256=None,
            prefix_architecture="not_applicable",
            wow64_strategy="not_applicable",
            dependency_profile_ids=(),
        ),
        permissions=PermissionsSection(
            filesystem=(FilesystemPermission(scope="app_data", access="read_write"),),
            network="deny",
            audio=False,
            microphone=False,
            camera=False,
            printing=False,
            clipboard="deny",
            display="wayland",
            isolation="not_applicable",
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
