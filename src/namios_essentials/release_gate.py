"""Cổng phát hành Essentials (APP11-036). Không phát hành nếu IME, Office,
browser, Security Center hoặc cập nhật/rollback P0 lỗi; không ghi "đã cài app
Linux" cho shortcut web; 6 dịch vụ web phải đã kiểm trên browser ship + máy
pilot. Hàm này CHỈ TỔNG HỢP các invariant đã có ở ``manifest``/``labels`` —
KHÔNG dựng thêm luật mới, để không lệch khỏi nguồn sự thật duy nhất."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from namios_essentials._errors import EssentialsErrorCode
from namios_essentials._types import EssentialsManifest, ReleaseGateResult
from namios_essentials.labels import web_label_is_honest
from namios_essentials.manifest import is_shippable

#: Các khóa P0 bắt buộc đạt trước khi phát hành (Phụ lục 11 §3.1/§3.2, APP11-036).
P0_GATE_KEYS: tuple[str, ...] = (
    "ime",
    "office",
    "browser",
    "security_center",
    "update_rollback",
)

#: 6 dịch vụ web bắt buộc có smoke test trên browser ship + máy pilot (APP11-018/036).
REQUIRED_WEB_SERVICES: tuple[str, ...] = (
    "zalo_web",
    "youtube",
    "maps",
    "facebook",
    "tiktok",
    "whatsapp",
)

__all__ = ["P0_GATE_KEYS", "REQUIRED_WEB_SERVICES", "evaluate_release_gate"]


def evaluate_release_gate(
    manifests: Iterable[EssentialsManifest],
    p0_checks: Mapping[str, bool],
    web_service_smoke_results: Mapping[str, bool],
    web_display_texts: Mapping[str, str] | None = None,
) -> ReleaseGateResult:
    """Xét cổng phát hành (APP11-036). ``blockers`` rỗng là điều kiện CẦN và
    ĐỦ cho ``shippable=True`` — không có nhánh tắt bỏ qua."""

    blockers: list[str] = []
    display_texts = web_display_texts or {}

    for key in P0_GATE_KEYS:
        if not p0_checks.get(key, False):
            blockers.append(f"{EssentialsErrorCode.E_APP11_RELEASE_GATE_BLOCKED.value}:{key}")

    for service in REQUIRED_WEB_SERVICES:
        if not web_service_smoke_results.get(service, False):
            blockers.append(f"{EssentialsErrorCode.E_APP11_RELEASE_GATE_BLOCKED.value}:{service}")

    for m in manifests:
        if not is_shippable(m):
            blockers.append(f"{EssentialsErrorCode.E_APP11_MANIFEST_NO_SOURCE.value}:{m.id}")
        display_text = display_texts.get(m.id, "")
        if display_text and not web_label_is_honest(m, display_text):
            blockers.append(f"{EssentialsErrorCode.E_APP11_LABEL_MISLEADING.value}:{m.id}")

    return ReleaseGateResult(shippable=not blockers, blockers=tuple(blockers))
