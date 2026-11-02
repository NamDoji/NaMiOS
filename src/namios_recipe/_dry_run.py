"""``dry_run`` — liệt kê hành động dự kiến của recipe đã parse, KHÔNG thực
thi gì (M1 gate; FACT M1-INTERFACES §7.6: "M1: chỉ dry_run. Thực thi thật là
M2 BLOCKED"). KHÔNG gọi ``subprocess``/``run_argv``, KHÔNG tạo prefix Wine,
KHÔNG đụng filesystem ngoài đọc đối tượng Python đã có sẵn trong bộ nhớ.

Đây là lớp phòng thủ THỨ HAI (runtime/semantic) sau ``parse`` (cấu trúc):
kiểm dependency ∈ approved_dependency_ids, re-kiểm argv-only cho
``RunInstaller`` (phòng trường hợp caller tự dựng ``RecipeStep`` không qua
``parse_recipe_steps``), kiểm sha256/registry value hợp lệ.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from namios_core.errors import ErrorCode
from namios_core.recipe_types import (
    CreateLauncher,
    CreatePrefix,
    DryRunResult,
    InstallDependency,
    RecipeStep,
    RunInstaller,
    SetRegistryValue,
    VerifyFile,
)
from namios_core.validation import SemanticContext, ValidationError

__all__ = ["dry_run_steps"]

_SHA256_RE = re.compile(r"[a-f0-9]{64}")
_SHELL_METACHAR_RE = re.compile(r"[;&|`$<>\\\n]|\$\(|&&|\|\|")


def _err(
    path: str, message_vi: str, code: ErrorCode = ErrorCode.E_SEMANTIC_RECIPE
) -> ValidationError:
    return ValidationError(code=code.value, path=path, message_vi=message_vi)


def _check_step(
    idx: int, step: RecipeStep, ctx: SemanticContext, errors: list[ValidationError]
) -> str:
    """Trả về mô tả hành động dự kiến (planned action); phụ lục errors khi
    step không đạt điều kiện runtime/semantic."""

    path = f"[{idx}]"

    if isinstance(step, CreatePrefix):
        return f"create_prefix({step.prefix_architecture})"

    if isinstance(step, InstallDependency):
        if step.dependency_profile_id not in ctx.approved_dependency_ids:
            errors.append(
                _err(
                    f"{path}.dependency_profile_id",
                    f"Dependency '{step.dependency_profile_id}' chưa được duyệt "
                    "(không ∈ approved_dependency_ids).",
                    code=ErrorCode.E_SEMANTIC_DEPENDENCY,
                )
            )
        return f"install_dependency({step.dependency_profile_id})"

    if isinstance(step, SetRegistryValue):
        if step.value_type not in ("REG_SZ", "REG_DWORD"):
            errors.append(_err(f"{path}.value_type", "value_type phải là REG_SZ hoặc REG_DWORD."))
        elif step.value_type == "REG_DWORD" and not step.value.lstrip("-").isdigit():
            errors.append(
                _err(f"{path}.value", "value của REG_DWORD phải là số nguyên dạng chuỗi.")
            )
        return f"set_registry_value({step.key}\\{step.value_name})"

    if isinstance(step, RunInstaller):
        if not step.argv:
            errors.append(_err(f"{path}.argv", "argv rỗng — không có gì để chạy (dry-run)."))
        elif len(step.argv) == 1 and _SHELL_METACHAR_RE.search(step.argv[0]):
            errors.append(
                _err(
                    f"{path}.argv",
                    "argv có dấu hiệu là chuỗi lệnh shell ghép, không phải argv-array thật.",
                )
            )
        for i, item in enumerate(step.argv):
            if not isinstance(item, str):
                errors.append(_err(f"{path}.argv[{i}]", "Mỗi phần tử argv phải là chuỗi."))
        return f"run_installer({step.installer_ref}, argv={list(step.argv)})"

    if isinstance(step, VerifyFile):
        if not _SHA256_RE.fullmatch(step.sha256):
            errors.append(_err(f"{path}.sha256", "sha256 phải là chuỗi hex 64 ký tự thường."))
        return f"verify_file({step.path_label})"

    if isinstance(step, CreateLauncher):
        if "://" in step.app_id or "://" in step.profile_id:
            errors.append(_err(f"{path}.app_id", "Launcher không được nhúng URL (COMP-006)."))
        return f"create_launcher({step.app_id})"

    errors.append(_err(path, "Loại RecipeStep không xác định."))  # pragma: no cover - defensive
    return "unknown"


def dry_run_steps(steps: Sequence[RecipeStep], ctx: SemanticContext) -> DryRunResult:
    """Mô phỏng thuần (KHÔNG thực thi gì): kiểm semantic/runtime cho mỗi
    step đã parse và liệt kê hành động dự kiến theo đúng thứ tự."""

    errors: list[ValidationError] = []
    planned: list[str] = []
    for idx, step in enumerate(steps):
        planned.append(_check_step(idx, step, ctx, errors))

    return DryRunResult(ok=not errors, planned_actions=tuple(planned), rejected=tuple(errors))
