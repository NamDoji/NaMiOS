"""Compatibility Resolver (COMP-025).

Nhận ngữ cảnh runtime thật (``ResolveInput``) + hồ sơ workflow đã khảo sát
(``WorkflowEntry``), trả danh sách mode theo THỨ TỰ ĐIỀU TRA mặc định
(native_linux → web_linux → wine → remote_windows → windows_vm) kèm lý do,
phụ thuộc, giới hạn, và mode ĐỀ XUẤT.

Hai bất biến trung thực (nghiệm thu COMP-025):
1. Nếu KHÔNG mode nào đạt ``workflow_verified`` cho tác vụ bắt buộc →
   ``no_verified_route=True``; KHÔNG đoán thành "chạy được".
2. Đổi ``app_version`` hoặc ``token_model`` so với bản đã chứng nhận → chứng
   nhận tương ứng MẤT HIỆU LỰC (route bị hạ khỏi verified, cần tái kiểm) —
   không giữ verified bằng metadata cũ.

Resolver KHÔNG tự nâng trạng thái: nó chỉ ĐỌC trạng thái route (đã do schema
COMP-048 + gate evidence COMP-049 quyết), áp mất-hiệu-lực, và lọc feasibility.
"""

from __future__ import annotations

from namios_compat import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_compat._types import (
    MODE_INVESTIGATION_ORDER,
    UNRESOLVED_VERSIONS,
    ResolveInput,
    Route,
    RouteCandidate,
    RouteResolution,
    WorkflowEntry,
)
from namios_eco.status import NEVER_USABLE_STATUSES, PublishedStatus, WindowsMode
from namios_i18n import Lang, t

__all__ = ["resolve_routes"]

#: Hiển thị khi không biết giá trị thực tế (app_version/token rỗng/None).
_UNKNOWN_LABEL = "(không xác định)"

_STATUS_REASON_KEY: dict[PublishedStatus, str] = {
    PublishedStatus.WORKFLOW_VERIFIED: "compat.resolver.reason.mode_verified",
    PublishedStatus.PARTIAL_WORKFLOW: "compat.resolver.reason.mode_partial",
    PublishedStatus.NOT_INVENTORIED: "compat.resolver.reason.mode_not_inventoried",
    PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY: "compat.resolver.reason.mode_blocked",
    PublishedStatus.UNSUPPORTED: "compat.resolver.reason.mode_unsupported",
    PublishedStatus.REVOKED: "compat.resolver.reason.mode_unsupported",
    PublishedStatus.DOWNLOADABLE_ONLY: "compat.resolver.reason.mode_never_usable",
    PublishedStatus.LAUNCHES_ONLY: "compat.resolver.reason.mode_never_usable",
}


def _parse_status(raw: str) -> PublishedStatus:
    try:
        return PublishedStatus(raw)
    except ValueError:
        # Phòng thủ: trạng thái lạ coi như chưa khảo sát (schema COMP-048 lẽ
        # ra đã chặn từ lúc nạp — không bao giờ tự nâng thành verified).
        return PublishedStatus.NOT_INVENTORIED


def _routes_by_mode(entry: WorkflowEntry) -> dict[WindowsMode, Route]:
    out: dict[WindowsMode, Route] = {}
    for r in entry.routes:
        out[r.mode] = r
    return out


def _feasibility(mode: WindowsMode, inp: ResolveInput) -> tuple[bool, str | None, tuple[str, ...]]:
    """Trả ``(feasible, infeasible_reason_key|None, dependencies)`` cho mode."""

    if mode == WindowsMode.NATIVE_LINUX:
        return True, None, ()
    if mode == WindowsMode.WEB_LINUX:
        if not inp.network_online:
            return False, "compat.resolver.reason.infeasible_network", ("network",)
        return True, None, ("network",)
    if mode == WindowsMode.WINE:
        if not inp.license_ok:
            return False, "compat.resolver.reason.infeasible_license", ("app_license",)
        return True, None, ("app_license",)
    if mode == WindowsMode.REMOTE_WINDOWS:
        deps: tuple[str, ...] = ("org_policy", "windows_license", "network")
        if not inp.org_policy_allows_remote:
            return False, "compat.resolver.reason.infeasible_policy", deps
        if not inp.license_ok:
            return False, "compat.resolver.reason.infeasible_license", deps
        if not inp.network_online:
            return False, "compat.resolver.reason.infeasible_network", deps
        return True, None, deps
    if mode == WindowsMode.WINDOWS_VM:
        deps = ("org_policy", "windows_license")
        if not inp.org_policy_allows_remote:
            return False, "compat.resolver.reason.infeasible_policy", deps
        if not inp.license_ok:
            return False, "compat.resolver.reason.infeasible_license", deps
        return True, None, deps
    return False, "compat.resolver.reason.no_route_for_mode", ()  # pragma: no cover


