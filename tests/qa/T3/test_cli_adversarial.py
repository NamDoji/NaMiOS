"""T3 — adversarial/negative: envelope JSON sạch, exit code đúng bảng
CLI-003, dispatch WP3 không crash khi implementation của WP2/WP6/WP9 trả
dữ liệu/raise lỗi bất thường. Độc lập với ``tests/unit/cli/test_main.py``
của dev — không import fakes của dev, tự dựng input adversarial riêng.
"""

from __future__ import annotations

import io
import json

import pytest

from namios_cli.deps import CliDependencies
from namios_cli.main import main
from namios_core.errors import ErrorCode
from namios_core.exitcodes import ExitCode

from ._qa_fakes import (
    QaEvidenceValidatorBadAllowedStatus,
    QaEvidenceValidatorRaisesOnGate,
    QaManifestValidatorBadErrorCode,
    QaManifestValidatorNotInstallReadyNoErrors,
    QaManifestValidatorOk,
    QaManifestValidatorRaisesOnSemantic,
    QaPlannerRaisesGenericException,
    QaPlannerRaisesPlanBuildError,
)


def _run(argv: list[str], deps: CliDependencies | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err, deps=deps)
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# DEFECT CLASS 1: exception từ implementation WP6 (install_planner.build_plan)
# thoát ra khỏi main() — vi phạm CLI-001 (mỗi lệnh --json PHẢI in đúng 1
# envelope JSON) và CLI-003 (exit code phải thuộc 0-9, mã 1 CỐ Ý không dùng).
# ---------------------------------------------------------------------------


def test_plan_install_uncaught_plan_build_error_breaks_json_contract() -> None:
    """``PlanBuildError`` (lỗi THẬT của WP6 khi app bị revoked/recipe bị từ
    chối — xem src/namios_planner/planner.py) KHÔNG được WP3 bắt lại ở
    ``_handle_app_plan_install``. Kỳ vọng hợp đồng: dù input "xấu" (app bị
    revoked), lệnh ``--json`` vẫn phải in envelope lỗi + exit 0-9. Thực tế
    quan sát: exception thoát ra ngoài ``main()``."""

    deps = CliDependencies(
        manifest_validator=QaManifestValidatorOk(),
        install_planner=QaPlannerRaisesPlanBuildError(),
    )
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(
            ["app", "plan-install", "fixture.json", "--json"], stdout=out, stderr=err, deps=deps
        )
    except Exception as exc:  # noqa: BLE001 — chính là điều đang kiểm tra
        pytest.fail(
            "DEFECT: main() để lộ exception "
            f"{type(exc).__name__}({exc!r}) ra ngoài khi install_planner.build_plan() "
            "raise PlanBuildError (case THẬT: app bị revoked). Lệnh --json phải LUÔN "
            "in đúng 1 envelope JSON + exit code 0-9, không được crash tiến trình."
        )
    # Nếu không fail ở trên thì hợp đồng vẫn đứng — khẳng định tường minh:
    assert 0 <= rc <= 9
    assert rc != 1
    json.loads(out.getvalue())  # phải là JSON hợp lệ, không phải traceback


def test_plan_install_uncaught_generic_exception_from_planner() -> None:
    """Biến thể: exception KHÔNG phải ``PlanBuildError`` (lỗi nội bộ bất kỳ
    của một implementation WP6 lỗi) cũng phải được chặn ở biên WP3, không
    crash tiến trình CLI."""

    deps = CliDependencies(
        manifest_validator=QaManifestValidatorOk(),
        install_planner=QaPlannerRaisesGenericException(),
    )
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(
            ["app", "plan-install", "fixture.json", "--json"], stdout=out, stderr=err, deps=deps
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            "DEFECT: exception nội bộ bất kỳ từ install_planner.build_plan() "
            f"({type(exc).__name__}) thoát ra ngoài main() thay vì thành "
            "envelope error ErrorCode.E_INTERNAL."
        )
    assert 0 <= rc <= 9
    json.loads(out.getvalue())


# ---------------------------------------------------------------------------
# DEFECT CLASS 2: exception từ validate_semantic (WP2) không được bọc —
# chỉ .load() được try/except trong _handle_catalog_validate.
# ---------------------------------------------------------------------------


