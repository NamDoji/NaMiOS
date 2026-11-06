"""Danh mục khả năng THẬT (SYS-038).

Bảng hỗ trợ tách rõ ``available_to_download`` / ``launches`` / ``workflow_verified``
theo (app, version, workflow, model, thiết bị, môi trường, ngày test). TÁI DÙNG
gate ECO-003: thêm dòng tự nhận "dùng được" (``USABLE``) khi ``published_status``
chưa đủ → bị CHẶN (SYS-038). Tra một (app, version) chưa có phiếu → "chưa kiểm".
"""

from __future__ import annotations

from namios_core.validation import ValidationError
from namios_eco.status import PublishedStatus, is_usable
from namios_i18n import Lang, t
from namios_sys import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_sys._errors import SysErrorCode
from namios_sys._types import CapabilityRow

__all__ = ["CapabilityCatalog", "validate_capability_row"]


def validate_capability_row(row: CapabilityRow) -> list[ValidationError]:
    """Chặn overclaim: không có dòng nào được coi là usable qua ``is_usable``
    mà lại thiếu ``test_date`` (bằng chứng tối thiểu: đã test ngày nào). Rỗng =
    hợp lệ. (Gate đủ/không-đủ evidence sâu hơn ở ECO/COMP.)"""

    errors: list[ValidationError] = []
    if is_usable(row.published_status) and not (row.test_date or "").strip():
        errors.append(
            ValidationError(
                code=SysErrorCode.E_SYS_CAPABILITY_OVERCLAIM.value,
                path="test_date",
                message_vi=t("sys.capability.overclaim", lang=Lang.VI),
            )
        )
    return errors


class CapabilityCatalog:
    """Kho dòng khả năng. ``add`` chặn overclaim; ``lookup`` trả dòng đúng
    (app, version) hoặc ``None`` ("chưa kiểm"); ``summary`` đếm theo mức thật."""

    def __init__(self) -> None:
        self._rows: list[CapabilityRow] = []

    def add(self, row: CapabilityRow) -> None:
        """Thêm dòng — từ chối (``ValueError``) nếu overclaim (SYS-038)."""

        problems = validate_capability_row(row)
        if problems:
            raise ValueError(problems[0].message_vi)
        self._rows.append(row)

    def rows(self) -> tuple[CapabilityRow, ...]:
        return tuple(self._rows)

    def lookup(
        self, app_id: str, version: str, workflow: str | None = None
    ) -> CapabilityRow | None:
        """Dòng khớp (app, version) [+ workflow nếu nêu]. Không có → ``None``
        (gọi ``untested_message`` để lấy câu 'chưa kiểm' trung thực)."""

        a, v = app_id.strip().lower(), version.strip().lower()
        for r in self._rows:
            if r.app_id.strip().lower() == a and r.version.strip().lower() == v:
                if workflow is None or r.workflow.strip().lower() == workflow.strip().lower():
                    return r
        return None

    def untested_message(self, app_id: str, version: str) -> str:
        return t("sys.capability.untested", lang=Lang.VI, app=app_id, version=version)

    def summary(self) -> dict[str, int]:
        """Đếm theo mức THẬT — tách tải/mở/đã-kiểm (SYS-038: không gộp)."""

        counts = {
            "available_to_download": 0,
            "launches": 0,
            "workflow_verified": 0,
            "other": 0,
        }
        for r in self._rows:
            if r.published_status == PublishedStatus.DOWNLOADABLE_ONLY:
                counts["available_to_download"] += 1
            elif r.published_status == PublishedStatus.LAUNCHES_ONLY:
                counts["launches"] += 1
            elif r.published_status == PublishedStatus.WORKFLOW_VERIFIED:
                counts["workflow_verified"] += 1
            else:
                counts["other"] += 1
        return counts
