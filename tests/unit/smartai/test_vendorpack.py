"""SAI-014 — Vendor Collaboration Pack: redact, không secret, bản nháp."""

from __future__ import annotations

from namios_smartai.vendorpack import build_vendor_pack, is_safe_to_share


def _pack(logs: list[str], collaboration: str = "desired"):
    return build_vendor_pack(
        product="MISA",
        version="2024",
        environment="wine-9.0",
        raw_logs=logs,
        windows_baseline_result="ok on Windows",
        needed_api="ActiveX signing plugin",
        test_cases=["submit a sample form"],
        collaboration=collaboration,
    )


def test_secrets_redacted_and_safe() -> None:
    pack = _pack(["connect failed password=Secret1 token=ghp_zz123456 CCCD 012345678901"])
    joined = " ".join(pack.redacted_logs)
    assert "Secret1" not in joined and "ghp_zz123456" not in joined and "012345678901" not in joined
    assert is_safe_to_share(pack) is True


def test_surviving_token_marks_unsafe() -> None:
    # Token dạng ghp_ nằm trần trong câu (redact_text bỏ sót) → residual scan
    # cờ contains_secrets → KHÔNG an toàn chia sẻ (chặn, đúng SAI-014).
    pack = _pack(["raw ghp_ABCDEF123456 leaked in prose"])
    assert is_safe_to_share(pack) is False


def test_more_token_shapes_flagged_unsafe() -> None:
    # AWS/Slack/GitHub-variant token dạng trần → cờ unsafe (SAI-014 hardening).
    assert is_safe_to_share(_pack(["leak AKIAABCDEFGHIJKLMNOP in log"])) is False
    assert is_safe_to_share(_pack(["slack xoxb-123456-abcdef token"])) is False
    assert is_safe_to_share(_pack(["gho_ABCDEF123456 refresh"])) is False


def test_legit_sha256_hash_not_over_flagged() -> None:
    # Hash sha256 hợp lệ (64 hex, KHÔNG phải secret, không có dãy ≥9 chữ số)
    # trong log KHÔNG bị cờ nhầm → tránh over-block.
    h = "deadbeefcafe0ba1" * 4  # 64 hex, không có run ≥9 chữ số liên tiếp
    assert is_safe_to_share(_pack([f"artifact sha256 {h} verified ok"])) is True


def test_collaboration_defaults_desired_not_auto_approved() -> None:
    assert _pack(["hi"]).collaboration == "desired"
    assert _pack(["hi"], collaboration="vendor_approved_fake").collaboration == "desired"
    assert _pack(["hi"], collaboration="vendor_approved").collaboration == "vendor_approved"


def test_no_auto_send_api() -> None:
    # SAI-014: chỉ bản nháp — module KHÔNG có hàm tự gửi/liên hệ vendor.
    import namios_smartai.vendorpack as vp

    public = {n for n in dir(vp) if not n.startswith("_")}
    assert not any(k in n.lower() for n in public for k in ("send", "contact", "submit", "email"))
