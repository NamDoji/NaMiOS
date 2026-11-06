"""Windows dependency graph + outcome validator (E08-020/031).

DAG installer→runtime→COM/service→DB→printer/token→portal→export/submit. Kết luận
workflow TRUNG THỰC: "mở GUI" ≠ "dùng được". DB mất → ``partial``; cổng thiếu plugin →
``blocked`` (test N02/A02). ``tool_success`` ≠ ``user_workflow_success`` — chỉ tính
hoàn-thành khi kỹ-thuật-ổn + nghiệp-vụ-duyệt + có bằng chứng (reuse tinh thần
``namios_pra.progress``/``namios_sys.goal``).
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_e08._types import DepNode, DepState, WorkflowVerdict

__all__ = ["workflow_verdict", "is_workflow_complete", "tool_success_is_workflow_success"]


def workflow_verdict(nodes: Iterable[DepNode]) -> WorkflowVerdict:
    """Kết luận workflow từ các node phụ thuộc (E08-020), fail-closed:

    - Node BẮT BUỘC ``BLOCKED`` (khóa-Windows/thiếu Linux API) → ``BLOCKED``.
    - Node bắt buộc ``DOWN``/``MISSING``/``UNKNOWN`` (vd DB mất) → ``PARTIAL``
      (mở được GUI nhưng CHƯA dùng được; không cho sửa dữ liệu thật).
    - Tất cả node bắt buộc ``OK`` → ``TOOL_OK_PENDING_BUSINESS`` (kỹ thuật ổn, VẪN
      cần nghiệp vụ xác nhận — chưa tự gắn "dùng được").
    - Không có node bắt buộc nào → ``UNKNOWN``.
    """

    required = [n for n in nodes if n.required]
    if not required:
        return WorkflowVerdict.UNKNOWN
    if any(n.state is DepState.BLOCKED for n in required):
        return WorkflowVerdict.BLOCKED
    if any(n.state in (DepState.DOWN, DepState.MISSING, DepState.UNKNOWN) for n in required):
        return WorkflowVerdict.PARTIAL
    return WorkflowVerdict.TOOL_OK_PENDING_BUSINESS


def is_workflow_complete(
    verdict: WorkflowVerdict,
    *,
    business_confirmed: bool,
    evidence_ids: Iterable[str] = (),
) -> bool:
    """Workflow đã HOÀN THÀNH chưa (E08-031). True CHỈ khi kỹ-thuật-ổn
    (``TOOL_OK_PENDING_BUSINESS``) + nghiệp-vụ-duyệt + có ≥1 bằng chứng non-blank."""

    if verdict is not WorkflowVerdict.TOOL_OK_PENDING_BUSINESS:
        return False
    if not business_confirmed:
        return False
    return any(e.strip() for e in evidence_ids)


def tool_success_is_workflow_success(
    tool_success: bool,
    *,
    business_confirmed: bool,
    evidence_ids: Iterable[str] = (),
) -> bool:
    """``tool_success`` KHÔNG tự thành ``user_workflow_success`` (E08-031, test A02):
    driver install success nhưng máy không in được → vẫn chưa hoàn thành; cần nghiệp
    vụ + bằng chứng."""

    if not tool_success:
        return False
    return bool(business_confirmed) and any(e.strip() for e in evidence_ids)
