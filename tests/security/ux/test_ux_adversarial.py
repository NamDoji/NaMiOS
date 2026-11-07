"""Adversarial QA — honest-status gates của ``namios_ux`` (Phụ lục 12).

Mục tiêu: cố PHÁ VỠ các bất biến trung thực của tầng UX bằng casing / whitespace
/ substring / Unicode / modifier đồng nghĩa / placeholder phủ định, rồi khoá
lại fail-closed. Mỗi vector dưới đây — SAU khi vá — PHẢI GIỮ (gate chặn) nên là
assertion thường. Hiện KHÔNG còn lỗ nào phải ``xfail`` (0 xfail).

Các lỗ hổng THẬT đã phát hiện + vá (xem từng test có nhãn ``REAL``):
  1. ``detect_conflicts`` không gộp modifier đồng nghĩa (``Super``/``Meta``/
     ``Win``, ``Control``/``Ctrl``, ``Escape``/``Esc``) → 2 action SYSTEM P0
     chiếm CÙNG phím vật lý vẫn lọt.  shortcuts.py `_normalize_combo`.
  2. ``shortcut_action_is_safe`` so marker bằng ``substring .lower()`` thô →
     lách bằng ``"send file"`` (space), fullwidth, zero-width, chữ ``ſ``.
  3. ``resolve_override`` cho đổi sang combo đồng nghĩa với phím đã bị chiếm
     (tạo xung đột ngầm) và chấp nhận combo rỗng.
  4. ``validate_wallpaper`` chỉ kiểm non-empty → ``rights_evidence``/``license``
     placeholder ("chưa có — cần cấp phép"/"pending"/"TODO") lọt; sha256 sai
     định dạng lọt; ``_ai_disclosed`` khớp ``"ai"`` trần → "Mai"/"Lào Cai" bị
     coi nhầm là ĐÃ khai báo AI (fail-open).
  6. ``missing_required_terms`` coi giá trị chỉ gồm ký tự vô hình (zero-width)
     là "đã dịch".

Mục 5 (tokens): công thức WCAG tự viết vốn đã fail-loud với hex sai — không có
lỗ; các test dưới XÁC NHẬN không trả ratio giả cao + biên 4.5/3.0 + cùng màu.
"""

from __future__ import annotations

import itertools

import pytest

from namios_ux._errors import UxErrorCode
from namios_ux.glossary import REQUIRED_GLOSSARY_TERMS, missing_required_terms
from namios_ux.shortcuts import (
    PLevel,
    ShortcutAction,
    ShortcutBinding,
    ShortcutScope,
    detect_conflicts,
    has_blocking_conflict,
    resolve_override,
    shortcut_action_is_safe,
)
from namios_ux.tokens import contrast_ratio, meets_wcag
from namios_ux.wallpaper import WallpaperEntry, validate_wallpaper, wallpaper_is_shippable

SYS = ShortcutScope.SYSTEM
WIN = ShortcutScope.WINDOW
APP = ShortcutScope.APP
ZWSP = "\u200b"  # zero-width space
NBSP = "\u00a0"  # non-breaking space


def _b(
    action_id: str,
    scope: ShortcutScope,
    combo: str,
    *,
    p_level: PLevel = PLevel.P0,
    overridable: bool = True,
) -> ShortcutBinding:
    return ShortcutBinding(
        action_id=action_id,
        scope=scope,
        combo=combo,
        p_level=p_level,
        overridable=overridable,
    )


# ===========================================================================
# 1) detect_conflicts / has_blocking_conflict — ép 2 SYSTEM P0 TRÙNG phím
#    mà KHÔNG bị phát hiện (modifier đồng nghĩa / order / case / unicode).
# ===========================================================================

#: (a, b) được coi là CÙNG một phím vật lý — phải sinh xung đột khi dùng chéo.
_SYNONYM_PAIRS = [
    ("Super+L", "Meta+L"),
    ("Super+L", "Win+L"),
    ("Super+L", "Windows+L"),
    ("Super+L", "Cmd+L"),
    ("Ctrl+Esc", "Control+Escape"),
    ("Ctrl+Esc", "Ctl+Esc"),
    ("Alt+F4", "Option+F4"),
    ("Ctrl+Enter", "Ctrl+Return"),
    ("Ctrl+Del", "Ctrl+Delete"),
    ("Ctrl+PgUp", "Ctrl+PageUp"),
]


