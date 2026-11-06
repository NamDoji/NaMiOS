"""Action Broker chung tầng desktop (SYS-001/002).

Một broker DUY NHẤT nhận ``ActionRequest`` (mở tệp/app, in, quét, chia sẻ, mở
URL, nối ổ mạng) và trả ``ActionResult`` có cấu trúc (ID + status + route +
quyền + lỗi). Desktop (chuột/menu/tìm kiếm), CLI và SmartAI đều gọi CÙNG broker
này → cùng một file cho ra cùng ứng dụng/mode theo policy (nghiệm thu SYS-001).

Bất biến trung thực: broker KHÔNG tự thực thi tác động OS. Việc thật do
``ActionHandler`` TIÊM vào (desktop thật/Wine/remote). KHÔNG có handler →
``BLOCKED`` trung thực ("cần desktop/thiết bị"), KHÔNG bao giờ bịa ``SUCCESS``.
Policy (tổ chức) được kiểm TRƯỚC handler; bị chặn → ``DENIED``.
``.exe`` không tự chạy khi mở tệp (SYS-002): OPEN_FILE với đuôi thực thi →
chuyển OPEN_APP có cảnh báo, không chạy ngầm.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from namios_i18n import Lang, t
from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_sys._errors import SysErrorCode
from namios_sys._types import ActionKind, ActionRequest, ActionResult, ActionStatus

__all__ = ["ActionHandler", "PolicyCheck", "ActionBroker", "EXECUTABLE_SUFFIXES"]

#: Đuôi tệp thực thi KHÔNG được tự chạy khi nhấp đúp (SYS-002).
EXECUTABLE_SUFFIXES: frozenset[str] = frozenset({".exe", ".msi", ".bat", ".cmd", ".com", ".scr"})


class ActionHandler(Protocol):
    """Bộ thực thi THẬT một action (desktop/Wine/remote). Trả ``ActionResult``.
    Kết quả là SỰ THẬT từ handler, KHÔNG từ suy đoán của broker/AI."""

    def execute(self, request: ActionRequest, action_id: str) -> ActionResult: ...


#: Policy tổ chức: trả ``True`` nếu CHO PHÉP request (SYS-025/036).
PolicyCheck = Callable[[ActionRequest], bool]


def _is_executable_target(target: str) -> bool:
    # Windows/Wine BỎ QUA dấu chấm/space ở CUỐI tên tệp → 'virus.exe.' và
    # 'setup.bat. ' phân giải về 'virus.exe'/'setup.bat' và vẫn THỰC THI. Phải
    # chuẩn hoá (rstrip '. ') TRƯỚC khi so đuôi, nếu không guard SYS-002 bị lách.
    low = (target or "").strip().lower().rstrip(". ")
    return any(low.endswith(suf) for suf in EXECUTABLE_SUFFIXES)


class ActionBroker:
    """Broker tất định. ``register`` handler theo ``ActionKind``; ``dispatch``
    kiểm policy → chọn handler → trả kết quả thật, hoặc ``BLOCKED`` khi chưa nối."""

    def __init__(self, *, policy: PolicyCheck | None = None) -> None:
        self._handlers: dict[ActionKind, ActionHandler] = {}
        self._policy = policy
        self._counter = 0

    def register(self, kind: ActionKind, handler: ActionHandler) -> None:
        self._handlers[kind] = handler

    def _next_id(self) -> str:
        self._counter += 1
        return f"act-{self._counter}"

    def dispatch(self, request: ActionRequest) -> ActionResult:
        action_id = self._next_id()

        # 0) Action không hợp lệ (không nên xảy ra với enum, nhưng fail-closed).
        if not isinstance(request.action, ActionKind):
            return ActionResult(
                action_id=action_id,
                action=request.action,
                status=ActionStatus.FAILED,
                error_code=SysErrorCode.E_SYS_ACTION_UNKNOWN.value,
                message_vi=t("sys.action.unknown", lang=Lang.VI, action=request.action),
            )

        # 1) SYS-002: mở tệp mà target là file thực thi → KHÔNG chạy ngầm, coi là
        #    mở ứng dụng (có cảnh báo); không để nhấp đúp .exe tự chạy.
        effective = request
        if request.action == ActionKind.OPEN_FILE and _is_executable_target(request.target):
            effective = ActionRequest(
                action=ActionKind.OPEN_APP,
                target=request.target,
                params=request.params,
                mode=request.mode,
                requested_by=request.requested_by,
            )

        # 2) Policy tổ chức kiểm TRƯỚC khi chạm handler (deny-ưu-tiên).
        if self._policy is not None and not self._policy(effective):
            return ActionResult(
                action_id=action_id,
                action=effective.action,
                status=ActionStatus.DENIED,
                permission_ok=False,
                error_code=SysErrorCode.E_SYS_ACTION_DENIED.value,
                message_vi=t("sys.action.denied", lang=Lang.VI, action=effective.action.value),
            )

        # 3) Chưa nối handler thật → BLOCKED trung thực (cần desktop/thiết bị).
        handler = self._handlers.get(effective.action)
        if handler is None:
            return ActionResult(
                action_id=action_id,
                action=effective.action,
                status=ActionStatus.BLOCKED,
                permission_ok=True,
                route_mode=effective.mode,
                error_code=SysErrorCode.E_SYS_NO_HANDLER.value,
                message_vi=t(
                    "sys.action.blocked_no_handler", lang=Lang.VI, action=effective.action.value
                ),
            )

        # 4) Có handler → kết quả THẬT từ handler (giữ nguyên action_id của broker).
        return handler.execute(effective, action_id)
