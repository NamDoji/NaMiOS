"""SAI-024 — Redaction Pipeline: secret/PII không lọt bundle chia sẻ."""

from __future__ import annotations

from namios_smartai.redaction import (
    is_shareable,
    redact_bundle,
    redact_text_full,
    residual_findings,
)


def test_text_redacts_secret_pii_cookie() -> None:
    s = "password=Secret1 token=ghp_AB123456 CCCD 012345678901 cookie=sess=abc123"
    out = redact_text_full(s)
    for leak in ("Secret1", "ghp_AB123456", "012345678901", "abc123"):
        assert leak not in out
    assert "[REDACTED]" in out


def test_bundle_recursive_keeps_structure() -> None:
    bundle = {
        "log": "password=X token=ghp_ABCDEF123",
        "steps": ["connect SQL", "CCCD 012345678901"],
    }
    r = redact_bundle(bundle)
    assert set(r.keys()) == {"log", "steps"}  # cấu trúc giữ nguyên
    assert "012345678901" not in str(r) and "ghp_ABCDEF123" not in str(r)


def test_is_shareable_clean_vs_leaked() -> None:
    assert is_shareable({"log": "password=hunter2 to SQL Server"}) is True  # redact sạch
    assert is_shareable({"log": "bare ghp_DEADBEEF1234 leaked"}) is False  # token trần sót


def test_sha256_hash_not_over_flagged() -> None:
    # Hash hex hợp lệ (không run ≥9 chữ số) KHÔNG bị cờ nhầm → tránh over-block.
    h = "deadbeefcafe0ba1" * 4
    assert is_shareable({"artifact": f"sha256 {h} ok"}) is True


def test_residual_findings_lists_leaks() -> None:
    assert residual_findings(["bare xoxb-123456-abcdef"]) != []
    assert residual_findings(["clean [REDACTED] line"]) == []
