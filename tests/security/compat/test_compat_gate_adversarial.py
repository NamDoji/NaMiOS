"""ADVERSARIAL QA -- gate trung thuc cua Trung tam tuong thich (COMP-025/048/049).

Vai tro: KHONG phai dev tu xac nhan thiet ke -- muc tieu la cong pha loi hua
"metadata/claims mot minh KHONG BAO GIO tao ra ket qua usable/workflow_verified
khi khong co bang chung thuc; doi app version hoac token ky lam mat hieu luc
chung nhan; revoked/expired/chua duyet nghiep vu khong bao gio hien usable".

10 nhom tan cong duoc giao, moi nhom >= 1 test:
  1. Fake verified qua metadata (schema.py)
  2. Unicode/type confusion tren enum + schema_version (schema.py)
  3. revoked=true nhung route/status van usable (schema.py + evidence.py)
  4. Evidence-gap elevation (derive_published_status qua evaluate_route_status)
  5. Business bypass (evaluate_route_status)
  6. Expiry bypass (evaluate_route_status)
  7. Resolver stale-cert bypass theo app_version/token (resolver.py)
  8. Resolver khong bao gio de xuat mode never-usable (resolver.py)
  9. Evidence provenance holes (evidence.validate_evidence)
  10. evidence_to_steps laundering (evidence.evidence_to_steps)

Quy uoc: MOI test ASSERT gate GIU VUNG (dung theo loi hua). Neu mot test lo
ra lo hong THAT (assert fail), test duoc GIU LAI lam BANG CHUNG bang
``pytest.mark.xfail(strict=True, reason="COMPAT-ADV-NNN: ...")`` -- khong
sua code src/ de che giau (dung quy uoc da cong bo o
``tests/security/sweep/__init__.py``). ``strict=True`` nghia la neu nguoi
tich hop va loi hong, test se chuyen thanh XPASS va TU DONG bi bao FAIL --
bat buoc phai xoa marker do khi do (khong lang le "sua la xong").

CHI file nay duoc viet/sua. KHONG dung src/ hay test khac.
"""

from __future__ import annotations

from typing import Any

import pytest

from namios_compat._types import (
    AppRef,
    BusinessStatus,
    Certification,
    CompatEvidence,
    EndToEndStatus,
    EvidenceEnvironment,
    ResolveInput,
    Route,
    Sector,
    TechnicalStatus,
    VendorSupport,
    WorkflowEntry,
)
from namios_compat.evidence import evaluate_route_status, evidence_to_steps, validate_evidence
from namios_compat.resolver import resolve_routes
from namios_compat.schema import validate_workflow_entry
from namios_eco.status import PublishedStatus, WindowsMode
from namios_eco.workflow import (
    WORKFLOW_STEP_ORDER,
    StepOutcome,
    WorkflowStep,
    WorkflowStepName,
)

_REQUIRED_STEP_VALUES = [s.value for s in WORKFLOW_STEP_ORDER]


# ---------------------------------------------------------------------------
# Helper builders -- KHONG tai dung helper cua dev/QA khac (quy uoc sweep):
# tu dung fixture rieng de khong vo tinh ke thua gia dinh sai cua ho.
# ---------------------------------------------------------------------------


def _cert_raw(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "tested_at": None,
        "evidence_ids": [],
        "technical_status": "not_inventoried",
        "business_status": "unreviewed",
        "end_to_end_status": "untested",
        "vendor_support": "unknown",
        "revoked": False,
    }
    base.update(overrides)
    return base


def _entry_raw(
    *,
    cert: dict[str, Any] | None = None,
    routes: list[dict[str, Any]] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "schema_version": "1.0",
        "workflow_id": "wf.adversarial.test",
        "sector": "tax",
        "provider_id": "prov.x",
        "region_scope": "VN",
        "app": {"id": "app.x", "version": "1.0.0"},
        "required_steps": list(_REQUIRED_STEP_VALUES),
        "requires": [],
        "routes": routes or [],
        "certification": cert if cert is not None else _cert_raw(),
        "last_updated": "2026-01-01",
    }
    raw.update(overrides)
    return raw


