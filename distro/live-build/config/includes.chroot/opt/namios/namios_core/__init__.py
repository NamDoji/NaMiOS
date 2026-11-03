"""``namios_core`` — hợp đồng dùng chung cho 10 gói dev M1 (WP1).

Chỉ kiểu (dataclass/enum/Protocol) + hằng số thuần Python. KHÔNG business
logic. Mọi WP khác import từ đây (chỉ đọc), KHÔNG import chéo implementation
của module khác. Xem ``docs/specs/M1-INTERFACES.md``.
"""

from __future__ import annotations

from namios_core.about import FOUNDERS, PRODUCT_NAME, AboutInfo, ComponentLicense
from namios_core.catalog_types import CatalogEntry, CatalogStore, RevocationRecord
from namios_core.compat import AppMode, CertificationTuple, CompatStatus
from namios_core.envelope import API_VERSION, Envelope, ErrorBody
from namios_core.errors import ERROR_CODE_EXIT_MAP, ErrorCode, exit_code_for
from namios_core.evidence_types import EvidenceReport, EvidenceTest, EvidenceValidator, GateResult
from namios_core.exitcodes import ExitCode
from namios_core.helper_types import (
    ApprovedPackagePlan,
    PackagePlanRequest,
    SystemCapabilities,
    SystemHelper,
    UpdateStatus,
)
from namios_core.manifest_types import (
    AppSection,
    CompatSection,
    FilesystemPermission,
    LicenseSection,
    Manifest,
    ManifestValidator,
    PermissionsSection,
    RuntimeSection,
    SchemaResult,
    SemanticResult,
    SourceSection,
)
from namios_core.paths import (
    APP_NAME,
    LOG_MAX_AGE_DAYS_DEFAULT,
    LOG_MAX_BYTES_DEFAULT,
    STATE_DB_FILENAME,
    cache_dir,
    config_dir,
    logs_dir,
    prefixes_dir,
    share_ro_dir,
    state_db_path,
    system_var_dir,
)
from namios_core.planner_types import ApplyCheck, InstallPlan, InstallPlanner
from namios_core.recipe_types import (
    CreateLauncher,
    CreatePrefix,
    DryRunResult,
    InstallDependency,
    RecipeEngine,
    RecipeStep,
    RunInstaller,
    SetRegistryValue,
    VerifyFile,
)
from namios_core.security_types import CompletedProc, Redactor, SafeExec, SafePath
from namios_core.txstate import (
    VALID_TRANSITIONS,
    JournalEntry,
    PrefixLock,
    StateStore,
    Transaction,
    TxState,
    validate_transition,
)
from namios_core.validation import SemanticContext, ValidationError

__all__ = [
    # envelope
    "API_VERSION",
    "Envelope",
    "ErrorBody",
    # exitcodes
    "ExitCode",
    # errors
    "ErrorCode",
    "ERROR_CODE_EXIT_MAP",
    "exit_code_for",
    # txstate
    "TxState",
    "VALID_TRANSITIONS",
    "validate_transition",
    "Transaction",
    "JournalEntry",
    "PrefixLock",
    "StateStore",
    # compat
    "CompatStatus",
    "AppMode",
    "CertificationTuple",
    # paths
    "APP_NAME",
    "STATE_DB_FILENAME",
    "LOG_MAX_BYTES_DEFAULT",
    "LOG_MAX_AGE_DAYS_DEFAULT",
    "config_dir",
    "prefixes_dir",
    "state_db_path",
    "cache_dir",
    "logs_dir",
    "share_ro_dir",
    "system_var_dir",
    # about
    "PRODUCT_NAME",
    "FOUNDERS",
    "ComponentLicense",
    "AboutInfo",
    # validation
    "ValidationError",
    "SemanticContext",
    # recipe_types
    "CreatePrefix",
    "InstallDependency",
    "SetRegistryValue",
    "RunInstaller",
    "VerifyFile",
    "CreateLauncher",
    "RecipeStep",
    "DryRunResult",
    "RecipeEngine",
    # manifest_types
    "AppSection",
    "LicenseSection",
    "SourceSection",
    "RuntimeSection",
    "FilesystemPermission",
    "PermissionsSection",
    "CompatSection",
    "Manifest",
    "SchemaResult",
    "SemanticResult",
    "ManifestValidator",
    # catalog_types
    "CatalogEntry",
    "RevocationRecord",
    "CatalogStore",
    # planner_types
    "InstallPlan",
    "ApplyCheck",
    "InstallPlanner",
    # helper_types
    "SystemCapabilities",
    "PackagePlanRequest",
    "ApprovedPackagePlan",
    "UpdateStatus",
    "SystemHelper",
    # evidence_types
    "EvidenceTest",
    "EvidenceReport",
    "GateResult",
    "EvidenceValidator",
    # security_types
    "CompletedProc",
    "SafePath",
    "SafeExec",
    "Redactor",
]
