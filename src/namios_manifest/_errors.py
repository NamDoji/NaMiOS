"""Exception nội bộ WP2 — bọc danh sách ``ValidationError`` để ``load()``
raise khi tầng 1 (schema) hoặc bước build-recipe (semantic sớm) fail.

KHÔNG dùng để truyền exception qua stdout JSON trực tiếp — caller (WP3 CLI)
chịu trách nhiệm bắt và ánh xạ sang envelope/exit code.
"""

from __future__ import annotations

from namios_core.validation import ValidationError

__all__ = ["ManifestLoadError"]


class ManifestLoadError(Exception):
    """Manifest không tải được (schema fail hoặc recipe build-time reject)."""

    def __init__(self, errors: tuple[ValidationError, ...]) -> None:
        self.errors = errors
        messages = "; ".join(e.message_vi for e in errors) or "lỗi không xác định"
        super().__init__(f"Không tải được manifest: {messages}")
