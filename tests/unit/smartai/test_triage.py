"""SAI-009 — Error Triage: phân loại tất định + redact PII/secret TRƯỚC."""

from __future__ import annotations

from namios_smartai._types import ErrorCategory, TriageInput
from namios_smartai.triage import triage_error


def _cat(log: str) -> ErrorCategory:
    return triage_error(TriageInput(log_text=log)).category


def test_three_error_gate() -> None:
    # SAI-009 nghiệm thu: 3 lỗi giả phân loại đúng.
    assert (
        _cat("err:module failed to load vcruntime140.dll, not found")
        == ErrorCategory.MISSING_RUNTIME
    )
    assert (
        _cat("SQLSTATE 08001 could not connect to SQL Server MISA") == ErrorCategory.DB_UNREACHABLE
    )
    assert (
        _cat("Portal requires ActiveX signing plugin (Windows only)") == ErrorCategory.PORTAL_PLUGIN
    )


def test_missing_dll_distinct_from_license() -> None:
    assert _cat("api-ms-win.dll not found") == ErrorCategory.MISSING_RUNTIME
    assert _cat("License activation expired — enter product key") == ErrorCategory.LICENSE


def test_device_and_unsupported_and_mismatch() -> None:
    assert _cat("PKCS11 token not detected, no reader") == ErrorCategory.DEVICE_MISSING
    assert _cat("wine: err:module fixme unimplemented function stub") in (
        ErrorCategory.UNSUPPORTED_API,
        ErrorCategory.MISSING_RUNTIME,
    )
    assert (
        _cat("total amount mismatch: expected differs from actual") == ErrorCategory.DATA_MISMATCH
    )


def test_unknown_when_no_signal() -> None:
    r = triage_error(TriageInput(log_text="chương trình chạy xong bình thường"))
    assert r.category == ErrorCategory.UNKNOWN
    assert r.confidence == 0.0


def test_secret_redacted_before_classify() -> None:
    # Mật khẩu/token/OTP KHÔNG được lọt vào redacted_log; vẫn phân loại đúng
    # trên bản đã redact.
    r = triage_error(
        TriageInput(
            log_text=(
                "connect failed password=SuperSecret123 token=ghp_deadbeef " "OTP 889900 SQL Server"
            )
        )
    )
    assert "SuperSecret123" not in r.redacted_log
    assert "ghp_deadbeef" not in r.redacted_log
    assert "889900" not in r.redacted_log
    assert "[REDACTED]" in r.redacted_log
    assert r.category == ErrorCategory.DB_UNREACHABLE


def test_bare_cccd_pii_scrubbed() -> None:
    # SAI-009 "lọc PII": CCCD/CMND trần (không nhãn) vẫn bị che (lớp SmartAI).
    r = triage_error(TriageInput(log_text="hồ sơ CCCD 012345678901 không kết nối SQL Server"))
    assert "012345678901" not in r.redacted_log
    assert r.category == ErrorCategory.DB_UNREACHABLE


def test_exit_code_not_over_masked() -> None:
    # Dãy số ngắn (exit code) KHÔNG bị che nhầm.
    r = triage_error(TriageInput(log_text="process exited with code 127, library not found"))
    assert "127" in r.redacted_log


def test_private_path_redacted() -> None:
    r = triage_error(TriageInput(log_text="cannot read /home/ketoan/so_cai.mdb database locked"))
    assert "/home/ketoan" not in r.redacted_log
    assert r.category == ErrorCategory.DB_UNREACHABLE
