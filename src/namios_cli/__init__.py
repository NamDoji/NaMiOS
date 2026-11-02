"""``namios_cli`` — CLI framework (WP3): parser argv, envelope writer,
exit-code mapper, dispatch subcommand. Xem M1-INTERFACES.md §1, §2, §8.

Business logic thật của từng subcommand (manifest/catalog/evidence/planner)
thuộc các WP khác; module này chỉ hiện thực khung + wiring qua
``CliDependencies`` (dependency injection theo Protocol trong ``namios_core``,
KHÔNG import implementation cứng của WP khác).
"""

from __future__ import annotations

from namios_cli.deps import CliDependencies
from namios_cli.envelope_io import emit_json, envelope_exit_code, new_operation_id
from namios_cli.errors import error_envelope, ok_envelope
from namios_cli.main import main

__all__ = [
    "CliDependencies",
    "emit_json",
    "envelope_exit_code",
    "new_operation_id",
    "error_envelope",
    "ok_envelope",
    "main",
]
