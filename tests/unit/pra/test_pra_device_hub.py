"""PRA-001 — Device Hub: năng lực từng chức năng; in+scan KHÔNG suy ra copy."""

from __future__ import annotations

from namios_pra import (
    DeviceCapability,
    DeviceFunction,
    DeviceFunctionStatus,
    can_copy,
    function_status,
    is_supported,
    untested_message,
)

F = DeviceFunction
S = DeviceFunctionStatus


def _cap(**funcs: DeviceFunctionStatus) -> DeviceCapability:
    return DeviceCapability(
        device_id="d1", model="HP M428", functions={F[k.upper()]: v for k, v in funcs.items()}
    )


def test_untested_by_default() -> None:
    cap = DeviceCapability(device_id="d1", model="Canon")
    for f in DeviceFunction:
        assert function_status(cap, f) is S.UNTESTED
    assert "Chưa kiểm" in untested_message(cap, F.COPY)


def test_print_scan_ok_does_not_imply_copy() -> None:
    # Nghiệm thu PRA-001: in=works + scan=works KHÔNG được coi copy=works.
    cap = _cap(print=S.WORKS, scan=S.WORKS)
    assert is_supported(cap, F.PRINT) is True
    assert is_supported(cap, F.SCAN) is True
    assert can_copy(cap) is False
    assert function_status(cap, F.COPY) is S.UNTESTED


def test_copy_only_when_tested_works() -> None:
    assert can_copy(_cap(copy=S.WORKS)) is True
    assert can_copy(_cap(copy=S.PARTIAL)) is False
    assert can_copy(_cap(copy=S.BLOCKED)) is False


def test_is_supported_strict_works_only() -> None:
    cap = _cap(scan=S.PARTIAL)
    assert is_supported(cap, F.SCAN) is False  # partial ≠ dùng được
