"""Argparse parser cho ``namios`` CLI (WP3) — argv-only, ``--`` kết thúc
options (FACT CLI-001/COMP-004). KHÔNG bao giờ ghép argv thành chuỗi shell;
``argparse`` tự tách option/positional, giá trị positional (ví dụ đường dẫn
bắt đầu bằng ``-``) luôn được giữ nguyên là DỮ LIỆU sau dấu ``--``.

Song ngữ (đợt nâng cấp i18n 03/11/2026): mọi description/help text của
argparse đi qua ``namios_i18n.t(key, lang=...)`` — xem ``docs/specs/I18N.md``
nhóm key ``cli.parser.*`` (đã seed sẵn VI/EN). Đây là phần HELP/USAGE hiển
thị cho người gõ lệnh, KHÔNG phải nội dung envelope JSON (``message_vi``/
``warnings`` của ``Envelope`` LUÔN tiếng Việt theo hợp đồng dữ liệu
M1-INTERFACES §1/§3 — xem ``namios_cli.main``, module đó KHÔNG đổi theo
``--lang``). Cờ toàn cục ``--lang vi|en`` (ưu tiên hơn biến môi trường
``NAMIOS_LANG``) CHỈ ảnh hưởng tới help/usage text + wrapper người-đọc ở
``_render_human``, phải đặt TRƯỚC tên lệnh con (option của parser gốc, không
phải của từng subparser).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import NoReturn

from namios_compat import _i18n as _compat_i18n  # noqa: F401  (đăng ký catalog i18n compat.*)
from namios_i18n import Lang, add_catalog, resolve_lang, t
from namios_smartai import _i18n as _sai_i18n  # noqa: F401  (đăng ký catalog i18n sai.*)

# Key riêng của ``namios_cli`` (chưa có trong catalog gốc ``namios_i18n`` lúc
# seed 03/11/2026) — góp qua ``add_catalog`` theo đúng hợp đồng I18N.md §4
# (KHÔNG sửa trực tiếp ``namios_i18n/locale/*.json``).
add_catalog(
    Lang.VI,
    {
        "cli.parser.flag.lang_help": (
            "Ngôn ngữ hiển thị trợ giúp/thông báo người-đọc: 'vi' (mặc định) hoặc "
            "'en' — đặt TRƯỚC tên lệnh con (vd 'namios --lang en doctor'). Ưu tiên "
            "hơn biến môi trường NAMIOS_LANG. KHÔNG đổi nội dung envelope JSON "
            "(message_vi/warnings luôn tiếng Việt theo hợp đồng dữ liệu)."
        ),
    },
)
add_catalog(
    Lang.EN,
    {
        "cli.parser.flag.lang_help": (
            "Display language for help/human-readable output: 'vi' (default) or "
            "'en' — put it BEFORE the subcommand (e.g. 'namios --lang en doctor'). "
            "Takes priority over the NAMIOS_LANG environment variable. Does NOT "
            "change the JSON envelope content (message_vi/warnings stay "
            "Vietnamese per the data contract)."
        ),
    },
)


class ArgumentParsingError(Exception):
    """Lỗi parse argv — thay cho ``SystemExit`` mặc định của argparse, để
    ``main()`` tự quyết định in envelope JSON hay thông báo người-đọc."""

    def __init__(self, status: int, message: str | None) -> None:
        super().__init__(message or "")
        self.status = status
        self.message = message


class _NonExitingArgumentParser(argparse.ArgumentParser):
    """``ArgumentParser`` KHÔNG tự ``sys.exit`` — ném ``ArgumentParsingError``
    để caller (``namios_cli.main``) kiểm soát toàn bộ output/exit code,
    tránh trộn thông báo argparse vào luồng JSON stdout khi ``--json``.

    Quan trọng (CLI-001): ``-h``/``--help`` của argparse mặc định gọi
    ``print_help()`` → ghi THẲNG ra ``sys.stdout`` THẬT TRƯỚC khi ``exit()``
    — bỏ qua stream caller truyền vào ``main()``, làm rò help text lẫn với
    dòng JSON. Ta override ``_print_message`` để KHÔNG ghi ra stream thật mà
    gom lại, rồi đính kèm vào ``ArgumentParsingError`` cho ``main()`` quyết
    định (envelope JSON khi ``--json``, hoặc in người-đọc khi không)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._captured_parts: list[str] = []

    def _print_message(self, message: str, file: object | None = None) -> None:
        if message:
            self._captured_parts.append(message)

    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:  # noqa: A003
        captured = "".join(self._captured_parts)
        self._captured_parts = []
        raise ArgumentParsingError(status, message or (captured or None))

    def error(self, message: str) -> NoReturn:
        raise ArgumentParsingError(2, f"{self.prog}: error: {message}\n")


def _add_json_flag(sub: argparse.ArgumentParser, lang: Lang) -> None:
    sub.add_argument(
        "--json",
        action="store_true",
        default=False,
        help=t("cli.parser.flag.json_help", lang=lang),
    )


