"""APP11-003/033 — chống mạo danh thương hiệu. E11-06 (whatsapp-login.example
bị chặn trước khi nhập mật khẩu) + E11-02 (6 dịch vụ web, URL HTTPS chính thức)."""

from __future__ import annotations

from namios_essentials import (
    TrademarkStatus,
    check_official_url,
    effective_trademark_status,
    may_render_login_form,
)
from namios_essentials._errors import EssentialsErrorCode

TS = TrademarkStatus

#: 6 dịch vụ web của §2 bảng danh mục (E11-02).
_SIX_OFFICIAL_URLS = (
    "https://id.zalo.me/",
    "https://www.youtube.com/",
    "https://maps.google.com/",
    "https://www.tiktok.com/",
    "https://www.facebook.com/",
    "https://web.whatsapp.com/",
)


def test_e11_02_six_official_services_are_https_and_allowlisted() -> None:
    for url in _SIX_OFFICIAL_URLS:
        result = check_official_url(url)
        assert result.allowed is True, url
        assert result.scheme_ok is True, url
        assert may_render_login_form(result) is True, url


def test_e11_06_lookalike_whatsapp_domain_is_blocked() -> None:
    # Trang giả "whatsapp-login.example" — KHÔNG mở từ shortcut, cảnh báo mạo danh.
    result = check_official_url("https://whatsapp-login.example/login")
    assert result.allowed is False
    assert result.impersonation_suspected is True
    assert result.error_code == EssentialsErrorCode.E_APP11_DOMAIN_IMPERSONATION_SUSPECTED.value
    # Cổng DUY NHẤT cho form đăng nhập phải khóa TRƯỚC khi người dùng nhập mật khẩu.
    assert may_render_login_form(result) is False


def test_lookalike_zalo_domain_is_also_blocked() -> None:
    result = check_official_url("https://zalo-id-login.example/")
    assert result.allowed is False
    assert result.impersonation_suspected is True


def test_unrelated_unknown_domain_is_blocked_without_impersonation_flag() -> None:
    # Domain lạ không liên quan thương hiệu nào — vẫn chặn (không allowlisted)
    # nhưng KHÔNG đáng báo "mạo danh" (phân biệt mức cảnh báo).
    result = check_official_url("https://random-unrelated-site.example/")
    assert result.allowed is False
    assert result.impersonation_suspected is False
    assert result.error_code == EssentialsErrorCode.E_APP11_DOMAIN_NOT_ALLOWLISTED.value


def test_http_scheme_is_rejected_even_if_domain_allowlisted() -> None:
    # APP11-003: shortcut web PHẢI HTTPS.
    result = check_official_url("http://web.whatsapp.com/")
    assert result.scheme_ok is False
    assert result.allowed is False
    assert may_render_login_form(result) is False


def test_subdomain_of_allowlisted_domain_is_allowed() -> None:
    result = check_official_url("https://m.facebook.com/")
    assert result.allowed is True


# --------------------------------------------------------------------------- #
# APP11-033 — trademark status                                                #
# --------------------------------------------------------------------------- #


def test_approved_without_permission_doc_falls_back_to_text() -> None:
    assert effective_trademark_status(TS.APPROVED, has_permission_doc=False) is TS.REPLACE_WITH_TEXT


def test_approved_with_permission_doc_stays_approved() -> None:
    assert effective_trademark_status(TS.APPROVED, has_permission_doc=True) is TS.APPROVED


def test_pending_always_falls_back_to_text() -> None:
    assert effective_trademark_status(TS.PENDING, has_permission_doc=True) is TS.REPLACE_WITH_TEXT
    assert effective_trademark_status(TS.PENDING, has_permission_doc=False) is TS.REPLACE_WITH_TEXT
