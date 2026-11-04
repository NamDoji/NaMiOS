"""Adversarial QA — SAI-025 Knowledge Base + SAI-029 Human Feedback.

Mục tiêu: cố tình PHÁ hai module "lớp tin cậy" để tìm lỗ TRUNG THỰC/AN TOÀN
thật. Không sửa ``src/``; chỉ tấn công qua API công khai.

Bất biến (phải giữ):

KB (SAI-025):
  I1 — chứng nhận cho version NÀY không nâng mức thử cho version KHÁC.
  I2 — nguồn cộng đồng/AI MỘT MÌNH không bao giờ đặt tested_level != UNTESTED,
       không bao giờ cho install_guidance_allowed=True.
  I3 — FAILED cert phải báo FAILED, không bị nguồn lạc quan (doc/community/AI)
       đè; install_guidance_allowed=False.
  I4 — không có cert cho đúng version hỏi → "chưa kiểm" + UNTESTED.
  I5 — cert MỚI NHẤT (theo as_of) thắng; VERIFIED cũ KHÔNG che được FAILED mới.
  I6 — cờ stale fail-honest: chỉ True khi BIẾT CHẮC now>valid_until.
  I7 — không có dữ liệu → provenance=None, confidence=0.0, install=False.

Feedback (SAI-029):
  F1 — không khối lượng/kết hợp phản hồi nào nâng would_promote / can_certify.
  F2 — suggested_test_cases không bịa từ mô tả rỗng / verdict UNCLEAR.
  F3 — verdicts_by_role giữ USER/IT/BUSINESS tách biệt.
  F4 — for_workflow / suggested_test_cases(wf) cách ly theo workflow.

Test nào đánh dấu ``xfail(strict=True, reason="HOLE: ...")`` = lỗ thật đã xác
nhận ở nguồn (ghi file:line trong reason). File tổng thể PHẢI xanh.
"""

from __future__ import annotations

import pytest

from namios_smartai._types import (
    Feedback,
    FeedbackVerdict,
    KbEntry,
    Provenance,
    ReporterRole,
    TestedLevel,
)
from namios_smartai.human_feedback import FeedbackLedger, can_certify_from_feedback
from namios_smartai.knowledge_base import KnowledgeBase, trust_rank

CERT = Provenance.NAMIOS_CERT
DOC = Provenance.OFFICIAL_DOC
COMM = Provenance.COMMUNITY_UNVERIFIED
AI = Provenance.AI_INFERENCE
TL = TestedLevel
FV = FeedbackVerdict
RR = ReporterRole


def _cert(app: str, ver: str, level: TestedLevel, as_of: str, **kw: object) -> KbEntry:
    return KbEntry(app, ver, CERT, "cert", as_of, level, kw.pop("confidence", 0.9), **kw)  # type: ignore[arg-type]


# ===========================================================================
# KB — I1: KHÔNG suy mức thử sang version khác
# ===========================================================================


@pytest.mark.parametrize("asked", ["2024.0", "2024.1", "2024-sp1", "2025", "", "2023"])
def test_i1_different_version_never_carries_over(asked: str) -> None:
    """Cert VERIFIED cho '2024' KHÔNG được làm version khác thành != UNTESTED."""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-01-01"))
    ans = kb.answer("MISA", asked)
    assert ans.tested_level is TL.UNTESTED
    assert ans.install_guidance_allowed is False
    assert ans.provenance is None  # không có bản ghi nào khớp version hỏi


def test_i1_fullwidth_digits_do_not_collide_with_ascii() -> None:
    """'２０２４' (fullwidth) KHÔNG được coi là '2024' → không carry-over."""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-01-01"))
    ans = kb.answer("MISA", "２０２４")
    assert ans.tested_level is TL.UNTESTED
    assert ans.install_guidance_allowed is False


def test_i1_whitespace_and_case_are_normalized_same_version() -> None:
    """Khoảng trắng/hoa-thường chỉ là nhiễu nhập liệu của CÙNG một version —
    chuẩn hoá (strip/lower) là hành vi CHỦ ĐÍCH, không phải lỗ carry-over."""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024 ", TL.VERIFIED, "2026-01-01"))
    assert kb.answer("  MISA ", "2024").tested_level is TL.VERIFIED
    kb2 = KnowledgeBase()
    kb2.add(_cert("App", "R2", TL.FAILED, "2026-01-01"))
    assert kb2.answer("app", "r2").tested_level is TL.FAILED  # FAILED giữ nguyên


# ===========================================================================
# KB — I2: cộng đồng/AI MỘT MÌNH không nâng mức thử, không cho cài
# ===========================================================================


@pytest.mark.parametrize("prov", [COMM, AI])
@pytest.mark.parametrize("planted", [TL.VERIFIED, TL.PARTIAL])
def test_i2_community_ai_alone_stay_untested_no_install(
    prov: Provenance, planted: TestedLevel
) -> None:
    """Dù bản ghi cộng đồng/AI tự gắn tested_level lạc quan + confidence cao,
    tổng hợp PHẢI là UNTESTED và install_guidance_allowed=False."""
    kb = KnowledgeBase()
    kb.add(KbEntry("MISA", "2024", prov, "tin don", "2026-01-01", planted, 0.99))
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.UNTESTED
    assert ans.install_guidance_allowed is False


