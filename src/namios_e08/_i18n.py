"""Lớp common song ngữ của ``namios_e08`` (Phụ lục 08) — đăng ký qua
``namios_i18n.add_catalog`` khi import. Trường dữ liệu ``*_vi`` luôn tiếng Việt.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    "e08.driver.no_hwid": "Thiếu hardware-ID → không ghép driver (không đoán theo tên).",
    "e08.driver.matched": "Đã ghép driver ở tầng '{tier}' theo đúng hardware-ID + nguồn tin cậy.",
    "e08.driver.unsupported": (
        "Chưa có driver/backend hợp lệ cho thiết bị này — ghi 'unsupported', không bịa."
    ),
    "e08.install.source_fail": "Nguồn/quyền driver không đạt → dừng, chưa đụng hệ.",
    "e08.install.snapshot_fail": "Không chụp được snapshot → KHÔNG cài khi chưa có đường lùi.",
    "e08.install.apply_rollback": "Áp driver hỏng → đã rollback về trạng thái cũ.",
    "e08.install.functest_rollback": "Kiểm chức năng sau cài thất bại → đã rollback về cũ.",
    "e08.install.committed": "Cài driver đạt + kiểm chức năng OK → commit.",
}

_EN: dict[str, str] = {
    "e08.driver.no_hwid": "Missing hardware-ID → no driver match (never guess by name).",
    "e08.driver.matched": (
        "Matched a driver at tier '{tier}' by exact hardware-ID + trusted source."
    ),
    "e08.driver.unsupported": (
        "No valid driver/backend for this device — record 'unsupported', do not fake."
    ),
    "e08.install.source_fail": "Driver source/permission not OK → stop, system untouched.",
    "e08.install.snapshot_fail": (
        "Could not take a snapshot → do NOT install without a rollback path."
    ),
    "e08.install.apply_rollback": "Driver apply failed → rolled back to the previous state.",
    "e08.install.functest_rollback": "Post-install function test failed → rolled back.",
    "e08.install.committed": "Driver installed + function test OK → commit.",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
