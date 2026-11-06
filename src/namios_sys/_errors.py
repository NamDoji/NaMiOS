"""Mã lỗi ổn định RIÊNG của ``namios_sys`` (Phụ lục 05, SYS-001..042).

Giống ``namios_eco``/``namios_compat``/``namios_smartai``: chỉ mã cho vi phạm
đặc thù tầng hệ điều hành không có tương đương trong ``namios_core.errors``.
``ValidationError.code`` là ``str`` nên trộn mã nhiều enum trong một list hợp lệ.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["SysErrorCode"]


class SysErrorCode(str, Enum):
    """Mã lỗi ổn định đặc thù SYS (KHÔNG đổi chuỗi sau phát hành)."""

    #: Action không nằm trong ActionKind đã đăng ký (SYS-001).
    E_SYS_ACTION_UNKNOWN = "E_SYS_ACTION_UNKNOWN"
    #: Chưa nối handler thật cho action → chặn trung thực (cần desktop/thiết bị).
    E_SYS_NO_HANDLER = "E_SYS_NO_HANDLER"
    #: Policy tổ chức từ chối hành động (SYS-025/036).
    E_SYS_ACTION_DENIED = "E_SYS_ACTION_DENIED"
    #: app_route thiếu nguồn (installer_hash/publisher) khi cần (SYS-037).
    E_SYS_ROUTE_NO_SOURCE = "E_SYS_ROUTE_NO_SOURCE"
    #: app_route thiếu version — không khớp được compat profile (SYS-008/037).
    E_SYS_ROUTE_NO_VERSION = "E_SYS_ROUTE_NO_VERSION"
    #: Bước workflow "completed/success" nhưng thiếu evidence (SYS-013/037).
    E_SYS_STEP_NO_EVIDENCE = "E_SYS_STEP_NO_EVIDENCE"
    #: Dòng capability tự nhận usable khi chưa đủ bằng chứng (SYS-038).
    E_SYS_CAPABILITY_OVERCLAIM = "E_SYS_CAPABILITY_OVERCLAIM"
