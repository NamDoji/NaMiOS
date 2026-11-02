"""Fake in-process D-Bus transport — dùng để test logic policy/caller-identity
KHI CHƯA CÓ D-Bus system bus thật (môi trường headless tại host build này).

M1-INTERFACES.md §7.5 chỉ yêu cầu M1 "hiện thực interface + policy, CHƯA cần
bus thật để test logic". ``FakeBusConnection`` mô phỏng đúng một thuộc tính
quan trọng của D-Bus thật: uid của caller được kernel gắn vào MỖI connection
(qua ``SO_PEERCRED``) tại lúc accept — ứng dụng gọi
``GetConnectionUnixUser(sender)`` để lấy uid đó, HOÀN TOÀN độc lập với bất kỳ
trường nào caller gửi trong message. Việc D-Bus thật tích hợp polkitd là
tích hợp M3 (BLOCKED tại host này) — ghi rõ trong phần "blocked" của báo cáo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from namios_helper.caller import CallerIdentity


@dataclass
class FakeBusConnection:
    """Một "kết nối" giả lập tới fake system bus, gắn cố định với một uid.

    Mô phỏng đúng thuộc tính của D-Bus thật: uid gắn vào CONNECTION (do
    kernel cấp khi accept socket), không phải vào từng message. Một
    connection không thể "tự đổi" uid của mình sau khi tạo.
    """

    uid: int
    unique_name: str

    def identity(self) -> CallerIdentity:
        return CallerIdentity(uid=self.uid, pid=None, exe_path=None)


@dataclass
class FakeSystemBus:
    """Fake system bus trong-tiến-trình: cấp connection theo uid, định tuyến
    method call tới một "object" (bất kỳ object implement đủ 4 method của
    ``SystemHelper``), và ghi lại lịch sử call để test introspection/audit."""

    _connections: dict[str, FakeBusConnection] = field(default_factory=dict)
    call_log: list[tuple[str, str, tuple[Any, ...]]] = field(default_factory=list)

    def connect(self, unique_name: str, uid: int) -> FakeBusConnection:
        conn = FakeBusConnection(uid=uid, unique_name=unique_name)
        self._connections[unique_name] = conn
        return conn

    def get_connection_unix_user(self, unique_name: str) -> int:
        """Tương đương ``org.freedesktop.DBus.GetConnectionUnixUser`` thật:
        tra uid theo TÊN KẾT NỐI (do bus cấp khi accept), KHÔNG theo tham số
        caller tự khai."""

        conn = self._connections.get(unique_name)
        if conn is None:
            raise LookupError(f"Không có connection tên {unique_name!r} trên fake bus")
        return conn.uid

    def call(self, sender_unique_name: str, method_name: str, *args: Any) -> CallerIdentity:
        """Ghi log + trả về ``CallerIdentity`` ĐÃ XÁC THỰC qua connection —
        hàm này KHÔNG thực hiện method, chỉ mô phỏng bước "bus xác định
        danh tính sender trước khi giao cho adaptor xử lý"."""

        self.call_log.append((sender_unique_name, method_name, args))
        uid = self.get_connection_unix_user(sender_unique_name)
        return CallerIdentity(uid=uid, pid=None, exe_path=None)
