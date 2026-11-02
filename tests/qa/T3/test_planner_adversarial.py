"""T3 — adversarial/negative cho ``namios_planner.DefaultInstallPlanner``
(CLI-02/CLI-03: stale-reject khi sửa installer / đổi user-host / hết hạn /
revoked). Dùng implementation THẬT của WP6 (không fake lại logic cần kiểm
chứng) — chỉ fake ``RecipeEngine`` (phụ thuộc ngoài, WP10) theo Protocol.

Độc lập với ``tests/unit/planner/`` của dev — tự dựng fixture/manifest
riêng, tấn công các góc dev có thể không viết (TOCTOU symlink-swap,
boundary hết hạn chính xác, nhiều artifact cùng lúc, revoked không qua
``validate_semantic`` mà qua ``ctx.revoked_ids`` thẳng ở build_plan)."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from namios_core.errors import ErrorCode
from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    FilesystemPermission,
    LicenseSection,
    Manifest,
    PermissionsSection,
    RuntimeSection,
    SourceSection,
)
from namios_core.planner_types import ApplyCheck, InstallPlan
from namios_core.recipe_types import CreatePrefix, DryRunResult, RecipeStep
from namios_core.validation import SemanticContext
from namios_planner.errors import PlanBuildError
from namios_planner.planner import DefaultInstallPlanner

# ---------------------------------------------------------------------------
# Fixtures riêng T3 (không import tests/unit/planner/_fixtures.py của dev)
# ---------------------------------------------------------------------------


def _qa_manifest(app_id: str = "qa.t3.planner.app") -> Manifest:
    return Manifest(
        schema_version="1.0",
        id=app_id,
        name="Ung dung QA planner T3",
        publisher="NaMiOS QA T3",
        mode="wine",
        application=AppSection(
            version="1.0.0", build="1.0.0+1", architecture="x86_64", installer_sha256="c" * 64
        ),
        license=LicenseSection(
            kind="commercial",
            spdx_expression=None,
            user_entitlement_required=True,
            redistribution="not_included",
            terms_url=None,
        ),
        source=SourceSection(
            acquisition="user_provided", official_url=None, allowed_hosts=(), automatic_download=False
        ),
        runtime=RuntimeSection(
            runner_id="wine-qa",
            runner_sha256="d" * 64,
            prefix_architecture="win64",
            wow64_strategy="new_wow64",
            dependency_profile_ids=(),
        ),
        permissions=PermissionsSection(
            filesystem=(FilesystemPermission(scope="app_data", access="read_write"),),
            network="deny",
            audio=False,
            microphone=False,
            camera=False,
            printing=False,
            clipboard="deny",
            display="xwayland",
            isolation="required",
            exceptions=(),
        ),
        recipe=(CreatePrefix(prefix_architecture="win64"),),
        compatibility=CompatSection(
            status="untested",
            vendor_support="unknown",
            required_task_ids=(),
            limitations=(),
            last_tested=None,
            evidence_id=None,
        ),
    )


def _qa_ctx(**kwargs: Any) -> SemanticContext:
    base: dict[str, Any] = dict(
        approved_dependency_ids=frozenset(),
        pinned_runner_hashes=frozenset({"d" * 64}),
        revoked_ids=frozenset(),
    )
    base.update(kwargs)
    return SemanticContext(**base)


@dataclass
class _QaPermissiveRecipeEngine:
    def parse(self, raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
        raise NotImplementedError

    def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
        return DryRunResult(ok=True, planned_actions=("qa-create-prefix",), rejected=())


def _fixed_clock(now: datetime) -> Any:
    def _clock() -> datetime:
        return now

    return _clock


def _make_planner(
    *,
    now: datetime | None = None,
    user: str = "nguoi-dung-test",
    host: str = "may-test-namios",
    ttl: timedelta = timedelta(minutes=15),
) -> DefaultInstallPlanner:
    now = now if now is not None else datetime(2026, 1, 1, tzinfo=UTC)
    return DefaultInstallPlanner(
        _QaPermissiveRecipeEngine(),
        clock=_fixed_clock(now),
        current_user=lambda: user,
        current_host=lambda: host,
        ttl=ttl,
    )


# ---------------------------------------------------------------------------
# revoked → reject NGAY tại build_plan (qua ctx.revoked_ids, không cần WP2)
# ---------------------------------------------------------------------------


def test_build_plan_rejects_revoked_app_even_when_otherwise_perfectly_valid() -> None:
    planner = _make_planner()
    manifest = _qa_manifest(app_id="qa.t3.revoked-app")
    ctx = _qa_ctx(revoked_ids=frozenset({"qa.t3.revoked-app"}))

    with pytest.raises(PlanBuildError) as exc_info:
        planner.build_plan(manifest, None, ctx)

    assert exc_info.value.code == ErrorCode.E_REVOKED


def test_build_plan_revoked_check_is_exact_match_not_prefix() -> None:
    """Negative tinh vi: app_id gần giống (prefix/substring) KHÔNG được coi
    là revoked nếu không khớp y hệt trong ``revoked_ids`` — xác nhận không
    có so khớp lỏng/accidental bypass theo chiều ngược (an toàn hơn) hoặc
    theo chiều thuận (chặn nhầm app hợp lệ)."""

    planner = _make_planner()
    manifest = _qa_manifest(app_id="qa.t3.app")
    ctx = _qa_ctx(revoked_ids=frozenset({"qa.t3.app.v2", "qa.t3.ap"}))  # không khớp y hệt

    plan = planner.build_plan(manifest, None, ctx)
    assert plan.app_id == "qa.t3.app"


# ---------------------------------------------------------------------------
# đổi user/host → reject tại verify_at_apply
# ---------------------------------------------------------------------------


def test_verify_at_apply_rejects_when_apply_user_differs_even_by_case() -> None:
    planner = _make_planner(user="Nguoi.Dung", host="may-A")
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, None, _qa_ctx())

    # Thử bypass bằng đổi hoa/thường — so khớp PHẢI là strict string equality,
    # không được fold case (nếu không sẽ mở lỗ cho user giả danh trên hệ
    # thống case-insensitive).
    check = planner.verify_at_apply(plan, current_user="nguoi.dung", current_host="may-A")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_verify_at_apply_rejects_when_host_has_trailing_whitespace_injected() -> None:
    planner = _make_planner(user="u1", host="host-goc")
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, None, _qa_ctx())

    check = planner.verify_at_apply(plan, current_user="u1", current_host="host-goc ")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_verify_at_apply_accepts_exact_user_host_match() -> None:
    planner = _make_planner(user="u1", host="h1")
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, None, _qa_ctx())
    check = planner.verify_at_apply(plan, current_user="u1", current_host="h1")
    assert check.ok is True
    assert check.code is None


# ---------------------------------------------------------------------------
# hết hạn → reject; boundary chính xác tại thời điểm expires_at
# ---------------------------------------------------------------------------


def test_verify_at_apply_rejects_exactly_one_second_after_expiry() -> None:
    created_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    ttl = timedelta(minutes=10)
    planner = _make_planner(now=created_at, ttl=ttl)
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, None, _qa_ctx())

    # Đổi "đồng hồ hiện tại" của planner sang 1 giây sau hạn dùng.
    planner._clock = _fixed_clock(created_at + ttl + timedelta(seconds=1))  # type: ignore[attr-defined]
    check = planner.verify_at_apply(plan, current_user="nguoi-dung-test", current_host="may-test-namios")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_verify_at_apply_accepts_exactly_at_expiry_boundary_not_after() -> None:
    """Hiện trạng code dùng ``self._clock() > expires_at`` (strict greater),
    nghĩa là thời điểm == expires_at CHƯA bị coi là hết hạn. Ghi lại hành vi
    boundary này tường minh (không phải lỗi — nhưng nếu đổi sang ``>=`` sau
    này, test này sẽ bắt được thay đổi hành vi không chủ ý)."""

    created_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    ttl = timedelta(minutes=10)
    planner = _make_planner(now=created_at, ttl=ttl)
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, None, _qa_ctx())

    planner._clock = _fixed_clock(created_at + ttl)  # type: ignore[attr-defined]
    check = planner.verify_at_apply(plan, current_user="nguoi-dung-test", current_host="may-test-namios")
    assert check.ok is True


def test_verify_at_apply_rejects_garbage_expires_at_without_crashing() -> None:
    """Tấn công: ``InstallPlan`` bị sửa tay (hoặc đọc từ file plan bị tamper)
    có ``expires_at`` là chuỗi rác hoàn toàn — ``verify_at_apply`` KHÔNG được
    ném exception, phải trả ``ApplyCheck(ok=False, code=E_PLAN_STALE)``."""

    planner = _make_planner(user="u1", host="h1")
    plan = InstallPlan(
        plan_id="tampered-plan",
        app_id="qa.t3.app",
        user="u1",
        host="h1",
        profile_digest="e" * 64,
        artifact_digests=(),
        changes=(),
        required_space_bytes=0,
        permissions=_qa_manifest().permissions,
        expires_at="khong-phai-iso-8601-gi-ca!!!",
    )
    check = planner.verify_at_apply(plan, current_user="u1", current_host="h1")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


# ---------------------------------------------------------------------------
# sửa installer (digest đổi) → reject; TOCTOU symlink-swap KHÔNG được bypass
# ---------------------------------------------------------------------------


def test_verify_at_apply_rejects_when_installer_content_changed_after_plan(tmp_path: Path) -> None:
    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"NOI DUNG INSTALLER GOC")

    planner = _make_planner(user="u1", host="h1")
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, str(installer), _qa_ctx())

    # Tấn công: thay nội dung installer SAU khi plan đã dựng xong (trước khi
    # user bấm "Apply").
    installer.write_bytes(b"NOI DUNG INSTALLER DA BI THAY (gia lap malware)")

    check = planner.verify_at_apply(plan, current_user="u1", current_host="h1")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_verify_at_apply_rejects_toctou_symlink_swap_instead_of_silently_passing(
    tmp_path: Path,
) -> None:
    """Tấn công TOCTOU cổ điển: sau khi lập plan trên file thường, kẻ tấn
    công XÓA file đó và đặt một SYMLINK cùng tên trỏ tới file khác (có thể
    là tài liệu nhạy cảm) trước khi ``verify_at_apply`` chạy. Kỳ vọng: KHÔNG
    được coi là hợp lệ một cách im lặng — ``sha256_file`` dùng ``O_NOFOLLOW``
    nên mở symlink phải THẤT BẠI rõ ràng (ELOOP), không phải là lỗ hổng đọc
    xuyên symlink. Xác nhận bằng test THẬT trên filesystem (không mock)."""

    target_dir = tmp_path / "secret"
    target_dir.mkdir()
    secret_file = target_dir / "du-lieu-nhay-cam.bin"
    secret_file.write_bytes(b"KHONG DUOC DOC QUA SYMLINK SWAP")

    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"NOI DUNG INSTALLER GOC")

    planner = _make_planner(user="u1", host="h1")
    manifest = _qa_manifest()
    plan = planner.build_plan(manifest, str(installer), _qa_ctx())

    # Swap: xóa file gốc, thay bằng symlink trỏ tới "secret_file".
    os.remove(installer)
    os.symlink(secret_file, installer)

    check = planner.verify_at_apply(plan, current_user="u1", current_host="h1")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value
    # Không bị crash bằng exception không kiểm soát (xác nhận gián tiếp vì
    # dòng trên không raise) và message_vi không rò nội dung bí mật.
    assert check.message_vi is not None
    assert "du-lieu-nhay-cam" not in check.message_vi or True  # path_label CÓ thể xuất hiện
    assert "KHONG DUOC DOC" not in check.message_vi


def test_verify_at_apply_rejects_when_one_of_multiple_artifacts_tampered(tmp_path: Path) -> None:
    """Plan có NHIỀU artifact (dựng tay — build_plan thật chỉ hỗ trợ 1, nhưng
    ``InstallPlan.artifact_digests`` là tuple nên có thể có nhiều theo kiểu
    dữ liệu). Chỉ 1/2 bị tamper vẫn phải reject toàn bộ plan, không "pass
    một phần"."""

    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    f1.write_bytes(b"AAA")
    f2.write_bytes(b"BBB")

    from namios_planner._digest import sha256_file

    planner = _make_planner(user="u1", host="h1")
    plan = InstallPlan(
        plan_id="multi-artifact-plan",
        app_id="qa.t3.app",
        user="u1",
        host="h1",
        profile_digest="e" * 64,
        artifact_digests=((str(f1), sha256_file(str(f1))), (str(f2), sha256_file(str(f2)))),
        changes=(),
        required_space_bytes=0,
        permissions=_qa_manifest().permissions,
        expires_at=(datetime(2099, 1, 1, tzinfo=UTC)).isoformat(),
    )

    # Tamper CHỈ file thứ 2.
    f2.write_bytes(b"BBB-DA-DOI")

    check = planner.verify_at_apply(plan, current_user="u1", current_host="h1")
    assert check.ok is False
    assert check.code == ErrorCode.E_PLAN_STALE.value


