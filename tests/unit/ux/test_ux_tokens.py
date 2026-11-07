"""UX12 §3.2 [4] — contrast_ratio/meets_wcag: gate cặp màu text/surface."""

from __future__ import annotations

import pytest

from namios_ux.tokens import (
    DesignToken,
    TokenCategory,
    contrast_ratio,
    meets_wcag,
    token_pair_meets_wcag,
)


def test_black_on_white_is_21_to_1() -> None:
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0, rel=1e-6)


def test_white_on_white_is_1_to_1() -> None:
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0, rel=1e-6)


def test_ratio_is_order_independent() -> None:
    forward = contrast_ratio("#000000", "#ffffff")
    backward = contrast_ratio("#ffffff", "#000000")
    assert forward == pytest.approx(backward, rel=1e-9)


def test_short_hex_form_matches_long_form() -> None:
    assert contrast_ratio("#fff", "#000") == pytest.approx(
        contrast_ratio("#ffffff", "#000000"), rel=1e-9
    )


def test_hex_without_hash_prefix_works() -> None:
    assert contrast_ratio("000000", "ffffff") == pytest.approx(21.0, rel=1e-6)


def test_invalid_hex_raises_value_error() -> None:
    with pytest.raises(ValueError):
        contrast_ratio("not-a-color", "#ffffff")


def test_invalid_hex_length_raises_value_error() -> None:
    with pytest.raises(ValueError):
        contrast_ratio("#1234", "#ffffff")


def test_meets_wcag_normal_text_threshold() -> None:
    assert meets_wcag(4.5) is True
    assert meets_wcag(4.49) is False


def test_meets_wcag_large_text_threshold() -> None:
    assert meets_wcag(3.0, large=True) is True
    assert meets_wcag(2.99, large=True) is False
    # Một tỉ lệ đạt ngưỡng chữ lớn nhưng KHÔNG đạt ngưỡng chữ thường.
    assert meets_wcag(3.5, large=False) is False
    assert meets_wcag(3.5, large=True) is True


def test_token_pair_below_threshold_fails_gate() -> None:
    # INVARIANT: cặp màu text/surface dưới ngưỡng → fail.
    light_gray_text = DesignToken(name="text.weak", value="#cccccc", category=TokenCategory.COLOR)
    white_surface = DesignToken(name="surface", value="#ffffff", category=TokenCategory.COLOR)
    assert token_pair_meets_wcag(light_gray_text, white_surface) is False


def test_token_pair_above_threshold_passes_gate() -> None:
    dark_text = DesignToken(name="text.primary", value="#1a1a1a", category=TokenCategory.COLOR)
    white_surface = DesignToken(name="surface", value="#ffffff", category=TokenCategory.COLOR)
    assert token_pair_meets_wcag(dark_text, white_surface) is True


def test_token_pair_large_text_relaxed_threshold() -> None:
    # Một tỉ lệ nằm giữa 3.0 và 4.5: fail ở chữ thường, pass ở chữ lớn.
    mid_gray_text = DesignToken(name="text.hero", value="#767676", category=TokenCategory.COLOR)
    white_surface = DesignToken(name="surface", value="#ffffff", category=TokenCategory.COLOR)
    ratio = contrast_ratio(mid_gray_text.value, white_surface.value)
    assert ratio == pytest.approx(4.5, rel=0.02)
    assert token_pair_meets_wcag(mid_gray_text, white_surface, large=True) is True
