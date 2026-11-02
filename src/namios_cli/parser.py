"""Argparse parser cho ``namios`` CLI (WP3) — argv-only, ``--`` kết thúc
options (FACT CLI-001/COMP-004). KHÔNG bao giờ ghép argv thành chuỗi shell;
``argparse`` tự tách option/positional, giá trị positional (ví dụ đường dẫn
bắt đầu bằng ``-``) luôn được giữ nguyên là DỮ LIỆU sau dấu ``--``.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import NoReturn


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


def _add_json_flag(sub: argparse.ArgumentParser) -> None:
    sub.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="In kết quả dưới dạng envelope JSON (CLI-001) ra stdout.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Dựng parser gốc ``namios`` với khung subcommand M1.

    Wiring implementation thật của từng subcommand (ngoại trừ ``doctor``,
    do WP3 hiện thực đầy đủ) thuộc các WP khác — xem ``namios_cli.main``
    và ``namios_cli.deps.CliDependencies``.
    """

    parser = _NonExitingArgumentParser(
        prog="namios",
        description="NaMiOS CLI (M1 — lõi Python thuần).",
    )
    top = parser.add_subparsers(dest="command", required=True)

    doctor_parser = top.add_parser("doctor", help="Capability report host thật.")
    _add_json_flag(doctor_parser)

    catalog_parser = top.add_parser("catalog", help="Thao tác catalog ứng dụng.")
    catalog_sub = catalog_parser.add_subparsers(dest="catalog_command", required=True)
    catalog_validate = catalog_sub.add_parser("validate", help="Thẩm định một manifest.")
    catalog_validate.add_argument("path", help="Đường dẫn file manifest.")
    _add_json_flag(catalog_validate)

    app_parser = top.add_parser("app", help="Thao tác trên một ứng dụng.")
    app_sub = app_parser.add_subparsers(dest="app_command", required=True)

    app_inspect = app_sub.add_parser("inspect", help="Xem tóm tắt manifest.")
    app_inspect.add_argument("path", help="Đường dẫn file manifest.")
    _add_json_flag(app_inspect)

    app_plan_install = app_sub.add_parser("plan-install", help="Dựng install plan.")
    app_plan_install.add_argument("path", help="Đường dẫn file manifest.")
    _add_json_flag(app_plan_install)

    app_install = app_sub.add_parser("install", help="Áp dụng install plan (M1: BLOCKED).")
    app_install.add_argument("plan_id", help="ID plan đã dựng trước.")
    _add_json_flag(app_install)

    evidence_parser = top.add_parser("evidence", help="Thao tác evidence report.")
    evidence_sub = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    evidence_validate = evidence_sub.add_parser("validate", help="Thẩm định evidence report.")
    evidence_validate.add_argument("path", help="Đường dẫn file evidence report.")
    _add_json_flag(evidence_validate)

    # ECO-006/ECO-007/ECO-022 — danh bạ dịch vụ/phần mềm thiết yếu VN
    # (``catalog/services/*.json``). Chỉ ĐỌC danh bạ tĩnh đóng gói cùng repo,
    # KHÔNG thực thi/tải/cài gì (namios_eco KHÔNG có trường lệnh).
    service_parser = top.add_parser(
        "service", help="Danh bạ dịch vụ/phần mềm thiết yếu Việt Nam (ECO-006)."
    )
    service_sub = service_parser.add_subparsers(dest="service_command", required=True)

    service_list = service_sub.add_parser(
        "list", help="Liệt kê toàn bộ danh bạ (trạng thái công bố trung thực — ECO-003)."
    )
    _add_json_flag(service_list)

    service_search = service_sub.add_parser(
        "search", help="Tìm theo tên phổ thông, có/không dấu (ECO-007)."
    )
    service_search.add_argument("query", help="Từ khoá tìm kiếm (vd 'khai thuế', 'hoc bac').")
    service_search.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Số kết quả tối đa trả về (mặc định 50).",
    )
    _add_json_flag(service_search)

    service_inspect = service_sub.add_parser(
        "inspect", help="Xem đầy đủ một entry theo id ổn định."
    )
    service_inspect.add_argument("id", help="ID ổn định của entry (vd 'thue.htkk').")
    _add_json_flag(service_inspect)

    return parser


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse ``argv`` (KHÔNG gồm tên chương trình) qua parser gốc.

    Ném ``ArgumentParsingError`` khi argv sai (subcommand thiếu/không rõ,
    thiếu positional, ``-h``/``--help``) — KHÔNG tự ``sys.exit``.
    """

    parser = build_parser()
    return parser.parse_args(list(argv))
