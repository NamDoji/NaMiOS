"""Redaction cho log/diagnostics/export — hiện thực
``namios_core.security_types.Redactor``.

Hai lớp phòng thủ độc lập (SUP-002 — "KHÔNG chỉ regex"):

1. **Allowlist field** (``redact_obj``): bất kỳ key tên khớp nhóm nhạy cảm
   (password/token/secret/otp/cookie/apikey/authorization/qr/username/…)
   bị thay NGUYÊN GIÁ TRỊ bằng ``"[REDACTED]"``, bất kể kiểu dữ liệu.
2. **Regex nội dung** (``redact_text``): quét text tự do tìm mẫu
   password=/token=/Bearer .../OTP .../IP nội bộ/đường dẫn ``/home/<user>``
   dù không có key rõ ràng (ví dụ log tự do, câu văn).

Áp dụng CẢ HAI lớp lồng nhau trong ``redact_obj`` — field match thì chặn
toàn bộ giá trị; field không match nhưng giá trị là chuỗi thì vẫn chạy qua
``redact_text``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

__all__ = ["RedactorImpl", "redact_text", "redact_obj"]

_MASK = "[REDACTED]"

#: Tên field coi là nhạy cảm bất kể giá trị (so khớp không phân biệt hoa/
#: thường, cho phép dấu phân cách '_'/'-' giữa các từ).
_SENSITIVE_KEY_RE = re.compile(
    r"(?i)^(?:.*[_\-]?)?"
    r"(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?key|refresh[_-]?token|otp|cookie|authorization|auth[_-]?header|"
    r"qr[_-]?code|qr[_-]?data|private[_-]?key|credential|session[_-]?id|"
    r"username|user[_-]?name)"
    r"(?:[_\-]?.*)?$"
)

_FIELD_WHOLE_MATCH_RE = re.compile(
    r"(?i)^(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?key|refresh[_-]?token|otp|cookie|authorization|auth[_-]?header|"
    r"qr[_-]?code|qr[_-]?data|private[_-]?key|credential|session[_-]?id|"
    r"username|user[_-]?name)$"
)

# --- Regex nội dung tự do (lớp 2) --------------------------------------

_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|otp|cookie|"
    r"authorization|credential|username)\b\s*[:=]\s*([^\s,;]+)"
)

_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-_.=]+")

_OTP_PHRASE_RE = re.compile(
    r"(?i)\b(OTP|mã xác minh|mã xác thực|verification code|security code)\b[^\d]{0,40}(\d{4,8})"
)

_PRIVATE_IPV4_RE = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
    r"|127\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"
)

_HOME_PATH_RE = re.compile(r"/home/[^/\s]+")

#: Khối PEM/OpenSSH private key lọt vào CHUỖI TỰ DO (traceback/message/log) —
#: SEC-009 "private key không bao giờ lộ, bất kể kiểu dữ liệu". Bắt cả
#: 'BEGIN RSA/EC/DSA/OPENSSH/ENCRYPTED PRIVATE KEY' lẫn 'BEGIN PRIVATE KEY'.
_PEM_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact_text(s: str) -> str:
    """Lọc chuỗi tự do: password/token/secret/OTP/Bearer/IP nội bộ/
    đường dẫn home người dùng. Trả bản đã lọc, giữ nguyên phần còn lại."""

    if not s:
        return s

    def _assignment_sub(m: re.Match[str]) -> str:
        return f"{m.group(1)}={_MASK}"

    # Bearer TRƯỚC assignment: "Authorization: Bearer <tok>" nếu chạy
    # assignment trước sẽ ăn luôn từ "Bearer" làm value rồi làm mất dấu hiệu
    # cho _BEARER_RE nhận diện phần token thật còn lại.
    # Khối PEM private key chạy TRƯỚC mọi regex khác, để base64 nhiều dòng
    # không bị _ASSIGNMENT_RE/_BEARER_RE cắt vụn trước khi nhận diện khối.
    out = _PEM_PRIVATE_KEY_RE.sub(_MASK, s)
    out = _BEARER_RE.sub(f"Bearer {_MASK}", out)
    out = _ASSIGNMENT_RE.sub(_assignment_sub, out)

    def _otp_sub(m: re.Match[str]) -> str:
        return f"{m.group(1)} {_MASK}"

    out = _OTP_PHRASE_RE.sub(_otp_sub, out)
    out = _PRIVATE_IPV4_RE.sub(_MASK, out)
    out = _HOME_PATH_RE.sub(f"/home/{_MASK}", out)
    return out


def _redact_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return redact_obj(value)
    if isinstance(value, (list, tuple)):
        return type(value)(_redact_scalar(v) for v in value)
    return value


def redact_obj(o: Mapping[str, Any]) -> Mapping[str, Any]:
    """Lọc một mapping (ví dụ ``ErrorBody.details``) đệ quy.

    Key khớp nhóm nhạy cảm (toàn bộ tên, ví dụ ``password``/``otp``/
    ``qr_code``) → giá trị bị thay nguyên bằng ``[REDACTED]``. Key khác mà
    giá trị là chuỗi vẫn chạy qua ``redact_text``; mapping/list lồng nhau
    được đệ quy."""

    result: dict[str, Any] = {}
    for key, value in o.items():
        if isinstance(key, str) and (
            _FIELD_WHOLE_MATCH_RE.match(key) or _SENSITIVE_KEY_RE.match(key)
        ):
            result[key] = _MASK
        else:
            result[key] = _redact_scalar(value)
    return result


class RedactorImpl:
    """Hiện thực ``namios_core.security_types.Redactor`` (Protocol)."""

    def redact_text(self, s: str) -> str:
        return redact_text(s)

    def redact_obj(self, o: Mapping[str, Any]) -> Mapping[str, Any]:
        return redact_obj(o)
