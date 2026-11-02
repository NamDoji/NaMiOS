"""WP2 — Manifest schema loader + semantic validator 2 tầng.

Xem ``docs/specs/M1-INTERFACES.md`` §7.1 và ``docs/specs/M1-WORK-PACKAGES.md``
WP2. Hiện thực ``namios_core.manifest_types.ManifestValidator``.
"""

from __future__ import annotations

from namios_manifest._errors import ManifestLoadError
from namios_manifest._safe_io import PathUnsafeError
from namios_manifest.validator import ManifestValidatorImpl

__all__ = ["ManifestValidatorImpl", "ManifestLoadError", "PathUnsafeError"]
