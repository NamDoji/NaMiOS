"""UX12-025..032/046 — hình nền: fail-closed quyền/nguồn gốc, không đoán quyền."""

from __future__ import annotations

from namios_ux._errors import UxErrorCode
from namios_ux.wallpaper import WallpaperEntry, validate_wallpaper, wallpaper_is_shippable


def _full_entry(**overrides: object) -> WallpaperEntry:
    base: dict[str, object] = dict(
        id="sapa-01",
        title="Ruộng bậc thang Sa Pa",
        location="Sa Pa, Lào Cai",
        author="Nguyễn Văn A",
        source="Chụp đặt hàng cho NaMiOS, 10/2026",
        license="CC-BY-4.0",
        rights_evidence="Hợp đồng chụp ảnh #2026-014, ký 01/10/2026",
        sha256="a" * 64,
        variants=("16:9", "16:10"),
        credit="Ảnh: Nguyễn Văn A / NaMiOS",
        ai_generated=False,
    )
    base.update(overrides)
    return WallpaperEntry(**base)  # type: ignore[arg-type]


def test_fully_valid_entry_is_shippable_and_clean() -> None:
    entry = _full_entry()
    assert validate_wallpaper(entry) == []
    assert wallpaper_is_shippable(entry) is True


def test_missing_license_blocks_shippable() -> None:
    entry = _full_entry(license="")
    issues = validate_wallpaper(entry)
    codes = [e.code for e in issues]
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_LICENSE.value in codes
    assert wallpaper_is_shippable(entry) is False


def test_missing_rights_evidence_blocks_shippable() -> None:
    entry = _full_entry(rights_evidence="   ")
    assert wallpaper_is_shippable(entry) is False


def test_missing_sha256_blocks_shippable() -> None:
    entry = _full_entry(sha256="")
    assert wallpaper_is_shippable(entry) is False


def test_ai_generated_without_disclosure_blocks_shippable() -> None:
    entry = _full_entry(ai_generated=True, credit="Ảnh: Nguyễn Văn A / NaMiOS")
    issues = validate_wallpaper(entry)
    codes = [e.code for e in issues]
    assert UxErrorCode.E_UX_WALLPAPER_AI_UNDISCLOSED.value in codes
    assert wallpaper_is_shippable(entry) is False


def test_ai_generated_with_disclosure_passes_hard_gate() -> None:
    entry = _full_entry(ai_generated=True, credit="Ảnh tạo bởi AI (Midjourney), hậu kỳ NaMiOS")
    assert wallpaper_is_shippable(entry) is True


def test_ai_disclosure_can_be_in_source_field() -> None:
    entry = _full_entry(
        ai_generated=True,
        credit="NaMiOS",
        source="Generative image, không phải ảnh tư liệu",
    )
    assert wallpaper_is_shippable(entry) is True


def test_missing_soft_metadata_reported_but_does_not_block_hard_gate() -> None:
    # title/location/author/variants thiếu là lỗi "mềm" (chất lượng biên tập),
    # KHÔNG thuộc 4 điều kiện cứng về quyền/nguồn gốc.
    entry = _full_entry(title="", location="", author="", variants=())
    issues = validate_wallpaper(entry)
    codes = {e.code for e in issues}
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_TITLE.value in codes
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_LOCATION.value in codes
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_AUTHOR.value in codes
    assert UxErrorCode.E_UX_WALLPAPER_MISSING_VARIANTS.value in codes
    assert wallpaper_is_shippable(entry) is True


def test_all_fields_missing_reports_everything_and_blocks() -> None:
    entry = WallpaperEntry(id="blank")
    issues = validate_wallpaper(entry)
    # 7 trường rỗng (title/location/author/license/rights_evidence/sha256/variants);
    # ai_undisclosed KHÔNG áp dụng vì ai_generated=False mặc định.
    assert len(issues) == 7
    assert wallpaper_is_shippable(entry) is False
