"""Install Planner API (WP6 hiện thực — CLI-002). Xem M1-INTERFACES.md §7.4."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from namios_core.manifest_types import Manifest, PermissionsSection
from namios_core.validation import SemanticContext


@dataclass(frozen=True)
class InstallPlan:
    plan_id: str
    app_id: str
    user: str
    host: str
    profile_digest: str
    artifact_digests: tuple[tuple[str, str], ...]  # (path_label, sha256)
    changes: tuple[str, ...]
    required_space_bytes: int
    permissions: PermissionsSection
    expires_at: str  # ISO 8601 UTC


@dataclass(frozen=True)
class ApplyCheck:
    ok: bool
    code: str | None  # code ∈ ErrorCode
    message_vi: str | None


class InstallPlanner(Protocol):
    """``verify_at_apply`` PHẢI xác minh lại artifact digest + user/host + hạn
    dùng; reject plan sai user, hết hạn, hoặc nội dung đổi → ``E_PLAN_STALE``
    (FACT CLI-002)."""

    def build_plan(
        self, m: Manifest, installer_path: str | None, ctx: SemanticContext
    ) -> InstallPlan: ...

    def verify_at_apply(
        self, plan: InstallPlan, current_user: str, current_host: str
    ) -> ApplyCheck: ...
