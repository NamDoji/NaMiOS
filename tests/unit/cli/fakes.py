"""Fake implementation khớp Protocol trong ``namios_core`` — chỉ dùng để
unit test khung dispatch của WP3 (``namios_cli``). KHÔNG phải triển khai
thật của WP2/WP6/WP9; test theo Protocol, không phụ thuộc impl module khác
(đúng quy tắc M1-INTERFACES §0).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from namios_core.compat import CompatStatus
from namios_core.evidence_types import EvidenceReport, GateResult
from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    FilesystemPermission,
    LicenseSection,
    Manifest,
    PermissionsSection,
    RuntimeSection,
    SchemaResult,
    SemanticResult,
    SourceSection,
)
from namios_core.planner_types import ApplyCheck, InstallPlan
from namios_core.validation import SemanticContext


def make_manifest(*, app_id: str = "app.test", install_ready_mode: str = "native") -> Manifest:
    return Manifest(
        schema_version="1.0",
        id=app_id,
        name="App kiểm thử",
        publisher="NaMiOS QA",
        mode=install_ready_mode,  # type: ignore[arg-type]
        application=AppSection(
            version="1.0.0", build="1", architecture="x86_64", installer_sha256="a" * 64
        ),
        license=LicenseSection(
            kind="open_source",
            spdx_expression="MIT",
            user_entitlement_required=False,
            redistribution="allowed_with_conditions",
            terms_url=None,
        ),
        source=SourceSection(
            acquisition="official_download",
            official_url="https://example.invalid/app",
            allowed_hosts=("example.invalid",),
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
            filesystem=(FilesystemPermission(scope="app_data", access="read"),),
            network="deny",
            audio=False,
            microphone=False,
            camera=False,
            printing=False,
            clipboard="deny",
            display="none",
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


class FakeManifestValidator:
    """Khớp ``namios_core.manifest_types.ManifestValidator`` Protocol."""

    def __init__(self, *, manifest: Manifest | None = None, install_ready: bool = True) -> None:
        self._manifest = manifest if manifest is not None else make_manifest()
        self._install_ready = install_ready

    def load(self, path: str) -> Manifest:
        if path == "__raise__":
            raise ValueError("đường dẫn giả lập lỗi tải manifest")
        return self._manifest

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult:
        return SemanticResult(ok=self._install_ready, errors=(), install_ready=self._install_ready)


class FakeInstallPlanner:
    """Khớp ``namios_core.planner_types.InstallPlanner`` Protocol."""

    def build_plan(
        self, m: Manifest, installer_path: str | None, ctx: SemanticContext
    ) -> InstallPlan:
        return InstallPlan(
            plan_id="plan-" + m.id,
            app_id=m.id,
            user="nguoi-dung-test",
            host="may-test-namios",
            profile_digest="d" * 64,
            artifact_digests=(),
            changes=("tao-prefix", "cai-dependency"),
            required_space_bytes=1024,
            permissions=m.permissions,
            expires_at="2099-01-01T00:00:00Z",
        )

    def verify_at_apply(
        self, plan: InstallPlan, current_user: str, current_host: str
    ) -> ApplyCheck:
        return ApplyCheck(ok=True, code=None, message_vi=None)


class FakeEvidenceValidator:
    """Khớp ``namios_core.evidence_types.EvidenceValidator`` Protocol."""

    def __init__(self, *, allowed_status: CompatStatus = CompatStatus.EXPERIMENTAL) -> None:
        self._allowed_status = allowed_status

    def load(self, path: str) -> EvidenceReport:
        if path == "__raise__":
            raise ValueError("đường dẫn giả lập lỗi tải evidence")
        return EvidenceReport(
            report_id="rep-1",
            manifest_id="app.test",
            tests=(),
            decision="experimental",
            qa_reviewer=None,
            environment={},
        )

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def compute_allowed_status(self, rep: EvidenceReport) -> GateResult:
        return GateResult(
            allowed_status=self._allowed_status,
            reasons_vi=("qa_reviewer vắng — không thể task_verified.",),
        )
