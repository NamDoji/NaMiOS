"""namios_eco — Phụ lục 02: hệ sinh thái phần mềm thiết yếu tại Việt Nam.

Module Python thuần (schema, state machine, validator, coverage, search) cho
ECO-001..024 (``docs/specs/PHU-LUC-02-HE-SINH-THAI-VN.md``). KHÔNG chứa UI/CLI
(thuộc WP3/namios_cli) và KHÔNG tự thực thi tải/cài/ký/nộp hồ sơ thật — chỉ mô
hình hoá trạng thái và thẩm định dữ liệu khảo sát đã có.

Nguyên tắc bất biến xuyên suốt module (xem GATE ở ``status.py``):
  - ``downloadable_only``/``launches_only`` KHÔNG BAO GIỜ được coi là "dùng được".
  - ``workflow_verified`` CHỈ khi có bằng chứng nộp/nhận thật (evidence_ref).
  - ``tested_by_namios`` và ``officially_supported_by_vendor`` là hai trường
    ĐỘC LẬP — không suy ra trường này từ trường kia.
"""

from __future__ import annotations

from namios_eco.models import ServiceEntry
from namios_eco.status import (
    PublishedStatus,
    WindowsMode,
    is_usable,
    is_windows_free,
)
from namios_eco.workflow import (
    StepOutcome,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepName,
)

__all__ = [
    "ServiceEntry",
    "PublishedStatus",
    "WindowsMode",
    "is_usable",
    "is_windows_free",
    "StepOutcome",
    "WorkflowResult",
    "WorkflowStep",
    "WorkflowStepName",
]
