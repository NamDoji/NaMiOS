"""Test ``namios_cli.envelope_io`` — ghi JSON envelope + mapper exit code."""

from __future__ import annotations

import io
import json
import uuid

import pytest

from namios_cli.envelope_io import emit_json, envelope_exit_code, new_operation_id
from namios_cli.errors import error_envelope, ok_envelope
from namios_core.errors import ErrorCode
from namios_core.exitcodes import ExitCode


def test_new_operation_id_is_uuid4_hex_and_unique() -> None:
    a = new_operation_id()
    b = new_operation_id()
    assert a != b
    # phải parse được thành uuid hợp lệ (hex, không dấu gạch)
    assert uuid.UUID(hex=a).hex == a
    assert len(a) == 32


def test_emit_json_writes_exactly_one_line() -> None:
    env = ok_envelope(new_operation_id(), {"k": "giá trị có dấu"})
    stream = io.StringIO()
    emit_json(env, stream)
    text = stream.getvalue()
    assert text.endswith("\n")
    assert text.count("\n") == 1
    parsed = json.loads(text)
    assert parsed["status"] == "ok"
    assert parsed["data"] == {"k": "giá trị có dấu"}
    assert parsed["error"] is None
    assert parsed["api_version"] == "1.0"
    assert "operation_id" in parsed
    assert parsed["warnings"] == []


def test_emit_json_preserves_vietnamese_without_escaping() -> None:
    env = ok_envelope(new_operation_id(), {"message": "Đỗ Chí Cường"})
    stream = io.StringIO()
    emit_json(env, stream)
    # ensure_ascii=False => không có dãy \u escape trong output thô
    assert "\\u" not in stream.getvalue()
    assert "Đỗ Chí Cường" in stream.getvalue()


def test_emit_json_error_envelope_has_null_data() -> None:
    env = error_envelope(new_operation_id(), ErrorCode.E_INPUT_SCHEMA, "sai tham số")
    stream = io.StringIO()
    emit_json(env, stream)
    parsed = json.loads(stream.getvalue())
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    assert parsed["error"]["message_vi"] == "sai tham số"


def test_emit_json_never_mixes_with_other_text_in_stream() -> None:
    env = ok_envelope(new_operation_id(), None)
    stream = io.StringIO()
    emit_json(env, stream)
    # một lệnh --json chỉ gọi emit_json đúng 1 lần => đúng 1 object parse được
    json.loads(stream.getvalue())


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (ErrorCode.E_INPUT_SCHEMA, ExitCode.INPUT),
        (ErrorCode.E_SEMANTIC_DEPENDENCY, ExitCode.DEPENDENCY),
        (ErrorCode.E_HASH_MISMATCH, ExitCode.NETWORK),
        (ErrorCode.E_PERMISSION_DENIED, ExitCode.PERMISSION),
        (ErrorCode.E_STATE_CONFLICT, ExitCode.CONFLICT),
        (ErrorCode.E_CANCELLED, ExitCode.CANCELLED),
        (ErrorCode.E_POSTCHECK_FAILED, ExitCode.VERIFY),
        (ErrorCode.E_INTERNAL, ExitCode.INTERNAL),
    ],
)
def test_envelope_exit_code_matches_table_for_every_branch(
    code: ErrorCode, expected: ExitCode
) -> None:
    env = error_envelope(new_operation_id(), code, "x")
    assert envelope_exit_code(env) == expected


def test_envelope_exit_code_ok_is_always_zero() -> None:
    env = ok_envelope(new_operation_id(), {"anything": 1})
    assert envelope_exit_code(env) == ExitCode.OK
    assert int(envelope_exit_code(env)) == 0
