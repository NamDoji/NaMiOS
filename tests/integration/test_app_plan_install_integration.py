"""Integration — ``namios app plan-install`` end-to-end với implementation
THẬT: ``ManifestValidatorImpl`` (WP2) + ``DefaultInstallPlanner`` (WP6) tiêm
``RecipeEngineImpl`` (WP10) thật, qua ``default_dependencies()`` khi ``main()``
không được truyền ``deps``.

Phạm vi M1 (FACT): CLI subcommand ``app plan-install`` chỉ ``build_plan`` —
``verify_at_apply`` (stale-reject) CHƯA có subcommand CLI riêng ở M1 (``app
install`` luôn ``blocked`` — xem ``_handle_app_install``). Test "stale" ở
đây gọi trực tiếp ``InstallPlanner`` Protocol thật (không qua dispatch CLI)
để xác nhận wiring thật (không fake) tôn trọng đúng hợp đồng CLI-002.
"""

from __future__ import annotations

import io
import json

from namios_cli.main import main
from namios_core.exitcodes import ExitCode
from namios_manifest import ManifestValidatorImpl
from namios_planner import DefaultInstallPlanner
from namios_recipe import RecipeEngineImpl

from ._paths import manifest_fixture_path


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_app_plan_install_happy_path_real_wiring() -> None:
    path = manifest_fixture_path("valid-demo-app.json")
    rc, out, err = _run(["app", "plan-install", path, "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    data = parsed["data"]
    assert data["app_id"] == "demo-app"
    assert data["plan_id"]  # uuid4 hex thật, không rỗng
    assert data["expires_at"]
    assert isinstance(data["changes"], list)
    assert data["required_space_bytes"] == 0  # không có installer_path truyền vào


def test_app_plan_install_blocked_when_manifest_not_install_ready_real_wiring() -> None:
    """Manifest TBD (``application.build``/``installer_sha256`` null) — gate
    semantic thật (WP2) PHẢI chặn, CLI trả ``E_SEMANTIC_TBD``/exit INPUT,
    KHÔNG dựng plan."""

    path = manifest_fixture_path("not-ready-tbd-app.json")
    rc, out, err = _run(["app", "plan-install", path, "--json"])
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_SEMANTIC_TBD"
    assert parsed["error"]["details"]["errors"]


def test_install_planner_verify_at_apply_rejects_stale_user_host_real_wiring(
    fake_user_host: object, another_fake_user_host: object
) -> None:
    """``DefaultInstallPlanner`` + ``RecipeEngineImpl`` THẬT (không fake):
    build_plan cho ``fake_user_host``, rồi verify_at_apply với
    ``another_fake_user_host`` khác → PHẢI reject ``E_PLAN_STALE`` (CLI-002:
    "reject plan sai user, hết hạn, hoặc nội dung đổi")."""

    from namios_core.validation import SemanticContext

    manifest_validator = ManifestValidatorImpl()
    manifest = manifest_validator.load(manifest_fixture_path("valid-demo-app.json"))
    ctx = SemanticContext(
        approved_dependency_ids=frozenset(),
        pinned_runner_hashes=frozenset(),
        revoked_ids=frozenset(),
    )

    planner = DefaultInstallPlanner(
        RecipeEngineImpl(),
        current_user=lambda: fake_user_host.user,  # type: ignore[attr-defined]
        current_host=lambda: fake_user_host.host,  # type: ignore[attr-defined]
    )
    plan = planner.build_plan(manifest, None, ctx)
    assert plan.user == fake_user_host.user  # type: ignore[attr-defined]
    assert plan.host == fake_user_host.host  # type: ignore[attr-defined]

    check = planner.verify_at_apply(
        plan,
        current_user=another_fake_user_host.user,  # type: ignore[attr-defined]
        current_host=another_fake_user_host.host,  # type: ignore[attr-defined]
    )
    assert check.ok is False
    assert check.code == "E_PLAN_STALE"
    assert check.message_vi


def test_install_planner_verify_at_apply_accepts_same_user_host_real_wiring(
    fake_user_host: object,
) -> None:
    """Đối chiếu dương: cùng user/host với lúc build_plan → ``verify_at_apply``
    PHẢI ``ok=True`` (chưa hết hạn ngay sau khi tạo plan)."""

    manifest_validator = ManifestValidatorImpl()
    manifest = manifest_validator.load(manifest_fixture_path("valid-demo-app.json"))
    from namios_core.validation import SemanticContext

    ctx = SemanticContext(
        approved_dependency_ids=frozenset(),
        pinned_runner_hashes=frozenset(),
        revoked_ids=frozenset(),
    )
    planner = DefaultInstallPlanner(
        RecipeEngineImpl(),
        current_user=lambda: fake_user_host.user,  # type: ignore[attr-defined]
        current_host=lambda: fake_user_host.host,  # type: ignore[attr-defined]
    )
    plan = planner.build_plan(manifest, None, ctx)
    check = planner.verify_at_apply(
        plan,
        current_user=fake_user_host.user,  # type: ignore[attr-defined]
        current_host=fake_user_host.host,  # type: ignore[attr-defined]
    )
    assert check.ok is True
    assert check.code is None
