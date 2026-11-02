"""Xây payload ``data`` cho lệnh ``namios doctor --json`` — WP3.

Chỉ chuyển ``SystemCapabilitiesReport`` (dataclass) thành ``dict`` JSON
hợp lệ để nhúng vào ``Envelope.data``. KHÔNG business logic cài đặt.
"""

from __future__ import annotations

from typing import Any

from namios_doctor.capabilities import SystemCapabilitiesReport, collect_capabilities


def _report_to_dict(report: SystemCapabilitiesReport) -> dict[str, Any]:
    return {
        "host": {
            "os_pretty_name": report.host.os_pretty_name,
            "kernel_release": report.host.kernel_release,
            "architecture": report.host.architecture,
            "python_version": report.host.python_version,
        },
        "session": {
            "session_type": report.session.session_type,
            "desktop_environment": report.session.desktop_environment,
        },
        "virtualization": {
            "has_kvm": report.virtualization.has_kvm,
            "kvm_device_path": report.virtualization.kvm_device_path,
        },
        "tooling": {
            "present": list(report.tooling_present),
            "absent": list(report.tooling_absent),
        },
    }


def build_doctor_data(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Trả payload ``data`` thật cho envelope ``namios doctor --json``."""

    report = collect_capabilities(env=env)
    return _report_to_dict(report)