def build_parser(lang: Lang | str | None = None) -> argparse.ArgumentParser:
    """Dựng parser gốc ``namios`` với khung subcommand M1.

    ``lang`` chọn ngôn ngữ của MỌI description/help text (đi qua
    ``namios_i18n.t``) — không có tham số (``None``) thì phân giải qua
    ``resolve_lang`` (env ``NAMIOS_LANG`` > VI mặc định, xem
    ``namios_i18n.resolve_lang``). Chỉ ảnh hưởng help/usage hiển thị cho
    người gõ lệnh; KHÔNG ảnh hưởng envelope JSON (xem ``namios_cli.main``).

    Wiring implementation thật của từng subcommand (ngoại trừ ``doctor``,
    do WP3 hiện thực đầy đủ) thuộc các WP khác — xem ``namios_cli.main``
    và ``namios_cli.deps.CliDependencies``.
    """

    resolved = resolve_lang(lang)
    parser = _NonExitingArgumentParser(
        prog="namios",
        description=t("cli.parser.description", lang=resolved),
    )
    parser.add_argument(
        "--lang",
        choices=[item.value for item in Lang],
        default=None,
        help=t("cli.parser.flag.lang_help", lang=resolved),
    )
    top = parser.add_subparsers(dest="command", required=True)

    doctor_parser = top.add_parser("doctor", help=t("cli.parser.cmd.doctor_help", lang=resolved))
    _add_json_flag(doctor_parser, resolved)

    catalog_parser = top.add_parser("catalog", help=t("cli.parser.cmd.catalog_help", lang=resolved))
    catalog_sub = catalog_parser.add_subparsers(dest="catalog_command", required=True)
    catalog_validate = catalog_sub.add_parser(
        "validate", help=t("cli.parser.cmd.catalog_validate_help", lang=resolved)
    )
    catalog_validate.add_argument(
        "path", help=t("cli.parser.arg.manifest_path_help", lang=resolved)
    )
    _add_json_flag(catalog_validate, resolved)

    app_parser = top.add_parser("app", help=t("cli.parser.cmd.app_help", lang=resolved))
    app_sub = app_parser.add_subparsers(dest="app_command", required=True)

    app_inspect = app_sub.add_parser(
        "inspect", help=t("cli.parser.cmd.app_inspect_help", lang=resolved)
    )
    app_inspect.add_argument("path", help=t("cli.parser.arg.manifest_path_help", lang=resolved))
    _add_json_flag(app_inspect, resolved)

    app_plan_install = app_sub.add_parser(
        "plan-install", help=t("cli.parser.cmd.app_plan_install_help", lang=resolved)
    )
    app_plan_install.add_argument(
        "path", help=t("cli.parser.arg.manifest_path_help", lang=resolved)
    )
    _add_json_flag(app_plan_install, resolved)

    app_install = app_sub.add_parser(
        "install", help=t("cli.parser.cmd.app_install_help", lang=resolved)
    )
    app_install.add_argument("plan_id", help=t("cli.parser.arg.plan_id_help", lang=resolved))
    _add_json_flag(app_install, resolved)

    evidence_parser = top.add_parser(
        "evidence", help=t("cli.parser.cmd.evidence_help", lang=resolved)
    )
    evidence_sub = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    evidence_validate = evidence_sub.add_parser(
        "validate", help=t("cli.parser.cmd.evidence_validate_help", lang=resolved)
    )
    evidence_validate.add_argument(
        "path", help=t("cli.parser.arg.evidence_path_help", lang=resolved)
    )
    _add_json_flag(evidence_validate, resolved)

    # ECO-006/ECO-007/ECO-022 — danh bạ dịch vụ/phần mềm thiết yếu VN
    # (``catalog/services/*.json``). Chỉ ĐỌC danh bạ tĩnh đóng gói cùng repo,
    # KHÔNG thực thi/tải/cài gì (namios_eco KHÔNG có trường lệnh).
    service_parser = top.add_parser("service", help=t("cli.parser.cmd.service_help", lang=resolved))
    service_sub = service_parser.add_subparsers(dest="service_command", required=True)

    service_list = service_sub.add_parser(
        "list", help=t("cli.parser.cmd.service_list_help", lang=resolved)
    )
    _add_json_flag(service_list, resolved)

    service_search = service_sub.add_parser(
        "search", help=t("cli.parser.cmd.service_search_help", lang=resolved)
    )
    service_search.add_argument("query", help=t("cli.parser.arg.service_query_help", lang=resolved))
    service_search.add_argument(
        "--limit",
        type=int,
        default=50,
        help=t("cli.parser.arg.service_limit_help", lang=resolved),
    )
    _add_json_flag(service_search, resolved)

    service_inspect = service_sub.add_parser(
        "inspect", help=t("cli.parser.cmd.service_inspect_help", lang=resolved)
    )
    service_inspect.add_argument("id", help=t("cli.parser.arg.service_id_help", lang=resolved))
    _add_json_flag(service_inspect, resolved)

    # COMP-050 — Trung tâm tương thích (Phụ lục 03). Chỉ ĐỌC catalog tĩnh
    # ``catalog/compat/*.json`` + chạy resolver/preflight; KHÔNG thực thi/cài gì.
    compat_parser = top.add_parser("compat", help=t("compat.cli.parser.cmd_help", lang=resolved))
    compat_sub = compat_parser.add_subparsers(dest="compat_command", required=True)

    compat_workflows = compat_sub.add_parser(
        "workflows", help=t("compat.cli.parser.workflows_help", lang=resolved)
    )
    _add_json_flag(compat_workflows, resolved)

    compat_route = compat_sub.add_parser(
        "route", help=t("compat.cli.parser.route_help", lang=resolved)
    )
    compat_route.add_argument(
        "workflow_id", help=t("compat.cli.parser.arg.workflow_id", lang=resolved)
    )
    compat_route.add_argument(
        "--app-version",
        dest="app_version",
        default=None,
        help=t("compat.cli.parser.arg.app_version", lang=resolved),
    )
    compat_route.add_argument(
        "--token-model",
        dest="token_model",
        default=None,
        help=t("compat.cli.parser.arg.token_model", lang=resolved),
    )
    compat_route.add_argument("--license-ok", dest="license_ok", action="store_true")
    compat_route.add_argument("--offline", dest="offline", action="store_true")
    compat_route.add_argument("--allow-remote", dest="allow_remote", action="store_true")
    _add_json_flag(compat_route, resolved)

    compat_preflight = compat_sub.add_parser(
        "preflight", help=t("compat.cli.parser.preflight_help", lang=resolved)
    )
    compat_preflight.add_argument(
        "workflow_id", help=t("compat.cli.parser.arg.workflow_id", lang=resolved)
    )
    _add_json_flag(compat_preflight, resolved)

    compat_evidence = compat_sub.add_parser(
        "evidence", help=t("compat.cli.parser.evidence_help", lang=resolved)
    )
    compat_evidence.add_argument(
        "workflow_id", help=t("compat.cli.parser.arg.workflow_id", lang=resolved)
    )
    _add_json_flag(compat_evidence, resolved)

    compat_blocker = compat_sub.add_parser(
        "blocker", help=t("compat.cli.parser.blocker_help", lang=resolved)
    )
    compat_blocker.add_argument(
        "workflow_id", help=t("compat.cli.parser.arg.workflow_id", lang=resolved)
    )
    _add_json_flag(compat_blocker, resolved)

    # SAI-001/002/050 — SmartAI (M0): chỉ LẬP KẾ HOẠCH tiếng Việt (chưa thực
    # thi) + liệt kê tool đã đăng ký. Dùng fake model provider (determinism).
    smartai_parser = top.add_parser("smartai", help=t("sai.cli.parser.cmd_help", lang=resolved))
    smartai_sub = smartai_parser.add_subparsers(dest="smartai_command", required=True)

    smartai_plan = smartai_sub.add_parser("plan", help=t("sai.cli.parser.plan_help", lang=resolved))
    smartai_plan.add_argument("intent", help=t("sai.cli.parser.arg.intent", lang=resolved))
    _add_json_flag(smartai_plan, resolved)

    smartai_tools = smartai_sub.add_parser(
        "tools", help=t("sai.cli.parser.tools_help", lang=resolved)
    )
    _add_json_flag(smartai_tools, resolved)

    smartai_diagnose = smartai_sub.add_parser(
        "diagnose", help=t("sai.cli.parser.diagnose_help", lang=resolved)
    )
    smartai_diagnose.add_argument("symptom", help=t("sai.cli.parser.arg.symptom", lang=resolved))
    _add_json_flag(smartai_diagnose, resolved)

    return parser


