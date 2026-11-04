"""Structured Error Triage (SAI-009).

Phân loại lỗi tương thích TẤT ĐỊNH từ ngữ cảnh lỗi (exit code / log / crash
signature). HAI bất biến an toàn:

1. **Redact TRƯỚC** — mọi log đi qua ``namios_security.redact_text`` trước khi
   phân loại/ghi/đưa model; bản ``redacted_log`` là bản DUY NHẤT được phép lộ
   ra ngoài (mật khẩu/token/OTP/khóa/IP nội bộ/đường home bị che). TriageInput
   CHỈ nhận log + metadata lỗi — KHÔNG nhận nội dung tài liệu (SAI-006 phạm vi).
2. **Không đoán** — nhãn từ DẤU HIỆU quan sát được; thiếu dấu hiệu → ``unknown``,
   không bịa nguyên nhân. Lỗi thiếu DLL (missing_runtime) phân biệt rõ với lỗi
   license (nghiệm thu SAI-009).
"""

from __future__ import annotations

import re

from namios_i18n import Lang, t
from namios_security import redact_text
from namios_smartai import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_smartai._types import ErrorCategory, TriageInput, TriageResult

__all__ = ["triage_error", "SIGNALS"]

#: Lớp PII bổ sung của SmartAI (SAI-009 "lọc PII/secret"): ``namios_security``
#: chỉ che secret (password/token/OTP có nhãn/Bearer/IP/home-path). Dãy ≥9 chữ
#: số TRẦN (CCCD 12 số, CMND 9 số, số điện thoại/tài khoản) dễ lọt → che thêm
#: ở đây. Không ảnh hưởng phân loại (tín hiệu là TỪ, không phải dãy số dài);
#: exit code/phiên bản (1–3 chữ số / có dấu chấm) không bị đụng.
_PII_DIGITS_RE = re.compile(r"\d{9,}")
_MASK = "[REDACTED]"


def _scrub_pii(text: str) -> str:
    return _PII_DIGITS_RE.sub(_MASK, text)


#: Dấu hiệu theo thứ tự ưu tiên (cụ thể trước chung). Mỗi mục: (category,
#: tuple các chuỗi con khớp không phân biệt hoa/thường trên log+crash đã redact).
SIGNALS: tuple[tuple[ErrorCategory, tuple[str, ...]], ...] = (
    (
        ErrorCategory.DB_UNREACHABLE,
        (
            "sql server",
            "sqlstate",
            "odbc",
            "could not connect",
            "cannot connect to",
            "connection refused",
            "database",
            "server does not exist",
            "named pipes provider",
        ),
    ),
    (
        ErrorCategory.DEVICE_MISSING,
        (
            "no such device",
            "device not found",
            "printer not",
            "scanner",
            "pkcs11",
            "pkcs#11",
            "smartcard",
            "smart card",
            "token not",
            "no reader",
        ),
    ),
    (
        ErrorCategory.PORTAL_PLUGIN,
        (
            "activex",
            "webview2",
            "signing plugin",
            "browser plugin",
            "portal plugin",
            "middleware",
            "ký số plugin",
        ),
    ),
    (
        ErrorCategory.LICENSE,
        (
            "license",
            "licence",
            "activation",
            "not activated",
            "trial expired",
            "serial",
            "product key",
            "bản quyền",
            "kích hoạt",
        ),
    ),
    (
        ErrorCategory.MISSING_RUNTIME,
        (
            ".dll",
            "not found",
            "could not be loaded",
            "vcruntime",
            "msvcp",
            "mscoree",
            ".net framework",
            "missing runtime",
            "library not",
            "no se encontr",  # cross-locale "not found" đôi khi xuất hiện trong log
        ),
    ),
    (
        ErrorCategory.UNSUPPORTED_API,
        (
            "unimplemented",
            "not implemented",
            "unsupported",
            "fixme",
            "stub",
            "wine: ",
            "err:module",
        ),
    ),
    (
        ErrorCategory.DATA_MISMATCH,
        (
            "mismatch",
            "checksum",
            "differs",
            "expected",
            "sai lệch",
            "không khớp",
            "total mismatch",
        ),
    ),
)


def triage_error(ctx: TriageInput) -> TriageResult:
    """Phân loại một lỗi (SAI-009). Redact log TRƯỚC; phân loại trên bản đã
    redact; trả ``TriageResult`` với ``redacted_log`` an toàn để ghi/đưa model."""

    # 1) Redact TRƯỚC — secret (namios_security) + PII dãy số dài (SmartAI).
    #    Không bao giờ phân loại/ghi trên bản thô.
    redacted_log = _scrub_pii(redact_text(ctx.log_text or ""))
    redacted_crash = _scrub_pii(redact_text(ctx.crash_signature or ""))
    haystack = f"{redacted_log}\n{redacted_crash}".lower()

    # 2) Phân loại tất định theo dấu hiệu (cụ thể trước chung).
    for category, needles in SIGNALS:
        if any(n in haystack for n in needles):
            return TriageResult(
                category=category,
                confidence=0.8,
                evidence_vi=(t(f"sai.triage.cat.{category.value}", lang=Lang.VI),),
                redacted_log=redacted_log,
                source="static-signal",
            )

    # 3) Không dấu hiệu rõ → unknown (không bịa).
    return TriageResult(
        category=ErrorCategory.UNKNOWN,
        confidence=0.0,
        evidence_vi=(t("sai.triage.cat.unknown", lang=Lang.VI),),
        redacted_log=redacted_log,
        source="static-signal",
    )
