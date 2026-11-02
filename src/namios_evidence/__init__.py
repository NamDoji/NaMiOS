"""namios_evidence — WP9: evidence model + evidence-report validator +
compatibility state gate (§11.2, §18.3).

Hiện thực ``namios_core.evidence_types.EvidenceValidator`` (§7.7). Gate:
``task_verified`` chỉ hợp lệ khi mọi test ``required=true`` có
``result="pass"`` VÀ ``qa_reviewer != null``; nếu không → KHÔNG được
``task_verified`` (``E_EVIDENCE_MISSING``)."""

from __future__ import annotations

from namios_evidence._errors import EvidenceLoadError
from namios_evidence._safe_io import PathUnsafeError
from namios_evidence.validator import EvidenceValidatorImpl, build_report

__all__ = [
    "EvidenceValidatorImpl",
    "EvidenceLoadError",
    "PathUnsafeError",
    "build_report",
]
