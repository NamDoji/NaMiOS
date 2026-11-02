"""CLI-02: ``DefaultInstallPlanner.build_plan`` — gom user/host/digest/
changes/permissions/expiry; reject khi profile revoked hoặc recipe bị tầng
ngữ nghĩa từ chối."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from tests.unit.planner._fixtures import (
    FakeRecipeEngine,
    RejectingRecipeEngine,
    make_manifest,
    make_semantic_context,
)

from namios_core.errors import ErrorCode
from namios_core.validation import ValidationError
from namios_planner.errors import PlanBuildError
from namios_planner.planner import DefaultInstallPlanner


def _planner(**kwargs: object) -> DefaultInstallPlanner:
    kwargs.setdefault("current_user", lambda: "nguoi-dung-test")
    kwargs.setdefault("current_host", lambda: "may-test-namios")
    kwargs.setdefault("recipe_engine", FakeRecipeEngine())
    return DefaultInstallPlanner(**kwargs)  # type: ignore[arg-type]


def test_build_plan_gom_du_user_host_digest_changes_permissions() -> None:
    manifest = make_manifest()
    ctx = make_semantic_context()
    fixed_now = datetime(2026, 11, 2, 8, 0, 0, tzinfo=UTC)
    planner = _planner(clock=lambda: fixed_now)

    plan = planner.build_plan(manifest, installer_path=None, ctx=ctx)

    assert plan.app_id == manifest.id
    assert plan.user == "nguoi-dung-test"
    assert plan.host == "may-test-namios"
    assert len(plan.profile_digest) == 64  # sha256 hex
    assert plan.artifact_digests == ()
    assert plan.changes == ("create_prefix(win64)",)
    assert plan.permissions == manifest.permissions
    assert plan.required_space_bytes == 0
    assert plan.expires_at == (fixed_now + timedelta(minutes=15)).isoformat()


def test_build_plan_voi_installer_tinh_digest_va_kich_thuoc(tmp_path: object) -> None:
    installer = tmp_path / "setup.exe"  # type: ignore[attr-defined]
    installer.write_bytes(b"noi dung installer gia lap " * 10)

    manifest = make_manifest()
    ctx = make_semantic_context()
    planner = _planner()

    plan = planner.build_plan(manifest, installer_path=str(installer), ctx=ctx)

    assert len(plan.artifact_digests) == 1
    label, digest = plan.artifact_digests[0]
    assert label == str(installer)
    assert len(digest) == 64
    assert plan.required_space_bytes == installer.stat().st_size  # type: ignore[attr-defined]


def test_build_plan_tu_choi_profile_bi_thu_hoi() -> None:
    manifest = make_manifest(app_id="app.vi.bithuhoi")
    ctx = make_semantic_context(revoked_ids=frozenset({"app.vi.bithuhoi"}))
    planner = _planner()

    with pytest.raises(PlanBuildError) as exc_info:
        planner.build_plan(manifest, installer_path=None, ctx=ctx)

    assert exc_info.value.code == ErrorCode.E_REVOKED
    assert "thu hồi" in exc_info.value.message_vi


def test_build_plan_tu_choi_khi_recipe_bi_tang_ngu_nghia_tu_choi() -> None:
    manifest = make_manifest()
    ctx = make_semantic_context()
    rejecting = RejectingRecipeEngine(
        error=ValidationError(
            code=ErrorCode.E_SEMANTIC_DEPENDENCY.value,
            path="recipe[0]",
            message_vi="Dependency profile chưa được duyệt.",
        )
    )
    planner = _planner(recipe_engine=rejecting)

    with pytest.raises(PlanBuildError) as exc_info:
        planner.build_plan(manifest, installer_path=None, ctx=ctx)

    assert exc_info.value.code == ErrorCode.E_SEMANTIC_RECIPE


def test_build_plan_tu_choi_installer_khong_doc_duoc(tmp_path: object) -> None:
    missing = tmp_path / "khong-ton-tai.exe"  # type: ignore[attr-defined]
    manifest = make_manifest()
    ctx = make_semantic_context()
    planner = _planner()

    with pytest.raises(PlanBuildError) as exc_info:
        planner.build_plan(manifest, installer_path=str(missing), ctx=ctx)

    assert exc_info.value.code == ErrorCode.E_PATH_UNSAFE


def test_build_plan_tu_choi_installer_la_symlink(tmp_path: object) -> None:
    import os

    real = tmp_path / "setup-thuc.exe"  # type: ignore[attr-defined]
    real.write_bytes(b"noi dung")
    link = tmp_path / "setup-link.exe"  # type: ignore[attr-defined]
    os.symlink(str(real), str(link))

    manifest = make_manifest()
    ctx = make_semantic_context()
    planner = _planner()

    with pytest.raises(PlanBuildError) as exc_info:
        planner.build_plan(manifest, installer_path=str(link), ctx=ctx)

    assert exc_info.value.code == ErrorCode.E_PATH_UNSAFE


def test_build_plan_khac_user_cho_hai_lan_goi_mac_dinh() -> None:
    # Hai instance planner với current_user khác nhau mô phỏng chạy trên hai
    # máy khác nhau — plan phải mang đúng user/host của lần build_plan đó
    # (không rò user/host của instance khác).
    manifest = make_manifest()
    ctx = make_semantic_context()
    planner_a = _planner(current_user=lambda: "a", current_host=lambda: "may-a")
    planner_b = _planner(current_user=lambda: "b", current_host=lambda: "may-b")

    plan_a = planner_a.build_plan(manifest, installer_path=None, ctx=ctx)
    plan_b = planner_b.build_plan(manifest, installer_path=None, ctx=ctx)

    assert plan_a.user == "a" and plan_a.host == "may-a"
    assert plan_b.user == "b" and plan_b.host == "may-b"
