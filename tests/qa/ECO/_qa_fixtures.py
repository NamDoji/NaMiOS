"""Helper dựng dữ liệu RIÊNG cho bộ test đối kháng (adversarial) của tester
ECO. CỐ Ý viết độc lập với ``tests/unit/eco/_fixtures.py`` của dev (không
import, không tái dùng) — tránh test của tester bị lệch cùng giả định với
code đang kiểm thử. Không phải test case (không có hàm bắt đầu bằng
``test_`` — không bị pytest thu thập)."""

from __future__ import annotations

from namios_eco.workflow import StepOutcome, WorkflowStep, WorkflowStepName

#: Thứ tự 7 nấc chuẩn — khai báo lại độc lập (không import
#: ``namios_eco.workflow.WORKFLOW_STEP_ORDER``) để không lệ thuộc nguồn đang
#: kiểm thử khi dựng input tấn công theo thứ tự.
_STEP_ORDER: tuple[WorkflowStepName, ...] = (
    WorkflowStepName.DISCOVER,
    WorkflowStepName.ACQUIRE,
    WorkflowStepName.INSTALL_OR_OPEN,
    WorkflowStepName.AUTHENTICATE,
    WorkflowStepName.EXECUTE,
    WorkflowStepName.SUBMIT_OR_EXPORT,
    WorkflowStepName.VERIFY_RESULT,
)


def steps_single_outcome(
    single_step: WorkflowStepName,
    single_outcome: StepOutcome,
    *,
    before: StepOutcome = StepOutcome.PASS,
    after: StepOutcome = StepOutcome.NOT_RUN,
    note_vi: str | None = None,
) -> tuple[WorkflowStep, ...]:
    """Dựng 7 nấc trong đó MỘT nấc có outcome tấn công (``single_outcome``),
    các nấc TRƯỚC nó = ``before`` (mặc định PASS — "đã làm tới đây"), các nấc
    SAU nó = ``after`` (mặc định NOT_RUN — "chưa thử gì tiếp"). Dùng để dò
    GATE ECO-016 ("blocked vì phụ thuộc ngoài") ở TỪNG vị trí trong 7 nấc,
    không chỉ các vị trí dev đã có test."""

    result: list[WorkflowStep] = []
    hit_index = _STEP_ORDER.index(single_step)
    for idx, name in enumerate(_STEP_ORDER):
        if idx < hit_index:
            result.append(WorkflowStep(name, before))
        elif idx == hit_index:
            result.append(WorkflowStep(name, single_outcome, note_vi=note_vi))
        else:
            result.append(WorkflowStep(name, after))
    return tuple(result)


def all_not_run() -> tuple[WorkflowStep, ...]:
    return tuple(WorkflowStep(name, StepOutcome.NOT_RUN) for name in _STEP_ORDER)


def raw_catalog_entry(**overrides: object) -> dict[str, object]:
    """Dựng raw dict JSON TỐI THIỂU hợp lệ cho
    ``contracts/service-catalog.schema.json`` — viết lại từ đặc tả hợp đồng,
    KHÔNG tái dùng helper của dev, để test schema/semantic một cách độc lập."""

    base: dict[str, object] = {
        "schema_version": "1.0",
        "id": "qa-eco.baseline",
        "provider": "QA Tester Provider",
        "agency": None,
        "purpose": "Khai và nộp hồ sơ giả định dùng cho test đối kháng ECO.",
        "official_url": "https://example.gov.vn/dich-vu",
        "source_check": "Khớp domain .gov.vn giả định cho test, ngày kiểm 2026-11-02.",
        "version": None,
        "license": "Miễn phí (test)",
        "published_os": ["Web"],
        "dependencies": [],
        "account_condition": "Không cần token cho test này.",
        "service_cost": "Miễn phí",
        "data_sensitivity": "cong_khai",
        "test_profile": "qa-eco-report-001",
        "last_updated": "2026-11-02",
        "evidence_source": "https://example.gov.vn/dich-vu",
        "published_status": "not_inventoried",
        "windows_mode": "web_linux",
        "tested_by_namios": False,
        "officially_supported_by_vendor": False,
    }
    base.update(overrides)
    return base
