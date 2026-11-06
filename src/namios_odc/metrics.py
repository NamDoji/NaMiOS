"""Chỉ số thành công TRUNG THỰC (ODC-048).

Báo RIÊNG từng số + mẫu số + nguồn: ``user_weighted_device_coverage`` (người pilot
đủ workflow thiết bị / tổng pilot), ``workflow_coverage``, ``office_fidelity_pass``,
``windows_dependency``. Bất biến: KHÔNG lấy "số model trong catalog" làm "số model
đã hỗ trợ" — ``models_published`` đếm model có ≥1 chức năng ``PUBLISHED``, luôn ≤
``models_surveyed`` (ODC-048 nghiệm thu: dashboard không coi 100 catalog = 100 hỗ trợ).
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_odc._types import CertState, CoverageMetrics, DeviceCert

__all__ = [
    "safe_fraction",
    "user_weighted_coverage",
    "published_model_count",
    "build_coverage",
]


def safe_fraction(numerator: int, denominator: int) -> float:
    """Tỉ lệ an toàn (ODC-048): mẫu ≤ 0 → 0.0 (KHÔNG mặc định 1.0/100%); kẹp [0,1];
    tử > mẫu → 1.0 (không bịa >100%)."""

    if denominator <= 0 or numerator <= 0:
        return 0.0
    return min(1.0, numerator / denominator)


def user_weighted_coverage(users_with_required_workflows: int, total_pilot_users: int) -> float:
    """Độ phủ theo NGƯỜI DÙNG (ODC-048): người pilot đủ workflow thiết bị bắt buộc /
    tổng người pilot. Chưa có pilot (mẫu 0) → 0.0, KHÔNG phải 100%."""

    return safe_fraction(users_with_required_workflows, total_pilot_users)


def published_model_count(certs: Iterable[DeviceCert]) -> int:
    """Số model ĐÃ CÔNG BỐ hỗ trợ (ODC-048): có ≥1 chức năng ``PUBLISHED``. KHÁC
    hẳn số model khảo sát/catalog — 'thấy/đã-báo/đã-lab' KHÔNG tính."""

    n = 0
    for cert in certs:
        if any(state is CertState.PUBLISHED for state in cert.functions.values()):
            n += 1
    return n


def build_coverage(
    *,
    pilot_users_with_required: int,
    pilot_users_total: int,
    workflows_verified: int,
    workflows_required: int,
    fidelity_fixtures_pass: int,
    fidelity_fixtures_measured: int,
    workflows_need_windows: int,
    models_surveyed: int,
    certs: Iterable[DeviceCert],
    data_loss_incidents: int = 0,
) -> CoverageMetrics:
    """Dựng báo cáo độ phủ trung thực (ODC-048). ``models_published`` suy từ ``certs``
    (PUBLISHED thật), KHÔNG lấy ``models_surveyed``. Mọi tỉ lệ dùng mẫu số thật."""

    published = published_model_count(certs)
    # Bất biến: đã-công-bố KHÔNG BAO GIỜ vượt đã-khảo-sát (kể cả khi khảo-sát ≤ 0 —
    # chưa khảo sát model nào thì không thể "đã công bố" model nào; fail-closed).
    surveyed = max(0, models_surveyed)
    published = min(published, surveyed)
    return CoverageMetrics(
        user_weighted_device_coverage=user_weighted_coverage(
            pilot_users_with_required, pilot_users_total
        ),
        pilot_users_total=max(0, pilot_users_total),
        workflow_coverage=safe_fraction(workflows_verified, workflows_required),
        office_fidelity_pass=safe_fraction(fidelity_fixtures_pass, fidelity_fixtures_measured),
        windows_dependency=safe_fraction(workflows_need_windows, workflows_required),
        models_surveyed=max(0, models_surveyed),
        models_published=published,
        data_loss_incidents=max(0, data_loss_incidents),
    )