def _full_pass_steps(
    *, verify_ref: str | None = "ev-verify", submit_ref: str | None = "ev-submit"
) -> tuple[WorkflowStep, ...]:
    """7 nac deu PASS, evidence_ref chi gan cho submit/verify (nhu that)."""

    steps: list[WorkflowStep] = []
    for name in WORKFLOW_STEP_ORDER:
        if name == WorkflowStepName.SUBMIT_OR_EXPORT:
            steps.append(WorkflowStep(name=name, outcome=StepOutcome.PASS, evidence_ref=submit_ref))
        elif name == WorkflowStepName.VERIFY_RESULT:
            steps.append(WorkflowStep(name=name, outcome=StepOutcome.PASS, evidence_ref=verify_ref))
        else:
            steps.append(WorkflowStep(name=name, outcome=StepOutcome.PASS))
    return tuple(steps)


def _resolver_entry(
    *,
    app_version: str = "2.1.0",
    requires: tuple[str, ...] = (),
    device_models: tuple[str, ...] = (),
    mode: WindowsMode = WindowsMode.NATIVE_LINUX,
    route_status: str = PublishedStatus.WORKFLOW_VERIFIED.value,
) -> WorkflowEntry:
    return WorkflowEntry(
        schema_version="1.0",
        workflow_id="wf.resolver.test",
        sector=Sector.TAX,
        provider_id="prov.x",
        region_scope="VN",
        app=AppRef(id="app.x", version=app_version),
        required_steps=tuple(WORKFLOW_STEP_ORDER),
        requires=requires,
        routes=(Route(mode=mode, status=route_status),),
        certification=Certification(
            tested_at="2026-01-01",
            evidence_ids=("ev-1",),
            technical_status=TechnicalStatus.VERIFIED,
            business_status=BusinessStatus.APPROVED,
            end_to_end_status=EndToEndStatus.PASS,
            vendor_support=VendorSupport.UNKNOWN,
            device_models=device_models,
        ),
        last_updated="2026-01-01",
    )


def _resolve_input(**overrides: Any) -> ResolveInput:
    base: dict[str, Any] = dict(
        workflow_id="wf.resolver.test",
        app_id="app.x",
        app_version="2.1.0",
        license_ok=True,
        org_policy_allows_remote=True,
    )
    base.update(overrides)
    return ResolveInput(**base)


def _evidence(**overrides: Any) -> CompatEvidence:
    base: dict[str, Any] = dict(
        evidence_id="ev-1",
        workflow_id="wf.evidence.test",
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        test_case_id="tc-1",
        fixture_hash="sha256:" + "a" * 64,
        expected="x",
        actual="x",
        outcome=StepOutcome.PASS,
        timestamp="2026-01-01T00:00:00Z",
        environment=EvidenceEnvironment.PRODUCTION,
        os_version="debian-13",
        app_version="1.0.0",
        runner_version="1.0.0",
        confirmed_by_role=None,
    )
    base.update(overrides)
    return CompatEvidence(**base)


# ---------------------------------------------------------------------------
# Attack 1 -- fake verified/supported qua metadata rong (COMP-048 schema.py)
# ---------------------------------------------------------------------------


def test_attack1_technical_verified_without_tested_at_or_evidence_is_rejected() -> None:
    raw = _entry_raw(cert=_cert_raw(technical_status="verified"))
    assert validate_workflow_entry(raw).ok is False


def test_attack1_end_to_end_pass_without_tested_at_or_evidence_is_rejected() -> None:
    raw = _entry_raw(cert=_cert_raw(end_to_end_status="pass"))
    assert validate_workflow_entry(raw).ok is False


def test_attack1_both_verified_and_pass_without_evidence_is_rejected() -> None:
    raw = _entry_raw(cert=_cert_raw(technical_status="verified", end_to_end_status="pass"))
    assert validate_workflow_entry(raw).ok is False


def test_attack1_vendor_supported_without_evidence_is_rejected() -> None:
    raw = _entry_raw(cert=_cert_raw(vendor_support="supported"))
    assert validate_workflow_entry(raw).ok is False


