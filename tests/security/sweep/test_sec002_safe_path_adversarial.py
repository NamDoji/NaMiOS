"""SEC-002 adversarial — ``namios_security.safe_path`` (resolve_within/
open_within). Mục tiêu: xác nhận PHÒNG THỦ GIỮ trước traversal/symlink
(trung gian + leaf)/absolute-escape/hardlink/NUL-byte/race TOCTOU mô phỏng.

Độc lập với ``tests/security/security/test_safe_path.py`` (dev) — tự dựng
case riêng, không import fixture của dev."""

from __future__ import annotations

import os

import pytest

from namios_security import PathUnsafeError, open_within, resolve_within

# ---------------------------------------------------------------------------
# Traversal / absolute escape
# ---------------------------------------------------------------------------


def test_resolve_within_rejects_dotdot_traversal(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("ngoai pham vi")

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "../secret.txt")


def test_resolve_within_rejects_deeply_nested_dotdot_traversal(tmp_path) -> None:
    base = tmp_path / "a" / "b" / "c"
    base.mkdir(parents=True)
    (tmp_path / "ssh_keys_pretend").mkdir()

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "../../../ssh_keys_pretend")


def test_resolve_within_rejects_absolute_candidate_even_if_inside_base(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    (base / "inner.txt").write_text("x")

    # Candidate tuyệt đối TRỎ VÀO base vẫn phải bị chặn — API chỉ nhận
    # candidate tương đối (FACT: "candidate phải là đường dẫn tương đối").
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), str(base / "inner.txt"))


def test_resolve_within_rejects_dotdot_disguised_with_extra_slashes(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    (tmp_path / "victim.txt").write_text("x")

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "sub/../../victim.txt")


def test_resolve_within_rejects_nul_byte_in_candidate(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "evil\x00.txt")


def test_resolve_within_rejects_empty_candidate(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "")


def test_resolve_within_rejects_candidate_collapsing_to_base_itself(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), ".")


# ---------------------------------------------------------------------------
# Symlink — trung gian + leaf
# ---------------------------------------------------------------------------


def test_resolve_within_rejects_leaf_symlink_pointing_outside(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret ngoai staging")
    link = base / "innocuous.txt"
    os.symlink(outside, link)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "innocuous.txt")


def test_resolve_within_rejects_intermediate_symlink_directory_pointing_outside(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    (outside_dir / "payload.txt").write_text("du lieu nhay cam")

    evil_link = base / "sub"
    os.symlink(outside_dir, evil_link)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "sub/payload.txt")


