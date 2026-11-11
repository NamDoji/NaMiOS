"""``Translator.t`` / hàm tiện ích ``t`` dùng instance mặc định — tra catalog,
format tham số an toàn, fallback VI->EN->chính key."""

from __future__ import annotations

import pytest

from namios_i18n import ENV_VAR, Lang, Translator, add_catalog, get_default_translator, has_key, t


def _clear_locale_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Xoá mọi biến ảnh hưởng resolve_lang để test đúng đường rơi cuối (VI)."""
    for var in (ENV_VAR, "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)


def test_vi_is_default_language(monkeypatch: pytest.MonkeyPatch) -> None:
    # Không NAMIOS_LANG + không locale máy → mặc định tiếng Việt (VN-001).
    _clear_locale_env(monkeypatch)
    assert t("cli.main.error.manifest_load_failed") == "Không tải được manifest."


def test_explicit_en_overrides_default() -> None:
    assert t("cli.main.error.manifest_load_failed", lang=Lang.EN) == "Could not load the manifest."


def test_lang_accepts_plain_string() -> None:
    assert t("cli.main.error.manifest_load_failed", lang="en") == "Could not load the manifest."


def test_env_var_selects_en(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "en")
    assert t("cli.main.error.manifest_load_failed") == "Could not load the manifest."


def test_system_locale_en_selects_en(monkeypatch: pytest.MonkeyPatch) -> None:
    # "Tiếng Anh theo ngôn ngữ của máy": không NAMIOS_LANG + máy en_US → tiếng Anh.
    _clear_locale_env(monkeypatch)
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    assert t("cli.main.error.manifest_load_failed") == "Could not load the manifest."


def test_system_locale_vi_selects_vi(monkeypatch: pytest.MonkeyPatch) -> None:
    # ISO NaMiOS mặc định LANG=vi_VN.UTF-8 → tiếng Việt.
    _clear_locale_env(monkeypatch)
    monkeypatch.setenv("LANG", "vi_VN.UTF-8")
    assert t("cli.main.error.manifest_load_failed") == "Không tải được manifest."


def test_namios_lang_overrides_system_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    # NAMIOS_LANG thắng locale máy (ưu tiên 2 > 3).
    _clear_locale_env(monkeypatch)
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    monkeypatch.setenv(ENV_VAR, "vi")
    assert t("cli.main.error.manifest_load_failed") == "Không tải được manifest."


def test_c_locale_falls_back_to_vi(monkeypatch: pytest.MonkeyPatch) -> None:
    # locale "C"/"POSIX" không phải vi/en → rơi về mặc định VI, không lỗi.
    _clear_locale_env(monkeypatch)
    monkeypatch.setenv("LANG", "C")
    assert t("cli.main.error.manifest_load_failed") == "Không tải được manifest."


def test_existing_vn_strings_preserved_verbatim() -> None:
    """RÀNG BUỘC CỰC KỲ QUAN TRỌNG: catalog vi PHẢI giữ nguyên y hệt chuỗi
    hiện có trong code (800 test cũ không được vỡ khi wire sau này)."""

    assert t("welcome.ui.welcome.title") == "Chào mừng đến với NaMi"
    assert (
        t("eco.status.reason.not_inventoried")
        == "Chưa nấc nào được chạy (toàn bộ not_run) — chưa khảo sát."
    )
    assert t("cli.main.error.unknown_command") == "Lệnh không xác định."


def test_param_substitution() -> None:
    assert (
        t("cli.main.error.service_not_found", id="thue.htkk")
        == "Không tìm thấy dịch vụ với id 'thue.htkk' trong danh bạ."
    )
    assert (
        t("cli.main.error.service_not_found", lang=Lang.EN, id="thue.htkk")
        == "No service found with id 'thue.htkk' in the directory."
    )


def test_missing_param_does_not_raise_and_degrades_to_empty() -> None:
    # Thiếu tham số 'id' -> không KeyError, chèn chuỗi rỗng.
    result = t("cli.main.error.service_not_found")
    assert "KeyError" not in result
    assert result == "Không tìm thấy dịch vụ với id '' trong danh bạ."


def test_extra_param_is_ignored() -> None:
    result = t(
        "cli.main.error.unknown_command",
        unused_extra="bất kỳ giá trị gì",
        another_unused=123,
    )
    assert result == "Lệnh không xác định."


def test_literal_double_braces_render_as_single_braces() -> None:
    expected_vi = "'xyz' không thuộc {telex, vni}"
    assert t("welcome.firstrun.error.ime_method_invalid", value="xyz") == expected_vi
    assert (
        t("welcome.firstrun.error.ime_method_invalid", lang=Lang.EN, value="xyz")
        == "'xyz' is not one of {telex, vni}"
    )


def test_malformed_template_degrades_to_raw_template_without_crash() -> None:
    translator = Translator()
    translator.add_catalog(Lang.VI, {"test.malformed": "Giá trị lạ: {0} {unterminated"})
    # Không ValueError/IndexError lọt ra ngoài — trả nguyên văn template.
    result = translator.t("test.malformed")
    assert result == "Giá trị lạ: {0} {unterminated"


def test_unknown_key_returns_key_itself() -> None:
    assert t("khong.ton.tai.key.nay") == "khong.ton.tai.key.nay"


def test_fallback_vi_then_en_when_key_only_in_one_catalog() -> None:
    translator = Translator()
    translator.add_catalog(Lang.VI, {"test.only_vi": "Chỉ có ở VI"})
    translator.add_catalog(Lang.EN, {"test.only_en": "Only in EN"})

    # Yêu cầu EN nhưng key chỉ có ở VI -> fallback về VI (không trả key thô).
    assert translator.t("test.only_vi", lang=Lang.EN) == "Chỉ có ở VI"
    # Yêu cầu VI nhưng key chỉ có ở EN -> fallback về EN.
    assert translator.t("test.only_en", lang=Lang.VI) == "Only in EN"


def test_add_catalog_contributes_new_key_to_default_instance() -> None:
    add_catalog(Lang.VI, {"test.module_khac.chao": "Xin chào {ten}"})
    add_catalog(Lang.EN, {"test.module_khac.chao": "Hello {ten}"})
    assert t("test.module_khac.chao", ten="Cường") == "Xin chào Cường"
    assert t("test.module_khac.chao", lang=Lang.EN, ten="Cường") == "Hello Cường"


def test_add_catalog_can_override_existing_key_on_a_fresh_instance() -> None:
    translator = Translator()
    translator.add_catalog(Lang.VI, {"cli.main.error.unknown_command": "Đã đổi"})
    assert translator.t("cli.main.error.unknown_command") == "Đã đổi"
    # Instance mặc định toàn cục KHÔNG bị ảnh hưởng bởi instance riêng này.
    assert t("cli.main.error.unknown_command") == "Lệnh không xác định."


def test_has_key_and_default_translator_accessors() -> None:
    assert has_key("cli.main.error.unknown_command", Lang.VI)
    assert has_key("cli.main.error.unknown_command", Lang.EN)
    assert not has_key("khong.ton.tai.key.nay")
    assert get_default_translator() is get_default_translator()


def test_translation_key_is_positional_only_so_param_named_key_still_works() -> None:
    """Regression (wire i18n 03/11/2026, ``namios_eco``/``namios_cli`` call
    sites): một số catalog có placeholder TÊN LÀ ``{key}`` (vd
    ``eco.catalog_schema.error.unknown_property``,
    ``eco.validator.error.executable_key_forbidden``). ``t()``'s own first
    (lookup) parameter is also named ``key`` — nếu nó KHÔNG positional-only,
    gọi ``t("some.catalog.key", lang=Lang.VI, key=value)`` sẽ ``TypeError:
    got multiple values for argument 'key'`` thay vì rơi vào ``**params``."""

    assert (
        t("eco.catalog_schema.error.unknown_property", key="loi_di")
        == "Thuộc tính không xác định 'loi_di' — danh bạ ECO-006 KHÔNG có "
        "trường thực thi/lệnh nào; chỉ các trường metadata đã khai báo."
    )
    assert (
        t("eco.validator.error.executable_key_forbidden", lang=Lang.EN, key="shell")
        == "Field 'shell' is absolutely forbidden in the ECO-006 catalog — the "
        "directory must NEVER control commands/execution."
    )