@pytest.mark.parametrize(
    "cert_overrides",
    [
        {"technical_status": "verified", "tested_at": "", "evidence_ids": []},
        {"technical_status": "verified", "tested_at": None, "evidence_ids": ["ev-1"]},
        {"technical_status": "verified", "tested_at": "   ", "evidence_ids": ["ev-1"]},
        {"technical_status": "verified", "tested_at": "2026-01-01", "evidence_ids": []},
        {"end_to_end_status": "pass", "tested_at": "", "evidence_ids": ["ev-1"]},
        {"end_to_end_status": "pass", "tested_at": "2026-01-01", "evidence_ids": None},
        {"vendor_support": "supported", "evidence_ids": []},
        {"vendor_support": "supported", "evidence_ids": None},
    ],
    ids=lambda d: ",".join(f"{k}={v!r}" for k, v in d.items()),
)
def test_attack1_every_half_filled_claim_combo_is_rejected(cert_overrides: dict[str, Any]) -> None:
    """Moi to hop claim verified/pass/supported thieu MOT trong hai dieu kien
    (tested_at khong rong / evidence_ids khong rong) phai bi tu choi -- khong
    co to hop "vua du" nao lot qua."""

    raw = _entry_raw(cert=_cert_raw(**cert_overrides))
    result = validate_workflow_entry(raw)
    assert result.ok is False, f"combo {cert_overrides} lot qua gate (ok=True)"


def test_attack1_control_case_fully_evidenced_claim_is_accepted() -> None:
    """Doi chung: claim DUNG dieu kien (tested_at + evidence_ids khong rong)
    phai duoc chap nhan -- xac nhan gate khong qua tay chan nham."""

    raw = _entry_raw(
        cert=_cert_raw(
            technical_status="verified",
            end_to_end_status="pass",
            vendor_support="supported",
            tested_at="2026-01-01",
            evidence_ids=["ev-1"],
        )
    )
    assert validate_workflow_entry(raw).ok is True


@pytest.mark.parametrize("blank_id", ["", "   ", "\t"])
def test_attack1_blank_string_evidence_ids_should_not_count_as_evidence(blank_id: str) -> None:
    raw = _entry_raw(
        cert=_cert_raw(
            technical_status="verified",
            tested_at="2026-01-01",
            evidence_ids=[blank_id],
        )
    )
    result = validate_workflow_entry(raw)
    assert result.ok is False, "evidence_ids voi phan tu rong/whitespace khong phai bang chung thuc"


# ---------------------------------------------------------------------------
# Attack 2 -- Unicode / type confusion tren schema_version + enum
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_version",
    [
        1.0,  # float, khong phai str
        True,  # bool la subclass int, khong phai "1.0"
        "1.0 ",  # trailing space
        " 1.0",  # leading space
        "1.00",  # them so 0
        "１.0",  # chu so fullwidth U+FF11 o vi tri dau
        "１.０",  # ca hai chu so fullwidth
        None,
        ["1.0"],
        10,
    ],
)
def test_attack2_schema_version_type_and_unicode_confusion_is_rejected(bad_version: Any) -> None:
    raw = _entry_raw(schema_version=bad_version)
    assert validate_workflow_entry(raw).ok is False


def test_attack2_schema_version_exact_match_control_case_is_accepted() -> None:
    raw = _entry_raw(schema_version="1.0")
    assert validate_workflow_entry(raw).ok is True


@pytest.mark.parametrize(
    "bad_technical_status",
    [
        "VERIFIED",  # uppercase
        "Verified",  # mixed case
        "verified ",  # trailing space
        " verified",  # leading space
        "verifed",  # typo gan giong
        "verified",  # typo khac
        "",
        None,
        123,
    ],
)
def test_attack2_technical_status_case_and_space_tricks_are_rejected(
    bad_technical_status: Any,
) -> None:
    raw = _entry_raw(cert=_cert_raw(technical_status=bad_technical_status))
    assert validate_workflow_entry(raw).ok is False


def test_attack2_technical_status_cyrillic_homoglyph_does_not_match_verified() -> None:
    """Dung ky tu Cyrillic 'е' (U+0435) thay cho Latin 'e' trong "verified" --
    _check_enum so sanh chuoi CHINH XAC (khong NFKC-normalize), nen homoglyph
    KHONG the tro thanh "verified" thuc -- phai bi tu choi vi enum invalid
    (an toan: khong co fuzzy-match nao vo tinh mo rong tap gia tri hop le)."""

    sneaky = "vеrified"  # 'е' Cyrillic, khong phai 'e' Latin
    assert sneaky != "verified"
    raw = _entry_raw(cert=_cert_raw(technical_status=sneaky))
    assert validate_workflow_entry(raw).ok is False


def test_attack2_required_steps_reordered_is_rejected() -> None:
    reordered = list(reversed(_REQUIRED_STEP_VALUES))
    assert reordered != _REQUIRED_STEP_VALUES
    raw = _entry_raw(required_steps=reordered)
    assert validate_workflow_entry(raw).ok is False


