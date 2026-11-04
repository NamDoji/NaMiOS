"""Human Feedback (SAI-029).

Người dùng đánh dấu "đã giải quyết/chưa giải quyết" + mô tả lỗi; IT và chuyên
gia nghiệp vụ đánh giá RIÊNG. Phản hồi KHÔNG tự trở thành chứng nhận — đầu ra
duy nhất có tác dụng là GỢI Ý TEST CASE. Mức ``workflow_verified`` chỉ do lab +
promotion gate (SAI-012/030/031) quyết, không do một lượt "thành công".

Bất biến cốt lõi (nghiệm thu SAI-029): một lượt phản hồi "đã giải quyết" KHÔNG
nâng được trạng thái ``workflow_verified``.
"""

from __future__ import annotations

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import (
    Feedback,
    FeedbackVerdict,
    ReporterRole,
    TestCaseSuggestion,
)

__all__ = ["FeedbackLedger", "can_certify_from_feedback"]


def can_certify_from_feedback(feedbacks: object = None) -> bool:
    """LUÔN ``False`` (SAI-029). Phản hồi con người — dù bao nhiêu lượt "đã giải
    quyết" — KHÔNG phải evidence/chứng nhận và KHÔNG nâng ``workflow_verified``.
    Tham số nhận vào chỉ để gọi thuận; kết quả không phụ thuộc nội dung."""

    return False


class FeedbackLedger:
    """Sổ phản hồi con người. Lưu đánh dấu + mô tả theo vai trò (người dùng/IT/
    nghiệp vụ đánh giá RIÊNG); sinh gợi ý test case; KHÔNG bao giờ tự chứng nhận."""

    def __init__(self) -> None:
        self._items: list[Feedback] = []

    def submit(self, feedback: Feedback) -> None:
        self._items.append(feedback)

    def all(self) -> tuple[Feedback, ...]:
        return tuple(self._items)

    def for_workflow(self, workflow_id: str) -> tuple[Feedback, ...]:
        return tuple(f for f in self._items if f.workflow_id == workflow_id)

    def verdicts_by_role(self, workflow_id: str) -> dict[ReporterRole, tuple[FeedbackVerdict, ...]]:
        """Đánh dấu tách THEO VAI TRÒ (SAI-029): phản hồi 'đã giải quyết' của
        người dùng cuối KHÔNG gộp chung / không thay cho thẩm định IT/nghiệp vụ."""

        out: dict[ReporterRole, list[FeedbackVerdict]] = {}
        for f in self.for_workflow(workflow_id):
            out.setdefault(f.role, []).append(f.verdict)
        return {role: tuple(v) for role, v in out.items()}

    def would_promote_to_workflow_verified(self, workflow_id: str) -> bool:
        """LUÔN ``False`` (SAI-029 nghiệm thu): không lượng phản hồi nào — kể cả
        toàn bộ 'đã giải quyết' từ mọi vai trò — nâng được ``workflow_verified``.
        Chỉ lab/evidence + promotion gate mới nâng."""

        return False

    def suggested_test_cases(
        self, workflow_id: str | None = None
    ) -> tuple[TestCaseSuggestion, ...]:
        """Sinh gợi ý test case TỪ phản hồi — đầu ra DUY NHẤT có tác dụng.

        - ``UNRESOLVED`` (có mô tả) → gợi ý TÁI HIỆN lỗi.
        - ``RESOLVED`` (có mô tả) → gợi ý HỒI QUY để xác nhận fix thực sự ổn.
        - ``UNCLEAR`` / không mô tả → bỏ qua (không bịa test case).
        """

        items = self._items if workflow_id is None else self.for_workflow(workflow_id)
        out: list[TestCaseSuggestion] = []
        for f in items:
            desc = (f.description_vi or "").strip()
            if not desc:
                continue
            if f.verdict == FeedbackVerdict.UNRESOLVED:
                kind, key = "repro", "sai.feedback.suggest.repro"
            elif f.verdict == FeedbackVerdict.RESOLVED:
                kind, key = "regression", "sai.feedback.suggest.regression"
            else:  # UNCLEAR → không đủ căn cứ
                continue
            out.append(
                TestCaseSuggestion(
                    workflow_id=f.workflow_id,
                    app_version=f.app_version,
                    origin_feedback_id=f.feedback_id,
                    kind=kind,
                    summary_vi=t(
                        key,
                        lang=Lang.VI,
                        summary=desc,
                        workflow_id=f.workflow_id,
                        version=f.app_version,
                    ),
                )
            )
        return tuple(out)
