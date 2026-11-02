"""Tầng 2 — gate ngữ nghĩa cho evidence report (§11.2/§18.3): "không
``task_verified`` khi thiếu evidence/QA approval". Xem M1-INTERFACES.md §7.7.

Quy tắc (FACT §11.2/§18.3):
  - ``decision == "revoked"`` → ``CompatStatus.REVOKED`` tuyệt đối.
  - Bất kỳ test ``required=true`` có ``result`` khác ``"pass"``
    (``fail``/``not_run``/``skipped``/``blocked_external_dependency``) →
    KHÔNG được ``task_verified`` (tối đa ``blocked`` — đúng định nghĩa
    ``CompatStatus.BLOCKED`` "tác vụ bắt buộc không đạt hoặc thiếu phụ
    thuộc ngoài", M1-INTERFACES §5).
  - Mọi test ``required=true`` đều ``pass`` NHƯNG ``qa_reviewer is None``
    → vẫn KHÔNG ``task_verified`` (``E_EVIDENCE_MISSING``); evidence có
    thật nên ở mức ``experimental`` (chạy được, còn thiếu QA độc lập).
  - Mọi test required pass + có ``qa_reviewer`` → ``task_verified``.
  - Không có test ``required=true`` nào trong report → không đủ bằng
    chứng để chứng nhận tác vụ bắt buộc → ``untested`` (không thể suy ra
    "đã làm xong tác vụ bắt buộc" từ một report không khai báo tác vụ nào
    là bắt buộc).

``skipped`` KHÔNG BAO GIỜ được coi như ``pass`` (FACT §18.1) — xử lý giống
``not_run``/``blocked_external_dependency`` ở trên.
"""

from __future__ import annotations

from namios_core.compat import CompatStatus
from namios_core.evidence_types import EvidenceReport, EvidenceTest, GateResult

__all__ = ["compute_allowed_status"]

_NON_PASS_RESULTS = frozenset({"fail", "not_run", "skipped", "blocked_external_dependency"})


def _required_tests(rep: EvidenceReport) -> tuple[EvidenceTest, ...]:
    return tuple(t for t in rep.tests if t.required)


def compute_allowed_status(rep: EvidenceReport) -> GateResult:
    reasons: list[str] = []

    if rep.decision == "revoked":
        return GateResult(
            allowed_status=CompatStatus.REVOKED,
            reasons_vi=(
                f"Report '{rep.report_id}' khai báo decision='revoked' — thu hồi tuyệt đối.",
            ),
        )

    required = _required_tests(rep)

    if not required:
        return GateResult(
            allowed_status=CompatStatus.UNTESTED,
            reasons_vi=(
                "Report không khai báo test nào là required=true — "
                "không đủ bằng chứng để đánh giá tác vụ bắt buộc.",
            ),
        )

    failing_required = tuple(t for t in required if t.result in _NON_PASS_RESULTS)
    if failing_required:
        for t in failing_required:
            reasons.append(
                f"Test bắt buộc '{t.test_id}' có result='{t.result}' (không phải 'pass') "
                "— chưa đạt tác vụ bắt buộc."
            )
        return GateResult(allowed_status=CompatStatus.BLOCKED, reasons_vi=tuple(reasons))

    # Tới đây: mọi required test đều result == "pass".
    if rep.qa_reviewer is None or not rep.qa_reviewer.strip():
        reasons.append(
            "Mọi test bắt buộc đã pass nhưng qa_reviewer rỗng/chỉ-khoảng-trắng/null — "
            "thiếu phê duyệt QA độc lập thật, KHÔNG đủ điều kiện task_verified "
            "(E_EVIDENCE_MISSING)."
        )
        return GateResult(allowed_status=CompatStatus.EXPERIMENTAL, reasons_vi=tuple(reasons))

    reasons.append(
        f"Tất cả {len(required)} test bắt buộc đã pass và có qa_reviewer='{rep.qa_reviewer}' "
        "— đủ điều kiện task_verified."
    )
    return GateResult(allowed_status=CompatStatus.TASK_VERIFIED, reasons_vi=tuple(reasons))
