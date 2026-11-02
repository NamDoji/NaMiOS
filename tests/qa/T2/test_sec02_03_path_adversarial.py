"""T2 (tester độc lập) — adversarial/negative cho SEC-02 (path traversal/
symlink escape) và SEC-03 (TOCTOU race) nhắm vào ``namios_security.safe_path``
(WP8). Viết ĐỘC LẬP với test của dev (``tests/security/security/test_safe_path.py``)
— không trùng case, chủ ý thử các vector dev CHƯA phủ: symlink chain nhiều
tầng, symlink loop, dangling symlink, NUL byte giữa chuỗi, backslash giả
separator, hardlink defense cho mode 'xb'/'ab', và một stress-test TOCTOU
thật bằng thread đổi symlink liên tục trong khi main thread liên tục gọi
``open_within``.

KHÔNG dùng secret/đường dẫn thật — mọi fixture nằm trong ``tmp_path`` của
pytest.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest

from namios_security import PathUnsafeError, open_within, resolve_within


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    base = tmp_path / "base"
    base.mkdir()
    return base


# --- Symlink chain nhiều tầng (dev chỉ test 1 tầng) ----------------------


def test_resolve_within_rejects_multi_hop_symlink_chain_escape(
    base_dir: Path, tmp_path: Path
) -> None:
    """``base/evil`` -> symlink -> ``mid`` (ngoài base) -> symlink -> file
    thật ngoài base. Hai tầng symlink gián tiếp vẫn phải bị chặn ngay ở tầng
    đầu (không theo dõi qua O_NOFOLLOW), không rơi vào vòng lặp vô hạn."""

    real_target = tmp_path / "real-secret.txt"
    real_target.write_text("qa-t2-secret-fake")
    mid_link = tmp_path / "mid-link"
    mid_link.symlink_to(real_target)
    evil = base_dir / "evil"
    evil.symlink_to(mid_link)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "evil")


def test_resolve_within_rejects_multi_hop_intermediate_dir_chain(
    base_dir: Path, tmp_path: Path
) -> None:
    """Thư mục trung gian là symlink trỏ tới MỘT symlink khác trỏ ra ngoài
    (2 hop), không phải 1 hop như test của dev."""

    outside_real = tmp_path / "outside-real-dir"
    outside_real.mkdir()
    (outside_real / "leak.txt").write_text("leak")
    outside_hop = tmp_path / "outside-hop-link"
    outside_hop.symlink_to(outside_real)

    evil_dir = base_dir / "evil-dir"
    evil_dir.symlink_to(outside_hop)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "evil-dir/leak.txt")


# --- Symlink loop (self-referential) -------------------------------------


def test_open_within_symlink_self_loop_does_not_crash_or_hang(base_dir: Path) -> None:
    """Symlink trỏ vào chính nó (``ELOOP``) phải thành ``PathUnsafeError``
    sạch, KHÔNG để OSError/ELOOP thô lọt ra ngoài và KHÔNG treo tiến trình."""

    loop_link = base_dir / "self-loop"
    loop_link.symlink_to(loop_link)

    with pytest.raises(PathUnsafeError):
        open_within(str(base_dir), "self-loop", "rb")


def test_resolve_within_symlink_mutual_loop_two_links(base_dir: Path) -> None:
    """Hai symlink trỏ chéo nhau (A->B, B->A) — cùng lớp lỗi vòng lặp."""

    a = base_dir / "loop-a"
    b = base_dir / "loop-b"
    b.symlink_to(a)
    a.symlink_to(b)

    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "loop-a")


# --- Dangling symlink (target không tồn tại) -----------------------------


def test_open_within_write_rejects_dangling_symlink_leaf(base_dir: Path, tmp_path: Path) -> None:
    """Symlink leaf trỏ tới một target CHƯA tồn tại ngoài base — vẫn phải bị
    chặn bởi lstat-based symlink check (không được coi là "trống, cho ghi
    mới") vì bản chất leaf hiện tại là symlink, không phải file thường."""

    nonexistent_outside = tmp_path / "does-not-exist-yet.txt"
    dangling = base_dir / "dangling"
    dangling.symlink_to(nonexistent_outside)

    with pytest.raises(PathUnsafeError):
        open_within(str(base_dir), "dangling", "wb")

    # Target vẫn KHÔNG được tạo ra do side-effect của lần gọi trên.
    assert not nonexistent_outside.exists()


# --- NUL byte ở thành phần giữa chuỗi (không phải đầu/cuối) --------------


def test_split_candidate_rejects_nul_byte_in_middle_component(base_dir: Path) -> None:
    (base_dir / "sub").mkdir()
    with pytest.raises(PathUnsafeError):
        resolve_within(str(base_dir), "sub/evil\x00name.txt")


# --- Backslash KHÔNG được coi là separator trên Linux --------------------


def test_backslash_in_candidate_is_literal_not_separator(base_dir: Path, tmp_path: Path) -> None:
    """``foo\\..\\secret`` trên Linux KHÔNG tách theo backslash — toàn bộ
    chuỗi là MỘT tên thành phần literal duy nhất (không có dấu '/' nào nên
    ``_split_candidate`` không bẻ nó thành nhiều phần). Vì là thành phần
    LEAF chưa tồn tại (hành vi cho phép — giống case "nonexistent leaf ok
    for future create"), ``resolve_within`` trả về path NẰM TRONG base với
    đúng tên literal đó — KHÔNG được hiểu backslash như dấu phân cấp kiểu
    Windows để thoát ra ngoài base."""

    outside_secret = tmp_path / "secret-backslash-test.txt"
    outside_secret.write_text("x")

    literal_name = "foo\\..\\secret-backslash-test.txt"
    result = resolve_within(str(base_dir), literal_name)

    base_real = os.path.realpath(str(base_dir))
    assert result == os.path.join(base_real, literal_name)
    # Tuyệt đối KHÔNG trùng với file thật ngoài base.
    assert result != str(outside_secret.resolve())
    # Không có thành phần nào tên như vậy từng được TẠO trong base (chỉ
    # resolve, không open/create).
    assert not any(base_dir.iterdir())


# --- Hardlink defense cho mode 'xb' và 'ab' (dev chỉ test 'wb') ----------


def test_open_within_xb_rejects_existing_symlink_leaf(base_dir: Path, tmp_path: Path) -> None:
    outside = tmp_path / "xb-outside.txt"
    outside.write_text("x")
    leaf = base_dir / "xb-target.txt"
    leaf.symlink_to(outside)

    with pytest.raises(PathUnsafeError):
        open_within(str(base_dir), "xb-target.txt", "xb")


def test_open_within_ab_rejects_existing_file_with_extra_hardlink(
    base_dir: Path, tmp_path: Path
) -> None:
    target = base_dir / "ab-shared.txt"
    target.write_text("data")
    other_link = tmp_path / "ab-shared-hardlink.txt"
    os.link(target, other_link)

    with pytest.raises(PathUnsafeError) as exc_info:
        open_within(str(base_dir), "ab-shared.txt", "ab")
    assert "hardlink" in exc_info.value.reason_vi


# --- TOCTOU thật: race-condition stress test (SEC-03) --------------------


def test_open_within_toctou_concurrent_symlink_flip_never_leaks_outside_content(
    base_dir: Path, tmp_path: Path
) -> None:
    """Chạy một thread NỀN liên tục đổi ``base/race`` qua lại giữa "thư mục
    thật trong base" và "symlink ra ngoài", đồng thời thread chính liên tục
    gọi ``open_within`` cho ``race/file.txt`` nhiều lần. Bất kể độ trùng thời
    gian (không cần trúng đúng khoảnh khắc), KHÔNG LẦN NÀO được đọc nội dung
    "OUTSIDE" — mọi lần thành công phải đọc đúng "INSIDE", mọi lần hớt đúng
    vào khoảnh khắc đang là symlink phải ném ``PathUnsafeError`` (không có
    "đọc nhầm" lọt qua)."""

    inside_real = base_dir / "race"
    inside_real.mkdir()
    (inside_real / "file.txt").write_text("INSIDE")

    outside_dir = tmp_path / "race-outside"
    outside_dir.mkdir()
    (outside_dir / "file.txt").write_text("OUTSIDE")

    stop = threading.Event()
    flip_errors: list[BaseException] = []

    def _flipper() -> None:
        toggle = False
        while not stop.is_set():
            try:
                target = base_dir / "race"
                if target.is_symlink() or not target.is_dir():
                    try:
                        target.unlink()
                    except (FileNotFoundError, IsADirectoryError):
                        pass
                if toggle:
                    if target.exists() or target.is_symlink():
                        pass
                    else:
                        target.symlink_to(outside_dir)
                else:
                    if not target.exists() and not target.is_symlink():
                        target.mkdir()
                        (target / "file.txt").write_text("INSIDE")
                toggle = not toggle
            except OSError:
                # Race giữa chính 2 lệnh filesystem của flipper là bình
                # thường (unlink rồi mkdir đụng tiến trình khác) — bỏ qua,
                # không phải điều ta đang kiểm.
                pass
            time.sleep(0.0005)

    flipper = threading.Thread(target=_flipper, daemon=True)
    flipper.start()
    try:
        seen_outside = False
        attempts = 400
        for _ in range(attempts):
            try:
                with open_within(str(base_dir), "race/file.txt", "rb") as f:
                    content = f.read()
            except PathUnsafeError:
                continue
            except OSError:
                # Thành phần bị unlink đúng lúc walk — không phải lỗi an
                # ninh, chỉ là trạng thái "biến mất tạm thời" của flipper.
                continue
            if content == b"OUTSIDE":
                seen_outside = True
                break
        assert not seen_outside, (
            "open_within() đọc được nội dung NGOÀI base qua race symlink-swap "
            "— vi phạm bất biến TOCTOU (SEC-03)."
        )
    finally:
        stop.set()
        flipper.join(timeout=2.0)
