"""Cross-cutting SmartAI — kiểm thử đối kháng an toàn dữ liệu / quan sát /
cách ly (SAI-024 redaction, SAI-034 observability, SAI-026 memory scope).

Mỗi ``test_attack_N_...`` cố tình CÔNG vào MỘT lời hứa cross-cutting:

(a) KHÔNG secret/PII nào sống sót qua gói chẩn đoán đã redact; ``note`` của
    trace KHÔNG BAO GIỜ chứa credential; ``is_shareable`` phải False bất cứ
    khi nào một secret nhận-diện-được còn sót lại sau pass chuẩn; dữ liệu
    hợp lệ (hash sha256) KHÔNG bị cờ nhầm (over-block).
(b) Phân loại nguồn lỗi (SAI-034) phân biệt RÕ model/policy/tool/vendor/
    portal — không gộp mập mờ.
(c) Trí nhớ (SAI-026) cách ly theo tenant tuyệt đối — không đọc/liệt/xuất/
    xoá được dữ liệu của tenant khác bằng bất kỳ trick nào (case, khoảng
    trắng, scope PUBLIC giả).

Nếu một bất biến thật sự SAI, test này PHẢI FAIL (hoặc ``xfail(strict=True)``
với lý do bắt đầu bằng ``"HOLE:"``) — KHÔNG được sửa ``src/`` từ file này.
"""

from __future__ import annotations

import pytest

from namios_smartai import (
    MemoryScope as MS,
)
from namios_smartai import (
    MemoryStore,
    Trace,
    TraceErrorClass,
    TraceEvent,
    classify_error_source,
    is_shareable,
    redact_bundle,
    scrub_all,
)

EC = TraceErrorClass

# ---------------------------------------------------------------------------
# Attack 1 — bundle lồng sâu (dict/list/dict) mang mọi loại secret cùng lúc:
# password, token gh*_, Authorization Bearer, khối PEM, CCCD 12 số, MST 13
# số, cookie, connection string/Pwd. Sau ``redact_bundle`` KHÔNG giá trị bí
# mật nào còn sót trong bất kỳ nhánh nào, và cấu trúc (key/kiểu container)
# được giữ nguyên để còn tái hiện lỗi.
# ---------------------------------------------------------------------------


def test_attack_1_nested_bundle_leaks_nothing_and_keeps_structure() -> None:
    bundle = {
        "top": "password=TopSecretVal1",
        "nested": {
            "auth": "Authorization: Bearer abcDEF123realtoken",
            "token_field": "token=ghp_REAL1aaaaaBBBB",
            "list_of_things": [
                "cookie=sess=abc123xyzREALCOOKIE",
                {"deep": "connection string = Server=myserver;Pwd=secretpass123"},
                "CCCD 012345678901",
                "MST 1234567890123",
                "-----BEGIN RSA PRIVATE KEY-----\n"
                "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCREALKEYDATA\n"
                "-----END RSA PRIVATE KEY-----\n",
            ],
        },
    }

    redacted = redact_bundle(bundle)
    rendered = str(redacted)

    secrets = (
        "TopSecretVal1",
        "abcDEF123realtoken",
        "ghp_REAL1aaaaaBBBB",
        "abc123xyzREALCOOKIE",
        "secretpass123",
        "012345678901",
        "1234567890123",
        "BEGIN RSA PRIVATE KEY",
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCREALKEYDATA",
    )
    leaked = [s for s in secrets if s in rendered]
    assert not leaked, f"HOLE: secret còn sót trong bundle đã redact: {leaked} -> {rendered!r}"

    # Cấu trúc được giữ: cùng tập key ở mọi cấp, cùng kiểu container, cùng
    # số phần tử — chỉ GIÁ TRỊ chuỗi bị thay, không mất thông tin tái hiện.
    assert set(redacted.keys()) == {"top", "nested"}
    assert set(redacted["nested"].keys()) == {"auth", "token_field", "list_of_things"}
    assert isinstance(redacted["nested"]["list_of_things"], list)
    assert len(redacted["nested"]["list_of_things"]) == 5
    assert isinstance(redacted["nested"]["list_of_things"][1], dict)
    assert set(redacted["nested"]["list_of_things"][1].keys()) == {"deep"}


