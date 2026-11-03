"""Kiểu dữ liệu thẩm định dùng chung, không phụ thuộc module nào khác trong
``namios_core`` — tồn tại để tránh import vòng giữa ``manifest_types`` và
``recipe_types`` (cả hai đều cần ``ValidationError``/``SemanticContext``).

KHÔNG chứa business logic (chỉ dataclass thuần). Xem M1-INTERFACES.md §7.1/§7.6.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    """Một lỗi thẩm định (schema hoặc semantic).

    ``code`` PHẢI là một giá trị của ``namios_core.errors.ErrorCode``.
    ``path`` trỏ đúng vị trí trong tài liệu nguồn (ví dụ ``"runtime.runner_id"``).
    """

    code: str
    path: str
    message_vi: str


@dataclass(frozen=True)
class SemanticContext:
    """Dữ liệu ngữ cảnh để kiểm điều kiện ngữ nghĩa (tầng 2) của manifest/recipe."""

    approved_dependency_ids: frozenset[str]
    pinned_runner_hashes: frozenset[str]
    revoked_ids: frozenset[str]
