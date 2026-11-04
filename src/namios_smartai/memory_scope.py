"""Memory Scope — cách ly đa tenant (SAI-026).

Trí nhớ tách theo phạm vi: ``session``/``machine``/``org`` cách ly theo tenant
(chủ sở hữu), ``public`` ai cũng đọc. Dữ liệu một tổ chức KHÔNG chảy sang tổ
chức khác. Người dùng tự xem/xuất/xoá cấu hình của chính mình.

Nghiệm thu SAI-026: hai tenant trên cùng lab KHÔNG truy xuất được history/
recipe riêng của nhau.
"""

from __future__ import annotations

from typing import Any

from namios_smartai._types import MemoryScope

__all__ = ["MemoryStore"]


class MemoryStore:
    """Kho trí nhớ trong-bộ-nhớ có cách ly tenant. Khoá nội bộ
    ``(scope, owner, key)``; đọc non-public yêu cầu ``requester == owner``."""

    def __init__(self) -> None:
        self._data: dict[tuple[MemoryScope, str, str], Any] = {}

    def put(self, scope: MemoryScope, owner: str, key: str, value: Any) -> None:
        self._data[(scope, owner, key)] = value

    def get(self, scope: MemoryScope, owner: str, key: str, *, requester: str) -> Any:
        """Đọc; non-public → ``requester`` phải TRÙNG ``owner`` (khác tenant →
        ``None``, từ chối). PUBLIC đọc tự do."""

        if scope != MemoryScope.PUBLIC and requester != owner:
            return None
        return self._data.get((scope, owner, key))

    def list_keys(self, scope: MemoryScope, owner: str, *, requester: str) -> tuple[str, ...]:
        """Liệt kê key; cùng cách ly như ``get`` (khác tenant non-public → rỗng)."""

        if scope != MemoryScope.PUBLIC and requester != owner:
            return ()
        return tuple(sorted(k[2] for k in self._data if k[0] == scope and k[1] == owner))

    def export_tenant(self, owner: str, *, requester: str) -> dict[str, Any]:
        """Tự-phục-vụ: xuất TOÀN BỘ dữ liệu của CHÍNH tenant (mọi scope).
        ``requester`` phải TRÙNG ``owner`` — không ai xuất dữ liệu tenant khác."""

        if requester != owner:
            return {}
        return {
            f"{scope.value}/{key}": value
            for (scope, own, key), value in self._data.items()
            if own == owner
        }

    def delete_tenant(self, owner: str, *, requester: str) -> int:
        """Tự-phục-vụ: xoá toàn bộ dữ liệu của CHÍNH tenant. ``requester`` phải
        TRÙNG ``owner`` — không ai xoá dữ liệu tenant khác. Trả số bản ghi đã xoá."""

        if requester != owner:
            return 0
        keys = [k for k in self._data if k[1] == owner]
        for k in keys:
            del self._data[k]
        return len(keys)
