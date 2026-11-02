"""ECO-001 — Mô hình 7 nấc của một workflow/thủ tục:
``discover``, ``acquire``, ``install_or_open``, ``authenticate``,
``execute``, ``submit_or_export``, ``verify_result``.

Quy tắc bắt buộc (FACT PHU-LUC-02 §3 ECO-001):
  - Mỗi nấc có kết quả RIÊNG (``StepOutcome``); không gộp kết quả các nấc.
  - Với phần mềm web không có bộ cài: ``install_or_open`` LÀ hành động mở
    trình duyệt đúng URL chính thức; TUYỆT ĐỐI không đánh dấu ``acquire``
    thành ``downloaded_binary`` (``validate_workflow_rules`` chặn).
  - Với thủ tục không cần ký: nấc liên quan ghi ``not_applicable`` — mô hình
    LUÔN giữ đủ 7 nấc (KHÔNG xoá nấc khỏi mô hình dù not_applicable); đây là
    bất biến KẾT CẤU của ``WorkflowResult`` (không có cách tạo kết quả thiếu
    nấc nào trong 7 nấc), không phải một rule riêng cần nhớ bật/tắt.

Hàm trong module này CHỈ kiểm cấu trúc + hai quy tắc acquire/install cho web
app. GATE suy ra ``PublishedStatus`` (bao gồm yêu cầu evidence cho
``workflow_verified``) nằm ở ``status.py`` theo đúng phân nhiệm trong lệnh
giao việc.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from namios_core.validation import ValidationError
from namios_eco._errors import EcoErrorCode

__all__ = [
    "WorkflowStepName",
    "WORKFLOW_STEP_ORDER",
    "StepOutcome",
    "METHOD_DOWNLOADED_BINARY",
    "METHOD_OPEN_BROWSER",
    "WorkflowStep",
    "WorkflowResult",
    "validate_workflow_structure",
    "validate_workflow_rules",
]


class WorkflowStepName(str, Enum):
    """7 nấc cố định (ECO-001). Giá trị chuỗi là ID ổn định, dùng trong
    evidence/báo cáo — KHÔNG đổi sau khi phát hành."""

    DISCOVER = "discover"
    ACQUIRE = "acquire"
    INSTALL_OR_OPEN = "install_or_open"
    AUTHENTICATE = "authenticate"
    EXECUTE = "execute"
    SUBMIT_OR_EXPORT = "submit_or_export"
    VERIFY_RESULT = "verify_result"


#: Thứ tự chuẩn — nguồn DUY NHẤT cho "đủ 7 nấc đúng thứ tự".
WORKFLOW_STEP_ORDER: tuple[WorkflowStepName, ...] = (
    WorkflowStepName.DISCOVER,
    WorkflowStepName.ACQUIRE,
    WorkflowStepName.INSTALL_OR_OPEN,
    WorkflowStepName.AUTHENTICATE,
    WorkflowStepName.EXECUTE,
    WorkflowStepName.SUBMIT_OR_EXPORT,
    WorkflowStepName.VERIFY_RESULT,
)


class StepOutcome(str, Enum):
    """Kết quả riêng của một nấc (FACT ECO-001: "mỗi nấc có kết quả riêng")."""

    PASS = "pass"  # noqa: S105 — kết quả nấc workflow, không phải mật khẩu
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"


#: Giá trị ``method`` công nhận cho nấc ``acquire`` khi phần mềm CÓ bộ cài nhị phân.
METHOD_DOWNLOADED_BINARY = "downloaded_binary"
#: Giá trị ``method`` công nhận cho nấc ``install_or_open`` khi phần mềm là web
#: không bộ cài — "mở trình duyệt đúng URL chính thức".
METHOD_OPEN_BROWSER = "open_browser"


@dataclass(frozen=True)
class WorkflowStep:
    """Kết quả của một nấc. ``method`` là mô tả CÁCH đạt outcome (tự do,
    nhưng có hai hằng số đã biết ``METHOD_DOWNLOADED_BINARY``/
    ``METHOD_OPEN_BROWSER`` dùng trong rule web-app). ``evidence_ref`` trỏ
    tới bằng chứng thật (vd report_id/log đã khử bí mật) — bắt buộc khi
    ``submit_or_export``/``verify_result`` pass để đủ điều kiện
    ``workflow_verified`` (xem ``status.derive_published_status``)."""

    name: WorkflowStepName
    outcome: StepOutcome
    method: str | None = None
    evidence_ref: str | None = None
    note_vi: str | None = None


@dataclass(frozen=True)
class WorkflowResult:
    """Kết quả đầy đủ một workflow đã khảo sát cho một ``ServiceEntry``."""

    service_id: str
    steps: tuple[WorkflowStep, ...]


def _err(code: str, path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=code, path=path, message_vi=message_vi)


def validate_workflow_structure(steps: tuple[WorkflowStep, ...]) -> list[ValidationError]:
    """Kiểm bất biến kết cấu ECO-001: ĐÚNG 7 nấc, ĐÚNG tên, ĐÚNG thứ tự,
    KHÔNG thiếu/KHÔNG trùng. Đây là cơ chế duy nhất bảo đảm "không xoá nấc
    khỏi mô hình dù not_applicable" — vì không có cách tạo ``WorkflowResult``
    hợp lệ (vượt qua hàm này) mà thiếu bất kỳ nấc nào trong 7 nấc chuẩn."""

    errors: list[ValidationError] = []

    names = tuple(s.name for s in steps)
    seen: set[WorkflowStepName] = set()
    for idx, name in enumerate(names):
        if name not in WORKFLOW_STEP_ORDER or name in seen:
            errors.append(
                _err(
                    EcoErrorCode.E_ECO_STEP_UNKNOWN_OR_DUPLICATE.value,
                    f"steps[{idx}]",
                    f"Nấc '{name}' không hợp lệ hoặc bị lặp lại tại vị trí {idx}.",
                )
            )
        seen.add(name)

    missing = tuple(n for n in WORKFLOW_STEP_ORDER if n not in seen)
    for name in missing:
        errors.append(
            _err(
                EcoErrorCode.E_ECO_STEP_MISSING.value,
                "steps",
                f"Thiếu nấc bắt buộc '{name.value}' — mô hình 7 nấc PHẢI giữ đủ "
                "7 nấc dù kết quả là not_applicable (ECO-001), không được xoá.",
            )
        )

    # Chỉ kiểm thứ tự khi đủ 7 nấc hợp lệ, tránh chồng lỗi gây nhiễu.
    if not errors and names != WORKFLOW_STEP_ORDER:
        errors.append(
            _err(
                EcoErrorCode.E_ECO_STEP_ORDER.value,
                "steps",
                f"Thứ tự nấc phải đúng {tuple(n.value for n in WORKFLOW_STEP_ORDER)}.",
            )
        )

    return errors


def validate_workflow_rules(
    steps: tuple[WorkflowStep, ...], *, is_web_without_binary: bool
) -> list[ValidationError]:
    """Rule ECO-001 cho phần mềm web không có bộ cài (``is_web_without_binary``):
      - ``acquire.method`` KHÔNG được là ``downloaded_binary``.
      - Nếu ``install_or_open`` đạt ``pass``, ``method`` PHẢI là ``open_browser``
        (xác nhận hành động thật là mở trình duyệt, không phải cài app).

    Gọi hàm này SAU khi ``validate_workflow_structure`` đã pass (giả định có
    đủ 7 nấc đúng tên)."""

    errors: list[ValidationError] = []
    if not is_web_without_binary:
        return errors

    by_name = {s.name: s for s in steps}
    acquire = by_name[WorkflowStepName.ACQUIRE]
    install = by_name[WorkflowStepName.INSTALL_OR_OPEN]

    if acquire.method == METHOD_DOWNLOADED_BINARY:
        errors.append(
            _err(
                EcoErrorCode.E_ECO_ACQUIRE_METHOD_INVALID.value,
                "steps.acquire.method",
                "Phần mềm web không có bộ cài KHÔNG được đánh dấu "
                "acquire.method='downloaded_binary' (ECO-001).",
            )
        )

    if install.outcome == StepOutcome.PASS and install.method != METHOD_OPEN_BROWSER:
        errors.append(
            _err(
                EcoErrorCode.E_ECO_INSTALL_METHOD_INVALID.value,
                "steps.install_or_open.method",
                "Phần mềm web không có bộ cài: install_or_open pass PHẢI có "
                f"method='{METHOD_OPEN_BROWSER}' (mở trình duyệt đúng URL chính thức).",
            )
        )

    return errors
