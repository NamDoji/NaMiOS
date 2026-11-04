"""SAI-006/007/008/009 — chẩn đoán tổng hợp: trung thực, tái dùng COMP-025,
không tự nhận 'đã sửa'/'native' sai."""

from __future__ import annotations

from namios_compat._types import (
    AppRef,
    Certification,
    ResolveInput,
    Route,
    Sector,
    TechnicalStatus,
    WorkflowEntry,
)
from namios_eco.status import PublishedStatus, WindowsMode
from namios_eco.workflow import WORKFLOW_STEP_ORDER
from namios_smartai._types import DepKind, DepNode, ErrorCategory, NodeStatus, TriageInput
from namios_smartai.depgraph import build_graph
from namios_smartai.diagnose import diagnose


def _entry(
    mode: WindowsMode, status: PublishedStatus, *, app_version: str = "1.0"
) -> WorkflowEntry:
    return WorkflowEntry(
        schema_version="1.0",
        workflow_id="w",
        sector=Sector.TAX,
        provider_id="p",
        region_scope="r",
        app=AppRef(id="a", version=app_version, architecture="x86_64"),
        required_steps=tuple(WORKFLOW_STEP_ORDER),
        requires=(),
        routes=(Route(mode=mode, status=status.value),),
        certification=Certification(technical_status=TechnicalStatus.VERIFIED),
        last_updated="2026-11-04",
    )


def test_blocked_plugin_suggests_vendor_no_route() -> None:
    g = build_graph(
        "vn.public_admin.dvc",
        (DepNode("sqlserver", DepKind.DATABASE, NodeStatus.UNKNOWN, required=True),),
    )
    d = diagnose(
        "vn.public_admin.dvc",
        triage_input=TriageInput(log_text="needs ActiveX signing plugin, Windows only"),
        graph=g,
    )
    assert d.triage is not None and d.triage.category == ErrorCategory.PORTAL_PLUGIN
    assert d.execute_blocked is True
    assert d.route_no_verified is True
    assert "vendor" in d.suggested_action_vi.lower() or "báo cáo" in d.suggested_action_vi.lower()


def test_verified_wine_route_recommended() -> None:
    entry = _entry(WindowsMode.WINE, PublishedStatus.WORKFLOW_VERIFIED, app_version="2.0")
    inp = ResolveInput(workflow_id="w", app_id="a", app_version="2.0", license_ok=True)
    d = diagnose("w", entry=entry, resolve_input=inp)
    assert d.route_recommended == "wine"
    assert d.route_no_verified is False
    assert "wine" in d.suggested_action_vi.lower()


def test_dotnet_label_does_not_force_native() -> None:
    # Entry chỉ có route WINE verified (không có native verified) → dù "thấy .NET",
    # resolver KHÔNG đề xuất native_linux (SAI-008).
    entry = _entry(WindowsMode.WINE, PublishedStatus.WORKFLOW_VERIFIED, app_version="1.0")
    inp = ResolveInput(workflow_id="w", app_id="a", app_version="1.0", license_ok=True)
    d = diagnose("w", entry=entry, resolve_input=inp)
    assert d.route_recommended != "native_linux"


def test_app_version_drift_invalidates_route() -> None:
    entry = _entry(WindowsMode.WINE, PublishedStatus.WORKFLOW_VERIFIED, app_version="2.0")
    inp = ResolveInput(workflow_id="w", app_id="a", app_version="9.9", license_ok=True)
    d = diagnose("w", entry=entry, resolve_input=inp)
    assert d.route_no_verified is True
    assert d.route_recommended is None


def test_no_inputs_is_honest_gather() -> None:
    d = diagnose("w")
    assert d.route_no_verified is True
    assert d.execute_blocked is False
    assert d.suggested_action_vi  # có đề xuất (gom thêm thông tin), không rỗng
