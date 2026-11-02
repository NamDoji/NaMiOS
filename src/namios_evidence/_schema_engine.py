"""Validator tầng 1 (cấu trúc) cho ``contracts/evidence-report.schema.json``.

Schema evidence-report CỐ ĐỊNH và biết trước (không phải schema tổng quát
như app-manifest) — nên ở đây viết thẳng các kiểm tra tương ứng từng
trường thay vì dựng một "mini JSON-Schema engine" tổng quát (tránh trùng
lặp không cần thiết với cách làm của WP2, và module ``_schema_engine`` của
WP2 là private — WP9 KHÔNG import chéo vào implementation module khác).

KHÔNG dùng thư viện ngoài (``jsonschema`` không có sẵn trong venv của host
hiện tại; không được ``pip install`` — xem CLAUDE.md môi trường build).
KHÔNG business logic domain (chỉ diễn giải cấu trúc — tầng 1; gate ngữ
nghĩa "task_verified cần evidence" là tầng 2, ở ``_gate.py``).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from namios_core.errors import ErrorCode
from namios_core.validation import ValidationError

__all__ = ["validate_raw"]

_RESULT_ENUM = frozenset({"pass", "fail", "not_run", "skipped", "blocked_external_dependency"})
_DECISION_ENUM = frozenset({"pending", "experimental", "task_verified", "blocked", "revoked"})

_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "report_id",
        "manifest_id",
        "profile_sha256",
        "source_commit",
        "run_started_at",
        "run_finished_at",
        "environment",
        "tests",
        "known_issues",
        "decision",
        "qa_approval",
    }
)
_TOP_LEVEL_REQUIRED = _TOP_LEVEL_KEYS  # tất cả 12 trường đều required trong schema

_ENVIRONMENT_STRING_KEYS = (
    "os_build",
    "kernel",
    "desktop_session",
    "runner_id",
    "application_version",
    "application_build",
    "architecture",
    "hardware_or_vm_profile",
    "test_suite_revision",
    "dataset_revision",
)
_ENVIRONMENT_SHA_KEYS = ("runner_sha256", "application_sha256")
_ENVIRONMENT_KEYS = frozenset(
    {*_ENVIRONMENT_STRING_KEYS, *_ENVIRONMENT_SHA_KEYS, "dependency_versions"}
)
_ENVIRONMENT_REQUIRED = _ENVIRONMENT_KEYS

_TEST_ITEM_KEYS = frozenset(
    {"test_id", "required", "result", "expected", "actual", "evidence_refs", "reason"}
)
_TEST_ITEM_REQUIRED = _TEST_ITEM_KEYS

_QA_APPROVAL_KEYS = frozenset({"reviewer", "approved_at", "approval_reference"})
_QA_APPROVAL_REQUIRED = _QA_APPROVAL_KEYS

_SHA256_HEX_LEN = 64


def _err(code: ErrorCode, path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=code.value, path=path, message_vi=message_vi)


def _is_date_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _check_nullable_string(
    value: Any, path: str, errors: list[ValidationError], *, max_len: int = 512
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or isinstance(value, bool):
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là chuỗi hoặc null."))
        return
    if not (1 <= len(value) <= max_len):
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                path,
                f"'{path}' phải có độ dài 1..{max_len} ký tự.",
            )
        )


def _check_nullable_date_time(value: Any, path: str, errors: list[ValidationError]) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not _is_date_time(value):
        errors.append(
            _err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là chuỗi date-time hoặc null.")
        )


def _check_nullable_sha256(value: Any, path: str, errors: list[ValidationError]) -> None:
    if value is None:
        return
    if (
        not isinstance(value, str)
        or len(value) != _SHA256_HEX_LEN
        or any(c not in "0123456789abcdef" for c in value)
    ):
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                path,
                f"'{path}' phải là chuỗi sha256 hex 64 ký tự thường hoặc null.",
            )
        )


def _check_string_array(
    value: Any,
    path: str,
    errors: list[ValidationError],
    *,
    max_items: int = 100,
    item_max_len: int = 512,
    require_unique: bool = True,
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
        is_bad_string = (
            not isinstance(item, str)
            or isinstance(item, bool)
            or not (1 <= len(item) <= item_max_len)
        )
        if is_bad_string:
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    item_path,
                    f"'{item_path}' phải là chuỗi 1..{item_max_len} ký tự.",
                )
            )
            continue
        if require_unique:
            if item in seen:
                errors.append(
                    _err(ErrorCode.E_INPUT_SCHEMA, item_path, f"'{path}' có phần tử trùng lặp.")
                )
            seen.add(item)


def _check_unknown_and_missing_keys(
    obj: Mapping[str, Any],
    allowed: frozenset[str],
    required: frozenset[str],
    path: str,
    errors: list[ValidationError],
) -> None:
    for key in obj:
        if key not in allowed:
            errors.append(
                _err(
                    ErrorCode.E_INPUT_UNKNOWN_KEY,
                    f"{path}.{key}" if path else key,
                    f"Thuộc tính không xác định '{key}' tại '{path or '$'}'.",
                )
            )
    for key in required:
        if key not in obj:
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    f"{path}.{key}" if path else key,
                    f"Thiếu thuộc tính bắt buộc '{key}' tại '{path or '$'}'.",
                )
            )


def _validate_environment(value: Any, path: str, errors: list[ValidationError]) -> None:
    if not isinstance(value, dict):
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là object."))
        return
    _check_unknown_and_missing_keys(value, _ENVIRONMENT_KEYS, _ENVIRONMENT_REQUIRED, path, errors)
    for key in _ENVIRONMENT_STRING_KEYS:
        if key in value:
            _check_nullable_string(value[key], f"{path}.{key}", errors)
    for key in _ENVIRONMENT_SHA_KEYS:
        if key in value:
            _check_nullable_sha256(value[key], f"{path}.{key}", errors)
    if "dependency_versions" in value:
        _check_string_array(value["dependency_versions"], f"{path}.dependency_versions", errors)


def _validate_test_item(value: Any, path: str, errors: list[ValidationError]) -> None:
    if not isinstance(value, dict):
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là object."))
        return
    _check_unknown_and_missing_keys(value, _TEST_ITEM_KEYS, _TEST_ITEM_REQUIRED, path, errors)
    if "test_id" in value:
        _check_nullable_string(value["test_id"], f"{path}.test_id", errors)
        if value["test_id"] is None:
            errors.append(
                _err(ErrorCode.E_INPUT_SCHEMA, f"{path}.test_id", "'test_id' không được null.")
            )
    if "required" in value and not isinstance(value["required"], bool):
        errors.append(
            _err(ErrorCode.E_INPUT_SCHEMA, f"{path}.required", "'required' phải là boolean.")
        )
    if "result" in value and value["result"] not in _RESULT_ENUM:
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                f"{path}.result",
                f"'result' phải thuộc {sorted(_RESULT_ENUM)}.",
            )
        )
    if "expected" in value:
        _check_nullable_string(value["expected"], f"{path}.expected", errors)
        if value["expected"] is None:
            errors.append(
                _err(ErrorCode.E_INPUT_SCHEMA, f"{path}.expected", "'expected' không được null.")
            )
    if "actual" in value:
        _check_nullable_string(value["actual"], f"{path}.actual", errors)
    if "reason" in value:
        _check_nullable_string(value["reason"], f"{path}.reason", errors)
    if "evidence_refs" in value:
        _check_string_array(value["evidence_refs"], f"{path}.evidence_refs", errors)


def _validate_tests(value: Any, path: str, errors: list[ValidationError]) -> None:
    if not isinstance(value, list):
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là mảng."))
        return
    if len(value) < 1:
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải có ít nhất 1 phần tử."))
    for idx, item in enumerate(value):
        _validate_test_item(item, f"{path}[{idx}]", errors)


def _validate_qa_approval(value: Any, path: str, errors: list[ValidationError]) -> None:
    if not isinstance(value, dict):
        errors.append(_err(ErrorCode.E_INPUT_SCHEMA, path, f"'{path}' phải là object."))
        return
    _check_unknown_and_missing_keys(value, _QA_APPROVAL_KEYS, _QA_APPROVAL_REQUIRED, path, errors)
    if "reviewer" in value:
        _check_nullable_string(value["reviewer"], f"{path}.reviewer", errors)
    if "approved_at" in value:
        _check_nullable_date_time(value["approved_at"], f"{path}.approved_at", errors)
    if "approval_reference" in value:
        _check_nullable_string(value["approval_reference"], f"{path}.approval_reference", errors)


_MANIFEST_ID_ALLOWED = frozenset("abcdefghijklmnopqrstuvwxyz0123456789.-")


def _manifest_id_pattern_ok(value: str) -> bool:
    # ^[a-z0-9]+(?:[.-][a-z0-9]+)*$
    if not value:
        return False
    groups = value.replace(".", "-").split("-")
    if any(g == "" for g in groups):
        return False
    return all(c.isascii() and (c.islower() or c.isdigit()) for g in groups for c in g) and all(
        c in _MANIFEST_ID_ALLOWED for c in value
    )


def validate_raw(raw: Any) -> list[ValidationError]:
    """Thẩm định ``raw`` (JSON đã parse) theo tầng 1 (cấu trúc).

    Trả danh sách lỗi (rỗng nếu hợp lệ). KHÔNG raise — caller quyết định
    cách dùng kết quả."""

    errors: list[ValidationError] = []

    if not isinstance(raw, dict):
        return [_err(ErrorCode.E_INPUT_SCHEMA, "$", "Evidence report phải là object JSON.")]

    _check_unknown_and_missing_keys(raw, _TOP_LEVEL_KEYS, _TOP_LEVEL_REQUIRED, "", errors)

    if "schema_version" in raw and raw["schema_version"] != "1.0":
        errors.append(
            _err(ErrorCode.E_INPUT_SCHEMA, "schema_version", "'schema_version' phải là \"1.0\".")
        )

    if "report_id" in raw:
        _check_nullable_string(raw["report_id"], "report_id", errors)
        if raw["report_id"] is None:
            errors.append(
                _err(ErrorCode.E_INPUT_SCHEMA, "report_id", "'report_id' không được null.")
            )

    if "manifest_id" in raw:
        mid = raw["manifest_id"]
        if not isinstance(mid, str) or len(mid) > 100 or not _manifest_id_pattern_ok(mid):
            errors.append(
                _err(
                    ErrorCode.E_INPUT_SCHEMA,
                    "manifest_id",
                    "'manifest_id' phải khớp mẫu chữ thường/số/.- và tối đa 100 ký tự.",
                )
            )

    if "profile_sha256" in raw:
        _check_nullable_sha256(raw["profile_sha256"], "profile_sha256", errors)
    if "source_commit" in raw:
        _check_nullable_string(raw["source_commit"], "source_commit", errors)
    if "run_started_at" in raw:
        _check_nullable_date_time(raw["run_started_at"], "run_started_at", errors)
    if "run_finished_at" in raw:
        _check_nullable_date_time(raw["run_finished_at"], "run_finished_at", errors)

    if "environment" in raw:
        _validate_environment(raw["environment"], "environment", errors)
    if "tests" in raw:
        _validate_tests(raw["tests"], "tests", errors)
    if "known_issues" in raw:
        _check_string_array(raw["known_issues"], "known_issues", errors)

    if "decision" in raw and raw["decision"] not in _DECISION_ENUM:
        errors.append(
            _err(
                ErrorCode.E_INPUT_SCHEMA,
                "decision",
                f"'decision' phải thuộc {sorted(_DECISION_ENUM)}.",
            )
        )

    if "qa_approval" in raw:
        _validate_qa_approval(raw["qa_approval"], "qa_approval", errors)

    return errors
