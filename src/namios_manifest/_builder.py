"""Build ``Manifest`` (namios_core.manifest_types) từ raw dict ĐÃ qua tầng 1
(schema). Giả định ``raw`` đã ``validate_schema(raw).ok is True`` — hàm này
KHÔNG tự chạy lại tầng 1 (caller — ``load()`` — chịu trách nhiệm thứ tự).
"""

from __future__ import annotations

from collections.abc import Mapping
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
from namios_manifest._recipe_build import build_recipe_steps

__all__ = ["build_manifest"]


def build_manifest(raw: Mapping[str, Any]) -> Manifest:
    application = raw["application"]
    license_ = raw["license"]
    source = raw["source"]
    runtime = raw["runtime"]
    permissions = raw["permissions"]
    compatibility = raw["compatibility"]

    app_section = AppSection(
        version=application["version"],
        build=application["build"],
        architecture=application["architecture"],
        installer_sha256=application["installer_sha256"],
    )
    license_section = LicenseSection(
        kind=license_["kind"],
        spdx_expression=license_["spdx_expression"],
        user_entitlement_required=license_["user_entitlement_required"],
        redistribution=license_["redistribution"],
        terms_url=license_["terms_url"],
    )
    source_section = SourceSection(
        acquisition=source["acquisition"],
        official_url=source["official_url"],
        allowed_hosts=tuple(source["allowed_hosts"]),
        automatic_download=source["automatic_download"],
    )
    runtime_section = RuntimeSection(
        runner_id=runtime["runner_id"],
        runner_sha256=runtime["runner_sha256"],
        prefix_architecture=runtime["prefix_architecture"],
        wow64_strategy=runtime["wow64_strategy"],
        dependency_profile_ids=tuple(runtime["dependency_profile_ids"]),
    )
    permissions_section = PermissionsSection(
        filesystem=tuple(
            FilesystemPermission(scope=item["scope"], access=item["access"])
            for item in permissions["filesystem"]
        ),
        network=permissions["network"],
        audio=permissions["audio"],
        microphone=permissions["microphone"],
        camera=permissions["camera"],
        printing=permissions["printing"],
        clipboard=permissions["clipboard"],
        display=permissions["display"],
        isolation=permissions["isolation"],
        exceptions=tuple(permissions["exceptions"]),
    )
    compat_section = CompatSection(
        status=compatibility["status"],
        vendor_support=compatibility["vendor_support"],
        required_task_ids=tuple(compatibility["required_task_ids"]),
        limitations=tuple(compatibility["limitations"]),
        last_tested=compatibility["last_tested"],
        evidence_id=compatibility["evidence_id"],
    )
    recipe_steps = build_recipe_steps(raw["recipe"])

    return Manifest(
        schema_version=raw["schema_version"],
        id=raw["id"],
        name=raw["name"],
        publisher=raw["publisher"],
        mode=raw["mode"],
        application=app_section,
        license=license_section,
        source=source_section,
        runtime=runtime_section,
        permissions=permissions_section,
        recipe=recipe_steps,
        compatibility=compat_section,
    )
