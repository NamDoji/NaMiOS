"""WP7 — System-helper API typed (no RunCommand) + Polkit/D-Bus interface +
policy. Hiện thực mô-đun ``namios_system_helper`` (xem M1-INTERFACES.md §7.5,
SEC-001, CLI-004, B009).

Thiết kế tầng (quan trọng cho an toàn — SEC-001):

- :mod:`namios_helper.service` — ``SystemHelperService``: logic nghiệp vụ
  THUẦN, khớp 1-1 với Protocol ``namios_core.helper_types.SystemHelper``
  (chỉ 4 method: ``GetSystemCapabilities``/``PlanPackageInstall``/
  ``ApplyApprovedPackagePlan``/``GetUpdateStatus``). KHÔNG tự xác thực caller
  — tầng này giả định đã được gọi qua tầng xác thực dưới.
- :mod:`namios_helper.policy` — ánh xạ method → Polkit action + quyết định
  allow/deny (``PolkitAuthority`` Protocol + ``InMemoryPolkitAuthority`` giả
  lập để test logic policy khi chưa có polkitd thật).
- :mod:`namios_helper.caller` — danh tính caller (``CallerIdentity``: uid lấy
  từ *kênh truyền* — D-Bus connection credentials thật/giả lập — KHÔNG BAO
  GIỜ tin PID do caller tự khai trong tham số).
- :mod:`namios_helper.allowlist` — ``PackagePlanAllowlist``: khóa trỏ tới
  plan ĐÃ DUYỆT SẴN; caller KHÔNG được truyền tên package/repo/key tự do.
- :mod:`namios_helper.authenticated` — ``AuthenticatedSystemHelper``: tầng
  bọc ngoài, nhận ``CallerIdentity`` + thực hiện Polkit check TRƯỚC khi gọi
  xuống ``SystemHelperService``. Đây là tầng D-Bus adaptor (M3) sẽ gọi.
- :mod:`namios_helper.dbus_interface` — hằng số bus name/object path/
  interface/method signature (DESIGN, dùng cho introspection test — KHÔNG
  cần D-Bus thật để kiểm tra).
- :mod:`namios_helper.fakebus` — kênh truyền giả lập trong-tiến-trình để test
  (mô phỏng D-Bus ``GetConnectionUnixUser`` — cấp uid theo *connection*,
  không theo tham số caller tự khai).

KHÔNG có ``RunCommand`` ở bất kỳ tầng nào. Thao tác phân vùng KHÔNG đi qua
module này.
"""

from __future__ import annotations

from namios_helper.errors import HelperError, PermissionDeniedError, UnknownAllowlistKeyError

__all__ = [
    "HelperError",
    "PermissionDeniedError",
    "UnknownAllowlistKeyError",
]
