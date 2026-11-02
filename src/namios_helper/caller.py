"""Danh tính caller cho ``namios_helper`` (SEC-001).

Quy tắc bắt buộc (FACT CLAUDE.md, M1-INTERFACES §7.5): "Helper xác thực: danh
tính caller (uid qua D-Bus, không tin PID thô)". Vì vậy:

- ``CallerIdentity.uid`` PHẢI được cấp bởi *kênh truyền* (D-Bus connection
  credentials thật ở M3, hoặc :mod:`namios_helper.fakebus` khi test tại đây)
  — KHÔNG BAO GIỜ đọc từ một tham số do caller tự khai trong body request.
- ``pid``/``exe_path`` là thông tin PHỤ (chỉ để log/chẩn đoán), KHÔNG được
  dùng làm căn cứ cấp quyền — PID có thể bị tái sử dụng (race) hoặc giả mạo
  dễ hơn uid kernel cấp qua socket credentials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CallerIdentity:
    """Danh tính một caller đã được kênh truyền xác thực.

    ``uid``: uid thật của tiến trình gọi, do kernel cấp qua
    ``SO_PEERCRED``/D-Bus ``GetConnectionUnixUser`` (hoặc tương đương trong
    fake bus test) — nguồn DUY NHẤT dùng để quyết định quyền.
    ``pid``: CHỈ để log/chẩn đoán — KHÔNG BAO GIỜ dùng trong quyết định
    Polkit/allowlist (có thể bị tái sử dụng/giả mạo).
    """

    uid: int
    pid: int | None = None
    exe_path: str | None = None

    def is_root(self) -> bool:
        return self.uid == 0


def identity_from_untrusted_request(
    *, trusted_uid: int, requested_pid_claim: int | None = None
) -> CallerIdentity:
    """Dựng ``CallerIdentity`` CHỈ từ ``trusted_uid`` lấy từ kênh truyền.

    ``requested_pid_claim`` mô phỏng một trường ``pid`` mà caller CỐ TÌNH
    nhúng vào nội dung request (ví dụ để giả mạo root) — hàm này nhận tham
    số đó CHỈ để ghi log chẩn đoán (``pid``), KHÔNG dùng nó để suy ra
    ``uid``/quyền. Đây là điểm test quan trọng: dù ``requested_pid_claim``
    là gì, ``uid`` trả về luôn là ``trusted_uid`` do kênh truyền cấp.
    """

    return CallerIdentity(uid=trusted_uid, pid=requested_pid_claim)
