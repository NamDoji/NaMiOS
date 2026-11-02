"""Integration — ``namios catalog validate`` end-to-end với implementation
THẬT (``ManifestValidatorImpl`` của WP2, qua ``default_dependencies()`` khi
``main()`` không được truyền ``deps`` — path thật, KHÔNG fake). Một manifest
hợp lệ (fixture local) + một manifest "injection" (recipe có khóa ``shell``
cấm tuyệt đối — xem ``namios_manifest._recipe_build``) PHẢI bị chặn, không
crash, exit code đúng bảng CLI-003.
"""

from __future__ import annotations

import io
import json

import pytest

from namios_cli.main import main
from namios_core.exitcodes import ExitCode

from ._paths import manifest_fixture_path


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    rc = main(argv, stdout=out, stderr=err)  # deps=None ⇒ wiring thật
    return rc, out.getvalue(), err.getvalue()


def test_catalog_validate_real_manifest_install_ready_ok() -> None:
    path = manifest_fixture_path("valid-demo-app.json")
    rc, out, err = _run(["catalog", "validate", path, "--json"])
    assert rc == ExitCode.OK
    assert err == ""
    parsed = json.loads(out)
    assert parsed["status"] == "ok"
    assert parsed["data"] == {"app_id": "demo-app", "install_ready": True}


def test_catalog_validate_real_manifest_injection_recipe_is_blocked_not_crashed() -> None:
    path = manifest_fixture_path("injection-shell-recipe.json")
    out, err = io.StringIO(), io.StringIO()
    try:
        rc = main(["catalog", "validate", path, "--json"], stdout=out, stderr=err)
    except Exception as exc:  # noqa: BLE001 — chính là điều đang kiểm tra
        pytest.fail(
            "DEFECT: manifest có recipe injection (khóa 'shell' cấm tuyệt "
            f"đối) làm main() crash bằng {type(exc).__name__}({exc!r}) thay "
            "vì trả envelope lỗi end-to-end."
        )
    assert 0 <= rc <= 9
    assert rc != 1
    assert rc == ExitCode.INPUT
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "error"
    assert parsed["data"] is None
    # 'Không tải được manifest' — load() của ManifestValidatorImpl raise
    # ManifestLoadError khi build recipe bị chặn (E_SEMANTIC_RECIPE); CLI
    # (``_handle_catalog_validate``) chuẩn hoá MỌI exception từ .load() về
    # E_INPUT_SCHEMA — xem src/namios_cli/main.py.
    assert parsed["error"]["code"] == "E_INPUT_SCHEMA"
    # Không lộ nội dung recipe độc hại ra envelope.
    full_payload = json.dumps(parsed, ensure_ascii=False)
    assert "rm -rf" not in full_payload