def test_catalog_validate_uncaught_exception_from_validate_semantic() -> None:
    deps = CliDependencies(manifest_validator=QaManifestValidatorRaisesOnSemantic())
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(
            ["catalog", "validate", "fixture.json", "--json"], stdout=out, stderr=err, deps=deps
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            "DEFECT: validate_semantic() của WP2 raise exception không được "
            f"WP3 bắt lại ({type(exc).__name__}); chỉ .load() có try/except "
            "trong _handle_catalog_validate (xem src/namios_cli/main.py)."
        )
    assert 0 <= rc <= 9
    json.loads(out.getvalue())


def test_app_inspect_does_not_crash_when_manifest_has_surprising_mode_value() -> None:
    """Negative nhẹ: ``app inspect`` chỉ đọc lại field của manifest đã tải —
    không có logic nào khác để tấn công, nhưng xác nhận envelope luôn sạch
    dù manifest có giá trị biên (mode literal hợp lệ nhưng hiếm dùng)."""

    deps = CliDependencies(manifest_validator=QaManifestValidatorOk())
    rc, out, err = _run(["app", "inspect", "fixture.json", "--json"], deps)
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["data"]["mode"] == "native"


# ---------------------------------------------------------------------------
# DEFECT CLASS 3: mã lỗi lạ (không thuộc ErrorCode enum) từ ValidationError
# của WP2 làm ``ErrorCode(first.code)`` ném ValueError không được bắt.
# ---------------------------------------------------------------------------


def test_catalog_validate_unknown_error_code_from_validator_crashes_valueerror() -> None:
    deps = CliDependencies(manifest_validator=QaManifestValidatorBadErrorCode())
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(
            ["catalog", "validate", "fixture.json", "--json"], stdout=out, stderr=err, deps=deps
        )
    except ValueError as exc:
        pytest.fail(
            "DEFECT: WP2 trả ValidationError.code ngoài ErrorCode enum "
            f"('{exc}') làm ErrorCode(first.code) ném ValueError không được "
            "WP3 bắt lại — một bug nhỏ ở WP2 (hoặc lệch phiên bản) có thể "
            "crash toàn bộ CLI thay vì trả E_INTERNAL an toàn."
        )
    assert 0 <= rc <= 9
    json.loads(out.getvalue())


def test_catalog_validate_not_install_ready_with_empty_errors_tuple_exit_code() -> None:
    """Khi ``install_ready=False`` và ``errors=()`` cùng lúc (Protocol không
    cấm) — ghi lại CHÍNH XÁC ErrorCode/exit code WP3 chọn, để không thay đổi
    âm thầm sau này (`first=None -> ErrorCode.E_INTERNAL` theo code hiện tại)."""

    deps = CliDependencies(manifest_validator=QaManifestValidatorNotInstallReadyNoErrors())
    rc, out, err = _run(["catalog", "validate", "fixture.json", "--json"], deps)
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    # Hành vi hiện tại: fallback về E_INTERNAL (exit 9) khi không có error cụ
    # thể để trỏ tới — ghi nhận là RỦI RO THIẾT KẾ (không phải crash): người
    # dùng nhận "lỗi nội bộ" cho một tình huống hoàn toàn bình thường (manifest
    # chưa sẵn sàng), gây khó hiểu/log sai mức nghiêm trọng.
    assert parsed["error"]["code"] == ErrorCode.E_INTERNAL.value
    assert rc == ExitCode.INTERNAL


# ---------------------------------------------------------------------------
# DEFECT CLASS 4: exception từ compute_allowed_status (WP9) không được bọc.
# ---------------------------------------------------------------------------


def test_evidence_validate_uncaught_exception_from_compute_allowed_status() -> None:
    deps = CliDependencies(evidence_validator=QaEvidenceValidatorRaisesOnGate())
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(
            ["evidence", "validate", "fixture.json", "--json"], stdout=out, stderr=err, deps=deps
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            "DEFECT: compute_allowed_status() của WP9 raise exception không "
            f"được WP3 bắt lại ({type(exc).__name__}); chỉ .load() có "
            "try/except trong _handle_evidence_validate."
        )
    assert 0 <= rc <= 9
    json.loads(out.getvalue())


def test_evidence_validate_echoes_bad_gate_without_defensive_check() -> None:
    """Quan sát (KHÔNG khẳng định là lỗi của WP3): nếu WP9 có bug trả
    ``task_verified`` dù ``qa_reviewer is None``, WP3 hiện chỉ echo nguyên
    ``allowed_status`` ra envelope — không có lớp phòng vệ phụ nào ở CLI để
    chặn việc này trước khi hiển thị cho người dùng. Ghi evidence để chủ dự
    án quyết định có cần double-check ở WP3 hay chỉ tin tưởng WP9 (gate đã
    có unit test riêng ở T5)."""

    deps = CliDependencies(evidence_validator=QaEvidenceValidatorBadAllowedStatus())
    rc, out, err = _run(["evidence", "validate", "fixture.json", "--json"], deps)
    assert rc == ExitCode.OK
    parsed = json.loads(out)
    # Hiện trạng: CLI tin tưởng tuyệt đối gate của WP9, không re-check
    # qa_reviewer. Ghi lại hành vi thật, không coi là "pass"/"fail" tuyệt đối.
    assert parsed["data"]["allowed_status"] == "task_verified"


