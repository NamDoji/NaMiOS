"""Unit test WP8 — ``namios_security.redactor`` (SEC-11, SUP-002).

Corpus dữ liệu nhạy cảm GIẢ (không phải secret thật) để xác minh
``Redactor`` lọc hết trước khi vào log/diagnostics/export."""

from __future__ import annotations

from namios_security import RedactorImpl, redact_obj, redact_text


def test_redact_text_password_assignment() -> None:
    s = "login attempt password=S3cr3t!FakePass user=cuong"
    out = redact_text(s)
    assert "S3cr3t!FakePass" not in out
    assert "password=[REDACTED]" in out


def test_redact_text_token_colon_form() -> None:
    s = "Authorization header token: abcDEF123FAKE.jwt.sig"
    out = redact_text(s)
    assert "abcDEF123FAKE.jwt.sig" not in out


def test_redact_text_bearer_token() -> None:
    s = "curl -H 'Authorization: Bearer ab12CD34fake-token-value'"
    out = redact_text(s)
    assert "ab12CD34fake-token-value" not in out
    assert "[REDACTED]" in out


def test_redact_text_otp_phrase() -> None:
    s = "Mã OTP của bạn là 482913, không chia sẻ cho ai."
    out = redact_text(s)
    assert "482913" not in out


def test_redact_text_private_ip() -> None:
    s = "kết nối tới máy nội bộ 192.168.1.42 cổng 8080 và 10.0.5.9"
    out = redact_text(s)
    assert "192.168.1.42" not in out
    assert "10.0.5.9" not in out


def test_redact_text_home_path() -> None:
    s = "đọc file cấu hình tại /home/cuongdc/.config/namios/secret.conf"
    out = redact_text(s)
    assert "/home/cuongdc" not in out


def test_redact_text_leaves_harmless_text_untouched() -> None:
    s = "Cài đặt thành công khóa học Toán lớp 1G0 cho học viên."
    assert redact_text(s) == s


def test_redact_text_empty_string() -> None:
    assert redact_text("") == ""


# --- redact_obj — allowlist field -----------------------------------------


def test_redact_obj_masks_password_field_regardless_of_type() -> None:
    o = {"username": "cuongdc", "password": "FakeSecretPass123", "retries": 3}
    out = redact_obj(o)
    assert out["password"] == "[REDACTED]"
    assert out["username"] == "[REDACTED]"
    assert out["retries"] == 3


def test_redact_obj_masks_otp_cookie_token_qr_fields() -> None:
    o = {
        "otp": "913842",
        "session_cookie": "sid=FAKECOOKIEVALUE",
        "api_key": "ak_live_FAKE1234567890",
        "qr_code": "data:image/png;base64,FAKEBASE64DATA==",
        "note": "an toàn",
    }
    out = redact_obj(o)
    assert out["otp"] == "[REDACTED]"
    assert out["api_key"] == "[REDACTED]"
    assert out["qr_code"] == "[REDACTED]"
    # 'session_cookie' chứa 'cookie' trong tên -> field-match toàn giá trị.
    assert out["session_cookie"] == "[REDACTED]"
    assert out["note"] == "an toàn"


def test_redact_obj_recurses_into_nested_mapping_and_list() -> None:
    o: dict[str, object] = {
        "user": {
            "password": "NestedFakePass",
            "profile": {"token": "NestedFakeToken"},
        },
        "events": [
            {"message": "login password=InlineFakePass ok"},
            {"ip": "login from 10.1.2.3"},
        ],
    }
    out = redact_obj(o)
    user = out["user"]
    assert isinstance(user, dict)
    assert user["password"] == "[REDACTED]"
    profile = user["profile"]
    assert isinstance(profile, dict)
    assert profile["token"] == "[REDACTED]"

    events = out["events"]
    assert isinstance(events, list)
    assert "InlineFakePass" not in events[0]["message"]
    assert "10.1.2.3" not in events[1]["ip"]


def test_redact_obj_keeps_non_sensitive_scalars_and_structure() -> None:
    o = {"status": "ok", "count": 42, "ratio": 0.5, "flag": True, "nothing": None}
    out = redact_obj(o)
    assert out == o


def test_redact_obj_tuple_preserved_as_tuple() -> None:
    o = {"items": ("password=FakeTuplePass", "safe-value")}
    out = redact_obj(o)
    assert isinstance(out["items"], tuple)
    assert "FakeTuplePass" not in out["items"][0]
    assert out["items"][1] == "safe-value"


def test_redactor_protocol_class_delegates() -> None:
    impl = RedactorImpl()
    assert impl.redact_text("password=FakeDelegatePass") == "password=[REDACTED]"
    assert impl.redact_obj({"token": "FakeDelegateToken"})["token"] == "[REDACTED]"


def test_error_body_details_full_corpus_no_leak() -> None:
    """Corpus tổng hợp mô phỏng ``ErrorBody.details`` chứa nhiều loại dữ
    liệu nhạy cảm giả cùng lúc — không loại nào được lộ ra ngoài."""

    fake_corpus = {
        "username": "nguoi-dung-fake",
        "password": "FakeCorpusPass!1",
        "otp": "654321",
        "api_key": "ak_fake_corpus_999",
        "cookie": "sid=FakeCorpusCookie",
        "qr_code": "FAKEQRPAYLOAD",
        "message": (
            "Lỗi đăng nhập cho user password=InlineCorpusPass "
            "token: InlineCorpusToken tại /home/nguoi-dung-fake "
            "từ máy nội bộ 172.16.4.5, mã OTP 112233"
        ),
    }
    out = redact_obj(fake_corpus)
    rendered = repr(out)
    for secret in (
        "FakeCorpusPass!1",
        "654321",
        "ak_fake_corpus_999",
        "FakeCorpusCookie",
        "FAKEQRPAYLOAD",
        "InlineCorpusPass",
        "InlineCorpusToken",
        "/home/nguoi-dung-fake",
        "172.16.4.5",
        "112233",
    ):
        assert secret not in rendered, f"secret '{secret}' đã rò ra ngoài redaction"
