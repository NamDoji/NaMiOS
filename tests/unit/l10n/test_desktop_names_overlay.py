"""Chống LỆCH giữa dữ liệu nguồn (translations/desktop-overlay/vi/*.tsv) và hook
build nhúng (0130-desktop-names-vi.hook.chroot).

Hook nhúng thẳng mapping (để không phụ thuộc thứ tự includes.chroot vs hooks của
live-build); TSV là bản người-đọc + nguồn quyết định. Test này bắt mọi lệch: mục
TSV đang BẬT (không comment) mà hook thiếu → đỏ. Cũng kiểm tính hợp lệ cơ bản:
khoá phải localized `[vi]`, giá trị không rỗng, đích là .desktop/.directory.
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_HOOK = _REPO / "distro/live-build/config/hooks/normal/0130-desktop-names-vi.hook.chroot"
_TSVS = (
    _REPO / "translations/desktop-overlay/vi/applications.tsv",
    _REPO / "translations/desktop-overlay/vi/systemsettings-categories.tsv",
    _REPO / "translations/desktop-overlay/vi/menu-directories.tsv",
)


def _active_entries() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for tsv in _TSVS:
        for line in tsv.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            relpath, key, value = (p.strip() for p in parts)
            out.append((relpath, key, value))
    return out


def test_hook_file_exists() -> None:
    assert _HOOK.is_file(), "thiếu hook 0130-desktop-names-vi.hook.chroot"


def test_every_active_tsv_entry_is_embedded_in_hook() -> None:
    hook = _HOOK.read_text(encoding="utf-8")
    missing = [
        f"{relpath} {key}={value}"
        for relpath, key, value in _active_entries()
        if value not in hook or relpath not in hook
    ]
    assert not missing, "hook lệch TSV, thiếu: " + "; ".join(missing)


def test_active_entries_are_valid() -> None:
    entries = _active_entries()
    assert entries, "không có mục nào đang bật trong TSV — nghi sai định dạng"
    for relpath, key, value in entries:
        assert value, f"giá trị rỗng: {relpath} {key}"
        assert key.endswith("[vi]"), f"khoá không localized tiếng Việt: {key}"
        assert relpath.endswith((".desktop", ".directory")), f"đích lạ: {relpath}"