def _peek_lang_argv(argv: Sequence[str]) -> str | None:
    """Dò trước giá trị ``--lang`` (nếu có) trong ``argv`` thô, KHÔNG parse
    đầy đủ — cần giá trị này TRƯỚC khi dựng parser (``build_parser``) để
    help/usage text (vd ``-h``) hiện đúng ngôn ngữ ngay từ thông báo đầu
    tiên. Chỉ nhận dạng 2 dạng ``--lang <value>``/``--lang=<value>``; dừng ở
    ``--`` (từ đó về sau là dữ liệu positional, không phải option — FACT
    COMP-004). Giá trị không hợp lệ được ``resolve_lang`` (caller) chuẩn hoá
    an toàn về VI, hàm này KHÔNG tự validate."""

    it = iter(argv)
    for item in it:
        if item == "--":
            break
        if item == "--lang":
            return next(it, None)
        if item.startswith("--lang="):
            return item.split("=", 1)[1]
    return None


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse ``argv`` (KHÔNG gồm tên chương trình) qua parser gốc.

    Ném ``ArgumentParsingError`` khi argv sai (subcommand thiếu/không rõ,
    thiếu positional, ``-h``/``--help``) — KHÔNG tự ``sys.exit``.
    """

    argv_list = list(argv)
    display_lang = resolve_lang(_peek_lang_argv(argv_list))
    parser = build_parser(display_lang)
    return parser.parse_args(argv_list)