# ---------------------------------------------------------------------------
# Attack 2 — ``is_shareable`` phải cờ-unsafe (False) cho MỌI dạng token lạ mà
# RESIDUAL_SECRET_RE nhận diện được (gh*_/AKIA/xox[baprs]-), ngay cả khi
# không có key/label rõ ràng ("bare ... leaked"). Đối chứng dương: bundle mà
# pass chuẩn redact sạch hoàn toàn thì phải True (không over-block).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bundle",
    [
        {"log": "bare ghp_DEADBEEF1234 leaked"},
        {"log": "AKIAABCDEFGHIJKLMNOP"},
        {"log": "xoxb-1-abcdef"},
    ],
)
def test_attack_2_is_shareable_flags_unrecognized_bare_tokens(bundle: dict) -> None:
    msg = f"HOLE: bundle không an toàn vẫn is_shareable=True: {bundle}"
    assert is_shareable(bundle) is False, msg


def test_attack_2_is_shareable_true_when_standard_pass_fully_redacts() -> None:
    assert is_shareable({"log": "password=x to SQL"}) is True


# ---------------------------------------------------------------------------
# Attack 3 — ``scrub_all`` (pass TỐI ĐA dùng cho trace note) phải xoá luôn
# token trần không có key rõ ràng, KHÔNG chỉ mask có điều kiện như pass
# chuẩn.
# ---------------------------------------------------------------------------


def test_attack_3_scrub_all_removes_bare_tokens_completely() -> None:
    out = scrub_all("bare ghp_DEADBEEF1234 and AKIAABCDEFGHIJKLMNOP")
    assert "ghp_DEADBEEF1234" not in out, f"HOLE: ghp_ trần còn sót sau scrub_all: {out!r}"
    assert "AKIAABCDEFGHIJKLMNOP" not in out, f"HOLE: AKIA trần còn sót sau scrub_all: {out!r}"


# ---------------------------------------------------------------------------
# Attack 4 — dữ liệu hợp lệ (hash sha256 hex, câu tiếng Việt bình thường)
# KHÔNG bị cờ nhầm (over-block) bởi ``\d{9,}`` hay bất kỳ pattern nào khác —
# nếu không, mọi báo cáo kỹ thuật chứa hash sẽ bị chặn chia sẻ vô cớ.
# ---------------------------------------------------------------------------


def test_attack_4_legit_hash_and_vietnamese_sentence_not_over_flagged() -> None:
    sha256_like = "sha256 " + ("deadbeefcafe0ba1" * 4)
    assert is_shareable({"h": sha256_like}) is True, "HOLE: hash hex hợp lệ bị cờ nhầm là secret"

    vn_sentence = "Học sinh làm đúng 8/10 câu, cần xem lại video buổi 3."
    assert is_shareable({"s": vn_sentence}) is True, "HOLE: câu tiếng Việt bình thường bị cờ nhầm"


# ---------------------------------------------------------------------------
# Attack 5 — trace note mang mọi loại secret (password, token gh*_ trần,
# header PEM, CCCD 12 số) → sau ``Trace.record`` (tự scrub) KHÔNG secret nào
# sống sót trong ``str(trace.events())`` (hình dạng log/export thực tế nhất).
# ---------------------------------------------------------------------------


def test_attack_5_trace_note_never_leaks_credentials() -> None:
    tr = Trace()
    note = (
        "password=TopSecretNoteVal ghp_ABCDEF123456REAL "
        "-----BEGIN RSA PRIVATE KEY-----\nMIIFAKEKEYDATA\n-----END RSA PRIVATE KEY-----\n "
        "CCCD 012345678901"
    )
    tr.record(
        TraceEvent(
            event_id="e1",
            plan_id="p1",
            action_id="a1",
            policy_decision="deny",
            tool="t",
            result="blocked",
            error_class=EC.POLICY,
            note=note,
        )
    )
    blob = str(tr.events())
    secrets = (
        "TopSecretNoteVal",
        "ghp_ABCDEF123456REAL",
        "BEGIN RSA PRIVATE KEY",
        "MIIFAKEKEYDATA",
        "012345678901",
    )
    leaked = [s for s in secrets if s in blob]
    assert not leaked, f"HOLE: trace note lộ credential: {leaked} -> {blob!r}"


