"""Office Route Resolver + Fidelity Gate (PRA-016/017).

Chọn tuyến xử lý tài liệu theo NHU CẦU (read/print/edit/collaborate/macro/addin/
sign) — bất biến then chốt: file cần MACRO/COM/ADD-IN KHÔNG gán được Office web
(VBA không chạy trên web, nguồn Microsoft §4.1); phải Windows VM/remote. Fidelity
Gate: khác biệt NGHĨA (số tiền/trang/chữ ký) → CHẶN lưu/in ("mở được ≠ đúng dữ liệu").
"""

from __future__ import annotations

from collections.abc import Sequence

from namios_i18n import Lang, t
from namios_pra import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_pra._types import (
    FidelityIssue,
    FidelitySeverity,
    OfficeNeed,
    OfficeRoute,
    OfficeRouteResult,
)

__all__ = ["resolve_office_route", "fidelity_gate", "is_fidelity_blocked"]

#: Nhu cầu CHỈ chạy trên Office desktop Windows (PRA-016 §4.1): macro/add-in.
_WINDOWS_DESKTOP_NEEDS: frozenset[OfficeNeed] = frozenset({OfficeNeed.MACRO, OfficeNeed.ADDIN})


def resolve_office_route(
    needs: Sequence[OfficeNeed],
    *,
    has_native_support: bool = True,
    web_available: bool = False,
) -> OfficeRouteResult:
    """Chọn tuyến Office TRUNG THỰC.

    - Cần macro/add-in → Windows VM/remote (không bao giờ web). windows_dependent=True.
    - Cần ký (sign) → cũng ưu tiên Windows desktop/remote (plugin cổng thường khóa Windows),
      trừ khi chỉ read → viewer.
    - Chỉ đọc → native nếu có, hoặc viewer read-only.
    - Sửa/in phổ thông → native Linux nếu hỗ trợ; else web nếu có; else blocked.
    """

    need_set = set(needs)

    # 1) Macro/COM/add-in: tuyệt đối không web.
    if need_set & _WINDOWS_DESKTOP_NEEDS:
        return OfficeRouteResult(
            route=OfficeRoute.WINDOWS_VM,
            reasons_vi=(t("pra.office.macro_not_web", lang=Lang.VI),),
            windows_dependent=True,
        )

    # 2) Ký số: cần desktop/remote Windows (plugin cổng), trừ khi chỉ read.
    if OfficeNeed.SIGN in need_set:
        return OfficeRouteResult(
            route=OfficeRoute.WINDOWS_VM,
            reasons_vi=(
                t(
                    "pra.office.windows_needed",
                    lang=Lang.VI,
                    needs=", ".join(sorted(n.value for n in need_set)),
                ),
            ),
            windows_dependent=True,
        )

    # 3) Chỉ đọc (không edit/collaborate) → native nếu có, else viewer read-only.
    only_read = need_set <= {OfficeNeed.READ, OfficeNeed.PRINT}
    if only_read:
        if has_native_support:
            return OfficeRouteResult(
                OfficeRoute.NATIVE_LINUX, (t("pra.office.native", lang=Lang.VI),)
            )
        return OfficeRouteResult(
            OfficeRoute.VIEWER_READONLY, (t("pra.office.viewer", lang=Lang.VI),)
        )

    # 4) Sửa/cộng tác phổ thông: native → web → blocked.
    if has_native_support:
        return OfficeRouteResult(OfficeRoute.NATIVE_LINUX, (t("pra.office.native", lang=Lang.VI),))
    if web_available:
        return OfficeRouteResult(OfficeRoute.MS365_WEB, (t("pra.office.web", lang=Lang.VI),))
    return OfficeRouteResult(OfficeRoute.BLOCKED, (t("pra.office.blocked", lang=Lang.VI),))


def is_fidelity_blocked(issues: Sequence[FidelityIssue]) -> bool:
    """``True`` nếu có BẤT KỲ khác biệt ``BLOCKING`` (số tiền/trang/chữ ký…)."""

    return any(i.severity == FidelitySeverity.BLOCKING for i in issues)


def fidelity_gate(issues: Sequence[FidelityIssue]) -> tuple[bool, str]:
    """Cổng fidelity (PRA-017): trả (cho_phép_lưu_in, lý_do_VI). Có issue BLOCKING
    → (False, nêu các trường sai). Không có → (True, ok)."""

    blocking = [i for i in issues if i.severity == FidelitySeverity.BLOCKING]
    if blocking:
        fields = ", ".join(i.field for i in blocking)
        return False, t("pra.fidelity.blocking", lang=Lang.VI, fields=fields)
    return True, t("pra.fidelity.ok", lang=Lang.VI)
