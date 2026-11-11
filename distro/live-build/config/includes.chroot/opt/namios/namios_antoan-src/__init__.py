"""``namios_antoan`` — Trung tâm An toàn (SEC-1, xem
``docs/roadmap/NEW-FUNCTIONS-DIRECTION.md`` khối SEC-1): MỘT nơi hiển thị
trạng thái an toàn THẬT (cập nhật, tường lửa UFW, AppArmor, quét virus
ClamAV theo yêu cầu, sao lưu Kup) và MỞ đúng công cụ thật đã có trong ảnh —
module này KHÔNG tự chế lại tường lửa/AppArmor/scanner/backup, chỉ ĐỌC
trạng thái (``probes``) và MỞ/BẬT qua ``pkexec`` khi cần quyền (``actions``).

Cùng quy ước ``namios_assistant``/``namios_welcome``: ``probes``/``actions``
là Python thuần (test được không cần PySide6/display); ``ui``/``__main__``
CHỈ chạy trên desktop session thật có PySide6 + display.

TRUNG THỰC BẮT BUỘC (VN09-030, ``docs/SECURITY-DEFAULTS.md`` §1/§6): module
này KHÔNG BAO GIỜ hiển thị hoặc trả về chuỗi kiểu "an toàn tuyệt đối"/"chống
được 100% virus/mã độc". Mọi trạng thái "tốt" chỉ có nghĩa "lớp phòng thủ
này đang BẬT theo cấu hình đọc được lúc kiểm tra", không phải một bảo đảm."""

from __future__ import annotations

from namios_antoan import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_antoan.actions import ActionResult
from namios_antoan.probes import CardStatus

__all__ = ["CardStatus", "ActionResult"]
