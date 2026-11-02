"""Hiện thực ``namios_core.planner_types.InstallPlanner`` (WP6 — CLI-002).

``DefaultInstallPlanner`` nhận một ``RecipeEngine`` (WP10) qua constructor
(dependency injection theo Protocol — KHÔNG import implementation cụ thể
của WP10, chỉ cần một đối tượng khớp ``namios_core.recipe_types.RecipeEngine``;
test của module này dùng fake). Nguồn thời gian/user/host cũng tiêm được để
test xác định, không phụ thuộc đồng hồ/host thật.
"""

from __future__ import annotations

import socket
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from namios_core.errors import ErrorCode
from namios_core.manifest_types import Manifest
from namios_core.planner_types import ApplyCheck, InstallPlan
from namios_core.recipe_types import RecipeEngine
from namios_core.validation import SemanticContext
from namios_planner._digest import DigestError, file_size_bytes, sha256_file
from namios_planner._profile import profile_digest
from namios_planner.errors import PlanBuildError

__all__ = ["DefaultInstallPlanner"]

#: Hạn dùng mặc định của một plan kể từ lúc tạo (DESIGN — chưa có yêu cầu
#: cụ thể khác trong đặc tả; đủ ngắn để giảm cửa sổ TOCTOU giữa plan và
#: apply, đủ dài để người dùng xác nhận thủ công).
_DEFAULT_TTL = timedelta(minutes=15)


def _default_current_user() -> str:
    try:
        import getpass

        return getpass.getuser()
    except Exception:  # pragma: no cover - phụ thuộc môi trường hệ thống
        return "unknown"


def _default_current_host() -> str:
    try:
        return socket.gethostname()
    except Exception:  # pragma: no cover - phụ thuộc môi trường hệ thống
        return "unknown"


def _default_clock() -> datetime:
    return datetime.now(UTC)


def _parse_iso(value: str) -> datetime:
    # ``datetime.fromisoformat`` (py3.11+) hiểu hậu tố "Z"; chuẩn hóa về
    # aware UTC để so sánh an toàn dù input thiếu offset.
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class DefaultInstallPlanner:
    """Hiện thực cụ thể khớp ``InstallPlanner`` Protocol."""

    def __init__(
        self,
        recipe_engine: RecipeEngine,
        *,
        clock: Callable[[], datetime] = _default_clock,
        current_user: Callable[[], str] = _default_current_user,
        current_host: Callable[[], str] = _default_current_host,
        ttl: timedelta = _DEFAULT_TTL,
    ) -> None:
        self._recipe_engine = recipe_engine
        self._clock = clock
        self._current_user = current_user
        self._current_host = current_host
        self._ttl = ttl

    # -- InstallPlanner Protocol -----------------------------------------

    def build_plan(
        self, m: Manifest, installer_path: str | None, ctx: SemanticContext
    ) -> InstallPlan:
        if m.id in ctx.revoked_ids:
            raise PlanBuildError(
                code=ErrorCode.E_REVOKED,
                message_vi=f"Hồ sơ '{m.id}' đã bị thu hồi, không thể tạo plan cài đặt.",
            )

        dry_run = self._recipe_engine.dry_run(m.recipe, ctx)
        if not dry_run.ok:
            first = dry_run.rejected[0] if dry_run.rejected else None
            message_vi = (
                first.message_vi
                if first is not None
                else "Recipe bị tầng ngữ nghĩa từ chối, không rõ lý do."
            )
            raise PlanBuildError(code=ErrorCode.E_SEMANTIC_RECIPE, message_vi=message_vi)

        artifact_digests: tuple[tuple[str, str], ...] = ()
        required_space_bytes = 0
        if installer_path is not None:
            try:
                digest = sha256_file(installer_path)
                required_space_bytes = file_size_bytes(installer_path)
            except DigestError as exc:
                raise PlanBuildError(
                    code=ErrorCode.E_PATH_UNSAFE,
                    message_vi=f"Không đọc được installer để lập plan: {exc.reason_vi}.",
                ) from exc
            artifact_digests = ((installer_path, digest),)

        now = self._clock()
        expires_at = (now + self._ttl).isoformat()

        return InstallPlan(
            plan_id=uuid.uuid4().hex,
            app_id=m.id,
            user=self._current_user(),
            host=self._current_host(),
            profile_digest=profile_digest(m),
            artifact_digests=artifact_digests,
            changes=dry_run.planned_actions,
            required_space_bytes=required_space_bytes,
            permissions=m.permissions,
            expires_at=expires_at,
        )

    def verify_at_apply(
        self, plan: InstallPlan, current_user: str, current_host: str
    ) -> ApplyCheck:
        if plan.user != current_user or plan.host != current_host:
            return ApplyCheck(
                ok=False,
                code=ErrorCode.E_PLAN_STALE.value,
                message_vi=(
                    "Plan được tạo cho người dùng/máy khác "
                    f"('{plan.user}'@'{plan.host}'), không áp dụng được cho "
                    f"'{current_user}'@'{current_host}'."
                ),
            )

        try:
            expires_at = _parse_iso(plan.expires_at)
        except ValueError:
            return ApplyCheck(
                ok=False,
                code=ErrorCode.E_PLAN_STALE.value,
                message_vi=f"Plan có hạn dùng không đọc được: '{plan.expires_at}'.",
            )

        if self._clock() > expires_at:
            return ApplyCheck(
                ok=False,
                code=ErrorCode.E_PLAN_STALE.value,
                message_vi=f"Plan đã hết hạn dùng lúc {plan.expires_at}.",
            )

        for path_label, expected_digest in plan.artifact_digests:
            try:
                actual_digest = sha256_file(path_label)
            except DigestError as exc:
                return ApplyCheck(
                    ok=False,
                    code=ErrorCode.E_PLAN_STALE.value,
                    message_vi=(
                        f"Không đọc lại được artifact '{path_label}' lúc apply: "
                        f"{exc.reason_vi}."
                    ),
                )
            if actual_digest != expected_digest:
                return ApplyCheck(
                    ok=False,
                    code=ErrorCode.E_PLAN_STALE.value,
                    message_vi=(f"Nội dung artifact '{path_label}' đã đổi so với lúc lập plan."),
                )

        return ApplyCheck(ok=True, code=None, message_vi=None)
