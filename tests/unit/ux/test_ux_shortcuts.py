"""UX12-019/021/024 — registry phím tắt: xung đột, tuỳ chỉnh, vượt quyền."""

from __future__ import annotations

from namios_ux._errors import UxErrorCode
from namios_ux.shortcuts import (
    PLevel,
    ShortcutAction,
    ShortcutBinding,
    ShortcutScope,
    detect_conflicts,
    has_blocking_conflict,
    resolve_override,
    shortcut_action_is_safe,
)

SYS = ShortcutScope.SYSTEM
WIN = ShortcutScope.WINDOW
APP = ShortcutScope.APP


def _binding(
    action_id: str,
    scope: ShortcutScope,
    combo: str,
    *,
    priority: int = 0,
    overridable: bool = True,
    p_level: PLevel = PLevel.P1,
) -> ShortcutBinding:
    return ShortcutBinding(
        action_id=action_id,
        scope=scope,
        combo=combo,
        priority=priority,
        overridable=overridable,
        p_level=p_level,
    )


# ---------------------------------------------------------------------------
# detect_conflicts / has_blocking_conflict (UX12-019)
# ---------------------------------------------------------------------------


def test_two_system_p0_same_combo_is_blocking_conflict() -> None:
    # INVARIANT UX12-019: 2 action SYSTEM P0 cùng combo = conflict + CHẶN phát hành.
    bindings = [
        _binding("lock_screen", SYS, "Super+L", p_level=PLevel.P0),
        _binding("open_settings", SYS, "Super+L", p_level=PLevel.P0),
    ]
    conflicts = detect_conflicts(bindings)
    assert len(conflicts) == 1
    assert conflicts[0].code == UxErrorCode.E_UX_SHORTCUT_P0_SYSTEM_CONFLICT.value
    assert has_blocking_conflict(bindings) is True


def test_system_p1_same_combo_conflict_but_not_blocking() -> None:
    bindings = [
        _binding("smartai_open", SYS, "Super+Space", p_level=PLevel.P1),
        _binding("quick_search", SYS, "Super+Space", p_level=PLevel.P1),
    ]
    conflicts = detect_conflicts(bindings)
    assert len(conflicts) == 1
    assert conflicts[0].code == UxErrorCode.E_UX_SHORTCUT_CONFLICT.value
    assert has_blocking_conflict(bindings) is False


def test_system_and_window_scope_same_combo_conflict() -> None:
    # SYSTEM giao với MỌI phạm vi khác (bắt toàn cục).
    bindings = [
        _binding("close_window", WIN, "Alt+F4", p_level=PLevel.P0),
        _binding("force_quit", SYS, "Alt+F4", p_level=PLevel.P0),
    ]
    conflicts = detect_conflicts(bindings)
    assert len(conflicts) == 1
    # Chỉ CẢ HAI đều SYSTEM mới là mã blocking riêng; SYSTEM+WINDOW là conflict thường.
    assert conflicts[0].code == UxErrorCode.E_UX_SHORTCUT_CONFLICT.value


def test_window_and_app_scope_same_combo_do_not_intersect() -> None:
    # Thiết kế: APP chỉ có hiệu lực khi app đó có focus — không giao với WINDOW toàn cục.
    bindings = [
        _binding("switch_window", WIN, "Ctrl+F", p_level=PLevel.P0),
        _binding("wine_app_find", APP, "Ctrl+F", p_level=PLevel.P0),
    ]
    assert detect_conflicts(bindings) == ()
    assert has_blocking_conflict(bindings) is False


def test_different_combo_no_conflict() -> None:
    bindings = [
        _binding("a", SYS, "Super+E", p_level=PLevel.P0),
        _binding("b", SYS, "Super+I", p_level=PLevel.P0),
    ]
    assert detect_conflicts(bindings) == ()


def test_combo_normalization_is_order_and_case_independent() -> None:
    bindings = [
        _binding("task_manager", SYS, "Ctrl+Shift+Esc", p_level=PLevel.P0),
        _binding("duplicate", SYS, "shift+ctrl+ESC", p_level=PLevel.P0),
    ]
    conflicts = detect_conflicts(bindings)
    assert len(conflicts) == 1


def test_same_action_id_does_not_conflict_with_itself() -> None:
    bindings = [
        _binding("file_manager", SYS, "Super+E", p_level=PLevel.P0),
        _binding("file_manager", SYS, "Super+E", p_level=PLevel.P0),
    ]
    assert detect_conflicts(bindings) == ()


