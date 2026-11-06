"""Lớp common song ngữ của tầng SYS (Phụ lục 05) — đăng ký qua
``namios_i18n.add_catalog`` khi import (giống ``namios_compat._i18n``).

Trường DỮ LIỆU ``*_vi``/``message_vi`` luôn tiếng Việt (call-site ép
``lang=Lang.VI``); chỉ help/usage CLI đổi theo ``--lang``. Module dùng
``t("sys.*")`` phải import module này: ``from namios_sys import _i18n as _i18n``.
"""

from __future__ import annotations

from namios_i18n import Lang, add_catalog

__all__: list[str] = []

_VI: dict[str, str] = {
    # action broker (SYS-001)
    "sys.action.ok": "Hành động '{action}' hoàn tất.",
    "sys.action.blocked_no_handler": (
        "Hành động '{action}' chưa chạy được ở đây — cần desktop/thiết bị thật "
        "(chưa nối handler). KHÔNG coi là đã xong."
    ),
    "sys.action.unknown": "Hành động '{action}' không có trong action broker — từ chối.",
    "sys.action.denied": "Chính sách tổ chức chặn hành động '{action}'.",
    # schema (SYS-037)
    "sys.schema.route_no_version": "app_route thiếu 'version' — không khớp được hồ sơ tương thích.",
    "sys.schema.route_no_source": (
        "app_route thiếu nguồn (publisher/installer_hash) cho mode cần bộ cài."
    ),
    "sys.schema.step_no_evidence": (
        "Bước '{step}' báo thành công nhưng THIẾU evidence — app mở được ≠ hoàn thành."
    ),
    # certification (SYS-013)
    "sys.cert.need_business": (
        "Chạy kỹ thuật đạt nhưng CHƯA có xác nhận nghiệp vụ — hạ xuống một phần (SYS-013)."
    ),
    "sys.cert.need_external": (
        "Thiếu hoàn tất với bên ngoài (biên nhận/nộp) — chặn phụ thuộc ngoài, chưa verified."
    ),
    "sys.cert.verified": "Đã kiểm đầu-cuối: chạy kỹ thuật + nghiệp vụ + hoàn tất bên ngoài.",
    "sys.cert.not_usable": "Chưa dùng được: mới ở mức tải/mở — chưa kiểm workflow (SYS-013).",
    # capability catalog (SYS-038)
    "sys.capability.overclaim": (
        "Dòng khả năng tự nhận 'dùng được' khi chưa đủ bằng chứng — bị chặn (SYS-038)."
    ),
    "sys.capability.untested": "Chưa kiểm: {app} {version} — chưa có phiếu kiểm workflow.",
    # CLI (song ngữ theo --lang)
    "sys.cli.parser.cmd_help": (
        "Tầng hệ điều hành NaMiOS: action broker + hồ sơ dùng chung (desktop/CLI/SmartAI)."
    ),
    "sys.cli.parser.actions_help": "Liệt kê các hành động desktop + trạng thái nối handler.",
    "sys.cli.parser.capability_help": (
        "Tra mức khả năng THẬT của một app/version (hoặc 'chưa kiểm')."
    ),
    "sys.cli.parser.arg.app": "Mã ứng dụng (vd 'misa').",
    "sys.cli.parser.arg.version": "Phiên bản ứng dụng (vd '2024').",
    "sys.cli.parser.routecheck_help": (
        "Kiểm một app_route JSON đã đủ điều kiện (nguồn/version) chưa — chưa cài."
    ),
    "sys.cli.parser.arg.route_path": "Đường dẫn file app_route JSON.",
    "sys.cli.error.route_load": "Không đọc được app_route JSON '{path}': {reason}.",
}

_EN: dict[str, str] = {
    "sys.action.ok": "Action '{action}' completed.",
    "sys.action.blocked_no_handler": (
        "Action '{action}' cannot run here — needs a real desktop/device (no handler wired). "
        "NOT counted as done."
    ),
    "sys.action.unknown": "Action '{action}' is not in the action broker — refused.",
    "sys.action.denied": "Organization policy blocks action '{action}'.",
    "sys.schema.route_no_version": (
        "app_route is missing 'version' — cannot match a compat profile."
    ),
    "sys.schema.route_no_source": (
        "app_route is missing a source (publisher/installer_hash) for an installer-based mode."
    ),
    "sys.schema.step_no_evidence": (
        "Step '{step}' reports success but has NO evidence — an app opening ≠ completion."
    ),
    "sys.cert.need_business": (
        "Technical run passed but business sign-off is MISSING — downgraded to partial (SYS-013)."
    ),
    "sys.cert.need_external": (
        "Missing external completion (receipt/submission) — blocked external dependency, "
        "not verified."
    ),
    "sys.cert.verified": "End-to-end verified: technical run + business + external completion.",
    "sys.cert.not_usable": "Not usable yet: only download/launch level — workflow not verified.",
    "sys.capability.overclaim": (
        "A capability row claims 'usable' without enough evidence — blocked (SYS-038)."
    ),
    "sys.capability.untested": "Not tested: {app} {version} — no workflow test card yet.",
    "sys.cli.parser.cmd_help": (
        "NaMiOS OS layer: action broker + shared records (desktop/CLI/SmartAI)."
    ),
    "sys.cli.parser.actions_help": "List desktop actions + handler-wiring status.",
    "sys.cli.parser.capability_help": "Look up the real capability level of an app/version.",
    "sys.cli.parser.arg.app": "Application id (e.g. 'misa').",
    "sys.cli.parser.arg.version": "Application version (e.g. '2024').",
    "sys.cli.parser.routecheck_help": (
        "Check whether an app_route JSON is well-formed (source/version) — does not install."
    ),
    "sys.cli.parser.arg.route_path": "Path to an app_route JSON file.",
    "sys.cli.error.route_load": "Could not read app_route JSON '{path}': {reason}.",
}

add_catalog(Lang.VI, _VI)
add_catalog(Lang.EN, _EN)
