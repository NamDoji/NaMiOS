"""Hiện thực ``EvidenceValidator`` (namios_core.evidence_types, §7.7).

Validation 2 tầng (giống WP2, FACT "schema hợp lệ ≠ an toàn/đủ để chứng
nhận"):
  - Tầng 1 (``validate_schema``): cấu trúc JSON theo
    ``contracts/evidence-report.schema.json`` (``_schema_engine``).
  - Tầng 2 (``compute_allowed_status``): gate ngữ nghĩa — "không
    task_verified khi thiếu evidence/QA approval" (``_gate``).

``load()`` đọc file qua ``_safe_io`` (dùng ``namios_security`` của WP8),
chạy tầng 1, rồi build ``EvidenceReport``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from namios_core.errors import ErrorCode
from namios_core.evidence_types import EvidenceReport, EvidenceTest, GateResult
from namios_core.manifest_types import SchemaResult
from namios_core.validation import ValidationError
from namios_evidence._errors import EvidenceLoadError
from namios_evidence._gate import compute_allowed_status as _compute_allowed_status
from namios_evidence._safe_io import PathUnsafeError, read_text_safe
from namios_evidence._schema_engine import validate_raw

__all__ = ["EvidenceValidatorImpl", "EvidenceLoadError", "PathUnsafeError", "build_report"]


def build_report(raw: Mapping[str, Any]) -> EvidenceReport:
    """Chuyển JSON đã qua tầng 1 (schema OK) thành ``EvidenceReport``.

    KHÔNG gọi hàm này trên ``raw`` chưa qua ``validate_schema`` — các truy
    cập dưới đây giả định cấu trúc đã hợp lệ (unknown key/kiểu sai đã bị
    chặn ở tầng 1)."""

    tests = tuple(
        EvidenceTest(
            test_id=t["test_id"],
            required=bool(t["required"]),
            result=t["result"],
        )
        for t in raw["tests"]
    )
    qa_approval = raw["qa_approval"]
    return EvidenceReport(
        report_id=raw["report_id"],
        manifest_id=raw["manifest_id"],
        tests=tests,
        decision=raw["decision"],
        qa_reviewer=qa_approval["reviewer"],
        environment=dict(raw["environment"]),
    )


class EvidenceValidatorImpl:
    """Hiện thực cụ thể khớp ``namios_core.evidence_types.EvidenceValidator``."""

    def load(self, path: str) -> EvidenceReport:
        text = read_text_safe(path)
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise EvidenceLoadError(
                (
                    ValidationError(
                        code=ErrorCode.E_INPUT_SCHEMA.value,
                        path="$",
                        message_vi=f"Nội dung evidence report không phải JSON hợp lệ: {exc.msg}.",
                    ),
                )
            ) from exc

        schema_result = self.validate_schema(raw)
        if not schema_result.ok:
            raise EvidenceLoadError(schema_result.errors)

        return build_report(raw)

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        violations = validate_raw(raw)
        return SchemaResult(ok=len(violations) == 0, errors=tuple(violations))

    def compute_allowed_status(self, rep: EvidenceReport) -> GateResult:
        return _compute_allowed_status(rep)
