"""SỰ KIỆN MÁY IN MÔ PHỎNG (simulated) — KHÔNG đụng máy in/máy quét thật.

Khác với mạng (có 2 mã thô NM-NET-001/002 đã code thật trong namios-chan-doan
để test lớp A "real tool"), TOÀN BỘ 6 mã máy in (NM-PRN-000..005) có
`detector: "specified"` — nghĩa là CHƯA có bất kỳ script nào trong repo thực
sự chạy `lpstat`/`lpinfo`/`systemctl is-active cups`/`scanimage -L` để tự
phân loại discovery/backend/queue/device/scan. Vì vậy test ở đây gồm 2 lớp:

  A) ORACLE THAM CHIẾU (`classify_printer_phase`) — hiện thực THUẦN PYTHON
     của bảng quyết định discovery→backend→queue→device→scan ở
     EVENT-ERROR-CONTRACT.md §3.2. Test-only, xem caveat ở sim_network.py
     đầu file (áp dụng y hệt ở đây).

  B) "COMMAND REPLAY" — chạy THẬT literal `command` lấy từ
     `safe_actions[].command` của catalog (khi kind=read-only, an toàn để
     chạy) trong sandbox có lệnh giả, xác nhận lệnh đó thực sự sinh ra đúng
     dạng tín hiệu mà catalog.`needs_evidence` mô tả — đây là cách gần nhất
     để "test tích hợp" catalog mà KHÔNG bịa ra một detector không tồn tại.

Chạy: python3 -m pytest tools/reliability-tests/sim_printer.py -v
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

import pytest

from conftest import FakeBin

# ===========================================================================
# A) ORACLE THAM CHIẾU — discovery → backend → queue → device → scan
# ===========================================================================


@dataclass
class PrinterEvidence:
    """Tín hiệu read-only y hệt cột 'Bằng chứng' ở EVENT-ERROR-CONTRACT.md
    §3.2 / error-codes.md §6.2. `None` = chưa quan sát được."""

    cups_active: bool | None = None  # systemctl is-active cups == active
    any_printer_discovered: bool | None = None  # lpstat -p không trống
    queue_jobs_stuck: bool | None = None  # lpstat -o tồn đọng
    printer_disabled_or_paused: bool | None = None  # lpstat -p disabled/paused
    device_reason: str | None = None  # media-empty|toner-empty|jam|door-open|offline
    scanner_discovered: bool | None = None  # scanimage -L không trống


def classify_printer_phase(ev: PrinterEvidence) -> tuple[str, str]:
    """Oracle THAM CHIẾU (test-only). Thứ tự pipeline ĐÚNG §3.2: discovery →
    backend → queue → device → scan — dừng ở bước ĐẦU TIÊN có bằng chứng
    thất bại. 'backend' (CUPS) là điều kiện NỀN: nếu CUPS không chạy thì
    không thể biết máy in có 'discovery' được hay không (mọi lệnh lpstat sẽ
    không phản hồi đáng tin) — vì vậy backend được kiểm NGAY SAU discovery
    chỉ khi discovery đã xác nhận KHÔNG thấy máy in (tránh báo nhầm discovery
    khi nguyên nhân thật là CUPS chết)."""
    if ev.cups_active is False:
        return ("backend", "NM-PRN-002")
    if ev.any_printer_discovered is False:
        return ("discovery", "NM-PRN-001")
    if ev.device_reason:
        return ("device", "NM-PRN-004")
    if ev.queue_jobs_stuck or ev.printer_disabled_or_paused:
        return ("queue", "NM-PRN-003")
    if ev.scanner_discovered is False:
        return ("scan", "NM-PRN-005")
    if ev.any_printer_discovered is True and ev.cups_active is True:
        return ("ok", "")
    return ("unknown", "NM-PRN-000")


@pytest.mark.parametrize(
    "evidence,expected_phase,expected_code",
    [
        (PrinterEvidence(cups_active=False), "backend", "NM-PRN-002"),
        (PrinterEvidence(any_printer_discovered=False), "discovery", "NM-PRN-001"),
        (PrinterEvidence(device_reason="media-empty"), "device", "NM-PRN-004"),
        (PrinterEvidence(device_reason="jam"), "device", "NM-PRN-004"),
        (PrinterEvidence(queue_jobs_stuck=True), "queue", "NM-PRN-003"),
        (PrinterEvidence(printer_disabled_or_paused=True), "queue", "NM-PRN-003"),
        (PrinterEvidence(scanner_discovered=False), "scan", "NM-PRN-005"),
        (
            PrinterEvidence(any_printer_discovered=True, cups_active=True),
            "ok",
            "",
        ),
    ],
)
def test_oracle_phase_detection(evidence, expected_phase, expected_code):
    phase, code = classify_printer_phase(evidence)
    assert (phase, code) == (expected_phase, expected_code)


def test_oracle_insufficient_evidence_is_unknown_never_fabricated():
    phase, code = classify_printer_phase(PrinterEvidence())
    assert (phase, code) == ("unknown", "NM-PRN-000")


def test_oracle_backend_down_wins_over_discovery_per_contract_note():
    """EVENT-ERROR-CONTRACT.md §7 'Integration bằng sự kiện mô phỏng' ghi rõ:
    'MÁY IN: ... CUPS tắt ⇒ NM-PRN-002' — nghĩa là khi CUPS không chạy, kết
    luận PHẢI là backend (NM-PRN-002), KHÔNG được báo nhầm thành discovery
    (NM-PRN-001) dù lpstat -p cũng sẽ trống/không phản hồi khi CUPS chết."""
    ev = PrinterEvidence(cups_active=False, any_printer_discovered=False)
    phase, code = classify_printer_phase(ev)
    assert (phase, code) == ("backend", "NM-PRN-002")


def test_oracle_outputs_always_match_catalog_phase_and_domain(catalog_data):
    sample_evidences = [
        PrinterEvidence(cups_active=False),
        PrinterEvidence(any_printer_discovered=False),
        PrinterEvidence(device_reason="jam"),
        PrinterEvidence(queue_jobs_stuck=True),
        PrinterEvidence(scanner_discovered=False),
        PrinterEvidence(),
    ]
    for ev in sample_evidences:
        phase, code = classify_printer_phase(ev)
        if phase == "ok":
            continue
        assert code in catalog_data["entries"], f"{code} (phase={phase}) không có trong catalog"
        entry = catalog_data["entries"][code]
        assert entry["phase"] == phase
        assert entry["domain"] == "may_in"


# ===========================================================================
# B) COMMAND REPLAY — chạy THẬT command trong catalog.safe_actions (kind
# read-only) trong sandbox, xác nhận tín hiệu khớp needs_evidence.
# ===========================================================================


def _read_only_command(catalog_data: dict, code: str, action_id: str) -> list[str]:
    entry = catalog_data["entries"][code]
    for a in entry["safe_actions"]:
        if a["id"] == action_id:
            assert a["kind"] == "read-only", f"{code}/{action_id} không phải read-only — không an toàn để replay"
            assert a["command"], f"{code}/{action_id} có command rỗng"
            return a["command"].split(" ")
    raise AssertionError(f"Không thấy action id={action_id} trong {code}")


def test_catalog_scan_command_replay_against_empty_scanner_fixture(catalog_data, fake_bin: FakeBin):
    """NM-PRN-005 (scan) khai needs_evidence 'scanimage -L không liệt kê thiết
    bị' và safe_actions có action read-only 'scan.list' với command
    'scanimage -L'. Chạy THẬT command đó (lấy nguyên văn từ catalog, không
    gõ lại tay) trong sandbox mô phỏng 'không có máy quét' — output phải
    trống, đúng với needs_evidence đã khai."""
    argv = _read_only_command(catalog_data, "NM-PRN-005", "scan.list")
    assert argv == ["scanimage", "-L"]
    fake_bin.add("scanimage", 'if [ "$1" = "-L" ]; then :; fi\nexit 0')  # không in gì — mô phỏng không có máy quét
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env={"PATH": fake_bin.path_env()},
        timeout=5,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "", "Mô phỏng 'không có máy quét' nhưng scanimage -L lại in ra thiết bị"


def test_catalog_scan_command_replay_against_found_scanner_fixture(catalog_data, fake_bin: FakeBin):
    """Đối chứng: khi CÓ máy quét, scanimage -L (vẫn command nguyên văn từ
    catalog) phải in ra thiết bị — tránh oracle/test tự khẳng định 'trống'
    bất kể input (test giả, không kiểm được gì)."""
    argv = _read_only_command(catalog_data, "NM-PRN-005", "scan.list")
    fake_bin.add(
        "scanimage",
        'if [ "$1" = "-L" ]; then printf \'device `airscan:e0:HP LaserJet` is a platform eSCL scanner\\n\'; fi\nexit 0',
    )
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env={"PATH": fake_bin.path_env()},
        timeout=5,
    )
    assert "HP LaserJet" in proc.stdout


def test_catalog_backend_evidence_command_matches_needs_evidence_text(catalog_data, fake_bin: FakeBin):
    """NM-PRN-002 (backend) không có safe_action read-only để replay, nhưng
    needs_evidence[0] trích literal `systemctl is-active cups` — kiểm chuỗi
    lệnh đó đúng là lệnh dùng để quan sát tín hiệu 'CUPS không chạy' bằng
    cách chạy chính lệnh đó (không phải viết lại bằng tay) trong sandbox."""
    entry = catalog_data["entries"]["NM-PRN-002"]
    assert "systemctl is-active cups" in entry["needs_evidence"][0]
    fake_bin.add("systemctl", 'if [ "$1" = "is-active" ] && [ "$2" = "cups" ]; then echo inactive; exit 3; fi\nexit 1')
    proc = subprocess.run(
        ["systemctl", "is-active", "cups"],
        capture_output=True,
        text=True,
        env={"PATH": fake_bin.path_env()},
        timeout=5,
    )
    assert proc.stdout.strip() == "inactive"
    assert proc.returncode != 0
