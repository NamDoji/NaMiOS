"""Mã lỗi ổn định RIÊNG của ``namios_smartai`` (Phụ lục 04, SAI-001..042).

Giống ``namios_eco._errors``/``namios_compat._errors``: chỉ mã cho vi phạm đặc
thù SmartAI không có tương đương trong ``namios_core.errors.ErrorCode``. Vi phạm
khớp ngữ nghĩa có sẵn dùng thẳng ``ErrorCode``. ``ValidationError.code`` là
``str`` nên trộn mã hai enum trong cùng list là hợp lệ.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["SaiErrorCode"]


class SaiErrorCode(str, Enum):
    """Mã lỗi ổn định đặc thù SmartAI (KHÔNG đổi chuỗi sau phát hành)."""

    #: Policy-as-Code (SAI-039) từ chối hành động (deny ưu tiên).
    E_SAI_POLICY_DENY = "E_SAI_POLICY_DENY"
    #: Hành động cần sự chấp thuận người dùng chưa có (SAI-017 consent gate).
    E_SAI_CONSENT_REQUIRED = "E_SAI_CONSENT_REQUIRED"
    #: Hành động R4 (ký/nộp/thanh toán) thiếu xác nhận giao dịch cụ thể (SAI-017).
    E_SAI_RISK_UNCONFIRMED = "E_SAI_RISK_UNCONFIRMED"
    #: Gọi tool không đăng ký trong Tool Registry (SAI-015).
    E_SAI_TOOL_UNKNOWN = "E_SAI_TOOL_UNKNOWN"
    #: Tham số tool ngoài schema / sai kiểu (SAI-040 fail-closed).
    E_SAI_TOOL_SCHEMA = "E_SAI_TOOL_SCHEMA"
    #: Tool truy cập path/URL/thiết bị ngoài phạm vi cho phép (SAI-015/016).
    E_SAI_TOOL_SCOPE = "E_SAI_TOOL_SCOPE"
    #: Capability token hết hạn / đã thu hồi / đã dùng (one-time) (SAI-016).
    E_SAI_CAP_EXPIRED = "E_SAI_CAP_EXPIRED"
    #: Capability token không phủ phạm vi yêu cầu (SAI-016).
    E_SAI_CAP_SCOPE = "E_SAI_CAP_SCOPE"
    #: Chuyển trạng thái task không hợp lệ (SAI-003 state machine).
    E_SAI_STATE_TRANSITION = "E_SAI_STATE_TRANSITION"
    #: Phát hiện mưu đồ prompt-injection trong dữ liệu không tin cậy (SAI-019).
    E_SAI_INJECTION_BLOCKED = "E_SAI_INJECTION_BLOCKED"
    #: Recipe thiếu điều kiện cấu trúc để publish (SAI-041: source/hash/rollback).
    E_SAI_RECIPE_UNPUBLISHABLE = "E_SAI_RECIPE_UNPUBLISHABLE"
    #: Promotion gate từ chối nâng trạng thái (SAI-012: thiếu evidence/nghiệp vụ/AI-label).
    E_SAI_PROMOTION_DENIED = "E_SAI_PROMOTION_DENIED"
    #: Tìm-kiếm-sửa có giới hạn DỪNG (SAI-010: dữ liệu sai/license/bảo mật/vendor/ngân sách).
    E_SAI_REPAIR_STOPPED = "E_SAI_REPAIR_STOPPED"