@pytest.mark.parametrize(("left", "right"), _SYNONYM_PAIRS)
def test_system_p0_modifier_synonyms_are_blocking_conflict(left: str, right: str) -> None:
    # REAL: trước khi vá, "Super+L" vs "Meta+L" chuẩn hoá khác nhau → lọt.
    bindings = [_b("a", SYS, left), _b("b", SYS, right)]
    conflicts = detect_conflicts(bindings)
    assert len(conflicts) == 1, (left, right)
    assert conflicts[0].code == UxErrorCode.E_UX_SHORTCUT_P0_SYSTEM_CONFLICT.value
    assert has_blocking_conflict(bindings) is True


def test_combo_order_case_and_padding_still_merge() -> None:
    # Bất biến cũ (regression guard): thứ tự + hoa/thường + khoảng trắng dư.
    bindings = [_b("a", SYS, "Ctrl+Shift+Esc"), _b("b", SYS, "  shift + CTRL +  escape ")]
    assert has_blocking_conflict(bindings) is True


def test_combo_fullwidth_and_zero_width_still_merge() -> None:
    # Fullwidth "Ｓｕｐｅｒ" + zero-width chèn giữa "L" không được giúp lách.
    bindings = [_b("a", SYS, "Super+L"), _b("b", SYS, f"Ｓｕｐｅｒ+{ZWSP}L")]
    assert has_blocking_conflict(bindings) is True


def test_distinct_system_p0_keys_stay_clean() -> None:
    # Không được "gộp quá tay": Super+E và Super+I vẫn là 2 phím khác nhau.
    bindings = [_b("a", SYS, "Super+E"), _b("b", SYS, "Super+I")]
    assert detect_conflicts(bindings) == ()
    assert has_blocking_conflict(bindings) is False


def test_sweep_all_super_aliases_collide_pairwise() -> None:
    aliases = ["Super+K", "Meta+K", "Win+K", "Windows+K", "Cmd+K", "Command+K", "Logo+K"]
    for left, right in itertools.combinations(aliases, 2):
        bindings = [_b("a", SYS, left), _b("b", SYS, right)]
        assert has_blocking_conflict(bindings) is True, (left, right)


# ===========================================================================
# 2) shortcut_action_is_safe — bypass forbidden-marker bằng hoa/thường/
#    khoảng trắng/substring/unicode.
# ===========================================================================

#: Biến thể né marker mà bản ``substring .lower()`` thô ĐỂ LỌT (REAL).
_MARKER_BYPASS = [
    "send file to cloud",  # space thay '_' trong send_file
    "send-file-now",  # hyphen
    "please sign submit the doc",  # sign_submit
    "flash firmware image",  # flash_firmware
    "download binary blob",  # download_binary
    "disable protection layer",  # disable_protection
    "bypass protection now",  # bypass_protection
    "disable lock screen quietly",  # disable_lock_screen
    "upload file silently",  # upload_file
    "run ｓｈｅｌｌ command",  # fullwidth shell
    f"ro{ZWSP}ot_shell",  # zero-width giữa marker
    "ſhell escape",  # chữ ſ dài casefold -> s
    "RUN_ROOT_SHELL",  # uppercase
    "ExFiLtRaTe data",  # mixed case
]


@pytest.mark.parametrize("command", _MARKER_BYPASS)
def test_forbidden_marker_variants_are_blocked(command: str) -> None:
    assert shortcut_action_is_safe(ShortcutAction(action_id="x", command=command)) is False


def test_benign_commands_still_safe() -> None:
    # Không được chặn nhầm lệnh lành (fail-closed ≠ chặn tất cả).
    for cmd in ("open_file_manager", "toggle_night_light", "show_desktop", "capture_region"):
        assert shortcut_action_is_safe(ShortcutAction(action_id="x", command=cmd)) is True


def test_empty_and_whitespace_command_not_safe() -> None:
    assert shortcut_action_is_safe(ShortcutAction(action_id="x", command="")) is False
    assert shortcut_action_is_safe(ShortcutAction(action_id="x", command=f"  {ZWSP} ")) is False


def test_privileged_gate_survives_marker_normalization() -> None:
    # Lệnh lành nhưng privileged chưa confirm vẫn KHÔNG an toàn.
    act = ShortcutAction(action_id="lock", command="lock_session", privileged=True)
    assert shortcut_action_is_safe(act) is False
    assert (
        shortcut_action_is_safe(
            ShortcutAction(
                action_id="lock", command="lock_session", privileged=True, confirmed=True
            )
        )
        is True
    )


