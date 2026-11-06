"""SYS-001/002 — Action Broker: handler thật mới SUCCESS; .exe không tự chạy."""

from __future__ import annotations

from namios_sys import ActionBroker, ActionKind, ActionRequest, ActionResult, ActionStatus
from namios_sys._errors import SysErrorCode


class _OkHandler:
    """Handler giả trả SUCCESS — chứng minh broker LẤY kết quả từ handler thật."""

    def execute(self, request: ActionRequest, action_id: str) -> ActionResult:
        return ActionResult(
            action_id=action_id,
            action=request.action,
            status=ActionStatus.SUCCESS,
            permission_ok=True,
            message_vi="ok",
        )


def test_no_handler_blocks_honestly() -> None:
    # Chưa nối handler → BLOCKED trung thực, KHÔNG bịa SUCCESS.
    res = ActionBroker().dispatch(ActionRequest(action=ActionKind.PRINT, target="bc.pdf"))
    assert res.status is ActionStatus.BLOCKED
    assert res.error_code == SysErrorCode.E_SYS_NO_HANDLER.value


def test_handler_success_passes_through() -> None:
    b = ActionBroker()
    b.register(ActionKind.PRINT, _OkHandler())
    res = b.dispatch(ActionRequest(action=ActionKind.PRINT, target="bc.pdf"))
    assert res.status is ActionStatus.SUCCESS
    assert res.action_id.startswith("act-")


def test_exe_not_auto_run_on_open_file() -> None:
    # SYS-002: nhấp đúp .exe KHÔNG tự chạy → chuyển sang OPEN_APP (có cảnh báo).
    b = ActionBroker()
    res = b.dispatch(ActionRequest(action=ActionKind.OPEN_FILE, target="/media/usb/setup.exe"))
    assert res.action is ActionKind.OPEN_APP  # không còn là OPEN_FILE chạy ngầm
    assert res.status is ActionStatus.BLOCKED  # chưa có handler → vẫn không chạy


def test_docx_open_file_stays_open_file() -> None:
    res = ActionBroker().dispatch(
        ActionRequest(action=ActionKind.OPEN_FILE, target="hop-dong.docx")
    )
    assert res.action is ActionKind.OPEN_FILE


def test_policy_denies_before_handler() -> None:
    # Policy chặn phải chặn TRƯỚC khi chạm handler (deny-ưu-tiên).
    calls = {"n": 0}

    class _CountHandler:
        def execute(self, request: ActionRequest, action_id: str) -> ActionResult:
            calls["n"] += 1
            return ActionResult(action_id, request.action, ActionStatus.SUCCESS)

    b = ActionBroker(policy=lambda req: False)
    b.register(ActionKind.SHARE, _CountHandler())
    res = b.dispatch(ActionRequest(action=ActionKind.SHARE, target="x"))
    assert res.status is ActionStatus.DENIED
    assert res.error_code == SysErrorCode.E_SYS_ACTION_DENIED.value
    assert calls["n"] == 0  # handler KHÔNG được gọi


def test_action_ids_unique_increment() -> None:
    b = ActionBroker()
    ids = [
        b.dispatch(ActionRequest(action=ActionKind.OPEN_URL, target="x")).action_id
        for _ in range(3)
    ]
    assert ids == ["act-1", "act-2", "act-3"]
