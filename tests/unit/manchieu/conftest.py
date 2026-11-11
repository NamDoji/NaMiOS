"""Conftest riêng cho test ``namios_manchieu``.

Cùng lý do/khuôn ``tests/unit/lich/conftest.py``: NaMiLịch/Máy chiếu & Màn
hình ngoài là module MỚI, phạm vi giao việc CHỈ gồm thư mục staging
``distro/live-build/config/includes.chroot/opt/namios/namios_manchieu-src``
(hậu tố ``-src`` — tên thư mục không phải tên gói Python hợp lệ, giống
``namios_lich-src`` TRƯỚC khi hook ``cp -a`` đổi tên lúc build ảnh) + hook +
desktop + doc — KHÔNG có mirror ``src/namios_manchieu`` nào được tạo thêm,
để không mở rộng phạm vi ngoài danh sách file được giao, và KHÔNG sửa
``pyproject.toml`` (cấu hình dùng chung toàn repo).

Conftest này nạp trực tiếp thư mục staging đó vào
``sys.modules["namios_manchieu"]`` bằng ``importlib.util`` (đăng ký
``submodule_search_locations`` đúng cách Python nạp package) — KHÔNG copy/
symlink file nào. Sau khi conftest này chạy, mọi test dưới
``tests/unit/manchieu/`` import ``namios_manchieu``/``namios_manchieu.
display``/``namios_manchieu.backend`` bình thường như một package thật."""

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
    / "namios_manchieu-src"
)


def _register_namios_manchieu_package() -> None:
    if "namios_manchieu" in sys.modules:
        return
    init_file = _SRC_DIR / "__init__.py"
    if not init_file.exists():
        raise ImportError(
            f"Khong tim thay {init_file} - kiem tra duong dan staging namios_manchieu-src"
        )
    spec = importlib.util.spec_from_file_location(
        "namios_manchieu", init_file, submodule_search_locations=[str(_SRC_DIR)]
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Khong the tao spec cho namios_manchieu tu {_SRC_DIR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["namios_manchieu"] = module
    spec.loader.exec_module(module)


_register_namios_manchieu_package()