# ===========================================================================
# 3) resolve_override — ép đổi phím non-overridable / phím bị chiếm.
# ===========================================================================


def test_cannot_steal_non_overridable_system_key_via_synonym() -> None:
    # REAL: "Meta+E" đồng nghĩa "Super+E" của một phím SYSTEM khóa-đổi →
    # phải báo combo_taken, không được âm thầm tạo xung đột.
    bindings = [
        _b("launcher", SYS, "Super+Space", overridable=True),
        _b("file_manager", SYS, "Super+E", overridable=False),
    ]
    res = resolve_override(bindings, "launcher", "Meta+E")
    assert res.allowed is False
    assert res.error_code == UxErrorCode.E_UX_SHORTCUT_COMBO_TAKEN.value
    assert res.bindings == tuple(bindings)  # không nửa-đổi


def test_cannot_change_non_overridable_action_itself() -> None:
    bindings = [_b("lock_screen", SYS, "Super+L", overridable=False)]
    res = resolve_override(bindings, "lock_screen", "Super+K")
    assert res.allowed is False
    assert res.error_code == UxErrorCode.E_UX_SHORTCUT_NOT_OVERRIDABLE.value
    assert res.bindings[0].combo == "Super+L"


def test_override_onto_app_claimed_combo_synonym_is_rejected() -> None:
    # Hai phím APP; ép my_app sang combo đồng nghĩa phím app kia đang chiếm.
    bindings = [
        _b("my_app_find", APP, "Ctrl+A", overridable=True),
        _b("other_app_find", APP, "Ctrl+F", overridable=True),
    ]
    res = resolve_override(bindings, "my_app_find", "Control+F")
    assert res.allowed is False
    assert res.error_code == UxErrorCode.E_UX_SHORTCUT_CLAIMED_BY_APP.value


def test_override_to_synonym_of_existing_system_combo_is_taken() -> None:
    # REAL: trước khi vá, đổi launcher sang "Meta+E" (đồng nghĩa file_manager
    # "Super+E") được CHO PHÉP → sinh xung đột ngầm.
    bindings = [
        _b("launcher", SYS, "Super", overridable=True),
        _b("file_manager", SYS, "Super+E", overridable=True),
    ]
    # control: một combo thật, tự do → allowed
    assert resolve_override(bindings, "launcher", "Super+Q").allowed is True
    res = resolve_override(bindings, "launcher", "Meta+E")
    assert res.allowed is False
    assert res.error_code == UxErrorCode.E_UX_SHORTCUT_COMBO_TAKEN.value


@pytest.mark.parametrize("blank", ["", "   ", "+", " + + ", ZWSP, f"+{ZWSP}+"])
def test_blank_or_separator_only_combo_is_invalid(blank: str) -> None:
    # REAL (hardening): combo rỗng/chỉ dấu phân tách không được âm thầm gán
    # (né phát hiện trùng bằng combo "trống").
    bindings = [_b("settings", WIN, "Super+I", overridable=True)]
    res = resolve_override(bindings, "settings", blank)
    assert res.allowed is False
    assert res.error_code == UxErrorCode.E_UX_SHORTCUT_INVALID_COMBO.value
    assert res.bindings[0].combo == "Super+I"


def test_override_free_combo_still_allowed() -> None:
    bindings = [_b("settings", WIN, "Super+I", overridable=True)]
    res = resolve_override(bindings, "settings", "Super+K")
    assert res.allowed is True
    assert res.bindings[0].combo == "Super+K"


# ===========================================================================
# 4) wallpaper — ép mục KHÔNG có quyền thật thành shippable.
# ===========================================================================


def _wp(**over: object) -> WallpaperEntry:
    base: dict[str, object] = dict(
        id="w1",
        title="Vịnh Hạ Long",
        location="Quảng Ninh",
        author="Trần B",
        source="Chụp đặt hàng cho NaMiOS",
        license="CC-BY-4.0",
        rights_evidence="Hợp đồng chụp ảnh #2026-030, ký 10/2026",
        sha256="b" * 64,
        variants=("16:9",),
        credit="Ảnh: Trần B",
        ai_generated=False,
    )
    base.update(over)
    return WallpaperEntry(**base)  # type: ignore[arg-type]


