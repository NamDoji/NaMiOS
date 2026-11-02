"""Exception nội bộ WP10 — bọc danh sách ``ValidationError`` để ``parse()``
raise khi recipe chứa action/param ngoài allowlist hoặc có shell/eval/
url-script/template nội suy.

KHÔNG dùng để truyền exception qua stdout JSON trực tiếp — caller (WP3 CLI/
WP6 planner) chịu trách nhiệm bắt và ánh xạ sang envelope/exit code.
"""

from __future__ import annotations

from namios_core.validation import ValidationError

__all__ = ["RecipeParseError"]


class RecipeParseError(Exception):
    """Recipe không parse được (action/param ngoài allowlist, shell/eval/
    url-script/template nội suy, hoặc kiểu dữ liệu sai)."""

    def __init__(self, errors: tuple[ValidationError, ...]) -> None:
        self.errors = errors
        messages = "; ".join(e.message_vi for e in errors) or "lỗi không xác định"
        super().__init__(f"Không parse được recipe: {messages}")
