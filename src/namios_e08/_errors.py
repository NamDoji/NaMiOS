"""Mã lỗi ổn định cho ``namios_e08`` (Phụ lục 08)."""

from __future__ import annotations

from enum import Enum

__all__ = ["E08ErrorCode"]


class E08ErrorCode(str, Enum):
    """Mã lỗi machine-readable (E08). Trường dữ liệu, giữ nguyên qua i18n."""

    E_E08_DRIVER_NAME_MATCH = "E_E08_DRIVER_NAME_MATCH"  # ghép theo tên gần giống
    E_E08_PROVENANCE_UNTRUSTED = "E_E08_PROVENANCE_UNTRUSTED"  # nguồn driver không tin
    E_E08_INSTALL_HALF = "E_E08_INSTALL_HALF"  # cài nửa vời không rollback
    E_E08_WORKFLOW_OVERCLAIM = "E_E08_WORKFLOW_OVERCLAIM"  # tool-ok coi là workflow-ok
    E_E08_LOG_AS_COMMAND = "E_E08_LOG_AS_COMMAND"  # log/tài liệu thành lệnh
    E_E08_AI_UNBOUNDED = "E_E08_AI_UNBOUNDED"  # AI root/binary/no-rollback
