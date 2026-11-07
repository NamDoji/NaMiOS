"""Gắn LÕI namios_ux vào DỮ LIỆU thiết kế thật (design/*.json) để cổng CI thực
thi bất biến PL12 trên chính registry/manifest sẽ ship — không chỉ trên fixture.

- UX12-019: registry phím tắt thật (``design/keyboard-shortcuts.json``) KHÔNG được
  có xung đột P0-system (nếu có → test đỏ → chặn phát hành). Đây là "detector thật
  (code)" mà $meta của file json còn ghi "CHƯA dựng" — test này dựng nó.
- UX12-026/046: KHÔNG mục hình nền nào trong ``design/wallpaper-manifest.json``
  được coi là đủ điều kiện đóng gói khi chưa có giấy phép thật (mọi mục hiện là
  placeholder) — fail-closed, chống lọt ảnh thiếu quyền vào ISO.
"""

from __future__ import annotations

import json
from pathlib import Path

from namios_ux.shortcuts import PLevel, ShortcutBinding, ShortcutScope, has_blocking_conflict

_REPO = Path(__file__).resolve().parents[3]


def _load_shipped_bindings() -> list[ShortcutBinding]:
    data = json.loads((_REPO / "design" / "keyboard-shortcuts.json").read_text(encoding="utf-8"))
    bindings: list[ShortcutBinding] = []
    for a in data["actions"]:
        if a.get("enabled") is False:
            continue  # vd smartai_invoke còn tắt chờ audit — combo null
        combo = a.get("default_combo")
        if not combo:
            continue
        bindings.append(
            ShortcutBinding(
                action_id=a["action_id"],
                scope=ShortcutScope(a["scope"]),
                combo=combo,
                priority=int(a.get("priority", 0)),
                overridable=bool(a.get("overridable", True)),
                p_level=PLevel(str(a["p_level"]).lower()),
            )
        )
    return bindings


def test_shipped_shortcut_registry_loads_and_is_substantial() -> None:
    bindings = _load_shipped_bindings()
    assert len(bindings) >= 20, "registry phím tắt thật quá ít mục — nghi sai định dạng"


def test_shipped_shortcut_registry_has_no_blocking_conflict() -> None:
    # UX12-019: 2 action hệ thống P0 trùng tổ hợp = chặn phát hành.
    assert not has_blocking_conflict(_load_shipped_bindings())


def test_shipped_wallpapers_none_shippable_without_real_rights() -> None:
    data = json.loads((_REPO / "design" / "wallpaper-manifest.json").read_text(encoding="utf-8"))
    entries = data["wallpapers"]
    assert entries, "manifest hình nền rỗng — nghi sai định dạng"
    for w in entries:
        lic = (w.get("license") or "").strip().lower()
        # Chưa có đợt cấp phép thật nào: mọi mục phải là placeholder/trống.
        assert lic in ("", "placeholder"), (
            f"{w.get('id')!r}: license={lic!r} — nếu là ảnh thật phải có bằng chứng "
            "quyền + người duyệt (UX12-026/048) trước khi đưa vào manifest ship."
        )
