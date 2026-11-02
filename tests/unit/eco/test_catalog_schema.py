"""ECO-006 — validator tầng 1 (cấu trúc) cho service-catalog entry."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from namios_eco.catalog_schema import build_entry, validate_raw, validate_schema
from namios_eco.models import ServiceEntry
from namios_eco.status import PublishedStatus, WindowsMode

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTRACT_PATH = _REPO_ROOT / "contracts" / "service-catalog.schema.json"


def _valid_raw() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "id": "thue.etax-ca-nhan",
        "provider": "Tổng cục Thuế",
        "agency": "Bộ Tài chính",
        "purpose": "Lập và nộp tờ khai thuế hộ kinh doanh",
        "official_url": "https://thuedientu.gdt.gov.vn/",
        "source_check": "Khớp domain .gov.vn + ngày kiểm 02/11/2026",
        "version": "2026.1",
        "license": "Miễn phí (dịch vụ công)",
        "published_os": ["Windows 10/11"],
        "dependencies": ["USB token ký số"],
        "account_condition": "Cần định danh điện tử mức 2",
        "service_cost": "Miễn phí",
        "data_sensitivity": "tai_chinh",
        "test_profile": "report-thue-001",
        "last_updated": "2026-11-02",
        "evidence_source": "https://thuedientu.gdt.gov.vn/",
        "published_status": "not_inventoried",
        "windows_mode": "web_linux",
        "tested_by_namios": False,
        "officially_supported_by_vendor": False,
    }


def test_contract_file_exists_and_is_valid_json_schema_shape() -> None:
    assert _CONTRACT_PATH.exists()
    schema = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert schema["additionalProperties"] is False
    assert schema["type"] == "object"
    assert set(schema["required"]) == set(_valid_raw().keys())


def test_valid_entry_passes() -> None:
    raw = _valid_raw()
    errors = validate_raw(raw)
    assert errors == [], errors


def test_build_entry_roundtrip() -> None:
    raw = _valid_raw()
    entry = build_entry(raw)
    assert isinstance(entry, ServiceEntry)
    assert entry.id == "thue.etax-ca-nhan"
    assert entry.published_status == PublishedStatus.NOT_INVENTORIED
    assert entry.windows_mode == WindowsMode.WEB_LINUX
    assert entry.published_os == ("Windows 10/11",)


def test_unknown_key_rejected() -> None:
    raw = _valid_raw()
    raw["extra_field_la"] = "khong duoc phep"
    errors = validate_raw(raw)
    assert any(e.code == "E_INPUT_UNKNOWN_KEY" for e in errors)


def test_missing_required_key_rejected() -> None:
    raw = _valid_raw()
    del raw["official_url"]
    errors = validate_raw(raw)
    assert any(e.path == "official_url" for e in errors)


def test_non_object_rejected() -> None:
    errors = validate_raw(["not", "an", "object"])
    assert errors and errors[0].code == "E_INPUT_SCHEMA"


def test_bad_id_pattern_rejected() -> None:
    raw = _valid_raw()
    raw["id"] = "Thue_ETax CaNhan!!"
    errors = validate_raw(raw)
    assert any(e.path == "id" for e in errors)


def test_official_url_without_scheme_rejected() -> None:
    raw = _valid_raw()
    raw["official_url"] = "thuedientu.gdt.gov.vn"
    errors = validate_raw(raw)
    assert any(e.path == "official_url" for e in errors)


def test_official_url_ftp_scheme_rejected() -> None:
    raw = _valid_raw()
    raw["official_url"] = "ftp://thuedientu.gdt.gov.vn/"
    errors = validate_raw(raw)
    assert any(e.path == "official_url" for e in errors)


def test_data_sensitivity_enum_enforced() -> None:
    raw = _valid_raw()
    raw["data_sensitivity"] = "bua-xua"
    errors = validate_raw(raw)
    assert any(e.path == "data_sensitivity" for e in errors)


def test_published_status_enum_enforced() -> None:
    raw = _valid_raw()
    raw["published_status"] = "da_xong"
    errors = validate_raw(raw)
    assert any(e.path == "published_status" for e in errors)


def test_windows_mode_enum_enforced() -> None:
    raw = _valid_raw()
    raw["windows_mode"] = "macos"
    errors = validate_raw(raw)
    assert any(e.path == "windows_mode" for e in errors)


def test_last_updated_bad_format_rejected() -> None:
    raw = _valid_raw()
    raw["last_updated"] = "02/11/2026"
    errors = validate_raw(raw)
    assert any(e.path == "last_updated" for e in errors)


def test_duplicate_dependencies_rejected() -> None:
    raw = _valid_raw()
    raw["dependencies"] = ["USB token", "USB token"]
    errors = validate_raw(raw)
    assert any("trùng" in e.message_vi for e in errors)


def test_boolean_fields_type_enforced() -> None:
    raw = _valid_raw()
    raw["tested_by_namios"] = "yes"
    errors = validate_raw(raw)
    assert any(e.path == "tested_by_namios" for e in errors)


def test_nullable_fields_accept_null() -> None:
    raw = _valid_raw()
    raw["agency"] = None
    raw["version"] = None
    assert validate_raw(raw) == []


def test_validate_schema_wraps_schema_result() -> None:
    result = validate_schema(_valid_raw())
    assert result.ok is True
    assert result.errors == ()

    bad = deepcopy(_valid_raw())
    del bad["id"]
    bad_result = validate_schema(bad)
    assert bad_result.ok is False
    assert bad_result.errors
