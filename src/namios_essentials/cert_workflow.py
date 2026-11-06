"""Chứng nhận workflow per-chức-năng (APP11-028) + kiểm version app Wine
(APP11-021).

Ghi theo app/version/browser/OS/hardware/permission/test date, MỖI CHỨC NĂNG
RIÊNG. TÁI DÙNG state machine ``namios_odc`` (``CertState``/``EvidenceKind``/
``advance``/``can_publish``/``publish``) — các hàm NÀY chỉ đổi ĐƠN VỊ áp dụng
từ "thiết bị" (``DeviceCert``) sang "app" (``AppCertProfile``); KHÔNG viết lại
quyết định thăng cấp (``advance``) — gọi thẳng hàm gốc của ``namios_odc``.

Bất biến (APP11-028 nghiệm thu): chứng nhận một chức năng KHÔNG BAO GIỜ suy ra
chức năng khác — YouTube ``WATCH_VIDEO`` đạt KHÔNG suy ra ``DRM_PLAYBACK`` đạt;
WhatsApp ``CHAT`` đạt KHÔNG suy ra ``CALL_VIDEO`` đạt (bảo đảm bằng cấu trúc:
``function_state`` chỉ đọc đúng key được truyền, không có nhánh "suy từ chức
năng khác cùng app").

Bất biến (APP11-021/026, E11-07): vendor tự đổi binary app Wine (hash đổi) →
MỌI chức năng đã ``PUBLISHED`` chuyển ``NEEDS_RETEST`` ngay — không âm thầm
giữ chứng nhận cũ, không tuyên bố tiếp tục hỗ trợ; ``last_known_good_hash``
lưu lại bản TRƯỚC để còn đường quay về khi điều khoản/installer cho phép.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from namios_essentials._types import AppCertProfile, AppFunction
from namios_odc import CertState, EvidenceKind, advance, can_publish, publish

__all__ = [
    "function_state",
    "is_function_supported",
    "with_needs_retest",
    "on_binary_hash_change",
    "advance_function",
    "can_publish_function",
    "publish_function",
]


def function_state(profile: AppCertProfile, func: AppFunction) -> CertState | None:
    """Trạng thái chứng nhận MỘT chức năng (APP11-028). Chưa khai → ``None`` —
    KHÔNG suy từ chức năng khác cùng app, KHÔNG mặc định ``REPORTED``."""

    return profile.functions.get(func)


def is_function_supported(profile: AppCertProfile, func: AppFunction) -> bool:
    """Chức năng đã CÔNG BỐ hỗ trợ chưa (APP11-028). ``True`` chỉ khi
    ``PUBLISHED`` — "mở được"/"đăng nhập được" của một chức năng KHÁC không
    đủ để coi chức năng này đạt."""

    return function_state(profile, func) is CertState.PUBLISHED


def with_needs_retest(profile: AppCertProfile, funcs: Iterable[AppFunction]) -> AppCertProfile:
    """Đánh dấu các chức năng PHẢI kiểm lại (APP11-021/033). Trả hồ sơ MỚI
    (bất biến) — chỉ các chức năng trong ``funcs`` bị đụng, phần còn lại giữ
    nguyên trạng thái cũ."""

    updated = dict(profile.functions)
    for f in funcs:
        updated[f] = CertState.NEEDS_RETEST
    return replace(profile, functions=updated)


def advance_function(
    profile: AppCertProfile, func: AppFunction, evidence: EvidenceKind
) -> AppCertProfile:
    """Nâng trạng thái MỘT chức năng theo bằng chứng (APP11-028) — ỦY QUYỀN
    thẳng cho ``namios_odc.advance`` (KHÔNG viết lại quyết định thăng cấp):
    cộng đồng/AI không bao giờ nâng; ``lab_test``/``pilot_signoff`` tiến tuyến
    tính, không nhảy cóc. Chỉ ``func`` được đụng tới."""

    current = function_state(profile, func)
    updated = dict(profile.functions)
    updated[func] = advance(current, evidence)
    return replace(profile, functions=updated)


def can_publish_function(profile: AppCertProfile, func: AppFunction) -> bool:
    """Chức năng đủ điều kiện công bố chưa (APP11-028) — ỦY QUYỀN
    ``namios_odc.can_publish``: chỉ ``True`` khi đã ``pilot_verified``."""

    return can_publish(function_state(profile, func))


def publish_function(profile: AppCertProfile, func: AppFunction) -> AppCertProfile:
    """Công bố MỘT chức năng (APP11-028) — ỦY QUYỀN ``namios_odc.publish``:
    chỉ chuyển ``PUBLISHED`` khi đã ``pilot_verified``, còn lại giữ nguyên."""

    current = function_state(profile, func)
    updated = dict(profile.functions)
    updated[func] = publish(current)
    return replace(profile, functions=updated)


def on_binary_hash_change(profile: AppCertProfile, new_hash: str) -> AppCertProfile:
    """Vendor tự đổi binary app Wine (APP11-021, E11-07). Hash không đổi →
    trả nguyên ``profile``. Hash đổi → MỌI chức năng hiện ``PUBLISHED`` chuyển
    ``NEEDS_RETEST`` (không tuyên bố tiếp tục hỗ trợ); ``last_known_good_hash``
    lưu hash CŨ để còn đường quay về bản trước đã chứng nhận."""

    if new_hash == profile.binary_hash:
        return profile

    published_funcs = [f for f, state in profile.functions.items() if state is CertState.PUBLISHED]
    retested = with_needs_retest(profile, published_funcs)
    return replace(retested, binary_hash=new_hash, last_known_good_hash=profile.binary_hash)
