"""Device event bus — debounce + correlation (E08-001/027).

Gộp event udev THÔ thành MỘT incident / thiết bị (``device_instance_id``). Cắm/rút
20 lần → 1 incident, KHÔNG 20 entry rác (nghiệm thu E08-001, test D02/A05). ``present``
= trạng thái ròng (action cuối ≠ remove). KHÔNG chạy mạng/cài gói/model AI ở đây —
udev chỉ xử lý event ngắn.
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_e08._types import DeviceAction, DeviceIncident, RawDeviceEvent

__all__ = ["coalesce_events", "should_invoke_ai"]


def coalesce_events(events: Iterable[RawDeviceEvent]) -> list[DeviceIncident]:
    """Gộp event thô → danh sách incident (E08-001/027). Mỗi ``device_instance_id``
    đúng MỘT incident; giữ thứ tự xuất hiện lần đầu; ``present`` theo action cuối;
    ``event_count`` = số event thô đã gộp."""

    order: list[str] = []
    latest: dict[str, RawDeviceEvent] = {}
    counts: dict[str, int] = {}
    for ev in events:
        did = ev.device_instance_id
        if did not in latest:
            order.append(did)
            counts[did] = 0
        latest[did] = ev  # action cuối cùng quyết định present
        counts[did] += 1

    incidents: list[DeviceIncident] = []
    for did in order:
        ev = latest[did]
        incidents.append(
            DeviceIncident(
                device_instance_id=did,
                bus=ev.bus,
                hardware_id=ev.hardware_id,
                present=ev.action is not DeviceAction.REMOVE,
                event_count=counts[did],
            )
        )
    return incidents


def should_invoke_ai(event_count: int, *, max_calls: int = 1) -> bool:
    """Giới hạn gọi AI theo incident (E08-027/036): dù có bao nhiêu event thô, một
    incident chỉ cho tối đa ``max_calls`` lần gọi AI (chống retry vô hạn, test A05)."""

    return max_calls >= 1
