"""Entry point + dispatch subcommand cho ``namios`` CLI (WP3).

Khung subcommand cho ``catalog validate``/``app inspect|plan-install|install``/
``evidence validate`` gọi Protocol tương ứng qua ``CliDependencies`` (dependency
injection — WP3 KHÔNG import implementation cứng của WP khác). Khi một
Protocol chưa được nối (``None``), subcommand trả envelope lỗi rõ ràng
(``E_INTERNAL``) thay vì giả lập kết quả hay crash không kiểm soát.

``namios doctor`` là subcommand WP3 hiện thực ĐẦY ĐỦ (capability report host
thật — xem ``namios_doctor``).
"""

from __future__ import annotations

import argparse
import sys
from typing import IO

from namios_cli.deps import CliDependencies
from namios_cli.envelope_io import emit_json, envelope_exit_code, new_operation_id
from namios_cli.errors import error_envelope, ok_envelope
from namios_cli.parser import ArgumentParsingError, parse_args
from namios_core.envelope import Envelope
from namios_core.errors import ErrorCode
from namios_core.validation import SemanticContext
from namios_doctor.doctor import build_doctor_data


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
    active_deps = deps if deps is not None else CliDependencies()
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
