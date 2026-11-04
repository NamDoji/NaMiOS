"""Chẩn đoán tổng hợp SmartAI M1 (SAI-006/007/008/009).

Gộp inventory (phạm vi đã đọc) + triage lỗi (đã redact) + dependency graph
(chặn execute) + route selection (COMP-025) thành một ``Diagnosis`` TRUNG
THỰC: nêu blocker + đề xuất bước kế, KHÔNG tự nhận "đã sửa"/"tương thích".
Model ngôn ngữ không tham gia ở đây — mọi kết luận là mã tất định từ dấu hiệu
quan sát được.
"""

from __future__ import annotations

from namios_compat._types import ResolveInput, RuntimeClassification, WorkflowEntry
from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import (
    DependencyGraph,
    Diagnosis,
    ErrorCategory,
    SystemInventory,
    TriageInput,
)
from namios_smartai.depgraph import execute_blockers
from namios_smartai.route import select_route
from namios_smartai.triage import triage_error

__all__ = ["diagnose"]

#: Loại lỗi mà khi KHÔNG có route kiểm chứng → đề xuất gói báo cáo vendor
#: (cần SDK/driver/plugin/API phía nhà cung cấp — không tự "sửa" được).
_VENDOR_CATEGORIES = frozenset(
    {
        ErrorCategory.PORTAL_PLUGIN,
        ErrorCategory.DEVICE_MISSING,
        ErrorCategory.UNSUPPORTED_API,
        ErrorCategory.LICENSE,
    }
)


def _human_blocker(descriptor: str) -> str:
    """``node_id|kind|reason`` → 'node_id (kind): reason'."""

    parts = descriptor.split("|")
    if len(parts) == 3:
        return f"{parts[0]} ({parts[1]}): {parts[2]}"
    return descriptor


def diagnose(
    workflow_id: str,
    *,
    triage_input: TriageInput | None = None,
    graph: DependencyGraph | None = None,
    entry: WorkflowEntry | None = None,
    resolve_input: ResolveInput | None = None,
    classification: RuntimeClassification | None = None,
    inventory: SystemInventory | None = None,
) -> Diagnosis:
    """Chẩn đoán một workflow/lỗi (SAI M1). Mọi đầu vào tùy chọn — có gì chẩn
    đoán nấy, phần thiếu ghi blocker, không bịa."""

    triage = triage_error(triage_input) if triage_input is not None else None

    raw_blockers = execute_blockers(graph) if graph is not None else ()
    human_blockers = [_human_blocker(b) for b in raw_blockers]
    execute_blocked = bool(raw_blockers)

    route_recommended: str | None = None
    route_no_verified = True
    route_reasons: tuple[str, ...] = ()
    if entry is not None and resolve_input is not None:
        rr = select_route(entry, resolve_input, classification=classification)
        route_recommended = rr.recommended.value if rr.recommended is not None else None
        route_no_verified = rr.no_verified_route
        route_reasons = rr.reasons_vi

    findings: list[str] = []
    if triage is not None:
        findings.extend(triage.evidence_vi)
    if execute_blocked:
        findings.append(
            t(
                "sai.diagnose.execute_blocked",
                lang=Lang.VI,
                blockers="; ".join(human_blockers),
            )
        )
    if route_no_verified:
        findings.append(t("sai.diagnose.no_verified_route", lang=Lang.VI, workflow_id=workflow_id))

    # Đề xuất bước kế (trung thực): vendor khi lỗi thuộc nhóm cần nhà cung cấp
    # và chưa có route; route khi có mode khả thi; còn lại = gom thêm thông tin.
    if triage is not None and triage.category in _VENDOR_CATEGORIES and route_no_verified:
        suggested = t("sai.diagnose.suggested.vendor", lang=Lang.VI)
    elif route_recommended is not None:
        suggested = t("sai.diagnose.suggested.route", lang=Lang.VI, mode=route_recommended)
    else:
        suggested = t("sai.diagnose.suggested.gather", lang=Lang.VI)

    blockers = tuple(human_blockers) + (route_reasons if route_no_verified else ())

    return Diagnosis(
        workflow_id=workflow_id,
        triage=triage,
        execute_blocked=execute_blocked,
        depgraph_blockers=tuple(human_blockers),
        route_recommended=route_recommended,
        route_no_verified=route_no_verified,
        inventory_read_fields=inventory.read_fields if inventory is not None else (),
        findings_vi=tuple(findings),
        suggested_action_vi=suggested,
        blockers=blockers,
    )
