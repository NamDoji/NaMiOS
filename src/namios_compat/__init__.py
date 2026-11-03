"""NaMiOS — Trung tâm tương thích (Phụ lục 03, COMP-025..054).

Bộ não quyết định "chạy ứng dụng Windows kiểu nào" cho từng workflow nghiệp
vụ Việt Nam: resolver chọn mode theo thứ tự điều tra (native_linux → web_linux
→ wine → remote_windows → windows_vm), classifier phân loại runtime, device
registry ghi năng lực thiết bị theo model, workflow pack theo ngành, và GATE
trạng thái trung thực (nối ECO-001..024).

Nguyên tắc: KHÔNG tự nhận tương thích khi chưa thử đúng phiên bản/nghiệp vụ/
thiết bị; thiếu môi trường thật → ``no_verified_route``/``blocked``, không bịa.
Chứng nhận thật (Wine, thiết bị, ký số, DB, pilot) là Giai đoạn B/C/D cần
vendor + build host — phần code ở đây là schema/resolver/validator/fixture
chạy + test được ngay (Giai đoạn A).

Package này tự được ``[tool.setuptools.packages.find] where=["src"]`` nhận
diện — KHÔNG cần sửa ``pyproject.toml``.
"""

from __future__ import annotations

from namios_compat import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n khi import package)
from namios_compat._errors import CompatErrorCode
from namios_compat._types import (
    MODE_INVESTIGATION_ORDER,
    SCHEMA_VERSION,
    WINE_BLOCKER_KINDS,
    AppRef,
    BusinessStatus,
    Certification,
    ClassificationConfidence,
    CompatEvidence,
    DeviceClass,
    DeviceEntry,
    DeviceProtocol,
    EndToEndStatus,
    EvidenceEnvironment,
    ResolveInput,
    Route,
    RouteCandidate,
    RouteResolution,
    RuntimeClassification,
    RuntimeKind,
    Sector,
    TechnicalStatus,
    VendorSupport,
    WorkflowEntry,
    WorkflowPack,
    WorkflowPackStep,
)
from namios_compat.classifier import classify_runtime
from namios_compat.device_registry import DeviceRegistry, load_devices
from namios_compat.evidence import (
    compute_fixture_hash,
    evaluate_route_status,
    evidence_to_steps,
    validate_evidence,
)
from namios_compat.resolver import resolve_routes
from namios_compat.schema import (
    build_device_entry,
    build_workflow_entry,
    validate_device_entry_raw,
    validate_workflow_entry,
    validate_workflow_entry_raw,
)
from namios_compat.workflow_pack import (
    SAMPLE_PACKS,
    load_sample_packs,
    pack_to_dict,
    validate_pack_raw,
)

__all__ = [
    # constants / enums
    "SCHEMA_VERSION",
    "MODE_INVESTIGATION_ORDER",
    "WINE_BLOCKER_KINDS",
    "TechnicalStatus",
    "BusinessStatus",
    "EndToEndStatus",
    "VendorSupport",
    "RuntimeKind",
    "ClassificationConfidence",
    "DeviceClass",
    "DeviceProtocol",
    "Sector",
    "EvidenceEnvironment",
    "CompatErrorCode",
    # dataclasses
    "AppRef",
    "Route",
    "Certification",
    "WorkflowEntry",
    "DeviceEntry",
    "WorkflowPack",
    "WorkflowPackStep",
    "CompatEvidence",
    "RuntimeClassification",
    "ResolveInput",
    "RouteCandidate",
    "RouteResolution",
    # resolver (COMP-025)
    "resolve_routes",
    # classifier (COMP-028)
    "classify_runtime",
    # device registry (COMP-032)
    "DeviceRegistry",
    "load_devices",
    # workflow packs (COMP-031)
    "SAMPLE_PACKS",
    "load_sample_packs",
    "pack_to_dict",
    "validate_pack_raw",
    # schema (COMP-048)
    "validate_workflow_entry",
    "validate_workflow_entry_raw",
    "build_workflow_entry",
    "validate_device_entry_raw",
    "build_device_entry",
    # evidence + gate (COMP-049)
    "compute_fixture_hash",
    "validate_evidence",
    "evidence_to_steps",
    "evaluate_route_status",
]
