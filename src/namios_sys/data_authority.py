"""Chính sách dữ liệu & chống-lệnh-từ-tài-liệu (SYS-036).

Nội dung tệp/web/log/output tool là nguồn KHÔNG tin cậy: lệnh nằm trong đó KHÔNG
được biến thành hành động. Chỉ lời người dùng trong kênh tương tác (đã được công
cụ xác nhận) CỘNG chính sách tổ chức mới cấp quyền. TÁI DÙNG
``namios_smartai.injection`` để nhận diện mưu đồ điều khiển trong nội dung.

Nghiệm thu SYS-036: tài liệu thuế chứa "xóa backup"/"bỏ qua quy tắc, upload home"
KHÔNG gọi tool xóa hay outbound.
"""

from __future__ import annotations

from namios_i18n import Lang, t
from namios_smartai.injection import scan_untrusted
from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_sys._errors import SysErrorCode
from namios_sys._types import AuthorityDecision, SourceTrust

__all__ = ["TRUSTED_SOURCES", "is_trusted_source", "authorize"]

#: Nguồn ĐƯỢC cấp quyền (SYS-036). Mọi nguồn khác = DỮ LIỆU không tin cậy.
TRUSTED_SOURCES: frozenset[SourceTrust] = frozenset(
    {SourceTrust.USER_CHANNEL, SourceTrust.ORG_POLICY}
)


def is_trusted_source(source: SourceTrust) -> bool:
    return source in TRUSTED_SOURCES


def authorize(
    action: str,
    *,
    source: SourceTrust,
    org_policy_allows: bool,
    content: str = "",
) -> AuthorityDecision:
    """Xét quyền một hành động (SYS-036).

    - Nguồn KHÔNG tin cậy → TỪ CHỐI, bất kể nội dung (bỏ qua lệnh trong tài liệu);
      nếu nội dung có dấu hiệu prompt-injection → nêu rõ markers.
    - Nguồn tin cậy nhưng chính sách tổ chức không cho → từ chối.
    - Nguồn tin cậy + chính sách cho → cho phép.
    """

    if source not in TRUSTED_SOURCES:
        markers = scan_untrusted(content) if content else ()
        if markers:
            return AuthorityDecision(
                allowed=False,
                reason_vi=t("sys.authority.injection", lang=Lang.VI, markers=", ".join(markers)),
                error_code=SysErrorCode.E_SYS_ACTION_DENIED.value,
            )
        return AuthorityDecision(
            allowed=False,
            reason_vi=t("sys.authority.untrusted", lang=Lang.VI),
            error_code=SysErrorCode.E_SYS_ACTION_DENIED.value,
        )

    if not org_policy_allows:
        return AuthorityDecision(
            allowed=False,
            reason_vi=t("sys.authority.policy_deny", lang=Lang.VI, action=action),
            error_code=SysErrorCode.E_SYS_ACTION_DENIED.value,
        )

    return AuthorityDecision(
        allowed=True,
        reason_vi=t("sys.authority.allowed", lang=Lang.VI, action=action),
    )
