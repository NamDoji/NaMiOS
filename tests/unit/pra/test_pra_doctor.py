"""PRA-028..031 — Doctor theo vùng: chẩn đoán có cấu trúc, trung thực, phân vai.

Bám bài nghiệm thu §9: P02 (in=đạt/scan=blocked/copy=chưa test), P03 (kẹt giữ
trang), P05 (5 lỗi mạng khác nhau ≠ "khởi động router"), P07 (.xlsm macro không
ra web), P08 (WPF không native), P09 (DB mất → partial), P10 (token OK + cổng
khóa-Windows → blocker), P31 (thử N lần → dừng, không lặp vô hạn).
"""

from __future__ import annotations

from namios_pra import (
    DeviceCapability,
    DeviceFault,
    DeviceFunction,
    DeviceFunctionStatus,
    DeviceSignals,
    Hypothesis,
    NetworkFault,
    NetworkSignals,
    OfficeNeed,
    OfficeRoute,
    ResolverRole,
    app_workflow_status,
    bounded_hypotheses,
    diagnose_device,
    diagnose_network,
    next_after_attempts,
    office_preflight,
)
from namios_smartai._types import ErrorCategory

F = DeviceFunction
S = DeviceFunctionStatus
N = OfficeNeed


# --------------------------------------------------------------------------- #
# PRA-028 Device Doctor                                                         #
# --------------------------------------------------------------------------- #

_DEVICE_FIXTURES = {
    "offline": DeviceSignals(requested=F.PRINT, reachable=False),
    "out_of_paper": DeviceSignals(requested=F.PRINT, paper_ok=False),
    "job_jammed": DeviceSignals(requested=F.PRINT, media_jam=True),
    "mdns_blocked": DeviceSignals(requested=F.PRINT, mdns_visible=False),
    "scan_backend_missing": DeviceSignals(requested=F.SCAN, scan_backend_present=False),
}


def test_device_five_fixtures_five_distinct_faults() -> None:
    # Nghiệm thu PRA-028: 5 fixture → 5 kết luận KHÁC nhau (+ việc-cần-làm khác).
    faults = {}
    next_steps = set()
    for name, sig in _DEVICE_FIXTURES.items():
        d = diagnose_device(sig)
        assert d.fault == name, (name, d.fault)
        assert d.domain == "device"
        assert d.cause_vi and d.next_step_vi
        faults[name] = d.fault
        next_steps.add(d.next_step_vi)
    assert len(set(faults.values())) == 5
    assert len(next_steps) == 5  # mỗi lỗi một việc-cần-làm riêng


def test_device_copy_absent_is_not_broken() -> None:
    # P02: máy in+scan được nhưng copy chưa kiểm → function_absent, KHÔNG "hỏng".
    cap = DeviceCapability(
        device_id="mfp1",
        model="MFP-X",
        functions={F.PRINT: S.WORKS, F.SCAN: S.WORKS},  # copy không khai
    )
    d = diagnose_device(DeviceSignals(requested=F.COPY), capability=cap)
    assert d.fault == DeviceFault.FUNCTION_ABSENT.value
    assert d.is_blocker is False
    assert d.resolver is ResolverRole.USER


def test_device_copy_works_is_healthy() -> None:
    cap = DeviceCapability(device_id="d", functions={F.COPY: S.WORKS})
    d = diagnose_device(DeviceSignals(requested=F.COPY), capability=cap)
    assert d.fault == DeviceFault.HEALTHY.value


def test_device_resolver_roles() -> None:
    # mDNS/scan-backend cần IT/vendor (blocker site); giấy/kẹt là user tự xử.
    assert diagnose_device(_DEVICE_FIXTURES["mdns_blocked"]).resolver is ResolverRole.IT
    assert diagnose_device(_DEVICE_FIXTURES["scan_backend_missing"]).resolver is ResolverRole.VENDOR
    assert diagnose_device(_DEVICE_FIXTURES["mdns_blocked"]).is_blocker is True
    assert diagnose_device(_DEVICE_FIXTURES["out_of_paper"]).resolver is ResolverRole.USER


def test_device_offline_takes_priority() -> None:
    # Máy không phản hồi → OFFLINE bất kể cờ khác (chẩn sâu hơn vô nghĩa).
    sig = DeviceSignals(requested=F.PRINT, reachable=False, paper_ok=False, media_jam=True)
    assert diagnose_device(sig).fault == DeviceFault.OFFLINE.value


def test_device_jam_keeps_pages_message() -> None:
    # P03: kẹt trang → thông điệp nêu rõ trang đã xử lý được GIỮ.
    d = diagnose_device(_DEVICE_FIXTURES["job_jammed"])
    assert d.fault == DeviceFault.JOB_JAMMED.value
    assert "giữ" in d.next_step_vi


# --------------------------------------------------------------------------- #
# PRA-029 Network Doctor                                                        #
# --------------------------------------------------------------------------- #

_NET_FIXTURES = {
    "ssid_not_found": NetworkSignals(ssid_visible=False),
    "wrong_password": NetworkSignals(auth_ok=False),
    "no_ip": NetworkSignals(has_ip=False),
    "captive_portal": NetworkSignals(captive_portal=True),
    "dns_error": NetworkSignals(dns_ok=False),
    "proxy_vpn": NetworkSignals(proxy_required=True, proxy_ok=False),
    "no_internet": NetworkSignals(internet_ok=False),
    "printer_off_network": NetworkSignals(checking_printer=True, printer_same_subnet=False),
}