def test_attack2_required_steps_with_duplicate_is_rejected() -> None:
    dup = _REQUIRED_STEP_VALUES[:-1] + [_REQUIRED_STEP_VALUES[0]]
    assert len(dup) == len(_REQUIRED_STEP_VALUES)
    raw = _entry_raw(required_steps=dup)
    assert validate_workflow_entry(raw).ok is False


def test_attack2_required_steps_with_extra_eighth_step_is_rejected() -> None:
    extra = _REQUIRED_STEP_VALUES + ["extra_bonus_step"]
    raw = _entry_raw(required_steps=extra)
    assert validate_workflow_entry(raw).ok is False


def test_attack2_required_steps_missing_one_is_rejected() -> None:
    missing_one = _REQUIRED_STEP_VALUES[:-1]
    raw = _entry_raw(required_steps=missing_one)
    assert validate_workflow_entry(raw).ok is False


def test_attack2_required_steps_exact_order_control_case_is_accepted() -> None:
    raw = _entry_raw(required_steps=list(_REQUIRED_STEP_VALUES))
    assert validate_workflow_entry(raw).ok is True


# ---------------------------------------------------------------------------
# Attack 3 -- revoked=true nhung route/status van "usable"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("usable_status", ["workflow_verified", "partial_workflow"])
def test_attack3_revoked_with_usable_route_status_is_rejected_by_schema(
    usable_status: str,
) -> None:
    raw = _entry_raw(
        cert=_cert_raw(revoked=True),
        routes=[{"mode": "native_linux", "status": usable_status}],
    )
    assert validate_workflow_entry(raw).ok is False


def test_attack3_revoked_with_non_usable_route_status_control_case_is_accepted() -> None:
    """Doi chung: revoked=true nhung route KHONG tu nhan usable thi khong vi
    pham rule nay (rule chi cam "revoked + claim usable", khong cam revoked
    ton tai cung route not_inventoried)."""

    raw = _entry_raw(
        cert=_cert_raw(revoked=True),
        routes=[{"mode": "native_linux", "status": "not_inventoried"}],
    )
    assert validate_workflow_entry(raw).ok is True


def test_attack3_evaluate_route_status_revoked_wins_over_full_pass_steps() -> None:
    """Du ky thuat PASS het 7 nac + nghiep vu APPROVED, revoked=True phai
    thang tuyet doi -- evaluate_route_status kiem revoked TRUOC gate ky
    thuat (evidence.py dong ~186)."""

    result = evaluate_route_status(
        _full_pass_steps(), business_status=BusinessStatus.APPROVED, revoked=True
    )
    assert result.status == PublishedStatus.REVOKED


def test_attack3_evaluate_route_status_revoked_wins_even_with_recertify_in_future() -> None:
    result = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        revoked=True,
        recertify_by="2099-01-01",
        now="2026-01-01",
    )
    assert result.status == PublishedStatus.REVOKED


# ---------------------------------------------------------------------------
# Attack 4 -- evidence-gap elevation (derive_published_status qua gate)
# ---------------------------------------------------------------------------


def test_attack4_seven_steps_pass_but_no_evidence_ref_is_not_workflow_verified() -> None:
    steps = _full_pass_steps(verify_ref=None, submit_ref=None)
    result = evaluate_route_status(steps, business_status=BusinessStatus.APPROVED)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED


def test_attack4_evidence_ref_whitespace_only_does_not_count_as_evidence() -> None:
    """evidence_ref = "   " (chi whitespace) khong duoc coi la bang chung
    thuc -- derive_published_status dung `.strip()` truoc khi kiem rong."""

    steps = _full_pass_steps(verify_ref="   ", submit_ref="   ")
    result = evaluate_route_status(steps, business_status=BusinessStatus.APPROVED)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED


def test_attack4_verify_not_applicable_is_never_workflow_verified() -> None:
    steps = list(_full_pass_steps())
    steps[-1] = WorkflowStep(
        name=WorkflowStepName.VERIFY_RESULT, outcome=StepOutcome.NOT_APPLICABLE
    )
    result = evaluate_route_status(tuple(steps), business_status=BusinessStatus.APPROVED)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED


