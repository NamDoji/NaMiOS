"""Validator hợp đồng SYS (SYS-037).

Chặn hai lỗi trung thực cốt lõi: (a) ``app_route`` thiếu nguồn/version → không
khớp được hồ sơ tương thích; (b) bước ``workflow_run`` báo thành công nhưng
THIẾU evidence → "app mở được ≠ hoàn thành". Nạp từ dict KHÔNG tin nhãn
``state`` tự khai (gate chứng nhận mới quyết — SYS-013).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from namios_core.validation import ValidationError
from namios_eco.status import WindowsMode
from namios_i18n import Lang, t
from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_sys._errors import SysErrorCode
from namios_sys._types import (
    ActionStatus,
    AppRoute,
    LicenseStatus,
    RunState,
    WorkflowRun,
    WorkflowStepRun,
)

__all__ = [
    "validate_app_route",
    "validate_workflow_run",
    "app_route_from_dict",
    "workflow_run_from_dict",
]

#: Mode cần bộ cài (phải có nguồn: publisher/installer_hash) — SYS-009/037.
_INSTALLER_MODES: frozenset[WindowsMode] = frozenset(
    {WindowsMode.WINE, WindowsMode.WINDOWS_VM, WindowsMode.REMOTE_WINDOWS}
)

#: Trạng thái bước coi là "đã hoàn thành" → BẮT BUỘC có evidence (SYS-013/037).
_COMPLETED_STEP_STATUSES: frozenset[ActionStatus] = frozenset(
    {ActionStatus.SUCCESS, ActionStatus.PARTIAL}
)


def validate_app_route(route: AppRoute) -> list[ValidationError]:
    """Điều kiện CẤU TRÚC cho app_route (SYS-008/037). Rỗng = đủ điều kiện."""

    errors: list[ValidationError] = []
    if not (route.version or "").strip():
        errors.append(
            ValidationError(
                code=SysErrorCode.E_SYS_ROUTE_NO_VERSION.value,
                path="version",
                message_vi=t("sys.schema.route_no_version", lang=Lang.VI),
            )
        )
    # Mode cần bộ cài phải có nguồn (publisher HOẶC installer_hash) — không để
    # route "trần" chạy recipe. (native/web không cần bộ cài → bỏ qua.)
    if route.mode in _INSTALLER_MODES:
        has_source = bool((route.publisher or "").strip()) or bool(
            (route.installer_hash or "").strip()
        )
        if not has_source:
            errors.append(
                ValidationError(
                    code=SysErrorCode.E_SYS_ROUTE_NO_SOURCE.value,
                    path="installer_hash",
                    message_vi=t("sys.schema.route_no_source", lang=Lang.VI),
                )
            )
    return errors


def validate_workflow_run(run: WorkflowRun) -> list[ValidationError]:
    """Mỗi bước SUCCESS/PARTIAL phải có evidence (SYS-013/037). Rỗng = hợp lệ."""

    errors: list[ValidationError] = []
    for step in run.steps:
        # Phải có ÍT NHẤT MỘT evidence id KHÔNG rỗng — ``("",)``/``("  ",)`` là
        # bằng chứng giả, không tính (cùng lớp lỗi COMPAT-ADV-001 evidence rỗng).
        has_real_evidence = any((e or "").strip() for e in step.evidence_ids)
        if step.status in _COMPLETED_STEP_STATUSES and not has_real_evidence:
            errors.append(
                ValidationError(
                    code=SysErrorCode.E_SYS_STEP_NO_EVIDENCE.value,
                    path=f"steps.{step.step_id}",
                    message_vi=t("sys.schema.step_no_evidence", lang=Lang.VI, step=step.step_id),
                )
            )
    return errors


def _enum(value: Any, enum_cls: type, default: Any) -> Any:
    try:
        return enum_cls(str(value))
    except ValueError:
        return default


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return ()


def app_route_from_dict(raw: Mapping[str, Any]) -> AppRoute:
    """Dựng ``AppRoute`` từ dict (JSON). Trường thiếu → mặc định an toàn; giá
    trị enum lạ → mặc định bảo thủ (native/unknown), KHÔNG lỗi im lặng nguy hiểm."""

    return AppRoute(
        app_id=str(raw.get("app_id", "")),
        version=str(raw.get("version", "")),
        publisher=str(raw.get("publisher", "")),
        installer_hash=(raw.get("installer_hash") or None),
        mode=_enum(raw.get("mode", "native_linux"), WindowsMode, WindowsMode.NATIVE_LINUX),
        license_status=_enum(
            raw.get("license_status", "unknown"), LicenseStatus, LicenseStatus.UNKNOWN
        ),
        recipe_id=(raw.get("recipe_id") or None),
        verified_workflows=_str_tuple(raw.get("verified_workflows")),
    )


def workflow_run_from_dict(raw: Mapping[str, Any]) -> WorkflowRun:
    """Dựng ``WorkflowRun`` từ dict. ``state`` LUÔN về ``proposed`` khi nạp từ
    ngoài (không tin nhãn tự khai — gate chứng nhận mới nâng, SYS-013)."""

    steps_raw = raw.get("steps")
    steps: list[WorkflowStepRun] = []
    if isinstance(steps_raw, (list, tuple)):
        for i, s in enumerate(steps_raw):
            if not isinstance(s, Mapping):
                continue
            steps.append(
                WorkflowStepRun(
                    step_id=str(s.get("step_id", f"s{i}")),
                    name=str(s.get("name", "")),
                    status=_enum(s.get("status", "blocked"), ActionStatus, ActionStatus.BLOCKED),
                    evidence_ids=_str_tuple(s.get("evidence_ids")),
                )
            )
    return WorkflowRun(
        task_id=str(raw.get("task_id", "")),
        user_intent=str(raw.get("user_intent", "")),
        route_id=(raw.get("route_id") or None),
        steps=tuple(steps),
        evidence_ids=_str_tuple(raw.get("evidence_ids")),
        business_approval=str(raw.get("business_approval", "pending")),
        state=RunState.PROPOSED,
    )
