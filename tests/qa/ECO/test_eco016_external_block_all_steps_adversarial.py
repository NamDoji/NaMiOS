"""ECO-016/ECO-003 — GATE đối kháng: MỌI nấc trong 7 nấc, khi bị chặn vì phụ
thuộc ngoài (``StepOutcome.BLOCKED`` — "thiếu sandbox/quyền/token"), phải
được ``derive_published_status`` suy ra ``blocked_external_dependency``
(KHÔNG BAO GIỜ một trạng thái "usable" như ``partial_workflow``).

Dev đã có test cho nấc bị blocked ở ``install_or_open``..``verify_result``
(``tests/unit/eco/test_status_gate.py::test_blocked_external_dependency_from_submit_step``).
Bộ test này dò ĐỘC LẬP tất cả 7 vị trí (bao gồm ``discover``/``acquire`` —
hai vị trí dev CHƯA có test) vì đây là vị trí quan trọng nhất trong thực tế:
mọi entry `catalog/services/*.json` hiện có ghi rõ trong `source_check`
rằng host build KHÔNG kết nối được tới domain .gov.vn (ECONNREFUSED/
ECONNRESET) — tức là tình huống thật sẽ xảy ra chính xác ở nấc `discover`
hoặc `acquire`, không phải ở các nấc sau."""

from __future__ import annotations

import pytest
from tests.qa.ECO._qa_fixtures import steps_single_outcome

from namios_eco.status import PublishedStatus, derive_published_status, is_usable
from namios_eco.workflow import StepOutcome, WorkflowStepName

_ALL_SEVEN_STEPS: tuple[WorkflowStepName, ...] = (
    WorkflowStepName.DISCOVER,
    WorkflowStepName.ACQUIRE,
    WorkflowStepName.INSTALL_OR_OPEN,
    WorkflowStepName.AUTHENTICATE,
    WorkflowStepName.EXECUTE,
    WorkflowStepName.SUBMIT_OR_EXPORT,
    WorkflowStepName.VERIFY_RESULT,
)


@pytest.mark.parametrize("blocked_step", _ALL_SEVEN_STEPS, ids=lambda s: s.value)
def test_any_step_blocked_by_external_dependency_must_be_blocked_status(
    blocked_step: WorkflowStepName,
) -> None:
    """DEFECT (cho ``discover``/``acquire``): ``derive_published_status``
    chỉ kiểm nhánh "blocked_external_dependency" cho chuỗi
    ``(install_or_open, authenticate, execute, submit_or_export,
    verify_result)`` — KHÔNG đưa ``discover``/``acquire`` vào chuỗi đó (xem
    ``src/namios_eco/status.py::derive_published_status``, biến ``chain``).

    Khi ``discover`` hoặc ``acquire`` bị ``BLOCKED`` (ví dụ: host build
    không có kết nối ra ngoài tới domain .gov.vn — đúng tình huống
    ``ECO-016`` thật đang xảy ra với mọi entry catalog hiện có), hàm trả về
    ``partial_workflow`` thay vì ``blocked_external_dependency``.

    Nếu dòng dưới FAIL cho ``blocked_step in (discover, acquire)`` — đó LÀ
    bằng chứng defect (xem ``qa/evidence-index/ECO/defects.md``), KHÔNG phải
    test sai. Với 5 nấc còn lại (``install_or_open``..``verify_result``),
    dòng này PHẢI pass (hành vi đã đúng, dev đã có test riêng)."""

    steps = steps_single_outcome(
        blocked_step,
        StepOutcome.BLOCKED,
        note_vi=(
            f"Nấc '{blocked_step.value}' dừng vì phụ thuộc ngoài (ECO-016) — "
            "ví dụ không có kết nối ra ngoài / không có sandbox / thiếu quyền."
        ),
    )
    result = derive_published_status(steps)

    assert result.status == PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY, (
        f"Nấc '{blocked_step.value}' bị BLOCKED (phụ thuộc ngoài) nhưng "
        f"derive_published_status() trả '{result.status.value}' — "
        f"reasons={result.reasons_vi!r}. Kỳ vọng 'blocked_external_dependency' "
        "cho MỌI nấc bị blocked, không chỉ các nấc sau install_or_open."
    )


@pytest.mark.parametrize(
    "blocked_step", (WorkflowStepName.DISCOVER, WorkflowStepName.ACQUIRE), ids=lambda s: s.value
)
def test_block_at_discover_or_acquire_must_never_be_shown_usable(
    blocked_step: WorkflowStepName,
) -> None:
    """Hệ quả trực tiếp của GATE ECO-003 ("downloadable_only"/"launches_only"
    KHÔNG BAO GIỜ usable — và theo cùng nguyên tắc, một workflow CHƯA chạy
    được gì thật ngoài một nấc đầu bị chặn bởi phụ thuộc ngoài TUYỆT ĐỐI
    không được hiển thị "dùng được"). Vì bug ở
    ``test_any_step_blocked_by_external_dependency_must_be_blocked_status``,
    kết quả hiện tại là ``partial_workflow`` — và ``is_usable(partial_workflow)
    == True`` (``partial_workflow`` nằm trong ``USABLE_STATUSES``) — tức là
    GATE hiện tại coi một workflow bị chặn ngay từ ``discover``/``acquire``
    là "dùng được". Đây là vi phạm GATE cấp độ cao hơn chỉ một nhãn sai."""

    steps = steps_single_outcome(blocked_step, StepOutcome.BLOCKED)
    result = derive_published_status(steps)

    assert is_usable(result.status) is False, (
        f"GATE VI PHẠM: nấc '{blocked_step.value}' bị blocked (phụ thuộc "
        f"ngoài) nhưng is_usable() == True cho status "
        f"'{result.status.value}' — một workflow chưa chạy được gì thật "
        "(blocked ngay từ discover/acquire) KHÔNG BAO GIỜ được coi là dùng "
        "được."
    )


def test_discover_blocked_reasons_text_must_not_falsely_claim_later_steps_passed() -> None:
    """DEFECT phụ (hệ quả của nhánh fallback sai): khi ``discover`` bị
    blocked và MỌI nấc sau đều ``not_run``, nhánh fallback hiện tại trả về
    lý do cố định "Đã qua authenticate/execute nhưng chưa tới
    submit_or_export/verify_result" — một câu SAI SỰ THẬT (không nấc nào
    ngoài discover được chạy). Thông tin sai trong ``reasons_vi`` tự nó là
    một vấn đề trung thực (bất kể nhãn trạng thái đúng/sai), vì đây là lý do
    hiển thị cho người xác minh catalog."""

    steps = steps_single_outcome(
        WorkflowStepName.DISCOVER,
        StepOutcome.BLOCKED,
        note_vi="Không có kết nối ra ngoài tới domain .gov.vn (ECONNREFUSED).",
    )
    result = derive_published_status(steps)
    joined = " ".join(result.reasons_vi)

    assert "authenticate/execute" not in joined, (
        "DEFECT: reasons_vi khẳng định sai rằng authenticate/execute đã "
        f"chạy, trong khi mọi nấc sau 'discover' đều not_run. reasons_vi "
        f"thật: {result.reasons_vi!r}"
    )
