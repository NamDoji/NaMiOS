"""Hàng rào chống prompt-injection trên nội dung KHÔNG TIN CẬY (SAI-019).

Bất biến kiến trúc (Phụ lục 04 §1/§8): log Wine/trang web/tài liệu/đầu ra
lệnh đọc được coi là DỮ LIỆU — không bao giờ tự nó biến thành ``ToolCall``.
Pipeline thật (intent → planner → policy → Tool Broker) chỉ nhận ACTION CÓ
CẤU TRÚC do lớp lập kế hoạch phát ra; không có đường nào để một chuỗi text
đọc từ nguồn không tin cậy "tự thực thi". Các hàm dưới đây CHỈ quét/đánh dấu
nội dung đó khi hiển thị cho người dùng hoặc khi một caller buộc phải NẠP
(ingest) nó — không hàm nào ở đây tạo ra hoặc gọi ``ToolCall``.
"""

from __future__ import annotations

from namios_eco.search import fold_vn
from namios_i18n import Lang, t
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._errors import SaiErrorCode
from namios_smartai._types import ToolResult, ToolResultStatus

__all__ = ["INJECTION_MARKERS", "scan_untrusted", "is_injection", "guard_untrusted"]


#: Cụm từ báo hiệu mưu đồ điều khiển trong nội dung không tin cậy (log/web/
#: tài liệu). So khớp dạng substring SAU KHI fold cả nội dung lẫn marker
#: (``fold_vn``: bỏ dấu + casefold) — bắt được biến thể có/không dấu tiếng
#: Việt (vd "Bỏ qua quy tắc" ~ "bo qua quy tac").
#: Lưu ý: dùng "/home" (không có dấu "/" ở cuối, khác bản thảo gốc) để bắt
#: được cả đường dẫn con (vd "/home/user/...") lẫn câu dạng tự do kiểu
#: "gửi /home sang ..." mà không yêu cầu khớp đúng ký tự cuối.
INJECTION_MARKERS: tuple[str, ...] = (
    "ignore previous",
    "ignore all previous",
    "bo qua quy tac",
    "bo qua huong dan",
    "disregard",
    "system prompt",
    "upload",
    "send to http",
    "gui /home",
    "rm -rf",
    "sudo",
    "curl ",
    "wget ",
    "exfiltrate",
    "/home",
)


def scan_untrusted(text: str) -> tuple[str, ...]:
    """Quét ``text`` (không tin cậy) tìm các marker mưu đồ điều khiển.

    Trả các marker khớp (fold-insensitive, theo thứ tự khai báo trong
    ``INJECTION_MARKERS``) — tuple rỗng = sạch. Hàm CHỈ đọc ``text`` làm dữ
    liệu chuỗi; không raise, không I/O, không có đường nào dẫn tới thực thi
    bất kỳ phần nào của ``text``."""

    folded = fold_vn(text)
    return tuple(marker for marker in INJECTION_MARKERS if fold_vn(marker) in folded)


def is_injection(text: str) -> bool:
    """``True`` nếu ``text`` chứa ít nhất một mưu đồ điều khiển đã biết."""

    return bool(scan_untrusted(text))


def guard_untrusted(text: str) -> ToolResult | None:
    """Tiện ích fail-closed cho caller PHẢI nạp nội dung không tin cậy.

    Trả ``ToolResult(BLOCKED, error_code=E_SAI_INJECTION_BLOCKED, ...)`` nếu
    phát hiện mưu đồ điều khiển trong ``text``; trả ``None`` nếu sạch (caller
    tự quyết tiếp — hàm này không tự động làm gì khác).

    Bảo đảm kiến trúc: đây KHÔNG phải là đường để ``text`` biến thành hành
    động. Không có nhánh nào trong hàm này xây hoặc gọi ``ToolCall`` — nội
    dung không tin cậy luôn chỉ được quét/hiển thị dưới dạng DỮ LIỆU; hàm
    này đơn thuần cho caller một lối fail-closed sớm trước khi dùng nội
    dung đó cho bất kỳ quyết định nào."""

    markers = scan_untrusted(text)
    if not markers:
        return None
    return ToolResult(
        status=ToolResultStatus.BLOCKED,
        error_code=SaiErrorCode.E_SAI_INJECTION_BLOCKED.value,
        message_vi=t("sai.injection.blocked", lang=Lang.VI, detail=", ".join(markers)),
    )
