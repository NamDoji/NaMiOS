"""Mã lỗi ổn định RIÊNG của ``namios_pra`` (Phụ lục 06, PRA-001..044)."""

from __future__ import annotations

from enum import Enum

__all__ = ["PraErrorCode"]


class PraErrorCode(str, Enum):
    """Mã lỗi đặc thù PRA (KHÔNG đổi chuỗi sau phát hành)."""

    #: Suy diễn chức năng thiết bị chưa đo (vd coi copy=được vì in+scan được) — PRA-001.
    E_PRA_DEVICE_INFERRED = "E_PRA_DEVICE_INFERRED"
    #: Tuyến Office không đáp ứng nhu cầu (vd .xlsm macro gán Office web) — PRA-016.
    E_PRA_OFFICE_ROUTE_UNFIT = "E_PRA_OFFICE_ROUTE_UNFIT"
    #: Khác biệt fidelity nghĩa (số tiền/trang/chữ ký) — chặn lưu/in — PRA-017.
    E_PRA_FIDELITY_BLOCKING = "E_PRA_FIDELITY_BLOCKING"
    #: Nhận WPF/WinUI là native Linux khi chưa có bằng chứng — PRA-023.
    E_PRA_DOTNET_OVERCLAIM = "E_PRA_DOTNET_OVERCLAIM"
    #: Báo "đã in/đã nhận/đã nộp" khi mới ở giai đoạn sớm — PRA-032.
    E_PRA_PROGRESS_OVERCLAIM = "E_PRA_PROGRESS_OVERCLAIM"
