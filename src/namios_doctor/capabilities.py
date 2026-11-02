"""Thu thập capability report host THẬT — không bịa, không secret.

Chỉ đọc: ``platform``/``os.environ``/``/etc/os-release``/``/dev/kvm``/PATH
(qua ``shutil.which`` — chỉ tra đường dẫn, KHÔNG thực thi gì). Không mở
file/path do người dùng cung cấp ⇒ không cần ``resolve_within`` ở đây
(``/etc/os-release`` và ``/dev/kvm`` là path hệ thống cố định, không phải
input động).
"""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

#: Tên công cụ dò bằng PATH (FACT inventory M0 §docs/_m0_inventory_raw.md).
#: Danh sách này phản ánh đúng những gì đặc tả M1/M2/M3 cần kiểm tra sự hiện
#: diện (KHÔNG thực thi, chỉ ``which``). Thêm công cụ mới ở đây khi cần.
TOOLING_PROBE_NAMES: tuple[str, ...] = (
    "git",
    "node",
    "pip",
    "wine",
    "winetricks",
    "qemu-system-x86_64",
    "lb",
    "debootstrap",
    "mmdebstrap",
    "xorriso",
    "fakeroot",
    "mkisofs",
)

#: Đường dẫn thiết bị KVM chuẩn trên Linux (FACT — hằng số hệ thống, không
#: phải input do người dùng cấp).
KVM_DEVICE_PATH = Path("/dev/kvm")

_OS_RELEASE_PATH = Path("/etc/os-release")


def _read_os_release() -> str | None:
    """Đọc ``PRETTY_NAME`` từ ``/etc/os-release`` nếu có; ``None`` nếu không
    đọc được (môi trường không phải Linux chuẩn hoặc file vắng)."""

    try:
        text = _OS_RELEASE_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def _has_kvm_device() -> bool:
    """``True`` nếu ``/dev/kvm`` tồn tại VÀ truy cập được (không phải chỉ
    tồn tại tên file — ``os.access`` kiểm quyền thật)."""

    import os

    return KVM_DEVICE_PATH.exists() and os.access(KVM_DEVICE_PATH, os.R_OK | os.W_OK)


@dataclass(frozen=True)
class HostInfo:
    os_pretty_name: str | None
    kernel_release: str
    architecture: str
    python_version: str


@dataclass(frozen=True)
class SessionInfo:
    session_type: str | None
    desktop_environment: str | None


@dataclass(frozen=True)
class VirtualizationInfo:
    has_kvm: bool
    kvm_device_path: str


@dataclass(frozen=True)
class SystemCapabilitiesReport:
    host: HostInfo
    session: SessionInfo
    virtualization: VirtualizationInfo
    tooling_present: tuple[str, ...]
    tooling_absent: tuple[str, ...]


def collect_capabilities(env: dict[str, str] | None = None) -> SystemCapabilitiesReport:
    """Thu thập capability report THẬT của host hiện tại.

    ``env`` cho phép test tiêm biến môi trường giả (``XDG_SESSION_TYPE``,
    ``XDG_CURRENT_DESKTOP``) mà KHÔNG đổi môi trường tiến trình thật; mặc
    định dùng ``os.environ``.
    """

    import os

    environ = env if env is not None else dict(os.environ)

    host = HostInfo(
        os_pretty_name=_read_os_release(),
        kernel_release=platform.release(),
        architecture=platform.machine(),
        python_version=platform.python_version(),
    )
    session = SessionInfo(
        session_type=environ.get("XDG_SESSION_TYPE"),
        desktop_environment=environ.get("XDG_CURRENT_DESKTOP"),
    )
    virtualization = VirtualizationInfo(
        has_kvm=_has_kvm_device(),
        kvm_device_path=str(KVM_DEVICE_PATH),
    )

    present: list[str] = []
    absent: list[str] = []
    for name in TOOLING_PROBE_NAMES:
        if shutil.which(name) is not None:
            present.append(name)
        else:
            absent.append(name)

    return SystemCapabilitiesReport(
        host=host,
        session=session,
        virtualization=virtualization,
        tooling_present=tuple(present),
        tooling_absent=tuple(absent),
    )
