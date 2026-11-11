"""Entry point ``python3 -m namios_manchieu`` — mở cửa sổ "Máy chiếu & Màn
hình ngoài". CHỈ chạy trên desktop session thật (cần PySide6 + display) —
import ``namios_manchieu.ui`` bị trì hoãn tới trong ``main()`` để riêng việc
``import namios_manchieu``/``namios_manchieu.display``/``namios_manchieu.
backend`` luôn import được, không cần PySide6 (cùng quy ước
``namios_antoan.__main__``/``namios_lich.__main__``).

Wrapper hệ thống ``/usr/bin/namios-manchieu`` (tạo bởi hook
``0311-namios-manchieu.hook.chroot``) đã tự kiểm tra ``import PySide6`` TRƯỚC
khi gọi lệnh này và báo lỗi rõ cho người dùng nếu thiếu — ``main()`` ở đây
không lặp lại việc đó, chỉ là lớp phòng thủ thứ hai nếu ai đó gọi trực tiếp
``python3 -m namios_manchieu`` mà bỏ qua wrapper."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        print(
            "namios-manchieu: thiếu PySide6 trên máy này — không mở được giao "
            "diện. Cài gói python3-pyside6.qtwidgets rồi thử lại.",
            file=sys.stderr,
        )
        return 1

    from namios_manchieu.ui import ManChieuWindow

    app = QApplication(sys.argv)
    window = ManChieuWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