def test_i2_many_community_ai_entries_still_untested() -> None:
    """Nhiều bản ghi cộng đồng + AII cộng dồn cũng không nâng được mức thử."""
    kb = KnowledgeBase()
    for i in range(50):
        kb.add(KbEntry("MISA", "2024", COMM, f"c{i}", "2026-01-01", TL.VERIFIED, 0.99))
        kb.add(KbEntry("MISA", "2024", AI, f"a{i}", "2026-02-01", TL.VERIFIED, 0.99))
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.UNTESTED
    assert ans.install_guidance_allowed is False


# ===========================================================================
# KB — I3: FAILED cert không bị nguồn lạc quan đè
# ===========================================================================


def test_i3_failed_cert_reported_failed_no_install() -> None:
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.FAILED, "2026-03-01"))
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.FAILED
    assert ans.install_guidance_allowed is False


def test_i3_failed_cert_not_overridden_by_optimistic_doc_community_ai() -> None:
    """Thêm OFFICIAL_DOC/community/AI lạc quan (cùng/ cũ hơn) KHÔNG lật FAILED."""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.FAILED, "2026-03-01"))
    kb.add(KbEntry("MISA", "2024", DOC, "doc says ok", "2026-04-01", TL.VERIFIED, 0.95))
    kb.add(KbEntry("MISA", "2024", COMM, "works for me", "2026-04-02", TL.VERIFIED, 0.95))
    kb.add(KbEntry("MISA", "2024", AI, "should work", "2026-04-03", TL.VERIFIED, 0.95))
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.FAILED
    assert ans.provenance is CERT
    assert ans.install_guidance_allowed is False


# ===========================================================================
# KB — I4: không cert đúng version → "chưa kiểm" + UNTESTED
# ===========================================================================


def test_i4_no_entries_say_untested() -> None:
    ans = KnowledgeBase().answer("Unknown", "1.0")
    assert ans.tested_level is TL.UNTESTED
    assert "Chưa kiểm" in ans.answer_vi


@pytest.mark.parametrize("prov", [DOC, COMM, AI])
def test_i4_noncert_only_is_untested_and_says_chua_kiem(prov: Provenance) -> None:
    kb = KnowledgeBase()
    kb.add(KbEntry("MISA", "2024", prov, "info", "2026-01-01", TL.VERIFIED, 0.9))
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.UNTESTED
    assert "Chưa kiểm" in ans.answer_vi


# ===========================================================================
# KB — I5: cert MỚI NHẤT thắng; VERIFIED cũ không che FAILED mới
# ===========================================================================


def test_i5_canonical_dates_newer_failed_governs() -> None:
    """Ngày ISO zero-pad chuẩn: FAILED mới (2026-10-01) ĐÈ VERIFIED cũ
    (2026-09-01). Đây là hành vi TRUNG THỰC — phải xanh."""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-09-01"))
    kb.add(_cert("MISA", "2024", TL.FAILED, "2026-10-01"))
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.FAILED
    assert ans.install_guidance_allowed is False


def test_i5_regression_nonpadded_dates_newer_failed_governs() -> None:
    """ĐÃ VÁ (I5): sort cert theo NGÀY THẬT (``_parse_utc``), không so-chuỗi.
    Ngày không zero-pad '2026-9-1' KHÔNG parse được → coi cũ nhất, KHÔNG đè được
    FAILED '2026-10-01' có ngày thật. (Trước đây so-chuỗi khiến VERIFIED cũ che
    FAILED mới + bật install.)"""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-9-1"))  # ngày hỏng → cũ nhất
    kb.add(_cert("MISA", "2024", TL.FAILED, "2026-10-01"))  # ngày thật, MỚI hơn
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.FAILED
    assert ans.install_guidance_allowed is False


def test_i5_regression_valid_iso_offset_newer_instant_governs() -> None:
    """ĐÃ VÁ (I5): so NGÀY THẬT dạng UTC-aware. ISO-8601 có offset múi giờ được
    chuẩn hoá về UTC → instant MUỘN hơn (FAILED '+00:00') governs, không bị
    instant SỚM hơn (VERIFIED '+07:00') che. (Trước đây so-chuỗi sai.)"""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-10-01T00:00:00+07:00"))  # instant sớm
    kb.add(_cert("MISA", "2024", TL.FAILED, "2026-10-01T00:00:00+00:00"))  # instant muộn
    ans = kb.answer("MISA", "2024")
    assert ans.tested_level is TL.FAILED
    assert ans.install_guidance_allowed is False


# ===========================================================================
# KB — I6: stale fail-honest
# ===========================================================================


def test_i6_stale_true_only_when_known_past_valid_until() -> None:
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-01-01", valid_until="2026-02-01"))
    assert kb.answer("MISA", "2024", now="2026-03-01").stale is True


