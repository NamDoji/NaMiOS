"""Test ``namios_cli.parser`` — argv-only, ``--`` kết thúc options
(FACT CLI-001/COMP-004), không bao giờ exec/shell."""

from __future__ import annotations

import pytest

from namios_cli.parser import ArgumentParsingError, parse_args


def test_doctor_json_flag_parses() -> None:
    ns = parse_args(["doctor", "--json"])
    assert ns.command == "doctor"
    assert ns.json is True


def test_doctor_without_json_flag_defaults_false() -> None:
    ns = parse_args(["doctor"])
    assert ns.json is False


@pytest.mark.parametrize(
    "argv",
    [
        ["app", "inspect", "--", "--looks-like-an-option.json"],
        ["catalog", "validate", "--", "-x"],
        ["evidence", "validate", "--", "--json"],  # path LITERALLY "--json" sau `--`
    ],
)
def test_double_dash_treats_following_token_as_positional_data(argv: list[str]) -> None:
    ns = parse_args(argv)
    # giá trị sau `--` phải được gán cho positional `path`, KHÔNG bị hiểu
    # thành option/flag của chương trình (FACT COMP-004: argv-only, `--`
    # kết thúc options).
    assert ns.path == argv[-1]
    # cờ --json thật của CLI vẫn ở giá trị mặc định False vì `--json` ở đây
    # là DỮ LIỆU path, không phải option.
    assert ns.json is False


def test_path_value_containing_shell_metacharacters_stays_literal_data() -> None:
    dangerous = "; rm -rf ~ #"
    ns = parse_args(["app", "inspect", "--", dangerous])
    assert ns.path == dangerous  # không bị argparse/parser "hiểu" thành gì khác


def test_unknown_top_level_command_raises_argument_parsing_error() -> None:
    with pytest.raises(ArgumentParsingError) as excinfo:
        parse_args(["khong-ton-tai"])
    assert excinfo.value.status != 0


def test_missing_required_positional_raises_argument_parsing_error() -> None:
    with pytest.raises(ArgumentParsingError):
        parse_args(["app", "inspect"])


def test_missing_subcommand_for_app_raises_argument_parsing_error() -> None:
    with pytest.raises(ArgumentParsingError):
        parse_args(["app"])


def test_evidence_validate_requires_path() -> None:
    with pytest.raises(ArgumentParsingError):
        parse_args(["evidence", "validate"])


def test_app_install_takes_plan_id_positional() -> None:
    ns = parse_args(["app", "install", "plan-xyz", "--json"])
    assert ns.plan_id == "plan-xyz"
    assert ns.json is True
