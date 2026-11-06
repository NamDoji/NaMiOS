"""Cài/đổi driver có GIAO DỊCH (E08-005).

stage → check source/quyền → snapshot → apply → function-test → commit | rollback.
Hỏng TRƯỚC commit → rollback về trạng thái cũ (test D03: cài lỗi rollback trả máy in/
card mạng về cũ); KHÔNG để nửa vời. Thao tác kernel/firmware cần IT + reboot (tham số
``privileged`` chỉ để đánh dấu — thực thi thật do action broker SYS, chưa nối = ngoài I0).
"""

from __future__ import annotations

from namios_e08 import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_e08._types import InstallResult, InstallStage
from namios_i18n import Lang, t

__all__ = ["run_install_transaction"]


def run_install_transaction(
    *,
    source_ok: bool,
    snapshot_ok: bool,
    apply_ok: bool,
    function_ok: bool,
) -> InstallResult:
    """Chạy giao dịch cài driver (E08-005), fail-closed:

    - Nguồn/quyền không đạt → FAILED ở ``check_source`` (chưa đụng hệ → không rollback).
    - Không chụp được snapshot → FAILED ở ``snapshot`` (KHÔNG apply khi chưa có đường lùi).
    - apply hỏng HOẶC function-test fail → ROLLBACK (đã có snapshot) → về trạng thái cũ.
    - Tất cả đạt → COMMIT.
    """

    if not source_ok:
        return InstallResult(
            committed=False,
            rolled_back=False,
            final_stage=InstallStage.FAILED,
            reason_vi=t("e08.install.source_fail", lang=Lang.VI),
        )
    if not snapshot_ok:
        return InstallResult(
            committed=False,
            rolled_back=False,
            final_stage=InstallStage.FAILED,
            reason_vi=t("e08.install.snapshot_fail", lang=Lang.VI),
        )
    if not apply_ok:
        return InstallResult(
            committed=False,
            rolled_back=True,
            final_stage=InstallStage.ROLLBACK,
            reason_vi=t("e08.install.apply_rollback", lang=Lang.VI),
        )
    if not function_ok:
        return InstallResult(
            committed=False,
            rolled_back=True,
            final_stage=InstallStage.ROLLBACK,
            reason_vi=t("e08.install.functest_rollback", lang=Lang.VI),
        )
    return InstallResult(
        committed=True,
        rolled_back=False,
        final_stage=InstallStage.COMMIT,
        reason_vi=t("e08.install.committed", lang=Lang.VI),
    )
