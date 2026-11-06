"""ODC-001/020/033/022/047/048 — vòng đời/recheck + chứng nhận thiết bị + chỉ số.

Bám nghiệm thu: T13 (kernel update → thiết bị needs_retest, không hạ Office file),
ODC-047 (cộng đồng/AI không nâng cert), ODC-048 (catalog ≠ đã-hỗ-trợ).
"""

from __future__ import annotations

from namios_odc import (
    CertFunction,
    CertState,
    Component,
    DeviceCert,
    EvidenceKind,
    LifecycleRing,
    PackageRelease,
    WorkflowDomain,
    advance,
    build_coverage,
    can_publish,
    can_rollback,
    function_state,
    is_function_supported,
    needs_retest_domains,
    office_failure_blocks_os,
    publish,
    published_model_count,
    safe_fraction,
    user_weighted_coverage,
    with_needs_retest,
)

CF = CertFunction
CS = CertState
EK = EvidenceKind
C = Component
WD = WorkflowDomain


# --------------------------------------------------------------------------- #
# ODC-001/020/033 — lifecycle + recheck                                         #
# --------------------------------------------------------------------------- #


def test_office_change_only_affects_documents() -> None:
    # ODC-020: đổi bộ lọc Office → chỉ workflow tài liệu, KHÔNG rớt Wi‑Fi.
    assert needs_retest_domains(C.OFFICE) == frozenset({WD.DOCUMENT})
    assert WD.NETWORK not in needs_retest_domains(C.OFFICE)


def test_kernel_change_touches_devices_not_documents() -> None:
    # T13/ODC-033: kernel update → thiết bị/mạng needs_retest, KHÔNG hạ Office file.
    dom = needs_retest_domains(C.OS_KERNEL)
    assert WD.NETWORK in dom and WD.DEVICE in dom
    assert WD.DOCUMENT not in dom


def test_each_trigger_is_narrow() -> None:
    assert needs_retest_domains(C.PRINT_STACK) == frozenset({WD.PRINT, WD.SCAN})
    assert needs_retest_domains(C.NETWORK_STACK) == frozenset({WD.NETWORK})
    assert needs_retest_domains(C.AI_MODEL) == frozenset({WD.AI})  # AI không hạ fidelity/thiết bị


def test_rollback_and_os_independence() -> None:
    rel = PackageRelease("office", "25.2", C.OFFICE, LifecycleRing.PILOT, rollback_to="25.1")
    assert can_rollback(rel) is True
    assert can_rollback(PackageRelease("office", "25.2", C.OFFICE)) is False  # chưa có rollback
    assert office_failure_blocks_os() is False  # Office lỗi không chặn OS boot


# --------------------------------------------------------------------------- #
# ODC-022/047 — chứng nhận thiết bị per-function                                #
# --------------------------------------------------------------------------- #


def test_community_and_ai_never_promote() -> None:
    # ODC-047: "máy tôi in được" / AI đoán KHÔNG nâng, dù lặp nhiều lần.
    st: CertState | None = None
    for _ in range(50):
        st = advance(st, EK.COMMUNITY_REPORT)
        st = advance(st, EK.AI_GUESS)
    assert st is CertState.REPORTED  # không vượt reported


def test_promotion_requires_real_evidence_in_order() -> None:
    st = advance(None, EK.LAB_TEST)
    assert st is CertState.LAB_TESTED
    st = advance(st, EK.PILOT_SIGNOFF)
    assert st is CertState.PILOT_VERIFIED
    assert can_publish(st) is True
    assert publish(st) is CertState.PUBLISHED


def test_cannot_skip_stages() -> None:
    # pilot_signoff khi chưa lab → không lên pilot_verified.
    assert advance(CS.REPORTED, EK.PILOT_SIGNOFF) is CertState.REPORTED
    # publish khi chưa pilot_verified → không published.
    assert publish(CS.LAB_TESTED) is CertState.LAB_TESTED
    assert can_publish(CS.LAB_TESTED) is False


def test_supported_only_when_published() -> None:
    for state in CS:
        cert = DeviceCert("MFP-X", functions={CF.PRINT: state})
        assert is_function_supported(cert, CF.PRINT) is (state is CS.PUBLISHED), state
    # chức năng không khai → None, không hỗ trợ (không suy từ chức năng khác).
    cert = DeviceCert("MFP-X", functions={CF.PRINT: CS.PUBLISHED})
    assert function_state(cert, CF.SCAN) is None
    assert is_function_supported(cert, CF.SCAN) is False


def test_needs_retest_marks_only_listed_functions() -> None:
    cert = DeviceCert("MFP-X", functions={CF.PRINT: CS.PUBLISHED, CF.SCAN: CS.PUBLISHED})
    out = with_needs_retest(cert, [CF.PRINT])
    assert function_state(out, CF.PRINT) is CS.NEEDS_RETEST
    assert function_state(out, CF.SCAN) is CS.PUBLISHED  # không đụng chức năng khác
    assert function_state(cert, CF.PRINT) is CS.PUBLISHED  # bản gốc bất biến


# --------------------------------------------------------------------------- #
# ODC-048 — chỉ số trung thực                                                   #
# --------------------------------------------------------------------------- #


def test_safe_fraction_no_overclaim() -> None:
    assert safe_fraction(0, 0) == 0.0  # mẫu 0 → 0, không phải 100%
    assert safe_fraction(5, 0) == 0.0
    assert safe_fraction(10, 5) == 1.0  # không bịa >100%
    assert safe_fraction(2, 4) == 0.5
    assert user_weighted_coverage(0, 0) == 0.0


def test_catalog_is_not_supported() -> None:
    # ODC-048: 100 model catalog + 2 published → đã-hỗ-trợ = 2, KHÔNG phải 100.
    certs = [
        DeviceCert("A", functions={CF.PRINT: CS.PUBLISHED}),
        DeviceCert("B", functions={CF.PRINT: CS.PUBLISHED, CF.SCAN: CS.LAB_TESTED}),
        DeviceCert("C", functions={CF.PRINT: CS.LAB_TESTED}),  # chưa published
        DeviceCert("D", functions={CF.PRINT: CS.REPORTED}),
    ]
    assert published_model_count(certs) == 2
    cov = build_coverage(
        pilot_users_with_required=3,
        pilot_users_total=5,
        workflows_verified=4,
        workflows_required=10,
        fidelity_fixtures_pass=2,
        fidelity_fixtures_measured=3,
        workflows_need_windows=2,
        models_surveyed=100,
        certs=certs,
    )
    assert cov.models_surveyed == 100
    assert cov.models_published == 2  # KHÔNG lấy catalog làm đã-hỗ-trợ
    assert cov.user_weighted_device_coverage == 0.6
    assert cov.workflow_coverage == 0.4
