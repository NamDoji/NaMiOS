"""N10-007/012/019/026/043 — hợp đồng dữ liệu + validator + vòng đời recipe.

Hai bất biến cốt lõi: (a) usage 30-ngày chỉ hợp lệ khi opt-in (N10-007); (b)
recipe đổi hash/version tự ``needs_retest``, không kế thừa nhãn xanh (N10-026).
"""

from __future__ import annotations

from namios_mig import (
    AppManifest,
    CertState,
    CompatibilityRecipe,
    CompatRoute,
    DeviceManifest,
    EvidenceKind,
    EvidenceRecord,
    MigrationInventory,
    PeripheralKind,
    PrintStage,
    WorkflowTest,
    WorkflowTestStatus,
    promote_recipe,
    publish_recipe,
    recipe_needs_retest,
    validate_app_manifest,
    validate_device_manifest,
    validate_evidence_record,
    validate_inventory,
    validate_recipe,
    validate_workflow_test,
)

# --------------------------------------------------------------------------- #
# AppManifest / DeviceManifest                                                #
# --------------------------------------------------------------------------- #


def test_app_manifest_requires_id() -> None:
    assert validate_app_manifest(AppManifest(app_id="")) != []
    assert validate_app_manifest(AppManifest(app_id="misa.sme")) == []


def test_usage_30_days_requires_opt_in() -> None:
    # N10-007: "app đang dùng 30 ngày (chỉ khi opt-in)" — không opt-in mà vẫn
    # khai last_used_days_ago là một lỗi cấu trúc, KHÔNG được lặng lẽ chấp nhận.
    no_opt_in = AppManifest(app_id="a", usage_opt_in=False, last_used_days_ago=3)
    errors = validate_app_manifest(no_opt_in)
    assert any(e.code == "E_MIG_USAGE_NO_OPTIN" for e in errors)

    opted_in = AppManifest(app_id="a", usage_opt_in=True, last_used_days_ago=3)
    assert validate_app_manifest(opted_in) == []

    no_usage_claim = AppManifest(app_id="a", usage_opt_in=False, last_used_days_ago=None)
    assert validate_app_manifest(no_usage_claim) == []


def test_device_manifest_requires_id() -> None:
    assert validate_device_manifest(DeviceManifest(device_id="")) != []
    assert (
        validate_device_manifest(DeviceManifest(device_id="dev1", kind=PeripheralKind.PRINTER))
        == []
    )


# --------------------------------------------------------------------------- #
# CompatibilityRecipe — N10-012/019/026                                       #
# --------------------------------------------------------------------------- #


def test_recipe_requires_app_and_version() -> None:
    errors = validate_recipe(CompatibilityRecipe(app_id="", version=""))
    codes = {e.code for e in errors}
    assert "E_MIG_RECIPE_NO_APP" in codes
    assert "E_MIG_RECIPE_NO_VERSION" in codes


def test_wine_route_requires_pinned_runner() -> None:
    # N10-019: "Wine runner được pin" — route=wine mà không pin runner là lỗi.
    no_runner = CompatibilityRecipe(app_id="a", version="1.0", route=CompatRoute.WINE, runner_id="")
    assert any(e.code == "E_MIG_RECIPE_NO_RUNNER" for e in validate_recipe(no_runner))

    pinned = CompatibilityRecipe(
        app_id="a", version="1.0", route=CompatRoute.WINE, runner_id="wine-9.0-staging"
    )
    assert validate_recipe(pinned) == []


def test_publish_requires_test_cases_and_owner() -> None:
    bare = CompatibilityRecipe(
        app_id="a", version="1.0", cert_state=CertState.PUBLISHED, test_case_ids=(), owner=""
    )
    codes = {e.code for e in validate_recipe(bare)}
    assert "E_MIG_RECIPE_PUBLISH_NO_TEST" in codes
    assert "E_MIG_RECIPE_PUBLISH_NO_OWNER" in codes

    complete = CompatibilityRecipe(
        app_id="a",
        version="1.0",
        cert_state=CertState.PUBLISHED,
        test_case_ids=("t1",),
        owner="qa-team",
    )
    assert validate_recipe(complete) == []


def test_recipe_needs_retest_on_hash_or_version_change() -> None:
    # N10-026: đổi hash/version → tự needs_retest, KHÔNG kế thừa nhãn xanh.
    published = CompatibilityRecipe(
        app_id="misa.sme",
        version="2024.1",
        installer_hash="sha256:aaa",
        cert_state=CertState.PUBLISHED,
        test_case_ids=("t1",),
        owner="qa",
    )

    unchanged = recipe_needs_retest(
        published, current_installer_hash="sha256:aaa", current_version="2024.1"
    )
    assert unchanged.cert_state is CertState.PUBLISHED  # không đổi gì thì giữ nguyên nhãn

    hash_changed = recipe_needs_retest(
        published, current_installer_hash="sha256:bbb", current_version="2024.1"
    )
    assert hash_changed.cert_state is CertState.NEEDS_RETEST

    version_changed = recipe_needs_retest(
        published, current_installer_hash="sha256:aaa", current_version="2024.2"
    )
    assert version_changed.cert_state is CertState.NEEDS_RETEST


