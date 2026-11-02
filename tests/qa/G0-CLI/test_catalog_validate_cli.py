"""QA tester integration — ``namios catalog validate`` end-to-end THẬT
(``deps=None`` ⇒ wiring thật: ``ManifestValidatorImpl`` của WP2).

Khẳng định bắt buộc: manifest hợp lệ → ok; manifest có recipe
url-script/template nội suy → bị chặn với exit code đúng + envelope error,
KHÔNG crash, KHÔNG lộ nội dung độc hại ra envelope.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

# Thư mục con "G0-CLI" chứa dấu gạch ngang → KHÔNG thể là package Python hợp
# lệ (không import tương đối được). Dùng path tuyệt đối trực tiếp, không
# chia sẻ module helper giữa các file test trong thư mục này.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_INTEGRATION_MANIFEST_DIR = _REPO_ROOT / "tests" / "integration" / "fixtures" / "manifest"
_QA_MANIFEST_DIR = Path(__file__).resolve().parent / "fixtures" / "manifest"


def integration_manifest_fixture_path(name: str) -> str:
    return str(_INTEGRATION_MANIFEST_DIR / name)


def qa_manifest_fixture_path(name: str) -> str:
    return str(_QA_MANIFEST_DIR / name)


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_catalog_validate_valid_manifest_is_ok() -> None:
    path = integration_manifest_fixture_path("valid-demo-app.json")
    rc, out, err = _run(["catalog", "validate", path, "--json"])
    assert rc == ExitCode.OK
    assert rc != 1
    assert err == ""
    lines = out.splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "ok"
    assert parsed["data"] == {"app_id": "demo-app", "install_ready": True}


def test_catalog_validate_url_script_recipe_is_blocked_not_crashed() -> None:
    path = qa_manifest_fixture_path("url-script-recipe.json")
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["catalog", "validate", path, "--json"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001 — chính là điều đang kiểm tra
        pytest.fail(
            "DEFECT: manifest recipe url-script (argv ghép pipe shell) làm "
            f"main() crash bằng {type(exc).__name__}({exc!r}) thay vì trả "
            "envelope lỗi end-to-end."
        )
    assert 0 <= rc <= 9
    assert rc != 1
    assert rc == ExitCode.INPUT
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    full_payload = json.dumps(parsed, ensure_ascii=False)
    assert "curl" not in full_payload
    assert "evil.example" not in full_payload


def test_catalog_validate_template_interpolation_recipe_is_blocked_not_crashed() -> None:
    path = qa_manifest_fixture_path("template-interpolation-recipe.json")
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["catalog", "validate", path, "--json"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            "DEFECT: manifest recipe chứa template nội suy '{{ secrets... }}' "
            f"làm main() crash bằng {type(exc).__name__}({exc!r}) thay vì trả "
            "envelope lỗi end-to-end."
        )
    assert 0 <= rc <= 9
    assert rc != 1
    assert rc == ExitCode.INPUT
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    full_payload = json.dumps(parsed, ensure_ascii=False)
    assert "secrets.admin_password" not in full_payload


def test_catalog_validate_shell_key_injection_recipe_is_blocked_not_crashed() -> None:
    """Đối chiếu với fixture 'shell' key tuyệt đối cấm (dùng lại chung với
    ``tests/integration``) để bảo đảm 3 loại chặn (shell/url-script/template)
    đều đồng nhất hành vi end-to-end, không chỉ một loại."""

    path = integration_manifest_fixture_path("injection-shell-recipe.json")
    rc, out, _err = _run(["catalog", "validate", path, "--json"])
    assert rc == ExitCode.INPUT
    parsed = json.loads(out)
    assert parsed["status"] == "error"
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    assert "rm -rf" not in json.dumps(parsed, ensure_ascii=False)