# ---------------------------------------------------------------------------
# Attack 6 — classify_error_source(SAI-034).
#
# 6a. 5 nguồn sạch (không mơ hồ) + rỗng→NONE + gibberish không khớp needle
#     nào → UNKNOWN. Đây là lõi lời hứa "phân biệt rõ 5 nguồn".
#
# 6b/6c. (xfail HOLE) Bộ phân loại chỉ dùng "needle substring in lowercase
#     text", KHÔNG word-boundary, với THỨ TỰ ưu tiên cố định
#     POLICY > TOOL > VENDOR > PORTAL > MODEL. Một tín hiệu THỰC chỉ nói về
#     TOOL (không nhắc policy/deny/consent/...) vẫn bị gắn nhãn POLICY nếu
#     tình cờ chứa từ chứa substring "risk" (ví dụ "brisket" — tên món ăn,
#     không liên quan an toàn); tương tự một tín hiệu nói rõ "vendor driver"
#     bị gắn nhãn TOOL vì chứa substring "scope" (ví dụ "horoscope"). Đây là
#     vi phạm thật của lời hứa "phân biệt RÕ nguồn" — bộ phân loại không
#     field/token-aware, dễ bị từ ngữ tình cờ (hoặc cố ý, nếu text đến từ
#     log vendor không kiểm soát) đánh lạc nguồn.
# ---------------------------------------------------------------------------


def test_attack_6a_classify_five_sources_plus_none_and_unknown() -> None:
    assert classify_error_source("policy deny consent") == EC.POLICY
    assert classify_error_source("tool schema fail-closed") == EC.TOOL
    assert classify_error_source("vendor sdk driver missing") == EC.VENDOR
    assert classify_error_source("portal activex plugin") == EC.PORTAL
    assert classify_error_source("model returned bad json") == EC.MODEL
    assert classify_error_source("") == EC.NONE

    # Gibberish KHÔNG được tình cờ chứa substring của bất kỳ needle nào
    # (kiểm tra thủ công trước khi coi là "gibberish sạch" — xem attack 6b
    # cho một ví dụ gibberish TÌNH CỜ trúng needle "sdk").
    gibberish = "lorem ipsum foobar baz qux zent"
    assert classify_error_source(gibberish) == EC.UNKNOWN


def test_attack_6b_tool_only_signal_misclassified_as_policy_via_substring() -> None:
    # Thông điệp CHỈ nói về tool (cảm biến), không nhắc policy/deny/consent/
    # capability — nhưng "brisket" (món thịt, vô hại) chứa substring "risk",
    # một needle của POLICY được kiểm TRƯỚC TOOL trong thứ tự ưu tiên.
    signal = "tool call failed: temperature sensor brisket reading out of range"
    got = classify_error_source(signal)
    if got == EC.POLICY:
        pytest.xfail(
            "HOLE: classify_error_source() (src/namios_smartai/observability.py, "
            "_ERROR_SIGNALS) khớp needle bằng substring KHÔNG word-boundary; tín hiệu "
            "chỉ-về-TOOL bị gắn nhãn POLICY vì 'brisket' chứa 'risk' và POLICY được "
            f"kiểm trước TOOL. signal={signal!r} got={got}"
        )
    assert got == EC.TOOL


def test_attack_6c_vendor_only_signal_misclassified_as_tool_via_substring() -> None:
    # Thông điệp nói RÕ "vendor driver" (không nhắc tool/schema/scope theo
    # nghĩa thật) — nhưng "horoscope" chứa substring "scope", needle của
    # TOOL được kiểm TRƯỚC VENDOR trong thứ tự ưu tiên.
    signal = "vendor driver crashed while reading horoscope calibration data"
    got = classify_error_source(signal)
    if got == EC.TOOL:
        pytest.xfail(
            "HOLE: classify_error_source() (src/namios_smartai/observability.py, "
            "_ERROR_SIGNALS) khớp needle bằng substring KHÔNG word-boundary; tín hiệu "
            "nói rõ 'vendor driver' bị gắn nhãn TOOL vì 'horoscope' chứa 'scope' và "
            f"TOOL được kiểm trước VENDOR. signal={signal!r} got={got}"
        )
    assert got == EC.VENDOR


# ---------------------------------------------------------------------------
# Attack 7 — reject_reasons() chỉ chứa mốc "deny" (không lẫn allow), kèm
# đúng error_class và note đã redact của đúng mốc đó.
# ---------------------------------------------------------------------------


def test_attack_7_reject_reasons_contains_only_deny_events() -> None:
    tr = Trace()
    tr.record(
        TraceEvent("e1", "p1", "a_deny", "deny", "t", "blocked", error_class=EC.TOOL, note="n-deny")
    )
    tr.record(
        TraceEvent(
            "e2", "p1", "a_allow", "allow", "t", "success", error_class=EC.NONE, note="n-allow"
        )
    )

    rr = tr.reject_reasons()
    assert len(rr) == 1, f"HOLE: reject_reasons() lẫn event allow: {rr}"
    assert rr[0] == ("a_deny", "tool", "n-deny")


