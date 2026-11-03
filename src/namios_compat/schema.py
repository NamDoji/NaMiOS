"""Schema + evidence gate cho catalog tương thích (COMP-048).

Validator tầng-1 (cấu trúc) viết tay, KHÔNG phụ thuộc ``jsonschema`` (đồng bộ
với ``namios_eco.catalog_schema``). Trọng tâm trung thực (nghiệm thu COMP-048):

- ``schema_version`` phải đúng hợp đồng hiện hành; ``workflow_id`` = ID ổn định.
- ``required_steps`` phải đúng 7 nấc ECO-001 theo thứ tự.
- Giá trị enum mode/status/sector hợp lệ.
- **Chặn metadata giả**: chứng nhận tự nhận ``technical_status=verified`` /
  ``end_to_end_status=pass`` PHẢI có ``tested_at`` + ``evidence_ids``;
  ``vendor_support=supported`` PHẢI có bằng chứng; ``revoked=true`` thì không
  route nào được gán trạng thái dùng được.

Trạng thái KHÔNG thể bị NÂNG bằng metadata — ``evidence.evaluate_route_status``
(COMP-049) mới là nơi suy trạng thái thật từ 7 nấc có bằng chứng.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any

from namios_compat import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_compat._errors import CompatErrorCode
from namios_compat._types import (
    SCHEMA_VERSION,
    UNRESOLVED_VERSIONS,
    AppRef,
    Certification,
    DeviceClass,
    DeviceEntry,
    DeviceProtocol,
    EndToEndStatus,
    Route,
    Sector,
    TechnicalStatus,
    VendorSupport,
    WorkflowEntry,
)
from namios_compat._types import BusinessStatus as _BusinessStatus
from namios_core.manifest_types import SchemaResult
from namios_core.validation import ValidationError
from namios_eco.status import USABLE_STATUSES, PublishedStatus, WindowsMode
from namios_eco.workflow import WORKFLOW_STEP_ORDER, WorkflowStepName
from namios_i18n import Lang, t

__all__ = [
    "validate_workflow_entry_raw",
    "validate_workflow_entry",
    "build_workflow_entry",
    "validate_device_entry_raw",
    "build_device_entry",
]

_REQUIRED_STEP_VALUES = [s.value for s in WORKFLOW_STEP_ORDER]

_ENTRY_REQUIRED_KEYS = (
    "schema_version",
    "workflow_id",
    "sector",
    "provider_id",
    "region_scope",
    "app",
    "required_steps",
    "requires",
    "routes",
    "certification",
    "last_updated",
)


def _enum_values(enum_cls: type[Enum]) -> set[str]:
    return {e.value for e in enum_cls}


def _has_real_evidence(evidence_ids: Any) -> bool:
    """Evidence hợp lệ = list có ÍT NHẤT một ID chuỗi không rỗng/không toàn
    khoảng trắng (COMP-048 / QA COMPAT-ADV-001: ``[""]`` không phải bằng chứng)."""

    return isinstance(evidence_ids, list) and any(
        isinstance(x, str) and x.strip() for x in evidence_ids
    )


def _is_iso_date(value: Any) -> bool:
    """``True`` nếu ``value`` là ngày/giờ ISO-8601 hợp lệ (zero-pad bắt buộc).

    Chặn QA COMPAT-ADV-002: chuỗi ngày không zero-pad (``2026-2-1``) hoặc rác
    bị từ chối ngay ở schema — không để lọt xuống so-sánh từ-điển ở gate."""

    if not isinstance(value, str) or not value.strip():
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False


def _err(code: CompatErrorCode | str, path: str, key: str, **params: Any) -> ValidationError:
    code_str = code.value if isinstance(code, CompatErrorCode) else code
    return ValidationError(code=code_str, path=path, message_vi=t(key, lang=Lang.VI, **params))


def _check_enum(
    raw: Mapping[str, Any], field: str, enum_cls: type[Enum], path: str
) -> list[ValidationError]:
    value = raw.get(field)
    if not isinstance(value, str) or value not in _enum_values(enum_cls):
        return [
            _err(
                CompatErrorCode.E_COMPAT_ENUM_INVALID,
                f"{path}.{field}",
                "compat.schema.error.enum_invalid",
                value=value,
                field=field,
            )
        ]
    return []


def _validate_certification_raw(
    cert: Mapping[str, Any], routes: Any, app_version: Any
) -> list[ValidationError]:
    """Phần CHỐNG METADATA GIẢ (COMP-048 + QA COMPAT-ADV-001/002/005)."""

    errors: list[ValidationError] = []
    for field, enum_cls in (
        ("technical_status", TechnicalStatus),
        ("business_status", _BusinessStatus),
        ("end_to_end_status", EndToEndStatus),
        ("vendor_support", VendorSupport),
    ):
        errors.extend(_check_enum(cert, field, enum_cls, "certification"))
    if errors:
        return errors  # enum sai thì không suy tiếp

    technical = cert.get("technical_status")
    e2e = cert.get("end_to_end_status")
    vendor = cert.get("vendor_support")
    tested_at = cert.get("tested_at")
    evidence_ids = cert.get("evidence_ids") or []
    recertify_by = cert.get("recertify_by")
    revoked = bool(cert.get("revoked", False))

    # Ngày phải đúng ISO-8601 nếu có (COMPAT-ADV-002: chặn '2026-2-1' lọt
    # xuống so-sánh từ-điển ở evidence gate).
    for field, value in (("tested_at", tested_at), ("recertify_by", recertify_by)):
        if value is not None and not _is_iso_date(value):
            errors.append(
                _err(
                    "E_INPUT_SCHEMA",
                    f"certification.{field}",
                    "compat.schema.error.date_format",
                    field=field,
                    value=value,
                )
            )

    claims_verified = (
        technical == TechnicalStatus.VERIFIED.value or e2e == EndToEndStatus.PASS.value
    )
    if claims_verified:
        claim = (
            "technical_status=verified"
            if technical == TechnicalStatus.VERIFIED.value
            else "end_to_end_status=pass"
        )
        if not (isinstance(tested_at, str) and tested_at.strip()):
            errors.append(
                _err(
                    CompatErrorCode.E_COMPAT_CERT_UNSUPPORTED,
                    "certification.tested_at",
                    "compat.schema.error.cert_tested_at_missing",
                    claim=claim,
                )
            )
        if not _has_real_evidence(evidence_ids):
            errors.append(
                _err(
                    CompatErrorCode.E_COMPAT_CERT_UNSUPPORTED,
                    "certification.evidence_ids",
                    "compat.schema.error.cert_evidence_missing",
                    claim=claim,
                    missing="required_steps",
                )
            )
        # COMPAT-ADV-005: không thể verified khi app.version chưa pin — nếu
        # version là "unresolved"/"unknown"/rỗng, chứng nhận vĩnh viễn miễn
        # nhiễm kiểm-tra-drift ở resolver, nên CẤM claim verified.
        if not isinstance(app_version, str) or app_version in UNRESOLVED_VERSIONS:
            errors.append(
                _err(
                    CompatErrorCode.E_COMPAT_CERT_UNSUPPORTED,
                    "app.version",
                    "compat.schema.error.cert_version_unpinned",
                    claim=claim,
                    version=app_version,
                )
            )

    if vendor == VendorSupport.SUPPORTED.value and not _has_real_evidence(evidence_ids):
        errors.append(
            _err(
                CompatErrorCode.E_COMPAT_VENDOR_CLAIM,
                "certification.vendor_support",
                "compat.schema.error.vendor_claim",
            )
        )

    if revoked and isinstance(routes, list):
        for i, r in enumerate(routes):
            if isinstance(r, Mapping) and r.get("status") in {s.value for s in USABLE_STATUSES}:
                errors.append(
                    _err(
                        "E_REVOKED",
                        f"routes[{i}].status",
                        "compat.schema.error.cert_revoked_usable",
                    )
                )
    return errors


def validate_workflow_entry_raw(raw: Any) -> list[ValidationError]:
    """Kiểm cấu trúc + ngữ nghĩa chống-metadata-giả của một mục workflow (COMP-048)."""

    if not isinstance(raw, Mapping):
        return [_err("E_INPUT_SCHEMA", "$", "compat.schema.error.type_invalid", field="$")]

    errors: list[ValidationError] = []
    for key in _ENTRY_REQUIRED_KEYS:
        if key not in raw:
            errors.append(
                _err("E_INPUT_SCHEMA", key, "compat.schema.error.missing_field", field=key)
            )
    if errors:
        return errors

    if raw.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            _err(
                CompatErrorCode.E_COMPAT_SCHEMA_VERSION,
                "schema_version",
                "compat.schema.error.schema_version",
                want=SCHEMA_VERSION,
                got=raw.get("schema_version"),
            )
        )

    if not (isinstance(raw.get("workflow_id"), str) and raw["workflow_id"].strip()):
        errors.append(
            _err(
                "E_INPUT_SCHEMA",
                "workflow_id",
                "compat.schema.error.missing_field",
                field="workflow_id",
            )
        )

    errors.extend(_check_enum(raw, "sector", Sector, "$"))

    app = raw.get("app")
    if (
        not isinstance(app, Mapping)
        or not isinstance(app.get("id"), str)
        or not isinstance(app.get("version"), str)
    ):
        errors.append(
            _err("E_INPUT_SCHEMA", "app", "compat.schema.error.type_invalid", field="app")
        )

    required_steps = raw.get("required_steps")
    if required_steps != _REQUIRED_STEP_VALUES:
        errors.append(
            _err(
                CompatErrorCode.E_COMPAT_REQUIRED_STEPS,
                "required_steps",
                "compat.schema.error.required_steps",
            )
        )

    if not isinstance(raw.get("requires"), list):
        errors.append(
            _err("E_INPUT_SCHEMA", "requires", "compat.schema.error.type_invalid", field="requires")
        )

    routes = raw.get("routes")
    if not isinstance(routes, list):
        errors.append(
            _err("E_INPUT_SCHEMA", "routes", "compat.schema.error.type_invalid", field="routes")
        )
    else:
        for i, r in enumerate(routes):
            if not isinstance(r, Mapping):
                errors.append(
                    _err(
                        "E_INPUT_SCHEMA",
                        f"routes[{i}]",
                        "compat.schema.error.type_invalid",
                        field=f"routes[{i}]",
                    )
                )
                continue
            errors.extend(_check_enum(r, "mode", WindowsMode, f"routes[{i}]"))
            errors.extend(_check_enum(r, "status", PublishedStatus, f"routes[{i}]"))

    cert = raw.get("certification")
    if not isinstance(cert, Mapping):
        errors.append(
            _err(
                "E_INPUT_SCHEMA",
                "certification",
                "compat.schema.error.type_invalid",
                field="certification",
            )
        )
    else:
        app_version = app.get("version") if isinstance(app, Mapping) else None
        errors.extend(_validate_certification_raw(cert, routes, app_version))

    return errors


def validate_workflow_entry(raw: Any) -> SchemaResult:
    """Bọc ``validate_workflow_entry_raw`` thành ``SchemaResult`` (hợp đồng chung)."""

    errors = validate_workflow_entry_raw(raw)
    return SchemaResult(ok=not errors, errors=tuple(errors))


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return ()


def build_workflow_entry(raw: Mapping[str, Any]) -> WorkflowEntry:
    """Dựng ``WorkflowEntry`` từ dict ĐÃ validate (gọi sau khi ok)."""

    app = raw["app"]
    cert = raw["certification"]
    routes = tuple(
        Route(
            mode=WindowsMode(r["mode"]),
            status=str(r["status"]),
            blockers=_str_tuple(r.get("blockers")),
            reason_vi=str(r.get("reason_vi", "")),
        )
        for r in raw["routes"]
    )
    certification = Certification(
        os_build=cert.get("os_build"),
        browser_or_runner=cert.get("browser_or_runner"),
        device_models=_str_tuple(cert.get("device_models")),
        tested_at=cert.get("tested_at"),
        evidence_ids=_str_tuple(cert.get("evidence_ids")),
        technical_status=TechnicalStatus(cert["technical_status"]),
        business_status=_BusinessStatus(cert["business_status"]),
        end_to_end_status=EndToEndStatus(cert["end_to_end_status"]),
        vendor_support=VendorSupport(cert["vendor_support"]),
        recertify_by=cert.get("recertify_by"),
        revoked=bool(cert.get("revoked", False)),
    )
    return WorkflowEntry(
        schema_version=str(raw["schema_version"]),
        workflow_id=str(raw["workflow_id"]),
        sector=Sector(raw["sector"]),
        provider_id=str(raw["provider_id"]),
        region_scope=str(raw["region_scope"]),
        app=AppRef(
            id=str(app["id"]),
            version=str(app["version"]),
            architecture=str(app.get("architecture", "unknown")),
            license=str(app.get("license", "verify_with_vendor")),
        ),
        required_steps=tuple(WorkflowStepName(s) for s in raw["required_steps"]),
        requires=_str_tuple(raw.get("requires")),
        routes=routes,
        certification=certification,
        last_updated=str(raw["last_updated"]),
        service_url=raw.get("service_url"),
        source=str(raw.get("source", "")),
    )


def validate_device_entry_raw(raw: Any) -> list[ValidationError]:
    """Kiểm cấu trúc một mục thiết bị (COMP-032)."""

    if not isinstance(raw, Mapping):
        return [_err("E_INPUT_SCHEMA", "$", "compat.schema.error.type_invalid", field="$")]
    errors: list[ValidationError] = []
    for key in ("device_id", "vendor", "model", "linux_mechanism"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            errors.append(
                _err("E_INPUT_SCHEMA", key, "compat.schema.error.missing_field", field=key)
            )
    errors.extend(_check_enum(raw, "device_class", DeviceClass, "$"))
    errors.extend(_check_enum(raw, "protocol", DeviceProtocol, "$"))
    if "status" in raw:
        errors.extend(_check_enum(raw, "status", TechnicalStatus, "$"))
    return errors


def build_device_entry(raw: Mapping[str, Any]) -> DeviceEntry:
    """Dựng ``DeviceEntry`` từ dict ĐÃ validate."""

    return DeviceEntry(
        device_id=str(raw["device_id"]),
        device_class=DeviceClass(raw["device_class"]),
        vendor=str(raw["vendor"]),
        model=str(raw["model"]),
        protocol=DeviceProtocol(raw["protocol"]),
        linux_mechanism=str(raw["linux_mechanism"]),
        tested_functions=_str_tuple(raw.get("tested_functions")),
        vid=raw.get("vid"),
        pid=raw.get("pid"),
        firmware=raw.get("firmware"),
        version=raw.get("version"),
        permission_condition=str(raw.get("permission_condition", "")),
        status=(
            TechnicalStatus(raw["status"]) if raw.get("status") else TechnicalStatus.NOT_INVENTORIED
        ),
        evidence_ids=_str_tuple(raw.get("evidence_ids")),
        notes_vi=str(raw.get("notes_vi", "")),
    )
