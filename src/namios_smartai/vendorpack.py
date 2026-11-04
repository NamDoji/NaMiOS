"""Vendor Collaboration Pack (SAI-014).

Khi bị chặn bởi plugin/driver/API Windows-only, tự dựng BẢN NHÁP báo cáo tái
hiện cho nhà cung cấp: sản phẩm/phiên bản, môi trường, log ĐÃ REDACT, kết quả
Windows đối chứng, API cần, test case. CHỈ bản nháp — KHÔNG có hàm tự gửi/liên
hệ. Gói KHÔNG chứa secret/dữ liệu sản xuất (redact + quét lại). Phân biệt rõ
``collaboration`` = 'desired' (mình muốn hợp tác) vs 'vendor_approved' (vendor
đã chấp thuận) — mặc định 'desired', không tự nâng.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from namios_security import redact_text
from namios_smartai._types import VendorPack
from namios_smartai.triage import _scrub_pii

__all__ = ["build_vendor_pack", "is_safe_to_share", "RESIDUAL_SECRET_RE"]

#: Dấu hiệu secret THẬT còn sót SAU redact (quét bảo thủ để quyết
#: ``contains_secrets``). Negative-lookahead ``(?!\[redacted\])`` để KHÔNG báo
#: nhầm chính cái mask ``[REDACTED]`` do redact_text/scrub để lại.
RESIDUAL_SECRET_RE = re.compile(
    r"(?i)(?:"
    r"-----BEGIN |"
    r"\bgh[pousr]_[A-Za-z0-9]{6,}|"  # GitHub token: ghp_/gho_/ghu_/ghs_/ghr_
    r"\bAKIA[0-9A-Z]{12,}|"  # AWS access key id
    r"\bxox[baprs]-[A-Za-z0-9-]{6,}|"  # Slack token
    r"(?:password|passwd|token|secret|bearer|api[_-]?key)\s*[:=]?\s*(?!\[redacted\])[^\s\[\]]{3,}|"
    r"\d{9,}"
    r")"
    # Chỉ bắt dạng secret CÓ DẤU HIỆU RÕ (prefix nhà cung cấp / nhãn / dãy số
    # dài) — KHÔNG bắt chuỗi dài chung chung (vd sha256 hash hợp lệ trong log)
    # để tránh over-block. Mở rộng danh sách này khi gặp định dạng token mới.
)


def _clean(line: str) -> str:
    """Redact secret (namios_security) + PII dãy số dài (lớp SmartAI)."""

    return _scrub_pii(redact_text(line))


def build_vendor_pack(
    *,
    product: str,
    version: str,
    environment: str,
    raw_logs: Sequence[str],
    windows_baseline_result: str,
    needed_api: str,
    test_cases: Sequence[str],
    collaboration: str = "desired",
) -> VendorPack:
    """Dựng gói vendor (bản nháp). Log được REDACT; nếu sau redact vẫn còn dấu
    hiệu secret → đánh dấu ``contains_secrets=True`` (caller/`is_safe_to_share`
    dùng để CHẶN chia sẻ). ``collaboration`` chỉ nhận 'desired' hoặc
    'vendor_approved'; giá trị lạ → 'desired' (bảo thủ)."""

    redacted = tuple(_clean(line) for line in raw_logs)
    residual = any(RESIDUAL_SECRET_RE.search(line) for line in redacted)
    collab = collaboration if collaboration in ("desired", "vendor_approved") else "desired"
    return VendorPack(
        product=product,
        version=version,
        environment=environment,
        redacted_logs=redacted,
        windows_baseline_result=windows_baseline_result,
        needed_api=needed_api,
        test_cases=tuple(test_cases),
        collaboration=collab,
        contains_secrets=residual,
    )


def is_safe_to_share(pack: VendorPack) -> bool:
    """CHỈ an toàn chia sẻ khi KHÔNG còn secret/dữ liệu sản xuất sót lại."""

    return not pack.contains_secrets
