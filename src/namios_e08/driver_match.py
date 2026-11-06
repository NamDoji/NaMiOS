"""Driver Match Service + provenance (E08-002/003).

Ghép driver theo HARDWARE-ID (VID:PID / id lớp thiết bị), THEO THỨ TỰ tier (kernel/
distro → lớp → OSS backend → vendor-linux → unsupported). KHÔNG ghép theo tên thương
mại gần giống (test D01: hai biến thể cùng tên, khác VID/PID → KHÔNG ghép sai). Provenance
fail-closed: thiếu nguồn chính thức / hash / chữ ký → KHÔNG tin (E08-003, test D04);
KHÔNG tải binary từ URL AI bịa.
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_e08 import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_e08._types import (
    DRIVER_TIER_ORDER,
    DriverCandidate,
    DriverMatch,
    DriverTier,
    Provenance,
)
from namios_i18n import Lang, t

__all__ = ["provenance_ok", "match_driver"]


def provenance_ok(p: Provenance) -> bool:
    """Nguồn gốc có tin được không (E08-003). Cần: nguồn chính thức + có hash + chữ
    ký hợp lệ. Thiếu bất kỳ → False (fail-closed, chống URL/binary trôi nổi)."""

    return bool(p.official) and bool(p.sha256.strip()) and bool(p.signature_ok)


def match_driver(
    hardware_id: str,
    candidates: Iterable[DriverCandidate],
) -> DriverMatch:
    """Ghép driver cho ``hardware_id`` (E08-002). Duyệt theo thứ tự tier; chọn ứng
    viên ĐẦU TIÊN mà (a) khai đúng ``hardware_id`` VÀ (b) provenance tin được. Không
    có → ``unsupported`` (KHÔNG đoán theo tên)."""

    hw = hardware_id.strip()
    cand_list = list(candidates)
    if not hw:
        return DriverMatch(
            matched=False,
            tier=DriverTier.UNSUPPORTED,
            package="",
            reason_vi=t("e08.driver.no_hwid", lang=Lang.VI),
        )

    for tier in DRIVER_TIER_ORDER:
        for c in cand_list:
            if c.tier is not tier:
                continue
            if hw not in c.hardware_ids:
                continue  # ghép theo hardware-id, KHÔNG theo tên
            if not provenance_ok(c.provenance):
                continue  # nguồn không tin → bỏ qua, không cài
            return DriverMatch(
                matched=True,
                tier=tier,
                package=c.package,
                reason_vi=t("e08.driver.matched", lang=Lang.VI, tier=tier.value),
            )

    return DriverMatch(
        matched=False,
        tier=DriverTier.UNSUPPORTED,
        package="",
        reason_vi=t("e08.driver.unsupported", lang=Lang.VI),
    )
