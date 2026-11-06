"""Device Hub — năng lực TỪNG CHỨC NĂNG (PRA-001).

Mỗi máy đa chức năng khai in/scan/copy/fax RIÊNG; mức hỗ trợ mặc định
``UNTESTED``. Bất biến trung thực: in được + scan được KHÔNG tự suy ra copy
được (copy là chức năng do máy hoặc workflow NaMiOS thực hiện, phải kiểm riêng).

TÁI DÙNG ``namios_sys.DeviceFunctionStatus``.
"""

from __future__ import annotations

from namios_i18n import Lang, t
from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra._types import DeviceCapability, DeviceFunction, DeviceFunctionStatus

__all__ = ["function_status", "is_supported", "untested_message", "can_copy"]


def function_status(cap: DeviceCapability, func: DeviceFunction) -> DeviceFunctionStatus:
    """Mức hỗ trợ của MỘT chức năng. Không khai → ``UNTESTED`` (không suy diễn)."""

    return cap.functions.get(func, DeviceFunctionStatus.UNTESTED)


def is_supported(cap: DeviceCapability, func: DeviceFunction) -> bool:
    """``True`` CHỈ khi chức năng ở mức ``WORKS`` (partial/blocked/untested → False)."""

    return function_status(cap, func) == DeviceFunctionStatus.WORKS


def can_copy(cap: DeviceCapability) -> bool:
    """Copy CHỈ True khi chức năng COPY được kiểm ``WORKS`` — TUYỆT ĐỐI KHÔNG suy
    từ print+scan (nghiệm thu PRA-001)."""

    return function_status(cap, DeviceFunction.COPY) == DeviceFunctionStatus.WORKS


def untested_message(cap: DeviceCapability, func: DeviceFunction) -> str:
    return t("pra.device.untested", lang=Lang.VI, func=func.value, model=cap.model)
