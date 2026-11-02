"""Test ``namios_doctor`` — capability report host THẬT, không bịa, không
secret. Phản ánh FACT inventory M0 (host hiện tại KHÔNG có kvm/wine/qemu/
live-build)."""

from __future__ import annotations

from namios_doctor.capabilities import TOOLING_PROBE_NAMES, collect_capabilities
from namios_doctor.doctor import build_doctor_data


def test_collect_capabilities_reports_real_host_facts() -> None:
    report = collect_capabilities()
    # FACT docs/_m0_inventory_raw.md: /dev/kvm ABSENT, không cờ vmx/svm.
    assert report.virtualization.has_kvm is False
    assert report.virtualization.kvm_device_path == "/dev/kvm"
    # FACT: git + python có; wine/qemu/live-build KHÔNG có trên host này.
    assert "git" in report.tooling_present
    for missing in ("wine", "winetricks", "qemu-system-x86_64", "lb", "debootstrap", "xorriso"):
        assert missing in report.tooling_absent
    # kernel/arch/python_version phải khớp platform thật, không rỗng
    assert report.host.kernel_release
    assert report.host.architecture
    assert report.host.python_version.startswith("3.")


def test_tooling_present_and_absent_partition_all_probe_names() -> None:
    report = collect_capabilities()
    all_reported = set(report.tooling_present) | set(report.tooling_absent)
    assert all_reported == set(TOOLING_PROBE_NAMES)
    # không trùng lặp giữa 2 tập
    assert set(report.tooling_present).isdisjoint(report.tooling_absent)


def test_collect_capabilities_reads_injected_session_env_without_mutating_process() -> None:
    import os

    before = dict(os.environ)
    report = collect_capabilities(env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "KDE"})
    assert report.session.session_type == "wayland"
    assert report.session.desktop_environment == "KDE"
    # môi trường tiến trình thật KHÔNG bị thay đổi bởi lệnh doctor
    assert dict(os.environ) == before


def test_collect_capabilities_session_falls_back_to_none_when_absent() -> None:
    report = collect_capabilities(env={})
    assert report.session.session_type is None
    assert report.session.desktop_environment is None


def test_build_doctor_data_is_json_serializable_shape() -> None:
    data = build_doctor_data()
    assert set(data.keys()) == {"host", "session", "virtualization", "tooling"}
    assert set(data["tooling"].keys()) == {"present", "absent"}
    assert isinstance(data["virtualization"]["has_kvm"], bool)


def test_build_doctor_data_never_contains_secret_like_keys() -> None:
    import json

    data = build_doctor_data()
    blob = json.dumps(data).lower()
    for forbidden in ("password", "token", "secret", "api_key", "apikey", "credential"):
        assert forbidden not in blob