def test_network_distinct_faults_and_steps() -> None:
    # Nghiệm thu PRA-029/P05: các lỗi khác nhau KHÔNG đều trả một việc-cần-làm.
    faults = set()
    steps = set()
    for name, sig in _NET_FIXTURES.items():
        d = diagnose_network(sig)
        assert d.fault == name, (name, d.fault)
        assert d.domain == "network"
        faults.add(d.fault)
        steps.add(d.next_step_vi)
    assert len(faults) == len(_NET_FIXTURES)
    assert len(steps) == len(_NET_FIXTURES)  # mỗi lỗi một cách xử lý riêng


def test_network_no_internet_not_just_restart_router() -> None:
    # P05 nhấn mạnh: "mất Internet" không được rút gọn thành "khởi động router".
    d = diagnose_network(_NET_FIXTURES["no_internet"])
    assert d.fault == NetworkFault.NO_INTERNET.value
    assert "router" not in d.next_step_vi.lower() or "không chỉ" in d.next_step_vi


def test_network_healthy_when_all_ok() -> None:
    assert diagnose_network(NetworkSignals()).fault == NetworkFault.HEALTHY.value


def test_network_printer_fault_only_when_checking_printer() -> None:
    # Máy in khác mạng chỉ là lỗi khi đang chẩn mạng cho máy in.
    assert diagnose_network(NetworkSignals(printer_same_subnet=False)).fault == (
        NetworkFault.HEALTHY.value
    )


# --------------------------------------------------------------------------- #
# PRA-030 Office Doctor                                                         #
# --------------------------------------------------------------------------- #


def test_office_macro_never_web_and_no_autoupload() -> None:
    # P07: .xlsm cần macro → route Windows VM, không bao giờ web; không tự upload.
    pf = office_preflight(
        [N.EDIT, N.MACRO], has_native_support=True, web_available=True, file_has_sensitive_data=True
    )
    assert pf.route is OfficeRoute.WINDOWS_VM
    assert pf.route is not OfficeRoute.MS365_WEB
    assert pf.auto_upload is False
    assert any("web" in w.lower() for w in pf.warnings_vi)


def test_office_sensitive_web_needs_consent_no_autoupload() -> None:
    # File nhạy cảm + tuyến web khả dụng → cần xác nhận rõ, KHÔNG tự upload.
    pf = office_preflight(
        [N.EDIT], has_native_support=False, web_available=True, file_has_sensitive_data=True
    )
    assert pf.route is OfficeRoute.MS365_WEB
    assert pf.needs_explicit_consent is True
    assert pf.auto_upload is False


def test_office_plain_read_native_no_consent() -> None:
    pf = office_preflight([N.READ], has_native_support=True)
    assert pf.route is OfficeRoute.NATIVE_LINUX
    assert pf.needs_explicit_consent is False
    assert pf.auto_upload is False


# --------------------------------------------------------------------------- #
# PRA-031 Windows App Doctor                                                    #
# --------------------------------------------------------------------------- #


def test_app_db_down_is_partial_not_usable() -> None:
    # P09: GUI mở nhưng DB mất → partial_workflow, chặn, không "dùng được".
    d = app_workflow_status(launched=True, triage_category=ErrorCategory.DB_UNREACHABLE)
    assert d.fault == "partial_workflow"
    assert d.is_blocker is True


def test_app_portal_plugin_is_blocker() -> None:
    # P10: token nhận được nhưng cổng cần plugin Windows → vẫn BLOCKED (vendor).
    d = app_workflow_status(launched=True, triage_category=ErrorCategory.PORTAL_PLUGIN)
    assert d.fault == "portal_blocker"
    assert d.is_blocker is True
    assert d.resolver is ResolverRole.VENDOR


def test_app_bounded_hypotheses_requires_rollback_and_caps() -> None:
    cands = [
        Hypothesis(summary_vi="thử A", test_vi="chạy test A", rollback_vi="gỡ A"),
        Hypothesis(summary_vi="thử B", test_vi="chạy test B", rollback_vi=""),  # thiếu rollback
        Hypothesis(summary_vi="thử C", test_vi="chạy test C", rollback_vi="gỡ C"),
        Hypothesis(summary_vi="thử D", test_vi="chạy test D", rollback_vi="gỡ D"),
    ]
    out = bounded_hypotheses(cands, max_n=2)
    assert len(out) == 2  # cap
    assert all(h.rollback_vi.strip() for h in out)  # thiếu rollback bị loại
    assert bounded_hypotheses(cands, max_n=0) == ()


def test_app_terminal_after_max_attempts_no_infinite_loop() -> None:
    # P31: thử tối đa N lần đều fail → DỪNG (terminal), không lặp vô hạn.
    assert next_after_attempts(failed_count=0, max_attempts=3) is None
    assert next_after_attempts(failed_count=2, max_attempts=3) is None
    d = next_after_attempts(failed_count=3, max_attempts=3)
    assert d is not None and d.is_terminal is True and d.is_blocker is True
    # max_attempts<=0 cũng terminal (không cho vòng nào).
    d0 = next_after_attempts(failed_count=0, max_attempts=0)
    assert d0 is not None and d0.is_terminal is True