@pytest.mark.parametrize("blocked_step", list(WORKFLOW_STEP_ORDER))
def test_attack4_blocked_step_hidden_among_pass_is_never_workflow_verified(
    blocked_step: WorkflowStepName,
) -> None:
    """BLOCKED o BAT KY nac nao (ke ca discover/acquire it quan trong ve
    "trai nghiem") phai ha trang thai, khong duoc lan qua nhu PASS."""

    steps = list(_full_pass_steps())
    idx = list(WORKFLOW_STEP_ORDER).index(blocked_step)
    name = steps[idx].name
    steps[idx] = WorkflowStep(name=name, outcome=StepOutcome.BLOCKED)
    result = evaluate_route_status(tuple(steps), business_status=BusinessStatus.APPROVED)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED
    assert result.status == PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY


def test_attack4_control_case_full_pass_with_real_evidence_is_workflow_verified() -> None:
    """Doi chung: 7 nac PASS + evidence_ref thuc + nghiep vu APPROVED PHAI
    cho workflow_verified -- xac nhan gate khong qua tay chan nham."""

    result = evaluate_route_status(_full_pass_steps(), business_status=BusinessStatus.APPROVED)
    assert result.status == PublishedStatus.WORKFLOW_VERIFIED


# ---------------------------------------------------------------------------
# Attack 5 -- business bypass
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("business_status", [BusinessStatus.UNREVIEWED, BusinessStatus.REJECTED])
def test_attack5_non_approved_business_status_never_yields_workflow_verified(
    business_status: BusinessStatus,
) -> None:
    result = evaluate_route_status(_full_pass_steps(), business_status=business_status)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED
    assert result.status == PublishedStatus.PARTIAL_WORKFLOW


def test_attack5_no_business_status_value_other_than_approved_sneaks_through() -> None:
    """Quet toan bo enum BusinessStatus: CHI gia tri APPROVED moi duoc cho
    workflow_verified lot qua -- khong co gia tri nao khac "lo"."""

    for status in BusinessStatus:
        result = evaluate_route_status(_full_pass_steps(), business_status=status)
        if status == BusinessStatus.APPROVED:
            assert result.status == PublishedStatus.WORKFLOW_VERIFIED
        else:
            assert (
                result.status != PublishedStatus.WORKFLOW_VERIFIED
            ), f"business_status={status} lam lo workflow_verified"


# ---------------------------------------------------------------------------
# Attack 6 -- expiry bypass (recertify_by / now)
# ---------------------------------------------------------------------------


def test_attack6_approved_with_recertify_by_in_the_past_same_format_is_downgraded() -> None:
    result = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        recertify_by="2026-02-01",
        now="2026-10-15",
    )
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED
    assert result.status == PublishedStatus.PARTIAL_WORKFLOW


def test_attack6_control_case_recertify_by_in_the_future_stays_verified() -> None:
    result = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        recertify_by="2099-01-01",
        now="2026-10-15",
    )
    assert result.status == PublishedStatus.WORKFLOW_VERIFIED


def test_attack6_now_exactly_equal_recertify_by_boundary_documented_as_still_verified() -> None:
    """Bien: now == recertify_by (code dung `now > recertify_by`, strict) ->
    CHUA bi coi la qua han. Day la lua chon thiet ke duoc ghi nhan (khong
    phai lo hong theo loi hua da neu, vi "qua han" nghia la now > recertify_by,
    khong bao gom bang nhau) -- test nay CHOT lai hanh vi hien tai de phat
    hien neu no am tham doi."""

    result = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        recertify_by="2026-10-15",
        now="2026-10-15",
    )
    assert result.status == PublishedStatus.WORKFLOW_VERIFIED


def test_attack6_non_zero_padded_recertify_by_date_format_defeats_expiry_check() -> None:
    result = evaluate_route_status(
        _full_pass_steps(),
        business_status=BusinessStatus.APPROVED,
        recertify_by="2026-2-1",  # KHONG zero-pad thang/ngay -- van la "ISO-ish"
        now="2026-10-15",  # zero-padded, 8+ thang SAU ngay het han thuc
    )
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED, (
        "chung nhan het han 8 thang nhung van bao cao workflow_verified do "
        "so sanh chuoi tu dien sai dinh dang (non-zero-padded recertify_by)"
    )


# ---------------------------------------------------------------------------
# Attack 7 -- resolver stale-cert bypass (app_version / token_model)
# ---------------------------------------------------------------------------


def test_attack7_control_case_matching_app_version_keeps_route_recommended() -> None:
    entry = _resolver_entry(app_version="2.1.0")
    result = resolve_routes(_resolve_input(app_version="2.1.0"), entry)
    assert result.recommended == WindowsMode.NATIVE_LINUX
    assert result.no_verified_route is False


