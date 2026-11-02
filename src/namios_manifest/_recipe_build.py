"""Build ``RecipeStep`` typed (namios_core.recipe_types) từ raw dict manifest.

Đây là nơi chặn "recipe ngoài allowlist/shell" ở cấp MANIFEST (độc lập với
``RecipeEngine`` thật của WP10 — WP2 không phụ thuộc WP10, xem M1-INTERFACES
§0 bảng phụ thuộc). JSON Schema (tầng 1, ``contracts/app-manifest.schema.json``)
CHO PHÉP ``params`` chứa bất kỳ khóa nào (chỉ giới hạn ``maxProperties``) —
nên khóa ``shell``/tham số lạ KHÔNG bị tầng 1 chặn; phải chặn ở đây (tầng 2).

Mọi lỗi dùng ``ErrorCode.E_SEMANTIC_RECIPE`` (chặn khi build — coi như một
phần của "recipe ngoài allowlist/có shell" theo M1-INTERFACES §7.1/§7.6).
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

__all__ = ["build_recipe_steps"]

#: Khóa param cho phép theo từng action — allowlist tường minh, KHÔNG suy diễn.
_ALLOWED_PARAM_KEYS: Mapping[str, frozenset[str]] = {
    "create_prefix": frozenset({"prefix_architecture"}),
    "install_dependency": frozenset({"dependency_profile_id"}),
    "set_registry_value": frozenset({"key", "value_name", "value_type", "value"}),
    "run_installer": frozenset({"installer_ref", "argv"}),
    "verify_file": frozenset({"path_label", "sha256"}),
    "create_launcher": frozenset({"app_id", "profile_id"}),
}

#: Khóa/param TUYỆT ĐỐI bị chặn bất kể action — dấu hiệu rõ ràng của chạy
#: lệnh tùy ý/nội suy template (FACT CLAUDE.md: không shell/eval/url-script).
_FORBIDDEN_PARAM_KEYS = frozenset(
    {"shell", "eval", "cmd", "command", "exec", "url_script", "template", "interpolate"}
)

#: Metacharacter shell điển hình — dùng để phát hiện argv bị "ghép thành một
#: chuỗi lệnh" thay vì argv-array thật (FACT COMP-004: argv-only).
_SHELL_METACHAR_RE = re.compile(r"[;&|`$<>\\\n]|\$\(|&&|\|\|")

#: Template nội suy dạng ``{{ ... }}`` / ``${...}`` / ``%(...)s`` bên trong
#: GIÁ TRỊ chuỗi của param (không chỉ tên khóa) — chặn luôn ở tầng build-manifest
#: (phòng thủ sâu, đồng bộ với ``namios_recipe._parse._TEMPLATE_INTERP_RE``).
_TEMPLATE_INTERP_RE = re.compile(r"\{\{.*?\}\}|\$\{.*?\}|%\([a-zA-Z_][\w]*\)s")

#: URL-script điển hình: lược đồ http(s)/ftp kèm "| sh" / "|sh" (đồng bộ với
#: ``namios_recipe._parse._URL_SCRIPT_RE``).
_URL_SCRIPT_RE = re.compile(r"(?i)\b(https?|ftp)://\S+\s*\|\s*(sh|bash|powershell|cmd)\b")


def _err(path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=ErrorCode.E_SEMANTIC_RECIPE.value, path=path, message_vi=message_vi)


def _scan_string_for_injection(value: str, path: str, errors: list[ValidationError]) -> None:
    """Chặn template nội suy / url-script bên trong MỘT giá trị chuỗi param
    (phòng thủ sâu ở cấp manifest, đồng nhất với ``namios_recipe._parse``)."""

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


def _build_one(
    raw_step: Mapping[str, Any], idx: int, errors: list[ValidationError]
) -> RecipeStep | None:
    path = f"recipe[{idx}]"
    action = raw_step.get("action")
    params = raw_step.get("params")
    if not isinstance(params, Mapping):
        errors.append(_err(f"{path}.params", "Trường 'params' phải là object."))
        return None
    if not isinstance(action, str) or action not in _ALLOWED_PARAM_KEYS:
        errors.append(
            _err(f"{path}.action", f"Action '{action}' không thuộc allowlist 6 action cho phép.")
        )
        return None

    _check_forbidden_and_unknown(params, action, f"{path}.params", errors)

    if action == "create_prefix":
        arch = params.get("prefix_architecture")
        if arch not in ("win32", "win64"):
            errors.append(
                _err(
                    f"{path}.params.prefix_architecture",
                    "prefix_architecture phải là 'win32' hoặc 'win64'.",
                )
            )
            return None
        return CreatePrefix(prefix_architecture=arch)

    if action == "install_dependency":
        dep = _require_str(params, "dependency_profile_id", f"{path}.params", errors)
        if dep is None:
            return None
        return InstallDependency(dependency_profile_id=dep)

    if action == "set_registry_value":
        key = _require_str(params, "key", f"{path}.params", errors)
        value_name = _require_str(params, "value_name", f"{path}.params", errors)
        value = _require_str(params, "value", f"{path}.params", errors)
        value_type = params.get("value_type")
        if value_type not in ("REG_SZ", "REG_DWORD"):
            errors.append(
                _err(
                    f"{path}.params.value_type",
                    "value_type phải là 'REG_SZ' hoặc 'REG_DWORD'.",
                )
            )
        if (
            key is None
            or value_name is None
            or value is None
            or value_type
            not in (
                "REG_SZ",
                "REG_DWORD",
            )
        ):
            return None
        return SetRegistryValue(key=key, value_name=value_name, value_type=value_type, value=value)

    if action == "run_installer":
        installer_ref = _require_str(params, "installer_ref", f"{path}.params", errors)
        argv_raw = params.get("argv")
        if not isinstance(argv_raw, Sequence) or isinstance(argv_raw, (str, bytes)):
            errors.append(_err(f"{path}.params.argv", "argv phải là một danh sách (array) chuỗi."))
            return None
        argv: list[str] = []
        for i, item in enumerate(argv_raw):
            if not isinstance(item, str):
                errors.append(_err(f"{path}.params.argv[{i}]", "Mỗi phần tử argv phải là chuỗi."))
                continue
            argv.append(item)
        # Argv-only (FACT COMP-004): một argv[0] duy nhất chứa metacharacter
        # shell là dấu hiệu chuỗi lệnh bị ghép thay vì mảng argv thật.
        if len(argv) == 1 and _SHELL_METACHAR_RE.search(argv[0]):
            errors.append(
                _err(
                    f"{path}.params.argv",
                    "argv có dấu hiệu là chuỗi lệnh shell ghép, không phải argv-array thật.",
                )
            )
        if installer_ref is None or len(argv) != len(argv_raw):
            return None
        return RunInstaller(installer_ref=installer_ref, argv=tuple(argv))

    if action == "verify_file":
        path_label = _require_str(params, "path_label", f"{path}.params", errors)
        sha256 = params.get("sha256")
        if not isinstance(sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", sha256):
            errors.append(
                _err(f"{path}.params.sha256", "sha256 phải là chuỗi hex 64 ký tự thường.")
            )
            sha256 = None
        if path_label is None or sha256 is None:
            return None
        return VerifyFile(path_label=path_label, sha256=sha256)

    if action == "create_launcher":
        app_id = _require_str(params, "app_id", f"{path}.params", errors)
        profile_id = _require_str(params, "profile_id", f"{path}.params", errors)
        if app_id is None or profile_id is None:
            return None
        return CreateLauncher(app_id=app_id, profile_id=profile_id)

    return None  # pragma: no cover - unreachable, action đã lọc ở trên


def build_recipe_steps(raw_recipe: Sequence[Mapping[str, Any]]) -> tuple[RecipeStep, ...]:
    """Build toàn bộ recipe steps; raise ``ManifestLoadError`` (qua caller)
    nếu có bất kỳ bước lỗi — KHÔNG build Manifest từ recipe không an toàn."""

    from namios_manifest._errors import ManifestLoadError  # tránh import vòng

    errors: list[ValidationError] = []
    steps: list[RecipeStep] = []
    for idx, raw_step in enumerate(raw_recipe):
        if not isinstance(raw_step, Mapping):
            errors.append(_err(f"recipe[{idx}]", "Mỗi bước recipe phải là object."))
            continue
        step = _build_one(raw_step, idx, errors)
        if step is not None:
            steps.append(step)

    if errors:
        raise ManifestLoadError(tuple(errors))
    return tuple(steps)
