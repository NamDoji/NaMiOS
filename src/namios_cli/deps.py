"""Dependency injection container cho các subcommand CLI — WP3.

Các subcommand `catalog validate` / `app inspect|plan-install|install` /
`evidence validate` cần implementation thật của WP2/WP4/WP6/WP9. WP3 KHÔNG
import cứng các package đó (tránh phụ thuộc vòng/giẫm chân khi các WP code
song song) — thay vào đó nhận object khớp ``Protocol`` tương ứng trong
``namios_core`` qua container này. Giai đoạn chưa nối (``None``), subcommand
trả lỗi ``E_INTERNAL`` rõ ràng ("chưa được nối") thay vì giả lập kết quả.
"""

from __future__ import annotations

from dataclasses import dataclass

from namios_core.catalog_types import CatalogStore
from namios_core.evidence_types import EvidenceValidator
from namios_core.manifest_types import ManifestValidator
from namios_core.planner_types import InstallPlanner
from namios_core.validation import SemanticContext


@dataclass(frozen=True)
class CliDependencies:
    """Container optional, mỗi field là một Protocol từ ``namios_core``.

    Mặc định mọi field là ``None`` (chưa wiring thật) — khung CLI vẫn chạy
    và trả envelope lỗi nhất quán thay vì crash hoặc giả đạt.
    """

    manifest_validator: ManifestValidator | None = None
    catalog_store: CatalogStore | None = None
    evidence_validator: EvidenceValidator | None = None
    install_planner: InstallPlanner | None = None
    semantic_context: SemanticContext | None = None


def empty_dependencies() -> CliDependencies:
    """Container rỗng — dùng khi chưa có implementation nào được nối."""

    return CliDependencies()
