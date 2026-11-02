"""Unit test ``namios_catalog._fold.fold_vn`` — chuẩn hóa bỏ dấu + casefold."""

from __future__ import annotations

from namios_catalog._fold import fold_vn


def test_fold_vn_removes_tone_marks() -> None:
    assert fold_vn("Đỗ Chí Cường") == "do chi cuong"


def test_fold_vn_casefold_is_locale_independent_for_ascii() -> None:
    assert fold_vn("MISA SME") == "misa sme"
    assert fold_vn("misa sme") == "misa sme"


def test_fold_vn_idempotent_on_already_plain_text() -> None:
    assert fold_vn("do chi cuong") == "do chi cuong"


def test_fold_vn_handles_dj_both_cases() -> None:
    assert fold_vn("đất nước") == "dat nuoc"
    assert fold_vn("ĐẤT NƯỚC") == "dat nuoc"


def test_fold_vn_does_not_mutate_input_string_object() -> None:
    original = "Đỗ Chí Cường"
    fold_vn(original)
    # chuỗi Python bất biến — xác nhận gọi fold không có side effect ẩn nào
    # khác ngoài trả giá trị mới.
    assert original == "Đỗ Chí Cường"


def test_fold_vn_empty_string() -> None:
    assert fold_vn("") == ""


def test_fold_vn_mixed_vn_and_ascii_substring_match() -> None:
    folded = fold_vn("Ứng Dụng Tiếng Việt")
    assert "ung dung" in folded
    assert "tieng viet" in folded