def test_attack7_honest_concrete_version_mismatch_invalidates_the_route() -> None:
    entry = _resolver_entry(app_version="2.1.0")
    result = resolve_routes(_resolve_input(app_version="9.9.9"), entry)
    assert result.recommended is None
    assert result.no_verified_route is True


def test_attack7_trailing_space_version_is_treated_as_a_real_mismatch() -> None:
    """ "1.0" vs "1.0 " (khoang trang cuoi) PHAI bi coi la khac nhau -- day la
    huong AN TOAN (qua chat chu khong phai lo hong): khong co "fuzzy-equal"
    nao lam hai phien ban khac nhau tro thanh "giong nhau"."""

    entry = _resolver_entry(app_version="1.0")
    result = resolve_routes(_resolve_input(app_version="1.0 "), entry)
    assert result.recommended is None
    assert result.no_verified_route is True


@pytest.mark.parametrize("token_model", ["TokenModelB", "", "unknown-token"])
def test_attack7_signing_token_mismatch_invalidates_the_route(token_model: str) -> None:
    entry = _resolver_entry(
        requires=("signing_method",),
        device_models=("TokenModelA",),
        mode=WindowsMode.WINE,
    )
    result = resolve_routes(_resolve_input(token_model=token_model, license_ok=True), entry)
    assert result.recommended is None
    assert result.no_verified_route is True


def test_attack7_control_case_matching_signing_token_keeps_route_recommended() -> None:
    entry = _resolver_entry(
        requires=("signing_method",),
        device_models=("TokenModelA",),
        mode=WindowsMode.WINE,
    )
    result = resolve_routes(_resolve_input(token_model="TokenModelA", license_ok=True), entry)
    assert result.recommended == WindowsMode.WINE
    assert result.no_verified_route is False


def test_attack7_empty_app_version_should_not_be_treated_as_a_confirmed_match() -> None:
    entry = _resolver_entry(app_version="2.1.0")
    result = resolve_routes(_resolve_input(app_version=""), entry)
    assert result.recommended is None, (
        "app_version rong (chua xac nhan) duoc resolver coi nhu KHOP voi "
        "ban chung nhan cu, giu nguyen route workflow_verified ma khong "
        "doi hoi xac nhan lai"
    )
    assert result.no_verified_route is True


def test_attack7_none_token_model_should_not_bypass_signing_requirement_check() -> None:
    entry = _resolver_entry(
        requires=("signing_method",),
        device_models=("TokenModelA",),
        mode=WindowsMode.WINE,
    )
    result = resolve_routes(_resolve_input(token_model=None, license_ok=True), entry)
    assert result.recommended is None, (
        "token_model=None (chua ro thiet bi nao) duoc resolver coi nhu du "
        "dieu kien ky, de xuat route WINE workflow_verified ma khong co "
        "bang chung token nao dang cam"
    )
    assert result.no_verified_route is True


@pytest.mark.parametrize("unresolved_cert_version", ["", "unresolved", "unknown"])
def test_attack7_unresolved_cert_app_version_never_invalidates_regardless_of_real_drift(
    unresolved_cert_version: str,
) -> None:
    entry = _resolver_entry(app_version=unresolved_cert_version)
    result = resolve_routes(_resolve_input(app_version="99.0.0-totally-different"), entry)
    assert result.recommended is None, (
        f"cert_app={unresolved_cert_version!r} (chua chot) van de xuat "
        "route workflow_verified du app_version thuc te khac hoan toan"
    )
    assert result.no_verified_route is True


# ---------------------------------------------------------------------------
# Attack 8 -- resolver khong bao gio de xuat mode never-usable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("never_usable_status", ["downloadable_only", "launches_only"])
def test_attack8_never_usable_status_as_only_route_is_never_recommended(
    never_usable_status: str,
) -> None:
    entry = _resolver_entry(route_status=never_usable_status)
    result = resolve_routes(_resolve_input(), entry)
    assert result.recommended is None
    assert result.no_verified_route is True


def test_attack8_never_usable_status_never_recommended_even_when_it_is_the_only_feasible_mode() -> (
    None
):
    """Native_linux luon feasible=True (khong deps) -- dam bao ca khi mode
    duy nhat ton tai VA kha thi, status never-usable van khong duoc de
    xuat."""

    entry = _resolver_entry(route_status="launches_only", mode=WindowsMode.NATIVE_LINUX)
    result = resolve_routes(_resolve_input(), entry)
    for candidate in result.candidates:
        if candidate.mode == WindowsMode.NATIVE_LINUX:
            assert candidate.feasible is True  # kha thi...
            assert candidate.status == "launches_only"  # ...nhung van never-usable
    assert result.recommended is None
    assert result.no_verified_route is True


