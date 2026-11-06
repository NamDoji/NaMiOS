"""Ngữ cảnh làm việc có GIỚI HẠN cho SmartAI (SYS-029).

SmartAI chỉ "thấy"/đọc được tài nguyên (cửa sổ/app/tệp/thiết bị) đã được CẤP
tường minh hoặc policy cho phép — KHÔNG mặc định đọc màn hình, bàn phím hay mọi
tệp. Mặc định rỗng: chưa cấp gì thì không đụng được gì.

Nghiệm thu SYS-029: hai cửa sổ mở cùng lúc, cấp quyền cửa sổ A → SmartAI đọc
được A nhưng KHÔNG đọc được cửa sổ B chưa cấp.
"""

from __future__ import annotations

from namios_sys._types import ContextResource, ResourceKind

__all__ = ["WorkContext"]


class WorkContext:
    """Phạm vi tài nguyên SmartAI được phép đụng. Mặc định RỖNG (deny-by-default);
    chỉ ``grant`` mới mở, ``revoke`` đóng lại."""

    def __init__(self) -> None:
        self._granted: set[tuple[ResourceKind, str]] = set()

    @staticmethod
    def _key(res: ContextResource) -> tuple[ResourceKind, str]:
        return (res.kind, res.resource_id)

    def grant(self, res: ContextResource) -> None:
        self._granted.add(self._key(res))

    def revoke(self, res: ContextResource) -> None:
        self._granted.discard(self._key(res))

    def can_access(self, res: ContextResource) -> bool:
        """``True`` CHỈ khi tài nguyên đã được cấp tường minh (SYS-029)."""

        return self._key(res) in self._granted

    def read(self, res: ContextResource) -> ContextResource | None:
        """Trả tài nguyên nếu được cấp, ngược lại ``None`` (từ chối đọc) — SmartAI
        KHÔNG tự đọc tài nguyên chưa cấp."""

        return res if self.can_access(res) else None

    def granted(self) -> tuple[ContextResource, ...]:
        """Danh sách tài nguyên đang được cấp (thứ tự ổn định) — minh bạch phạm vi."""

        return tuple(ContextResource(kind=k, resource_id=rid) for (k, rid) in sorted(self._granted))
