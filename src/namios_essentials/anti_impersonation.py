"""Chống mạo danh thương hiệu (APP11-003/033).

Allowlist tên miền chính thức: một URL chỉ được coi là "link chính thức" khi
(a) scheme HTTPS VÀ (b) host bằng đúng — hoặc là subdomain của — một tên miền
trong ``OFFICIAL_DOMAIN_ALLOWLIST``. Tên miền GẦN GIỐNG (vd
``whatsapp-login.example`` chứa thương hiệu "whatsapp" nhưng KHÔNG nằm trong
allowlist) bị CHẶN TRƯỚC khi bất kỳ form đăng nhập nào được phép hiển thị
(APP11-003 nghiệm thu, E11-06) — ``may_render_login_form`` là cổng DUY NHẤT,
cho nên không có đường nào khác để một trang giả hiện ô nhập mật khẩu.

Trạng thái nhãn hiệu (APP11-033): ``approved`` chỉ hiệu lực khi ĐI KÈM hồ sơ
quyền thật (``has_permission_doc``); ``pending`` hoặc thiếu hồ sơ → luôn
``replace_with_text`` (không tự ý dùng logo/tên khi quyền chưa rõ).
"""

from __future__ import annotations

from urllib.parse import urlsplit

from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._errors import EssentialsErrorCode
from namios_essentials._types import DomainCheckResult, TrademarkStatus
from namios_i18n import Lang, t

__all__ = [
    "OFFICIAL_DOMAIN_ALLOWLIST",
    "BRAND_TOKENS",
    "check_official_url",
    "may_render_login_form",
    "effective_trademark_status",
]

#: Allowlist tên miền chính thức (Phụ lục 11 §2/§6 nguồn [1][2]) — kiểm độc lập
#: trước mỗi release (APP11-003 nghiệm thu). Danh sách này mô tả cấu trúc hợp
#: đồng; danh sách THẬT do đội vận hành ký duyệt mỗi lần đóng ISO.
OFFICIAL_DOMAIN_ALLOWLIST: frozenset[str] = frozenset(
    {
        "zalo.me",
        "id.zalo.me",
        "youtube.com",
        "www.youtube.com",
        "google.com",
        "maps.google.com",
        "www.google.com",
        "tiktok.com",
        "www.tiktok.com",
        "facebook.com",
        "www.facebook.com",
        "whatsapp.com",
        "web.whatsapp.com",
    }
)

#: Thương hiệu hay bị mạo danh — dùng để PHÁT HIỆN domain "gần giống" (chứa tên
#: thương hiệu nhưng không allowlisted), KHÔNG dùng để tự động cho phép.
BRAND_TOKENS: tuple[str, ...] = (
    "zalo",
    "whatsapp",
    "facebook",
    "youtube",
    "tiktok",
    "maps",
    "google",
)


def _registrable_allowed(host: str) -> bool:
    host = host.lower().rstrip(".")
    for allowed in OFFICIAL_DOMAIN_ALLOWLIST:
        if host == allowed or host.endswith("." + allowed):
            return True
    return False


def check_official_url(url: str) -> DomainCheckResult:
    """Kiểm một URL trước khi mở shortcut (APP11-003). Fail-closed: thiếu
    HTTPS hoặc host không nằm trong allowlist → ``allowed=False``; nếu host có
    chứa tên thương hiệu đã biết thì đánh dấu ``impersonation_suspected=True``
    kèm mã lỗi riêng (phân biệt "domain lạ không liên quan" với "domain giả
    mạo thương hiệu" — cả hai đều bị chặn, nhưng cảnh báo khác mức)."""

    parts = urlsplit(url.strip())
    scheme_ok = parts.scheme == "https"
    host = (parts.hostname or "").lower()

    if scheme_ok and _registrable_allowed(host):
        return DomainCheckResult(
            allowed=True,
            scheme_ok=True,
            domain=host,
            reason_vi=t("essentials.domain.allowed", lang=Lang.VI, domain=host),
        )

    suspected = any(token in host for token in BRAND_TOKENS) and not _registrable_allowed(host)
    if suspected:
        return DomainCheckResult(
            allowed=False,
            scheme_ok=scheme_ok,
            domain=host,
            reason_vi=t("essentials.domain.impersonation", lang=Lang.VI, domain=host),
            impersonation_suspected=True,
            error_code=EssentialsErrorCode.E_APP11_DOMAIN_IMPERSONATION_SUSPECTED.value,
        )
    return DomainCheckResult(
        allowed=False,
        scheme_ok=scheme_ok,
        domain=host,
        reason_vi=t("essentials.domain.not_allowlisted", lang=Lang.VI, domain=host),
        error_code=EssentialsErrorCode.E_APP11_DOMAIN_NOT_ALLOWLISTED.value,
    )


def may_render_login_form(check: DomainCheckResult) -> bool:
    """Cổng DUY NHẤT quyết định có được hiển thị form đăng nhập không
    (APP11-003, E11-06). Domain mạo danh/không allowlisted → luôn ``False``
    — TRƯỚC khi người dùng có cơ hội nhập mật khẩu."""

    return check.allowed


def effective_trademark_status(
    status: TrademarkStatus, *, has_permission_doc: bool
) -> TrademarkStatus:
    """APP11-033: ``approved`` chỉ hiệu lực khi CÓ hồ sơ quyền thật; ``pending``
    hoặc thiếu hồ sơ → luôn hạ về ``replace_with_text`` (fail-closed, không tự
    ý giữ logo/tên khi quyền chưa xác nhận)."""

    if status is TrademarkStatus.APPROVED and has_permission_doc:
        return TrademarkStatus.APPROVED
    return TrademarkStatus.REPLACE_WITH_TEXT
