"""Redaction Pipeline cho gói chẩn đoán/telemetry (SAI-024).

Lớp lọc DÙNG CHUNG: trước khi một bundle (dict/list/str — log, diagnostic,
telemetry) rời máy hoặc vào model/support, PHẢI đi qua đây. Che: secret
(password/token/OTP/Bearer/PEM — reuse ``namios_security.redact_text``) + PII
dãy số dài (CCCD/CMND/MST/số tài khoản/điện thoại) + cookie/connection-string
rõ. Vừa đủ để vẫn tái hiện lỗi (không xoá cấu trúc/thông điệp).

Nghiệm thu SAI-024: fixture chứa secret giả KHÔNG xuất hiện trong bundle đã
redact; ``is_shareable`` = True chỉ khi không còn dấu hiệu secret sót.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from namios_security import redact_text

__all__ = [
    "redact_text_full",
    "scrub_all",
    "redact_bundle",
    "residual_findings",
    "is_shareable",
    "RESIDUAL_SECRET_RE",
]

_MASK = "[REDACTED]"

#: PII dãy ≥9 chữ số trần (CCCD 12, CMND 9, MST 10/13, SĐT, số tài khoản).
_PII_DIGITS_RE = re.compile(r"\d{9,}")

#: Cookie / connection-string rõ (giá trị KHÔNG phải mask).
_KV_SECRET_RE = re.compile(
    r"(?i)\b(cookie|set-cookie|connection ?string|conn ?str|pwd|uid=\S)\b"
    r"\s*[:=]?\s*(?!\[redacted\])[^\s;]+"
)

#: Dấu hiệu secret THẬT còn sót SAU redact (quyết ``is_shareable``). Lookahead
#: loại chính mask ``[REDACTED]``. Chỉ bắt dạng rõ — không bắt chuỗi dài chung
#: (vd sha256 hash hợp lệ) để tránh over-block.
RESIDUAL_SECRET_RE = re.compile(
    r"(?i)(?:"
    r"-----BEGIN |"
    r"\bgh[pousr]_[A-Za-z0-9]{6,}|"
    r"\bAKIA[0-9A-Z]{12,}|"
    r"\bxox[baprs]-[A-Za-z0-9-]{6,}|"
    r"(?:password|passwd|token|secret|bearer|api[_-]?key|cookie)\s*[:=]?\s*(?!\[redacted\])[^\s\[\]]{3,}|"
    r"\d{9,}"
    r")"
)


def redact_text_full(s: str) -> str:
    """Redact một chuỗi: secret (namios_security) → PII dãy số dài → cookie/
    connection-string rõ. Thứ tự: secret trước (giữ nhãn), rồi số, rồi KV."""

    out = _KV_SECRET_RE.sub(lambda m: f"{m.group(1)}={_MASK}", redact_text(s or ""))
    return _PII_DIGITS_RE.sub(_MASK, out)


def scrub_all(s: str) -> str:
    """Scrub TỐI ĐA cho nơi PHẢI lưu sạch tuyệt đối (vd trace note SAI-034 —
    không lộ credential): ``redact_text_full`` RỒI che luôn token dạng rõ còn
    sót (gh_/AWS/Slack/PEM). Khác ``redact_bundle`` (pass chuẩn) vốn CỐ Ý để
    token lạ sót để ``is_shareable`` cờ-unsafe (chặn chia sẻ) thay vì âm thầm
    giữ — hai ngữ cảnh khác nhau."""

    return RESIDUAL_SECRET_RE.sub(_MASK, redact_text_full(s))


def redact_bundle(bundle: Any) -> Any:
    """Redact đệ quy một bundle (str/Mapping/Sequence) — giữ nguyên CẤU TRÚC,
    chỉ che giá trị chuỗi. Key của Mapping giữ nguyên (để tái hiện lỗi)."""

    if isinstance(bundle, str):
        return redact_text_full(bundle)
    if isinstance(bundle, Mapping):
        return {k: redact_bundle(v) for k, v in bundle.items()}
    if isinstance(bundle, (list, tuple)):
        return type(bundle)(redact_bundle(v) for v in bundle)
    return bundle


def _iter_strings(bundle: Any) -> list[str]:
    if isinstance(bundle, str):
        return [bundle]
    if isinstance(bundle, Mapping):
        return [s for v in bundle.values() for s in _iter_strings(v)]
    if isinstance(bundle, Sequence) and not isinstance(bundle, (str, bytes)):
        return [s for v in bundle for s in _iter_strings(v)]
    return []


def residual_findings(bundle: Any) -> list[str]:
    """Quét bundle (nên là bản ĐÃ redact) tìm dấu hiệu secret còn sót. Trả danh
    sách chuỗi dính (rỗng = sạch)."""

    return [s for s in _iter_strings(bundle) if RESIDUAL_SECRET_RE.search(s)]


def is_shareable(bundle: Any) -> bool:
    """An toàn chia sẻ CHỈ khi sau redact không còn dấu hiệu secret (SAI-024)."""

    return not residual_findings(redact_bundle(bundle))