# ---------------------------------------------------------------------------
# Envelope cleanliness + exit-code table — negative trên mọi nhánh lỗi thật
# WP3 CÓ wiring đủ trong chính nó (doctor, parse error, unwired).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["doctor", "--json"],
        ["doctor"],
        ["khong-ton-tai-subcommand", "--json"],
        ["app", "inspect"],  # thiếu positional path
        ["catalog", "validate", "fixture.json", "--json"],  # unwired -> E_INTERNAL
        ["app", "install", "plan-xyz", "--json"],  # luôn blocked M1
    ],
)
def test_stdout_never_contains_more_than_one_line_when_json_or_is_empty_otherwise(
    argv: list[str],
) -> None:
    rc, out, err = _run(argv)
    assert isinstance(rc, int)
    assert 0 <= rc <= 9
    assert rc != 1, "exit code 1 CỐ Ý dành cho interpreter, không phải lỗi hợp đồng CLI"
    if "--json" in argv:
        # đúng 1 dòng JSON, parse được, không lẫn ký tự log nào khác
        lines = out.splitlines()
        assert len(lines) == 1
        json.loads(lines[0])
    else:
        # không --json: hoặc rỗng (lỗi parse) hoặc 1 dòng người-đọc; KHÔNG BAO
        # GIỜ là JSON (stdout của human-mode không phải máy đọc)
        if out:
            with pytest.raises(json.JSONDecodeError):
                json.loads(out)


def test_help_flag_does_not_emit_json_even_with_json_flag_present() -> None:
    """``-h`` luôn thắng mọi flag khác trong argparse — xác nhận ``--json``
    không "rò" help text thành field dữ liệu hay làm argparse tự ``sys.exit``
    vượt qua lớp kiểm soát của ``main()`` (``_NonExitingArgumentParser``)."""

    out, err = io.StringIO(), io.StringIO()
    rc = main(["doctor", "--json", "-h"], stdout=out, stderr=err)
    # -h luôn thoát qua ArgumentParsingError(status=0) theo argparse chuẩn —
    # không được crash bằng SystemExit thật (sẽ phá main() của caller).
    assert isinstance(rc, int)
    assert 0 <= rc <= 9


def test_doctor_stderr_always_empty_no_hidden_logging() -> None:
    """``doctor`` không có nhánh lỗi nào (luôn đọc host thật, không input
    người dùng) — xác nhận không có log ẩn nào ghi ra stderr ở happy path,
    đúng tinh thần CLI-001 "log kỹ thuật → stderr" nhưng ĐÂY không nên có
    log kỹ thuật nào cả vì không có gì để log."""

    rc, out, err = _run(["doctor", "--json"])
    assert rc == ExitCode.OK
    assert err == ""


def test_catalog_validate_loader_exception_detail_does_not_leak_raw_exception_message() -> None:
    """Negative cho redaction biên: khi ``.load()`` raise với message chứa
    dữ liệu "nhạy cảm" giả (đường dẫn tuyệt đối thật của máy), WP3 hiện chỉ
    đưa ``type(exc).__name__`` vào ``details.reason`` (KHÔNG đưa ``str(exc)``
    trực tiếp) — xác nhận hành vi này đúng như code, không bị đổi ngầm."""

    class _LeakyValidator(QaManifestValidatorOk):
        def load(self, path: str) -> object:  # type: ignore[override]
            raise ValueError(f"/home/thuc/.ssh/id_rsa khong doc duoc tai '{path}'")

    deps = CliDependencies(manifest_validator=_LeakyValidator())
    rc, out, err = _run(["catalog", "validate", "fixture.json", "--json"], deps)
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    details = parsed["error"]["details"]
    assert details["reason"] == "ValueError"
    # Chuỗi message gốc (có path nhạy cảm) KHÔNG xuất hiện trong envelope.
    full_payload = json.dumps(parsed, ensure_ascii=False)
    assert "id_rsa" not in full_payload
    assert "/home/thuc" not in full_payload
