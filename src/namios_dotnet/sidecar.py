"""Đọc ``.runtimeconfig.json``/``.deps.json`` ĐI KÈM file PE (NET-001/002).

CHỈ ``json.loads`` (an toàn, không ``eval``) trên dữ liệu đã bị giới hạn
kích thước bởi ``namios_dotnet._io``. Không có nhánh nào tải mạng hay mở
thêm file ngoài 2 sidecar đã xác định theo tên quy ước cạnh file PE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from namios_dotnet._errors import DotnetAnalysisError
from namios_dotnet._io import read_sidecar_if_present
from namios_dotnet.types import SidecarInfo

__all__ = ["KNOWN_SHARED_FRAMEWORKS", "load_sidecar_info"]

#: Shared framework chính thức .NET — KHÔNG bị gắn cờ "unknown_dependency".
#: Mọi tên khác trong deps.json libraries bị coi là phụ thuộc chưa rõ gốc
#: (NET-002 "unknown_deps") vì ta không resolve/tin cậy package bên thứ ba
#: mặc định.
KNOWN_SHARED_FRAMEWORKS: frozenset[str] = frozenset(
    {
        "Microsoft.NETCore.App",
        "Microsoft.AspNetCore.App",
        "Microsoft.WindowsDesktop.App",
    }
)

#: Chuỗi con (so khớp không phân biệt hoa/thường) cho biết app cần API
#: desktop Windows (WinForms/WPF) — bắt buộc không coi các app này là
#: "Linux native" dù TargetFramework là net6.0+ (test matrix NET-01/NET-04).
_WINDOWS_DESKTOP_MARKERS: tuple[str, ...] = ("windowsdesktop", "windowsforms", "wpf")


@dataclass(frozen=True)
class _RuntimeConfigParsed:
    tfm: str | None
    framework_names: tuple[str, ...]
    has_windows_desktop: bool
    warnings_vi: tuple[str, ...]


def _parse_runtimeconfig_json(raw: bytes) -> _RuntimeConfigParsed:
    warnings: list[str] = []
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _RuntimeConfigParsed(
            tfm=None,
            framework_names=(),
            has_windows_desktop=False,
            warnings_vi=("runtimeconfig.json không parse được (JSON/UTF-8 không hợp lệ)",),
        )
    if not isinstance(doc, dict):
        return _RuntimeConfigParsed(
            tfm=None,
            framework_names=(),
            has_windows_desktop=False,
            warnings_vi=("runtimeconfig.json không phải object JSON",),
        )

    runtime_options = doc.get("runtimeOptions")
    if not isinstance(runtime_options, dict):
        return _RuntimeConfigParsed(
            tfm=None,
            framework_names=(),
            has_windows_desktop=False,
            warnings_vi=("runtimeconfig.json thiếu 'runtimeOptions'",),
        )

    tfm = runtime_options.get("tfm")
    if not isinstance(tfm, str):
        tfm = None

    names: list[str] = []
    framework = runtime_options.get("framework")
    if isinstance(framework, dict):
        n = framework.get("name")
        if isinstance(n, str):
            names.append(n)
    frameworks = runtime_options.get("frameworks")
    if isinstance(frameworks, list):
        for f in frameworks:
            if isinstance(f, dict):
                n = f.get("name")
                if isinstance(n, str):
                    names.append(n)

    has_windows_desktop = any(
        marker in n.lower() for n in names for marker in _WINDOWS_DESKTOP_MARKERS
    )
    return _RuntimeConfigParsed(
        tfm=tfm,
        framework_names=tuple(names),
        has_windows_desktop=has_windows_desktop,
        warnings_vi=tuple(warnings),
    )


@dataclass(frozen=True)
class _DepsParsed:
    library_ids: tuple[str, ...]
    unknown_ids: tuple[str, ...]
    has_windows_desktop: bool
    warnings_vi: tuple[str, ...]


def _package_short_name(library_id: str) -> str:
    # deps.json libraries key dạng "Pkg.Name/1.2.3" — bỏ phần version.
    return library_id.split("/", 1)[0]


def _parse_deps_json(raw: bytes) -> _DepsParsed:
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _DepsParsed(
            library_ids=(),
            unknown_ids=(),
            has_windows_desktop=False,
            warnings_vi=("deps.json không parse được (JSON/UTF-8 không hợp lệ)",),
        )
    if not isinstance(doc, dict):
        return _DepsParsed(
            library_ids=(),
            unknown_ids=(),
            has_windows_desktop=False,
            warnings_vi=("deps.json không phải object JSON",),
        )

    libraries = doc.get("libraries")
    ids: list[str] = []
    if isinstance(libraries, dict):
        ids = [str(k) for k in libraries.keys()]

    short_names = [_package_short_name(i) for i in ids]
    unknown = tuple(
        name
        for name in short_names
        if name not in KNOWN_SHARED_FRAMEWORKS and not name.startswith("runtimepack.")
    )
    has_windows_desktop = any(
        marker in name.lower() for name in short_names for marker in _WINDOWS_DESKTOP_MARKERS
    )
    return _DepsParsed(
        library_ids=tuple(ids),
        unknown_ids=unknown,
        has_windows_desktop=has_windows_desktop,
        warnings_vi=(),
    )


def load_sidecar_info(pe_path: str) -> SidecarInfo | None:
    """Tìm + đọc ``<stem>.runtimeconfig.json`` và ``<stem>.deps.json`` cùng
    thư mục ``pe_path``. Trả ``None`` nếu KHÔNG có sidecar nào (hợp lệ — đa
    số native PE không có). Lỗi đọc/an toàn của một sidecar chỉ làm giảm dữ
    liệu khả dụng (ghi ``parse_warnings_vi``), KHÔNG làm hỏng toàn bộ phân
    tích."""

    warnings: list[str] = []

    runtimeconfig_path: str | None = None
    tfm: str | None = None
    framework_names: tuple[str, ...] = ()
    has_windows_desktop = False

    try:
        rc = read_sidecar_if_present(pe_path, ".runtimeconfig.json")
    except DotnetAnalysisError as exc:
        rc = None
        warnings.append(f"không đọc được runtimeconfig.json an toàn: {exc.reason_vi}")
    if rc is not None:
        runtimeconfig_path, rc_result = rc
        if rc_result.truncated:
            warnings.append("runtimeconfig.json vượt giới hạn kích thước đọc, đã cắt bớt")
        parsed_rc = _parse_runtimeconfig_json(rc_result.data)
        tfm = parsed_rc.tfm
        framework_names = parsed_rc.framework_names
        has_windows_desktop = has_windows_desktop or parsed_rc.has_windows_desktop
        warnings.extend(parsed_rc.warnings_vi)

    deps_json_path: str | None = None
    library_ids: tuple[str, ...] = ()
    unknown_ids: tuple[str, ...] = ()

    try:
        deps = read_sidecar_if_present(pe_path, ".deps.json")
    except DotnetAnalysisError as exc:
        deps = None
        warnings.append(f"không đọc được deps.json an toàn: {exc.reason_vi}")
    if deps is not None:
        deps_json_path, deps_result = deps
        if deps_result.truncated:
            warnings.append("deps.json vượt giới hạn kích thước đọc, đã cắt bớt")
        parsed_deps = _parse_deps_json(deps_result.data)
        library_ids = parsed_deps.library_ids
        unknown_ids = parsed_deps.unknown_ids
        has_windows_desktop = has_windows_desktop or parsed_deps.has_windows_desktop
        warnings.extend(parsed_deps.warnings_vi)

    if runtimeconfig_path is None and deps_json_path is None:
        return None

    return SidecarInfo(
        runtimeconfig_path=runtimeconfig_path,
        target_framework_moniker=tfm,
        framework_names=framework_names,
        has_windows_desktop_framework=has_windows_desktop,
        deps_json_path=deps_json_path,
        declared_library_ids=library_ids,
        unknown_dependency_ids=unknown_ids,
        parse_warnings_vi=tuple(warnings),
    )
