"""Entry point + dispatch subcommand cho ``namios`` CLI (WP3, nối WIRING).

Khung subcommand cho ``catalog validate``/``app inspect|plan-install|install``/
``evidence validate`` gọi Protocol tương ứng qua ``CliDependencies`` (dependency
injection). Khi một Protocol chưa được nối (``None`` — trường hợp caller tự
truyền ``deps=CliDependencies()`` rỗng, như test đơn vị/QA), subcommand trả
envelope lỗi rõ ràng (``E_INTERNAL``) thay vì giả lập kết quả hay crash không
kiểm soát.

Khi ``main()`` được gọi KHÔNG truyền ``deps`` (``deps=None``, ví dụ chạy
``namios ...`` thật từ console-script ``run()``), WIRING tích hợp (vai trò sở
hữu ``namios_cli/``/``namios_doctor/``/``tests/integration/``, sau khi các WP đã
merge) nối ``CliDependencies`` với implementation THẬT của từng WP qua
``namios_cli.deps.default_dependencies()`` — chạy end-to-end thật, không fake.

``namios doctor`` là subcommand hiện thực ĐẦY ĐỦ ngay trong WP3 (capability
report host thật — xem ``namios_doctor``), không qua ``CliDependencies``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from typing import IO

from namios_cli.deps import CliDependencies, default_dependencies
from namios_cli.envelope_io import emit_json, envelope_exit_code, new_operation_id
from namios_cli.errors import error_envelope, ok_envelope
from namios_cli.parser import ArgumentParsingError, parse_args
from namios_cli.service_catalog_loader import ServiceCatalogLoadError, load_service_catalog
from namios_core.envelope import Envelope
from namios_core.errors import ErrorCode
from namios_core.validation import SemanticContext
from namios_doctor.doctor import build_doctor_data
from namios_eco.coverage import listed_vs_working
from namios_eco.models import ServiceEntry
from namios_eco.search import search_services
from namios_eco.status import NEVER_USABLE_STATUSES, is_usable


def _not_wired(operation_id: str, feature_vi: str) -> Envelope:
    """Envelope lỗi chuẩn cho subcommand chưa nối implementation thật.

    KHÔNG phải lỗi nội bộ bất ngờ theo nghĩa thông thường của ``E_INTERNAL``,
    nhưng ``namios_core.errors`` M1 chưa có mã riêng cho "chưa wiring" —
    dùng ``E_INTERNAL`` kèm thông điệp rõ ràng, KHÔNG đổi thành ``ok`` giả.
    """

    return error_envelope(
        operation_id,
        ErrorCode.E_INTERNAL,
        f"{feature_vi} chưa được nối với triển khai thật (wiring sau khi WP tương ứng merge).",
        details={"wired": False},
    )


def _empty_semantic_context() -> SemanticContext:
    return SemanticContext(
        approved_dependency_ids=frozenset(),
        pinned_runner_hashes=frozenset(),
        revoked_ids=frozenset(),
    )


def _handle_doctor(operation_id: str) -> Envelope:
    data = build_doctor_data()
    return ok_envelope(operation_id, data)


def _handle_catalog_validate(operation_id: str, path: str, deps: CliDependencies) -> Envelope:
    if deps.manifest_validator is None:
        return _not_wired(operation_id, "Thẩm định catalog")
    ctx = deps.semantic_context or _empty_semantic_context()
    try:
        manifest = deps.manifest_validator.load(path)
    except Exception as exc:  # noqa: BLE001 — chuẩn hoá lỗi WP2 thành envelope nhất quán
        return error_envelope(
            operation_id,
            ErrorCode.E_INPUT_SCHEMA,
            "Không tải được manifest.",
            details={"path_label": "manifest", "reason": type(exc).__name__},
        )
    result = deps.manifest_validator.validate_semantic(manifest, ctx)
    if not result.ok:
        first = result.errors[0] if result.errors else None
        if first is None:
            code = ErrorCode.E_INTERNAL
        else:
            try:
                code = ErrorCode(first.code)
            except ValueError:
                # WP2 trả mã lỗi ngoài ErrorCode enum (bug nhỏ/lệch phiên
                # bản) — fallback an toàn về E_INTERNAL thay vì crash CLI.
                code = ErrorCode.E_INTERNAL
        message = first.message_vi if first is not None else "Manifest không hợp lệ."
        return error_envelope(
            operation_id,
            code,
            message,
            details={
                "errors": [
                    {"code": e.code, "path": e.path, "message_vi": e.message_vi}
                    for e in result.errors
                ]
            },
        )
    return ok_envelope(
        operation_id,
        {"app_id": manifest.id, "install_ready": result.install_ready},
    )


def _handle_app_inspect(operation_id: str, path: str, deps: CliDependencies) -> Envelope:
    if deps.manifest_validator is None:
        return _not_wired(operation_id, "Xem tóm tắt ứng dụng")
    try:
        manifest = deps.manifest_validator.load(path)
    except Exception as exc:  # noqa: BLE001
        return error_envelope(
            operation_id,
            ErrorCode.E_INPUT_SCHEMA,
            "Không tải được manifest.",
            details={"path_label": "manifest", "reason": type(exc).__name__},
        )
    return ok_envelope(
        operation_id,
        {
            "app_id": manifest.id,
            "name": manifest.name,
            "publisher": manifest.publisher,
            "mode": manifest.mode,
            "compatibility_status": manifest.compatibility.status,
        },
    )


def _handle_app_plan_install(operation_id: str, path: str, deps: CliDependencies) -> Envelope:
    if deps.manifest_validator is None or deps.install_planner is None:
        return _not_wired(operation_id, "Dựng install plan")
    ctx = deps.semantic_context or _empty_semantic_context()
    try:
        manifest = deps.manifest_validator.load(path)
    except Exception as exc:  # noqa: BLE001
        return error_envelope(
            operation_id,
            ErrorCode.E_INPUT_SCHEMA,
            "Không tải được manifest.",
            details={"path_label": "manifest", "reason": type(exc).__name__},
        )
    semantic = deps.manifest_validator.validate_semantic(manifest, ctx)
    if not semantic.install_ready:
        return error_envelope(
            operation_id,
            ErrorCode.E_SEMANTIC_TBD,
            "Manifest chưa sẵn sàng để cài (còn hồ sơ TBD/chưa duyệt).",
            details={
                "errors": [
                    {"code": e.code, "path": e.path, "message_vi": e.message_vi}
                    for e in semantic.errors
                ]
            },
        )
    plan = deps.install_planner.build_plan(manifest, None, ctx)
    return ok_envelope(
        operation_id,
        {
            "plan_id": plan.plan_id,
            "app_id": plan.app_id,
            "expires_at": plan.expires_at,
            "changes": list(plan.changes),
            "required_space_bytes": plan.required_space_bytes,
        },
    )


def _handle_app_install(operation_id: str) -> Envelope:
    # M1 gate (FACT): KHÔNG cài thật — chỉ dry-run/plan. Thực thi thật là M2
    # (BLOCKED tại host này — thiếu Wine/txstate apply thật).
    return error_envelope(
        operation_id,
        ErrorCode.E_INTERNAL,
        "Cài đặt thật thuộc phạm vi M2 (BLOCKED tại host này); M1 chỉ hỗ trợ "
        "plan-install/dry-run.",
        details={"blocked_external_dependency": True},
    )


def _handle_evidence_validate(operation_id: str, path: str, deps: CliDependencies) -> Envelope:
    if deps.evidence_validator is None:
        return _not_wired(operation_id, "Thẩm định evidence report")
    try:
        report = deps.evidence_validator.load(path)
    except Exception as exc:  # noqa: BLE001
        return error_envelope(
            operation_id,
            ErrorCode.E_INPUT_SCHEMA,
            "Không tải được evidence report.",
            details={"path_label": "evidence", "reason": type(exc).__name__},
        )
    gate = deps.evidence_validator.compute_allowed_status(report)
    return ok_envelope(
        operation_id,
        {
            "report_id": report.report_id,
            "manifest_id": report.manifest_id,
            "allowed_status": gate.allowed_status,
            "reasons_vi": list(gate.reasons_vi),
        },
    )


# ---------------------------------------------------------------------------
# namios service — danh bạ ECO-006/ECO-007/ECO-022 (đọc catalog/services tĩnh,
# KHÔNG qua CliDependencies — danh bạ không phải Protocol liên-WP, là dữ liệu
# đóng gói cùng repo do chính vai trò này sở hữu).
# ---------------------------------------------------------------------------


def _service_entry_summary(entry: ServiceEntry) -> dict[str, object]:
    """Tóm tắt một entry cho ``list``/``search`` — LUÔN kèm trường ``usable``
    suy từ GATE ``namios_eco.status.is_usable`` (ECO-003), KHÔNG để caller tự
    suy đoán "dùng được" từ ``published_status`` thô."""

    return {
        "id": entry.id,
        "provider": entry.provider,
        "agency": entry.agency,
        "purpose": entry.purpose,
        "official_url": entry.official_url,
        "published_status": entry.published_status,
        "usable": is_usable(entry.published_status),
        "windows_mode": entry.windows_mode,
        "tested_by_namios": entry.tested_by_namios,
        "officially_supported_by_vendor": entry.officially_supported_by_vendor,
        "last_updated": entry.last_updated,
    }


def _service_entry_full(entry: ServiceEntry) -> dict[str, object]:
    """Toàn bộ trường của một entry (cho ``inspect``) + ``usable`` suy ra."""

    return {
        "id": entry.id,
        "provider": entry.provider,
        "agency": entry.agency,
        "purpose": entry.purpose,
        "official_url": entry.official_url,
        "source_check": entry.source_check,
        "version": entry.version,
        "license": entry.license,
        "published_os": list(entry.published_os),
        "dependencies": list(entry.dependencies),
        "account_condition": entry.account_condition,
        "service_cost": entry.service_cost,
        "data_sensitivity": entry.data_sensitivity,
        "test_profile": entry.test_profile,
        "last_updated": entry.last_updated,
        "evidence_source": entry.evidence_source,
        "published_status": entry.published_status,
        "windows_mode": entry.windows_mode,
        "tested_by_namios": entry.tested_by_namios,
        "officially_supported_by_vendor": entry.officially_supported_by_vendor,
        "usable": is_usable(entry.published_status),
    }


def _never_usable_warnings(entries: Iterable[ServiceEntry]) -> list[str]:
    """ECO-003 GATE hiển thị: cảnh báo RÕ RÀNG cho từng entry đang ở
    ``downloadable_only``/``launches_only`` — các trạng thái TUYỆT ĐỐI không
    được hiểu là "dùng được", dù trường ``usable`` đã là ``False``."""

    return [
        f"'{e.id}': trạng thái '{e.published_status.value}' KHÔNG đồng nghĩa "
        "dùng được (GATE ECO-003) — chỉ mới tải được hoặc mở được, chưa xác "
        "nhận hoàn tất quy trình."
        for e in entries
        if e.published_status in NEVER_USABLE_STATUSES
    ]


def _load_catalog_or_error(operation_id: str) -> tuple[Envelope | None, tuple[ServiceEntry, ...]]:
    """Tải danh bạ; trả ``(error_envelope, ())`` nếu hỏng, hoặc ``(None, entries)``.

    Danh bạ hỏng là lỗi NỘI BỘ (dữ liệu đóng gói cùng repo, không phải input
    người dùng tại runtime) — không có mã ``ErrorCode`` chuyên biệt nào khớp
    hơn ``E_INTERNAL`` trong M1-INTERFACES §3.
    """

    try:
        entries = load_service_catalog()
    except ServiceCatalogLoadError as exc:
        return (
            error_envelope(
                operation_id,
                ErrorCode.E_INTERNAL,
                "Không đọc được danh bạ dịch vụ (dữ liệu đóng gói cùng repo bị hỏng).",
                details={"reason": str(exc)},
            ),
            (),
        )
    return None, entries


def _handle_service_list(operation_id: str) -> Envelope:
    err, entries = _load_catalog_or_error(operation_id)
    if err is not None:
        return err
    listed, working = listed_vs_working(entries)
    warnings = [
        # ECO-022: "100 phần mềm được liệt kê" KHÔNG đồng nghĩa "100 phần
        # mềm chạy được" — luôn nói rõ cả hai số cùng lúc trong warnings.
        f"Danh bạ liệt kê {listed} dịch vụ; CHỈ {working} trong số đó đang ở "
        "workflow_verified (đã xác nhận nộp/nhận thật) — số liệt kê KHÔNG "
        "đồng nghĩa số dùng được (ECO-022).",
        *_never_usable_warnings(entries),
    ]
    return ok_envelope(
        operation_id,
        {
            "entries": [_service_entry_summary(e) for e in entries],
            "listed": listed,
            "workflow_verified": working,
        },
        warnings=warnings,
    )


def _handle_service_search(operation_id: str, query: str, limit: int) -> Envelope:
    err, entries = _load_catalog_or_error(operation_id)
    if err is not None:
        return err
    if limit <= 0:
        return error_envelope(
            operation_id,
            ErrorCode.E_INPUT_SCHEMA,
            "'--limit' phải là số nguyên dương.",
            details={"limit": limit},
        )
    hits = search_services(entries, query, limit=limit)
    warnings = _never_usable_warnings(h.entry for h in hits)
    return ok_envelope(
        operation_id,
        {
            "query": query,
            "hits": [
                {
                    **_service_entry_summary(h.entry),
                    "requires_account_or_token": h.requires_account_or_token,
                }
                for h in hits
            ],
        },
        warnings=warnings,
    )


def _handle_service_inspect(operation_id: str, service_id: str) -> Envelope:
    err, entries = _load_catalog_or_error(operation_id)
    if err is not None:
        return err
    by_id = {e.id: e for e in entries}
    entry = by_id.get(service_id)
    if entry is None:
        return error_envelope(
            operation_id,
            ErrorCode.E_INPUT_SCHEMA,
            f"Không tìm thấy dịch vụ với id '{service_id}' trong danh bạ.",
            details={"id": service_id},
        )
    warnings = _never_usable_warnings((entry,))
    return ok_envelope(operation_id, _service_entry_full(entry), warnings=warnings)


def _dispatch(ns: argparse.Namespace, deps: CliDependencies) -> Envelope:
    operation_id = new_operation_id()
    command = ns.command

    if command == "doctor":
        return _handle_doctor(operation_id)
    if command == "catalog" and ns.catalog_command == "validate":
        return _handle_catalog_validate(operation_id, ns.path, deps)
    if command == "app":
        if ns.app_command == "inspect":
            return _handle_app_inspect(operation_id, ns.path, deps)
        if ns.app_command == "plan-install":
            return _handle_app_plan_install(operation_id, ns.path, deps)
        if ns.app_command == "install":
            return _handle_app_install(operation_id)
    if command == "evidence" and ns.evidence_command == "validate":
        return _handle_evidence_validate(operation_id, ns.path, deps)
    if command == "service":
        if ns.service_command == "list":
            return _handle_service_list(operation_id)
        if ns.service_command == "search":
            return _handle_service_search(operation_id, ns.query, ns.limit)
        if ns.service_command == "inspect":
            return _handle_service_inspect(operation_id, ns.id)

    # Không đạt được nếu `required=True` trên mọi subparsers — giữ lại để
    # không bao giờ trả `ok` giả cho một lệnh không xác định.
    return error_envelope(operation_id, ErrorCode.E_INTERNAL, "Lệnh không xác định.")


def _render_human(stream: IO[str], env: Envelope) -> None:
    """In một dòng tiếng Việt ngắn cho người đọc khi KHÔNG dùng ``--json``.

    KHÔNG dùng cho luồng máy đọc — chỉ tiện khi gõ tay tại terminal.
    """

    if env.status == "ok":
        stream.write(f"OK (operation_id={env.operation_id})\n")
    else:
        assert env.error is not None
        stream.write(f"LỖI [{env.error.code}]: {env.error.message_vi}\n")


def main(
    argv: list[str] | None = None,
    *,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
    deps: CliDependencies | None = None,
) -> int:
    """Entry point CLI thuần hàm — KHÔNG tự ``sys.exit`` (caller/script quyết
    định). Trả exit code 0-9 theo bảng CLI-003."""

    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    # Khi caller KHÔNG truyền ``deps`` (tham số hoàn toàn vắng, không phải
    # ``CliDependencies()`` rỗng tường minh), WIRING tích hợp dùng
    # implementation THẬT (end-to-end) — xem ``namios_cli.deps.
    # default_dependencies``. Truyền ``deps=CliDependencies()`` tường minh
    # (như test đơn vị/QA làm) vẫn giữ hành vi "chưa wiring" cũ, KHÔNG đổi.
    active_deps = deps if deps is not None else default_dependencies()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]

    try:
        ns = parse_args(raw_argv)
    except ArgumentParsingError as exc:
        operation_id = new_operation_id()
        if "--json" in raw_argv:
            env = error_envelope(
                operation_id,
                ErrorCode.E_INPUT_SCHEMA,
                "Tham số dòng lệnh không hợp lệ.",
                details=None,
            )
            emit_json(env, out)
            return int(envelope_exit_code(env))
        if exc.message:
            err.write(exc.message)
        return 0 if exc.status == 0 else 2

    try:
        env = _dispatch(ns, active_deps)
    except Exception as exc:  # noqa: BLE001 — biên bắt lỗi cuối cùng của CLI:
        # BẤT KỲ exception chưa được xử lý cụ thể từ implementation downstream
        # (install_planner.build_plan, manifest_validator.validate_semantic,
        # evidence_validator.compute_allowed_status, v.v.) PHẢI trở thành
        # envelope JSON status=error/E_INTERNAL, KHÔNG BAO GIỜ thoát khỏi
        # main() hay làm tiến trình crash. KHÔNG lộ str(exc) ra envelope.
        operation_id = new_operation_id()
        env = error_envelope(
            operation_id,
            ErrorCode.E_INTERNAL,
            "Lỗi nội bộ không xác định khi xử lý lệnh.",
            details={"reason": type(exc).__name__},
        )
    use_json = bool(getattr(ns, "json", False))
    if use_json:
        emit_json(env, out)
    else:
        _render_human(out, env)
    return int(envelope_exit_code(env))


def run() -> None:
    """Console-script entry point (``[project.scripts] namios``).

    Mỏng — chỉ gọi ``main()`` với ``sys.argv``/``sys.stdout``/``sys.stderr``
    thật (deps=None ⇒ wiring thật qua ``default_dependencies()``) rồi
    ``sys.exit`` đúng exit code 0-9 (CLI-003). KHÔNG thêm logic ở đây."""

    sys.exit(main())
