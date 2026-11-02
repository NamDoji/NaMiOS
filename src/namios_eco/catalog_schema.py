"""Validator tầng 1 (cấu trúc) cho ``contracts/service-catalog.schema.json``
(ECO-006). Schema cố định và biết trước — viết thẳng kiểm tra từng trường
(mirror cách làm của ``namios_evidence/_schema_engine.py`` cho
``evidence-report.schema.json``), KHÔNG dùng ``jsonschema`` (không có sẵn
trong venv của host hiện tại — xem CLAUDE.md).

KHÔNG business logic domain (GATE "usable"/evidence/transition là tầng 2 ở
``validator.py``) — ở đây CHỈ diễn giải cấu trúc JSON thô.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from namios_core.errors import ErrorCode
from namios_core.manifest_types import SchemaResult
from namios_core.validation import ValidationError
from namios_eco.models import ServiceEntry
from namios_eco.status import PublishedStatus, WindowsMode

__all__ = ["validate_raw", "validate_schema", "build_entry", "DATA_SENSITIVITY_VALUES"]

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "id",
        "provider",
        "agency",
        "purpose",
        "official_url",
        "source_check",
        "version",
        "license",
        "published_os",
        "dependencies",
        "account_condition",
        "service_cost",
        "data_sensitivity",
        "test_profile",
        "last_updated",
        "evidence_source",
        "published_status",
        "windows_mode",
        "tested_by_namios",
        "officially_supported_by_vendor",
    }
)
_TOP_LEVEL_REQUIRED = _TOP_LEVEL_KEYS  # tất cả đều required trong schema

#: Phải khớp đúng enum ``data_sensitivity`` trong
#: ``contracts/service-catalog.schema.json``.
DATA_SENSITIVITY_VALUES = frozenset(
    {"cong_khai", "noi_bo", "ca_nhan", "tai_chinh", "nhay_cam_nha_nuoc"}
)

_PUBLISHED_STATUS_VALUES = frozenset(s.value for s in PublishedStatus)
_WINDOWS_MODE_VALUES = frozenset(m.value for m in WindowsMode)

_ID_ALLOWED = frozenset("abcdefghijklmnopqrstuvwxyz0123456789.-")


def _err(code: ErrorCode, path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=code.value, path=path, message_vi=message_vi)


def _id_pattern_ok(value: str) -> bool:
    # ^[a-z0-9]+(?:[.-][a-z0-9]+)*$
    if not value:
        return False
    groups = value.replace(".", "-").split("-")
    if any(g == "" for g in groups):
        return False
    return all(c.isascii() and (c.islower() or c.isdigit()) for g in groups for c in g) and all(
        c in _ID_ALLOWED for c in value
    )


def _check_required_string(
    value: Any, path: str, errors: list[ValidationError], *, max_len: int = 512
) -> None:
    if not isinstance(value, str) or isinstance(value, bool) or not (1 <= len(value) <= max_len):
        errors.append(
            _err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là chuỗi 1..{max_len} ký tự.")
        )


def _check_nullable_string(
    value: Any, path: str, errors: list[ValidationError], *, max_len: int = 512
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or isinstance(value, bool) or not (1 <= len(value) <= max_len):
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                path,
                f"'{path}' phải là chuỗi 1..{max_len} ký tự hoặc null.",
            )
        )


def _check_string_array(
    value: Any,
    path: str,
    errors: list[ValidationError],
    *,
    max_items: int,
    item_max_len: int = 200,
) -> None:
    if not isinstance(value, list):
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là mảng."))
        return
    if len(value) > max_items:
        errors.append(
            _err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' vượt số lượng tối đa {max_items}.")
        )
    seen: set[str] = set()
    for idx, item in enumerate(value):
        item_path = f"{path}[{idx}]"
        if (
            not isinstance(item, str)
            or isinstance(item, bool)
            or not (1 <= len(item) <= item_max_len)
        ):
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    item_path,
                    f"'{item_path}' phải là chuỗi 1..{item_max_len} ký tự.",
                )
            )
            continue
        if item in seen:
            errors.append(
                _err(ErrorCode.E_INPUT_SCHEMA, item_path, f"'{path}' có phần tử trùng lặp.")
            )
        seen.add(item)


def _check_unknown_and_missing_keys(obj: Mapping[str, Any], errors: list[ValidationError]) -> None:
    for key in obj:
        if key not in _TOP_LEVEL_KEYS:
            errors.append(
                _err(
                    ErrorCode.E_INPUT_UNKNOWN_KEY,
                    key,
                    f"Thuộc tính không xác định '{key}' — danh bạ ECO-006 KHÔNG có "
                    "trường thực thi/lệnh nào; chỉ các trường metadata đã khai báo.",
                )
            )
    for key in _TOP_LEVEL_REQUIRED:
        if key not in obj:
            errors.append(
                _err(ErrorCode.E_INPUT_SCHEMA, key, f"Thiếu thuộc tính bắt buộc '{key}'.")
            )


def validate_raw(raw: Any) -> list[ValidationError]:
    """Thẩm định ``raw`` (JSON đã parse) theo tầng 1 (cấu trúc).

    Trả danh sách lỗi (rỗng nếu hợp lệ). KHÔNG raise."""

    errors: list[ValidationError] = []

    if not isinstance(raw, dict):
        return [_err(ErrorCode.E_INPUT_SCHEMA, "$", "Service-catalog entry phải là object JSON.")]

    _check_unknown_and_missing_keys(raw, errors)

    if "schema_version" in raw and raw["schema_version"] != "1.0":
        errors.append(
            _err(ErrorCode.E_INPUT_SCHEMA, "schema_version", "'schema_version' phải là \"1.0\".")
        )

    if "id" in raw:
        value = raw["id"]
        if not isinstance(value, str) or len(value) > 100 or not _id_pattern_ok(value):
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    "id",
                    "'id' phải khớp mẫu chữ thường/số/.- và tối đa 100 ký tự.",
                )
            )

    if "provider" in raw:
        _check_required_string(raw["provider"], "provider", errors)
    if "agency" in raw:
        _check_nullable_string(raw["agency"], "agency", errors)
    if "purpose" in raw:
        _check_required_string(raw["purpose"], "purpose", errors, max_len=2000)

    if "official_url" in raw:
        value = raw["official_url"]
        if (
            not isinstance(value, str)
            or len(value) > 2048
            or not (value.startswith("http://") or value.startswith("https://"))
            or len(value) <= len("https://")
        ):
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    "official_url",
                    "'official_url' phải là chuỗi http(s):// hợp lệ, tối đa 2048 ký tự.",
                )
            )

    if "source_check" in raw:
        _check_required_string(raw["source_check"], "source_check", errors, max_len=2000)
    if "version" in raw:
        _check_nullable_string(raw["version"], "version", errors)
    if "license" in raw:
        _check_required_string(raw["license"], "license", errors)
    if "published_os" in raw:
        _check_string_array(raw["published_os"], "published_os", errors, max_items=20)
    if "dependencies" in raw:
        _check_string_array(raw["dependencies"], "dependencies", errors, max_items=50)
    if "account_condition" in raw:
        _check_required_string(raw["account_condition"], "account_condition", errors, max_len=2000)
    if "service_cost" in raw:
        _check_required_string(raw["service_cost"], "service_cost", errors)

    if "data_sensitivity" in raw and raw["data_sensitivity"] not in DATA_SENSITIVITY_VALUES:
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                "data_sensitivity",
                f"'data_sensitivity' phải thuộc {sorted(DATA_SENSITIVITY_VALUES)}.",
            )
        )

    if "test_profile" in raw:
        _check_required_string(raw["test_profile"], "test_profile", errors)

    if "last_updated" in raw:
        value = raw["last_updated"]
        ok = (
            isinstance(value, str)
            and len(value) == 10
            and value[4] == "-"
            and value[7] == "-"
            and value[:4].isdigit()
            and value[5:7].isdigit()
            and value[8:10].isdigit()
        )
        if not ok:
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    "last_updated",
                    "'last_updated' phải là ngày dạng \"YYYY-MM-DD\".",
                )
            )

    if "evidence_source" in raw:
        _check_required_string(raw["evidence_source"], "evidence_source", errors, max_len=2048)

    if "published_status" in raw and raw["published_status"] not in _PUBLISHED_STATUS_VALUES:
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                "published_status",
                f"'published_status' phải thuộc {sorted(_PUBLISHED_STATUS_VALUES)}.",
            )
        )

    if "windows_mode" in raw and raw["windows_mode"] not in _WINDOWS_MODE_VALUES:
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                "windows_mode",
                f"'windows_mode' phải thuộc {sorted(_WINDOWS_MODE_VALUES)}.",
            )
        )

    for bool_key in ("tested_by_namios", "officially_supported_by_vendor"):
        if bool_key in raw and not isinstance(raw[bool_key], bool):
            errors.append(
                _err(ErrorCode.E_INPUT_SCHEMA, bool_key, f"'{bool_key}' phải là boolean.")
            )

    return errors


def validate_schema(raw: Mapping[str, Any]) -> SchemaResult:
    violations = validate_raw(raw)
    return SchemaResult(ok=len(violations) == 0, errors=tuple(violations))


def build_entry(raw: Mapping[str, Any]) -> ServiceEntry:
    """Chuyển JSON đã qua tầng 1 (schema OK) thành ``ServiceEntry``.

    KHÔNG gọi hàm này trên ``raw`` chưa qua ``validate_schema``/``validate_raw``
    — các truy cập dưới đây giả định cấu trúc đã hợp lệ."""

    return ServiceEntry(
        id=raw["id"],
        provider=raw["provider"],
        agency=raw["agency"],
        purpose=raw["purpose"],
        official_url=raw["official_url"],
        source_check=raw["source_check"],
        version=raw["version"],
        license=raw["license"],
        published_os=tuple(raw["published_os"]),
        dependencies=tuple(raw["dependencies"]),
        account_condition=raw["account_condition"],
        service_cost=raw["service_cost"],
        data_sensitivity=raw["data_sensitivity"],
        test_profile=raw["test_profile"],
        last_updated=raw["last_updated"],
        evidence_source=raw["evidence_source"],
        published_status=PublishedStatus(raw["published_status"]),
        windows_mode=WindowsMode(raw["windows_mode"]),
        tested_by_namios=bool(raw["tested_by_namios"]),
        officially_supported_by_vendor=bool(raw["officially_supported_by_vendor"]),
    )