def _cert_invalidation(
    entry: WorkflowEntry, inp: ResolveInput
) -> tuple[PublishedStatus | None, str | None]:
    """Nếu chứng nhận mất hiệu lực (đổi app version / token, HOẶC không xác
    nhận được version/token hiện tại) → trả ``(NOT_INVENTORIED, reason_key)``
    để hạ route khỏi verified/partial. Ngược lại ``(None, None)``.

    Bảo thủ (COMP-025 + QA COMPAT-ADV-003/004): nếu chứng nhận pin một version
    cụ thể mà ngữ cảnh KHÔNG biết version đang chạy (``app_version`` rỗng) →
    KHÔNG xác nhận được khớp → coi như mất hiệu lực. Tương tự với workflow ký
    số mà không biết token (``token_model=None``) → không xác nhận được."""

    cert_app = entry.app.version
    if cert_app in UNRESOLVED_VERSIONS:
        # Chứng nhận chưa pin version cụ thể → KHÔNG thể xác nhận khớp với bản
        # đang chạy → không giữ verified/partial (COMPAT-ADV-005). Chỉ ảnh
        # hưởng route verified/partial (vòng lặp chính), route not_inventoried
        # giữ nguyên.
        return (
            PublishedStatus.NOT_INVENTORIED,
            t(
                "compat.resolver.reason.cert_stale_app",
                lang=Lang.VI,
                got=inp.app_version or _UNKNOWN_LABEL,
                want=_UNKNOWN_LABEL,
            ),
        )
    if not inp.app_version or inp.app_version != cert_app:
        return (
            PublishedStatus.NOT_INVENTORIED,
            t(
                "compat.resolver.reason.cert_stale_app",
                lang=Lang.VI,
                got=inp.app_version or _UNKNOWN_LABEL,
                want=cert_app,
            ),
        )
    if "signing_method" in entry.requires:
        pinned = entry.certification.device_models
        if inp.token_model is None or (pinned and inp.token_model not in pinned):
            return (
                PublishedStatus.NOT_INVENTORIED,
                t(
                    "compat.resolver.reason.cert_stale_token",
                    lang=Lang.VI,
                    token=inp.token_model or _UNKNOWN_LABEL,
                ),
            )
    return (None, None)


def resolve_routes(inp: ResolveInput, entry: WorkflowEntry) -> RouteResolution:
    """Giải đường chạy cho một workflow (COMP-025)."""

    by_mode = _routes_by_mode(entry)
    stale_status, stale_reason = _cert_invalidation(entry, inp)

    candidates: list[RouteCandidate] = []
    recommended: WindowsMode | None = None
    verified_exists = False

    for mode in MODE_INVESTIGATION_ORDER:
        route = by_mode.get(mode)
        if route is None:
            candidates.append(
                RouteCandidate(
                    mode=mode,
                    feasible=False,
                    status=PublishedStatus.NOT_INVENTORIED.value,
                    reason_vi=t(
                        "compat.resolver.reason.no_route_for_mode", lang=Lang.VI, mode=mode.value
                    ),
                )
            )
            continue

        raw_status = _parse_status(route.status)
        effective = raw_status
        reason_vi: str

        # Mất hiệu lực chứng nhận: chỉ hạ các route đang (hoặc từng) tự nhận
        # usable (verified/partial) — route chưa khảo sát/blocked giữ nguyên.
        if stale_status is not None and raw_status in (
            PublishedStatus.WORKFLOW_VERIFIED,
            PublishedStatus.PARTIAL_WORKFLOW,
        ):
            effective = stale_status
            assert stale_reason is not None
            reason_vi = stale_reason
        else:
            reason_vi = t(
                _STATUS_REASON_KEY.get(effective, "compat.resolver.reason.mode_not_inventoried"),
                lang=Lang.VI,
                mode=mode.value,
            )

        feasible, infeasible_key, deps = _feasibility(mode, inp)
        limits: tuple[str, ...] = ()
        if not feasible and infeasible_key is not None:
            limits = (t(infeasible_key, lang=Lang.VI, mode=mode.value),)

        if effective == PublishedStatus.WORKFLOW_VERIFIED:
            verified_exists = True
            if feasible and recommended is None:
                recommended = mode

        candidates.append(
            RouteCandidate(
                mode=mode,
                feasible=feasible,
                status=effective.value,
                reason_vi=reason_vi,
                dependencies=deps,
                limits_vi=limits,
                untested_steps=(),
            )
        )

    no_verified_route = not verified_exists
    if no_verified_route:
        reasons_vi: tuple[str, ...] = (
            t(
                "compat.resolver.reason.no_verified_route",
                lang=Lang.VI,
                workflow_id=inp.workflow_id,
            ),
        )
    elif recommended is not None:
        reasons_vi = (
            t("compat.resolver.reason.recommended", lang=Lang.VI, mode=recommended.value),
        )
    else:
        # Có route verified nhưng không mode nào khả thi trong ngữ cảnh hiện
        # tại — nêu đúng lý do chặn của route verified đầu tiên (limits).
        first_verified = next(
            (c for c in candidates if c.status == PublishedStatus.WORKFLOW_VERIFIED.value),
            None,
        )
        if first_verified is not None and first_verified.limits_vi:
            reasons_vi = first_verified.limits_vi
        elif first_verified is not None:
            reasons_vi = (first_verified.reason_vi,)
        else:  # pragma: no cover - không đạt được khi verified_exists=True
            reasons_vi = ()

    # Bất biến: không bao giờ "đề xuất" một mode never-usable (GATE ECO-003).
    if recommended is not None:
        rec_status = next(
            (PublishedStatus(c.status) for c in candidates if c.mode == recommended),
            PublishedStatus.NOT_INVENTORIED,
        )
        assert rec_status not in NEVER_USABLE_STATUSES

    return RouteResolution(
        workflow_id=inp.workflow_id,
        candidates=tuple(candidates),
        recommended=recommended,
        no_verified_route=no_verified_route,
        reasons_vi=reasons_vi,
    )
