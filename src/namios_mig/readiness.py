"""Điểm sẵn sàng chuyển đổi (N10-009).

``ready`` / ``ready_with_limits`` / ``pilot_only`` / ``blocked`` / ``unknown``.
BẤT BIẾN then chốt: một công việc THIẾT YẾU (``essential=True``) bị chặn
(``UNSUPPORTED``/``FAILED``/``NEEDS_RETEST``/thiếu thiết bị) → CẢ MÁY
``blocked`` — dù 90% app khác ``ready`` (kế toán không ký được hóa đơn = máy
blocked dù mở được Word/Zalo). Thiếu bằng chứng (chưa test) trên một việc
thiết yếu → ``unknown`` (không được tự nhận ``ready``).

TÁI DÙNG ``namios_pra.device_hub.is_supported`` cho phần phụ thuộc thiết bị —
"nhận thiết bị" không đủ, phải kiểm chức năng THẬT.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import Enum

from namios_i18n import Lang, t
from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_mig._types import CertState, CompatRoute, WorkflowTestStatus
from namios_pra import DeviceCapability, DeviceFunction
from namios_pra.device_hub import is_supported

__all__ = [
    "ReadinessLevel",
    "AppReadinessInput",
    "MachineReadiness",
    "is_device_requirement_met",
    "compute_machine_readiness",
]


class ReadinessLevel(str, Enum):
    """5 mức sẵn sàng chuyển đổi (N10-009)."""

    READY = "ready"
    READY_WITH_LIMITS = "ready_with_limits"
    PILOT_ONLY = "pilot_only"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


#: Route coi là "có giới hạn" dù workflow pass (N10-009/017) — phụ thuộc
#: Wine/Windows vẫn chạy được nhưng kèm điều kiện, không phải native/web sạch.
_LIMITED_ROUTES: frozenset[CompatRoute] = frozenset(
    {CompatRoute.WINE, CompatRoute.REMOTE_WINDOWS, CompatRoute.VENDOR_PORT}
)


@dataclass(frozen=True)
class AppReadinessInput:
    """Đầu vào readiness cho MỘT app/công việc (N10-008/009). ``essential``
    đến từ bản đồ công việc (N10-008) — KHÔNG phải mọi app cài trên máy đều
    essential. ``device_ready`` do caller tính qua ``is_device_requirement_met``
    nếu công việc phụ thuộc một ngoại vi cụ thể (mặc định ``True`` = không phụ
    thuộc thiết bị nào)."""

    app_id: str
    essential: bool
    route: CompatRoute
    workflow_status: WorkflowTestStatus = WorkflowTestStatus.NOT_TESTED
    cert_state: CertState = CertState.REPORTED
    device_ready: bool = True
    limitations_vi: tuple[str, ...] = ()


@dataclass(frozen=True)
class MachineReadiness:
    """Kết luận sẵn sàng của CẢ MÁY (N10-009). ``blocking_apps`` = app/công
    việc thiết yếu gây ra mức hiện tại (rỗng ở mức ``ready``)."""

    level: ReadinessLevel
    blocking_apps: tuple[str, ...] = ()
    reasons_vi: tuple[str, ...] = ()


def _coerce_route(value: object) -> CompatRoute:
    """Ép ``route`` về ``CompatRoute`` FAIL-CLOSED: chuỗi lạ/không nhận diện →
    ``UNSUPPORTED`` (xấu nhất = blocker)."""

    if isinstance(value, CompatRoute):
        return value
    if isinstance(value, str):
        try:
            return CompatRoute(value)
        except ValueError:
            return CompatRoute.UNSUPPORTED
    return CompatRoute.UNSUPPORTED


def _coerce_workflow(value: object) -> WorkflowTestStatus:
    """Ép ``workflow_status`` FAIL-CLOSED: chuỗi lạ/không nhận diện → ``FAILED``
    (xấu nhất = blocker)."""

    if isinstance(value, WorkflowTestStatus):
        return value
    if isinstance(value, str):
        try:
            return WorkflowTestStatus(value)
        except ValueError:
            return WorkflowTestStatus.FAILED
    return WorkflowTestStatus.FAILED


def _coerce_cert(value: object) -> CertState:
    """Ép ``cert_state`` FAIL-CLOSED: chuỗi lạ/không nhận diện → ``NEEDS_RETEST``
    (xấu nhất = blocker)."""

    if isinstance(value, CertState):
        return value
    if isinstance(value, str):
        try:
            return CertState(value)
        except ValueError:
            return CertState.NEEDS_RETEST
    return CertState.NEEDS_RETEST


def is_device_requirement_met(cap: DeviceCapability, func: DeviceFunction) -> bool:
    """Yêu cầu thiết bị của một công việc có đạt chưa (N10-047). TÁI DÙNG
    ``namios_pra.device_hub.is_supported`` — chỉ ``True`` khi chức năng đã
    kiểm ``WORKS``; "thấy thiết bị" không đủ."""

    return is_supported(cap, func)


def compute_machine_readiness(apps: Iterable[AppReadinessInput]) -> MachineReadiness:
    """Tính điểm sẵn sàng CẢ MÁY (N10-009), fail-closed theo thứ tự ưu tiên
    BLOCKED > UNKNOWN > PILOT_ONLY > READY_WITH_LIMITS > READY:

    1. Không có công việc thiết yếu nào được khai → ``UNKNOWN`` (chưa đủ dữ
       liệu để kết luận, không suy "chắc là ready").
    2. Một công việc thiết yếu ``UNSUPPORTED``/``FAILED``/``NEEDS_RETEST``/
       thiếu thiết bị → ``BLOCKED`` — BẤT KỂ app khác ra sao.
    3. Một công việc thiết yếu chưa test (``NOT_TESTED``) → ``UNKNOWN``.
    4. Một công việc thiết yếu chưa ``PUBLISHED`` (còn ``lab_tested``/
       ``pilot_verified``/``reported``) → ``PILOT_ONLY``.
    5. Một công việc thiết yếu ``PARTIAL``/có hạn chế/route Wine-Windows →
       ``READY_WITH_LIMITS``.
    6. Còn lại → ``READY``.
    """

    # Coerce enum fail-closed NGAY từ đầu (dữ liệu khảo sát có thể gửi chuỗi):
    # so bằng ``is`` trên chuỗi hợp lệ sẽ trượt mọi guard → fail-OPEN. Chuỗi
    # lạ/không nhận diện được → giá trị XẤU NHẤT (unsupported/failed/needs_retest).
    required = tuple(
        replace(
            a,
            route=_coerce_route(a.route),
            workflow_status=_coerce_workflow(a.workflow_status),
            cert_state=_coerce_cert(a.cert_state),
        )
        for a in apps
        if a.essential
    )
    if not required:
        return MachineReadiness(
            ReadinessLevel.UNKNOWN, reasons_vi=(t("mig.readiness.no_essential", lang=Lang.VI),)
        )

    blockers = tuple(
        a
        for a in required
        if a.route == CompatRoute.UNSUPPORTED
        or a.workflow_status == WorkflowTestStatus.FAILED
        or a.cert_state == CertState.NEEDS_RETEST
        or not a.device_ready
    )
    if blockers:
        ids = tuple(a.app_id for a in blockers)
        return MachineReadiness(
            ReadinessLevel.BLOCKED,
            blocking_apps=ids,
            reasons_vi=(t("mig.readiness.blocked", lang=Lang.VI, apps=", ".join(ids)),),
        )

    untested = tuple(a for a in required if a.workflow_status == WorkflowTestStatus.NOT_TESTED)
    if untested:
        ids = tuple(a.app_id for a in untested)
        return MachineReadiness(
            ReadinessLevel.UNKNOWN,
            blocking_apps=ids,
            reasons_vi=(t("mig.readiness.unknown", lang=Lang.VI, apps=", ".join(ids)),),
        )

    not_published = tuple(a for a in required if a.cert_state != CertState.PUBLISHED)
    if not_published:
        ids = tuple(a.app_id for a in not_published)
        return MachineReadiness(
            ReadinessLevel.PILOT_ONLY,
            blocking_apps=ids,
            reasons_vi=(t("mig.readiness.pilot_only", lang=Lang.VI, apps=", ".join(ids)),),
        )

    limited = tuple(
        a
        for a in required
        if a.workflow_status == WorkflowTestStatus.PARTIAL
        or a.limitations_vi
        or a.route in _LIMITED_ROUTES
    )
    if limited:
        ids = tuple(a.app_id for a in limited)
        return MachineReadiness(
            ReadinessLevel.READY_WITH_LIMITS,
            blocking_apps=ids,
            reasons_vi=(t("mig.readiness.limits", lang=Lang.VI, apps=", ".join(ids)),),
        )

    return MachineReadiness(
        ReadinessLevel.READY, reasons_vi=(t("mig.readiness.ready", lang=Lang.VI),)
    )
