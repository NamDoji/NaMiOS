"""Mã lỗi ổn định RIÊNG của ``namios_eco`` — chỉ cho những vi phạm không có
mã tương đương trong ``namios_core.errors.ErrorCode`` (module đó do WP1 sở
hữu; ``namios_eco`` KHÔNG sửa/thêm vào đó). Khi một vi phạm khớp ngữ nghĩa có
sẵn (ví dụ lỗi cấu trúc JSON chung, lỗi scheme URL, lỗi chuyển trạng thái,
thiếu evidence) thì dùng thẳng ``namios_core.errors.ErrorCode`` để giữ một bộ
mã lỗi thống nhất toàn repo; chỉ các vi phạm ĐẶC THÙ ECO mới cần mã riêng ở
đây.

``namios_core.validation.ValidationError.code`` chỉ là ``str`` (không ép kiểu
enum), nên trộn mã từ hai enum khác nhau trong cùng danh sách lỗi là hợp lệ.
"""

from __future__ import annotations

from enum import Enum


class EcoErrorCode(str, Enum):
    """Mã lỗi ổn định đặc thù ECO (KHÔNG đổi giá trị chuỗi sau khi phát hành)."""

    #: Mô hình 7 nấc (ECO-001) thiếu một tên nấc bắt buộc.
    E_ECO_STEP_MISSING = "E_ECO_STEP_MISSING"
    #: Mô hình 7 nấc có tên nấc lặp lại hoặc không thuộc 7 tên hợp lệ.
    E_ECO_STEP_UNKNOWN_OR_DUPLICATE = "E_ECO_STEP_UNKNOWN_OR_DUPLICATE"
    #: Thứ tự 7 nấc không đúng thứ tự chuẩn ECO-001.
    E_ECO_STEP_ORDER = "E_ECO_STEP_ORDER"
    #: Dịch vụ web không có bộ cài nhưng đánh dấu acquire=downloaded_binary.
    E_ECO_ACQUIRE_METHOD_INVALID = "E_ECO_ACQUIRE_METHOD_INVALID"
    #: Dịch vụ web install_or_open pass nhưng method không phải mở trình duyệt.
    E_ECO_INSTALL_METHOD_INVALID = "E_ECO_INSTALL_METHOD_INVALID"
    #: Có nơi gán ``downloadable_only``/``launches_only`` là "dùng được" (GATE ECO-003).
    E_ECO_USABILITY_CLAIM = "E_ECO_USABILITY_CLAIM"
    #: Văn bản catalog dùng cụm "ứng dụng chính thức của NaMiOS" cho bên thứ ba (ECO-007).
    E_ECO_OFFICIAL_CLAIM_FORBIDDEN = "E_ECO_OFFICIAL_CLAIM_FORBIDDEN"


__all__ = ["EcoErrorCode"]
