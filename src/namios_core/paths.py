"""Layout thư mục dữ liệu + hằng số XDG (§11.3) — FACT + DESIGN.

Mọi hàm trả path đã resolve theo biến môi trường ``$XDG_*`` hiện tại
(KHÔNG hardcode ``/home/<name>``; không nối chuỗi không kiểm tra —
FACT §11.3/SEC-002). Path do caller cung cấp (ví dụ tên app/instance người
dùng chọn) PHẢI còn đi qua ``namios_security.resolve_within()`` (§8) trước
khi mở — module này chỉ tính thư mục GỐC, không tự mở/ghi file.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Tên ứng dụng dùng xuyên suốt CLI/path/envelope — nguồn DUY NHẤT, KHÔNG
#: hardcode "namios" rải rác ở các module khác.
APP_NAME = "namios"

STATE_DB_FILENAME = "state.sqlite3"
LOG_MAX_BYTES_DEFAULT = 100 * 1024 * 1024
LOG_MAX_AGE_DAYS_DEFAULT = 14


def _xdg_base(env_var: str, fallback_relative: str) -> Path:
    """Trả thư mục base cho một biến XDG, dùng giá trị môi trường nếu có,
    nếu không thì fallback theo chuẩn XDG dưới home của người dùng hiện tại
    (``Path.home()`` — không phải chuỗi hardcode)."""

    value = os.environ.get(env_var)
    if value:
        return Path(value)
    return Path.home() / fallback_relative


def config_dir() -> Path:
    """``$XDG_CONFIG_HOME/namios/`` (≈ ``~/.config/namios/``)."""

    return _xdg_base("XDG_CONFIG_HOME", ".config") / APP_NAME


def prefixes_dir() -> Path:
    """``$XDG_DATA_HOME/namios/prefixes/`` — caller tự nối
    ``<app-id>/<instance-id>`` qua ``resolve_within`` trước khi dùng."""

    return _xdg_base("XDG_DATA_HOME", ".local/share") / APP_NAME / "prefixes"


def state_db_path() -> Path:
    """``$XDG_DATA_HOME/namios/state.sqlite3`` — transaction/launcher/state;
    KHÔNG chứa mật khẩu."""

    return _xdg_base("XDG_DATA_HOME", ".local/share") / APP_NAME / STATE_DB_FILENAME


def cache_dir() -> Path:
    """``$XDG_CACHE_HOME/namios/`` — download/staging có TTL + hạn mức."""

    return _xdg_base("XDG_CACHE_HOME", ".cache") / APP_NAME


def logs_dir() -> Path:
    """``$XDG_STATE_HOME/namios/logs/`` — log đã lọc (redacted)."""

    return _xdg_base("XDG_STATE_HOME", ".local/state") / APP_NAME / "logs"


def share_ro_dir() -> Path:
    """``/usr/share/namios/`` — tài nguyên package chỉ đọc."""

    return Path("/usr/share") / APP_NAME


def system_var_dir() -> Path:
    """``/var/lib/namios/`` — metadata hệ thống/cache root; KHÔNG làm prefix user."""

    return Path("/var/lib") / APP_NAME
