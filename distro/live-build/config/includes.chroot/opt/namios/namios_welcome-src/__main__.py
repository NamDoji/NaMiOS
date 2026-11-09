"""Entry point ``python -m namios_welcome`` — khởi chạy wizard GUI.

CHỈ chạy trên desktop session thật (cần PySide6 + display). KHÔNG chạy
trong môi trường build/test headless (``ModuleNotFoundError: PySide6`` là
dự kiến ở đó) — import ``namios_welcome.ui`` bị trì hoãn tới trong
``main()`` để ``import namios_welcome`` (gói) và logic
``migrate``/``firstrun`` luôn import được không cần GUI.

CHẶN MỞ LẠI MỖI LẦN ĐĂNG NHẬP (Phụ lục 13 §6, "tiếp cận nhẹ nhàng"):
``etc/skel/.config/autostart/namios-welcome.desktop`` tự chạy lệnh này ở
MỌI lần đăng nhập KDE (XDG autostart không có cờ "chỉ 1 lần"). ``main()``
kiểm tra ``WelcomeDoneMarker`` (``~/.config/namios/welcome-done``) TRƯỚC
khi import PySide6/mở cửa sổ — nếu đã chạy xong một lần trước đó thì thoát
ngay ``0``, không có cửa sổ nào chớp lên. ``WelcomeWizard`` tự ghi marker
này khi đóng (xem ``namios_welcome.ui.WelcomeWizard._mark_welcome_done``).
"""

from __future__ import annotations

import sys
from pathlib import Path

from namios_core.paths import config_dir
from namios_welcome.firstrun import WelcomeDoneMarker


def main() -> int:
    cfg_dir = config_dir()
    if WelcomeDoneMarker(cfg_dir).is_done():
        # Đã chào mừng xong ở lần đăng nhập trước — không tự mở lại (người
        # dùng vẫn chạy lại thủ công được bất cứ lúc nào bằng lệnh
        # `namios-welcome`). KHÔNG import PySide6 ở nhánh này — tránh mở
        # QApplication/hiện cửa sổ rồi mới đóng (tránh "chớp màn hình").
        return 0

    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

    from namios_welcome.ui import WelcomeWizard

    app = QApplication(sys.argv)
    wizard = WelcomeWizard(config_dir=cfg_dir, dest_home=Path.home())
    wizard.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
