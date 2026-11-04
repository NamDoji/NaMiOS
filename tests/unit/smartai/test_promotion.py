"""SAI-012/042 — promotion gate: AI-label không nâng, ladder evidence, quá hạn→needs_retest."""

from __future__ import annotations

import dataclasses

from namios_smartai._types import RecipeState, TrustEvidence
from namios_smartai.promotion import is_legitimately_published, promote
from namios_smartai.recipe import new_candidate


def _recipe(**kw: object) -> object:
    base = new_candidate(
        "r1",
        publisher="p",
        source_url="https://misa.vn/x",
        app_id="misa",
        app_version="2024",
        app_hash="sha256:aa",
        architecture="x86_64",
        runner="wine",
        runtime="net48",
        rollback="snapshot",
    )
    return dataclasses.replace(base, **kw) if kw else base


def _tool_pass(**kw: object) -> TrustEvidence:
    base = TrustEvidence(
        origin="tool", timestamp="2026-11-04", version="1", fixture_hash="h", test_result="pass"
    )
    return dataclasses.replace(base, **kw) if kw else base


def test_no_evidence_stays_experimental() -> None:
    state, _ = promote(_recipe(), evidence=[])
    assert state == RecipeState.EXPERIMENTAL


def test_ai_set_published_label_not_legit() -> None:
    # Recipe tự gán state=published nhưng không evidence/approver → KHÔNG hợp lệ.
    fake = _recipe(state=RecipeState.PUBLISHED, reviewers=("qa",))
    assert is_legitimately_published(fake, evidence=[], approver=None) is False


def test_tool_pass_reaches_lab_without_approver() -> None:
    state, _ = promote(_recipe(), evidence=[_tool_pass()], approver=None)
    assert state == RecipeState.LAB_PASSED


def test_full_chain_published() -> None:
    r = _recipe(reviewers=("qa",))
    state, _ = promote(r, evidence=[_tool_pass()], approver="admin", business_ok=True)
    assert state == RecipeState.PUBLISHED
    assert is_legitimately_published(r, evidence=[_tool_pass()], approver="admin", business_ok=True)


def test_business_gate_blocks_publish() -> None:
    r = _recipe(reviewers=("qa",))
    state, reason = promote(r, evidence=[_tool_pass()], approver="admin", business_ok=False)
    assert state == RecipeState.PILOT_VERIFIED
    assert "nghiệp vụ" in reason or "business" in reason.lower()


def test_vendor_or_user_evidence_not_enough() -> None:
    vendor = _tool_pass(origin="vendor")
    state, _ = promote(_recipe(), evidence=[vendor], approver="admin", business_ok=True)
    assert state == RecipeState.EXPERIMENTAL  # nguồn ngoài chỉ tham khảo


def test_expired_evidence_needs_retest() -> None:
    expired = _tool_pass(valid_until="2020-01-01")
    state, _ = promote(_recipe(), evidence=[expired], approver="admin", now="2026-11-04")
    assert state == RecipeState.NEEDS_RETEST


def test_structural_gap_caps_below_published() -> None:
    # Recipe đổi hệ thống thiếu rollback → không thể published dù đủ người duyệt.
    r = _recipe(rollback=None, reviewers=("qa",))
    state, _ = promote(r, evidence=[_tool_pass()], approver="admin", business_ok=True)
    assert state != RecipeState.PUBLISHED
