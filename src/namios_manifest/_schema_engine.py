"""Mini JSON Schema (draft 2020-12 — tập con) dùng nội bộ cho WP2.

KHÔNG dùng thư viện ngoài (``jsonschema`` không có sẵn trong venv của host
hiện tại và WP2 không được phép ``pip install``). Tập con này đủ để diễn
giải ``contracts/app-manifest.schema.json`` (type/const/enum/pattern/
minLength/maxLength/format=date-time/anyOf/object{properties,required,
additionalProperties,maxProperties}/array{items,uniqueItems,maxItems}).

KHÔNG business logic domain (chỉ diễn giải cấu trúc schema thuần — tầng 1).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

__all__ = ["SchemaViolation", "validate_instance"]


@dataclass(frozen=True)
class SchemaViolation:
    """Một vi phạm cấu trúc JSON Schema.

    ``kind`` ∈ {"unknown_key", "structural"} — WP2 dùng để chọn
    ``ErrorCode`` đúng (``E_INPUT_UNKNOWN_KEY`` vs ``E_INPUT_SCHEMA``).
    """

    path: str
    kind: str
    message_vi: str


_TYPE_MAP: Mapping[str, tuple[type, ...]] = {
    "object": (dict,),
    "array": (list, tuple),
    "string": (str,),
    "boolean": (bool,),
    "integer": (int,),
    "number": (int, float),
    "null": (type(None),),
}


def _json_type_ok(expected: str, value: Any) -> bool:
    if expected == "integer":
        # bool là subclass của int trong Python — KHÔNG coi bool là integer.
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    types = _TYPE_MAP.get(expected)
    if types is None:
        return True
    if isinstance(value, bool) and bool not in types:
        return False
    return isinstance(value, types)


def _is_valid_date_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _path_join(base: str, key: str) -> str:
    return f"{base}.{key}" if base else key


def validate_instance(
    schema: Mapping[str, Any], instance: Any, path: str = "$"
) -> list[SchemaViolation]:
    """Thẩm định ``instance`` theo ``schema`` (tập con draft 2020-12).

    Trả danh sách vi phạm (rỗng nếu hợp lệ). KHÔNG raise — caller quyết
    định cách ánh xạ sang ``ErrorCode``/exit code.
    """

    violations: list[SchemaViolation] = []

    if "anyOf" in schema:
        sub_schemas: Sequence[Mapping[str, Any]] = schema["anyOf"]
        for sub in sub_schemas:
            if not validate_instance(sub, instance, path):
                return []
        violations.append(
            SchemaViolation(
                path=path,
                kind="structural",
                message_vi=f"Giá trị tại '{path}' không khớp bất kỳ kiểu cho phép (anyOf).",
            )
        )
        return violations

    if "const" in schema and instance != schema["const"]:
        violations.append(
            SchemaViolation(
                path=path,
                kind="structural",
                message_vi=f"Giá trị tại '{path}' phải đúng bằng hằng số bắt buộc.",
            )
        )
        return violations

    if "enum" in schema and instance not in schema["enum"]:
        violations.append(
            SchemaViolation(
                path=path,
                kind="structural",
                message_vi=f"Giá trị tại '{path}' không thuộc tập enum cho phép.",
            )
        )
        return violations

    expected_type = schema.get("type")
    if expected_type is not None and not _json_type_ok(expected_type, instance):
        violations.append(
            SchemaViolation(
                path=path,
                kind="structural",
                message_vi=f"Giá trị tại '{path}' sai kiểu dữ liệu (cần '{expected_type}').",
            )
        )
        return violations

    if isinstance(instance, str):
        min_len = schema.get("minLength")
        max_len = schema.get("maxLength")
        pattern = schema.get("pattern")
        fmt = schema.get("format")
        if min_len is not None and len(instance) < min_len:
            violations.append(
                SchemaViolation(
                    path=path,
                    kind="structural",
                    message_vi=f"Chuỗi tại '{path}' ngắn hơn độ dài tối thiểu {min_len}.",
                )
            )
        if max_len is not None and len(instance) > max_len:
            violations.append(
                SchemaViolation(
                    path=path,
                    kind="structural",
                    message_vi=f"Chuỗi tại '{path}' dài hơn độ dài tối đa {max_len}.",
                )
            )
        if pattern is not None and re.match(pattern, instance) is None:
            violations.append(
                SchemaViolation(
                    path=path,
                    kind="structural",
                    message_vi=f"Chuỗi tại '{path}' không khớp mẫu pattern bắt buộc.",
                )
            )
        if fmt == "date-time" and not _is_valid_date_time(instance):
            violations.append(
                SchemaViolation(
                    path=path,
                    kind="structural",
                    message_vi=f"Chuỗi tại '{path}' không phải date-time ISO 8601 hợp lệ.",
                )
            )

    if expected_type == "object" or (expected_type is None and isinstance(instance, dict)):
        if not isinstance(instance, dict):
            return violations
        properties: Mapping[str, Any] = schema.get("properties", {})
        required: Sequence[str] = schema.get("required", ())
        additional = schema.get("additionalProperties", True)
        max_props = schema.get("maxProperties")

        for req_key in required:
            if req_key not in instance:
                violations.append(
                    SchemaViolation(
                        path=_path_join(path, req_key),
                        kind="structural",
                        message_vi=(f"Thiếu trường bắt buộc '{req_key}' tại '{path}'."),
                    )
                )

        for key, value in instance.items():
            child_path = _path_join(path, key)
            if key in properties:
                violations.extend(validate_instance(properties[key], value, child_path))
            elif additional is False:
                violations.append(
                    SchemaViolation(
                        path=child_path,
                        kind="unknown_key",
                        message_vi=(f"Thuộc tính '{key}' không được công nhận tại '{path}'."),
                    )
                )
            elif isinstance(additional, Mapping):
                violations.extend(validate_instance(additional, value, child_path))

        if max_props is not None and len(instance) > max_props:
            violations.append(
                SchemaViolation(
                    path=path,
                    kind="structural",
                    message_vi=(f"Đối tượng tại '{path}' có nhiều thuộc tính hơn {max_props}."),
                )
            )

    if expected_type == "array" or (expected_type is None and isinstance(instance, (list, tuple))):
        if not isinstance(instance, (list, tuple)):
            return violations
        items_schema = schema.get("items")
        max_items = schema.get("maxItems")
        unique_items = schema.get("uniqueItems", False)

        if items_schema is not None:
            for idx, item in enumerate(instance):
                violations.extend(validate_instance(items_schema, item, f"{path}[{idx}]"))

        if max_items is not None and len(instance) > max_items:
            violations.append(
                SchemaViolation(
                    path=path,
                    kind="structural",
                    message_vi=(f"Mảng tại '{path}' có nhiều phần tử hơn {max_items}."),
                )
            )

        if unique_items:
            seen: list[Any] = []
            for item in instance:
                if item in seen:
                    violations.append(
                        SchemaViolation(
                            path=path,
                            kind="structural",
                            message_vi=f"Mảng tại '{path}' có phần tử trùng lặp (cần duy nhất).",
                        )
                    )
                    break
                seen.append(item)

    return violations