def test_baseline_entry_is_shippable() -> None:
    assert wallpaper_is_shippable(_wp()) is True


#: ``rights_evidence`` KHÔNG rỗng nhưng nghĩa là CHƯA có quyền — phải chặn.
_RIGHTS_PLACEHOLDERS = [
    "chưa có — cần cấp phép",
    "chưa có",
    "cần cấp phép",
    "đang chờ cấp phép",
    "pending",
    "TODO",
    "placeholder",
    "unknown",
    "N/A",
    "n/a",
    "none",
    "-",
    "...",
    ZWSP,
    NBSP * 3,
    f"  {ZWSP}  ",
]


@pytest.mark.parametrize("value", _RIGHTS_PLACEHOLDERS)
def test_placeholder_rights_evidence_blocks_shippable(value: str) -> None:
    # REAL: validator cũ chỉ kiểm non-empty → các giá trị này lọt thành shippable.
    entry = _wp(rights_evidence=value)
    assert wallpaper_is_shippable(entry) is False
    codes = {e.code for e in validate_wallpaper(entry)}
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_RIGHTS_EVIDENCE.value in codes


@pytest.mark.parametrize("value", ["TODO", "pending", "placeholder", "chưa có", "none", "   ", ""])
def test_placeholder_license_blocks_shippable(value: str) -> None:
    entry = _wp(license=value)
    assert wallpaper_is_shippable(entry) is False
    codes = {e.code for e in validate_wallpaper(entry)}
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_LICENSE.value in codes


def test_real_licenses_still_ship() -> None:
    for lic in ("CC-BY-4.0", "CC0-1.0", "MIT", "Mua bản quyền trọn gói #2026-07"):
        assert wallpaper_is_shippable(_wp(license=lic)) is True, lic


#: sha256 sai định dạng (không phải đúng 64 hex) — phải chặn.
_BAD_SHA = [
    "deadbeef",  # quá ngắn
    "g" * 64,  # không phải hex
    "a" * 63,  # thiếu 1
    "a" * 65,  # thừa 1
    "a" * 32 + " " + "a" * 31,  # khoảng trắng bên trong
    "0xabc" + "a" * 59,  # tiền tố 0x
    "not-a-real-sha256-hash",
]


@pytest.mark.parametrize("value", _BAD_SHA)
def test_malformed_sha256_blocks_shippable(value: str) -> None:
    entry = _wp(sha256=value)
    assert wallpaper_is_shippable(entry) is False
    codes = {e.code for e in validate_wallpaper(entry)}
    assert UxErrorCode.E_UX_WALLPAPER_INVALID_SHA256.value in codes


def test_valid_sha256_any_case_ships() -> None:
    assert wallpaper_is_shippable(_wp(sha256="A" * 64)) is True  # uppercase hex
    assert wallpaper_is_shippable(_wp(sha256="DeadBeef" * 8)) is True  # 64 hex mixed case
    assert wallpaper_is_shippable(_wp(sha256="  " + "a" * 64 + "  ")) is True  # padded ok


def test_empty_sha256_is_missing_not_invalid() -> None:
    codes = {e.code for e in validate_wallpaper(_wp(sha256=""))}
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_SHA256.value in codes
    assert UxErrorCode.E_UX_WALLPAPER_INVALID_SHA256.value not in codes


#: Credit/nguồn chứa chuỗi con "ai" NHƯNG không thật sự khai báo AI — REAL
#: fail-open của bản ``"ai" in haystack`` trần.
_FAKE_AI_DISCLOSURE = [
    ("Ảnh của Mai", ""),
    ("", "Chụp tại Lào Cai"),
    ("Hai bức ảnh ghép", ""),
    ("Tác giả: Trai Nguyen", ""),
]


@pytest.mark.parametrize(("credit", "source"), _FAKE_AI_DISCLOSURE)
def test_ai_generated_with_fake_disclosure_substring_is_blocked(credit: str, source: str) -> None:
    entry = _wp(ai_generated=True, credit=credit, source=source)
    assert wallpaper_is_shippable(entry) is False
    codes = {e.code for e in validate_wallpaper(entry)}
    assert UxErrorCode.E_UX_WALLPAPER_AI_UNDISCLOSED.value in codes


def test_ai_generated_with_no_disclosure_is_blocked() -> None:
    entry = _wp(ai_generated=True, credit="Ảnh: Trần B", source="Chụp đặt hàng")
    assert wallpaper_is_shippable(entry) is False


