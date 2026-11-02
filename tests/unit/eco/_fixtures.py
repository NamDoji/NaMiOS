"""Fixture helper dùng chung cho test namios_eco."""

from __future__ import annotations

from namios_eco.models import ServiceEntry
from namios_eco.status import PublishedStatus, WindowsMode
from namios_eco.workflow import StepOutcome, WorkflowStep, WorkflowStepName

#: 7 nấc mặc định — tất cả pass + có evidence ở submit/verify (trường hợp
#: "lý tưởng" dùng làm baseline rồi test chỉnh từng nấc một.
ALL_PASS_STEPS: tuple[WorkflowStep, ...] = (
    WorkflowStep(WorkflowStepName.DISCOVER, StepOutcome.PASS),
    WorkflowStep(WorkflowStepName.ACQUIRE, StepOutcome.PASS, method="downloaded_binary"),
    WorkflowStep(WorkflowStepName.INSTALL_OR_OPEN, StepOutcome.PASS),
    WorkflowStep(WorkflowStepName.AUTHENTICATE, StepOutcome.PASS),
    WorkflowStep(WorkflowStepName.EXECUTE, StepOutcome.PASS),
    WorkflowStep(
        WorkflowStepName.SUBMIT_OR_EXPORT,
        StepOutcome.PASS,
        evidence_ref="evidence://sandbox/submit-001",
    ),
    WorkflowStep(
        WorkflowStepName.VERIFY_RESULT,
        StepOutcome.PASS,
        evidence_ref="evidence://sandbox/verify-001",
    ),
)


def steps_with(overrides: dict[WorkflowStepName, WorkflowStep]) -> tuple[WorkflowStep, ...]:
    """Trả bản sao ``ALL_PASS_STEPS`` với một số nấc được thay bằng
    ``overrides`` (map theo tên nấc)."""

    return tuple(overrides.get(s.name, s) for s in ALL_PASS_STEPS)


def not_run_steps() -> tuple[WorkflowStep, ...]:
    return tuple(WorkflowStep(name, StepOutcome.NOT_RUN) for name in WorkflowStepName)


def make_entry(**overrides: object) -> ServiceEntry:
    base: dict[str, object] = dict(
        id="thue.etax-ca-nhan",
        provider="Tổng cục Thuế",
        agency="Bộ Tài chính",
        purpose="Lập và nộp tờ khai thuế hộ kinh doanh",
        official_url="https://thuedientu.gdt.gov.vn/",
        source_check="Khớp domain .gov.vn chính thức + ngày kiểm 02/11/2026",
        version="2026.1",
        license="Miễn phí (dịch vụ công)",
        published_os=("Windows 10/11",),
        dependencies=("USB token ký số",),
        account_condition="Cần tài khoản định danh điện tử mức 2",
        service_cost="Miễn phí",
        data_sensitivity="tai_chinh",
        test_profile="report-thue-001",
        last_updated="2026-11-02",
        evidence_source="https://thuedientu.gdt.gov.vn/",
        published_status=PublishedStatus.NOT_INVENTORIED,
        windows_mode=WindowsMode.WEB_LINUX,
        tested_by_namios=False,
        officially_supported_by_vendor=False,
    )
    base.update(overrides)
    return ServiceEntry(**base)  # type: ignore[arg-type]
