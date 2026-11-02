"""Exception nội bộ WP9 — bọc danh sách ``ValidationError`` để ``load()``
raise khi tầng 1 (schema) fail (JSON không parse được hoặc vi phạm cấu trúc).

KHÔNG dùng để truyền exception qua stdout JSON trực tiếp — caller (WP3 CLI)
chịu trách nhiệm bắt và ánh xạ sang envelope/exit code (mirror
``namios_manifest._errors.ManifestLoadError``).
"""

from __future__ import annotations

from namios_core.validation import ValidationError

__all__ = ["EvidenceLoadError"]


class EvidenceLoadError(Exception):
    """Evidence report không tải được (JSON hỏng hoặc schema tầng 1 fail)."""

    def __init__(self, errors: tuple[ValidationError, ...]) -> None:
        self.errors = errors
        messages = "; ".join(e.message_vi for e in errors) or "lỗi không xác định"
        super().__init__(f"Không tải được evidence report: {messages}")
