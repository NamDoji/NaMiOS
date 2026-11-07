"""Registry phím tắt (Phụ lục 12, §3.5 — UX12-019/020/021/024).

Mục tiêu honest-core: giữ thói quen Windows, phát hiện xung đột phím tắt TRƯỚC
khi phát hành, không để hai hành động hệ thống cùng tổ hợp (CI gate), cho phép
người dùng tùy biến có kiểm soát (UX12-021), và chặn fail-closed phím tắt nào
đó gán cho một hành động VƯỢT QUYỀN (UX12-024).

UX12-024 tái dùng kiểu "forbidden tool marker" của ``namios_e08.actuator``
(E08-030): hợp nhất ``FORBIDDEN_TOOL_MARKERS`` của E08 với vài dấu hiệu riêng
của phím tắt desktop (gửi tệp / tắt bảo vệ màn hình khóa) mà E08 (vận hành
driver/.NET) không có lý do liệt kê.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import Enum

from namios_e08.actuator import FORBIDDEN_TOOL_MARKERS as _E08_FORBIDDEN_TOOL_MARKERS
from namios_i18n import Lang, t
from namios_ux import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import)
from namios_ux._errors import UxErrorCode
from namios_ux._text import contains_forbidden_marker, is_blank, normalize_text

__all__ = [
    "ShortcutScope",
    "PLevel",
    "ShortcutBinding",
    "ShortcutAction",
    "ShortcutConflict",
    "OverrideResult",
    "SHORTCUT_FORBIDDEN_MARKERS",
    "detect_conflicts",
    "has_blocking_conflict",
    "resolve_override",
    "shortcut_action_is_safe",
]


class ShortcutScope(str, Enum):
    """Phạm vi hiệu lực một phím tắt (UX12-019 bảng registry §3.5)."""

    SYSTEM = "system"
    WINDOW = "window"
    APP = "app"


class PLevel(str, Enum):
    """Mức ưu tiên nghiệm thu (UX12 bảng §3.5/§3.3: P0 chặn phát hành, P1 không)."""

    P0 = "p0"
    P1 = "p1"


@dataclass(frozen=True)
class ShortcutBinding:
    """Một dòng trong registry phím tắt (UX12-019).

    ``combo`` là chuỗi tổ hợp hiển thị (vd ``"Super+E"``, ``"Ctrl+Shift+Esc"``);
    so khớp trùng combo dùng dạng chuẩn hoá (xem ``_normalize_combo``) — không
    phân biệt hoa/thường hay thứ tự modifier. ``priority`` cao hơn thắng khi
    hiển thị nhưng KHÔNG tự xoá xung đột — xung đột vẫn phải báo (UX12-019:
    "CI phát hiện... không phát hành nếu P0 conflict", không phải "ai cao hơn
    thắng thì thôi")."""

    action_id: str
    scope: ShortcutScope
    combo: str
    priority: int = 0
    overridable: bool = True
    p_level: PLevel = PLevel.P1


@dataclass(frozen=True)
class ShortcutAction:
    """Hành động THẬT đứng sau một phím tắt (UX12-024) — tách khỏi
    ``ShortcutBinding`` vì đăng ký phím (action_id/scope/combo) khác với mô tả
    "bấm phím này thì máy làm gì". ``privileged`` = hành động có tác động an
    toàn/hệ thống (vd khóa máy, chụp màn hình, tắt bảo vệ) cần xác nhận rõ
    ràng trước khi coi là an toàn để bấm một phím là xong (UX12-024: "tác vụ
    nguy hiểm vẫn cần xác nhận và audit")."""

    action_id: str
    command: str = ""
    privileged: bool = False
    confirmed: bool = False


@dataclass(frozen=True)
class ShortcutConflict:
    """Một cặp binding XUNG ĐỘT (UX12-019): cùng combo (chuẩn hoá) + phạm vi
    giao nhau. ``code`` là ``UxErrorCode`` dạng chuỗi — dùng
    ``E_UX_SHORTCUT_P0_SYSTEM_CONFLICT`` riêng cho cặp SYSTEM+P0 để CI phân
    biệt được mức phải CHẶN phát hành khỏi xung đột thường."""

    first: ShortcutBinding
    second: ShortcutBinding
    combo: str
    code: str
    reason_vi: str


@dataclass(frozen=True)
class OverrideResult:
    """Kết quả một yêu cầu đổi phím tắt (UX12-021). ``bindings`` là danh sách
    SAU khi đổi khi ``allowed`` — khi bị từ chối, ``bindings`` trả nguyên danh
    sách gốc KHÔNG đổi (không âm thầm nửa-đổi)."""

    allowed: bool
    reason_vi: str
    error_code: str | None
    bindings: tuple[ShortcutBinding, ...]


#: Dấu hiệu thêm NGOÀI ``FORBIDDEN_TOOL_MARKERS`` (E08-030) mà UX12-024 nêu rõ
#: cho ngữ cảnh "bấm một phím" (gửi tệp / tắt lớp bảo vệ màn hình khóa) — E08
#: xoay quanh vận hành driver/.NET nên không có lý do liệt kê các dấu hiệu này.
_EXTRA_FORBIDDEN_MARKERS: frozenset[str] = frozenset(
    {
        "send_file",
        "upload_file",
        "exfiltrate",
        "disable_protection",
        "bypass_protection",
        "disable_lock_screen",
        "disable_lock",
    }
)

#: Hợp nhất — TÁI DÙNG (không fork) tập markers của ``namios_e08.actuator``.
SHORTCUT_FORBIDDEN_MARKERS: frozenset[str] = _E08_FORBIDDEN_TOOL_MARKERS | _EXTRA_FORBIDDEN_MARKERS


#: Bí danh phím/modifier đồng nghĩa → tên CHUẨN (so khớp sau ``normalize_text``
#: + bỏ khoảng trắng trong tên). ``Super``/``Meta``/``Win`` là CÙNG một phím
#: vật lý (logo); ``Control``/``Ctrl``, ``Escape``/``Esc``, ``Option``/``Alt``
#: v.v. cũng vậy — nếu không gộp, hai action SYSTEM P0 gán ``"Super+L"`` và
#: ``"Meta+L"`` sẽ LỌT qua detect_conflicts dù chiếm đúng một phím (UX12-019).
_COMBO_ALIASES: dict[str, str] = {
    "control": "ctrl",
    "ctrl": "ctrl",
    "ctl": "ctrl",
    "option": "alt",
    "opt": "alt",
    "alt": "alt",
    "altgr": "altgr",
    "shift": "shift",
    "super": "super",
    "meta": "super",
    "win": "super",
    "windows": "super",
    "cmd": "super",
    "command": "super",
    "logo": "super",
    "mod4": "super",
    "escape": "esc",
    "esc": "esc",
    "return": "enter",
    "enter": "enter",
    "delete": "del",
    "del": "del",
    "insert": "ins",
    "ins": "ins",
    "pageup": "pageup",
    "pgup": "pageup",
    "pagedown": "pagedown",
    "pgdn": "pagedown",
    "pgdown": "pagedown",
    "space": "space",
    "spacebar": "space",
    "printscreen": "printscreen",
    "prtsc": "printscreen",
    "prtscn": "printscreen",
    "prtscr": "printscreen",
    "prtscrn": "printscreen",
    "sysrq": "printscreen",
}

_INNER_WS = re.compile(r"\s+")


def _normalize_key_token(token: str) -> str:
    """Chuẩn hoá MỘT phần của tổ hợp (một modifier hoặc phím): fail-closed qua
    ``normalize_text`` (casefold/NFKC/bỏ ký tự vô hình) + bỏ khoảng trắng bên
    trong (``"page up"`` → ``"pageup"``), rồi quy về tên chuẩn theo
    ``_COMBO_ALIASES`` (giữ nguyên nếu không có bí danh)."""

    base = _INNER_WS.sub("", normalize_text(token))
    return _COMBO_ALIASES.get(base, base)


def _normalize_combo(combo: str) -> str:
    """Chuẩn hoá tổ hợp phím để SO KHỚP trùng lặp: chuẩn hoá từng phần (casefold
    + Unicode + bỏ ký tự vô hình + gộp modifier đồng nghĩa), bỏ phần rỗng rồi
    SẮP XẾP theo thứ tự chữ cái. Sắp xếp làm mất thứ tự hiển thị gốc (không dùng
    kết quả này để HIỂN THỊ) nhưng cho phép coi ``"Ctrl+Shift+Esc"``,
    ``"Shift+Control+Escape"`` và ``"shift + ctrl + esc"`` là MỘT tổ hợp khi xét
    trùng — đúng tinh thần UX12-019 (xung đột không phụ thuộc thứ tự/cách gõ
    modifier người thiết kế nhập vào registry)."""

    parts = [tok for p in combo.split("+") if (tok := _normalize_key_token(p))]
    return "+".join(sorted(parts))


def _scopes_intersect(a: ShortcutScope, b: ShortcutScope) -> bool:
    """Hai phạm vi có "giao nhau" theo nghĩa UX12-019 không.

    - ``SYSTEM`` là bắt toàn cục (global capture): giao với MỌI phạm vi khác
      và với chính nó — bắt buộc cho bất biến UX12-019 (2 action SYSTEM P0
      cùng combo = conflict).
    - ``WINDOW`` (trình quản lý cửa sổ/shell) giao với ``SYSTEM`` và chính nó
      — đây cũng là tầng toàn cục theo cửa sổ đang focus.
    - ``APP`` giao với ``SYSTEM`` (hệ thống luôn thắng) và với chính nó —
      hợp đồng này KHÔNG có trường định danh ứng dụng riêng biệt, nên fail-
      closed: hai binding cùng phạm vi APP + cùng combo được coi là CÙNG một
      ngữ cảnh (không ngầm định "chắc là app khác nhau nên an toàn").
    - ``WINDOW`` và ``APP`` KHÔNG mặc định giao nhau: shortcut của một ứng
      dụng cụ thể chỉ có hiệu lực khi ứng dụng đó đang có focus, tách biệt
      khỏi tầng window-manager toàn cục."""

    if a is ShortcutScope.SYSTEM or b is ShortcutScope.SYSTEM:
        return True
    return a is b


def detect_conflicts(bindings: Sequence[ShortcutBinding]) -> tuple[ShortcutConflict, ...]:
    """Mọi cặp binding cùng combo (chuẩn hoá) + phạm vi giao nhau (UX12-019).

    So khớp từng cặp KHÔNG trùng ``action_id`` (một action giữ nguyên định
    nghĩa của chính nó không tự xung đột với mình). Trả tuple RỖNG = registry
    sạch."""

    items = list(bindings)
    conflicts: list[ShortcutConflict] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            first, second = items[i], items[j]
            if first.action_id == second.action_id:
                continue
            if _normalize_combo(first.combo) != _normalize_combo(second.combo):
                continue
            if not _scopes_intersect(first.scope, second.scope):
                continue

            is_blocking = (
                first.scope is ShortcutScope.SYSTEM
                and second.scope is ShortcutScope.SYSTEM
                and first.p_level is PLevel.P0
                and second.p_level is PLevel.P0
            )
            if is_blocking:
                code = UxErrorCode.E_UX_SHORTCUT_P0_SYSTEM_CONFLICT.value
                reason_vi = t(
                    "ux.shortcut.p0_system_conflict",
                    lang=Lang.VI,
                    a=first.action_id,
                    b=second.action_id,
                    combo=first.combo,
                )
            else:
                code = UxErrorCode.E_UX_SHORTCUT_CONFLICT.value
                reason_vi = t(
                    "ux.shortcut.conflict",
                    lang=Lang.VI,
                    a=first.action_id,
                    b=second.action_id,
                    combo=first.combo,
                )
            conflicts.append(
                ShortcutConflict(
                    first=first,
                    second=second,
                    combo=first.combo,
                    code=code,
                    reason_vi=reason_vi,
                )
            )
    return tuple(conflicts)


def has_blocking_conflict(bindings: Sequence[ShortcutBinding]) -> bool:
    """CI gate UX12-019: ``True`` nếu có ÍT NHẤT một xung đột SYSTEM+P0 —
    "không phát hành nếu P0 conflict"."""

    return any(
        c.code == UxErrorCode.E_UX_SHORTCUT_P0_SYSTEM_CONFLICT.value
        for c in detect_conflicts(bindings)
    )


def resolve_override(
    bindings: Sequence[ShortcutBinding], action_id: str, new_combo: str
) -> OverrideResult:
    """Yêu cầu đổi tổ hợp phím của ``action_id`` sang ``new_combo`` (UX12-021).

    Fail-closed theo đúng thứ tự:
    1. ``action_id`` không có trong registry → từ chối, danh sách không đổi.
    2. Binding đó ``overridable=False`` → từ chối rõ ràng.
    3. ``new_combo`` đã bị MỘT binding khác (phạm vi giao nhau) chiếm → từ
       chối, nêu rõ nếu đó là một app đang chiếm (UX12-021: "phím được ứng
       dụng chiếm" phải báo riêng khỏi xung đột chung).
    4. Còn lại → cho phép, trả danh sách binding đã cập nhật."""

    original = tuple(bindings)
    target = next((b for b in original if b.action_id == action_id), None)
    if target is None:
        return OverrideResult(
            allowed=False,
            reason_vi=t("ux.shortcut.unknown_action", lang=Lang.VI, action=action_id),
            error_code=UxErrorCode.E_UX_SHORTCUT_UNKNOWN_ACTION.value,
            bindings=original,
        )

    if not target.overridable:
        return OverrideResult(
            allowed=False,
            reason_vi=t("ux.shortcut.not_overridable", lang=Lang.VI, action=action_id),
            error_code=UxErrorCode.E_UX_SHORTCUT_NOT_OVERRIDABLE.value,
            bindings=original,
        )

    normalized_new = _normalize_combo(new_combo)
    if not normalized_new:
        # Tổ hợp rỗng/chỉ dấu phân tách ("+", "   ", ký tự vô hình) KHÔNG phải
        # tổ hợp hợp lệ — fail-closed, không âm thầm gỡ phím hay né phát hiện
        # trùng bằng một combo "trống".
        return OverrideResult(
            allowed=False,
            reason_vi=t(
                "ux.shortcut.invalid_combo", lang=Lang.VI, combo=new_combo, action=action_id
            ),
            error_code=UxErrorCode.E_UX_SHORTCUT_INVALID_COMBO.value,
            bindings=original,
        )
    for other in original:
        if other.action_id == action_id:
            continue
        if _normalize_combo(other.combo) != normalized_new:
            continue
        if not _scopes_intersect(target.scope, other.scope):
            continue
        if other.scope is ShortcutScope.APP:
            return OverrideResult(
                allowed=False,
                reason_vi=t(
                    "ux.shortcut.claimed_by_app",
                    lang=Lang.VI,
                    combo=new_combo,
                    owner=other.action_id,
                    action=action_id,
                ),
                error_code=UxErrorCode.E_UX_SHORTCUT_CLAIMED_BY_APP.value,
                bindings=original,
            )
        return OverrideResult(
            allowed=False,
            reason_vi=t(
                "ux.shortcut.combo_taken",
                lang=Lang.VI,
                combo=new_combo,
                owner=other.action_id,
                action=action_id,
            ),
            error_code=UxErrorCode.E_UX_SHORTCUT_COMBO_TAKEN.value,
            bindings=original,
        )

    updated = tuple(
        replace(b, combo=new_combo) if b.action_id == action_id else b for b in original
    )
    return OverrideResult(
        allowed=True,
        reason_vi=t("ux.shortcut.override_ok", lang=Lang.VI, action=action_id, combo=new_combo),
        error_code=None,
        bindings=updated,
    )


def shortcut_action_is_safe(action: ShortcutAction) -> bool:
    """UX12-024, fail-closed: phím tắt không được tự chạy lệnh vượt quyền.

    - ``command`` rỗng — gồm cả chỉ-khoảng-trắng hay chỉ ký-tự-vô-hình
      (zero-width) → KHÔNG an toàn (không rõ làm gì thì không coi là an toàn).
    - ``command`` chứa dấu hiệu bị cấm (root/shell/exec/tải-binary/gửi-tệp/
      bỏ-bảo-vệ/ký-nộp, xem ``SHORTCUT_FORBIDDEN_MARKERS``) → KHÔNG.
    - ``privileged=True`` (tác động an toàn/hệ thống) mà chưa ``confirmed`` →
      KHÔNG (UX12-024: "tác vụ nguy hiểm vẫn cần xác nhận và audit").
    - Còn lại → an toàn."""

    if is_blank(action.command):
        return False
    # So khớp marker qua chuẩn hoá fail-closed (``_text.compact``): chặn mọi
    # biến thể hoa/thường (kể cả ``ſ``→``s``), ký tự vô hình (zero-width),
    # fullwidth, và dấu phân tách thay thế ("send file"/"send-file" cho
    # "send_file") — vá lỗ hổng substring .lower() thô của E08.
    if contains_forbidden_marker(action.command, SHORTCUT_FORBIDDEN_MARKERS):
        return False
    if action.privileged and not action.confirmed:
        return False
    return True
