"""Tách vòng đời + recheck trigger (ODC-001/020/033).

Office/templates/extension/font/model-AI/OS mỗi thứ version + ring + rollback RIÊNG.
Đổi MỘT thành phần chỉ làm ``needs_retest`` đúng VÙNG ẢNH HƯỞNG — KHÔNG hạ toàn hệ:
- Đổi bộ lọc Office → chỉ workflow TÀI LIỆU, KHÔNG rớt Wi‑Fi (ODC-020 nghiệm thu).
- Cập nhật kernel → card Wi‑Fi/thiết bị cần kiểm lại, KHÔNG hạ file Office không phụ
  thuộc card (ODC-033 nghiệm thu, test T13).
- Office lỗi KHÔNG chặn OS boot (ODC-001) — gói tách rời.
"""

from __future__ import annotations

from enum import Enum

from namios_odc._types import Component, PackageRelease

__all__ = [
    "WorkflowDomain",
    "RECHECK_MAP",
    "can_rollback",
    "office_failure_blocks_os",
    "needs_retest_domains",
]


class WorkflowDomain(str, Enum):
    """Vùng workflow bị ảnh hưởng khi một thành phần đổi (ODC-033)."""

    DOCUMENT = "document"
    PRINT = "print"
    SCAN = "scan"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"
    DEVICE = "device"
    AI = "ai"


#: Ánh xạ thành phần ĐỔI → vùng phải kiểm lại (ODC-033). Cố ý HẸP: mỗi thành phần
#: chỉ chạm vùng liên quan trực tiếp, không lan ra vùng độc lập.
RECHECK_MAP: dict[Component, frozenset[WorkflowDomain]] = {
    Component.OFFICE: frozenset({WorkflowDomain.DOCUMENT}),
    Component.TEMPLATES: frozenset({WorkflowDomain.DOCUMENT}),
    Component.EXTENSION: frozenset({WorkflowDomain.DOCUMENT}),
    Component.FONT: frozenset({WorkflowDomain.DOCUMENT}),
    Component.AI_MODEL: frozenset(
        {WorkflowDomain.AI}
    ),  # AI chỉ tư vấn — không hạ fidelity/thiết bị
    Component.OS_KERNEL: frozenset(
        {
            WorkflowDomain.NETWORK,
            WorkflowDomain.BLUETOOTH,
            WorkflowDomain.PRINT,
            WorkflowDomain.SCAN,
            WorkflowDomain.DEVICE,
        }
    ),  # driver phụ thuộc kernel — KHÔNG gồm DOCUMENT
    Component.FIRMWARE: frozenset({WorkflowDomain.DEVICE}),
    Component.PRINT_STACK: frozenset({WorkflowDomain.PRINT, WorkflowDomain.SCAN}),
    Component.NETWORK_STACK: frozenset({WorkflowDomain.NETWORK}),
    Component.BLUETOOTH_STACK: frozenset({WorkflowDomain.BLUETOOTH}),
    Component.DEVICE_MODEL: frozenset({WorkflowDomain.DEVICE}),
}


def can_rollback(release: PackageRelease) -> bool:
    """Gói có rollback được không (ODC-001). True chỉ khi khai rõ version quay lại."""

    return bool(release.rollback_to.strip())


def office_failure_blocks_os() -> bool:
    """Office lỗi có chặn OS boot không (ODC-001). KHÔNG — gói Office tách rời, hỏng
    thì chỉ mất app Office, NaMiOS vẫn boot."""

    return False


def needs_retest_domains(changed: Component) -> frozenset[WorkflowDomain]:
    """Đổi ``changed`` → các vùng workflow phải ``needs_retest`` (ODC-033). Thành
    phần lạ (enum mới) → rỗng theo bảng; KHÔNG lan toàn hệ."""

    return RECHECK_MAP.get(changed, frozenset())