# ---------------------------------------------------------------------------
# Attack 9 -- evidence provenance holes (validate_evidence)
# ---------------------------------------------------------------------------


def test_attack9_production_pass_submit_without_confirmed_by_role_is_rejected() -> None:
    ev = _evidence(
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.PRODUCTION,
        confirmed_by_role=None,
    )
    errors = validate_evidence(ev)
    assert any(e.code == "E_EVIDENCE_MISSING" for e in errors)


def test_attack9_production_pass_verify_without_confirmed_by_role_is_rejected() -> None:
    ev = _evidence(
        step=WorkflowStepName.VERIFY_RESULT,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.PRODUCTION,
        confirmed_by_role=None,
    )
    errors = validate_evidence(ev)
    assert any(e.code == "E_EVIDENCE_MISSING" for e in errors)


def test_attack9_production_pass_with_whitespace_only_role_is_rejected() -> None:
    ev = _evidence(
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.PRODUCTION,
        confirmed_by_role="   ",
    )
    errors = validate_evidence(ev)
    assert any(e.code == "E_EVIDENCE_MISSING" for e in errors)


def test_attack9_sandbox_environment_does_not_require_reviewer_role() -> None:
    """Khong duoc "qua chat": sandbox KHONG can nguoi vai-tro-nghiep-vu xac
    nhan -- neu test nay fail, gate dang over-block mot truong hop hop le."""

    ev = _evidence(
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.SANDBOX,
        confirmed_by_role=None,
    )
    errors = validate_evidence(ev)
    assert errors == []


def test_attack9_lab_environment_does_not_require_reviewer_role() -> None:
    ev = _evidence(
        step=WorkflowStepName.VERIFY_RESULT,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.LAB,
        confirmed_by_role=None,
    )
    errors = validate_evidence(ev)
    assert errors == []


def test_attack9_production_but_non_reviewer_step_does_not_require_role() -> None:
    """discover/acquire/... KHONG thuoc REVIEWER_REQUIRED_STEPS -- production
    pass o cac nac nay khong can confirmed_by_role (khong over-block)."""

    ev = _evidence(
        step=WorkflowStepName.DISCOVER,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.PRODUCTION,
        confirmed_by_role=None,
    )
    errors = validate_evidence(ev)
    assert errors == []


@pytest.mark.parametrize(
    "bad_hash",
    [
        "sha256:" + "a" * 63,  # thieu 1 ky tu
        "sha256:" + "a" * 65,  # du 1 ky tu
        "sha256:" + "A" * 64,  # hoa thay thuong
        "sha512:" + "a" * 128,  # sai thuat toan
        "sha256" + "a" * 64,  # thieu dau ":"
        "sha256:",  # thieu hash hoan toan
        "md5:" + "a" * 32,
        " sha256:" + "a" * 64,  # khoang trang dau
        "sha256:" + "a" * 64 + " ",  # khoang trang cuoi
        "sha256:" + "g" * 64,  # ky tu ngoai hex
    ],
)
def test_attack9_malformed_fixture_hash_is_rejected(bad_hash: str) -> None:
    ev = _evidence(fixture_hash=bad_hash, confirmed_by_role="qa.reviewer")
    errors = validate_evidence(ev)
    assert any(e.path == "fixture_hash" for e in errors)


def test_attack9_control_case_well_formed_evidence_is_accepted() -> None:
    ev = _evidence(
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        outcome=StepOutcome.PASS,
        environment=EvidenceEnvironment.PRODUCTION,
        confirmed_by_role="qa.reviewer",
        fixture_hash="sha256:" + "a" * 64,
    )
    assert validate_evidence(ev) == []


# ---------------------------------------------------------------------------
# Attack 10 -- evidence_to_steps laundering
# ---------------------------------------------------------------------------


def test_attack10_evidence_for_different_workflow_id_is_ignored_not_run() -> None:
    ev_other = _evidence(workflow_id="OTHER.workflow", outcome=StepOutcome.PASS)
    steps = evidence_to_steps("wf.evidence.test", [ev_other])
    submit = next(s for s in steps if s.name == WorkflowStepName.SUBMIT_OR_EXPORT)
    assert submit.outcome == StepOutcome.NOT_RUN
    assert submit.evidence_ref is None


