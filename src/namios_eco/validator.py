"""Validator tầng 2 (ngữ nghĩa) cho danh bạ ECO-006 (ECO-002/ECO-003).

"Schema hợp lệ (tầng 1, ``catalog_schema.py``) KHÔNG đồng nghĩa với an toàn/
đúng để công bố" (cùng nguyên tắc với WP2/WP9). Ở đây thẩm định:
  - URL chính thức phải http(s), không scheme lạ, không nhúng thông tin xác
    thực đánh lừa domain (ECO-006).
  - KHÔNG cho gán ``usable`` cho ``downloadable_only``/``launches_only`` (GATE
    ECO-003 — tuyệt đối, không ngoại lệ).
  - KHÔNG cho đặt ``workflow_verified`` khi thiếu evidence nộp/nhận thật ở
    ``submit_or_export``/``verify_result`` (ECO-003 §3).
  - Chuyển trạng thái công bố phải hợp lệ theo bảng ECO-003 (không nhảy tắt
    tuỳ ý, không thoát khỏi ``revoked``).
  - Catalog KHÔNG BAO GIỜ được chứa trường điều khiển lệnh/thực thi, dù ở
    JSON thô chưa qua ``catalog_schema`` (phòng vệ nhiều lớp).
  - KHÔNG dùng cụm "ứng dụng chính thức của NaMiOS" để tả sản phẩm bên thứ ba
    (ECO-007).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from namios_core.errors import ErrorCode
from namios_core.validation import ValidationError
from namios_eco._errors import EcoErrorCode
from namios_eco.status import NEVER_USABLE_STATUSES, PublishedStatus, derive_published_status
from namios_eco.workflow import WorkflowStep
from namios_i18n import Lang, t

# NOTE (i18n, 03/11/2026): ``message_vi`` dưới đây đi qua ``namios_i18n.t``
# (nhóm key ``eco.validator.error.*``, VI/EN đã seed) nhưng LUÔN ép
# ``lang=Lang.VI`` — xem NOTE tương tự ở ``status.py``/``workflow.py``.

__all__ = [
    "validate_official_url",
    "validate_usability_claim",
    "validate_status_matches_workflow",
    "validate_status_transition",
    "validate_no_executable_keys",
    "validate_no_official_claim_text",
    "ALLOWED_STATUS_TRANSITIONS",
]

_ALLOWED_SCHEMES = frozenset({"http", "https"})

#: Tên trường bị cấm tuyệt đối trong bất kỳ dữ liệu catalog thô nào — "catalog
#: không bao giờ điều khiển lệnh" (CLAUDE.md + ECO-006). Phòng vệ thêm một
#: lớp NGOÀI ``additionalProperties: false`` của schema tầng 1, cho trường
#: hợp dữ liệu thô được kiểm trước khi tới ``catalog_schema.validate_raw``.
FORBIDDEN_EXECUTABLE_KEYS = frozenset(
    {"command", "argv", "shell", "run", "exec", "script", "cmd", "installer_argv", "url_script"}
)

#: Cụm bị cấm dùng để tả sản phẩm bên thứ ba (ECO-007 §4.1: "Không dùng từ
#: 'ứng dụng chính thức của NaMiOS' để mô tả sản phẩm bên thứ ba").
_FORBIDDEN_OFFICIAL_CLAIM_PHRASES = (
    "ứng dụng chính thức của namios",
    "ung dung chinh thuc cua namios",
    "chính thức của namios",
)

#: Ký tự vô hình kẻ tấn công chèn để tách cụm bị cấm (zero-width space/
#: non-joiner/joiner/word-joiner, BOM, soft-hyphen) — loại bỏ trước khi so.
_INVISIBLE_CHARS = dict.fromkeys((0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD), None)


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _normalize_claim_text(text: str) -> str:
    """Chuẩn hoá chống lách gate ECO-007 bằng biểu diễn Unicode khác: NFKC
    (gộp NFD→NFC + ký tự tương thích) + bỏ ký tự vô hình + casefold."""

    return unicodedata.normalize("NFKC", text).translate(_INVISIBLE_CHARS).casefold()


def _err(code: str, path: str, message_vi: str) -> ValidationError:
    return ValidationError(code=code, path=path, message_vi=message_vi)


def validate_official_url(url: str, *, path: str = "official_url") -> list[ValidationError]:
    """ECO-006: URL phải http(s) nguồn chính thức, không scheme lạ, không
    nhúng thông tin xác thực đánh lừa domain (vd
    ``https://co-quan.gov.vn@trang-gia.example/``)."""

    errors: list[ValidationError] = []
    parts = urlsplit(url)

    if parts.scheme.lower() not in _ALLOWED_SCHEMES:
        errors.append(
            _err(
                ErrorCode.E_SOURCE_POLICY.value,
                path,
                t(
                    "eco.validator.error.url_scheme_invalid",
                    lang=Lang.VI,
                    path=path,
                    scheme=parts.scheme,
                ),
            )
        )

    if not parts.netloc:
        errors.append(
            _err(
                ErrorCode.E_SOURCE_POLICY.value,
                path,
                t("eco.validator.error.url_missing_domain", lang=Lang.VI, path=path),
            )
        )
    elif "@" in parts.netloc:
        errors.append(
            _err(
                ErrorCode.E_SOURCE_POLICY.value,
                path,
                t("eco.validator.error.url_embedded_credentials", lang=Lang.VI, path=path),
            )
        )

    return errors


def validate_usability_claim(
    status: PublishedStatus, *, claimed_usable: bool, path: str = "published_status"
) -> list[ValidationError]:
    """GATE ECO-003 tuyệt đối: ``downloadable_only``/``launches_only`` KHÔNG
    BAO GIỜ được gán là usable. Gọi hàm này tại bất kỳ nơi nào định hiển thị/
    tính một status là "dùng được" trước khi hiển thị."""

    if claimed_usable and status in NEVER_USABLE_STATUSES:
        return [
            _err(
                EcoErrorCode.E_ECO_USABILITY_CLAIM.value,
                path,
                t(
                    "eco.validator.error.usability_claim_forbidden",
                    lang=Lang.VI,
                    status=status.value,
                ),
            )
        ]
    return []


def validate_status_matches_workflow(
    claimed_status: PublishedStatus,
    steps: tuple[WorkflowStep, ...],
    *,
    path: str = "published_status",
) -> list[ValidationError]:
    """Từ chối đặt ``workflow_verified`` (hoặc bất kỳ trạng thái "cao" hơn
    những gì 7 nấc chứng minh được) khi dữ liệu workflow thật không đủ bằng
    chứng. Dùng ``status.derive_published_status`` làm nguồn sự thật — nếu
    ``claimed_status`` khác trạng thái suy ra được VÀ claimed là
    ``workflow_verified`` trong khi suy luận không phải vậy → lỗi
    ``E_EVIDENCE_MISSING``."""

    derived = derive_published_status(steps)
    if (
        claimed_status == PublishedStatus.WORKFLOW_VERIFIED
        and derived.status != PublishedStatus.WORKFLOW_VERIFIED
    ):
        return [
            _err(
                ErrorCode.E_EVIDENCE_MISSING.value,
                path,
                t(
                    "eco.validator.error.status_evidence_missing",
                    lang=Lang.VI,
                    derived_status=derived.status.value,
                    reasons="; ".join(derived.reasons_vi),
                ),
            )
        ]
    return []


#: Bảng chuyển trạng thái hợp lệ (ECO-003), mirror cách làm TxState
#: (M1-INTERFACES §4): mỗi lần đổi version/cổng/plugin PHẢI đánh giá lại,
#: không nhảy tắt tuỳ ý; ``revoked`` là terminal (không tự phục hồi qua hàm
#: này — phục hồi sau revoke là quyết định quản trị riêng, ngoài phạm vi
#: state machine tự động).
ALLOWED_STATUS_TRANSITIONS: Mapping[PublishedStatus, frozenset[PublishedStatus]] = {
    PublishedStatus.NOT_INVENTORIED: frozenset(
        {
            PublishedStatus.DOWNLOADABLE_ONLY,
            PublishedStatus.LAUNCHES_ONLY,
            PublishedStatus.PARTIAL_WORKFLOW,
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            PublishedStatus.UNSUPPORTED,
        }
    ),
    PublishedStatus.DOWNLOADABLE_ONLY: frozenset(
        {
            PublishedStatus.LAUNCHES_ONLY,
            PublishedStatus.PARTIAL_WORKFLOW,
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            PublishedStatus.UNSUPPORTED,
            PublishedStatus.REVOKED,
        }
    ),
    PublishedStatus.LAUNCHES_ONLY: frozenset(
        {
            PublishedStatus.DOWNLOADABLE_ONLY,
            PublishedStatus.PARTIAL_WORKFLOW,
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            PublishedStatus.UNSUPPORTED,
            PublishedStatus.REVOKED,
        }
    ),
    PublishedStatus.PARTIAL_WORKFLOW: frozenset(
        {
            PublishedStatus.LAUNCHES_ONLY,
            PublishedStatus.WORKFLOW_VERIFIED,
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            PublishedStatus.UNSUPPORTED,
            PublishedStatus.REVOKED,
        }
    ),
    PublishedStatus.WORKFLOW_VERIFIED: frozenset(
        {
            PublishedStatus.PARTIAL_WORKFLOW,
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            PublishedStatus.UNSUPPORTED,
            PublishedStatus.REVOKED,
        }
    ),
    PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY: frozenset(
        {
            PublishedStatus.PARTIAL_WORKFLOW,
            PublishedStatus.WORKFLOW_VERIFIED,
            PublishedStatus.UNSUPPORTED,
            PublishedStatus.REVOKED,
        }
    ),
    PublishedStatus.UNSUPPORTED: frozenset(
        {
            PublishedStatus.DOWNLOADABLE_ONLY,
            PublishedStatus.LAUNCHES_ONLY,
            PublishedStatus.PARTIAL_WORKFLOW,
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            PublishedStatus.REVOKED,
        }
    ),
    PublishedStatus.REVOKED: frozenset(),  # terminal
}


def validate_status_transition(
    frm: PublishedStatus, to: PublishedStatus, *, path: str = "published_status"
) -> list[ValidationError]:
    """Chặn chuyển trạng thái không hợp lệ theo ``ALLOWED_STATUS_TRANSITIONS``.
    Đứng yên (``frm == to``) luôn hợp lệ (không phải một "chuyển")."""

    if frm == to:
        return []
    allowed = ALLOWED_STATUS_TRANSITIONS.get(frm, frozenset())
    if to not in allowed:
        allowed_values = sorted(s.value for s in allowed) or ["(không có — terminal)"]
        return [
            _err(
                ErrorCode.E_STATE_CONFLICT.value,
                path,
                t(
                    "eco.validator.error.status_transition_invalid",
                    lang=Lang.VI,
                    from_status=frm.value,
                    to_status=to.value,
                    allowed=allowed_values,
                ),
            )
        ]
    return []


def validate_no_executable_keys(
    raw: Mapping[str, Any], *, path: str = "$"
) -> list[ValidationError]:
    """Phòng vệ nhiều lớp: catalog KHÔNG BAO GIỜ được điều khiển lệnh. Chặn
    bất kỳ key thô nào trùng ``FORBIDDEN_EXECUTABLE_KEYS`` ở BẤT KỲ cấp lồng
    nào trong ``raw`` (đệ quy qua dict/list), không chỉ cấp cao nhất — để
    không phụ thuộc duy nhất vào ``additionalProperties: false`` của tầng 1."""

    errors: list[ValidationError] = []

    def _walk(node: Any, node_path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                child_path = f"{node_path}.{key}" if node_path else str(key)
                if isinstance(key, str) and key.lower() in FORBIDDEN_EXECUTABLE_KEYS:
                    errors.append(
                        _err(
                            ErrorCode.E_SEMANTIC_RECIPE.value,
                            child_path,
                            t(
                                "eco.validator.error.executable_key_forbidden",
                                lang=Lang.VI,
                                key=key,
                            ),
                        )
                    )
                _walk(value, child_path)
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                _walk(item, f"{node_path}[{idx}]")

    _walk(raw, path if path != "$" else "")
    return errors


def validate_no_official_claim_text(text: str, *, path: str) -> list[ValidationError]:
    """ECO-007: KHÔNG dùng cụm "ứng dụng chính thức của NaMiOS" (có/không
    dấu, không phân biệt hoa thường) để tả một sản phẩm bên thứ ba."""

    normalized = _normalize_claim_text(text)
    accent_folded = _strip_accents(normalized)
    for phrase in _FORBIDDEN_OFFICIAL_CLAIM_PHRASES:
        if phrase in normalized or _strip_accents(phrase) in accent_folded:
            return [
                _err(
                    EcoErrorCode.E_ECO_OFFICIAL_CLAIM_FORBIDDEN.value,
                    path,
                    t("eco.validator.error.official_claim_forbidden", lang=Lang.VI, path=path),
                )
            ]
    return []


def validate_no_official_claim_in_entry_texts(
    texts: Sequence[tuple[str, str]],
) -> list[ValidationError]:
    """Tiện ích chạy ``validate_no_official_claim_text`` trên nhiều trường
    văn bản của một entry cùng lúc. ``texts`` là ``(path, value)``."""

    errors: list[ValidationError] = []
    for path, value in texts:
        errors.extend(validate_no_official_claim_text(value, path=path))
    return errors
