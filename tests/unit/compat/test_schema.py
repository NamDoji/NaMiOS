"""COMP-048 — schema + CHỐNG METADATA GIẢ.

Các catalog tương thích shipped (``catalog/compat/*.json``) phải hợp lệ VÀ
trung thực (không có entry nào tự nhận workflow_verified mà chưa test). Các
biến thể metadata giả phải bị TỪ CHỐI."""

from __future__ import annotations

import glob
import json
import os

from namios_compat._errors import CompatErrorCode
from namios_compat.schema import (
    build_workflow_entry,
    validate_workflow_entry,
    validate_workflow_entry_raw,
)

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_STEPS = [
    "discover",
    "acquire",
    "install_or_open",
    "authenticate",
    "execute",
    "submit_or_export",
    "verify_result",
]


def _base_entry() -> dict:
    """Entry hợp lệ, TRUNG THỰC (chưa khảo sát) — nền để đột biến thành các
    ca metadata giả."""
    return {
        "schema_version": "1.0",
        "workflow_id": "vn.test.sample",
        "sector": "tax",
        "provider_id": "unresolved",
        "region_scope": "unresolved",
        "service_url": None,
        "app": {
            "id": "unresolved",
            "version": "1.0",
            "architecture": "x86_64",
            "license": "verify_with_vendor",
        },
        "required_steps": list(_STEPS),
        "requires": ["browser", "signing_method"],
        "routes": [
            {"mode": "wine", "status": "not_inventoried", "blockers": [], "reason_vi": ""},
        ],
        "certification": {
            "os_build": None,
            "browser_or_runner": None,
            "device_models": [],
            "tested_at": None,
            "evidence_ids": [],
            "technical_status": "not_inventoried",
            "business_status": "unreviewed",
            "end_to_end_status": "untested",
            "vendor_support": "unknown",
            "recertify_by": None,
            "revoked": False,
        },
        "last_updated": "2026-11-03",
        "source": "test",
    }


def _codes(raw: dict) -> set[str]:
    return {e.code for e in validate_workflow_entry_raw(raw)}


def test_base_entry_valid() -> None:
    assert validate_workflow_entry(_base_entry()).ok


def test_shipped_catalog_valid_and_honest() -> None:
    paths = glob.glob(os.path.join(_REPO, "catalog", "compat", "*.json"))
    assert paths, "catalog/compat phải có entry mẫu"
    for p in paths:
        raw = json.load(open(p, encoding="utf-8"))
        res = validate_workflow_entry(raw)
        assert res.ok, f"{p}: {[(e.code, e.path) for e in res.errors]}"
        entry = build_workflow_entry(raw)
        # Trung thực: KHÔNG entry shipped nào được tự nhận đã verified/pass khi
        # ta chưa thực sự test trên host thật.
        assert entry.certification.technical_status.value != "verified"
        assert entry.certification.end_to_end_status.value != "pass"
        assert entry.certification.vendor_support.value != "supported"


def test_reject_wrong_schema_version() -> None:
    raw = _base_entry()
    raw["schema_version"] = "9.9"
    assert CompatErrorCode.E_COMPAT_SCHEMA_VERSION.value in _codes(raw)


def test_reject_wrong_required_steps() -> None:
    raw = _base_entry()
    raw["required_steps"] = _STEPS[:5]
    assert CompatErrorCode.E_COMPAT_REQUIRED_STEPS.value in _codes(raw)


def test_reject_bad_enum_sector() -> None:
    raw = _base_entry()
    raw["sector"] = "banking_not_a_sector"
    assert CompatErrorCode.E_COMPAT_ENUM_INVALID.value in _codes(raw)


def test_reject_bad_route_status() -> None:
    raw = _base_entry()
    raw["routes"][0]["status"] = "totally_working"
    assert CompatErrorCode.E_COMPAT_ENUM_INVALID.value in _codes(raw)


def test_reject_verified_without_tested_at() -> None:
    # METADATA GIẢ: tự nhận technical=verified nhưng tested_at trống.
    raw = _base_entry()
    raw["certification"]["technical_status"] = "verified"
    raw["certification"]["evidence_ids"] = ["ev-1"]  # có evidence nhưng vẫn thiếu tested_at
    assert CompatErrorCode.E_COMPAT_CERT_UNSUPPORTED.value in _codes(raw)


def test_reject_verified_without_evidence() -> None:
    raw = _base_entry()
    raw["certification"]["end_to_end_status"] = "pass"
    raw["certification"]["tested_at"] = "2026-11-03"
    raw["certification"]["evidence_ids"] = []  # thiếu bằng chứng
    assert CompatErrorCode.E_COMPAT_CERT_UNSUPPORTED.value in _codes(raw)


def test_reject_vendor_supported_without_evidence() -> None:
    raw = _base_entry()
    raw["certification"]["vendor_support"] = "supported"
    raw["certification"]["evidence_ids"] = []
    assert CompatErrorCode.E_COMPAT_VENDOR_CLAIM.value in _codes(raw)


def test_reject_revoked_but_route_usable() -> None:
    raw = _base_entry()
    raw["certification"]["revoked"] = True
    raw["routes"][0]["status"] = "workflow_verified"
    assert "E_REVOKED" in _codes(raw)


def test_fully_evidenced_verified_passes_schema() -> None:
    # Có đủ tested_at + evidence_ids → schema CHO qua (còn đúng hay không là
    # việc của gate evidence COMP-049 khi có 7 nấc thật).
    raw = _base_entry()
    raw["certification"]["technical_status"] = "verified"
    raw["certification"]["tested_at"] = "2026-11-03"
    raw["certification"]["evidence_ids"] = ["ev-1", "ev-2"]
    raw["routes"][0]["status"] = "workflow_verified"
    assert validate_workflow_entry(raw).ok
