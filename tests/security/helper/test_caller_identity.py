"""SEC-01: danh tính caller PHẢI lấy từ kênh truyền (uid gắn vào connection),
KHÔNG BAO GIỜ tin một trường ``pid``/``uid`` do caller tự khai trong request."""

from __future__ import annotations

from namios_helper.caller import CallerIdentity, identity_from_untrusted_request
from namios_helper.fakebus import FakeSystemBus


def test_identity_from_untrusted_request_bo_qua_pid_tu_khai() -> None:
    # Caller tự khai pid=1 (giả mạo "tiến trình của root") — hàm PHẢI chỉ
    # dùng trusted_uid cho uid, pid chỉ được giữ lại để log.
    identity = identity_from_untrusted_request(trusted_uid=2000, requested_pid_claim=1)
    assert identity.uid == 2000
    assert identity.pid == 1  # giữ lại để chẩn đoán, KHÔNG dùng để cấp quyền
    assert not identity.is_root()


def test_fake_bus_uid_gan_theo_connection_khong_theo_tham_so_call() -> None:
    bus = FakeSystemBus()
    bus.connect(":1.100", uid=1000)

    # Dù method call có tham số nào (kể cả cố tình truyền uid=0 trong args),
    # danh tính trả về PHẢI vẫn là uid của CONNECTION (1000), không phải
    # một giá trị trong args.
    identity = bus.call(":1.100", "PlanPackageInstall", {"uid": 0, "allowlist_key": "x"})
    assert identity.uid == 1000
    assert identity.uid != 0


def test_fake_bus_khong_the_tra_uid_cho_connection_khong_ton_tai() -> None:
    bus = FakeSystemBus()
    try:
        bus.get_connection_unix_user(":9.999")
    except LookupError:
        pass
    else:
        raise AssertionError("Phải từ chối connection không tồn tại trên fake bus")


def test_caller_identity_la_frozen_khong_sua_duoc() -> None:
    identity = CallerIdentity(uid=1000, pid=42)
    try:
        identity.uid = 0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("CallerIdentity phải bất biến (frozen dataclass)")
