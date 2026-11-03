"""Mã lỗi ổn định RIÊNG của ``namios_compat`` (Phụ lục 03, COMP-025..054).

Giống ``namios_eco._errors``: chỉ định nghĩa mã cho vi phạm KHÔNG có mã tương
đương trong ``namios_core.errors.ErrorCode`` (WP1 sở hữu module đó — không
sửa). Vi phạm khớp ngữ nghĩa có sẵn (cấu trúc JSON chung, thiếu evidence,
chuyển trạng thái, path không an toàn, nguồn không hợp lệ) thì dùng thẳng
``ErrorCode`` để giữ MỘT bộ mã thống nhất toàn repo.

``namios_core.validation.ValidationError.code`` chỉ là ``str`` (không ép enum),
nên trộn mã từ hai enum trong cùng danh sách lỗi là hợp lệ.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["CompatErrorCode"]


class CompatErrorCode(str, Enum):
    """Mã lỗi ổn định đặc thù Trung tâm tương thích (KHÔNG đổi chuỗi sau phát hành)."""

    #: ``schema_version`` thiếu hoặc khác giá trị hợp đồng hiện hành (COMP-048).
    E_COMPAT_SCHEMA_VERSION = "E_COMPAT_SCHEMA_VERSION"
    #: ``required_steps`` không khớp đúng 7 nấc ECO-001 (tên/thứ tự/số lượng).
    E_COMPAT_REQUIRED_STEPS = "E_COMPAT_REQUIRED_STEPS"
    #: Giá trị enum (mode/status/sector/device_class/protocol…) không hợp lệ.
    E_COMPAT_ENUM_INVALID = "E_COMPAT_ENUM_INVALID"
    #: Chứng nhận tự nhận end_to_end=pass / technical=verified nhưng thiếu
    #: ``tested_at`` hoặc thiếu evidence cho đủ các nấc bắt buộc (COMP-048/049).
    E_COMPAT_CERT_UNSUPPORTED = "E_COMPAT_CERT_UNSUPPORTED"
    #: ``vendor_support=supported`` nhưng không có bằng chứng (COMP-048).
    E_COMPAT_VENDOR_CLAIM = "E_COMPAT_VENDOR_CLAIM"
    #: Chứng nhận gắn với phiên bản app/token đã đổi → mất hiệu lực (COMP-025).
    E_COMPAT_CERT_STALE = "E_COMPAT_CERT_STALE"
    #: Thiết bị cùng hãng khác model bị suy ra "được hỗ trợ" mà chưa test riêng (COMP-032).
    E_COMPAT_DEVICE_CARRYOVER = "E_COMPAT_DEVICE_CARRYOVER"
    #: Workflow pack chứa thông tin đăng nhập/cookie/PIN/secret (COMP-031 cấm).
    E_COMPAT_PACK_SECRET = "E_COMPAT_PACK_SECRET"
