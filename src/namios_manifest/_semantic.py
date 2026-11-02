"""Tầng 2 — semantic validator (COMP-004, §11.1): "schema hợp lệ" ≠
"install-ready". Xem M1-INTERFACES.md §7.1.

Chặn: profile TBD/null bắt buộc để cài, runner chưa pin, dependency chưa
duyệt, revoked, ``task_verified`` thiếu evidence. Recipe ngoài
allowlist/shell đã bị chặn SỚM hơn, lúc build Manifest (``_recipe_build``),
nên tới đây ``m.recipe`` luôn là các ``RecipeStep`` đã sạch — chỗ này chỉ
còn kiểm tra ngữ nghĩa liên-trường (ví dụ dependency trong recipe có nằm
trong danh sách đã duyệt hay không).
"""

from __future__ import annotations

from namios_core.errors import ErrorCode
from namios_core.manifest_types import Manifest, SemanticResult
from namios_core.recipe_types import InstallDependency
from namios_core.validation import SemanticContext, ValidationError

__all__ = ["validate_semantic"]

#: Mode không cần cài cục bộ (không app build/runner/installer) — web chạy
#: trong browser, remote chạy ở máy khác (FACT WIN-003/AppMode).
_NO_LOCAL_INSTALL_MODES = frozenset({"web", "remote"})

#: Mode cần runner (compatibility layer) được pin hash trước khi cài.
_RUNNER_REQUIRED_MODES = frozenset({"wine", "vm"})


def _err(code: ErrorCode, path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=code.value, path=path, message_vi=message_vi)


def validate_semantic(m: Manifest, ctx: SemanticContext) -> SemanticResult:
    errors: list[ValidationError] = []

    # 1) Revoked — chặn tuyệt đối, không xét gì khác (FACT §5).
    if m.id in ctx.revoked_ids or m.compatibility.status == "revoked":
        errors.append(
            _err(
                ErrorCode.E_REVOKED,
                "id",
                f"Hồ sơ '{m.id}' đã bị thu hồi (revoked) — không được cài.",
            )
        )

    needs_local_install = (
        m.mode not in _NO_LOCAL_INSTALL_MODES and m.source.acquisition != "existing_environment"
    )

    # 2) TBD/null bắt buộc để cài.
    if needs_local_install:
        if m.application.build is None:
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_TBD,
                    "application.build",
                    "Chưa có build ứng dụng được phép dùng (còn TBD/null).",
                )
            )
        if m.application.installer_sha256 is None:
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_TBD,
                    "application.installer_sha256",
                    "Chưa có hash bộ cài được xác nhận (còn TBD/null).",
                )
            )

    if m.mode in _RUNNER_REQUIRED_MODES:
        if m.runtime.runner_id is None:
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_TBD,
                    "runtime.runner_id",
                    "Chưa chọn runner (runtime) — còn TBD/null.",
                )
            )
        if m.runtime.runner_sha256 is None:
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_TBD,
                    "runtime.runner_sha256",
                    "Chưa pin hash runner — còn TBD/null.",
                )
            )
        elif m.runtime.runner_sha256 not in ctx.pinned_runner_hashes:
            # 3) Runner có hash nhưng chưa nằm trong danh sách đã pin/duyệt.
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_DEPENDENCY,
                    "runtime.runner_sha256",
                    "Runner chưa được pin trong danh sách hash đã duyệt.",
                )
            )

    # 4) Dependency chưa duyệt (declared ở runtime.dependency_profile_ids).
    for idx, dep_id in enumerate(m.runtime.dependency_profile_ids):
        if dep_id not in ctx.approved_dependency_ids:
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_DEPENDENCY,
                    f"runtime.dependency_profile_ids[{idx}]",
                    f"Dependency '{dep_id}' chưa thuộc danh sách đã duyệt.",
                )
            )

    # 4b) Dependency chưa duyệt khai báo qua recipe (install_dependency).
    for idx, step in enumerate(m.recipe):
        if isinstance(step, InstallDependency) and step.dependency_profile_id not in (
            ctx.approved_dependency_ids
        ):
            errors.append(
                _err(
                    ErrorCode.E_SEMANTIC_DEPENDENCY,
                    f"recipe[{idx}].dependency_profile_id",
                    f"Dependency '{step.dependency_profile_id}' trong recipe chưa được duyệt.",
                )
            )

    # 5) task_verified thiếu evidence (tự-chứa trong CompatSection; evidence
    #    report đầy đủ từ WP9 là lớp gate khác, ngoài phạm vi WP2).
    if m.compatibility.status == "task_verified" and m.compatibility.evidence_id is None:
        errors.append(
            _err(
                ErrorCode.E_EVIDENCE_MISSING,
                "compatibility.evidence_id",
                "Trạng thái 'task_verified' nhưng thiếu evidence_id.",
            )
        )

    ok = len(errors) == 0
    return SemanticResult(ok=ok, errors=tuple(errors), install_ready=ok)