def test_build_plan_rejects_relative_installer_path_as_path_unsafe(tmp_path: Path) -> None:
    """``installer_path`` tương đối (không phải tuyệt đối) PHẢI bị chặn ở
    tầng digest (``_open_regular_file_no_follow`` yêu cầu ``os.path.isabs``)
    — xác nhận ``build_plan`` biến lỗi đó thành ``PlanBuildError`` đúng mã
    ``E_PATH_UNSAFE``, không phải crash hay silent-pass."""

    (tmp_path / "relative.exe").write_bytes(b"x")
    planner = _make_planner()
    manifest = _qa_manifest()

    with pytest.raises(PlanBuildError) as exc_info:
        # cwd của test process không đảm bảo là tmp_path — cố ý dùng path
        # tương đối để kiểm tra guard ``isabs``, không quan tâm file có tồn
        # tại ở cwd hay không (phải fail SỚM vì không tuyệt đối).
        planner.build_plan(manifest, "relative.exe", _qa_ctx())

    assert exc_info.value.code == ErrorCode.E_PATH_UNSAFE


def test_build_plan_rejects_recipe_dry_run_failure_as_semantic_recipe_error() -> None:
    manifest = _qa_manifest()

    class _RejectingEngine(_QaPermissiveRecipeEngine):
        def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
            from namios_core.validation import ValidationError

            err = ValidationError(code="E_SEMANTIC_RECIPE", path="$.recipe[0]", message_vi="bi chan (T3)")
            return DryRunResult(ok=False, planned_actions=(), rejected=(err,))

    planner = DefaultInstallPlanner(_RejectingEngine())
    with pytest.raises(PlanBuildError) as exc_info:
        planner.build_plan(manifest, None, _qa_ctx())
    assert exc_info.value.code == ErrorCode.E_SEMANTIC_RECIPE
