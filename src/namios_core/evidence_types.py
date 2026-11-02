"""Evidence API (WP9 hiện thực — §11.2). Xem M1-INTERFACES.md §7.7.

Gate (FACT §11.2/§18.3): ``task_verified`` chỉ khi mọi test ``required=true``
có ``result="pass"`` **và** ``qa_reviewer != null``. ``skipped`` KHÔNG được
đổi thành pass (FACT §18.1).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from namios_core.compat import CompatStatus
from namios_core.manifest_types import SchemaResult


@dataclass(frozen=True)
class EvidenceTest:
    test_id: str
    required: bool
    result: Literal["pass", "fail", "not_run", "skipped", "blocked_external_dependency"]


@dataclass(frozen=True)
class EvidenceReport:
    """Ánh xạ ``contracts/evidence-report.schema.json``."""

    report_id: str
    manifest_id: str
    tests: tuple[EvidenceTest, ...]
    decision: Literal["pending", "experimental", "task_verified", "blocked", "revoked"]
    qa_reviewer: str | None
    environment: Mapping[str, Any]


@dataclass(frozen=True)
class GateResult:
    allowed_status: CompatStatus
    reasons_vi: tuple[str, ...]


class EvidenceValidator(Protocol):
    def load(self, path: str) -> EvidenceReport: ...

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult: ...

    def compute_allowed_status(
        self, rep: EvidenceReport
    ) -> GateResult: ...  # gate "no task_verified w/o evidence"
