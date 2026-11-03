"""Enum compatibility status + tuple chứng nhận (§11.2) + AppMode (WIN-003).

Xem M1-INTERFACES.md §1b, §5.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CompatStatus(str, Enum):
    """Trạng thái tương thích của một tuple chứng nhận (§11.2)."""

    UNTESTED = "untested"
    EXPERIMENTAL = "experimental"
    TASK_VERIFIED = "task_verified"
    BLOCKED = "blocked"
    REVOKED = "revoked"


class AppMode(str, Enum):
    """5 chế độ chạy ứng dụng (WIN-003) — nguồn DUY NHẤT; ``Manifest.mode`` và
    evidence/tuple tham chiếu giá trị này. KHÔNG cộng gộp mode để báo tỷ lệ
    tương thích desktop (quy tắc báo cáo M3/M4; M1 chỉ bảo đảm ghi tách)."""

    NATIVE = "native"
    WEB = "web"
    WINE = "wine"
    VM = "vm"
    REMOTE = "remote"


@dataclass(frozen=True)
class CertificationTuple:
    """Tuple chứng nhận (§11.2): kết quả trên một tuple KHÔNG tự lan sang
    tuple khác. Đổi bất kỳ thành phần quan trọng ⇒ phải đánh giá lại
    (về ``untested``/``experimental``)."""

    os_build: str
    kernel: str | None
    graphics: str | None
    desktop_session: str
    runner_hash: str
    profile_digest: str
    app_build: str
    app_hash: str
    architecture: str
    runtime_dependency_versions: tuple[str, ...]
    dataset_revision: str
    test_suite_revision: str
    hardware_or_vm_profile: str
