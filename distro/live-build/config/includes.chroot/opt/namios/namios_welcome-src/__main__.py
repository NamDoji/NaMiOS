"""Entry point ``python -m namios_welcome`` — khởi chạy wizard GUI.

CHỈ chạy trên desktop session thật (cần PySide6 + display). KHÔNG chạy
trong môi trường build/test headless (``ModuleNotFoundError: PySide6`` là
dự kiến ở đó) — import ``namios_welcome.ui`` bị trì hoãn tới trong
``main()`` để ``import namios_welcome`` (gói) và logic
``migrate``/``firstrun`` luôn import được không cần GUI.
"""

from __future__ import annotations

import sys
from pathlib import Path

from namios_core.paths import config_dir


def main() -> int:
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from namios_welcome.ui import WelcomeWizard

    app = QApplication(sys.argv)
    wizard = WelcomeWizard(config_dir=config_dir(), dest_home=Path.home())
    wizard.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
