"""Provenance + GATE trạng thái tương thích (COMP-048/049).

KHÔNG dựng lại gate kỹ thuật: tái dùng ``namios_eco.status.derive_published_status``
(ECO-003 — "workflow_verified chỉ khi đủ evidence nộp/nhận"). Module này:

1. Mô hình bằng chứng có provenance đầy đủ (``CompatEvidence`` ở ``_types``)
   + validator (COMP-049): đủ trường, hash đúng dạng, evidence production phải
   có người vai-trò-nghiệp-vụ xác nhận.
2. Quy đổi danh sách evidence → 7 ``WorkflowStep`` để đưa vào gate kỹ thuật.
3. ``evaluate_route_status`` = CHỒNG thêm 3 tầng trung thực lên gate kỹ thuật:
   thu hồi (revoked) · nghiệp vụ chưa/không duyệt (COMP-052: pass nghiệp vụ là
   điều kiện cần) · quá hạn tái kiểm (COMP-054: needs_retest). Không tầng nào
   NÂNG trạng thái — chỉ HẠ xuống khi chưa đủ điều kiện. Metadata một mình
   KHÔNG bao giờ tạo ra ``workflow_verified``.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import date, datetime, time

from namios_compat import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_compat._types import (
    BusinessStatus,
    CompatEvidence,
    EvidenceEnvironment,
)
from namios_core.validation import ValidationError
from namios_eco.status import (
    PublishedStatus,
    PublishedStatusResult,
    derive_published_status,
)
from namios_eco.workflow import (
    WORKFLOW_STEP_ORDER,
    StepOutcome,
    WorkflowStep,
    WorkflowStepName,
)
from namios_i18n import Lang, t

__all__ = [
    "compute_fixture_hash",
    "FIXTURE_HASH_RE",
    "validate_evidence",
    "evidence_to_steps",
    "evaluate_route_status",
    "REVIEWER_REQUIRED_STEPS",
]

#: Dạng hash fixture bắt buộc: ``sha256:<64 hex>`` (COMP-049 provenance).
FIXTURE_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

#: Nấc mà bằng chứng ở môi trường production PHẢI có người vai-trò-nghiệp-vụ
#: xác nhận (COMP-049). Nộp/xuất và kiểm kết quả là nơi dữ liệu nghiệp vụ thật
#: xuất hiện — không ai ký thay cho nghiệp vụ.
REVIEWER_REQUIRED_STEPS: frozenset[WorkflowStepName] = frozenset(
    {WorkflowStepName.SUBMIT_OR_EXPORT, WorkflowStepName.VERIFY_RESULT}
)

_REQUIRED_STR_FIELDS = (
    "evidence_id",
    "workflow_id",
    "test_case_id",
    "fixture_hash",
    "expected",
    "actual",
    "timestamp",
    "os_version",
    "app_version",
    "runner_version",
)


def compute_fixture_hash(data: bytes) -> str:
    """Băm nội dung fixture → chuỗi provenance ``sha256:<hex>`` (COMP-049)."""

    return "sha256:" + hashlib.sha256(data).hexdigest()


def _parse_iso(value: str) -> datetime | None:
    """Parse ngày/giờ ISO-8601 thành ``datetime`` (ngày → nửa đêm). Trả
    ``None`` nếu không hợp lệ.

    QA COMPAT-ADV-002: so HẠN tái kiểm phải so như NGÀY THẬT, không so chuỗi
    từ-điển (``'2026-10-15' > '2026-2-1'`` sai). Zero-pad bắt buộc (schema đã
    chặn ở tầng nạp; đây là phòng thủ tầng gate)."""

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(value), time.min)
        except ValueError:
            return None


def validate_evidence(ev: CompatEvidence) -> list[ValidationError]:
    """Kiểm một bằng chứng (COMP-049): đủ trường, hash đúng dạng, evidence
    production ở nấc nghiệp vụ phải có người xác nhận.

    KHÔNG tự phán trạng thái workflow ở đây — đó là việc của
    ``evaluate_route_status`` sau khi gộp đủ 7 nấc."""

    errors: list[ValidationError] = []
    for name in _REQUIRED_STR_FIELDS:
        value = getattr(ev, name)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                ValidationError(
                    code="E_INPUT_SCHEMA",
                    path=name,
                    message_vi=t("compat.evidence.error.missing_field", lang=Lang.VI, field=name),
                )
            )
    if ev.fixture_hash and not FIXTURE_HASH_RE.match(ev.fixture_hash):
        errors.append(
            ValidationError(
                code="E_INPUT_SCHEMA",
                path="fixture_hash",
                message_vi=t(
                    "compat.evidence.error.hash_format", lang=Lang.VI, value=ev.fixture_hash
                ),
            )
        )
    if (
        ev.environment == EvidenceEnvironment.PRODUCTION
        and ev.step in REVIEWER_REQUIRED_STEPS
        and ev.outcome == StepOutcome.PASS
        and not (ev.confirmed_by_role or "").strip()
    ):
        errors.append(
            ValidationError(
                code="E_EVIDENCE_MISSING",
                path="confirmed_by_role",
                message_vi=t(
                    "compat.evidence.error.production_needs_reviewer",
                    lang=Lang.VI,
                    step=ev.step.value,
                ),
            )
        )
    return errors


def evidence_to_steps(
    workflow_id: str, evidence: Sequence[CompatEvidence]
) -> tuple[WorkflowStep, ...]:
    """Quy đổi các bằng chứng của một workflow → đúng 7 ``WorkflowStep`` theo
    thứ tự ECO-001, để đưa vào gate kỹ thuật ``derive_published_status``.

    Nấc không có bằng chứng → ``NOT_RUN`` (KHÔNG giả định pass). Nấc có nhiều
    bằng chứng → lấy bản xấu nhất (FAIL > BLOCKED > NOT_RUN > NOT_APPLICABLE >
    PASS) để không che lỗi; ``evidence_ref`` chỉ gắn khi có một bằng chứng
    PASS thật (gate kỹ thuật yêu cầu ``evidence_ref`` cho verify/submit)."""

    severity = {
        StepOutcome.FAIL: 5,
        StepOutcome.BLOCKED: 4,
        StepOutcome.NOT_RUN: 3,
        StepOutcome.NOT_APPLICABLE: 2,
        StepOutcome.PASS: 1,
    }
    by_step: dict[WorkflowStepName, list[CompatEvidence]] = {}
    for ev in evidence:
        if ev.workflow_id != workflow_id:
            continue
        by_step.setdefault(ev.step, []).append(ev)

    steps: list[WorkflowStep] = []
    for name in WORKFLOW_STEP_ORDER:
        evs = by_step.get(name, [])
        if not evs:
            steps.append(WorkflowStep(name=name, outcome=StepOutcome.NOT_RUN))
            continue
        worst = max(evs, key=lambda e: severity.get(e.outcome, 3))
        evidence_ref: str | None = None
        if worst.outcome == StepOutcome.PASS:
            # Gắn ref của một bằng chứng PASS (ưu tiên bản đầu tiên) — gate kỹ
            # thuật dùng sự hiện diện của evidence_ref ở verify/submit.
            passing = next((e for e in evs if e.outcome == StepOutcome.PASS), worst)
            evidence_ref = passing.evidence_id
        steps.append(WorkflowStep(name=name, outcome=worst.outcome, evidence_ref=evidence_ref))
    return tuple(steps)


def evaluate_route_status(
    steps: tuple[WorkflowStep, ...],
    *,
    business_status: BusinessStatus,
    revoked: bool = False,
    recertify_by: str | None = None,
    now: str | None = None,
) -> PublishedStatusResult:
    """GATE tương thích tổng hợp (COMP-048/052/054).

    Thứ tự: thu hồi (cao nhất) → gate kỹ thuật ECO-003 → chồng điều kiện
    nghiệp vụ + hạn tái kiểm. KHÔNG tầng nào nâng trạng thái; chỉ HẠ khi chưa
    đủ. ``recertify_by``/``now`` là chuỗi ISO 8601 (so sánh từ điển hợp lệ cho
    cùng định dạng)."""

    if revoked:
        return PublishedStatusResult(
            PublishedStatus.REVOKED,
            (t("compat.evidence.reason.revoked", lang=Lang.VI),),
        )

    base = derive_published_status(steps)
    if base.status != PublishedStatus.WORKFLOW_VERIFIED:
        return base

    # Kỹ thuật đã workflow_verified — giờ chồng nghiệp vụ + hạn tái kiểm.
    if business_status == BusinessStatus.REJECTED:
        return PublishedStatusResult(
            PublishedStatus.PARTIAL_WORKFLOW,
            (t("compat.evidence.reason.business_rejected", lang=Lang.VI),),
        )
    if business_status != BusinessStatus.APPROVED:
        return PublishedStatusResult(
            PublishedStatus.PARTIAL_WORKFLOW,
            (t("compat.evidence.reason.business_unreviewed", lang=Lang.VI),),
        )
    if recertify_by:
        rc = _parse_iso(recertify_by)
        # recertify_by không parse được → KHÔNG xác nhận được độ tươi → hạ.
        if rc is None:
            return PublishedStatusResult(
                PublishedStatus.PARTIAL_WORKFLOW,
                (
                    t(
                        "compat.evidence.reason.cert_expired",
                        lang=Lang.VI,
                        recertify_by=recertify_by,
                    ),
                ),
            )
        if now:
            nw = _parse_iso(now)
            if nw is None or nw > rc:
                return PublishedStatusResult(
                    PublishedStatus.PARTIAL_WORKFLOW,
                    (
                        t(
                            "compat.evidence.reason.cert_expired",
                            lang=Lang.VI,
                            recertify_by=recertify_by,
                        ),
                    ),
                )
    return base
