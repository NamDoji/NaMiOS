"""Workflow verdict + evidence (N10-043) — "đã xong" chỉ khi có bằng chứng hợp lệ.

Exit-code=0/CUPS "completed" một mình KHÔNG đủ: job spool OK nhưng giấy trắng
vẫn phải kết luận ``failed``/``partial`` (N10-043 nghiệm thu). TÁI DÙNG mốc
TRUNG THỰC ``namios_pra.progress`` (``print_received``/``sign_submitted_done``)
làm ngưỡng "đủ mạnh" cho print/sign stage, và ``namios_e08.depgraph`` cho kết
luận phụ thuộc kỹ thuật tổng (mở GUI ≠ dùng được: DB mất → partial, cổng khóa
→ blocked). TÁI DÙNG ``namios_pra.doctor.next_after_attempts`` để quyết định
khi nào DỪNG thử lại một workflow liên tục fail (N10-060 "điểm dừng").
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Literal

from namios_e08 import DepNode, WorkflowVerdict
from namios_e08 import workflow_verdict as e08_workflow_verdict
from namios_i18n import Lang, t
from namios_mig import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_mig._types import EvidenceRecord, WorkflowTest, WorkflowTestStatus
from namios_pra import Diagnosis, PrintStage, SignSubmitStage
from namios_pra.doctor import next_after_attempts
from namios_pra.progress import print_received, sign_submitted_done

__all__ = [
    "EvidenceOutcome",
    "evidence_outcome",
    "evaluate_workflow",
    "assess_workflow",
    "terminal_diagnosis_if_exhausted",
]

EvidenceOutcome = Literal["positive", "negative", "insufficient"]

#: Giai đoạn print/sign coi là THẤT BẠI rõ ràng (không phải "chưa đủ bằng
#: chứng" mà là đã có bằng chứng cho THẤT BẠI) — N10-043.
_PRINT_FAILURE_STAGES: frozenset[PrintStage] = frozenset({PrintStage.FAILED, PrintStage.CANCELLED})
_SIGN_FAILURE_STAGES: frozenset[SignSubmitStage] = frozenset({SignSubmitStage.FAILED})


def evidence_outcome(evidence: EvidenceRecord) -> EvidenceOutcome:
    """Phân loại MỘT bằng chứng thành ``positive``/``negative``/``insufficient``
    (N10-043). ``independent_check_ok=False`` (vd người xem thấy giấy trắng)
    là ``negative`` DÙ pipeline kỹ thuật (print_stage) báo xong. CUPS
    ``MACHINE_DONE``/exit-code một mình chỉ là ``insufficient`` — TÁI DÙNG
    ``namios_pra.progress.print_received``/``sign_submitted_done`` làm ngưỡng
    "đủ mạnh" (chỉ ``USER_CONFIRMED``/``RECEIPT_VERIFIED`` mới ``positive``)."""

    if evidence.independent_check_ok is False:
        return "negative"
    if evidence.print_stage in _PRINT_FAILURE_STAGES:
        return "negative"
    if evidence.sign_stage in _SIGN_FAILURE_STAGES:
        return "negative"
    if evidence.independent_check_ok is True:
        return "positive"
    if evidence.print_stage is not None and print_received(evidence.print_stage):
        return "positive"
    if evidence.sign_stage is not None and sign_submitted_done(evidence.sign_stage):
        return "positive"
    return "insufficient"


def evaluate_workflow(
    test: WorkflowTest, evidence: Iterable[EvidenceRecord], *, tested_at: str | None = None
) -> WorkflowTest:
    """Tính lại ``status`` của một ``WorkflowTest`` TỪ evidence thật (N10-043).

    - Không có evidence khớp ``workflow_id`` → ``NOT_TESTED``.
    - Có ÍT NHẤT một evidence ``negative`` → ``FAILED`` (bằng chứng cho thấy
      thất bại thắng mọi bằng chứng dương/yếu khác — fail-closed).
    - Không có ``negative`` nhưng có evidence ``positive`` → ``PASSED``.
    - Chỉ có evidence ``insufficient`` (exit-code/spool/machine_done một
      mình) → ``PARTIAL`` — KHÔNG được ``PASSED`` (bất biến cốt lõi N10-043).
    """

    matched = tuple(e for e in evidence if e.workflow_id == test.workflow_id)
    if not matched:
        return replace(test, status=WorkflowTestStatus.NOT_TESTED, evidence_ids=())

    outcomes = [evidence_outcome(e) for e in matched]
    ids = tuple(e.evidence_id for e in matched)

    if "negative" in outcomes:
        return replace(
            test,
            status=WorkflowTestStatus.FAILED,
            evidence_ids=ids,
            limitations_vi=(
                *test.limitations_vi,
                t("mig.workflow.evidence_negative", lang=Lang.VI),
            ),
        )
    if "positive" in outcomes:
        return replace(
            test,
            status=WorkflowTestStatus.PASSED,
            evidence_ids=ids,
            tested_at=tested_at or test.tested_at,
        )
    return replace(
        test,
        status=WorkflowTestStatus.PARTIAL,
        evidence_ids=ids,
        limitations_vi=(
            *test.limitations_vi,
            t("mig.workflow.evidence_insufficient", lang=Lang.VI),
        ),
    )


def assess_workflow(
    test: WorkflowTest,
    dep_nodes: Iterable[DepNode],
    evidence: Iterable[EvidenceRecord],
    *,
    tested_at: str | None = None,
) -> WorkflowTest:
    """Kết luận workflow TỔNG HỢP: kỹ thuật (dependency graph) + bằng chứng
    (N10-020/043). TÁI DÙNG ``namios_e08.depgraph.workflow_verdict`` cho trục
    kỹ thuật — kỹ thuật chưa ổn (``BLOCKED``/``PARTIAL``) thì KHÔNG được bằng
    chứng evidence nâng lên ``PASSED`` (chỉ có thể hạ, không bao giờ nâng quá
    mức kỹ thuật thật — cùng tinh thần ``namios_sys.certification``)."""

    verdict = e08_workflow_verdict(tuple(dep_nodes))

    if verdict is WorkflowVerdict.BLOCKED:
        return replace(
            test,
            status=WorkflowTestStatus.FAILED,
            evidence_ids=(),
            limitations_vi=(*test.limitations_vi, t("mig.workflow.dep_blocked", lang=Lang.VI)),
        )

    evaluated = evaluate_workflow(test, evidence, tested_at=tested_at)

    if verdict is WorkflowVerdict.PARTIAL and evaluated.status is WorkflowTestStatus.PASSED:
        # Kỹ thuật chưa ổn (vd DB mất) dù evidence trông có vẻ đủ → hạ xuống
        # PARTIAL (fail-closed, không nâng vượt mức kỹ thuật thật).
        return replace(
            evaluated,
            status=WorkflowTestStatus.PARTIAL,
            limitations_vi=(*evaluated.limitations_vi, t("mig.workflow.dep_partial", lang=Lang.VI)),
        )
    if verdict is WorkflowVerdict.UNKNOWN and evaluated.status is WorkflowTestStatus.PASSED:
        # Không có node bắt buộc nào để biết kỹ thuật ổn chưa → không tự nhận
        # PASSED chỉ từ evidence; hạ về PARTIAL (thiếu bằng chứng kỹ thuật).
        return replace(
            evaluated,
            status=WorkflowTestStatus.PARTIAL,
            limitations_vi=(*evaluated.limitations_vi, t("mig.workflow.dep_unknown", lang=Lang.VI)),
        )
    return evaluated


def terminal_diagnosis_if_exhausted(*, failed_attempts: int, max_attempts: int) -> Diagnosis | None:
    """Đã thử lại một workflow liên tục fail đến mức phải DỪNG chưa (N10-060).
    TÁI DÙNG ``namios_pra.doctor.next_after_attempts`` trực tiếp — không dựng
    lại ngưỡng dừng thứ hai. Trả ``None`` nếu còn được thử tiếp."""

    return next_after_attempts(failed_count=failed_attempts, max_attempts=max_attempts)
