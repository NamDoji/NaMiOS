"""``namios_doctor`` — thu thập capability report host THẬT (WP3).

Dùng bởi subcommand ``namios doctor --json``. KHÔNG bịa dữ liệu: mọi giá trị
đọc trực tiếp từ ``platform``/``os``/``shutil.which``/``/etc/os-release``/
``/dev/kvm`` tại thời điểm chạy. KHÔNG spawn process con, KHÔNG shell — chỉ
đọc thuộc tính hệ thống + tra PATH (``shutil.which``, không exec gì).
"""

from __future__ import annotations

from namios_doctor.capabilities import TOOLING_PROBE_NAMES, collect_capabilities
from namios_doctor.doctor import build_doctor_data

__all__ = [
    "TOOLING_PROBE_NAMES",
    "collect_capabilities",
    "build_doctor_data",
]
