"""ECO-003 — Trạng thái công bố (``PublishedStatus``) suy ra từ 7 nấc
(ECO-001) + GATE "downloadable_only/launches_only KHÔNG BAO GIỜ usable" +
GATE "workflow_verified CHỈ khi có evidence nộp/nhận".
ECO-004 — hai trường độc lập ``tested_by_namios``/``officially_supported_by_vendor``
(xem ``models.ServiceEntry``; module này chỉ cung cấp phát biểu bất biến).
ECO-015 — ``WindowsMode`` (5 chế độ) + tỉ lệ không-phụ-thuộc-Windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from namios_eco.workflow import StepOutcome, WorkflowStep, WorkflowStepName
from namios_i18n import Lang, t

# NOTE (i18n, 03/11/2026): ``reasons_vi`` dưới đây đi qua ``namios_i18n.t``
# (nhóm key ``eco.status.reason.*``, đã seed VI/EN — xem docs/specs/I18N.md)
# nhưng LUÔN ép ``lang=Lang.VI`` — một nguồn sự thật chung, KHÔNG đổi theo
# ngôn ngữ hiển thị CLI/UI. ``PublishedStatusResult.reasons_vi`` là trường
# DỮ LIỆU đặt tên theo quy ước ``_vi`` (giống ``ErrorBody.message_vi`` ở
# M1-INTERFACES §1/§3) — tiêu thụ bởi các WP khác qua ``validator.py``/
# envelope JSON (``namios_cli``), LUÔN tiếng Việt bất kể ``--lang``.

__all__ = [
    "PublishedStatus",
    "NEVER_USABLE_STATUSES",
    "USABLE_STATUSES",
    "is_usable",
    "WindowsMode",
    "WINDOWS_DEPENDENT_MODES",
    "is_windows_free",
    "PublishedStatusResult",
    "derive_published_status",
]


class PublishedStatus(str, Enum):
    """Trạng thái công bố (ECO-003). Giá trị chuỗi là hợp đồng ổn định dùng
    trong catalog/evidence — KHÔNG đổi sau khi phát hành."""

    NOT_INVENTORIED = "not_inventoried"
    DOWNLOADABLE_ONLY = "downloadable_only"
    LAUNCHES_ONLY = "launches_only"
    PARTIAL_WORKFLOW = "partial_workflow"
    WORKFLOW_VERIFIED = "workflow_verified"
    BLOCKED_EXTERNAL_DEPENDENCY = "blocked_external_dependency"
    UNSUPPORTED = "unsupported"
    REVOKED = "revoked"


#: GATE (FACT ECO-003): "downloadable_only và launches_only TUYỆT ĐỐI không
#: hiển thị là 'dùng được'" — không có cấu hình/ngoại lệ nào được bật usable
#: cho hai trạng thái này. Giữ hằng số này ở đây để mọi nơi (CLI/UI tương
#: lai) tham chiếu MỘT nguồn sự thật, không tự định nghĩa lại.
NEVER_USABLE_STATUSES: frozenset[PublishedStatus] = frozenset(
    {PublishedStatus.DOWNLOADABLE_ONLY, PublishedStatus.LAUNCHES_ONLY}
)

#: Trạng thái được phép hiển thị là "có thể dùng" — toàn phần
#: (``workflow_verified``) hoặc một phần có công bố rõ giới hạn
#: (``partial_workflow``). Tất cả trạng thái khác (gồm toàn bộ
#: ``NEVER_USABLE_STATUSES``) đều KHÔNG usable.
USABLE_STATUSES: frozenset[PublishedStatus] = frozenset(
    {PublishedStatus.WORKFLOW_VERIFIED, PublishedStatus.PARTIAL_WORKFLOW}
)


def is_usable(status: PublishedStatus) -> bool:
    """GATE ECO-003. Trả ``True`` CHỈ cho trạng thái trong ``USABLE_STATUSES``.
    Đặc biệt: luôn trả ``False`` cho mọi phần tử của ``NEVER_USABLE_STATUSES``
    (bất biến — có test adversarial canh giữ)."""

    if status in NEVER_USABLE_STATUSES:
        return False
    return status in USABLE_STATUSES


class WindowsMode(str, Enum):
    """5 chế độ Windows hợp lệ (ECO-015)."""

    NATIVE_LINUX = "native_linux"
    WEB_LINUX = "web_linux"
    WINE = "wine"
    REMOTE_WINDOWS = "remote_windows"
    WINDOWS_VM = "windows_vm"


#: Các mode vẫn còn phụ thuộc Windows ở lớp nào đó (ECO-015 §4.4: nếu workflow
#: bắt buộc chỉ đạt qua các mode này, "nhóm đó CHƯA đạt mục tiêu loại bỏ hoàn
#: toàn Windows" dù NaMiOS có thể là desktop chính).
WINDOWS_DEPENDENT_MODES: frozenset[WindowsMode] = frozenset(
    {WindowsMode.WINE, WindowsMode.REMOTE_WINDOWS, WindowsMode.WINDOWS_VM}
)


def is_windows_free(mode: WindowsMode) -> bool:
    """``True`` nếu mode KHÔNG phụ thuộc Windows ở bất kỳ lớp nào
    (``native_linux``/``web_linux``)."""

    return mode not in WINDOWS_DEPENDENT_MODES


@dataclass(frozen=True)
class PublishedStatusResult:
    status: PublishedStatus
    reasons_vi: tuple[str, ...]


def _by_name(steps: tuple[WorkflowStep, ...]) -> dict[WorkflowStepName, WorkflowStep]:
    return {s.name: s for s in steps}


def derive_published_status(steps: tuple[WorkflowStep, ...]) -> PublishedStatusResult:
    """Suy ra ``PublishedStatus`` từ kết quả 7 nấc (ECO-001), theo đúng GATE
    ECO-003/ECO-016/ECO-017.

    Giả định ``steps`` đã qua ``workflow.validate_workflow_structure`` (đủ 7
    nấc, đúng tên, đúng thứ tự) — hàm này KHÔNG tự kiểm lại kết cấu.

    KHÔNG tự suy ra ``revoked``: thu hồi là quyết định quản trị độc lập (như
    catalog revocation của WP4), gán trực tiếp lên
    ``ServiceEntry.published_status`` — không qua pipeline suy luận từ bước
    kỹ thuật này (một chứng chỉ có thể bị revoke dù kỹ thuật vẫn pass, ví dụ
    vì phát hiện sai dữ liệu nghiêm trọng)."""

    by_name = _by_name(steps)
    discover = by_name[WorkflowStepName.DISCOVER]
    acquire = by_name[WorkflowStepName.ACQUIRE]
    install = by_name[WorkflowStepName.INSTALL_OR_OPEN]
    authenticate = by_name[WorkflowStepName.AUTHENTICATE]
    submit = by_name[WorkflowStepName.SUBMIT_OR_EXPORT]
    verify = by_name[WorkflowStepName.VERIFY_RESULT]

    if all(s.outcome == StepOutcome.NOT_RUN for s in steps):
        return PublishedStatusResult(
            PublishedStatus.NOT_INVENTORIED,
            (t("eco.status.reason.not_inventoried", lang=Lang.VI),),
        )

    if discover.outcome == StepOutcome.FAIL:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            (t("eco.status.reason.discover_failed", lang=Lang.VI),),
        )

    if acquire.outcome == StepOutcome.FAIL:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            (t("eco.status.reason.acquire_failed", lang=Lang.VI),),
        )

    if install.outcome == StepOutcome.FAIL:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            (t("eco.status.reason.install_failed", lang=Lang.VI),),
        )

    # ECO-016: BẤT KỲ nấc nào bị BLOCKED vì phụ thuộc ngoài (gồm cả
    # discover/acquire — vd host không kết nối được .gov.vn, thiếu sandbox/
    # quyền/token) => blocked_external_dependency (is_usable=False). "blocked"
    # trung thực hơn "fail" khi nguyên nhân là bên ngoài, không phải lỗi kỹ
    # thuật của chính workflow. Lý do CHỈ nêu đúng các nấc bị blocked —
    # TUYỆT ĐỐI không khẳng định các nấc sau đã pass khi chúng chưa chạy.
    blocked = tuple(s for s in steps if s.outcome == StepOutcome.BLOCKED)
    if blocked:
        return PublishedStatusResult(
            PublishedStatus.BLOCKED_EXTERNAL_DEPENDENCY,
            tuple(
                t("eco.status.reason.step_blocked", lang=Lang.VI, step=s.name.value)
                for s in blocked
            ),
        )

    chain = (install, authenticate, by_name[WorkflowStepName.EXECUTE], submit, verify)
    failed = tuple(s for s in chain if s.outcome == StepOutcome.FAIL)
    if failed:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            tuple(
                t("eco.status.reason.step_failed", lang=Lang.VI, step=s.name.value) for s in failed
            ),
        )

    if acquire.outcome == StepOutcome.PASS and install.outcome not in (
        StepOutcome.PASS,
        StepOutcome.NOT_APPLICABLE,
    ):
        return PublishedStatusResult(
            PublishedStatus.DOWNLOADABLE_ONLY,
            (t("eco.status.reason.downloadable_only", lang=Lang.VI),),
        )

    if (
        install.outcome in (StepOutcome.PASS, StepOutcome.NOT_APPLICABLE)
        and authenticate.outcome == StepOutcome.NOT_RUN
    ):
        return PublishedStatusResult(
            PublishedStatus.LAUNCHES_ONLY,
            (t("eco.status.reason.launches_only", lang=Lang.VI),),
        )

    if submit.outcome == StepOutcome.NOT_RUN or verify.outcome == StepOutcome.NOT_RUN:
        return PublishedStatusResult(
            PublishedStatus.PARTIAL_WORKFLOW,
            (t("eco.status.reason.partial_pending_submit_verify", lang=Lang.VI),),
        )

    if verify.outcome == StepOutcome.PASS and submit.outcome in (
        StepOutcome.PASS,
        StepOutcome.NOT_APPLICABLE,
    ):
        missing_evidence: list[str] = []
        if verify.outcome == StepOutcome.PASS and not (verify.evidence_ref or "").strip():
            missing_evidence.append("verify_result")
        if submit.outcome == StepOutcome.PASS and not (submit.evidence_ref or "").strip():
            missing_evidence.append("submit_or_export")

        if not missing_evidence:
            return PublishedStatusResult(
                PublishedStatus.WORKFLOW_VERIFIED,
                (t("eco.status.reason.workflow_verified", lang=Lang.VI),),
            )
        return PublishedStatusResult(
            PublishedStatus.PARTIAL_WORKFLOW,
            (
                t(
                    "eco.status.reason.partial_missing_evidence",
                    lang=Lang.VI,
                    missing=", ".join(missing_evidence),
                ),
            ),
        )

    # Mọi tổ hợp còn lại (vd verify not_applicable) không đủ rõ để khẳng
    # định đã xong toàn luồng — giữ an toàn ở partial, không tự nâng cấp.
    return PublishedStatusResult(
        PublishedStatus.PARTIAL_WORKFLOW,
        (t("eco.status.reason.partial_unclear", lang=Lang.VI),),
    )
