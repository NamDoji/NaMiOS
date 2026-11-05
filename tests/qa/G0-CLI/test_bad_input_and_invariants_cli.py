"""QA tester integration — input xấu + bất biến chung cho MỌI subcommand
CLI thật (``deps=None`` ⇒ wiring thật qua ``default_dependencies()``).

Khẳng định bất biến (nhiệm vụ giao):
- stdout khi ``--json`` LUÔN đúng 1 dòng JSON parse được.
- exit code thuộc 0-9, KHÔNG BAO GIỜ 1.
- KHÔNG exception thoát ra khỏi ``main()``.
- Input xấu (path không tồn tại, ``--json`` kèm ``-h``) được xử lý có kiểm
  soát, không crash.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

# "G0-CLI" chứa dấu gạch ngang → không thể import tương đối; dùng path tuyệt
# đối trực tiếp (không chia sẻ module helper giữa các file trong thư mục này).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_INTEGRATION_MANIFEST_DIR = _REPO_ROOT / "tests" / "integration" / "fixtures" / "manifest"


def integration_manifest_fixture_path(name: str) -> str:
    return str(_INTEGRATION_MANIFEST_DIR / name)


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


# --- path không tồn tại cho mọi subcommand nhận path -----------------------


@pytest.mark.parametrize(
    "argv_prefix",
    [
        ["catalog", "validate"],
        ["app", "inspect"],
        ["app", "plan-install"],
        ["evidence", "validate"],
    ],
)
def test_nonexistent_path_never_crashes_and_stays_in_exit_range(
    argv_prefix: list[str],
) -> None:
    path = "/tmp/namios-qa-g0-cli-khong-ton-tai-tuyet-doi-123456789.json"
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main([*argv_prefix, path, "--json"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001 — chính là điều đang kiểm tra
        pytest.fail(
            f"DEFECT: lệnh {argv_prefix} với path không tồn tại làm main() "
            f"crash bằng {type(exc).__name__}({exc!r}) thay vì trả envelope "
            "lỗi."
        )
    assert 0 <= rc <= 9
    assert rc != 1
    lines = out.getvalue().splitlines()
    assert len(lines) == 1, f"{argv_prefix}: stdout --json phải đúng 1 dòng JSON"
    parsed = json.loads(lines[0])  # phải parse được — không trộn log vào stdout
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"] is not None


def test_path_traversal_like_input_never_crashes() -> None:
    """Không phải test an toàn path chi tiết (đó là ``tests/security/``) —
    chỉ xác nhận lớp CLI không crash/không lộ thông tin khi nhận path adversarial."""

    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(
            ["app", "inspect", "../../../../etc/passwd", "--json"],
            stdout=out,
            stderr=err,
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"DEFECT: path traversal-like làm main() crash: {exc!r}")
    assert 0 <= rc <= 9
    assert rc != 1
    parsed = json.loads(out.getvalue().splitlines()[0])
    assert parsed["status"] == "error"


# --- --json kèm -h ----------------------------------------------------------


def test_json_flag_combined_with_help_flag_does_not_crash_and_stays_controlled() -> None:
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["doctor", "--json", "-h"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"DEFECT: '--json -h' làm main() crash: {exc!r}")
    assert 0 <= rc <= 9
    assert rc != 1
    # Không crash — nhưng xem DEFECT riêng ngay dưới: khi stdout là sys.stdout
    # THẬT (không truyền ``stdout=`` tường minh, như console-script thật),
    # help text của argparse bị trộn vào CÙNG stdout với dòng JSON envelope.
    stdout_val = out.getvalue()
    if stdout_val.strip().startswith("{"):
        lines = stdout_val.splitlines()
        assert len(lines) == 1
        json.loads(lines[0])  # phải parse được nếu CLI chọn in JSON cho -h


# ĐÃ VÁ (02/11/2026): _NonExitingArgumentParser nay override _print_message để
# gom help/usage text vào ArgumentParsingError thay vì ghi thẳng sys.stdout thật.
# Nhờ đó 'namios <cmd> --json -h' chỉ in ĐÚNG 1 dòng JSON envelope (exit 2) — không
# còn rò help text. Test chuyển từ xfail(strict) evidence-defect sang khẳng định
# bất biến CLI-001 (khoá cố định bản vá).
def test_json_with_help_emits_single_json_line_no_help_leak(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["doctor", "--json", "-h"])  # KHÔNG truyền stdout= ⇒ dùng sys.stdout thật
    captured = capsys.readouterr()
    assert rc == ExitCode.INPUT
    lines = captured.out.splitlines()
    # Bất biến bắt buộc: PHẢI đúng 1 dòng JSON parse được trên stdout thật.
    assert len(lines) == 1, (
        f"DEFECT: stdout thật có {len(lines)} dòng (lẫn argparse help text), "
        f"không phải 1 dòng JSON như CLI-001 yêu cầu: {captured.out!r}"
    )
    json.loads(lines[0])


def test_help_flag_alone_does_not_crash() -> None:
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["-h"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"DEFECT: '-h' làm main() crash: {exc!r}")
    assert 0 <= rc <= 9
    assert rc != 1


def test_missing_required_subcommand_does_not_crash() -> None:
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main([], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"DEFECT: argv rỗng làm main() crash: {exc!r}")
    assert 0 <= rc <= 9
    assert rc != 1


def test_unknown_subcommand_does_not_crash() -> None:
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["khong-ton-tai-command", "--json"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"DEFECT: subcommand không rõ làm main() crash: {exc!r}")
    assert 0 <= rc <= 9
    assert rc != 1


def test_malformed_json_file_as_manifest_path_does_not_crash() -> None:
    """File tồn tại nhưng KHÔNG phải JSON hợp lệ — ``.load()`` của WP2 phải
    raise có kiểm soát, CLI chuẩn hoá về envelope lỗi, không crash."""

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
        handle.write("{ không phải json hợp lệ ][")
        tmp_path = handle.name
    try:
        out, err = io.StringIO(), io.StringIO()
        try:
            rc = main(["app", "inspect", tmp_path, "--json"], stdout=out, stderr=err)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"DEFECT: JSON malformed làm main() crash: {exc!r}")
        assert 0 <= rc <= 9
        assert rc != 1
        parsed = json.loads(out.getvalue().splitlines()[0])
        assert parsed["status"] == "error"
    finally:
        import os

        os.unlink(tmp_path)


# --- bất biến chéo mọi subcommand happy-path --------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["doctor", "--json"],
        ["catalog", "validate", integration_manifest_fixture_path("valid-demo-app.json"), "--json"],
        ["app", "inspect", integration_manifest_fixture_path("valid-demo-app.json"), "--json"],
        ["app", "plan-install", integration_manifest_fixture_path("valid-demo-app.json"), "--json"],
    ],
)
def test_json_stdout_is_always_exactly_one_parseable_line_and_exit_in_range(
    argv: list[str],
) -> None:
    rc, out, err = _run(argv)
    assert 0 <= rc <= 9
    assert rc != 1
    assert err == "", f"{argv}: KHÔNG được trộn log vào stderr khi --json ok"
    lines = out.splitlines()
    assert len(lines) == 1, f"{argv}: stdout phải đúng 1 dòng JSON"
    envelope = json.loads(lines[0])
    assert envelope["api_version"] == "1.0"
    assert envelope["status"] in ("ok", "error")
    if envelope["status"] == "ok":
        assert envelope["error"] is None
    else:
        assert envelope["data"] is None
        assert envelope["error"] is not None


def test_exit_code_one_is_never_used_across_known_commands() -> None:
    """Exit code 1 'không dùng' (M1-INTERFACES §2) — kiểm tra một lượt qua
    các lệnh/đường happy+error đã biết, không riêng một case."""

    scenarios: list[list[str]] = [
        ["doctor", "--json"],
        ["app", "install", "fake-plan", "--json"],
        [
            "app",
            "inspect",
            "/tmp/namios-qa-g0-cli-khong-ton-tai-tuyet-doi-123456789.json",
            "--json",
        ],
    ]
    for argv in scenarios:
        rc, _out, _err = _run(argv)
        assert rc != 1, f"{argv}: exit code 1 bị cấm dùng theo CLI-003"
