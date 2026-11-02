"""Lỗi hiện thực riêng của ``namios_planner`` (KHÔNG phải Protocol dùng
chung — ``namios_core`` chỉ khai báo kiểu, không có exception type cho
``build_plan``). ``code`` PHẢI là một giá trị ``namios_core.errors.ErrorCode``
để caller (CLI — WP3) map sang exit code đúng §2/§3.
"""

from __future__ import annotations

from namios_core.errors import ErrorCode

__all__ = ["PlanBuildError"]


class PlanBuildError(Exception):
    """``build_plan`` không thể tạo plan (vd. hồ sơ đã bị thu hồi, recipe bị
    tầng ngữ nghĩa từ chối). KHÔNG dùng để báo lỗi "stale lúc apply" — đó là
    ``ApplyCheck(ok=False, ...)`` trả về từ ``verify_at_apply`` theo Protocol,
    không phải exception."""

    def __init__(self, code: ErrorCode, message_vi: str) -> None:
        super().__init__(message_vi)
        self.code = code
        self.message_vi = message_vi
