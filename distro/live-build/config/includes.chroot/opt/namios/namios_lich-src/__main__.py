"""Entry point ``python -m namios_lich`` — mở cửa sổ NaMiLịch.

CHỈ chạy trên desktop session thật (cần PySide6 + display). KHÔNG chạy trong
môi trường build/test headless (``ModuleNotFoundError: PySide6`` là dự kiến
ở đó) — import ``namios_lich.ui`` bị trì hoãn tới trong ``main()`` để
``import namios_lich`` (gói, logic ``lunar``/``holidays``) luôn import được
không cần GUI (xem ``tests/unit/lich/``, cùng cách ``namios_welcome`` đã
làm — ``namios_welcome/__main__.py``).

Wrapper ``/usr/bin/namios-lich`` (tạo bởi
``hooks/normal/0307-namios-lich.hook.chroot``) ĐÃ kiểm ``import PySide6``
trước khi gọi file này và thoát ``0`` yên lặng nếu thiếu — ``main()`` dưới
đây không CẦN tự kiểm lại, nhưng vẫn giữ import PySide6 bên trong hàm (không
phải ở top-level module) để file này luôn ``py_compile`` được + ``import
namios_lich.__main__`` không crash trên máy build thiếu PySide6."""

from __future__ import annotations

import sys

from namios_core.paths import config_dir


def main() -> int:
    from namios_lich.ui import NaMiLichWindow
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    app = QApplication(sys.argv)
    window = NaMiLichWindow(config_dir=config_dir())
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
