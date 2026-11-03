"""Task Plan hữu hình (SAI-002, Phụ lục 04).

``build_task`` dựng một ``Task`` + danh sách ``PlanStep`` DỰ KIẾN từ một
``IntentResult`` đã có (xem ``namios_smartai.intent``). Mọi bước luôn bắt
đầu ở ``TaskStatus.PROPOSED`` — hàm này KHÔNG tự thực thi, không gọi tool,
không đổi trạng thái sang bất kỳ gì ngụ ý đã làm (``APPLYING``/``COMPLETED``
chỉ do orchestrator cập nhật từ ``ToolResult`` thật, xem
``namios_smartai.state_machine``).

Bất biến an toàn (nghiệm thu T01): khi ``intent.unknowns`` còn phần tử, kế
hoạch CHỈ gồm một bước inspect/explain (``R0``) — không có bước cài/áp dụng
nào được đưa vào, dù intent là gì. "Cài MISA" thiếu phiên bản/license →
chỉ hỏi lại, không tự tải/cài.
"""

from __future__ import annotations

from collections.abc import Callable

from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import IntentResult, PlanStep, RiskTier, Task, TaskStatus

__all__ = ["build_task"]


def _step(
    step_id: str,
    tool: str,
    risk: RiskTier,
    expected_vi: str,
    *,
    consent_required: bool = False,
) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        tool=tool,
        risk=risk,
        expected_vi=expected_vi,
        status=TaskStatus.PROPOSED,
        consent_required=consent_required,
    )


def _explain_step(expected_vi: str) -> PlanStep:
    """Bước duy nhất khi chưa đủ thông tin/chưa hiểu rõ — chỉ tra cứu/giải
    thích (``R0``, không consent, không ghi/cài gì)."""

    return _step("explain", "inspect_app", RiskTier.R0, expected_vi)


def _plan_install_app(intent: IntentResult) -> tuple[PlanStep, ...]:
    """``install_app`` đủ thông tin (có version + đã xác nhận license, tức
    ``unknowns`` rỗng): preflight/check_source (R0) → capsule/cài thử (R2,
    cần consent) → chạy thử/so khớp (R1)."""

    return (
        _step("preflight", "preflight", RiskTier.R0, "Kiểm tra môi trường trước khi cài đặt."),
        _step(
            "check_source",
            "check_source",
            RiskTier.R0,
            "Kiểm tra nguồn bộ cài có hợp lệ/chính thức.",
        ),
        _step(
            "create_capsule",
            "create_capsule",
            RiskTier.R2,
            "Tạo capsule cách ly để cài thử — cần sự chấp thuận phạm vi.",
            consent_required=True,
        ),
        _step(
            "install_test",
            "install_test",
            RiskTier.R2,
            "Cài thử ứng dụng trong capsule đã cấp quyền — cần sự chấp thuận phạm vi.",
            consent_required=True,
        ),
        _step("run_test", "run_test", RiskTier.R1, "Chạy thử ứng dụng sau khi cài."),
        _step(
            "compare_artifacts",
            "compare_artifacts",
            RiskTier.R1,
            "So sánh kết quả với kỳ vọng để xác nhận cài đặt đúng.",
        ),
    )


def _plan_submit_filing(intent: IntentResult) -> tuple[PlanStep, ...]:
    """``submit_filing`` đủ thông tin (đã có người nộp + số tiền tường
    minh): preflight (R0) → thử nháp/dry-run (R1) → nộp thật (R4, PHẢI có
    xác nhận GIAO DỊCH cụ thể — policy/orchestrator gate, không phải hàm
    này). Hàm này chỉ LẬP KẾ HOẠCH, không đánh dấu sẵn sàng/đã nộp."""

    return (
        _step("preflight", "preflight", RiskTier.R0, "Kiểm tra môi trường trước khi nộp tờ khai."),
        _step(
            "run_test",
            "run_test",
            RiskTier.R1,
            "Chạy thử ở dạng nháp/dry-run (draft) — CHƯA nộp thật.",
        ),
        _step(
            "submit",
            "submit_filing",
            RiskTier.R4,
            (
                "Nộp tờ khai — bắt buộc xác nhận GIAO DỊCH cụ thể (đúng người nộp + "
                "đúng số tiền) trước khi thực hiện; một câu 'cứ làm đi' không thay "
                "thế được."
            ),
            consent_required=True,
        ),
    )