@pytest.mark.parametrize("now", [None, "2026-01-15", "not-a-date", "", "2026-02-01"])
def test_i6_stale_fail_honest_when_undetermined(now: str | None) -> None:
    """now trước hạn / bằng hạn / rỗng / rác / thiếu → KHÔNG tự nhận stale."""
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-01-01", valid_until="2026-02-01"))
    assert kb.answer("MISA", "2024", now=now).stale is False


def test_i6_stale_false_when_valid_until_malformed() -> None:
    kb = KnowledgeBase()
    kb.add(_cert("MISA", "2024", TL.VERIFIED, "2026-01-01", valid_until="garbage"))
    assert kb.answer("MISA", "2024", now="2099-01-01").stale is False


# ===========================================================================
# KB — I7: no-data trung thực
# ===========================================================================


def test_i7_no_data_reports_none_zero_no_install() -> None:
    ans = KnowledgeBase().answer("Nope", "0")
    assert ans.provenance is None
    assert ans.confidence == 0.0
    assert ans.install_guidance_allowed is False
    assert ans.tested_level is TL.UNTESTED
    assert ans.sources == ()


def test_trust_rank_order_is_cert_highest_ai_lowest() -> None:
    assert trust_rank(CERT) > trust_rank(DOC) > trust_rank(COMM) > trust_rank(AI)


# ===========================================================================
# Feedback — F1: không phản hồi nào nâng certification
# ===========================================================================


def test_f1_no_volume_of_feedback_promotes_or_certifies() -> None:
    ledger = FeedbackLedger()
    for i in range(1000):
        for role in (RR.USER, RR.IT, RR.BUSINESS):
            ledger.submit(
                Feedback(f"f{i}-{role.value}", "wf1", "v1", "u", role, FV.RESOLVED, "đã xong")
            )
    assert ledger.would_promote_to_workflow_verified("wf1") is False
    assert can_certify_from_feedback(ledger.all()) is False
    assert can_certify_from_feedback() is False


# ===========================================================================
# Feedback — F2: không bịa gợi ý từ mô tả rỗng / UNCLEAR
# ===========================================================================


def test_f2_no_suggestion_from_empty_or_unclear() -> None:
    ledger = FeedbackLedger()
    ledger.submit(Feedback("a", "wf1", "v1", "u", RR.USER, FV.UNCLEAR, "không rõ"))
    ledger.submit(Feedback("b", "wf1", "v1", "u", RR.USER, FV.RESOLVED, "   "))
    ledger.submit(Feedback("c", "wf1", "v1", "u", RR.USER, FV.UNRESOLVED, ""))
    ledger.submit(Feedback("d", "wf1", "v1", "u", RR.USER, FV.UNCLEAR, ""))
    assert ledger.suggested_test_cases("wf1") == ()


def test_f2_resolved_gives_regression_unresolved_gives_repro() -> None:
    ledger = FeedbackLedger()
    ledger.submit(Feedback("a", "wf1", "v1", "u", RR.USER, FV.UNRESOLVED, "lỗi in ấn"))
    ledger.submit(Feedback("b", "wf1", "v1", "u", RR.IT, FV.RESOLVED, "đã vá"))
    kinds = sorted(s.kind for s in ledger.suggested_test_cases("wf1"))
    assert kinds == ["regression", "repro"]


# ===========================================================================
# Feedback — F3: verdicts_by_role tách vai trò
# ===========================================================================


def test_f3_verdicts_separated_by_role() -> None:
    ledger = FeedbackLedger()
    ledger.submit(Feedback("a", "wf1", "v1", "u1", RR.USER, FV.RESOLVED))
    ledger.submit(Feedback("b", "wf1", "v1", "u2", RR.IT, FV.UNRESOLVED))
    ledger.submit(Feedback("c", "wf1", "v1", "u3", RR.BUSINESS, FV.UNCLEAR))
    by_role = ledger.verdicts_by_role("wf1")
    assert by_role[RR.USER] == (FV.RESOLVED,)
    assert by_role[RR.IT] == (FV.UNRESOLVED,)
    assert by_role[RR.BUSINESS] == (FV.UNCLEAR,)
    # USER "resolved" KHÔNG bị gộp thành IT/BUSINESS sign-off.
    assert FV.RESOLVED not in by_role.get(RR.IT, ())
    assert FV.RESOLVED not in by_role.get(RR.BUSINESS, ())


# ===========================================================================
# Feedback — F4: cách ly theo workflow
# ===========================================================================


def test_f4_no_cross_workflow_leakage() -> None:
    ledger = FeedbackLedger()
    ledger.submit(Feedback("a", "wf1", "v1", "u", RR.USER, FV.UNRESOLVED, "bug wf1"))
    ledger.submit(Feedback("b", "wf2", "v1", "u", RR.USER, FV.UNRESOLVED, "bug wf2"))
    assert {f.workflow_id for f in ledger.for_workflow("wf1")} == {"wf1"}
    assert {s.workflow_id for s in ledger.suggested_test_cases("wf1")} == {"wf1"}
    assert {s.workflow_id for s in ledger.suggested_test_cases("wf2")} == {"wf2"}
    # Khoảng trắng không làm lẫn workflow (so khớp CHÍNH XÁC, chặt hơn KB).
    assert ledger.for_workflow("wf1 ") == ()
