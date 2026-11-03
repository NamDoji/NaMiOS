"""Test COMP-032 (kèm COMP-036) cho ``namios_compat.device_registry``.

Trọng tâm nghiệm thu: "thiết bị cùng hãng khác model KHÔNG tự được công
nhận" (no-carryover) — xem ``test_capability_by_model_refuses_carryover_*``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from namios_compat._types import DeviceClass, DeviceEntry, DeviceProtocol, TechnicalStatus
from namios_compat.device_registry import DeviceRegistry, load_devices

_FIXTURE_PATH = "fixtures/compat/devices/sample_devices.json"


def _printer_verified(
    device_id: str = "dev.printer.hp_m404dn",
    vendor: str = "HP",
    model: str = "HP LaserJet Pro M404dn",
) -> DeviceEntry:
    return DeviceEntry(
        device_id=device_id,
        device_class=DeviceClass.PRINTER,
        vendor=vendor,
        model=model,
        protocol=DeviceProtocol.IPP,
        linux_mechanism="driverless qua IPP Everywhere (CUPS).",
        tested_functions=("print_a4", "duplex", "print_pdf"),
        vid="03F0",
        pid="4A2A",
        status=TechnicalStatus.VERIFIED,
        evidence_ids=("EV-DEV-0001",),
    )


def _printer_untested_same_vendor() -> DeviceEntry:
    return DeviceEntry(
        device_id="dev.printer.hp_m15w",
        device_class=DeviceClass.PRINTER,
        vendor="HP",
        model="HP LaserJet M15w",
        protocol=DeviceProtocol.IPP_OVER_USB,
        linux_mechanism="chưa thử.",
        tested_functions=(),
        vid="03F0",
        pid="6B2A",
        status=TechnicalStatus.NOT_INVENTORIED,
    )


# --- register / get / list -------------------------------------------------


def test_register_get_roundtrip() -> None:
    registry = DeviceRegistry()
    entry = _printer_verified()

    registry.register(entry)

    assert registry.get(entry.device_id) == entry


def test_get_unknown_device_returns_none() -> None:
    registry = DeviceRegistry()

    assert registry.get("khong-ton-tai") is None


def test_register_duplicate_id_raises_value_error() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    with pytest.raises(ValueError):
        registry.register(_printer_verified())


def test_list_filters_by_device_class_and_is_sorted() -> None:
    registry = DeviceRegistry()
    printer = _printer_verified()
    other_printer = _printer_untested_same_vendor()
    scanner = DeviceEntry(
        device_id="dev.scanner.canon_lide300",
        device_class=DeviceClass.SCANNER,
        vendor="Canon",
        model="CanoScan LiDE 300",
        protocol=DeviceProtocol.SANE,
        linux_mechanism="SANE backend genesys.",
        tested_functions=("scan_a4_300dpi",),
        status=TechnicalStatus.PARTIAL,
    )
    # Đăng ký không theo thứ tự alphabet để kiểm tra list() tự sort.
    registry.register(scanner)
    registry.register(other_printer)
    registry.register(printer)

    all_entries = registry.list()
    assert [e.device_id for e in all_entries] == sorted(e.device_id for e in all_entries)
    assert len(all_entries) == 3

    printers = registry.list(device_class=DeviceClass.PRINTER)
    assert {e.device_id for e in printers} == {printer.device_id, other_printer.device_id}

    scanners = registry.list(device_class=DeviceClass.SCANNER)
    assert scanners == (scanner,)


def test_list_empty_registry_is_empty_tuple() -> None:
    registry = DeviceRegistry()

    assert registry.list() == ()


# --- capability_for ---------------------------------------------------------


def test_capability_for_true_only_for_tested_function_on_verified_model() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    ok, reason = registry.capability_for("dev.printer.hp_m404dn", "print_a4")

    assert ok is True
    assert reason  # non-empty
    assert "print_a4" in reason or "HP LaserJet Pro M404dn" in reason


def test_capability_for_false_for_untested_function_on_known_device() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    ok, reason = registry.capability_for("dev.printer.hp_m404dn", "scan_fax")

    assert ok is False
    assert reason


def test_capability_for_false_when_status_not_verified_even_if_function_listed() -> None:
    registry = DeviceRegistry()
    partial_entry = DeviceEntry(
        device_id="dev.scanner.partial",
        device_class=DeviceClass.SCANNER,
        vendor="Canon",
        model="CanoScan LiDE 300",
        protocol=DeviceProtocol.SANE,
        linux_mechanism="SANE backend genesys.",
        tested_functions=("scan_a4_300dpi",),
        status=TechnicalStatus.PARTIAL,
    )
    registry.register(partial_entry)

    ok, reason = registry.capability_for("dev.scanner.partial", "scan_a4_300dpi")

    assert ok is False
    assert reason


def test_capability_for_unregistered_device_returns_false() -> None:
    registry = DeviceRegistry()

    ok, reason = registry.capability_for("khong-ton-tai", "print_a4")

    assert ok is False
    assert reason


# --- capability_by_model: NO-CARRYOVER (nghiệm thu chính COMP-032) --------


def test_capability_by_model_ok_for_exact_tested_model() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    ok, reason = registry.capability_by_model("HP", "HP LaserJet Pro M404dn", "duplex")

    assert ok is True
    assert reason


def test_capability_by_model_refuses_carryover_same_vendor_other_model_tested() -> None:
    """Nghiệm thu COMP-032: hãng đã có model KHÁC được test (verified) —
    model chưa test riêng vẫn PHẢI bị từ chối, không suy diễn chéo."""

    registry = DeviceRegistry()
    registry.register(_printer_verified())
    registry.register(_printer_untested_same_vendor())

    ok, reason = registry.capability_by_model("HP", "HP LaserJet M15w", "print_a4")

    assert ok is False
    assert reason
    assert "HP LaserJet M15w" in reason or "HP" in reason


def test_capability_by_model_refuses_when_vendor_entirely_unknown() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    ok, reason = registry.capability_by_model("Epson", "Epson L3250", "print_a4")

    assert ok is False
    assert reason


def test_capability_by_model_vendor_match_is_case_insensitive() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    ok, _reason = registry.capability_by_model("hp", "HP LASERJET PRO M404DN", "print_a4")

    assert ok is True


# --- lookup_vid_pid ----------------------------------------------------------


def test_lookup_vid_pid_exact_match() -> None:
    registry = DeviceRegistry()
    entry = _printer_verified()
    registry.register(entry)
    registry.register(_printer_untested_same_vendor())

    matches = registry.lookup_vid_pid("03F0", "4A2A")

    assert matches == (entry,)


def test_lookup_vid_pid_case_insensitive_and_no_match_returns_empty() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())

    matches = registry.lookup_vid_pid("03f0", "4a2a")
    assert len(matches) == 1

    no_matches = registry.lookup_vid_pid("FFFF", "0000")
    assert no_matches == ()


def test_lookup_vid_pid_can_return_multiple_entries() -> None:
    registry = DeviceRegistry()
    entry_a = _printer_verified(device_id="dev.printer.a")
    entry_b = DeviceEntry(
        device_id="dev.printer.b",
        device_class=DeviceClass.PRINTER,
        vendor="HP",
        model="HP LaserJet Pro M404dn (hàng thứ 2 cùng model)",
        protocol=DeviceProtocol.IPP,
        linux_mechanism="driverless qua IPP Everywhere (CUPS).",
        tested_functions=("print_a4",),
        vid="03F0",
        pid="4A2A",
        status=TechnicalStatus.VERIFIED,
    )
    registry.register(entry_a)
    registry.register(entry_b)

    matches = registry.lookup_vid_pid("03F0", "4A2A")

    assert set(matches) == {entry_a, entry_b}


# --- load_devices ------------------------------------------------------------


def test_load_devices_from_sample_fixture_loads_all_entries() -> None:
    entries = load_devices(_FIXTURE_PATH)

    assert len(entries) == 5
    assert all(isinstance(e, DeviceEntry) for e in entries)
    device_ids = {e.device_id for e in entries}
    assert "dev.printer.hp_m404dn" in device_ids
    assert "dev.printer.hp_m15w" in device_ids

    # Entries thật nạp được vào registry và tái lập hành vi no-carryover.
    registry = DeviceRegistry()
    for entry in entries:
        registry.register(entry)
    ok, _reason = registry.capability_by_model("HP", "HP LaserJet M15w", "print_a4")
    assert ok is False


def test_load_devices_tolerates_missing_optional_fields(tmp_path: Path) -> None:
    data = [
        {
            "device_id": "dev.minimal.printer",
            "device_class": "printer",
            "vendor": "Acme",
            "model": "Acme Printer One",
            "protocol": "ipp",
            "linux_mechanism": "driverless.",
        }
    ]
    minimal_path = tmp_path / "minimal.json"
    minimal_path.write_text(json.dumps(data), encoding="utf-8")

    entries = load_devices(str(minimal_path))

    assert len(entries) == 1
    entry = entries[0]
    assert entry.tested_functions == ()
    assert entry.evidence_ids == ()
    assert entry.vid is None
    assert entry.status == TechnicalStatus.NOT_INVENTORIED
    assert entry.notes_vi == ""


def test_load_devices_bad_enum_value_raises_value_error(tmp_path: Path) -> None:
    data = [
        {
            "device_id": "dev.bad.enum",
            "device_class": "may_in",  # giá trị không hợp lệ (không phải "printer")
            "vendor": "Acme",
            "model": "Acme Printer One",
            "protocol": "ipp",
            "linux_mechanism": "driverless.",
        }
    ]
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError):
        load_devices(str(bad_path))


def test_load_devices_missing_required_field_raises_value_error(tmp_path: Path) -> None:
    data = [
        {
            "device_id": "dev.missing.vendor",
            "device_class": "printer",
            # "vendor" thiếu.
            "model": "Acme Printer One",
            "protocol": "ipp",
            "linux_mechanism": "driverless.",
        }
    ]
    bad_path = tmp_path / "missing.json"
    bad_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError):
        load_devices(str(bad_path))


def test_load_devices_top_level_not_array_raises_value_error(tmp_path: Path) -> None:
    bad_path = tmp_path / "not_array.json"
    bad_path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

    with pytest.raises(ValueError):
        load_devices(str(bad_path))


# --- reason strings are Vietnamese / non-empty ------------------------------


def test_all_reason_strings_are_non_empty_and_vietnamese_flavoured() -> None:
    registry = DeviceRegistry()
    registry.register(_printer_verified())
    registry.register(_printer_untested_same_vendor())

    _, ok_reason = registry.capability_for("dev.printer.hp_m404dn", "print_a4")
    _, untested_reason = registry.capability_for("dev.printer.hp_m404dn", "scan_fax")
    _, carryover_reason = registry.capability_by_model("HP", "HP LaserJet M15w", "print_a4")

    for reason in (ok_reason, untested_reason, carryover_reason):
        assert isinstance(reason, str)
        assert reason.strip() != ""

    # Dấu hiệu tiếng Việt (có dấu) — tránh hồi quy âm thầm đổi sang tiếng Anh.
    assert any(ch in carryover_reason for ch in "ăâđêôơưàằầậèềẹìịòồộùừựỳ")
