"""T2 (tester độc lập) — adversarial/negative cho SEC-11 (redaction không
lộ secret) nhắm vào ``namios_security.redactor`` (WP8). Độc lập với
``tests/security/security/test_redactor.py`` của dev — tập trung vector
dev CHƯA phủ: case-insensitive key với dấu phân cách khác nhau
(``API-Key``/``apiKey``/``API_KEY``), QR/OTP lồng trong JSON-string thô
(không phải key khớp), secret dính liền KHÔNG có dấu phân cách rõ
(``password=`` ngay sát dấu câu), nhiều secret liên tiếp trong 1 chuỗi,
secret Unicode (user Việt), và áp lực ``ErrorBody``-shaped export thật có
``warnings``/``data`` lồng sâu 4 cấp.

KHÔNG dùng secret/đường dẫn thật — toàn bộ giá trị FAKE, không chứa dữ liệu
nhạy cảm thật."""

from __future__ import annotations

from namios_security import redact_obj, redact_text


# --- Case-insensitive + biến thể phân cách tên field ---------------------


def test_redact_obj_masks_mixed_case_and_delimiter_variants_of_sensitive_keys() -> None:
    o = {
        "API-Key": "FakeDashKey111",
        "apiKey": "FakeCamelKey222",
        "API_KEY": "FakeUnderscoreKey333",
        "Authorization": "FakeAuthCapitalized444",
        "REFRESH-TOKEN": "FakeRefreshDash555",
        "harmless_api_reference": "chỉ-là-mô-tả-không-phải-secret",
    }
    out = redact_obj(o)
    for key in ("API-Key", "apiKey", "API_KEY", "Authorization", "REFRESH-TOKEN"):
        assert out[key] == "[REDACTED]", f"key '{key}' không bị redact (case/delimiter variant)"


# --- Nhiều secret LIÊN TIẾP trong một chuỗi tự do (không chỉ 1 secret/dòng) --


def test_redact_text_multiple_distinct_secrets_in_single_line_all_removed() -> None:
    s = (
        "Đăng nhập: username=cuongdc password=FakePass!2026 token: "
        "fakeTokA1B2C3 Authorization: Bearer fakeBearerXYZ789 "
        "mã OTP là 773311, từ IP nội bộ 10.20.30.40 "
        "và máy 192.168.9.9, đường dẫn /home/cuongdc/tai-lieu-mat.pdf"
    )
    out = redact_text(s)
    leaked = [
        secret
        for secret in (
            "cuongdc",
            "FakePass!2026",
            "fakeTokA1B2C3",
            "fakeBearerXYZ789",
            "773311",
            "10.20.30.40",
            "192.168.9.9",
            "/home/cuongdc",
        )
        if secret in out
    ]
    assert not leaked, f"các secret vẫn còn trong output sau redact_text: {leaked}"


def test_redact_text_otp_phrase_with_longer_realistic_vietnamese_gap_not_caught() -> None:
    """KỲ VỌNG AN TOÀN: số OTP sau cụm từ "mã OTP" vẫn phải bị redact dù có
    một câu tiếng Việt thực tế hơi dài hơn mẫu test của dev chen giữa cụm
    từ và con số (ví dụ "mã OTP của giao dịch chuyển tiền là 773311").

    HIỆN TRẠNG: ``_OTP_PHRASE_RE`` dùng ``[^\\d]{0,12}`` — cửa sổ CỐ ĐỊNH
    tối đa 12 ký tự không-phải-số giữa cụm từ và con số. Câu tiếng Việt tự
    nhiên hơi dài ("của giao dịch chuyển tiền là ") vượt quá 12 ký tự nên
    KHÔNG khớp, số OTP thật lọt ra ngoài redaction. Nếu test này FAIL (OTP
    vẫn còn trong output), đó là bằng chứng defect thật (brittleness của
    cửa sổ khoảng cách cố định) — ghi vào báo cáo, KHÔNG tự sửa code dev."""

    s = "Mã OTP của giao dịch chuyển tiền là 773311, không chia sẻ cho ai."
    out = redact_text(s)
    assert "773311" not in out


# --- Secret dính sát dấu câu / không có khoảng trắng phân cách -----------


