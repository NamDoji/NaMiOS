"""UX hỗ trợ: hướng dẫn tiếp-tục-được, quyền rõ ràng, chế độ offline (PRA-033..035).

- **Guidance** (PRA-033): checklist ≤3 bước/màn hình, có checkpoint để tiếp tục
  sau reboot.
- **Permission** (PRA-034): TÁI DÙNG ``namios_sys.data_authority.authorize`` —
  nguồn không tin cậy (tài liệu/web/log/output-tool) KHÔNG cấp được quyền mới;
  ký/nộp/thanh toán luôn cần xác nhận hành động cụ thể (SAI-017), không có grant
  chung.
- **Offline** (PRA-035): khi model cloud không dùng được, lõi in/scan/Wi‑Fi/app
  native VẪN chạy; chỉ phần suy-luận-AI-nâng-cao bị giảm.
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_i18n import Lang, t
from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra._types import (
    Checklist,
    ChecklistStep,
    OfflineReport,
    PermissionDecision,
    PermissionScope,
)
from namios_sys._types import SourceTrust
from namios_sys.data_authority import TRUSTED_SOURCES, authorize

__all__ = [
    "make_checklist",
    "visible_steps",
    "advance",
    "request_permission",
    "offline_capabilities",
]


# --------------------------------------------------------------------------- #
# PRA-033 — Hướng dẫn đa bước có thể tiếp tục                                   #
# --------------------------------------------------------------------------- #


def make_checklist(
    titles: Iterable[str],
    *,
    checkpoint: int = 0,
    max_visible: int = 3,
) -> Checklist:
    """Dựng checklist (PRA-033). ``max_visible`` ≥1 (mặc định 3); ``checkpoint``
    kẹp trong [0, số bước]."""

    steps = tuple(ChecklistStep(title_vi=s) for s in titles)
    cp = max(0, min(checkpoint, len(steps)))
    return Checklist(steps=steps, checkpoint=cp, max_visible=max(1, max_visible))


def visible_steps(cl: Checklist) -> tuple[ChecklistStep, ...]:
    """Các bước HIỂN THỊ trên một màn hình (PRA-033): tối đa ``max_visible`` kể từ
    checkpoint — không dồn hết lên một màn gây quá tải."""

    return cl.steps[cl.checkpoint : cl.checkpoint + cl.max_visible]


def advance(cl: Checklist) -> Checklist:
    """Hoàn tất bước hiện tại + đẩy checkpoint (PRA-033). Lưu được để tiếp tục sau
    reboot. Đã ở cuối → giữ nguyên (idempotent)."""

    if cl.checkpoint >= len(cl.steps):
        return cl
    steps = tuple(
        ChecklistStep(title_vi=s.title_vi, done=True) if i == cl.checkpoint else s
        for i, s in enumerate(cl.steps)
    )
    return Checklist(steps=steps, checkpoint=cl.checkpoint + 1, max_visible=cl.max_visible)


# --------------------------------------------------------------------------- #
# PRA-034 — Quyền rõ và dễ hiểu                                                 #
# --------------------------------------------------------------------------- #


def request_permission(
    action: str,
    *,
    scope: PermissionScope,
    source: SourceTrust,
    org_policy_allows: bool,
    content: str = "",
) -> PermissionDecision:
    """AI xin quyền trước khi thử sửa (PRA-034). Bất biến:

    - Nguồn KHÔNG tin cậy (log/web/tài liệu/output-tool) → KHÔNG cấp, kể cả khi
      ``org_policy_allows`` True (lệnh trong nội dung không nâng quyền được).
    - ``TRANSACT`` (ký/nộp/thanh toán) → KHÔNG grant chung; đòi xác nhận hành động
      cụ thể (SAI-017) ngay cả khi nguồn tin cậy + policy cho.
    - Nguồn tin cậy + policy cho + scope đọc/ghi → cấp (có thời hạn + hoàn tác).
    """

    decision = authorize(
        action, source=source, org_policy_allows=org_policy_allows, content=content
    )
    if not decision.allowed:
        # Nguồn không tin cậy được nêu rõ là "không cấp quyền mới cho AI".
        reason = (
            decision.reason_vi
            if source in TRUSTED_SOURCES
            else t("pra.perm.untrusted", lang=Lang.VI)
        )
        return PermissionDecision(granted=False, reason_vi=reason, error_code=decision.error_code)

    if scope is PermissionScope.TRANSACT:
        return PermissionDecision(
            granted=False,
            reason_vi=t("pra.perm.transact_confirm", lang=Lang.VI),
            requires_explicit_confirmation=True,
        )

    return PermissionDecision(
        granted=True,
        reason_vi=t("pra.perm.granted", lang=Lang.VI, scope=scope.value, action=action),
    )


# --------------------------------------------------------------------------- #
# PRA-035 — Chế độ máy yếu/không Internet                                       #
# --------------------------------------------------------------------------- #

#: Khả năng LÕI — không phụ thuộc model AI cloud (PRA-035). Luôn khả dụng.
_CORE_OFFLINE_KEYS: tuple[str, ...] = (
    "pra.offline.print",
    "pra.offline.scan",
    "pra.offline.wifi",
    "pra.offline.open_offline_app",
    "pra.offline.local_catalog",
    "pra.offline.local_diag",
)


def offline_capabilities(*, cloud_ai_available: bool) -> OfflineReport:
    """Khả năng khi model cloud bật/tắt (PRA-035). Lõi desktop/thiết bị/Office
    native luôn nằm trong ``available_vi`` bất kể cloud; chỉ suy-luận-AI-nâng-cao
    rơi vào ``degraded_vi`` khi cloud tắt."""

    available = tuple(t(k, lang=Lang.VI) for k in _CORE_OFFLINE_KEYS)
    degraded: tuple[str, ...] = (
        () if cloud_ai_available else (t("pra.offline.cloud_reasoning", lang=Lang.VI),)
    )
    return OfflineReport(
        cloud_ai_available=cloud_ai_available,
        available_vi=available,
        degraded_vi=degraded,
    )