# ---------------------------------------------------------------------------
# Attack 8 — đọc chéo tenant bị từ chối tuyệt đối: get()/list_keys() cho
# owner "A" bằng requester "B" → None/(); owner đọc đúng-mình thì được. Thử
# thêm trick case-folding ("a" thay "A") và khoảng trắng thừa ("A ") — không
# được coi là trùng owner.
# ---------------------------------------------------------------------------


def test_attack_8_cross_tenant_read_denied_including_case_and_whitespace_tricks() -> None:
    m = MemoryStore()
    m.put(MS.ORG, "A", "recipe1", {"x": 1})

    assert m.get(MS.ORG, "A", "recipe1", requester="B") is None
    assert m.list_keys(MS.ORG, "A", requester="B") == ()

    # Trick case-folding / khoảng trắng — KHÔNG được coi là trùng owner.
    assert m.get(MS.ORG, "A", "recipe1", requester="a") is None, "HOLE: case-fold bypass"
    assert m.get(MS.ORG, "A", "recipe1", requester="A ") is None, "HOLE: whitespace bypass"

    # Đối chứng: owner đọc đúng mình thì được.
    assert m.get(MS.ORG, "A", "recipe1", requester="A") == {"x": 1}
    assert m.list_keys(MS.ORG, "A", requester="A") == ("recipe1",)


# ---------------------------------------------------------------------------
# Attack 9 — export_tenant/delete_tenant chéo tenant bị từ chối; delete của
# chính chủ XOÁ THẬT (và không đụng tenant khác); dữ liệu A vẫn còn sau một
# lần delete bị B thử (delete trả 0, không side-effect).
# ---------------------------------------------------------------------------


def test_attack_9_cross_tenant_export_and_delete_denied_self_delete_real() -> None:
    m = MemoryStore()
    m.put(MS.ORG, "A", "recipe1", {"x": 1})
    m.put(MS.ORG, "B", "recipeB", {"z": 9})

    # B không xuất/xoá được dữ liệu của A.
    assert m.export_tenant("A", requester="B") == {}, "HOLE: B xuất được dữ liệu của A"
    deleted_by_b = m.delete_tenant("A", requester="B")
    assert deleted_by_b == 0, f"HOLE: B xoá được dữ liệu của A (trả {deleted_by_b})"
    assert m.get(MS.ORG, "A", "recipe1", requester="A") == {
        "x": 1
    }, "HOLE: dữ liệu A biến mất sau lần delete-chéo bị từ chối (side-effect)"

    # A tự xuất/xoá được — và KHÔNG đụng B.
    exported = m.export_tenant("A", requester="A")
    assert exported == {"org/recipe1": {"x": 1}}
    deleted_by_a = m.delete_tenant("A", requester="A")
    assert deleted_by_a == 1
    assert m.get(MS.ORG, "A", "recipe1", requester="A") is None
    assert m.get(MS.ORG, "B", "recipeB", requester="B") == {
        "z": 9
    }, "HOLE: delete_tenant('A') xoá luôn dữ liệu B"


# ---------------------------------------------------------------------------
# Attack 10 — PUBLIC đọc tự do bởi BẤT KỲ requester nào (kể cả chuỗi lạ chưa
# từng đăng ký); nhưng một entry KHÔNG-public của chủ khác thì KHÔNG BAO GIỜ
# đọc được dù cùng "key" trùng tên với entry PUBLIC (không lẫn scope).
# ---------------------------------------------------------------------------


def test_attack_10_public_scope_universally_readable_non_public_never_crosses() -> None:
    m = MemoryStore()
    m.put(MS.PUBLIC, "namios", "kb1", "public info")
    m.put(MS.ORG, "namios", "kb1", {"private": "org-only, same key name as the PUBLIC entry"})

    # PUBLIC đọc được bởi bất kỳ ai, kể cả requester chưa từng xuất hiện.
    assert m.get(MS.PUBLIC, "namios", "kb1", requester="totally-unregistered-stranger") == (
        "public info"
    )
    assert m.list_keys(MS.PUBLIC, "namios", requester="anyone-else") == ("kb1",)

    # ORG cùng owner + cùng TÊN KEY nhưng khác scope — người lạ vẫn bị chặn;
    # không bị rò do trùng key name với entry PUBLIC.
    assert (
        m.get(MS.ORG, "namios", "kb1", requester="totally-unregistered-stranger") is None
    ), "HOLE: entry ORG rò ra qua trùng tên key với entry PUBLIC"
