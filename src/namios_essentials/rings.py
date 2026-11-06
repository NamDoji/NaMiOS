"""Update rings — lab/pilot/stable (APP11-017). TÁI DÙNG
``namios_odc.LifecycleRing`` (lab/pilot/stable) làm enum ring DUY NHẤT trong
toàn hệ — KHÔNG khai một enum ring thứ hai riêng cho Essentials.

Bất biến (APP11-017 nghiệm thu): nếu một candidate làm hỏng một dịch vụ TRỌNG
YẾU ở ring ``lab`` (vd browser mới làm lỗi Zalo Web), ring ``stable`` GIỮ bản
cũ nhưng CÓ THỜI HẠN kèm cảnh báo rủi ro bảo mật — KHÔNG giữ vô hạn.
``is_retention_expired`` coi hạn RỖNG là ĐÃ hết hạn ngay (fail-closed): không
có đường nào để "giữ mãi" một cách âm thầm, kể cả khi caller quên đặt hạn.
"""

from __future__ import annotations

from datetime import date

from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._types import RingPromotionResult
from namios_i18n import Lang, t
from namios_odc import LifecycleRing

__all__ = ["evaluate_ring_promotion", "is_retention_expired"]


def evaluate_ring_promotion(
    *,
    candidate_version: str,
    previous_stable_version: str,
    lab_regression_failed_services: frozenset[str],
    critical_services: frozenset[str],
    retention_deadline: str,
) -> RingPromotionResult:
    """Xét thăng ``candidate_version`` từ ``lab`` lên ``stable`` (APP11-017).
    Nếu ``lab_regression_failed_services`` giao với ``critical_services``
    không rỗng → KHÔNG đẩy candidate lên; ``stable`` giữ
    ``previous_stable_version`` với ``retention_deadline`` BẮT BUỘC (rỗng vẫn
    được GHI lại nguyên trạng để caller/test thấy rõ vi phạm — xem
    ``is_retention_expired``, coi rỗng là hết hạn ngay, không tự gia hạn)."""

    broken_critical = lab_regression_failed_services & critical_services
    if broken_critical:
        deadline_text = retention_deadline.strip() or t("essentials.ring.no_deadline", lang=Lang.VI)
        return RingPromotionResult(
            target_ring=LifecycleRing.STABLE,
            blocked=True,
            retained_version=previous_stable_version,
            retention_deadline=retention_deadline.strip(),
            warning_vi=t(
                "essentials.ring.retained_with_deadline",
                lang=Lang.VI,
                services=", ".join(sorted(broken_critical)),
                deadline=deadline_text,
            ),
        )

    return RingPromotionResult(
        target_ring=LifecycleRing.STABLE,
        blocked=False,
        retained_version=None,
        retention_deadline="",
        warning_vi="",
    )


def is_retention_expired(deadline: str, today: str) -> bool:
    """Hạn giữ bản cũ đã hết chưa (APP11-017). Hạn RỖNG → ``True`` NGAY (fail
    -closed: không có "giữ mãi" ngầm). Ngày hỏng định dạng ISO (``YYYY-MM-DD``)
    cũng coi là hết hạn — KHÔNG đoán, KHÔNG giữ khi không đọc được ngày."""

    text = deadline.strip()
    if not text:
        return True
    try:
        deadline_date = date.fromisoformat(text)
        today_date = date.fromisoformat(today.strip())
    except ValueError:
        return True
    return today_date > deadline_date
