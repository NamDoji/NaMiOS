"""CLI-02/CLI-03: ``DefaultInstallPlanner.verify_at_apply`` — reject plan
sai user, hết hạn, hoặc nội dung artifact đổi; ok khi nguyên vẹn."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.unit.planner._fixtures import FakeRecipeEngine, make_manifest, make_semantic_context

from namios_core.errors import ErrorCode
from namios_planner.planner import DefaultInstallPlanner

_NOW = datetime(2026, 11, 2, 8, 0, 0, tzinfo=UTC)


def _planner(now: datetime = _NOW, **kwargs: object) -> DefaultInstallPlanner:
    kwargs.setdefault("current_user", lambda: "nguoi-dung-test")
    kwargs.setdefault("current_host", lambda: "may-test-namios")
    kwargs.setdefault("recipe_engine", FakeRecipeEngine())
    kwargs.setdefault("clock", lambda: now)
    return DefaultInstallPlanner(**kwargs)  # type: ignore[arg-type]


def test_plan_nguyen_ven_dung_user_host_con_han_thi_ok() -> None:
    planner = _planner()
    plan = planner.build_plan(make_manifest(), installer_path=None, ctx=make_semantic_context())

    check = planner.verify_at_apply(
        plan, current_user="nguoi-dung-test", current_host="may-test-namios"
    )

    assert check.ok is True
    assert check.code is None
    assert check.message_vi is None


def test_apply_boi_user_khac_bi_reject(
    fake_user_host: object, another_fake_user_host: object
) -> None:  # noqa: E501
    planner = _planner(
        current_user=lambda: fake_user_host.user,  # type: ignore[attr-defined]
        current_host=lambda: fake_user_host.host,  # type: ignore[attr-defined]
    )
    plan = planner.build_plan(make_manifest(), installer_path=None, ctx=make_semantic_context())

    check = planner.verify_at_apply(
        plan,
        current_user=another_fake_user_host.user,  # type: ignore[attr-defined]
        current_host=another_fake_user_host.host,  # type: ignore[attr-defined]
    )

    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_apply_tren_may_khac_cung_user_bi_reject() -> None:
    planner = _planner(current_user=lambda: "nguoi-dung-test", current_host=lambda: "may-a")
    plan = planner.build_plan(make_manifest(), installer_path=None, ctx=make_semantic_context())

    check = planner.verify_at_apply(plan, current_user="nguoi-dung-test", current_host="may-khac")

    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_plan_qua_han_dung_bi_reject() -> None:
    planner = _planner()
    plan = planner.build_plan(make_manifest(), installer_path=None, ctx=make_semantic_context())

    later = _NOW + timedelta(minutes=16)  # TTL mặc định 15 phút đã trôi qua
    planner_at_apply = _planner(now=later)

    check = planner_at_apply.verify_at_apply(
        plan, current_user="nguoi-dung-test", current_host="may-test-namios"
    )

    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value
    assert "hết hạn" in (check.message_vi or "")


def test_plan_con_han_vua_truoc_moc_het_han_van_ok() -> None:
    planner = _planner()
    plan = planner.build_plan(make_manifest(), installer_path=None, ctx=make_semantic_context())

    just_before = _NOW + timedelta(minutes=14, seconds=59)
    planner_at_apply = _planner(now=just_before)

    check = planner_at_apply.verify_at_apply(
        plan, current_user="nguoi-dung-test", current_host="may-test-namios"
    )

    assert check.ok is True


def test_noi_dung_installer_doi_giua_plan_va_apply_bi_reject(tmp_path: object) -> None:
    installer = tmp_path / "setup.exe"  # type: ignore[attr-defined]
    installer.write_bytes(b"ban goc")

    planner = _planner()
    plan = planner.build_plan(
        make_manifest(), installer_path=str(installer), ctx=make_semantic_context()
    )

    # Đổi nội dung installer SAU khi plan đã tạo, TRƯỚC khi apply.
    installer.write_bytes(b"ban da bi doi noi dung")

    check = planner.verify_at_apply(
        plan, current_user="nguoi-dung-test", current_host="may-test-namios"
    )

    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_installer_bi_xoa_truoc_khi_apply_bi_reject(tmp_path: object) -> None:
    import os

    installer = tmp_path / "setup.exe"  # type: ignore[attr-defined]
    installer.write_bytes(b"noi dung")

    planner = _planner()
    plan = planner.build_plan(
        make_manifest(), installer_path=str(installer), ctx=make_semantic_context()
    )

    os.remove(str(installer))

    check = planner.verify_at_apply(
        plan, current_user="nguoi-dung-test", current_host="may-test-namios"
    )

    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_noi_dung_installer_khong_doi_thi_ok(tmp_path: object) -> None:
    installer = tmp_path / "setup.exe"  # type: ignore[attr-defined]
    installer.write_bytes(b"noi dung khong doi")

    planner = _planner()
    plan = planner.build_plan(
        make_manifest(), installer_path=str(installer), ctx=make_semantic_context()
    )

    check = planner.verify_at_apply(
        plan, current_user="nguoi-dung-test", current_host="may-test-namios"
    )

    assert check.ok is True
