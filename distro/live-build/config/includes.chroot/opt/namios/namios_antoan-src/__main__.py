"""Entry point ``python3 -m namios_antoan`` — mở cửa sổ Trung tâm An toàn.
CHỈ chạy trên desktop session thật (cần PySide6 + display) — import
``namios_antoan.ui`` bị trì hoãn tới trong ``main()`` để riêng việc
``import namios_antoan`` (gói)/``namios_antoan.probes``/``namios_antoan.
actions`` luôn import được, không cần PySide6 (cùng quy ước
``namios_assistant.__main__``).

Wrapper hệ thống ``/usr/bin/namios-antoan`` (tạo bởi hook
``0309-namios-antoan.hook.chroot``) đã tự kiểm tra ``import PySide6`` TRƯỚC
khi gọi lệnh này và báo lỗi rõ cho người dùng nếu thiếu — ``main()`` ở đây
không lặp lại việc đó, chỉ là lớp phòng thủ thứ hai nếu ai đó gọi trực tiếp
``python3 -m namios_antoan`` mà bỏ qua wrapper."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        print(
            "namios-antoan: thiếu PySide6 trên máy này — không mở được giao "
            "diện. Cài gói python3-pyside6.qtwidgets rồi thử lại.",
            file=sys.stderr,
        )
        return 1

    from namios_antoan.ui import AntoanWindow

    app = QApplication(sys.argv)
    window = AntoanWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