@pytest.mark.parametrize(
    "credit",
    [
        "Tạo bởi AI (Midjourney)",
        "Ảnh AI, hậu kỳ NaMiOS",
        "Generative image",
        "Stable Diffusion render",
        "Artificial intelligence assisted",
    ],
)
def test_genuine_ai_disclosure_passes(credit: str) -> None:
    assert wallpaper_is_shippable(_wp(ai_generated=True, credit=credit)) is True


def test_ai_disclosure_in_source_field_passes() -> None:
    assert (
        wallpaper_is_shippable(
            _wp(ai_generated=True, credit="NaMiOS", source="generative, không phải ảnh tư liệu")
        )
        is True
    )


# ===========================================================================
# 5) tokens — hex sai KHÔNG trả ratio giả cao; biên 4.5/3.0; cùng màu = 1.0.
# ===========================================================================


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "#",
        "#12",
        "#1234",
        "#12345",
        "#1234567",
        "not-a-color",
        "#gggggg",
        "#12 34 56",
        "rgb(0,0,0)",
        "0xffffff",
        "######",
        "#xyz",
    ],
)
def test_invalid_hex_raises_not_fake_ratio(bad: str) -> None:
    with pytest.raises(ValueError):
        contrast_ratio(bad, "#ffffff")


def test_contrast_ratio_bounds_and_identity() -> None:
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, rel=1e-6)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, rel=1e-9)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0, rel=1e-9)
    # Thứ tự tham số không đổi kết quả; luôn trong [1, 21].
    r = contrast_ratio("#123456", "#abcdef")
    assert r == pytest.approx(contrast_ratio("#abcdef", "#123456"), rel=1e-12)
    assert 1.0 <= r <= 21.0


def test_case_and_hash_and_shortform_consistent() -> None:
    assert contrast_ratio("ABCDEF", "#000000") == pytest.approx(
        contrast_ratio("#abcdef", "000000"), rel=1e-12
    )
    assert contrast_ratio("#fff", "#000") == pytest.approx(
        contrast_ratio("#ffffff", "#000000"), rel=1e-12
    )


def test_wcag_thresholds_exact_boundaries() -> None:
    assert meets_wcag(4.5) is True
    assert meets_wcag(4.4999999) is False
    assert meets_wcag(3.0, large=True) is True
    assert meets_wcag(2.9999999, large=True) is False
    # cùng màu → 1.0 → không đạt ở cả hai ngưỡng.
    assert meets_wcag(1.0) is False
    assert meets_wcag(1.0, large=True) is False


# ===========================================================================
# 6) glossary — ép term bắt buộc bị coi "có" do khác hoa/thường/khoảng trắng.
# ===========================================================================


def _full() -> dict[str, str]:
    return {t: "x" + t for t in REQUIRED_GLOSSARY_TERMS}


def test_zero_width_only_value_counts_missing() -> None:
    # REAL: "​".strip() != "" nên bản cũ coi là đã dịch.
    g = _full()
    g["may_in"] = ZWSP
    assert missing_required_terms(g) == ("may_in",)


def test_various_invisible_only_values_count_missing() -> None:
    for blank in (NBSP, ZWSP * 4, "\u200c\u200d", "\ufeff", "\u00ad", f" {ZWSP}\t"):
        g = _full()
        g["bo_go"] = blank
        assert "bo_go" in missing_required_terms(g), repr(blank)


def test_differently_cased_key_does_not_satisfy_requirement() -> None:
    # Fail-closed: key sai hoa/thường/khoảng trắng KHÔNG khớp lỏng → vẫn thiếu.
    g = _full()
    del g["may_in"]
    g["May_In"] = "Máy in"
    g[" may_in "] = "Máy in"
    g["MAY_IN"] = "Máy in"
    assert "may_in" in missing_required_terms(g)


def test_plain_whitespace_value_counts_missing() -> None:
    g = _full()
    g["cap_nhat"] = "   \t  "
    assert missing_required_terms(g) == ("cap_nhat",)


def test_real_terms_are_not_flagged() -> None:
    g = {
        "tep": "Tệp",
        "thu_muc": "Thư mục",
        "ung_dung": "Ứng dụng",
        "may_in": "Máy in",
        "cap_nhat": "Cập nhật",
        "khoi_phuc": "Khôi phục",
        "bo_go": "Bộ gõ",
    }
    assert missing_required_terms(g) == ()
