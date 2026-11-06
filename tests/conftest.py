"""Fixtures gốc dùng chung cho toàn bộ test suite M1 (chỉ WP1 sửa file này).

Cung cấp: thư mục XDG tạm (cô lập mỗi test khỏi ``$HOME`` thật của máy chạy
CI/dev) + ngữ cảnh user/host giả để các WP dùng trong test của riêng mình.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import pytest


@pytest.fixture(autouse=True)
def _deterministic_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    """Xoá mọi biến locale/ngôn ngữ TRƯỚC mỗi test → ``resolve_lang()`` mặc định
    tiếng Việt TẤT ĐỊNH, không phụ thuộc locale của máy chạy CI/dev.

    Lý do: ``namios_i18n.resolve_lang`` đọc ``LC_ALL``/``LC_MESSAGES``/``LANG`` của
    hệ thống ("tiếng Anh theo ngôn ngữ máy", VN-001). Runner GitHub có thể đặt
    ``LANG=en_US.UTF-8`` → khiến test gọi ``t()`` không kèm ``lang=`` ra tiếng Anh
    và CI đỏ dù local (LANG rỗng) xanh. Fixture này khử yếu tố đó cho CẢ suite;
    test nào CẦN hành vi locale cụ thể tự ``monkeypatch.setenv`` (chạy SAU fixture)."""

    for var in ("NAMIOS_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)


class XdgDirs(NamedTuple):
    """Các thư mục XDG tạm đã trỏ qua biến môi trường cho một test."""

    config_home: Path
    data_home: Path
    cache_home: Path
    state_home: Path
    home: Path


@pytest.fixture()
def xdg_tmp_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> XdgDirs:
    """Tạo + trỏ ``$XDG_CONFIG_HOME``/``$XDG_DATA_HOME``/``$XDG_CACHE_HOME``/
    ``$XDG_STATE_HOME`` (và ``$HOME`` dự phòng) vào thư mục tạm của pytest,
    để test KHÔNG bao giờ đọc/ghi vào home thật của máy chạy."""

    home = tmp_path / "home"
    config_home = tmp_path / "config"
    data_home = tmp_path / "data"
    cache_home = tmp_path / "cache"
    state_home = tmp_path / "state"
    for d in (home, config_home, data_home, cache_home, state_home):
        d.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))

    return XdgDirs(
        config_home=config_home,
        data_home=data_home,
        cache_home=cache_home,
        state_home=state_home,
        home=home,
    )


class FakeUserHostContext(NamedTuple):
    """Ngữ cảnh user/host giả — dùng cho test planner/txstate cần so khớp
    user/host (ví dụ ``verify_at_apply`` plan stale-reject)."""

    user: str
    host: str


@pytest.fixture()
def fake_user_host() -> FakeUserHostContext:
    return FakeUserHostContext(user="nguoi-dung-test", host="may-test-namios")


@pytest.fixture()
def another_fake_user_host() -> FakeUserHostContext:
    """Một user/host KHÁC — dùng để test reject khi apply bởi người khác."""

    return FakeUserHostContext(user="nguoi-dung-khac", host="may-khac")
