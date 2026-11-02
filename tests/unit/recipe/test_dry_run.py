"""``dry_run`` recipe vô hại: liệt kê planned_actions, KHÔNG tạo prefix Wine/
chạy installer thật; kiểm dependency ∈ approved; reject recipe runtime-unsafe."""

from __future__ import annotations

from namios_core.errors import ErrorCode
from namios_core.recipe_types import CreatePrefix, InstallDependency, RunInstaller
from namios_recipe import RecipeEngineImpl, parse_recipe_steps

from ._fixtures import ctx, step


def test_dry_run_harmless_recipe_ok_lists_planned_actions() -> None:
    engine = RecipeEngineImpl()
    steps = parse_recipe_steps(
        [
            step("create_prefix", {"prefix_architecture": "win64"}),
            step("install_dependency", {"dependency_profile_id": "vcrun2019-x64"}),
            step(
                "run_installer",
                {"installer_ref": "installer.exe", "argv": ["installer.exe", "/S"]},
            ),
        ]
    )

    result = engine.dry_run(steps, ctx())

    assert result.ok is True
    assert result.rejected == ()
    assert len(result.planned_actions) == 3
    assert "create_prefix" in result.planned_actions[0]
    assert "install_dependency" in result.planned_actions[1]
    assert "run_installer" in result.planned_actions[2]


def test_dry_run_does_not_execute_anything(monkeypatch) -> None:
    """Chứng minh dry_run KHÔNG gọi subprocess/run_argv (M1 gate: không thực
    thi gì, không tạo prefix Wine thật)."""

    import subprocess

    called = {"n": 0}

    def _boom(*args: object, **kwargs: object) -> None:
        called["n"] += 1
        raise AssertionError("dry_run KHÔNG được gọi subprocess.run")

    monkeypatch.setattr(subprocess, "run", _boom)

    engine = RecipeEngineImpl()
    steps = parse_recipe_steps(
        [
            step("create_prefix", {"prefix_architecture": "win64"}),
            step(
                "run_installer",
                {"installer_ref": "installer.exe", "argv": ["installer.exe", "/S"]},
            ),
        ]
    )
    result = engine.dry_run(steps, ctx())

    assert called["n"] == 0
    assert result.ok is True


def test_dry_run_rejects_unapproved_dependency() -> None:
    engine = RecipeEngineImpl()
    steps = parse_recipe_steps(
        [step("install_dependency", {"dependency_profile_id": "sketchy-unapproved-dep"})]
    )

    result = engine.dry_run(steps, ctx())

    assert result.ok is False
    assert any(e.code == ErrorCode.E_SEMANTIC_DEPENDENCY.value for e in result.rejected)


def test_dry_run_approved_dependency_passes() -> None:
    engine = RecipeEngineImpl()
    steps = (InstallDependency(dependency_profile_id="dotnet-48-x64"),)

    result = engine.dry_run(steps, ctx())

    assert result.ok is True
    assert result.rejected == ()


def test_dry_run_rejects_run_installer_with_shell_metachar_argv_built_directly() -> None:
    """Belt-and-suspenders: nếu một ``RecipeStep`` được dựng trực tiếp (không
    qua ``parse``) với argv-ghép-shell, ``dry_run`` vẫn phải chặn."""

    engine = RecipeEngineImpl()
    steps = (RunInstaller(installer_ref="installer.exe", argv=("rm -rf / ; echo pwned",)),)

    result = engine.dry_run(steps, ctx())

    assert result.ok is False
    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in result.rejected)


def test_dry_run_rejects_empty_argv_run_installer() -> None:
    engine = RecipeEngineImpl()
    steps = (RunInstaller(installer_ref="installer.exe", argv=()),)

    result = engine.dry_run(steps, ctx())

    assert result.ok is False


def test_dry_run_single_create_prefix_is_ok() -> None:
    engine = RecipeEngineImpl()
    result = engine.dry_run((CreatePrefix(prefix_architecture="win32"),), ctx())
    assert result.ok is True
    assert result.planned_actions == ("create_prefix(win32)",)


def test_dry_run_empty_steps_is_ok_noop() -> None:
    engine = RecipeEngineImpl()
    result = engine.dry_run((), ctx())
    assert result.ok is True
    assert result.planned_actions == ()
    assert result.rejected == ()