def test_promote_recipe_reuses_odc_cert_state_machine() -> None:
    # TÁI DÙNG namios_odc.device_cert: cộng đồng/AI KHÔNG BAO GIỜ nâng; lab→pilot
    # tuần tự, không nhảy cóc.
    reported = CompatibilityRecipe(app_id="a", version="1.0")
    still_reported = promote_recipe(reported, EvidenceKind.COMMUNITY_REPORT)
    assert still_reported.cert_state is CertState.REPORTED

    lab_tested = promote_recipe(reported, EvidenceKind.LAB_TEST)
    assert lab_tested.cert_state is CertState.LAB_TESTED

    # Chưa qua lab mà đưa pilot_signoff thẳng → không nhảy cóc.
    no_skip = promote_recipe(reported, EvidenceKind.PILOT_SIGNOFF)
    assert no_skip.cert_state is CertState.REPORTED

    pilot_verified = promote_recipe(lab_tested, EvidenceKind.PILOT_SIGNOFF)
    assert pilot_verified.cert_state is CertState.PILOT_VERIFIED


def test_publish_recipe_fail_closed_without_tests_or_owner() -> None:
    pilot_no_tests = CompatibilityRecipe(
        app_id="a", version="1.0", cert_state=CertState.PILOT_VERIFIED, test_case_ids=(), owner=""
    )
    # can_publish() cho True nhưng validate_recipe(published) fail → không công bố.
    assert publish_recipe(pilot_no_tests).cert_state is CertState.PILOT_VERIFIED

    pilot_ready = CompatibilityRecipe(
        app_id="a",
        version="1.0",
        cert_state=CertState.PILOT_VERIFIED,
        test_case_ids=("t1",),
        owner="qa",
    )
    assert publish_recipe(pilot_ready).cert_state is CertState.PUBLISHED

    not_yet_pilot = CompatibilityRecipe(app_id="a", version="1.0", cert_state=CertState.LAB_TESTED)
    assert publish_recipe(not_yet_pilot).cert_state is CertState.LAB_TESTED


# --------------------------------------------------------------------------- #
# WorkflowTest / EvidenceRecord — N10-031/043                                 #
# --------------------------------------------------------------------------- #


def test_workflow_test_passed_requires_evidence_and_tested_at() -> None:
    bare_pass = WorkflowTest(
        workflow_id="vn.invoice.sign.test", app_id="a", status=WorkflowTestStatus.PASSED
    )
    codes = {e.code for e in validate_workflow_test(bare_pass)}
    assert "E_MIG_WORKFLOW_NO_EVIDENCE" in codes
    assert "E_MIG_WORKFLOW_NO_TESTED_AT" in codes

    complete_pass = WorkflowTest(
        workflow_id="vn.invoice.sign.test",
        app_id="a",
        status=WorkflowTestStatus.PASSED,
        evidence_ids=("ev1",),
        tested_at="2026-11-07",
    )
    assert validate_workflow_test(complete_pass) == []

    not_tested = WorkflowTest(workflow_id="w", app_id="a")
    assert validate_workflow_test(not_tested) == []


def test_evidence_record_must_carry_a_signal() -> None:
    empty = EvidenceRecord(evidence_id="ev1", workflow_id="w1")
    assert any(e.code == "E_MIG_EVIDENCE_EMPTY" for e in validate_evidence_record(empty))

    with_signal = EvidenceRecord(
        evidence_id="ev1", workflow_id="w1", print_stage=PrintStage.USER_CONFIRMED
    )
    assert validate_evidence_record(with_signal) == []

    no_id = EvidenceRecord(evidence_id="", workflow_id="")
    assert validate_evidence_record(no_id) != []


# --------------------------------------------------------------------------- #
# MigrationInventory                                                           #
# --------------------------------------------------------------------------- #


def test_inventory_requires_machine_id_and_validates_nested_apps() -> None:
    bad = MigrationInventory(machine_id="", apps=(AppManifest(app_id=""),))
    codes = {e.code for e in validate_inventory(bad)}
    assert "E_MIG_INVENTORY_NO_MACHINE" in codes
    assert "E_MIG_APP_NO_ID" in codes

    good = MigrationInventory(machine_id="m1", apps=(AppManifest(app_id="a"),))
    assert validate_inventory(good) == []
