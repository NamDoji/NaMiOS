"""Tầng xác thực/ủy quyền bọc ngoài ``SystemHelperService`` (SEC-001).

Đây là nơi DUY NHẤT thực hiện: (1) xác định danh tính caller qua kênh
truyền (D-Bus thật ở M3 / fake bus ở test M1 — KHÔNG tin tham số tự khai),
(2) tra action Polkit đúng method, (3) hỏi ``PolkitAuthority``. Deny ở BẤT
KỲ bước nào → ``PermissionDeniedError`` (exit 5) và TUYỆT ĐỐI KHÔNG gọi
xuống ``SystemHelperService`` (không có side-effect nào xảy ra trước khi
pass toàn bộ kiểm tra).
"""

from __future__ import annotations

from namios_core.helper_types import (
    ApprovedPackagePlan,
    PackagePlanRequest,
    SystemCapabilities,
    UpdateStatus,
)
from namios_helper.caller import CallerIdentity
from namios_helper.errors import PermissionDeniedError
from namios_helper.policy import METHOD_TO_ACTION, PolkitAuthority
from namios_helper.service import SystemHelperService


class AuthenticatedSystemHelper:
    """Adaptor "D-Bus-facing": nhận ``CallerIdentity`` đã xác thực bởi kênh
    truyền (không phải tham số request) + enforce Polkit TRƯỚC khi ủy quyền
    xuống ``SystemHelperService``. Tương ứng lớp sẽ được gắn vào
    object D-Bus thật (``org.namios.SystemHelper1``) ở M3."""

    def __init__(self, service: SystemHelperService, authority: PolkitAuthority) -> None:
        self._service = service
        self._authority = authority

    def _authorize(self, caller: CallerIdentity, method_name: str) -> None:
        action = METHOD_TO_ACTION[method_name]
        decision = self._authority.check_authorization(caller, action)
        if not decision.allowed:
            raise PermissionDeniedError(
                f"Bị từ chối quyền gọi {method_name}: {decision.reason_vi}",
                details={"method": method_name, "action": action.value, "uid": caller.uid},
            )

    def GetSystemCapabilities(self, caller: CallerIdentity) -> SystemCapabilities:
        self._authorize(caller, "GetSystemCapabilities")
        return self._service.GetSystemCapabilities()

    def PlanPackageInstall(
        self, caller: CallerIdentity, req: PackagePlanRequest
    ) -> ApprovedPackagePlan:
        self._authorize(caller, "PlanPackageInstall")
        return self._service.PlanPackageInstall(req)

    def ApplyApprovedPackagePlan(
        self, caller: CallerIdentity, plan: ApprovedPackagePlan
    ) -> UpdateStatus:
        self._authorize(caller, "ApplyApprovedPackagePlan")
        return self._service.ApplyApprovedPackagePlan(plan)

    def GetUpdateStatus(self, caller: CallerIdentity) -> UpdateStatus:
        self._authorize(caller, "GetUpdateStatus")
        return self._service.GetUpdateStatus()
