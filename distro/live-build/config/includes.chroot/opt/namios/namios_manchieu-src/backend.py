"""``namios_manchieu.backend`` — lớp IO THẬT: tìm ``kscreen-doctor`` + gọi nó
qua ``run_argv`` (argv-only, ``shell=False``, có timeout — WP8, xem
``namios_security.safe_exec``). KHÔNG chứa quyết định "chế độ nào làm gì" —
mọi quyết định đó nằm ở ``namios_manchieu.display`` (Python thuần, test được
không cần subprocess/PySide6). File này CHỈ: (1) đọc trạng thái output hiện
tại (``read_outputs`` — read-only, KHÔNG cần quyền quản trị), (2) áp 1 chế độ
(``apply_mode`` — đổi hiển thị THẬT, đó chính là mục đích của app, KHÔNG cần
``pkexec``: đổi cấu hình output của phiên đăng nhập hiện tại là hành động
người dùng thường có quyền tự làm, giống khi tự mở System Settings > Display
và bấm Apply — KHÔNG phải hành động toàn hệ thống cần quyền root)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field

from namios_manchieu import display

from namios_security import ExecPolicyError, run_argv

__all__ = ["BackendResult", "kscreen_doctor_bin", "read_outputs", "apply_mode"]

_READ_TIMEOUT_SECONDS = 10.0
_APPLY_TIMEOUT_SECONDS = 15.0


@dataclass(frozen=True)
class BackendResult:
    """Kết quả một lần đọc/áp dụng. ``message`` LUÔN là câu thân thiện hiển
    thị thẳng cho người dùng (không có mã lỗi kỹ thuật trần nào kèm riêng)."""

    success: bool
    message: str
    outputs: tuple[display.OutputInfo, ...] = field(default_factory=tuple)


def kscreen_doctor_bin() -> str | None:
    """Đường dẫn tuyệt đối tới ``kscreen-doctor`` nếu có trên máy, ``None``
    nếu không — ``run_argv``/``ArgvSafeExec`` YÊU CẦU argv[0] là đường dẫn
    tuyệt đối đã xác nhận tồn tại (xem ``namios_security.safe_exec``), nên
    KHÔNG thể truyền thẳng tên trần ``"kscreen-doctor"``."""

    return shutil.which("kscreen-doctor")


def read_outputs() -> BackendResult:
    """Đọc danh sách output hiện tại (``kscreen-doctor -o``) — READ-ONLY,
    không đổi gì trên máy. Thất bại (thiếu binary/timeout/parse lỗi) trả
    ``success=False`` với câu thân thiện, KHÔNG raise ra ngoài (fail-safe
    tuyệt đối cho tầng UI gọi hàm này trong luồng nền)."""

    bin_path = kscreen_doctor_bin()
    if bin_path is None:
        return BackendResult(
            success=False,
            message=(
                "Không tìm thấy kscreen-doctor trên máy này — cần gói libkscreen-bin "
                "(bình thường đi kèm gói kscreen đã cài sẵn)."
            ),
        )
    try:
        result = run_argv([bin_path, "-o"], timeout=_READ_TIMEOUT_SECONDS)
    except ExecPolicyError as exc:
        return BackendResult(
            success=False, message=f"Không đọc được danh sách màn hình: {exc.reason_vi}"
        )

    if result.returncode != 0:
        stderr_text = result.stderr.decode("utf-8", "replace").strip()
        detail = stderr_text or "(không có output)"
        return BackendResult(
            success=False,
            message=f"kscreen-doctor trả mã lỗi {result.returncode}.\n{detail}",
        )

    stdout_text = result.stdout.decode("utf-8", "replace")
    try:
        outputs = display.parse_outputs(stdout_text)
    except Exception as exc:  # noqa: BLE001 - fail-safe tuyệt đối, output lạ không được làm sập app
        return BackendResult(
            success=False, message=f"Không đọc hiểu được output của kscreen-doctor: {exc}"
        )
    if not outputs:
        return BackendResult(success=False, message=display.NO_OUTPUTS_MESSAGE)
    return BackendResult(success=True, message="", outputs=tuple(outputs))


def apply_mode(mode: str) -> BackendResult:
    """Đọc trạng thái mới nhất RỒI áp 1 chế độ (``display.plan`` + MỘT lần
    gọi ``kscreen-doctor`` atomic — xem ``display`` docstring điểm (3)).
    Luôn đọc lại trạng thái ngay trước khi áp — KHÔNG dùng trạng thái cũ từ
    một lần "Làm mới" trước đó, tránh áp lệnh dựa trên output đã rút cáp."""

    bin_path = kscreen_doctor_bin()
    if bin_path is None:
        return BackendResult(
            success=False, message="Không tìm thấy kscreen-doctor trên máy này."
        )

    current = read_outputs()
    if not current.success:
        return current

    try:
        display_plan = display.plan(mode, current.outputs)
    except display.DisplayError as exc:
        return BackendResult(success=False, message=exc.message, outputs=current.outputs)

    argv = [bin_path, *display_plan.tokens]
    try:
        result = run_argv(argv, timeout=_APPLY_TIMEOUT_SECONDS)
    except ExecPolicyError as exc:
        return BackendResult(
            success=False, message=f"Không áp dụng được: {exc.reason_vi}", outputs=current.outputs
        )

    stdout_text = result.stdout.decode("utf-8", "replace").strip()
    stderr_text = result.stderr.decode("utf-8", "replace").strip()
    if result.returncode != 0:
        combined = (stdout_text + ("\n" + stderr_text if stderr_text else "")).strip()
        detail = combined or "(không có output)"
        return BackendResult(
            success=False,
            message=f"kscreen-doctor trả mã lỗi {result.returncode}.\n{detail}",
            outputs=current.outputs,
        )
    return BackendResult(
        success=True,
        message=stdout_text or f"Đã áp dụng '{display.MODE_LABELS_VI[mode]}'.",
        outputs=current.outputs,
    )
