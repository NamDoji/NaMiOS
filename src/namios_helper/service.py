"""``SystemHelperService`` — hiện thực THUẦN nghiệp vụ của
``namios_core.helper_types.SystemHelper`` (M1-INTERFACES §7.5).

QUAN TRỌNG (SEC-001): class này KHÔNG tự xác thực caller/Polkit — nó giả
định đã được gọi sau khi tầng :class:`namios_helper.authenticated.AuthenticatedSystemHelper`
cho qua. Giữ tầng này "ngu" (không caller, không I/O hệ thống thật ngoài đọc
capability tĩnh) để:

1. Test introspection đảm bảo KHÔNG có method ``RunCommand`` hoặc method
   nhận argv/path tự do nào lọt vào đúng interface công khai.
2. ``AuthenticatedSystemHelper`` là nơi DUY NHẤT thực hiện kiểm tra quyền —
   dễ audit, không thể "quên" check ở một nhánh code khác.
"""

from __future__ import annotations

from collections.abc import Callable

from namios_core.helper_types import (
    ApprovedPackagePlan,
    PackagePlanRequest,
    SystemCapabilities,
    UpdateStatus,
)
from namios_helper.allowlist import PackagePlanAllowlist

#: Tên 4 method công khai duy nhất — dùng cho test introspection (đảm bảo
#: KHÔNG method nào khác, đặc biệt KHÔNG có "RunCommand").
PUBLIC_METHOD_NAMES: tuple[str, ...] = (
    "GetSystemCapabilities",
    "PlanPackageInstall",
    "ApplyApprovedPackagePlan",
    "GetUpdateStatus",
)


class SystemHelperService:
    """Hiện thực Protocol ``SystemHelper`` — KHÔNG có ``RunCommand``, KHÔNG
    nhận repository/key/package tùy ý ngoài ``allowlist_key`` (CLI-004).
    Thao tác phân vùng KHÔNG đi qua class này."""

    def __init__(
        self,
        *,
        allowlist: PackagePlanAllowlist,
        capabilities_provider: Callable[[], SystemCapabilities],
        update_status_provider: Callable[[], UpdateStatus],
    ) -> None:
        self._allowlist = allowlist
        self._capabilities_provider = capabilities_provider
        self._update_status_provider = update_status_provider
        # Theo dõi các plan đã được apply (idempotent nếu caller gọi lại
        # đúng plan — KHÔNG mutate hệ thống thêm lần hai; M1 chỉ mô phỏng
        # trạng thái nội bộ, cài thật là M2 BLOCKED).
        self._applied_plan_ids: set[str] = set()

    def GetSystemCapabilities(self) -> SystemCapabilities:
        return self._capabilities_provider()

    def PlanPackageInstall(self, req: PackagePlanRequest) -> ApprovedPackagePlan:
        # ``req.allowlist_key`` là KHÓA, không phải tên package/đường dẫn —
        # tra thẳng trong allowlist nội bộ, không diễn giải chuỗi theo cách
        # khác (không nối path, không truyền cho exec).
        return self._allowlist.plan_for(req.allowlist_key)

    def ApplyApprovedPackagePlan(self, plan: ApprovedPackagePlan) -> UpdateStatus:
        entry = self._allowlist.verify_plan(plan)
        self._applied_plan_ids.add(entry.plan_id)
        # M1: KHÔNG cài thật (cài gói hệ thống là M2+ BLOCKED tại host này).
        # Trả trạng thái mô phỏng nhất quán: package trong entry được coi là
        # "đã áp dụng", không còn pending.
        return self._update_status_provider()

    def GetUpdateStatus(self) -> UpdateStatus:
        return self._update_status_provider()
