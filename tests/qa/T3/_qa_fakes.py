"""Fake/adversarial test doubles riêng của tester T3 — khớp các Protocol
công khai trong ``namios_core`` (ManifestValidator/InstallPlanner/
EvidenceValidator). KHÔNG import từ ``tests/unit/cli/fakes.py`` hay
``tests/unit/planner/_fixtures.py`` của dev — T3 tự dựng fixture độc lập để
test không "copy" đúng giả định của dev (tránh bỏ lọt case dev không nghĩ
tới)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from namios_core.evidence_types import EvidenceReport, GateResult
from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    FilesystemPermission,
    LicenseSection,
    Manifest,
    PermissionsSection,
    RuntimeSection,
    SchemaResult,
    SemanticResult,
    SourceSection,
)
from namios_core.planner_types import ApplyCheck, InstallPlan
from namios_core.recipe_types import DryRunResult, RecipeStep
from namios_core.validation import SemanticContext, ValidationError

__all__ = [
    "qa_make_manifest",
    "QaManifestValidatorOk",
    "QaManifestValidatorBadErrorCode",
    "QaManifestValidatorRaisesOnSemantic",
    "QaManifestValidatorNotInstallReadyNoErrors",
    "QaPlannerRaisesPlanBuildError",
    "QaPlannerRaisesGenericException",
    "QaPlannerReturnsBadApplyCheckCode",
    "QaEvidenceValidatorRaisesOnGate",
    "QaEvidenceValidatorBadAllowedStatus",
    "QaRecipeEngineRejects",
]


def qa_make_manifest(*, app_id: str = "qa.app.adversarial") -> Manifest:
    """Manifest hợp lệ tối thiểu (KHÔNG đi qua schema thật — chỉ để nạp vào
    code path dispatch WP3 như một ``Manifest`` đã tải xong)."""

    return Manifest(
        schema_version="1.0",
        id=app_id,
        name="Ứng dụng kiểm thử T3",
        publisher="NaMiOS QA T3",
        mode="native",
        application=AppSection(
            version="9.9.9", build="9", architecture="x86_64", installer_sha256="f" * 64
        ),
        license=LicenseSection(
            kind="open_source",
            spdx_expression="MIT",
            user_entitlement_required=False,
            redistribution="allowed_with_conditions",
            terms_url=None,
        ),
        source=SourceSection(
            acquisition="official_download",
            official_url="https://example.invalid/qa",
            allowed_hosts=("example.invalid",),
            automatic_download=False,
        ),
        runtime=RuntimeSection(
            runner_id=None,
            runner_sha256=None,
            prefix_architecture="not_applicable",
            wow64_strategy="not_applicable",
            dependency_profile_ids=(),
        ),
        permissions=PermissionsSection(
            filesystem=(FilesystemPermission(scope="app_data", access="read"),),
            network="deny",
            audio=False,
            microphone=False,
            camera=False,
            printing=False,
            clipboard="deny",
            display="none",
            isolation="not_applicable",
            exceptions=(),
        ),
        recipe=(),
        compatibility=CompatSection(
            status="untested",
            vendor_support="unknown",
            required_task_ids=(),
            limitations=(),
            last_tested=None,
            evidence_id=None,
        ),
    )


class QaManifestValidatorOk:
    """Khớp ``ManifestValidator`` Protocol — happy path, install_ready=True."""

    def __init__(self, manifest: Manifest | None = None) -> None:
        self._manifest = manifest if manifest is not None else qa_make_manifest()

    def load(self, path: str) -> Manifest:
        return self._manifest

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult:
        return SemanticResult(ok=True, errors=(), install_ready=True)


class QaManifestValidatorBadErrorCode:
    """Adversarial: ``validate_semantic`` trả một ``ValidationError.code``
    KHÔNG thuộc ``namios_core.errors.ErrorCode`` — mô phỏng WP2 bị bug/lệch
    phiên bản gửi mã lỗi lạ. Dispatch của WP3 KHÔNG được sập vì input xấu từ
    một module khác — phải trả envelope lỗi an toàn (vd ``E_INTERNAL``)."""

    def __init__(self, manifest: Manifest | None = None, bad_code: str = "E_KHONG_TON_TAI") -> None:
        self._manifest = manifest if manifest is not None else qa_make_manifest()
        self._bad_code = bad_code

    def load(self, path: str) -> Manifest:
        return self._manifest

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult:
        bad = ValidationError(code=self._bad_code, path="$.compatibility", message_vi="lỗi giả lập mã lạ")
        return SemanticResult(ok=False, errors=(bad,), install_ready=False)


class QaManifestValidatorRaisesOnSemantic:
    """Adversarial: ``load()`` thành công nhưng ``validate_semantic`` ném
    exception bất ngờ (vd lỗi nội bộ WP2). WP3 chỉ bọc ``try/except`` quanh
    ``load()`` trong code hiện tại — case này kiểm tra liệu lỗi có thoát ra
    ngoài ``main()`` (phá hợp đồng envelope) hay không."""

    def __init__(self, manifest: Manifest | None = None) -> None:
        self._manifest = manifest if manifest is not None else qa_make_manifest()

    def load(self, path: str) -> Manifest:
        return self._manifest

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult:
        raise RuntimeError("WP2 nội bộ sập bất ngờ trong validate_semantic")


class QaManifestValidatorNotInstallReadyNoErrors:
    """Adversarial hợp lệ-theo-Protocol nhưng dữ liệu rỗng: ``install_ready
    =False`` và ``errors=()`` cùng lúc (Protocol KHÔNG cấm tổ hợp này). Dò
    xem WP3 chọn exit-code/ErrorCode nào khi không có error cụ thể để trỏ
    tới."""

    def __init__(self, manifest: Manifest | None = None) -> None:
        self._manifest = manifest if manifest is not None else qa_make_manifest()

    def load(self, path: str) -> Manifest:
        return self._manifest

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def validate_semantic(self, m: Manifest, ctx: SemanticContext) -> SemanticResult:
        return SemanticResult(ok=False, errors=(), install_ready=False)


class QaPlannerRaisesPlanBuildError:
    """Mô phỏng ĐÚNG hành vi thật của ``namios_planner.DefaultInstallPlanner``
    khi gặp app bị revoked / recipe bị từ chối: ném ``PlanBuildError``
    (exception riêng của WP6, không thuộc Protocol). Đây KHÔNG phải lỗi giả
    tùy tiện — là hành vi đã xác nhận bằng cách đọc ``namios_planner/
    planner.py`` + ``errors.py`` (xem `src/namios_planner/planner.py:86-100`)."""

    def __init__(self, message_vi: str = "Hồ sơ đã bị thu hồi (giả lập T3).") -> None:
        self._message_vi = message_vi

    def build_plan(self, m: Manifest, installer_path: str | None, ctx: SemanticContext) -> InstallPlan:
        # Import tại chỗ để không buộc WP6 phải có mặt khi chạy test khác của T3.
        from namios_core.errors import ErrorCode

        try:
            from namios_planner.errors import PlanBuildError
        except ImportError:  # WP6 có thể vắng trong vài cấu hình venv
            raise RuntimeError(self._message_vi) from None
        raise PlanBuildError(code=ErrorCode.E_REVOKED, message_vi=self._message_vi)

    def verify_at_apply(self, plan: InstallPlan, current_user: str, current_host: str) -> ApplyCheck:
        raise NotImplementedError("Không dùng trong case này")


class QaPlannerRaisesGenericException:
    """Adversarial: planner ném exception KHÔNG thuộc hệ thống lỗi ổn định
    nào (vd ``MemoryError``/``RuntimeError`` bất kỳ)."""

    def build_plan(self, m: Manifest, installer_path: str | None, ctx: SemanticContext) -> InstallPlan:
        raise RuntimeError("Lỗi nội bộ WP6 bất ngờ, không phải PlanBuildError")

    def verify_at_apply(self, plan: InstallPlan, current_user: str, current_host: str) -> ApplyCheck:
        raise NotImplementedError("Không dùng trong case này")


class QaPlannerReturnsBadApplyCheckCode:
    """Adversarial: ``verify_at_apply`` trả ``ApplyCheck.code`` là chuỗi
    KHÔNG thuộc ``ErrorCode`` — kiểm tra caller nào đọc field này (nếu có
    wiring sau này) không được crash khi ép kiểu."""

    def build_plan(self, m: Manifest, installer_path: str | None, ctx: SemanticContext) -> InstallPlan:
        raise NotImplementedError("Không dùng trong case này")

    def verify_at_apply(self, plan: InstallPlan, current_user: str, current_host: str) -> ApplyCheck:
        return ApplyCheck(ok=False, code="E_KHONG_TON_TAI_TRONG_ENUM", message_vi="mã lạ")


class QaEvidenceValidatorRaisesOnGate:
    """Adversarial: ``load()`` thành công nhưng ``compute_allowed_status``
    ném exception — kiểm tra có thoát ra ngoài envelope contract không."""

    def __init__(self, report: EvidenceReport | None = None) -> None:
        self._report = report or EvidenceReport(
            report_id="qa-rep-1",
            manifest_id="qa.app.adversarial",
            tests=(),
            decision="pending",
            qa_reviewer=None,
            environment={},
        )

    def load(self, path: str) -> EvidenceReport:
        return self._report

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def compute_allowed_status(self, rep: EvidenceReport) -> GateResult:
        raise RuntimeError("WP9 nội bộ sập bất ngờ trong compute_allowed_status")


class QaEvidenceValidatorBadAllowedStatus:
    """Adversarial: gate trả ``allowed_status`` là ``task_verified`` dù
    ``qa_reviewer is None`` trong report — mô phỏng WP9 bị bug để kiểm tra
    WP3 (CLI) KHÔNG tự thêm lớp phòng vệ phụ nào sai (chỉ echo nguyên trạng,
    không "sửa hộ" dữ liệu — ghi lại là rủi ro tích hợp, không phải lỗi WP3
    nếu WP3 chỉ echo)."""

    def __init__(self) -> None:
        self._report = EvidenceReport(
            report_id="qa-rep-2",
            manifest_id="qa.app.adversarial",
            tests=(),
            decision="task_verified",
            qa_reviewer=None,  # <-- thiếu reviewer nhưng vẫn "task_verified"
            environment={},
        )

    def load(self, path: str) -> EvidenceReport:
        return self._report

    def validate_schema(self, raw: Mapping[str, Any]) -> SchemaResult:
        return SchemaResult(ok=True, errors=())

    def compute_allowed_status(self, rep: EvidenceReport) -> GateResult:
        from namios_core.compat import CompatStatus

        # Gate "xấu" (giả lập WP9 bug) — KHÔNG chặn task_verified dù thiếu
        # qa_reviewer. T3 chỉ quan sát WP3 có phản xạ phòng vệ hay không.
        return GateResult(
            allowed_status=CompatStatus.TASK_VERIFIED,
            reasons_vi=("gate bug giả lập — không nên tin tưởng ở WP3",),
        )


class QaRecipeEngineRejects:
    """Khớp ``RecipeEngine`` Protocol — ``dry_run`` luôn từ chối, dùng để
    dựng ``DefaultInstallPlanner`` thật trong test build_plan qua CLI."""

    def parse(self, raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
        raise NotImplementedError("Không cần cho test T3")

    def dry_run(self, steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
        err = ValidationError(
            code="E_SEMANTIC_RECIPE", path="$.recipe[0]", message_vi="recipe giả lập bị chặn (T3)"
        )
        return DryRunResult(ok=False, planned_actions=(), rejected=(err,))
