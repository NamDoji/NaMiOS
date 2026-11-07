"""UX12-037 — glossary tiếng Việt thống nhất, tái dùng namios_i18n."""

from __future__ import annotations

from namios_i18n import Lang
from namios_ux.glossary import (
    REQUIRED_GLOSSARY_TERMS,
    load_glossary,
    missing_required_terms,
)


def test_default_catalog_has_no_missing_required_terms() -> None:
    glossary = load_glossary()
    assert missing_required_terms(glossary) == ()


def test_default_catalog_uses_canonical_vietnamese_terms() -> None:
    glossary = load_glossary()
    assert glossary["tep"] == "Tệp"
    assert glossary["thu_muc"] == "Thư mục"
    assert glossary["ung_dung"] == "Ứng dụng"
    assert glossary["may_in"] == "Máy in"
    assert glossary["cap_nhat"] == "Cập nhật"
    assert glossary["khoi_phuc"] == "Khôi phục"
    assert glossary["bo_go"] == "Bộ gõ"


def test_english_catalog_also_resolves() -> None:
    glossary_en = load_glossary(lang=Lang.EN)
    assert glossary_en["tep"] == "File"
    assert glossary_en["may_in"] == "Printer"


def test_missing_required_terms_is_self_contained_fixture() -> None:
    # Fixture tự dựng, KHÔNG phụ thuộc catalog thật/file design/*.json ngoài repo.
    fake_glossary = {
        "tep": "Tệp",
        "thu_muc": "Thư mục",
        "ung_dung": "Ứng dụng",
        # thiếu "may_in", "cap_nhat", "khoi_phuc", "bo_go"
    }
    missing = missing_required_terms(fake_glossary)
    assert set(missing) == {"may_in", "cap_nhat", "khoi_phuc", "bo_go"}


def test_blank_value_counts_as_missing() -> None:
    fake_glossary = dict.fromkeys(REQUIRED_GLOSSARY_TERMS, "x")
    fake_glossary["may_in"] = "   "
    missing = missing_required_terms(fake_glossary)
    assert missing == ("may_in",)


def test_empty_glossary_reports_all_required_terms_missing() -> None:
    assert set(missing_required_terms({})) == set(REQUIRED_GLOSSARY_TERMS)


def test_unregistered_term_id_is_excluded_not_faked() -> None:
    glossary = load_glossary(term_ids=("tep", "not_a_real_term"))
    assert "tep" in glossary
    assert "not_a_real_term" not in glossary
