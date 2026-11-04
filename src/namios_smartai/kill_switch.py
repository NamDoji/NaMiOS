"""Kill Switch (SAI-035).

Tắt ĐỘC LẬP từng thứ: model provider, tool, recipe, signing adapter, auto-repair,
release ring — KHÔNG phải tắt cả OS. Khi phát hiện sai dữ liệu/ghi file/chữ ký →
TỰ CHẶN phát hành kế tiếp. Dùng ``guard()`` ở các điểm nhạy cảm (orchestrator/
promotion/tool-broker) để từ chối an toàn khi một đối tượng bị tắt.

Nghiệm thu: thu hồi recipe đang pilot TRƯỚC khi bắt đầu tác vụ mới; tác vụ đang
chạy dừng ở điểm an toàn (caller kiểm ``guard`` giữa các bước).
"""

from __future__ import annotations

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import SwitchTarget

__all__ = ["KillSwitch", "WILDCARD"]

#: Tắt cả một LỚP đối tượng (vd mọi recipe) thay vì một tên cụ thể.
WILDCARD = "*"


class KillSwitch:
    """Sổ đăng ký trạng thái tắt (stateful). Mặc định mọi thứ BẬT."""

    def __init__(self) -> None:
        self._off: set[tuple[SwitchTarget, str]] = set()
        self._release_blocked: bool = False
        self._release_reason: str = ""

    def disable(self, target: SwitchTarget, name: str = WILDCARD) -> None:
        """Tắt ``name`` thuộc ``target`` (``WILDCARD`` = tắt cả lớp)."""

        self._off.add((target, name))

    def enable(self, target: SwitchTarget, name: str = WILDCARD) -> None:
        self._off.discard((target, name))

    def is_enabled(self, target: SwitchTarget, name: str = WILDCARD) -> bool:
        """``False`` nếu chính ``name`` bị tắt HOẶC cả lớp ``target`` bị tắt."""

        if (target, WILDCARD) in self._off:
            return False
        return (target, name) not in self._off

    def guard(self, target: SwitchTarget, name: str = WILDCARD) -> str | None:
        """Trả lý do VI nếu bị tắt (để caller chặn), hoặc ``None`` nếu được phép."""

        if self.is_enabled(target, name):
            return None
        label = name if name != WILDCARD else target.value
        return t("sai.killswitch.off", lang=Lang.VI, target=label)

    def block_release(self, reason: str = "") -> None:
        """Tự chặn phát hành kế tiếp (khi phát hiện sai dữ liệu/chữ ký)."""

        self._release_blocked = True
        self._release_reason = reason or t("sai.killswitch.release_blocked", lang=Lang.VI)

    def release_blocked(self) -> bool:
        return self._release_blocked

    def release_block_reason(self) -> str:
        return self._release_reason
