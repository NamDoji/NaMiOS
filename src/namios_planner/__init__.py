"""Install Planner (WP6 hiện thực — CLI-002). Xem
``docs/specs/M1-INTERFACES.md`` §7.4.

Hiện thực ``namios_core.planner_types.InstallPlanner``: ``build_plan`` gom
user/host hiện tại, digest hồ sơ (manifest), digest artifact (installer,
nếu có), danh sách thay đổi (từ ``RecipeEngine.dry_run`` — WP10), dung
lượng ước tính, permissions, hạn dùng (``expires_at``). ``verify_at_apply``
tính lại digest + so khớp user/host + hạn dùng; sai bất kỳ điều kiện nào →
``E_PLAN_STALE`` (CLI-002).
"""

from __future__ import annotations

from namios_planner.errors import PlanBuildError
from namios_planner.planner import DefaultInstallPlanner

__all__ = ["DefaultInstallPlanner", "PlanBuildError"]
