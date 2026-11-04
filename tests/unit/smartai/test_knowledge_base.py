"""SAI-025 — Knowledge Base có nguồn: provenance + mức thử theo version."""

from __future__ import annotations

from namios_smartai._types import KbEntry, Provenance, TestedLevel
from namios_smartai.knowledge_base import KnowledgeBase, trust_rank


def _kb(*entries: KbEntry) -> KnowledgeBase:
    kb = KnowledgeBase()
    for e in entries:
        kb.add(e)
    return kb


def _cert(
    app: str, ver: str, level: TestedLevel, *, as_of: str = "2026-10-01", **kw: object
) -> KbEntry:
    return KbEntry(
        app_id=app,
        app_version=ver,
        provenance=Provenance.NAMIOS_CERT,
        statement_vi="chứng nhận",
        as_of=as_of,
        tested_level=level,
        confidence=0.95,
        **kw,  # type: ignore[arg-type]
    )


def test_cert_verified_answers_tested_level() -> None:
    # Nghiệm thu SAI-025: hỏi version CỤ THỂ có chứng nhận → trả đúng mức thử.
    kb = _kb(_cert("MISA", "2024", TestedLevel.VERIFIED))
    ans = kb.answer("misa", "2024")
    assert ans.tested_level == TestedLevel.VERIFIED
    assert ans.provenance == Provenance.NAMIOS_CERT
    assert ans.install_guidance_allowed is True
    assert "Đã kiểm" in ans.answer_vi


def test_unknown_version_is_untested() -> None:
    # Nghiệm thu SAI-025: không có chứng nhận cho version đang hỏi → "chưa kiểm".
    kb = _kb(_cert("MISA", "2024", TestedLevel.VERIFIED))
    ans = kb.answer("MISA", "2025")  # version khác
    assert ans.tested_level == TestedLevel.UNTESTED
    assert "chưa kiểm" in ans.answer_vi.lower()
    assert ans.install_guidance_allowed is False


def test_cert_version_does_not_carry_over() -> None:
    # VERIFIED cho 2024 KHÔNG được suy sang 2025 (chống bắc cầu version).
    kb = _kb(_cert("MISA", "2024", TestedLevel.VERIFIED))
    assert kb.answer("MISA", "2025").tested_level == TestedLevel.UNTESTED


def test_community_and_ai_cannot_raise_level() -> None:
    # Lời đồn cộng đồng / suy luận AI tích cực KHÔNG nâng mức thử (vẫn UNTESTED)
    # và KHÔNG cho phép chỉ dẫn cài driver.
    kb = _kb(
        KbEntry("foo", "1.0", Provenance.COMMUNITY_UNVERIFIED, "ai đó bảo chạy ngon", "2026-01-01"),
        KbEntry("foo", "1.0", Provenance.AI_INFERENCE, "chắc là chạy được", "2026-01-01"),
    )
    ans = kb.answer("foo", "1.0")
    assert ans.tested_level == TestedLevel.UNTESTED
    assert ans.install_guidance_allowed is False
    assert "chưa kiểm" in ans.answer_vi.lower()


def test_official_doc_allows_install_but_still_untested() -> None:
    kb = _kb(
        KbEntry(
            "bar",
            "3",
            Provenance.OFFICIAL_DOC,
            "hãng nói có bản Linux",
            "2026-02-02",
            confidence=0.6,
        ),
    )
    ans = kb.answer("bar", "3")
    assert ans.tested_level == TestedLevel.UNTESTED  # tài liệu ≠ đã thử trên NaMiOS
    assert ans.install_guidance_allowed is True
    assert ans.provenance == Provenance.OFFICIAL_DOC


def test_failed_cert_reported_honestly_not_overridden() -> None:
    # Chứng nhận FAILED + cộng đồng khen "chạy tốt" → vẫn FAILED, không cho cài.
    kb = _kb(
        _cert("baz", "9", TestedLevel.FAILED),
        KbEntry("baz", "9", Provenance.COMMUNITY_UNVERIFIED, "máy mình chạy ok", "2026-05-05"),
    )
    ans = kb.answer("baz", "9")
    assert ans.tested_level == TestedLevel.FAILED
    assert ans.install_guidance_allowed is False


def test_newest_cert_wins_regression() -> None:
    # FAILED mới (2026) đè VERIFIED cũ (2025) — hồi quy trung thực.
    kb = _kb(
        _cert("qux", "1", TestedLevel.VERIFIED, as_of="2025-01-01"),
        _cert("qux", "1", TestedLevel.FAILED, as_of="2026-01-01"),
    )
    assert kb.answer("qux", "1").tested_level == TestedLevel.FAILED


def test_stale_flag_when_expired() -> None:
    kb = _kb(_cert("old", "1", TestedLevel.VERIFIED, valid_until="2026-01-01"))
    fresh = kb.answer("old", "1", now="2025-06-01")
    stale = kb.answer("old", "1", now="2026-06-01")
    assert fresh.stale is False
    assert stale.stale is True and "cũ" in stale.answer_vi


def test_no_data_untested() -> None:
    ans = KnowledgeBase().answer("nothing", "1")
    assert ans.tested_level == TestedLevel.UNTESTED
    assert ans.provenance is None and ans.as_of is None and ans.confidence == 0.0
    assert ans.install_guidance_allowed is False


def test_trust_rank_order() -> None:
    assert (
        trust_rank(Provenance.NAMIOS_CERT)
        > trust_rank(Provenance.OFFICIAL_DOC)
        > trust_rank(Provenance.COMMUNITY_UNVERIFIED)
        > trust_rank(Provenance.AI_INFERENCE)
    )
