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
            ("Chưa nấc nào được chạy (toàn bộ not_run) — chưa khảo sát.",),
        )

    if discover.outcome == StepOutcome.FAIL:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            ("Nấc discover fail — không tìm được/không còn nguồn chính thức.",),
        )

    if acquire.outcome == StepOutcome.FAIL:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            ("Nấc acquire fail thật (không phải blocked bên ngoài).",),
        )

    if install.outcome == StepOutcome.FAIL:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            ("Nấc install_or_open fail thật (cài/mở không thành công).",),
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
                f"Nấc '{s.name.value}' blocked vì phụ thuộc ngoài "
                "(vd thiếu kết nối/sandbox/quyền/token) — ECO-016."
                for s in blocked
            ),
        )

    chain = (install, authenticate, by_name[WorkflowStepName.EXECUTE], submit, verify)
    failed = tuple(s for s in chain if s.outcome == StepOutcome.FAIL)
    if failed:
        return PublishedStatusResult(
            PublishedStatus.UNSUPPORTED,
            tuple(f"Nấc '{s.name.value}' fail thật." for s in failed),
        )

    if acquire.outcome == StepOutcome.PASS and install.outcome not in (
        StepOutcome.PASS,
        StepOutcome.NOT_APPLICABLE,
    ):
        return PublishedStatusResult(
            PublishedStatus.DOWNLOADABLE_ONLY,
            (
                "Chỉ mới tải/truy cập được nguồn (acquire pass) — chưa xác nhận "
                "mở/cài được (install_or_open chưa pass). GATE: KHÔNG hiển thị "
                "trạng thái này là dùng được.",
            ),
        )

    if (
        install.outcome in (StepOutcome.PASS, StepOutcome.NOT_APPLICABLE)
        and authenticate.outcome == StepOutcome.NOT_RUN
    ):
        return PublishedStatusResult(
            PublishedStatus.LAUNCHES_ONLY,
            (
                "Mở/cài được (install_or_open) nhưng chưa thử đăng nhập/tác vụ kế "
                "tiếp. GATE: KHÔNG hiển thị trạng thái này là dùng được.",
            ),
        )

    if submit.outcome == StepOutcome.NOT_RUN or verify.outcome == StepOutcome.NOT_RUN:
        return PublishedStatusResult(
            PublishedStatus.PARTIAL_WORKFLOW,
            ("Đã qua authenticate/execute nhưng chưa tới submit_or_export/verify_result.",),
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
                ("submit_or_export + verify_result đều pass và có evidence_ref thật.",),
            )
        return PublishedStatusResult(
            PublishedStatus.PARTIAL_WORKFLOW,
            (
                "submit_or_export/verify_result pass nhưng THIẾU evidence_ref ở: "
                f"{', '.join(missing_evidence)} — GATE ECO-003 không cho "
                "workflow_verified khi thiếu bằng chứng nộp/nhận thật.",
            ),
        )

    # Mọi tổ hợp còn lại (vd verify not_applicable) không đủ rõ để khẳng
    # định đã xong toàn luồng — giữ an toàn ở partial, không tự nâng cấp.
    return PublishedStatusResult(
        PublishedStatus.PARTIAL_WORKFLOW,
        (
            "Tổ hợp kết quả không khớp nhánh rõ ràng khác (vd verify_result "
            "not_applicable) — giữ partial_workflow để an toàn, không tự suy "
            "ra workflow_verified khi chưa chắc chắn.",
        ),
    )
