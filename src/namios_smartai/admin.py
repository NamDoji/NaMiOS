"""Multiuser Administration (SAI-037).

Chính sách theo ĐƠN VỊ; KHÔNG admin một-cửa mặc định. Phân quyền tất định:
chỉ admin CÙNG đơn vị mới sửa được chính sách đơn vị đó; người hỗ trợ
(helpdesk) chỉ đọc log khi đơn vị bật thu-log và cùng đơn vị; duyệt R3/R4 theo
danh sách người được uỷ quyền.

Nghiệm thu: giáo viên (đơn vị A) KHÔNG sửa được chính sách kế toán (đơn vị B);
người hỗ trợ chỉ xem log được phân quyền.
"""

from __future__ import annotations

from namios_smartai._types import Principal, UnitPolicy

__all__ = [
    "can_edit_policy",
    "can_approve_r3_r4",
    "can_read_logs",
]


def _same_unit(principal: Principal, policy: UnitPolicy) -> bool:
    return principal.unit_id == policy.unit_id


def can_edit_policy(principal: Principal, policy: UnitPolicy) -> bool:
    """Sửa chính sách đơn vị: phải CÙNG đơn vị + nằm trong ``admin_users`` của
    chính đơn vị đó (SAI-037 — không có admin một-cửa chéo đơn vị)."""

    return _same_unit(principal, policy) and principal.user_id in policy.admin_users


def can_approve_r3_r4(principal: Principal, policy: UnitPolicy) -> bool:
    """Duyệt hành động R3/R4: cùng đơn vị + thuộc danh sách người được uỷ quyền."""

    return _same_unit(principal, policy) and principal.user_id in policy.approve_r3_r4_users


def can_read_logs(principal: Principal, policy: UnitPolicy) -> bool:
    """Đọc log đơn vị: phải CÙNG đơn vị; admin đơn vị luôn được; helpdesk chỉ
    khi đơn vị bật ``log_collection``. Khác đơn vị → luôn từ chối."""

    if not _same_unit(principal, policy):
        return False
    if principal.user_id in policy.admin_users:
        return True
    return "helpdesk" in principal.roles and policy.log_collection