def test_redact_text_password_assignment_stuck_to_punctuation() -> None:
    """``password=FakeStuckPass123!,tiếp`` (dấu phẩy ngay sau, không có
    khoảng trắng) — kiểm tra regex ``[^\\s,;]+`` dừng đúng tại dấu phẩy/chấm
    phẩy KHÔNG để chúng dính vào giá trị bị thay, nhưng phần SECRET TRƯỚC
    dấu phẩy vẫn phải được loại hoàn toàn."""

    s = "lỗi xảy ra: password=FakeStuckPass123!,tiếp tục xử lý; token=FakeStuckTok9;kết thúc"
    out = redact_text(s)
    assert "FakeStuckPass123!" not in out
    assert "FakeStuckTok9" not in out


# --- Unicode / tiếng Việt trong giá trị secret ---------------------------


def test_redact_obj_masks_vietnamese_valued_secret_fields() -> None:
    o = {
        "password": "MậtKhẩuGiảĐâyLàFake123",
        "otp": "Mã giả không phải số: ABC-FAKE-OTP",
        "note": "Học viên Nguyễn Văn Ánh đã nộp bài — không phải secret.",
    }
    out = redact_obj(o)
    assert out["password"] == "[REDACTED]"
    assert out["otp"] == "[REDACTED]"
    assert out["note"] == o["note"]  # nội dung vô hại giữ nguyên


# --- Export lồng sâu 4 cấp mô phỏng ErrorBody.details thật ---------------


def test_redact_obj_deeply_nested_four_levels_export_no_leak() -> None:
    o: dict[str, object] = {
        "status": "error",
        "warnings": [
            {
                "context": {
                    "request": {
                        "headers": {"authorization": "Bearer FakeDeepNestedToken000"},
                        "body": {"password": "FakeDeepNestedPass000"},
                    },
                    "trace": [
                        {"step": "login", "detail": "password=FakeTraceInline999 ok"},
                        {"step": "lookup", "detail": "từ máy 172.20.5.5 tới /home/fakehost/data"},
                    ],
                }
            }
        ],
        "data": {"ok": False},
    }
    out = redact_obj(o)
    rendered = repr(out)
    for secret in (
        "FakeDeepNestedToken000",
        "FakeDeepNestedPass000",
        "FakeTraceInline999",
        "172.20.5.5",
        "/home/fakehost",
    ):
        assert secret not in rendered, f"secret lồng sâu '{secret}' rò ra ngoài export"
    # Cấu trúc/field vô hại vẫn giữ nguyên để debug được.
    assert out["status"] == "error"
    assert out["data"] == {"ok": False}


# --- QR payload thô (base64-like) không khớp key nhưng khớp giá trị ------


def test_redact_obj_qr_field_masked_even_with_long_base64_like_payload() -> None:
    long_fake_qr = "data:image/png;base64," + ("Qr1FakeBase64" * 20)
    o = {"qr_data": long_fake_qr, "unrelated_base64_blob": ("Qr1FakeBase64" * 20)}
    out = redact_obj(o)
    assert out["qr_data"] == "[REDACTED]"
    # Field KHÔNG khớp tên nhạy cảm — hành vi thật hiện tại: giá trị dài
    # không chứa pattern regex nội dung (không phải password=/token=/Bearer/
    # OTP/IP/home-path) nên KHÔNG bị lớp 2 (redact_text) phát hiện và vẫn
    # còn nguyên. Ghi nhận: đây là giới hạn đã biết của "chỉ 2 lớp phòng
    # thủ" (field-match + vài regex nội dung cố định) — KHÔNG phải lỗi vi
    # phạm acceptance hiện tại (acceptance chỉ yêu cầu field ``qr_data``
    # khớp tên bị mask, không yêu cầu phát hiện QR payload trôi tự do ở
    # field khác tên).
    assert out["unrelated_base64_blob"] == o["unrelated_base64_blob"]


def test_redact_text_bearer_token_immediately_followed_by_newline_and_more_text() -> None:
    s = "Authorization: Bearer FakeNewlineTok123\nNext-Header: value\n"
    out = redact_text(s)
    assert "FakeNewlineTok123" not in out
    assert "Next-Header: value" in out
