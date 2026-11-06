"""Compatibility Broker route (N10-017) — chọn tuyến THEO TÁC VỤ, không chỉ theo app.

Một app có thể "mở GUI được" (route ổn cho tác vụ ``open``) nhưng một tác vụ
CỤ THỂ của cùng app (vd ký số) phụ thuộc một node khác trong dependency graph
mà đã ``BLOCKED`` (token/middleware chỉ-Windows) → tác vụ đó PHẢI nhận route
KHÁC (hoặc ``unsupported``), KHÔNG được "ready" chỉ vì app mở được (N10-017
nghiệm thu). Kernel driver/token-chỉ-Windows KHÔNG BAO GIỜ được route Wine,
BẤT KỂ ``wine_tested`` nói gì — Wine không làm driver Linux (§0/§5).

TÁI DÙNG ``namios_e08.depgraph`` (``DepNode``/``DepState``/``workflow_verdict``)
cho dependency graph + ``namios_e08.actuator.action_is_safe`` cho N10-027
(không tự tải/vá binary); ``namios_pra.office_route``/``namios_odc.route_matrix``
cho tác vụ tài liệu Office — KHÔNG dựng lại bộ chọn tuyến Office thứ hai.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from namios_e08 import AiAction, DepKind, DepNode, DepState, WorkflowVerdict
from namios_e08 import workflow_verdict as e08_workflow_verdict
from namios_e08.actuator import action_is_safe
from namios_i18n import Lang, t
from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_mig._types import CompatRoute
from namios_odc import DocRouteResult, DocumentMetadata
from namios_odc.route_matrix import resolve_document_route
from namios_pra import OfficeNeed, OfficeRouteResult
from namios_pra.office_route import resolve_office_route

__all__ = [
    "TaskRouteResult",
    "resolve_task_route",
    "office_task_route",
    "office_document_route",
    "proposed_action_is_safe",
    "assess_dependency_verdict",
    # re-export tiện dùng (tái dùng namios_e08, không fork)
    "WorkflowVerdict",
    "DepKind",
    "DepNode",
    "DepState",
]


@dataclass(frozen=True)
class TaskRouteResult:
    """Kết quả chọn tuyến cho MỘT tác vụ của một app (N10-017). ``gui_openable``
    và ``task_ready`` TÁCH RIÊNG: app có thể mở GUI (``gui_openable=True``)
    trong khi tác vụ cụ thể này vẫn ``task_ready=False`` (vd ký số thất bại)."""

    task_id: str
    route: CompatRoute
    gui_openable: bool
    task_ready: bool
    reasons_vi: tuple[str, ...] = ()
    limitations_vi: tuple[str, ...] = ()


#: Loại dependency coi là "chỉ-Windows nếu BLOCKED" (token ký số/máy in vật
#: lý/driver chuyên biệt) — BLOCKED ở đây KHÔNG BAO GIỜ được vá bằng Wine.
_HARDWARE_OR_VENDOR_LOCKED_KINDS: frozenset[DepKind] = frozenset(
    {DepKind.PRINTER_TOKEN, DepKind.COM_SERVICE}
)


def resolve_task_route(
    task_id: str,
    nodes: Iterable[DepNode],
    *,
    gui_opens: bool,
    vendor_linux_native: bool = False,
    vendor_web: bool = False,
    wine_tested: bool = False,
    windows_licensed_available: bool = False,
) -> TaskRouteResult:
    """Chọn tuyến cho một tác vụ từ dependency graph + chứng cứ (N10-017).

    Thứ tự fail-closed:
    1. Vendor có Linux native/web chính thức → luôn ưu tiên (an toàn nhất,
       không phụ thuộc Windows).
    2. Có node BẮT BUỘC ``BLOCKED`` thuộc nhóm phần-cứng/vendor-khóa-Windows
       (``PRINTER_TOKEN``/``COM_SERVICE``) → KHÔNG BAO GIỜ route Wine — dù
       ``wine_tested=True``. Có Windows có phép → ``remote_windows``
       (``task_ready=False``, cần xác nhận thêm); không có → ``unsupported``.
    3. Node bắt buộc còn ``DOWN``/``MISSING``/``UNKNOWN`` (chưa chắc) → tuyến
       tạm (wine nếu đã thử) nhưng ``task_ready=False`` (chưa đủ bằng chứng).
    4. Mọi node bắt buộc ``OK`` → wine (nếu đã thử) hoặc remote_windows (nếu
       có Windows có phép) với ``task_ready=True``; không có gì → unsupported.
    """

    node_list = tuple(nodes)
    required = tuple(n for n in node_list if n.required)

    if vendor_linux_native:
        return TaskRouteResult(
            task_id,
            CompatRoute.NATIVE,
            gui_openable=True,
            task_ready=True,
            reasons_vi=(t("mig.route.vendor_native", lang=Lang.VI),),
        )
    if vendor_web:
        return TaskRouteResult(
            task_id,
            CompatRoute.WEB,
            gui_openable=True,
            task_ready=True,
            reasons_vi=(t("mig.route.vendor_web", lang=Lang.VI),),
        )

    locked_blocked = tuple(
        n
        for n in required
        if n.state is DepState.BLOCKED and n.kind in _HARDWARE_OR_VENDOR_LOCKED_KINDS
    )
    other_blocked = tuple(
        n
        for n in required
        if n.state is DepState.BLOCKED and n.kind not in _HARDWARE_OR_VENDOR_LOCKED_KINDS
    )
    if locked_blocked or other_blocked:
        if windows_licensed_available:
            return TaskRouteResult(
                task_id,
                CompatRoute.REMOTE_WINDOWS,
                gui_openable=gui_opens,
                task_ready=False,
                reasons_vi=(t("mig.route.blocked_kernel_windows", lang=Lang.VI),),
                limitations_vi=(t("mig.route.needs_confirmation", lang=Lang.VI),),
            )
        return TaskRouteResult(
            task_id,
            CompatRoute.UNSUPPORTED,
            gui_openable=gui_opens,
            task_ready=False,
            reasons_vi=(t("mig.route.blocked_unsupported", lang=Lang.VI),),
        )

    degraded = tuple(
        n for n in required if n.state in (DepState.DOWN, DepState.MISSING, DepState.UNKNOWN)
    )
    if degraded:
        if wine_tested:
            return TaskRouteResult(
                task_id,
                CompatRoute.WINE,
                gui_openable=gui_opens,
                task_ready=False,
                reasons_vi=(t("mig.route.degraded", lang=Lang.VI),),
            )
        return TaskRouteResult(
            task_id,
            CompatRoute.UNSUPPORTED,
            gui_openable=gui_opens,
            task_ready=False,
            reasons_vi=(t("mig.route.degraded", lang=Lang.VI),),
        )

    if wine_tested:
        return TaskRouteResult(
            task_id,
            CompatRoute.WINE,
            gui_openable=gui_opens,
            task_ready=True,
            reasons_vi=(t("mig.route.wine_ok", lang=Lang.VI),),
        )
    if windows_licensed_available:
        return TaskRouteResult(
            task_id,
            CompatRoute.REMOTE_WINDOWS,
            gui_openable=gui_opens,
            task_ready=True,
            reasons_vi=(t("mig.route.remote_windows_ok", lang=Lang.VI),),
        )
    return TaskRouteResult(
        task_id,
        CompatRoute.UNSUPPORTED,
        gui_openable=gui_opens,
        task_ready=False,
        reasons_vi=(t("mig.route.blocked_unsupported", lang=Lang.VI),),
    )


def office_task_route(
    needs: Iterable[OfficeNeed], *, has_native_support: bool = True, web_available: bool = False
) -> OfficeRouteResult:
    """Tuyến cho tác vụ Office theo NHU CẦU (N10-023/031 "soạn DOCX"/"bảng
    XLSX"). TÁI DÙNG ``namios_pra.office_route.resolve_office_route`` —
    macro/add-in/ký không bao giờ ra web."""

    return resolve_office_route(
        tuple(needs), has_native_support=has_native_support, web_available=web_available
    )


def office_document_route(metadata: DocumentMetadata, **kwargs: object) -> DocRouteResult:
    """Tuyến cho MỘT tài liệu Office đã khảo sát được metadata (N10-031).
    TÁI DÙNG ``namios_odc.route_matrix.resolve_document_route`` — tách 4 trục
    mở/sửa/in/macro, không dựng lại bộ chọn tuyến tài liệu thứ hai."""

    return resolve_document_route(metadata, **kwargs)  # type: ignore[arg-type]


def proposed_action_is_safe(tool_name: str, *, changes_system: bool, rollback_id: str = "") -> bool:
    """Một đề xuất hành động của SmartAI trong luồng chọn-tuyến có an toàn
    không (N10-027 "Không tự tải hoặc vá binary"). TÁI DÙNG
    ``namios_e08.actuator.action_is_safe`` — chặn root/shell/exec/
    download_binary/flash/sign_submit và bước thay-đổi thiếu rollback."""

    action = AiAction(incident_id="mig", tool_name=tool_name, rollback_id=rollback_id)
    return action_is_safe(action, changes_system=changes_system)


#: Kết luận workflow TỔNG của app (mở GUI ≠ dùng được) — TÁI DÙNG
#: ``namios_e08.depgraph.workflow_verdict`` trực tiếp, không ghép lại.
assess_dependency_verdict = e08_workflow_verdict
