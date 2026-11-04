"""System Inventory — metadata-only (SAI-006, Phụ lục 04 M1).

Bất biến nghiệm thu SAI-006: inventory CHỈ thu thập METADATA (hệ điều hành,
kiến trúc CPU, kernel, trình duyệt, app/runtime, thiết bị/máy in/token/cổng
mạng ĐÃ KHAI BÁO) — KHÔNG BAO GIỜ đọc nội dung tài liệu, KHÔNG quét thư mục
cá nhân của người dùng (home/Documents/Desktop/Downloads), KHÔNG đọc lịch sử
trình duyệt, email, hay dữ liệu kế toán.

``read_fields`` là danh sách MINH BẠCH — đúng những trường đã thực sự được
đọc, theo tiền tố ``declared.*`` (do caller khai báo tường minh, ví dụ app
đang inventory) hoặc ``host.*`` (đọc qua ``platform`` stdlib, KHÔNG đụng
filesystem/network). ``out_of_scope`` LUÔN liệt kê các vùng dữ liệu cá nhân
bị TỪ CHỐI đọc một cách có chủ đích, để mọi lệnh gọi đều minh bạch về phạm
vi — không có "đọc ngầm" nằm ngoài hai danh sách này.

Hai hàm:

- :func:`inventory_from_declared` — builder THUẦN (pure), tất định, không
  gọi host/platform/filesystem/network. Dùng cho test/fixture cần xác định
  trước kết quả.
- :func:`collect_inventory` — như trên, cộng thêm (khi ``include_host=True``)
  đọc CHỈ 3 trường host qua ``platform.system()``/``platform.machine()``/
  ``platform.release()``. Không có lệnh gọi nào khác tới host.
"""

from __future__ import annotations

import platform

from namios_smartai._types import SystemInventory

__all__ = ["inventory_from_declared", "collect_inventory"]

#: Vùng dữ liệu cá nhân LUÔN bị từ chối đọc (SAI-006) — inventory một app/
#: runtime không kéo theo quét nội dung cá nhân của người dùng.
_OUT_OF_SCOPE: tuple[str, ...] = (
    "home_documents",
    "home_desktop",
    "home_downloads",
    "browser_history",
    "file_contents",
    "email",
    "accounting_data",
)


def _declared_read_fields(
    *,
    app_id: str | None,
    app_version: str | None,
    runtime: str | None,
    browser: str | None,
    devices: tuple[str, ...],
    printers: tuple[str, ...],
    tokens: tuple[str, ...],
    network_ports: tuple[str, ...],
) -> tuple[str, ...]:
    """Liệt kê CHÍNH XÁC các trường ``declared.*`` đã được caller cung cấp
    (không rỗng/None) — minh bạch những gì thực sự được ghi vào inventory."""

    out: list[str] = []
    if app_id is not None:
        out.append("declared.app_id")
    if app_version is not None:
        out.append("declared.app_version")
    if runtime is not None:
        out.append("declared.runtime")
    if browser is not None:
        out.append("declared.browser")
    if devices:
        out.append("declared.devices")
    if printers:
        out.append("declared.printers")
    if tokens:
        out.append("declared.tokens")
    if network_ports:
        out.append("declared.network_ports")
    return tuple(out)


def inventory_from_declared(
    *,
    app_id: str | None = None,
    app_version: str | None = None,
    runtime: str | None = None,
    browser: str | None = None,
    devices: tuple[str, ...] = (),
    printers: tuple[str, ...] = (),
    tokens: tuple[str, ...] = (),
    network_ports: tuple[str, ...] = (),
) -> SystemInventory:
    """Dựng :class:`SystemInventory` THUẦN từ các trường đã khai báo.

    KHÔNG gọi host/``platform``/filesystem/network — tất định 100%, dùng cho
    test/fixture. ``os``/``cpu_arch`` giữ ``"unknown"`` (host không được đọc
    ở đây). ``device_scope``: thiết bị/máy in/token/cổng mạng chỉ phản ánh
    đúng những gì caller truyền vào — KHÔNG tự dò quét.
    """

    read_fields = _declared_read_fields(
        app_id=app_id,
        app_version=app_version,
        runtime=runtime,
        browser=browser,
        devices=devices,
        printers=printers,
        tokens=tokens,
        network_ports=network_ports,
    )
    return SystemInventory(
        os="unknown",
        cpu_arch="unknown",
        kernel=None,
        browser=browser,
        app_id=app_id,
        app_version=app_version,
        runtime=runtime,
        devices=tuple(devices),
        printers=tuple(printers),
        tokens=tuple(tokens),
        network_ports=tuple(network_ports),
        read_fields=read_fields,
        out_of_scope=_OUT_OF_SCOPE,
    )


def collect_inventory(
    *,
    app_id: str | None = None,
    app_version: str | None = None,
    runtime: str | None = None,
    browser: str | None = None,
    devices: tuple[str, ...] = (),
    printers: tuple[str, ...] = (),
    tokens: tuple[str, ...] = (),
    network_ports: tuple[str, ...] = (),
    include_host: bool = True,
) -> SystemInventory:
    """Dựng :class:`SystemInventory` từ khai báo, cộng thêm host metadata.

    Khi ``include_host=True``, đọc THÊM đúng 3 trường qua stdlib ``platform``:
    ``platform.system()`` → ``os``, ``platform.machine()`` → ``cpu_arch``,
    ``platform.release()`` → ``kernel``; thêm ``"host.os"``/``"host.cpu_arch"``/
    ``"host.kernel"`` vào ``read_fields``. KHÔNG có lệnh host/filesystem/
    network nào khác. ``out_of_scope`` giữ nguyên bộ vùng cá nhân bị từ chối
    đọc; ``device_scope`` vẫn chỉ ghi nhận thiết bị/máy in/token đã khai báo
    (không tự dò quét) dù ``include_host`` là True hay False.
    """

    declared = inventory_from_declared(
        app_id=app_id,
        app_version=app_version,
        runtime=runtime,
        browser=browser,
        devices=devices,
        printers=printers,
        tokens=tokens,
        network_ports=network_ports,
    )

    if not include_host:
        return declared

    host_fields = ("host.os", "host.cpu_arch", "host.kernel")
    return SystemInventory(
        os=platform.system(),
        cpu_arch=platform.machine(),
        kernel=platform.release(),
        browser=declared.browser,
        app_id=declared.app_id,
        app_version=declared.app_version,
        runtime=declared.runtime,
        devices=declared.devices,
        printers=declared.printers,
        tokens=declared.tokens,
        network_ports=declared.network_ports,
        read_fields=declared.read_fields + host_fields,
        out_of_scope=declared.out_of_scope,
    )