def test_clean_registry_has_no_conflicts() -> None:
    bindings = [
        _binding("launcher", SYS, "Super", p_level=PLevel.P0),
        _binding("file_manager", SYS, "Super+E", p_level=PLevel.P0),
        _binding("lock_screen", SYS, "Super+L", p_level=PLevel.P0),
        _binding("settings", WIN, "Super+I", p_level=PLevel.P1),
    ]
    assert detect_conflicts(bindings) == ()
    assert has_blocking_conflict(bindings) is False


# ---------------------------------------------------------------------------
# resolve_override (UX12-021)
# ---------------------------------------------------------------------------


def test_resolve_override_allowed_when_overridable_and_free() -> None:
    bindings = [_binding("settings", WIN, "Super+I", overridable=True)]
    result = resolve_override(bindings, "settings", "Super+K")
    assert result.allowed is True
    assert result.bindings[0].combo == "Super+K"


def test_resolve_override_denied_when_not_overridable() -> None:
    bindings = [_binding("lock_screen", SYS, "Super+L", overridable=False)]
    result = resolve_override(bindings, "lock_screen", "Super+K")
    assert result.allowed is False
    assert result.error_code == UxErrorCode.E_UX_SHORTCUT_NOT_OVERRIDABLE.value
    # Danh sách KHÔNG đổi khi bị từ chối.
    assert result.bindings[0].combo == "Super+L"


def test_resolve_override_denied_for_unknown_action() -> None:
    bindings = [_binding("settings", WIN, "Super+I")]
    result = resolve_override(bindings, "does_not_exist", "Super+K")
    assert result.allowed is False
    assert result.error_code == UxErrorCode.E_UX_SHORTCUT_UNKNOWN_ACTION.value
    assert result.bindings == tuple(bindings)


def test_resolve_override_denied_when_claimed_by_app() -> None:
    bindings = [
        _binding("settings", WIN, "Super+I", overridable=True),
        _binding("wine_app_save", APP, "Super+I", overridable=True),
    ]
    # settings là WINDOW nhưng mục tiêu mới trùng với một binding APP — theo
    # _scopes_intersect, WINDOW không giao APP nên đây PHẢI cho phép (không
    # giả lập xung đột không có thật). Đổi sang test đúng ngữ cảnh "bị app chiếm":
    # hai binding CÙNG phạm vi APP.
    result = resolve_override(bindings, "settings", "Super+I")
    assert result.allowed is True

    bindings_app = [
        _binding("my_app_find", APP, "Ctrl+F", overridable=True),
        _binding("other_app_save", APP, "Ctrl+S", overridable=True),
    ]
    result_app = resolve_override(bindings_app, "my_app_find", "Ctrl+S")
    assert result_app.allowed is False
    assert result_app.error_code == UxErrorCode.E_UX_SHORTCUT_CLAIMED_BY_APP.value
    assert "other_app_save" in result_app.reason_vi


def test_resolve_override_denied_when_combo_taken_by_system() -> None:
    bindings = [
        _binding("launcher", SYS, "Super", overridable=True),
        _binding("file_manager", SYS, "Super+E", overridable=True),
    ]
    result = resolve_override(bindings, "launcher", "Super+E")
    assert result.allowed is False
    assert result.error_code == UxErrorCode.E_UX_SHORTCUT_COMBO_TAKEN.value


# ---------------------------------------------------------------------------
# shortcut_action_is_safe (UX12-024, fail-closed)
# ---------------------------------------------------------------------------


def test_safe_benign_non_privileged_action() -> None:
    action = ShortcutAction(action_id="open_file_manager", command="open_file_manager")
    assert shortcut_action_is_safe(action) is True


def test_empty_command_is_not_safe() -> None:
    action = ShortcutAction(action_id="mystery", command="   ")
    assert shortcut_action_is_safe(action) is False


def test_root_shell_marker_blocks() -> None:
    action = ShortcutAction(action_id="x", command="run_root_shell")
    assert shortcut_action_is_safe(action) is False


def test_send_file_marker_blocks() -> None:
    action = ShortcutAction(action_id="x", command="send_file_to_cloud")
    assert shortcut_action_is_safe(action) is False


def test_disable_protection_marker_blocks() -> None:
    action = ShortcutAction(action_id="x", command="disable_protection_now")
    assert shortcut_action_is_safe(action) is False


def test_sign_submit_marker_blocks() -> None:
    action = ShortcutAction(action_id="x", command="sign_submit_contract")
    assert shortcut_action_is_safe(action) is False


def test_privileged_without_confirmation_blocks() -> None:
    action = ShortcutAction(
        action_id="screenshot", command="capture_screen", privileged=True, confirmed=False
    )
    assert shortcut_action_is_safe(action) is False


def test_privileged_with_confirmation_allows() -> None:
    action = ShortcutAction(
        action_id="screenshot", command="capture_screen", privileged=True, confirmed=True
    )
    assert shortcut_action_is_safe(action) is True
