"""Hằng số D-Bus (DESIGN, M1-INTERFACES.md §7.5) — chỉ dữ liệu, dùng cho
test introspection "không có RunCommand / đúng 4 method typed". D-Bus system
bus THẬT không chạy ở host build này (headless) — việc đăng ký object thật
qua ``python-dbus``/``dbus-next`` lên system bus thật là tích hợp M3
(BLOCKED tại đây, ghi vào phần blocked)."""

from __future__ import annotations

from typing import Final

BUS_NAME: Final[str] = "org.namios.SystemHelper1"
OBJECT_PATH: Final[str] = "/org/namios/SystemHelper1"
INTERFACE_NAME: Final[str] = "org.namios.SystemHelper1"

#: Method D-Bus signature (chữ ký kiểu scalar/struct, KHÔNG mảng lệnh/argv
#: tự do) — ánh xạ 1-1 với §7.5. Khóa là tên method; giá trị là
#: ``(in_signature, out_signature)`` theo định dạng D-Bus.
METHOD_SIGNATURES: Final[dict[str, tuple[str, str]]] = {
    "GetSystemCapabilities": ("", "ssssb"),
    "PlanPackageInstall": ("s", "ss"),
    "ApplyApprovedPackagePlan": ("ss", "asb"),
    "GetUpdateStatus": ("", "asb"),
}

#: Danh sách method hợp lệ DUY NHẤT — bất kỳ tên nào khác (đặc biệt
#: ``"RunCommand"``) KHÔNG được xuất hiện trong introspection XML thật (M3)
#: hay trong ``PUBLIC_METHOD_NAMES`` (M1, kiểm tra được tại đây).
ALLOWED_METHOD_NAMES: Final[frozenset[str]] = frozenset(METHOD_SIGNATURES.keys())

#: Tên method bị CẤM TUYỆT ĐỐI — có mặt trong introspection là lỗi nghiêm
#: trọng (cho phép caller chạy lệnh tùy ý). Dùng trong test phủ định.
FORBIDDEN_METHOD_NAMES: Final[frozenset[str]] = frozenset(
    {"RunCommand", "RunShell", "Exec", "ExecCommand", "RunArbitrary"}
)