def test_attack10_duplicate_step_fail_and_pass_worst_outcome_wins() -> None:
    ev_pass = _evidence(
        workflow_id="wf.evidence.test",
        evidence_id="ev-pass",
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        outcome=StepOutcome.PASS,
    )
    ev_fail = _evidence(
        workflow_id="wf.evidence.test",
        evidence_id="ev-fail",
        step=WorkflowStepName.SUBMIT_OR_EXPORT,
        outcome=StepOutcome.FAIL,
    )
    steps = evidence_to_steps("wf.evidence.test", [ev_pass, ev_fail])
    submit = next(s for s in steps if s.name == WorkflowStepName.SUBMIT_OR_EXPORT)
    assert submit.outcome == StepOutcome.FAIL
    assert submit.evidence_ref is None


def test_attack10_duplicate_step_blocked_and_pass_worst_outcome_wins() -> None:
    ev_pass = _evidence(
        workflow_id="wf.evidence.test",
        evidence_id="ev-pass",
        step=WorkflowStepName.VERIFY_RESULT,
        outcome=StepOutcome.PASS,
    )
    ev_blocked = _evidence(
        workflow_id="wf.evidence.test",
        evidence_id="ev-blocked",
        step=WorkflowStepName.VERIFY_RESULT,
        outcome=StepOutcome.BLOCKED,
    )
    steps = evidence_to_steps("wf.evidence.test", [ev_pass, ev_blocked])
    verify = next(s for s in steps if s.name == WorkflowStepName.VERIFY_RESULT)
    assert verify.outcome == StepOutcome.BLOCKED
    assert verify.evidence_ref is None


def test_attack10_laundered_evidence_cannot_push_full_gate_to_workflow_verified() -> None:
    """Ket hop: 6 nac PASS thuc + 1 nac (verify) co bang chung FAIL lon
    duoc "rua" bang mot bang chung PASS trung + mot bang chung cho workflow
    KHAC -- gate tong hop van khong duoc workflow_verified."""

    evidences = []
    for name in WORKFLOW_STEP_ORDER:
        if name == WorkflowStepName.VERIFY_RESULT:
            evidences.append(
                _evidence(
                    workflow_id="wf.evidence.test",
                    evidence_id="ev-verify-pass",
                    step=name,
                    outcome=StepOutcome.PASS,
                )
            )
            evidences.append(
                _evidence(
                    workflow_id="wf.evidence.test",
                    evidence_id="ev-verify-fail",
                    step=name,
                    outcome=StepOutcome.FAIL,
                )
            )
        elif name == WorkflowStepName.SUBMIT_OR_EXPORT:
            evidences.append(
                _evidence(
                    workflow_id="wf.evidence.test",
                    evidence_id="ev-submit-pass",
                    step=name,
                    outcome=StepOutcome.PASS,
                )
            )
        else:
            evidences.append(
                _evidence(
                    workflow_id="wf.evidence.test",
                    evidence_id=f"ev-{name.value}",
                    step=name,
                    outcome=StepOutcome.PASS,
                )
            )
    # Them bang chung cho workflow KHAC, co the gay nham lan neu loc sai.
    evidences.append(
        _evidence(workflow_id="OTHER.workflow", evidence_id="ev-noise", outcome=StepOutcome.PASS)
    )

    steps = evidence_to_steps("wf.evidence.test", evidences)
    result = evaluate_route_status(steps, business_status=BusinessStatus.APPROVED)
    assert result.status != PublishedStatus.WORKFLOW_VERIFIED


def test_attack10_control_case_clean_matching_evidence_yields_workflow_verified() -> None:
    """Doi chung: bang chung sach (dung workflow_id, toan PASS, co
    evidence_ref thuc) qua evidence_to_steps -> evaluate_route_status PHAI
    cho workflow_verified."""

    evidences = []
    for name in WORKFLOW_STEP_ORDER:
        evidences.append(
            _evidence(
                workflow_id="wf.evidence.test",
                evidence_id=f"ev-{name.value}",
                step=name,
                outcome=StepOutcome.PASS,
            )
        )
    steps = evidence_to_steps("wf.evidence.test", evidences)
    result = evaluate_route_status(steps, business_status=BusinessStatus.APPROVED)
    assert result.status == PublishedStatus.WORKFLOW_VERIFIED