def test_open_within_rejects_leaf_symlink_even_for_write(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    outside = tmp_path / "outside_target.txt"
    outside.write_text("goc")
    link = base / "launcher.cfg"
    os.symlink(outside, link)

    with pytest.raises(PathUnsafeError):
        open_within(str(base), "launcher.cfg", "wb")

    # Xác nhận KHÔNG ghi đè được nội dung file ngoài qua symlink.
    assert outside.read_text() == "goc"


def test_open_within_rejects_symlink_loop_without_hanging(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    loop = base / "loop"
    os.symlink(loop, loop)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "loop")


# ---------------------------------------------------------------------------
# Hardlink attack (ghi đè file có nhiều hardlink)
# ---------------------------------------------------------------------------


def test_open_within_rejects_write_to_existing_file_with_extra_hardlink(tmp_path) -> None:
    base = tmp_path / "staging"
    base.mkdir()
    target = base / "state.sqlite3"
    target.write_text("du lieu that")
    # Hardlink thứ hai ở NGOÀI base — nếu "wb" được phép ghi đè, nội dung
    # bên ngoài cũng đổi theo (tấn công hardlink cổ điển).
    outside_alias = tmp_path / "alias_outside"
    os.link(target, outside_alias)

    with pytest.raises(PathUnsafeError):
        open_within(str(base), "state.sqlite3", "wb")

    assert outside_alias.read_text() == "du lieu that"


def test_open_within_allows_write_to_fresh_file_without_hardlink(tmp_path) -> None:
    """Đối chứng (control case): file MỚI (không hardlink) vẫn ghi được —
    xác nhận guard hardlink không chặn quá tay thao tác hợp lệ bình thường."""

    base = tmp_path / "staging"
    base.mkdir()
    with open_within(str(base), "fresh.txt", "wb") as fh:
        fh.write(b"ok")
    assert (base / "fresh.txt").read_bytes() == b"ok"


# ---------------------------------------------------------------------------
# TOCTOU mô phỏng: race GIỮA lúc validate thành phần cuối và lúc mở thật.
# resolve_within/open_within là FD-based (dir_fd + O_NOFOLLOW mỗi bước) nên
# PHẢI chặn được — khác với so sánh realpath đơn giản.
# ---------------------------------------------------------------------------


def test_open_within_toctou_leaf_swapped_to_symlink_right_before_final_open(
    tmp_path, monkeypatch
) -> None:
    """Mô phỏng kẻ tấn công thắng race: ngay TRƯỚC lệnh ``os.open`` cuối
    cùng (thành phần leaf, đã đi qua walk FD-based), đổi file thường thành
    symlink trỏ ra ngoài. Vì bước mở cuối dùng ``O_NOFOLLOW`` trên FD cha đã
    pin, kỳ vọng: việc swap bị phát hiện/ chặn (ELOOP) — không đọc/ghi được
    xuyên symlink mới."""

    base = tmp_path / "staging"
    base.mkdir()
    victim = base / "report.txt"
    victim.write_text("an toan")
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("BI MAT KHONG DUOC LO")

    import os as os_module

    real_open = os_module.open
    swapped = {"done": False}

    def evil_open(path, flags, *a, **kw):
        # Chỉ can thiệp vào lệnh open() có dir_fd trỏ đúng base's fd cho
        # "report.txt" — swap NGAY TRƯỚC KHI gọi open() thật, mô phỏng
        # attacker thắng race đúng thời điểm nhạy nhất.
        if path == "report.txt" and not swapped["done"] and "dir_fd" in kw:
            swapped["done"] = True
            os_module.remove(victim)
            os_module.symlink(outside, victim)
        return real_open(path, flags, *a, **kw)

    monkeypatch.setattr(os_module, "open", evil_open)

    with pytest.raises(PathUnsafeError):
        open_within(str(base), "report.txt", "rb")


def test_resolve_within_toctou_intermediate_dir_swapped_mid_walk(tmp_path, monkeypatch) -> None:
    """Mô phỏng race ở một thành phần TRUNG GIAN: ngay trước khi
    ``_walk_to_parent_fd`` mở thành phần trung gian kế tiếp bằng
    ``dir_fd=current_fd`` (đã pin từ base), kẻ tấn công đổi thành phần đó
    (vẫn còn là tên cũ dưới base) thành symlink trỏ ra ngoài. Vì bước mở
    dùng ``O_NOFOLLOW`` + so khớp ``st_dev`` ngay sau mỗi bước, kỳ vọng:
    walk thất bại rõ ràng, không âm thầm đi theo symlink mới."""

    base = tmp_path / "staging"
    sub = base / "profiles"
    sub.mkdir(parents=True)
    (sub / "cfg.json").write_text("an toan")

    outside_dir = tmp_path / "outside_profiles"
    outside_dir.mkdir()
    (outside_dir / "cfg.json").write_text("BI MAT")

    import os as os_module

    real_open = os_module.open
    swapped = {"done": False}

    def evil_open(path, flags, *a, **kw):
        if path == "profiles" and not swapped["done"] and "dir_fd" in kw:
            swapped["done"] = True
            os_module.rmdir(sub) if not any(sub.iterdir()) else None
        return real_open(path, flags, *a, **kw)

    # Thay thư mục "profiles" dưới base bằng symlink NGAY TRƯỚC bước mở —
    # dùng rename nguyên tử (os.rename không có target cùng tên nên dùng
    # remove+symlink tương tự test trên, nhưng cho thư mục cần dọn file con
    # trước để rmdir không lỗi).
    for f in list(sub.iterdir()):
        f.unlink()

    monkeypatch.setattr(os_module, "open", evil_open)

    def evil_open2(path, flags, *a, **kw):
        if path == "profiles" and not swapped["done"] and "dir_fd" in kw:
            swapped["done"] = True
            os_module.rmdir(sub)
            os_module.symlink(outside_dir, sub)
        return real_open(path, flags, *a, **kw)

    monkeypatch.setattr(os_module, "open", evil_open2)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base), "profiles/cfg.json")
