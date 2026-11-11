"""Entry point ``python3 -m namios_assistant`` — mở cửa sổ chat NaMiOS
Assistant. CHỈ chạy trên desktop session thật (cần PySide6 + display) — import
``namios_assistant.ui`` bị trì hoãn tới trong ``main()`` để riêng việc
``import namios_assistant`` (gói)/``namios_assistant.engine``/``config`` luôn
import được, không cần PySide6 (cùng quy ước ``namios_welcome.__main__``).

Wrapper hệ thống ``/usr/bin/namios-assistant`` (tạo bởi hook
``0305-namios-assistant.hook.chroot``) đã tự kiểm tra ``import PySide6`` TRƯỚC
khi gọi lệnh này và báo lỗi rõ cho người dùng nếu thiếu — ``main()`` ở đây
không lặp lại việc đó, chỉ là lớp phòng thủ thứ hai nếu ai đó gọi trực tiếp
``python3 -m namios_assistant`` mà bỏ qua wrapper."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        print(
            "namios-assistant: thiếu PySide6 trên máy này — không mở được giao "
            "diện. Cài gói python3-pyside6.qtwidgets rồi thử lại.",
            file=sys.stderr,
        )
        return 1

    from namios_assistant.ui import AssistantWindow

    app = QApplication(sys.argv)
    window = AssistantWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