def _plan_open_or_print(intent: IntentResult) -> tuple[PlanStep, ...]:
    verb_vi = "mở ứng dụng" if intent.intent == "open_app" else "in tài liệu"
    return (
        _step("preflight", "preflight", RiskTier.R0, f"Kiểm tra môi trường trước khi {verb_vi}."),
        _step("run_test", "run_test", RiskTier.R1, f"Thử {verb_vi} để xác nhận hoạt động."),
    )


#: Bộ dựng kế hoạch theo từng loại intent ĐÃ ĐỦ THÔNG TIN (``unknowns`` rỗng
#: và ``intent`` khác ``"unknown"``). Intent lạ không có trong bảng này rơi
#: về nhánh "chưa hiểu rõ" (fail-closed) trong ``build_task``.
_PLAN_BUILDERS: dict[str, Callable[[IntentResult], tuple[PlanStep, ...]]] = {
    "install_app": _plan_install_app,
    "submit_filing": _plan_submit_filing,
    "open_app": _plan_open_or_print,
    "print_document": _plan_open_or_print,
}


def _awaiting_input_task(
    *, task_id: str, intent: IntentResult, expected_vi: str, blockers: tuple[str, ...] = ()
) -> Task:
    return Task(
        task_id=task_id,
        intent=intent.intent,
        status=TaskStatus.AWAITING_INPUT,
        app_id=intent.target_app,
        steps=(_explain_step(expected_vi),),
        blockers=blockers,
        next_action=expected_vi,
    )


def build_task(intent: IntentResult, *, task_id: str) -> Task:
    """Dựng ``Task`` + kế hoạch hữu hình (SAI-002) từ ``intent``.

    KHÔNG tự thực thi gì — chỉ mô tả, mọi ``PlanStep`` bắt đầu ``PROPOSED``.

    - ``intent.unknowns`` còn phần tử → ``AWAITING_INPUT``, kế hoạch CHỈ có
      một bước inspect/explain (``R0``) nêu rõ cần hỏi gì; KHÔNG có bước
      cài/áp dụng nào, bất kể ``intent.intent`` là gì (SAI-001 T01).
    - ``intent.intent == "unknown"`` (hiểu nhầm/không chắc) → cũng
      ``AWAITING_INPUT`` với một bước giải thích, dùng thông báo mức chắc
      chắn thấp.
    - Ngược lại (đủ thông tin, intent nhận diện được) → kế hoạch theo loại
      intent, ``status = PROPOSED``.
    """

    if intent.unknowns:
        expected_vi = t(
            "sai.intent.need_info",
            lang=Lang.VI,
            unknowns=", ".join(intent.unknowns),
        )
        return _awaiting_input_task(
            task_id=task_id,
            intent=intent,
            expected_vi=expected_vi,
            blockers=intent.unknowns,
        )

    if intent.intent == "unknown":
        expected_vi = t("sai.intent.low_confidence", lang=Lang.VI)
        return _awaiting_input_task(task_id=task_id, intent=intent, expected_vi=expected_vi)

    builder = _PLAN_BUILDERS.get(intent.intent)
    if builder is None:
        # Intent không nằm trong hợp đồng đã biết — fail-closed: hỏi lại
        # thay vì tự đoán một kế hoạch cho một intent lạ.
        expected_vi = t("sai.intent.low_confidence", lang=Lang.VI)
        return _awaiting_input_task(task_id=task_id, intent=intent, expected_vi=expected_vi)

    return Task(
        task_id=task_id,
        intent=intent.intent,
        status=TaskStatus.PROPOSED,
        app_id=intent.target_app,
        steps=builder(intent),
    )
