"""SỰ KIỆN BLUETOOTH MÔ PHỎNG (simulated) — KHÔNG đụng thiết bị BT thật.

Giống máy in: cả 5 mã NM-BT-000..004 có `detector: "specified"` (BT-001..003
ghi rõ "ở namios-ket-noi-thiet-bi, chưa gắn mã"; BT-004 "chưa gắn mã") — chưa
có script nào trong repo tự phân loại discover/pair/profile/service. Test ở
đây dùng ORACLE THAM CHIẾU (test-only, xem caveat đầy đủ ở đầu sim_network.py)
cho bảng quyết định discover→pair→profile→service, VỚI quy tắc đặc biệt của
Bluetooth: `service` là ĐIỀU KIỆN NỀN kiểm TRƯỚC — nếu bluetoothd không chạy
thì KHÔNG được gán discover/pair/profile (EVENT-ERROR-CONTRACT.md §3.3 "Lưu ý
thứ tự"). Đây là bài test quan trọng nhất của file này.

Chạy: python3 -m pytest tools/reliability-tests/sim_bluetooth.py -v
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

import pytest

from conftest import FakeBin


@dataclass
class BtEvidence:
    """Tín hiệu read-only y hệt cột 'Bằng chứng' ở EVENT-ERROR-CONTRACT.md
    §3.3 / error-codes.md §6.3."""

    bluetoothd_active: bool | None = None  # systemctl is-active bluetooth == active
    bluetoothctl_missing: bool | None = None  # thiếu lệnh bluetoothctl (chưa cài bluez)
    adapter_powered: bool | None = None  # bluetoothctl show: Powered=yes/no
    rfkill_blocked: bool | None = None
    device_found_in_scan: bool | None = None
    pairing_failed: bool | None = None
    paired_but_profile_missing: bool | None = None  # Connected=yes, không có card BT trong pactl


def classify_bt_phase(ev: BtEvidence) -> tuple[str, str]:
    """Oracle THAM CHIẾU (test-only). BẤT BIẾN BẮT BUỘC: `service` kiểm
    TRƯỚC TIÊN — service hỏng thì KHÔNG định vị được discover/pair/profile
    (§3.3 'Lưu ý thứ tự'). Sau service, thứ tự còn lại: discover → pair →
    profile."""
    if ev.bluetoothd_active is False or ev.bluetoothctl_missing is True:
        return ("service", "NM-BT-004")
    if ev.adapter_powered is False or ev.rfkill_blocked or ev.device_found_in_scan is False:
        return ("discover", "NM-BT-001")
    if ev.pairing_failed:
        return ("pair", "NM-BT-002")
    if ev.paired_but_profile_missing:
        return ("profile", "NM-BT-003")
    return ("unknown", "NM-BT-000")


@pytest.mark.parametrize(
    "evidence,expected_phase,expected_code",
    [
        (BtEvidence(bluetoothd_active=False), "service", "NM-BT-004"),
        (BtEvidence(bluetoothctl_missing=True), "service", "NM-BT-004"),
        (BtEvidence(adapter_powered=False), "discover", "NM-BT-001"),
        (BtEvidence(rfkill_blocked=True), "discover", "NM-BT-001"),
        (BtEvidence(device_found_in_scan=False), "discover", "NM-BT-001"),
        (BtEvidence(pairing_failed=True), "pair", "NM-BT-002"),
        (BtEvidence(paired_but_profile_missing=True), "profile", "NM-BT-003"),
    ],
)
def test_oracle_phase_detection(evidence, expected_phase, expected_code):
    phase, code = classify_bt_phase(evidence)
    assert (phase, code) == (expected_phase, expected_code)


def test_oracle_insufficient_evidence_is_unknown_never_fabricated():
    phase, code = classify_bt_phase(BtEvidence())
    assert (phase, code) == ("unknown", "NM-BT-000")


def test_oracle_service_down_gates_discover_pair_profile():
    """BÀI TEST TRỌNG TÂM của file: dù có ĐẦY ĐỦ bằng chứng pairing thất bại
    (trông như NM-BT-002), nếu bluetoothd KHÔNG chạy thì kết luận PHẢI là
    NM-BT-004 (service), KHÔNG ĐƯỢC gán pair/discover/profile — vì mọi dấu
    hiệu discover/pair/profile đều KHÔNG đáng tin khi service nền đã hỏng
    (§3.3 'nếu service hỏng thì không định vị được discover/pair/profile')."""
    ev = BtEvidence(
        bluetoothd_active=False,
        adapter_powered=True,
        device_found_in_scan=True,
        pairing_failed=True,
    )
    phase, code = classify_bt_phase(ev)
    assert (phase, code) == ("service", "NM-BT-004"), (
        "Service down phải THẮNG mọi tín hiệu pair/discover/profile khác — "
        f"nhưng oracle trả ({phase}, {code})"
    )


def test_oracle_service_down_gates_even_with_profile_evidence():
    ev = BtEvidence(bluetoothd_active=False, paired_but_profile_missing=True)
    phase, code = classify_bt_phase(ev)
    assert (phase, code) == ("service", "NM-BT-004")


def test_oracle_outputs_always_match_catalog_phase_and_domain(catalog_data):
    sample_evidences = [
        BtEvidence(bluetoothd_active=False),
        BtEvidence(bluetoothctl_missing=True),
        BtEvidence(adapter_powered=False),
        BtEvidence(pairing_failed=True),
        BtEvidence(paired_but_profile_missing=True),
        BtEvidence(),
    ]
    for ev in sample_evidences:
        phase, code = classify_bt_phase(ev)
        assert code in catalog_data["entries"], f"{code} (phase={phase}) không có trong catalog"
        entry = catalog_data["entries"][code]
        assert entry["phase"] == phase
        assert entry["domain"] == "bluetooth"


def test_catalog_delegates_bt_playbooks_to_ket_noi_thiet_bi(catalog_data):
    """error-codes.md §6.3 ghi: khắc phục Bluetooth được UỶ cho
    `namios-ket-noi-thiet-bi` (U13-06) — namios-smartai không tự cài lại logic
    pair/scan. Xác nhận MỌI mã NM-BT-* (trừ sentinel đã launch thẳng công cụ
    đó) có playbook='delegate_ket_noi' hoặc action nào đó launch
    `bluedevil-wizard`/`namios-ket-noi-thiet-bi` — không có action nào tự
    nhận 'đã pair xong' kiểu state-change không qua uỷ quyền."""
    for code, entry in catalog_data["entries"].items():
        if not code.startswith("NM-BT-"):
            continue
        playbooks = {a["playbook"] for a in entry["safe_actions"]}
        assert "delegate_ket_noi" in playbooks, (
            f"{code}: không action nào trỏ playbook='delegate_ket_noi' (playbooks={playbooks})"
        )


# ---------------------------------------------------------------------------
# Command replay cho NM-BT-004 (service) — needs_evidence trích literal
# `systemctl is-active bluetooth`.
# ---------------------------------------------------------------------------


def test_catalog_service_evidence_command_replay(catalog_data, fake_bin: FakeBin):
    entry = catalog_data["entries"]["NM-BT-004"]
    assert "systemctl is-active bluetooth" in entry["needs_evidence"][0]
    fake_bin.add(
        "systemctl",
        'if [ "$1" = "is-active" ] && [ "$2" = "bluetooth" ]; then echo inactive; exit 3; fi\nexit 1',
    )
    proc = subprocess.run(
        ["systemctl", "is-active", "bluetooth"],
        capture_output=True,
        text=True,
        env={"PATH": fake_bin.path_env()},
        timeout=5,
    )
    assert proc.stdout.strip() == "inactive"
    assert proc.returncode != 0
