"""Conftest riêng cho test ``namios_lich``.

Mọi module khác (``namios_welcome``, ``namios_core``...) có một mirror
``src/<tên_gói>/`` ở repo gốc với TÊN GÓI ĐÚNG (không hậu tố ``-src``) đã nằm
trong ``pythonpath`` của ``pyproject.toml`` — đó là lý do ``tests/unit/welcome``
import được ``namios_welcome`` thẳng. NaMiLịch là module MỚI, phạm vi giao
việc CHỈ gồm thư mục staging
``distro/live-build/config/includes.chroot/opt/namios/namios_lich-src``
(hậu tố ``-src`` — tên thư mục không phải tên gói Python hợp lệ, giống
``namios_welcome-src`` TRƯỚC khi hook ``cp -a`` đổi tên lúc build ảnh) + hook
+ desktop + doc — KHÔNG có mirror ``src/namios_lich`` nào được tạo thêm, để
không mở rộng phạm vi ngoài danh sách file được giao.

Conftest này nạp trực tiếp thư mục staging đó vào ``sys.modules["namios_lich"]``
bằng ``importlib.util`` (đăng ký ``submodule_search_locations`` đúng cách
Python nạp package) — KHÔNG sửa ``pyproject.toml`` (cấu hình dùng chung toàn
repo), KHÔNG copy/symlink file nào. Sau khi conftest này chạy, mọi test dưới
``tests/unit/lich/`` import ``namios_lich``/``namios_lich.lunar``/
``namios_lich.holidays`` bình thường như một package thật."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SRC_DIR = (
    Path(__file__).resolve().parents[3]
    / "distro"
    / "live-build"
    / "config"
    / "includes.chroot"
    / "opt"
    / "namios"
    / "namios_lich-src"
)


def _register_namios_lich_package() -> None:
    if "namios_lich" in sys.modules:
        return
    init_file = _SRC_DIR / "__init__.py"
    if not init_file.exists():
        raise ImportError(
            f"Khong tim thay {init_file} - kiem tra duong dan staging namios_lich-src"
        )
    spec = importlib.util.spec_from_file_location(
        "namios_lich", init_file, submodule_search_locations=[str(_SRC_DIR)]
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Khong the tao spec cho namios_lich tu {_SRC_DIR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["namios_lich"] = module
    spec.loader.exec_module(module)


_register_namios_lich_package()
