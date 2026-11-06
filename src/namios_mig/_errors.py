"""Mã lỗi ổn định cho ``namios_mig`` (Phụ lục 10, N10-001..060)."""

from __future__ import annotations

from enum import Enum

__all__ = ["MigErrorCode"]


class MigErrorCode(str, Enum):
    """Mã lỗi machine-readable (MIG). Trường dữ liệu, giữ nguyên qua i18n."""

    # Hợp đồng dữ liệu (N10-007/009/026)
    E_MIG_APP_NO_ID = "E_MIG_APP_NO_ID"
    E_MIG_DEVICE_NO_ID = "E_MIG_DEVICE_NO_ID"
    E_MIG_USAGE_NO_OPTIN = "E_MIG_USAGE_NO_OPTIN"  # usage 30-ngày thiếu opt-in
    E_MIG_RECIPE_NO_APP = "E_MIG_RECIPE_NO_APP"
    E_MIG_RECIPE_NO_VERSION = "E_MIG_RECIPE_NO_VERSION"
    E_MIG_RECIPE_NO_RUNNER = "E_MIG_RECIPE_NO_RUNNER"  # wine route thiếu runner pin
    E_MIG_RECIPE_PUBLISH_NO_TEST = "E_MIG_RECIPE_PUBLISH_NO_TEST"
    E_MIG_RECIPE_PUBLISH_NO_OWNER = "E_MIG_RECIPE_PUBLISH_NO_OWNER"
    E_MIG_WORKFLOW_NO_EVIDENCE = "E_MIG_WORKFLOW_NO_EVIDENCE"  # passed thiếu evidence
    E_MIG_WORKFLOW_NO_TESTED_AT = "E_MIG_WORKFLOW_NO_TESTED_AT"
    E_MIG_EVIDENCE_EMPTY = "E_MIG_EVIDENCE_EMPTY"  # evidence record không mang tín hiệu nào
    E_MIG_INVENTORY_NO_MACHINE = "E_MIG_INVENTORY_NO_MACHINE"
    # Assessor (N10-007/014) — bí mật/opt-in
    E_MIG_SECRET_FIELD_REJECTED = (
        "E_MIG_SECRET_FIELD_REJECTED"  # noqa: S105 (mã lỗi, không phải mật khẩu)
    )
    # Readiness (N10-009)
    E_MIG_READINESS_OVERCLAIM = "E_MIG_READINESS_OVERCLAIM"  # ready dù còn essential blocked
    # Compat broker (N10-017/027)
    E_MIG_ROUTE_OVERCLAIM = "E_MIG_ROUTE_OVERCLAIM"  # gán wine cho driver/token-chỉ-Windows
    E_MIG_AI_UNBOUNDED = "E_MIG_AI_UNBOUNDED"  # AI tự tải/vá binary
    # PE analyzer (N10-018)
    E_MIG_DRIVER_AS_APP = "E_MIG_DRIVER_AS_APP"  # gán driver .sys thành app user-mode
    # Workflow verdict (N10-043)
    E_MIG_EXITCODE_AS_DONE = "E_MIG_EXITCODE_AS_DONE"  # exit-code/spool một mình = "xong"
