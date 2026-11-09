"""Fixtures dùng chung cho bộ test độ tin cậy (reliability-tests) — roadmap A4.

Bộ test này KIỂM THỬ hàng hoá có thật trong repo (error-catalog.json,
docs/support/error-codes.md, docs/specs/EVENT-ERROR-CONTRACT.md,
namios-chan-doan, namios-smartai, namios-smartai-policy.sh) bằng SỰ KIỆN
MÔ PHỎNG (fixture) — KHÔNG có phần cứng Wi-Fi/máy in/Bluetooth thật nào được
đụng tới. Mọi lệnh hệ thống (`nmcli`, `systemctl`, `pkexec`, `lpstat`,
`bluetoothctl`, ...) được THAY bằng script giả (fake bin) đặt lên đầu PATH —
xem fixture `fake_bin` dưới đây. Đây là quy ước SỐNG CÒN để test không bao giờ
chạm máy thật và chạy được trong sandbox không có các gói đó.

Không tái hiện logic của namios-chan-doan/namios-smartai ở đây — chỉ gọi
THẬT các binary đó qua subprocess (`run_cli`) rồi so khớp đầu ra, hoặc `source`
thật namios-smartai-policy.sh trong smartai_tests.sh (bash, không phải file
này) để gọi trực tiếp các hàm thật.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pytest

# ---------------------------------------------------------------------------
# Đường dẫn tới các tệp nguồn sự thật — PHẢI khớp với những gì
# docs/specs/EVENT-ERROR-CONTRACT.md §"Tệp nguồn sự thật đi kèm" khai báo.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]

INCLUDES_BIN = (
    REPO_ROOT
    / "distro"
    / "live-build"
    / "config"
    / "includes.chroot"
    / "usr"
    / "local"
    / "bin"
)

CATALOG_PATH = (
    REPO_ROOT
    / "distro"
    / "live-build"
    / "config"
    / "includes.chroot"
    / "usr"
    / "share"
    / "namios"
    / "error-catalog.json"
)
ERROR_CODES_MD = REPO_ROOT / "docs" / "support" / "error-codes.md"
CONTRACT_MD = REPO_ROOT / "docs" / "specs" / "EVENT-ERROR-CONTRACT.md"
CHAN_DOAN_BIN = INCLUDES_BIN / "namios-chan-doan"
SMARTAI_BIN = INCLUDES_BIN / "namios-smartai"
POLICY_LIB = INCLUDES_BIN / "namios-smartai-policy.sh"
NAMIOS_SECURITY_SRC = REPO_ROOT / "src"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def catalog_path() -> Path:
    assert CATALOG_PATH.is_file(), f"Không thấy catalog tại {CATALOG_PATH}"
    return CATALOG_PATH


@pytest.fixture(scope="session")
def catalog_data() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def error_codes_md_text() -> str:
    return ERROR_CODES_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def contract_md_text() -> str:
    return CONTRACT_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def chan_doan_bin() -> Path:
    assert CHAN_DOAN_BIN.is_file(), f"Không thấy {CHAN_DOAN_BIN}"
    return CHAN_DOAN_BIN


@pytest.fixture(scope="session")
def smartai_bin() -> Path:
    assert SMARTAI_BIN.is_file(), f"Không thấy {SMARTAI_BIN}"
    return SMARTAI_BIN


@pytest.fixture(scope="session")
def policy_lib() -> Path:
    assert POLICY_LIB.is_file(), f"Không thấy {POLICY_LIB}"
    return POLICY_LIB


# ---------------------------------------------------------------------------
# FakeBin — dựng một thư mục PATH giả chứa các "lệnh nền" mô phỏng
# (nmcli/systemctl/pkexec/lpstat/bluetoothctl/...). KHÔNG đụng lệnh thật của
# máy host; coreutils cơ bản (date/cat/sed/awk/grep/tr/mktemp/printf...) vẫn
# lấy từ /usr/bin:/bin thật vì FakeBin chỉ chặn (shadow) đúng tên lệnh được
# `add()` tường minh.
# ---------------------------------------------------------------------------


@dataclass
class FakeBin:
    bin_dir: Path
    log_file: Path = field(init=False)

    def __post_init__(self) -> None:
        self.log_file = self.bin_dir / "_calls.log"

    def add(self, name: str, body: str, *, log_calls: bool = True) -> Path:
        """Tạo lệnh giả `name` với nội dung bash `body`. Nếu log_calls, mỗi
        lần gọi ghi một dòng "argv" vào _calls.log (để test kiểm tra lệnh có
        thực sự được gọi hay không — vd kiểm 'không bypass' khi người dùng từ
        chối)."""
        script = self.bin_dir / name
        log_line = ""
        if log_calls:
            # argv ghép bằng dấu cách đơn giản (đủ dùng cho test — không cần
            # xử lý escaping phức tạp, lệnh giả không nhận input có khoảng
            # trắng lạ trong test này).
            log_line = f'printf \'%s %s %s\\n\' "$(date -u +%s)" "{name}" "$*" >> "{self.log_file}"\n'
        script.write_text("#!/bin/bash\n" + log_line + body + "\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return script

    def missing(self, name: str) -> None:
        """Đánh dấu tường minh một lệnh KHÔNG có trên máy (không tạo gì) —
        dùng để test đường "thiếu công cụ -> báo rõ, không suy diễn OK"."""
        p = self.bin_dir / name
        if p.exists():
            p.unlink()

    def calls(self) -> list[str]:
        if not self.log_file.exists():
            return []
        return self.log_file.read_text(encoding="utf-8").splitlines()

    def called(self, name: str) -> bool:
        return any(f" {name} " in (line + " ") for line in self.calls())

    def path_env(self, extra_dirs: str = "/usr/bin:/bin:/usr/sbin:/sbin") -> str:
        return f"{self.bin_dir}:{extra_dirs}"


@pytest.fixture()
def fake_bin(tmp_path: Path) -> FakeBin:
    d = tmp_path / "fakebin"
    d.mkdir(parents=True, exist_ok=True)
    return FakeBin(d)


@pytest.fixture()
def xdg_state_dir(tmp_path: Path) -> Path:
    d = tmp_path / "xdg-state"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture()
def run_cli() -> Callable[..., subprocess.CompletedProcess]:
    """Chạy MỘT công cụ shell thật (namios-chan-doan/namios-smartai) qua
    subprocess, với PATH/HOME/XDG đã cô lập + stdin mô phỏng. Trả
    subprocess.CompletedProcess (stdout/stderr đã decode, có timeout để một
    test treo không treo cả suite)."""

    def _run(
        cmd: list[str],
        *,
        path_env: str,
        stdin_text: str = "",
        extra_env: dict | None = None,
        home: Path | None = None,
        timeout: float = 10.0,
    ) -> subprocess.CompletedProcess:
        env = {
            "PATH": path_env,
            "LC_ALL": "C",
            "LANG": "C",
            # Luôn ép TTY-fallback (không kdialog) để test chạy headless.
        }
        if home is not None:
            env["HOME"] = str(home)
            env["XDG_STATE_HOME"] = str(home / ".local" / "state")
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            cmd,
            input=stdin_text,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout,
        )

    return _run


@pytest.fixture(scope="session")
def namios_security_redact_text() -> Callable[[str], str]:
    """Nạp `namios_security.redact_text` THẬT (từ src/, không mô phỏng) để
    test lớp 'localization + redaction' cốt lõi — đây là module các tool
    bash gọi qua PYTHONPATH=/opt/namios lúc chạy trên ISO thật."""
    sys.path.insert(0, str(NAMIOS_SECURITY_SRC))
    from namios_security import redact_text  # type: ignore

    return redact_text
