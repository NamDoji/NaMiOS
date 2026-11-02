"""Tầng "parse" của recipe engine — chặn action/param ngoài allowlist, field
``shell``/``eval``/url-script/template nội suy, TRƯỚC KHI build thành
``RecipeStep`` typed (FACT COMP-004; M1-INTERFACES §7.6).

Độc lập hoàn toàn với ``namios_manifest`` (WP2 sở hữu package đó) — WP10
không import namios_manifest; chỉ dùng chung các kiểu đọc-only trong
``namios_core``. Lặp lại một phần logic allowlist là CHỦ Ý (hai lớp phòng
thủ độc lập ở hai nơi khác nhau trong pipeline: build-manifest-time ở WP2,
recipe-engine-time ở WP10) — không phải giẫm chân vì không chung file/package.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from namios_core.errors import ErrorCode
from namios_core.recipe_types import (
    CreateLauncher,
    CreatePrefix,
    InstallDependency,
    RecipeStep,
    RunInstaller,
    SetRegistryValue,
    VerifyFile,
)
from namios_core.validation import ValidationError
from namios_recipe._errors import RecipeParseError

__all__ = ["parse_recipe_steps", "ALLOWED_ACTIONS"]

#: 6 action khai báo duy nhất cho phép (FACT contract recipe.enum,
#: ``contracts/app-manifest.schema.json`` §recipe.items.properties.action).
ALLOWED_ACTIONS = frozenset(
    {
        "create_prefix",
        "install_dependency",
        "set_registry_value",
        "run_installer",
        "verify_file",
        "create_launcher",
    }
)

#: Khóa param cho phép theo từng action — allowlist tường minh, KHÔNG suy diễn.
_ALLOWED_PARAM_KEYS: Mapping[str, frozenset[str]] = {
    "create_prefix": frozenset({"prefix_architecture"}),
    "install_dependency": frozenset({"dependency_profile_id"}),
    "set_registry_value": frozenset({"key", "value_name", "value_type", "value"}),
    "run_installer": frozenset({"installer_ref", "argv"}),
    "verify_file": frozenset({"path_label", "sha256"}),
    "create_launcher": frozenset({"app_id", "profile_id"}),
}

#: Khóa param TUYỆT ĐỐI bị chặn bất kể action — dấu hiệu rõ ràng của chạy
#: lệnh tùy ý/nội suy template/url-script (FACT CLAUDE.md).
_FORBIDDEN_PARAM_KEYS = frozenset(
    {
        "shell",
        "eval",
        "cmd",
        "command",
        "exec",
        "url_script",
        "template",
        "interpolate",
        "format_string",
    }
)

#: Metacharacter shell điển hình — phát hiện argv bị "ghép thành một chuỗi
#: lệnh" thay vì argv-array thật (FACT COMP-004: argv-only).
_SHELL_METACHAR_RE = re.compile(r"[;&|`$<>\\\n]|\$\(|&&|\|\|")

#: Template nội suy dạng ``{{ ... }}`` / ``${...}`` / ``%(...)s`` bên trong
#: GIÁ TRỊ chuỗi của param (không chỉ tên khóa) — chặn luôn ở tầng parse.
_TEMPLATE_INTERP_RE = re.compile(r"\{\{.*?\}\}|\$\{.*?\}|%\([a-zA-Z_][\w]*\)s")

#: URL-script điển hình: lược đồ non-http(s) hoặc chuỗi "| sh" / "|sh" kèm URL.
_URL_SCRIPT_RE = re.compile(r"(?i)\b(https?|ftp)://\S+\s*\|\s*(sh|bash|powershell|cmd)\b")


def _err(path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=ErrorCode.E_SEMANTIC_RECIPE.value, path=path, message_vi=message_vi)


def _scan_string_for_injection(value: str, path: str, errors: list[ValidationError]) -> None:
    """Chặn template nội suy / url-script bên trong MỘT giá trị chuỗi param."""

    if _TEMPLATE_INTERP_RE.search(value):
        errors.append(
            _err(path, "Giá trị chứa template nội suy (ví dụ '{{...}}'/'${...}') bị cấm.")
        )
    if _URL_SCRIPT_RE.search(value):
        errors.append(_err(path, "Giá trị chứa url-script (URL ghép pipe vào shell) bị cấm."))


def _require_str(
    params: Mapping[str, Any], key: str, path: str, errors: list[ValidationError]
) -> str | None:
    value = params.get(key)
    if not isinstance(value, str) or not value:
        errors.append(_err(f"{path}.{key}", f"Tham số '{key}' phải là chuỗi không rỗng."))
        return None
    _scan_string_for_injection(value, f"{path}.{key}", errors)
    return value


def _check_forbidden_and_unknown(
    params: Mapping[str, Any], action: str, path: str, errors: list[ValidationError]
) -> None:
    allowed = _ALLOWED_PARAM_KEYS.get(action, frozenset())
    for key in params:
        if key in _FORBIDDEN_PARAM_KEYS:
            errors.append(
                _err(
                    f"{path}.{key}",
                    f"Tham số '{key}' bị cấm tuyệt đối (shell/eval/url-script/template nội suy).",
                )
            )
        elif key not in allowed:
            errors.append(
                _err(
                    f"{path}.{key}",
                    f"Tham số '{key}' không thuộc allowlist của action '{action}'.",
                )
            )


def _build_create_prefix(
    params: Mapping[str, Any], path: str, errors: list[ValidationError]
) -> RecipeStep | None:
    arch = params.get("prefix_architecture")
    if arch not in ("win32", "win64"):
        errors.append(
            _err(f"{path}.prefix_architecture", "prefix_architecture phải là 'win32' hoặc 'win64'.")
        )
        return None
    return CreatePrefix(prefix_architecture=arch)


def _build_install_dependency(
    params: Mapping[str, Any], path: str, errors: list[ValidationError]
) -> RecipeStep | None:
    dep = _require_str(params, "dependency_profile_id", path, errors)
    if dep is None:
        return None
    return InstallDependency(dependency_profile_id=dep)


def _build_set_registry_value(
    params: Mapping[str, Any], path: str, errors: list[ValidationError]
) -> RecipeStep | None:
    key = _require_str(params, "key", path, errors)
    value_name = _require_str(params, "value_name", path, errors)
    value = _require_str(params, "value", path, errors)
    value_type = params.get("value_type")
    if value_type not in ("REG_SZ", "REG_DWORD"):
        errors.append(_err(f"{path}.value_type", "value_type phải là 'REG_SZ' hoặc 'REG_DWORD'."))
        return None
    if value_type == "REG_DWORD" and value is not None and not value.lstrip("-").isdigit():
        errors.append(_err(f"{path}.value", "value của REG_DWORD phải là số nguyên dạng chuỗi."))
        return None
    if key is None or value_name is None or value is None:
        return None
    return SetRegistryValue(key=key, value_name=value_name, value_type=value_type, value=value)


def _build_run_installer(
    params: Mapping[str, Any], path: str, errors: list[ValidationError]
) -> RecipeStep | None:
    installer_ref = _require_str(params, "installer_ref", path, errors)
    argv_raw = params.get("argv")
    if not isinstance(argv_raw, Sequence) or isinstance(argv_raw, (str, bytes)):
        errors.append(_err(f"{path}.argv", "argv phải là một danh sách (array) chuỗi."))
        return None
    argv: list[str] = []
    ok = True
    for i, item in enumerate(argv_raw):
        if not isinstance(item, str):
            errors.append(_err(f"{path}.argv[{i}]", "Mỗi phần tử argv phải là chuỗi."))
            ok = False
            continue
        argv.append(item)
    # Argv-only (FACT COMP-004): một argv[0] duy nhất chứa metacharacter shell
    # là dấu hiệu chuỗi lệnh bị ghép thay vì mảng argv thật.
    if len(argv) == 1 and _SHELL_METACHAR_RE.search(argv[0]):
        errors.append(
            _err(
                f"{path}.argv",
                "argv có dấu hiệu là chuỗi lệnh shell ghép, không phải argv-array thật.",
            )
        )
        ok = False
    for i, item in enumerate(argv):
        _scan_string_for_injection(item, f"{path}.argv[{i}]", errors)
    if installer_ref is None or not ok or len(argv) != len(argv_raw):
        return None
    return RunInstaller(installer_ref=installer_ref, argv=tuple(argv))


def _build_verify_file(
    params: Mapping[str, Any], path: str, errors: list[ValidationError]
) -> RecipeStep | None:
    path_label = _require_str(params, "path_label", path, errors)
    sha256 = params.get("sha256")
    if not isinstance(sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", sha256):
        errors.append(_err(f"{path}.sha256", "sha256 phải là chuỗi hex 64 ký tự thường."))
        sha256 = None
    if path_label is None or sha256 is None:
        return None
    return VerifyFile(path_label=path_label, sha256=sha256)


def _build_create_launcher(
    params: Mapping[str, Any], path: str, errors: list[ValidationError]
) -> RecipeStep | None:
    app_id = _require_str(params, "app_id", path, errors)
    profile_id = _require_str(params, "profile_id", path, errors)
    if app_id is None or profile_id is None:
        return None
    # COMP-006: launcher KHÔNG nhúng mật khẩu/URL-1-lần/lệnh.
    for field_name, field_value in (("app_id", app_id), ("profile_id", profile_id)):
        if "://" in field_value or " " in field_value:
            errors.append(
                _err(
                    f"{path}.{field_name}",
                    f"'{field_name}' không được chứa URL hoặc khoảng trắng "
                    "(nghi ngờ nhúng lệnh/URL).",
                )
            )
            return None
    return CreateLauncher(app_id=app_id, profile_id=profile_id)


_BUILDERS = {
    "create_prefix": _build_create_prefix,
    "install_dependency": _build_install_dependency,
    "set_registry_value": _build_set_registry_value,
    "run_installer": _build_run_installer,
    "verify_file": _build_verify_file,
    "create_launcher": _build_create_launcher,
}


def _parse_one(
    raw_step: Mapping[str, Any], idx: int, errors: list[ValidationError]
) -> RecipeStep | None:
    step_path = f"[{idx}]"
    action = raw_step.get("action")
    params = raw_step.get("params")

    extra_keys = set(raw_step) - {"action", "params"}
    for key in sorted(extra_keys):
        errors.append(
            _err(f"{step_path}.{key}", f"Khóa '{key}' ở cấp bước recipe không được phép.")
        )

    if not isinstance(params, Mapping):
        errors.append(_err(f"{step_path}.params", "Trường 'params' phải là object."))
        return None
    if not isinstance(action, str) or action not in ALLOWED_ACTIONS:
        errors.append(
            _err(
                f"{step_path}.action",
                f"Action '{action}' không thuộc allowlist 6 action cho phép.",
            )
        )
        return None

    param_path = f"{step_path}.params"
    _check_forbidden_and_unknown(params, action, param_path, errors)

    before = len(errors)
    step = _BUILDERS[action](params, param_path, errors)
    if len(errors) > before:
        return None
    return step


def parse_recipe_steps(raw_steps: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
    """Parse ``raw_steps`` thành ``RecipeStep`` typed. Reject TOÀN BỘ recipe
    (raise ``RecipeParseError``) nếu BẤT KỲ bước nào ngoài allowlist/có
    shell/eval/url-script/template nội suy — KHÔNG build một phần."""

    if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, (str, bytes)):
        raise RecipeParseError((_err("", "raw_steps phải là một danh sách (array) các bước."),))

    errors: list[ValidationError] = []
    steps: list[RecipeStep] = []
    for idx, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, Mapping):
            errors.append(_err(f"[{idx}]", "Mỗi bước recipe phải là object."))
            continue
        step = _parse_one(raw_step, idx, errors)
        if step is not None:
            steps.append(step)

    if errors:
        raise RecipeParseError(tuple(errors))
    return tuple(steps)
