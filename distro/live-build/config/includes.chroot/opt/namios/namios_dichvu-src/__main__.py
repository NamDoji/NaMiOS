"""Entry point ``python3 -m namios_dichvu`` — mở cửa sổ Cổng Dịch vụ Việt +
Trung tâm Ký số. CHỈ chạy trên desktop session thật (cần PySide6 + display) —
import ``namios_dichvu.ui`` bị trì hoãn tới trong ``main()`` để riêng việc
``import namios_dichvu`` (gói)/``namios_dichvu.catalog``/``namios_dichvu.
envcheck`` luôn import được, không cần PySide6 (cùng quy ước
``namios_assistant.__main__``/``namios_lich.__main__``).

Wrapper hệ thống ``/usr/bin/namios-dichvu`` (tạo bởi hook
``0308-namios-dichvu.hook.chroot``) ĐÃ tự kiểm ``import PySide6`` TRƯỚC khi
gọi lệnh này và **thoát 0 yên lặng** nếu thiếu (chỉ đạo phạm vi của wave này:
"fail-safe PySide6/xdg-open missing -> quiet exit 0" — khác
``namios_assistant`` (báo lỗi rõ + exit 1) nhưng ĐÚNG với quy ước mới hơn
``namios_lich`` cùng ngày 11/11/2026, xem docstring
``namios_lich.__main__``). ``main()`` ở đây lặp lại đúng hành vi "quiet exit
0" làm lớp phòng thủ thứ hai, phòng khi ai đó gọi trực tiếp
``python3 -m namios_dichvu`` mà bỏ qua wrapper."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        # Quiet exit 0 (không phải exit 1 kèm kdialog như namios_assistant) —
        # chỉ đạo phạm vi của wave này: thiếu PySide6 không được làm hỏng
        # trải nghiệm mở launcher (không popup lỗi gây hoảng, không mã thoát
        # báo "crash" cho desktop shell). Vẫn ghi một dòng stderr cho ai gỡ
        # lỗi từ terminal.
        print(
            "namios-dichvu: thiếu PySide6 trên máy này — không mở được giao diện "
            "(thoát lặng lẽ, không coi là lỗi).",
            file=sys.stderr,
        )
        return 0

    from namios_dichvu.ui import DichVuWindow

    app = QApplication(sys.argv)
    window = DichVuWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
