"""Bounded actuator cho SmartAI vận hành (E08-030).

AI chỉ gọi typed-tool theo quyền; nội dung LOG/tài-liệu/output-tool KHÔNG thành lệnh
(test A01: log "cài driver từ URL" không trở thành action — TÁI DÙNG
``namios_sys.data_authority``). Bước THAY ĐỔI hệ bắt buộc có rollback; không root shell,
không tự tải binary (E08-030).
"""

from __future__ import annotations

from namios_e08._types import AiAction
from namios_sys._types import SourceTrust
from namios_sys.data_authority import authorize

__all__ = ["log_instruction_authorized", "FORBIDDEN_TOOL_MARKERS", "action_is_safe"]

#: Dấu hiệu công cụ bị CẤM cho AI (E08-030): root shell, tự tải/chạy binary.
FORBIDDEN_TOOL_MARKERS: frozenset[str] = frozenset(
    {"root_shell", "shell", "exec", "download_binary", "curl", "flash_firmware", "sign_submit"}
)


def log_instruction_authorized(action: str, *, content: str = "") -> bool:
    """Chỉ-dẫn trong LOG/output-tool có thành hành động không (E08-030, A01). KHÔNG —
    log là nguồn không tin cậy (data_authority: source=LOG luôn bị từ chối)."""

    return authorize(
        action, source=SourceTrust.LOG, org_policy_allows=True, content=content
    ).allowed


def action_is_safe(action: AiAction, *, changes_system: bool) -> bool:
    """Hành động AI có được phép thực thi không (E08-030), fail-closed:

    - Tên tool chứa dấu hiệu cấm (root/shell/exec/download/flash/ký-nộp) → KHÔNG.
    - Bước THAY ĐỔI hệ mà thiếu ``rollback_id`` → KHÔNG (bắt buộc có đường lùi).
    - Còn lại (typed-tool, read-only, hoặc có rollback) → được.
    """

    name = action.tool_name.strip().lower()
    if not name:
        return False
    if any(marker in name for marker in FORBIDDEN_TOOL_MARKERS):
        return False
    if changes_system and not action.rollback_id.strip():
        return False
    return True
