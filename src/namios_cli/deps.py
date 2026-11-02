"""Dependency injection container cho các subcommand CLI — WP3, nối WIRING.

Các subcommand `catalog validate` / `app inspect|plan-install|install` /
`evidence validate` cần implementation thật của WP2/WP4/WP6/WP9. Trong giai
đoạn 10 WP code song song, ``namios_cli`` KHÔNG import cứng các package đó
(tránh phụ thuộc vòng/giẫm chân) — nhận object khớp ``Protocol`` tương ứng
trong ``namios_core`` qua container này; field ``None`` ⇒ subcommand trả lỗi
``E_INTERNAL`` rõ ràng ("chưa được nối") thay vì giả lập kết quả.

Sau khi các WP đã merge, vai trò WIRING TÍCH HỢP (owns ``namios_cli/``,
``namios_doctor/``, ``tests/integration/``) nối container này với implementation
THẬT qua :func:`default_dependencies` — dùng khi ``main()`` không được truyền
``deps`` tường minh (xem ``namios_cli.main``). Dataclass ``CliDependencies``
TỰ THÂN vẫn giữ mọi field mặc định ``None`` (không đổi hợp đồng cũ) để test
đơn vị/QA hiện có (``CliDependencies()`` rỗng tường minh = "chưa wiring")
tiếp tục đúng như trước.
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
    và trả envelope lỗi nhất quán thay vì crash hoặc giả đạt. Dùng
    :func:`default_dependencies` để lấy một container đã nối implementation
    thật (WIRING tích hợp, sau khi các WP merge).
    """

    manifest_validator: ManifestValidator | None = None
    catalog_store: CatalogStore | None = None
    evidence_validator: EvidenceValidator | None = None
    install_planner: InstallPlanner | None = None
    semantic_context: SemanticContext | None = None


def empty_dependencies() -> CliDependencies:
    """Container rỗng — dùng khi chưa có implementation nào được nối."""

    return CliDependencies()


def default_dependencies() -> CliDependencies:
    """Container đã nối implementation THẬT của từng WP (WIRING tích hợp).

    Import implementation cụ thể của các WP khác CHỈ xảy ra ở đây (KHÔNG ở
    ``namios_core``/Protocol) — đây là lớp tích hợp cuối, sau khi mọi WP đã
    merge, KHÔNG phải code chạy song song giữa các WP nữa:

    - ``manifest_validator`` → ``namios_manifest.ManifestValidatorImpl`` (WP2).
    - ``catalog_store`` → ``namios_catalog.InMemoryCatalogStore`` (WP4, rỗng
      lúc khởi tạo — nạp entry là trách nhiệm của caller/CLI command khác).
    - ``evidence_validator`` → ``namios_evidence.EvidenceValidatorImpl`` (WP9).
    - ``install_planner`` → ``namios_planner.DefaultInstallPlanner`` (WP6)
      tiêm ``namios_recipe.RecipeEngineImpl`` (WP10) thật — KHÔNG fake.
    - ``semantic_context`` → ``None``: mỗi handler tự fallback về context
      rỗng (``approved_dependency_ids/pinned_runner_hashes/revoked_ids`` đều
      rỗng — DESIGN an toàn-mặc-định: chưa duyệt gì thì không gì được coi
      là đã duyệt) qua ``namios_cli.main._empty_semantic_context``.

    ``app install`` (M2, cài thật) vẫn luôn ``blocked`` tại host này dù
    container có đủ wiring — đó là gate M1 cố ý trong ``_handle_app_install``,
    không phụ thuộc container.
    """

    from namios_catalog import InMemoryCatalogStore
    from namios_evidence import EvidenceValidatorImpl
    from namios_manifest import ManifestValidatorImpl
    from namios_planner import DefaultInstallPlanner
    from namios_recipe import RecipeEngineImpl

    return CliDependencies(
        manifest_validator=ManifestValidatorImpl(),
        catalog_store=InMemoryCatalogStore(),
        evidence_validator=EvidenceValidatorImpl(),
        install_planner=DefaultInstallPlanner(RecipeEngineImpl()),
        semantic_context=None,
    )
