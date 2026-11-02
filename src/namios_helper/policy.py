"""Polkit action-per-method cho ``SystemHelper`` (SEC-001).

M1-INTERFACES.md §7.5 (DESIGN): mỗi method gắn MỘT action Polkit riêng:

- ``org.namios.systemhelper.get-capabilities`` — allow-active, no-auth (đọc).
- ``org.namios.systemhelper.get-update-status`` — allow-active, no-auth (đọc;
  cùng mức với get-capabilities — không ghi/đổi hệ thống).
- ``org.namios.systemhelper.plan-package`` — auth_admin_keep.
- ``org.namios.systemhelper.apply-package`` — auth_admin_keep.

Polkitd thật là tích hợp M3 (BLOCKED tại host build hiện tại — headless,
không có polkitd/D-Bus system bus chạy). Ở đây ta định nghĩa
``PolkitAuthority`` như một Protocol mà adaptor D-Bus thật (M3) sẽ hiện thực
bằng cách gọi polkitd qua ``org.freedesktop.PolicyKit1.Authority.CheckAuthorization``;
``InMemoryPolkitAuthority`` là một hiện thực giả lập ĐỦ để kiểm tra LOGIC
quyết định allow/deny theo uid + action tại M1 (không kiểm tra được hành vi
polkitd thật).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from namios_helper.caller import CallerIdentity


class PolkitAction(str, Enum):
    """Action id Polkit — PHẢI khớp tên trong file ``.policy`` đóng gói
    (``packaging/debian/org.namios.SystemHelper1.policy``)."""

    GET_CAPABILITIES = "org.namios.systemhelper.get-capabilities"
    GET_UPDATE_STATUS = "org.namios.systemhelper.get-update-status"
    PLAN_PACKAGE = "org.namios.systemhelper.plan-package"
    APPLY_PACKAGE = "org.namios.systemhelper.apply-package"


class AuthRequirement(str, Enum):
    """Mức yêu cầu xác thực Polkit (ánh xạ ``<allow_active>``/
    ``<allow_any>`` trong file ``.policy``)."""

    ALLOW_ACTIVE_NO_AUTH = "allow_active_no_auth"
    AUTH_ADMIN_KEEP = "auth_admin_keep"


#: Ánh xạ method → action Polkit (DESIGN §7.5). Dùng ở mọi nơi cần tra action
#: cho một method — KHÔNG hardcode chuỗi action rải rác.
METHOD_TO_ACTION: dict[str, PolkitAction] = {
    "GetSystemCapabilities": PolkitAction.GET_CAPABILITIES,
    "GetUpdateStatus": PolkitAction.GET_UPDATE_STATUS,
    "PlanPackageInstall": PolkitAction.PLAN_PACKAGE,
    "ApplyApprovedPackagePlan": PolkitAction.APPLY_PACKAGE,
}

#: Mức xác thực yêu cầu cho mỗi action (DESIGN §7.5).
ACTION_AUTH_REQUIREMENT: dict[PolkitAction, AuthRequirement] = {
    PolkitAction.GET_CAPABILITIES: AuthRequirement.ALLOW_ACTIVE_NO_AUTH,
    PolkitAction.GET_UPDATE_STATUS: AuthRequirement.ALLOW_ACTIVE_NO_AUTH,
    PolkitAction.PLAN_PACKAGE: AuthRequirement.AUTH_ADMIN_KEEP,
    PolkitAction.APPLY_PACKAGE: AuthRequirement.AUTH_ADMIN_KEEP,
}


@dataclass(frozen=True)
class PolkitDecision:
    allowed: bool
    reason_vi: str


class PolkitAuthority(Protocol):
    """Protocol mà adaptor D-Bus thật (M3) hiện thực bằng cách gọi polkitd
    thật. Tại M1 ta chỉ cần Protocol này + một hiện thực giả lập để test
    logic LỰA CHỌN action/quyết định — KHÔNG mô phỏng hành vi polkitd đầy
    đủ (UI đồng ý mật khẩu, TTL phiên, v.v. — đó là hành vi hệ thống thật)."""

    def check_authorization(
        self, caller: CallerIdentity, action: PolkitAction
    ) -> PolkitDecision: ...


# uid cố định dành riêng cho "người dùng hệ thống" chạy session desktop
# active trong môi trường test/giả lập — KHÔNG phải một đặc quyền ma thuật,
# chỉ là quy ước nội bộ cho ``InMemoryPolkitAuthority`` suy luận allow_active.
_NOBODY_UID = 65534


@dataclass
class InMemoryPolkitAuthority:
    """Hiện thực ``PolkitAuthority`` giả lập, trong tiến trình — DÙNG CHO
    TEST LOGIC CHÍNH SÁCH tại M1 (không có polkitd thật).

    - ``active_session_uids``: tập uid được coi là "đang có session desktop
      active" (polkit thật xác định qua logind) — action
      ``ALLOW_ACTIVE_NO_AUTH`` chỉ pass khi uid caller nằm trong tập này.
    - ``admin_authenticated_uids``: tập uid ĐÃ xác thực admin thành công
      (polkit thật yêu cầu UI nhập mật khẩu quản trị) — action
      ``AUTH_ADMIN_KEEP`` chỉ pass khi uid caller nằm trong tập này.

    Mặc định (không truyền gì) → TỪ CHỐI MỌI THỨ (an toàn nhất: không giả
    định quyền nào caller chưa được cấp rõ ràng)."""

    active_session_uids: frozenset[int] = field(default_factory=frozenset)
    admin_authenticated_uids: frozenset[int] = field(default_factory=frozenset)

    def check_authorization(self, caller: CallerIdentity, action: PolkitAction) -> PolkitDecision:
        requirement = ACTION_AUTH_REQUIREMENT[action]
        if requirement is AuthRequirement.ALLOW_ACTIVE_NO_AUTH:
            if caller.uid in self.active_session_uids:
                return PolkitDecision(
                    allowed=True,
                    reason_vi=f"uid {caller.uid} có session active, action đọc không cần xác thực",
                )
            return PolkitDecision(
                allowed=False,
                reason_vi=(
                    f"uid {caller.uid} không có session desktop active; "
                    f"action {action.value} bị từ chối"
                ),
            )
        if requirement is AuthRequirement.AUTH_ADMIN_KEEP:
            if caller.uid in self.admin_authenticated_uids:
                return PolkitDecision(
                    allowed=True,
                    reason_vi=f"uid {caller.uid} đã xác thực quản trị cho action {action.value}",
                )
            return PolkitDecision(
                allowed=False,
                reason_vi=(
                    f"uid {caller.uid} chưa xác thực quản trị; "
                    f"action {action.value} yêu cầu auth_admin_keep"
                ),
            )
        # Không đáng xảy ra (enum đã đóng); giữ an toàn mặc định: từ chối.
        return PolkitDecision(allowed=False, reason_vi="Yêu cầu xác thực không xác định")
