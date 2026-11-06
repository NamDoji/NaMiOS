"""Chứng nhận thiết bị per-function + state machine (ODC-022/047).

Vòng đời MỖI chức năng: ``reported → lab_tested → pilot_verified → published``
(+ ``needs_retest`` khi trigger). Bất biến trung thực:
- CHỈ bằng chứng THẬT nâng trạng thái: ``lab_test`` (đội kiểm, testcase + ảnh bản in
  che dữ liệu) và ``pilot_signoff`` (người nghiệp vụ duyệt). ``community_report``
  ("máy tôi in được") và ``ai_guess`` KHÔNG BAO GIỜ nâng (ODC-047/048).
- Không nhảy cóc: chưa lab thì không pilot; chưa pilot thì không published.
- Mỗi chức năng RIÊNG, không suy từ model cùng hãng (ODC-022) — cấu trúc không cho
  phép diễn đạt "suy từ model khác".
- Hỗ trợ (``is_function_supported``) chỉ True khi ``PUBLISHED``.
"""

from __future__ import annotations

from collections.abc import Iterable

from namios_odc._types import CertFunction, CertState, DeviceCert, EvidenceKind

__all__ = [
    "PROMOTING_EVIDENCE",
    "function_state",
    "advance",
    "can_publish",
    "publish",
    "is_function_supported",
    "with_needs_retest",
]

#: Bằng chứng ĐƯỢC nâng trạng thái (ODC-047). Mọi nguồn khác (cộng đồng/AI) = không.
PROMOTING_EVIDENCE: frozenset[EvidenceKind] = frozenset(
    {EvidenceKind.LAB_TEST, EvidenceKind.PILOT_SIGNOFF}
)


def function_state(cert: DeviceCert, func: CertFunction) -> CertState | None:
    """Trạng thái chứng nhận một chức năng (ODC-022). Không khai = ``None`` (chưa có
    dữ liệu — KHÔNG mặc định 'reported', KHÔNG suy từ chức năng/ model khác)."""

    return cert.functions.get(func)


def advance(current: CertState | None, evidence: EvidenceKind) -> CertState:
    """Nâng trạng thái theo bằng chứng (ODC-047), fail-closed:

    - ``community_report``/``ai_guess`` → KHÔNG nâng (giữ nguyên; chưa có gì → REPORTED).
    - ``lab_test`` → chỉ ``reported``/``needs_retest``/chưa-có → ``lab_tested``.
    - ``pilot_signoff`` → chỉ ``lab_tested`` → ``pilot_verified`` (không nhảy cóc).
    - ``published`` KHÔNG đạt được ở đây — phải qua ``publish()`` (ODC-047).
    """

    cur = current if current is not None else CertState.REPORTED

    if evidence not in PROMOTING_EVIDENCE:
        # Cộng đồng/AI chỉ ghi nhận "đã báo", không bao giờ vượt reported.
        return cur if current is not None else CertState.REPORTED

    if evidence is EvidenceKind.LAB_TEST:
        if cur in (CertState.REPORTED, CertState.NEEDS_RETEST):
            return CertState.LAB_TESTED
        return cur  # đã ≥ lab_tested → re-test không hạ/không nhảy

    # pilot_signoff: chỉ từ lab_tested mới lên pilot_verified.
    if cur is CertState.LAB_TESTED:
        return CertState.PILOT_VERIFIED
    return cur


def can_publish(current: CertState | None) -> bool:
    """Đủ điều kiện công bố hỗ trợ chưa (ODC-047). CHỈ khi đã ``pilot_verified``."""

    return current is CertState.PILOT_VERIFIED


def publish(current: CertState | None) -> CertState:
    """Công bố (ODC-047). Chỉ ``pilot_verified`` → ``published``; còn lại giữ nguyên
    (fail-closed, không nâng dối)."""

    return CertState.PUBLISHED if can_publish(current) else (current or CertState.REPORTED)


def is_function_supported(cert: DeviceCert, func: CertFunction) -> bool:
    """Chức năng đã CÔNG BỐ hỗ trợ chưa (ODC-022/041). True chỉ khi ``PUBLISHED`` —
    'thấy thiết bị'/'đã báo'/'đã lab' đều CHƯA phải 'hỗ trợ'."""

    return function_state(cert, func) is CertState.PUBLISHED


def with_needs_retest(cert: DeviceCert, funcs: Iterable[CertFunction]) -> DeviceCert:
    """Đánh dấu các chức năng phải kiểm lại (ODC-033). Trả hồ sơ MỚI (bất biến)."""

    updated = dict(cert.functions)
    for f in funcs:
        updated[f] = CertState.NEEDS_RETEST
    return DeviceCert(
        model=cert.model,
        firmware=cert.firmware,
        functions=updated,
        test_dates=cert.test_dates,
    )
