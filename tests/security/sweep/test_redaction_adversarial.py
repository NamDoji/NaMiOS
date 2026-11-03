"""Redaction adversarial — SEC-009/SUP-002. password/token/cookie/OTP/
QR/private-key KHONG duoc lo ra log/envelope/diagnostics/export, thu nhieu
bien the Unicode/format. ``namios_security.redactor`` co 2 lop: allowlist
field (``redact_obj``) + regex noi dung tu do (``redact_text``)."""

from __future__ import annotations

import pytest

from namios_security import redact_obj, redact_text

_MASK = "[REDACTED]"

# ---------------------------------------------------------------------------
# Field-based (redact_obj) — nhieu bien the ten khoa.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "Password",
        "PASSWORD",
        "passwd",
        "pwd",
        "user_password",
        "db_password",
        "api_key",
        "api-key",
        "apiKey".lower(),
        "access_token",
        "refresh_token",
        "otp",
        "cookie",
        "session_cookie",
        "authorization",
        "auth_header",
        "qr_code",
        "qr_data",
        "private_key",
        "ssh_private_key",
        "credential",
        "username",
        "user_name",
    ],
)
def test_redact_obj_masks_sensitive_field_regardless_of_case_or_separator(key: str) -> None:
    out = redact_obj({key: "gia-tri-bi-mat-123"})
    assert out[key] == _MASK


def test_redact_obj_masks_nested_mapping_recursively() -> None:
    nested = {
        "user": {"profile": {"otp": "445566", "display_name": "Cuong"}},
        "items": [{"token": "abc.def.ghi"}, {"ok": True}],
    }
    out = redact_obj(nested)
    assert out["user"]["profile"]["otp"] == _MASK
    assert out["user"]["profile"]["display_name"] == "Cuong"
    assert out["items"][0]["token"] == _MASK
    assert out["items"][1]["ok"] is True


def test_redact_obj_masks_value_even_when_value_is_nonstring() -> None:
    out = redact_obj({"otp": 123456, "password": None, "api_key": ["a", "b"]})
    assert out["otp"] == _MASK
    assert out["password"] == _MASK
    assert out["api_key"] == _MASK


def test_redact_obj_does_not_mask_unrelated_fields() -> None:
    out = redact_obj({"course_name": "Toan lop 6", "score": 95})
    assert out["course_name"] == "Toan lop 6"
    assert out["score"] == 95


# ---------------------------------------------------------------------------
# Content-based (redact_text) — password=/token=/Bearer/OTP/IP noi bo/home.
# ---------------------------------------------------------------------------


def test_redact_text_masks_password_assignment_in_free_sentence() -> None:
    s = "Loi dang nhap MISA: password=SuperSecret123 khong dung"
    out = redact_text(s)
    assert "SuperSecret123" not in out
    assert _MASK in out


def test_redact_text_masks_bearer_token_in_authorization_header_log() -> None:
    s = "Request header: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
    out = redact_text(s)
    assert "eyJhbGciOiJIUzI1NiJ9" not in out


def test_redact_text_masks_otp_phrase_vietnamese() -> None:
    s = "Mã xác minh của bạn là 778899, không chia sẻ cho ai."
    out = redact_text(s)
    assert "778899" not in out


def test_redact_text_masks_private_ipv4_address() -> None:
    s = "Ket noi SQL lab tai 192.168.1.50 bi timeout"
    out = redact_text(s)
    assert "192.168.1.50" not in out


def test_redact_text_masks_home_path_hiding_username() -> None:
    s = "Khong doc duoc file /home/do.chi.cuong/Documents/bao-cao.docx"
    out = redact_text(s)
    assert "do.chi.cuong" not in out


def test_redact_text_leaves_unrelated_text_untouched() -> None:
    s = "Hoc sinh lam dung 8/10 cau, can xem lai video buoi 3."
    assert redact_text(s) == s


def test_redact_text_handles_empty_string() -> None:
    assert redact_text("") == ""


# ---------------------------------------------------------------------------
# FINDING — PEM/SSH private key noi dung TU DO (khong duoi mot key ten
# "private_key") lo hoan toan khong bi loc boi CA HAI lop (field + regex).
# Day la kich ban thuc te: exception traceback/log tu do nhung mot thu vien
# parser nhung noi dung file nguoi dung vao message, hoac diagnostics export
# chep nguyen van mot doan log co dinh kem khoa.
# ---------------------------------------------------------------------------

_PEM_RSA_KEY = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDemo1234567890\n"
    "-----END RSA PRIVATE KEY-----\n"
)

_PEM_OPENSSH_KEY = (
    "-----BEGIN OPENSSH PRIVATE KEY-----\n"
    "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMw==\n"
    "-----END OPENSSH PRIVATE KEY-----\n"
)


def test_redact_text_masks_pem_rsa_private_key_block_in_free_text() -> None:
    message = f"Loi khi nap khoa Wine runner: {_PEM_RSA_KEY}"
    out = redact_text(message)
    assert "BEGIN RSA PRIVATE KEY" not in out, f"VULNERABLE: PEM key lo nguyen ven: {out!r}"


def test_redact_text_masks_openssh_private_key_block_in_free_text() -> None:
    message = f"Doc file cau hinh that bai, noi dung: {_PEM_OPENSSH_KEY}"
    out = redact_text(message)
    assert "BEGIN OPENSSH PRIVATE KEY" not in out, f"VULNERABLE: SSH key lo nguyen ven: {out!r}"


def test_redact_obj_masks_pem_private_key_embedded_in_free_text_field() -> None:
    payload = {"message": f"stacktrace: {_PEM_RSA_KEY}"}
    out = redact_obj(payload)
    assert (
        "BEGIN RSA PRIVATE KEY" not in out["message"]
    ), f"VULNERABLE: redact_obj() khong loc noi dung PEM trong field tu do: {out!r}"
