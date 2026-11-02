"""Helper dựng ``Manifest``/``CatalogEntry`` tối thiểu cho test WP4 (không
phải test case — không được pytest thu thập).

Chỉ phụ thuộc ``namios_core`` (dataclass thuần) — KHÔNG import implementation
của WP2 (``namios_manifest``) để giữ test catalog độc lập khỏi logic tải/
thẩm định manifest của module khác (chống giẫm chân theo CLAUDE.md).
"""

from __future__ import annotations

from namios_core.catalog_types import CatalogEntry
from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    LicenseSection,
    Manifest,
    PermissionsSection,
    RuntimeSection,
    SourceSection,
)


def make_manifest(
    app_id: str,
    name: str,
    publisher: str = "Demo Publisher",
) -> Manifest:
    """Manifest hợp lệ tối thiểu, đủ field bắt buộc, chỉ khác nhau ở
    id/name/publisher — dùng để dựng nhiều ``CatalogEntry`` cho test tìm
    kiếm/revocation."""

    return Manifest(
        schema_version="1.0",
        id=app_id,
        name=name,
        publisher=publisher,
        mode="native",
        application=AppSection(
            version="1.0.0",
            build="2026.11.01",
            architecture="x86_64",
            installer_sha256="a" * 64,
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
            official_url=None,
            allowed_hosts=(),
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
            filesystem=(),
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
        recipe=(),
        compatibility=CompatSection(
            status="untested",
            vendor_support="unknown",
            required_task_ids=(),
            limitations=(),
            last_tested=None,
            evidence_id=None,
        ),
    )


def make_entry(
    app_id: str,
    name: str,
    publisher: str = "Demo Publisher",
    channel: str = "stable",
    digest: str | None = None,
) -> CatalogEntry:
    return CatalogEntry(
        manifest=make_manifest(app_id, name, publisher),
        digest=digest or ("0" * 64),
        channel=channel,
    )
