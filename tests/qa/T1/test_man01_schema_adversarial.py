"""T1 (tester độc lập) — MAN-01: tấn công tầng 1 (JSON Schema) của WP2.

Mục tiêu: chứng minh "schema hợp lệ" KHÔNG đồng nghĩa "an toàn"/"đúng kiểu
mọi nơi" và rằng unknown-key/type-confusion bị chặn đúng ``ErrorCode`` ở
đúng vị trí — KHÔNG tạo process, KHÔNG crash ra exception lạ (phải trả
``SchemaResult`` có cấu trúc, không ``raise`` không kiểm soát).

Viết ĐỘC LẬP với ``tests/unit/manifest/test_schema_tier.py`` của dev — các
case dưới đây KHÔNG trùng case dev đã viết (type confusion sâu, injection
qua tên khóa dict giả làm key, mảng lồng object giả, unicode/NFC bypass,
trường ``null`` ở nơi không cho phép null, số thay cho object...).
"""

from __future__ import annotations

from namios_core.errors import ErrorCode
from namios_manifest import ManifestValidatorImpl

from ._qa_fixtures import baseline_manifest, mutate


def _validator() -> ManifestValidatorImpl:
    return ManifestValidatorImpl()


def test_type_confusion_object_where_string_expected_does_not_crash() -> None:
    """``publisher`` là string theo schema — thử nhồi một object (dict) vào
    đó (kiểu kỹ thuật "type confusion" hay dùng để dò injection ở downstream
    string-formatting). Phải bị chặn ở tầng 1, KHÔNG raise AttributeError/
    TypeError không kiểm soát."""

    raw = mutate(baseline_manifest())
    raw["publisher"] = {"__proto__": "x", "toString": "rm -rf /"}

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_type_confusion_array_where_object_expected() -> None:
    """``application`` phải là object — thử truyền một array. Diễn giải
    schema phải tự phát hiện sai type ở tầng object, không âm thầm bỏ qua
    (ví dụ do code chỉ kiểm tra object khi ``isinstance(instance, dict)`` mà
    quên nhánh ``expected_type == "object"`` với instance không phải dict)."""

    raw = mutate(baseline_manifest())
    raw["application"] = ["version", "1.0.0"]

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_installer_sha256_as_integer_rejected_not_coerced() -> None:
    """Thử gửi số nguyên (không phải chuỗi hex) cho ``installer_sha256`` —
    JS/JSON client lỗi có thể gửi số nếu hash toàn chữ số. Phải FAIL tầng 1,
    không được âm thầm ``str()``-hoá rồi cho qua."""

    raw = mutate(baseline_manifest())
    raw["application"]["installer_sha256"] = 1234567890

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_recipe_as_object_instead_of_array_rejected() -> None:
    """``recipe`` theo schema là array — ép thành object (dict khóa số) để
    dò xem engine có coi nhầm là "iterable hợp lệ" rồi lặp qua ``.items()``
    gây hành vi không xác định."""

    raw = mutate(baseline_manifest())
    raw["recipe"] = {"0": {"action": "create_prefix", "params": {"prefix_architecture": "win64"}}}

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_boolean_true_where_string_expected_is_rejected() -> None:
    """``name`` là string — Python ``bool`` là subclass của ``int`` nhưng
    KHÔNG của ``str``; vẫn kiểm tra tường minh để chắc engine không có lỗ
    hổng coerce ngầm."""

    raw = mutate(baseline_manifest())
    raw["name"] = True

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_boolean_one_where_integer_like_field_not_coerced_from_bool() -> None:
    """``automatic_download`` phải là boolean thật — gửi số nguyên 1 (dễ bị
    coerce nhầm vì nhiều ngôn ngữ coi 1 == True) phải bị từ chối (type
    integer != boolean theo JSON Schema nghiêm ngặt)."""

    raw = mutate(baseline_manifest())
    raw["source"]["automatic_download"] = 1

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_unknown_key_with_dunder_name_is_rejected() -> None:
    """Khóa lạ dạng ``__proto__``/``constructor`` (kỹ thuật prototype-
    pollution từ thế giới JS) đưa vào object Python dict thường — phải vẫn
    bị bắt như unknown key bình thường, không có xử lý đặc biệt nào bỏ qua
    nó."""

    raw = mutate(baseline_manifest())
    raw["application"]["__proto__"] = {"polluted": True}

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_UNKNOWN_KEY.value for e in result.errors)
    assert any("__proto__" in e.path for e in result.errors)


def test_unknown_key_using_unicode_nfc_nfd_confusable_name() -> None:
    """Khóa lạ dùng ký tự Unicode tổ hợp (combining) trông giống khóa hợp lệ
    (ví dụ ``buildd`` với một ký tự combining chèn vào giữa) — không được
    coi nhầm là khóa ``build`` hợp lệ đã biết."""

    raw = mutate(baseline_manifest())
    # "build" nhìn giống "build" nhưng có thêm hậu tố lạ phía sau.
    raw["application"]["build​"] = "sneaky"

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_UNKNOWN_KEY.value for e in result.errors)


def test_deeply_nested_filesystem_permission_unknown_key_is_caught() -> None:
    """Unknown key chèn sâu bên trong một phần tử mảng
    ``permissions.filesystem[]`` (khác vị trí dev đã test ở
    ``application``) — xác nhận recursion unknown-key hoạt động đều ở mọi
    cấp lồng, không chỉ cấp 1-2."""

    raw = mutate(baseline_manifest())
    raw["permissions"]["filesystem"][0]["sneaky_extra"] = "payload"

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_UNKNOWN_KEY.value for e in result.errors)
    assert any("sneaky_extra" in e.path for e in result.errors)


def test_duplicate_dependency_profile_ids_rejected_unique_items() -> None:
    """``dependency_profile_ids`` khai báo ``uniqueItems`` — thử trùng lặp
    cố ý (kỹ thuật "duplicate key" dùng để qua mặt bộ đếm/approve logic ở
    tầng khác) phải bị chặn ngay tầng schema."""

    raw = mutate(baseline_manifest())
    raw["runtime"]["dependency_profile_ids"] = ["dotnet-48-x64", "dotnet-48-x64"]

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_null_at_strictly_required_non_nullable_field_rejected() -> None:
    """``mode`` không có ``anyOf null`` trong contract — gửi ``null`` thẳng
    phải FAIL (không được coi null == "chưa có, cho qua" ở các trường
    không khai báo nullable, khác hẳn ``application.build`` là cố ý
    nullable)."""

    raw = mutate(baseline_manifest())
    raw["mode"] = None

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)


def test_extremely_long_string_field_rejected_by_max_length() -> None:
    """Chuỗi khổng lồ (vượt ``maxLength`` khai báo cho ``version``) — cũng
    là một góc DoS nhẹ (bộ nhớ) khi xử lý chuỗi; phải bị chặn bởi
    ``maxLength`` của contract, không được "cho qua vì dù sao cũng validate
    nội dung sau"."""

    raw = mutate(baseline_manifest())
    raw["application"]["version"] = "9" * 10_000

    result = _validator().validate_schema(raw)

    assert result.ok is False
    assert any(e.code == ErrorCode.E_INPUT_SCHEMA.value for e in result.errors)
