"""Test read-only OS adapters nối qua Tool Broker (ADR-0021, M4 backbone).

Hai lớp kiểm:
  (A) PARSE thuần tuý trên fixture CLI đã bắt sẵn (nmcli/lpstat/rfkill/bluetoothctl);
  (B) đường BROKER đầy đủ của ``run_adapter``: policy gate → registry fail-closed →
      lệnh khả dụng → chạy (runner tiêm fixture) → parse → REDACT → Trace → ToolResult,
      + đường ``tool_unavailable`` khi CLI vắng + guard read-only (ghi/đặc quyền bị chặn).
"""

from __future__ import annotations

from pathlib import Path

from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import RiskTier, ToolResultStatus, ToolSpec
from namios_smartai.adapters import (
    ADAPTER_TOOLS,
    ADAPTERS_BY_NAME,
    CommandResult,
    ReadOnlyAdapter,
    build_adapter_registry,
    parse_bluetoothctl_show,
    parse_lpstat,
    parse_nmcli_devices,
    parse_rfkill,
    run_adapter,
)
from namios_smartai.observability import Trace
from namios_smartai.tools import DEFAULT_TOOLS, ToolRegistry

_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "smartai"


def _fixture(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


def _runner_from(text: str, *, returncode: int = 0, stderr: str = ""):
    """Runner giả: trả fixture, KHÔNG đụng OS (chạy toàn bộ đường broker)."""

    def _run(argv: tuple[str, ...], timeout_s: int) -> CommandResult:
        return CommandResult(returncode, text, stderr)

    return _run


# --- (A) PARSE thuần tuý ------------------------------------------------------
def test_parse_nmcli_devices_bo_loopback_va_phat_hien_online() -> None:
    data = parse_nmcli_devices(_fixture("nmcli_device.txt"))
    assert data["online"] is True
    assert data["device_count"] == 2  # wifi + ethernet; loopback bị loại
    devices = data["devices"]
    assert {d["device"] for d in devices} == {"wlp2s0", "enp3s0"}
    wifi = next(d for d in devices if d["device"] == "wlp2s0")
    assert wifi["state"] == "connected"
    assert wifi["connection"] == "PhongHop-5G"


def test_parse_lpstat_may_in_va_default() -> None:
    data = parse_lpstat(_fixture("lpstat.txt"))
    assert data["printer_count"] == 3
    assert data["default"] == "HP_LaserJet_P1102"
    by_name = {p["name"]: p["state"] for p in data["printers"]}
    assert by_name["HP_LaserJet_P1102"] == "idle"
    assert by_name["Canon_MF3010"] == "printing"
    assert by_name["Old_Samsung"] == "disabled"


def test_parse_rfkill_soft_hard_block() -> None:
    data = parse_rfkill(_fixture("rfkill.txt"))
    assert data["radio_count"] == 2
    assert data["any_blocked"] is True  # Bluetooth soft-blocked
    bt = next(r for r in data["radios"] if r["type"] == "Bluetooth")
    assert bt["soft_blocked"] is True
    assert bt["hard_blocked"] is False
    wifi = next(r for r in data["radios"] if r["type"] == "Wireless LAN")
    assert wifi["soft_blocked"] is False


def test_parse_bluetoothctl_show() -> None:
    data = parse_bluetoothctl_show(_fixture("bluetoothctl_show.txt"))
    assert data["controller"] == "AA:BB:CC:DD:EE:FF"  # raw trước redact
    assert data["powered"] is True
    assert data["discoverable"] is False
    assert data["pairable"] is True


# --- (B) đường BROKER đầy đủ ---------------------------------------------------
def test_run_adapter_network_happy_path_tra_bang_chung() -> None:
    adapter = ADAPTERS_BY_NAME["network.diagnose"]
    trace = Trace()
    result = run_adapter(
        adapter, runner=_runner_from(_fixture("nmcli_device.txt")), trace=trace
    )
    assert result.status is ToolResultStatus.SUCCESS
    assert result.error_code is None
    assert result.data["mock"] is False
    assert result.data["online"] is True
    assert result.data["evidence"] == {"online": True, "device_count": 2}
    # Trace ghi 1 mốc success (SAI-034).
    events = trace.events()
    assert events[-1].result == "success"
    assert events[-1].tool == "network.diagnose"


def test_run_adapter_bluetooth_redact_mac() -> None:
    adapter = ADAPTERS_BY_NAME["bluetooth.status"]
    result = run_adapter(
        adapter, runner=_runner_from(_fixture("bluetoothctl_show.txt"))
    )
    assert result.status is ToolResultStatus.SUCCESS
    # MAC bộ điều khiển PHẢI bị che (SAI-024) — không rò ra ngoài tiến trình.
    assert result.data["controller"] == "[REDACTED-MAC]"
    assert "AA:BB:CC:DD:EE:FF" not in str(result.data)
    assert result.data["powered"] is True


def test_run_adapter_tool_unavailable_khi_thieu_cli() -> None:
    # KHÔNG tiêm runner ⇒ kiểm shutil.which; các CLI không có trong sandbox này.
    adapter = ADAPTERS_BY_NAME["printer.status"]
    result = run_adapter(adapter)
    assert result.status is ToolResultStatus.FAILED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_UNAVAILABLE.value
    assert result.data["tool_unavailable"] is True
    assert result.data["command"] == "lpstat"


def test_run_adapter_returncode_khac_0_la_failed_khong_bia() -> None:
    adapter = ADAPTERS_BY_NAME["radio.status"]
    result = run_adapter(
        adapter, runner=_runner_from("", returncode=1, stderr="rfkill: cannot open")
    )
    assert result.status is ToolResultStatus.FAILED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_UNAVAILABLE.value
    # KHÔNG có "evidence" bịa khi lệnh lỗi.
    assert "evidence" not in result.data


def test_run_adapter_broker_fail_closed_tool_chua_dang_ky() -> None:
    # Registry KHÔNG chứa spec adapter ⇒ broker chặn (E_SAI_TOOL_UNKNOWN) TRƯỚC khi chạy.
    adapter = ADAPTERS_BY_NAME["network.diagnose"]
    result = run_adapter(
        adapter,
        registry=ToolRegistry(specs=DEFAULT_TOOLS),  # thiếu ADAPTER_TOOLS
        runner=_runner_from(_fixture("nmcli_device.txt")),
    )
    assert result.status is ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_UNKNOWN.value


def test_run_adapter_guard_tu_choi_adapter_khong_read_only() -> None:
    # Phòng thủ chiều sâu: adapter có spec GHI (writes/R2) KHÔNG được đi đường đọc.
    bad = ReadOnlyAdapter(
        tool="network.radio_on",
        summary_vi="(sai cấu hình) bật radio = GHI",
        spec=ToolSpec(name="network.radio_on", risk=RiskTier.R2, writes=True),
        command=("nmcli", "radio", "wifi", "on"),
        parse=lambda _text: {},
    )
    result = run_adapter(bad, runner=_runner_from("ok"))
    assert result.status is ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_SCOPE.value


def test_adapter_tools_khong_lam_ban_default_tools() -> None:
    # Bất biến: DEFAULT_TOOLS (M0) giữ nguyên; adapter nằm ở registry riêng.
    default_names = {s.name for s in DEFAULT_TOOLS}
    adapter_names = {s.name for s in ADAPTER_TOOLS}
    assert default_names.isdisjoint(adapter_names)
    registry = build_adapter_registry()
    assert registry.get("network.diagnose") is not None
    assert registry.get("install_test") is not None  # M0 vẫn còn
    # Mọi adapter spec là read-only (writes=False, R0/R1).
    for spec in ADAPTER_TOOLS:
        assert spec.writes is False
        assert spec.risk in (RiskTier.R0, RiskTier.R1)
