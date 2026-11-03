"""Test Tool Broker SmartAI M0 (SAI-015/040/016, Phụ lục 04).

Nghiệm thu: tool lạ bị chặn (T04), schema/scope/capability fail-closed theo
đúng thứ tự, R0 read-only chạy không cần capability, tool ``writes`` LUÔN
cần capability hợp lệ (đúng chủ thể, còn hạn, đủ bậc rủi ro)."""

from __future__ import annotations

from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import (
    CapabilityToken,
    RiskTier,
    ToolCall,
    ToolResultStatus,
)
from namios_smartai.tools import DEFAULT_TOOLS, ToolRegistry


def test_tool_khong_dang_ky_bi_tu_choi() -> None:  # T04
    registry = ToolRegistry()
    result = registry.invoke(ToolCall(tool="rm_rf_home"))
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_UNKNOWN.value


def test_install_test_thieu_source_hash_bi_tu_choi_schema() -> None:
    registry = ToolRegistry()
    result = registry.invoke(ToolCall(tool="install_test", params={}, target="capsule-1"))
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_SCHEMA.value


def test_install_test_co_source_hash_nhung_khong_capability_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="install_test",
        params={"source_hash": "sha256:abc123"},
        target="capsule-1",
    )
    result = registry.invoke(call, capability=None)
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_CAP_SCOPE.value


def test_install_test_voi_capability_r2_hop_le_thanh_cong() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="install_test",
        params={"source_hash": "sha256:abc123"},
        target="capsule-1",
    )
    capability = CapabilityToken(
        token_id="cap-1",
        subject="capsule-1",
        risk_tier=RiskTier.R2,
        expires_at="2099-01-01",
    )
    result = registry.invoke(call, capability=capability, now="2026-01-01")
    assert result.status == ToolResultStatus.SUCCESS
    assert result.error_code is None
    assert result.data["tool"] == "install_test"


def test_install_test_voi_capability_het_han_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="install_test",
        params={"source_hash": "sha256:abc123"},
        target="capsule-1",
    )
    capability = CapabilityToken(
        token_id="cap-2",
        subject="capsule-1",
        risk_tier=RiskTier.R2,
        expires_at="2020-01-01",
    )
    result = registry.invoke(call, capability=capability, now="2026-01-01")
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_CAP_EXPIRED.value


def test_install_test_voi_capability_bi_thu_hoi_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="install_test",
        params={"source_hash": "sha256:abc123"},
        target="capsule-1",
    )
    capability = CapabilityToken(
        token_id="cap-3",
        subject="capsule-1",
        risk_tier=RiskTier.R2,
        revoked=True,
    )
    result = registry.invoke(call, capability=capability)
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_CAP_EXPIRED.value


def test_install_test_voi_capability_chu_the_khac_target_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="install_test",
        params={"source_hash": "sha256:abc123"},
        target="capsule-1",
    )
    capability = CapabilityToken(
        token_id="cap-4",
        subject="capsule-KHAC",
        risk_tier=RiskTier.R2,
    )
    result = registry.invoke(call, capability=capability)
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_CAP_SCOPE.value


def test_install_test_voi_capability_bac_thap_hon_yeu_cau_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="install_test",
        params={"source_hash": "sha256:abc123"},
        target="capsule-1",
    )
    capability = CapabilityToken(
        token_id="cap-5",
        subject="capsule-1",
        risk_tier=RiskTier.R1,  # thấp hơn R2 install_test yêu cầu
    )
    result = registry.invoke(call, capability=capability)
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_CAP_SCOPE.value


def test_open_official_url_ngoai_allowed_urls_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(tool="open_official_url", params={"url": "https://evil.example"})
    result = registry.invoke(call, allowed_urls=("https://chinhphu.vn",))
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_SCOPE.value


def test_open_official_url_trong_allowed_urls_thanh_cong() -> None:
    registry = ToolRegistry()
    call = ToolCall(tool="open_official_url", params={"url": "https://chinhphu.vn"})
    result = registry.invoke(call, allowed_urls=("https://chinhphu.vn",))
    assert result.status == ToolResultStatus.SUCCESS


def test_path_co_dotdot_cho_tool_capsule_scope_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="run_test",
        params={"path": "../../etc/passwd"},
        target="capsule-1",
    )
    result = registry.invoke(call, allowed_paths=("/var/lib/namios/capsules",))
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_SCOPE.value


def test_path_ngoai_allowed_paths_bi_tu_choi() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="run_test",
        params={"path": "/opt/khac/evil.sh"},
        target="capsule-1",
    )
    result = registry.invoke(call, allowed_paths=("/var/lib/namios/capsules",))
    assert result.status == ToolResultStatus.BLOCKED
    assert result.error_code == SaiErrorCode.E_SAI_TOOL_SCOPE.value


def test_path_trong_allowed_paths_thanh_cong() -> None:
    registry = ToolRegistry()
    call = ToolCall(
        tool="run_test",
        params={"path": "/var/lib/namios/capsules/c1/test.sh"},
        target="capsule-1",
    )
    result = registry.invoke(call, allowed_paths=("/var/lib/namios/capsules",))
    assert result.status == ToolResultStatus.SUCCESS


def test_inspect_app_r0_thanh_cong_khong_can_capability() -> None:
    registry = ToolRegistry()
    result = registry.invoke(ToolCall(tool="inspect_app", params={"app_id": "firefox"}))
    assert result.status == ToolResultStatus.SUCCESS
    assert result.error_code is None


def test_default_tools_khop_danh_sach_sai_015() -> None:
    names = {spec.name for spec in DEFAULT_TOOLS}
    assert names == {
        "inspect_app",
        "check_source",
        "preflight",
        "open_official_url",
        "request_vendor_help",
        "run_test",
        "capture_sanitized_log",
        "compare_artifacts",
        "create_capsule",
        "install_test",
        "rollback",
    }


def test_registry_list_sap_xep_theo_ten() -> None:
    registry = ToolRegistry()
    names = [spec.name for spec in registry.list()]
    assert names == sorted(names)
    assert len(names) == len(DEFAULT_TOOLS)


def test_registry_get_tool_la_tra_none() -> None:
    registry = ToolRegistry()
    assert registry.get("khong_ton_tai") is None
    assert registry.get("inspect_app") is not None
