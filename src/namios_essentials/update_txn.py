"""Cập nhật giao dịch cho NaMi Update Center (APP11-016) — BỌC
``namios_e08.run_install_transaction``, KHÔNG dựng lại máy trạng thái giao dịch
thứ hai. Chuỗi đầy đủ: stage → kiểm chữ ký/dung lượng/PIN → snapshot → apply →
health check → commit/rollback. Ba kiểm thêm (chữ ký/dung lượng/PIN) chạy
TRƯỚC và gộp vào ``source_ok`` của ``install_txn`` — thiếu MỘT trong ba thì
coi như nguồn/quyền không đạt, dừng trước khi đụng hệ, giống hệt ngữ nghĩa
``check_source`` gốc.

Tách dữ liệu người dùng (APP11-016 nghiệm thu: "ngắt điện/mất mạng/hết ổ ở ba
điểm không mất file"): hàm giao dịch ở đây KHÔNG nhận, không đọc, không ghi bất
kỳ đường dẫn tài liệu cá nhân nào — ``EssentialsUpdateResult.user_data_touched``
luôn ``False`` theo đúng cấu trúc chữ ký hàm (không có tham số nào trỏ tới vùng
dữ liệu người dùng), không phải một cờ caller có thể tự ý bật.

``WEB_SHORTCUT`` không có gói để cài/rollback phía NaMiOS (APP11-019/032) — gọi
hàm này cho kênh đó là lỗi dùng sai API, trả ngay ``FAILED`` thay vì giả vờ chạy
một giao dịch không tồn tại.
"""

from __future__ import annotations

from namios_e08 import InstallResult, InstallStage, run_install_transaction
from namios_essentials import _i18n as _i18n  # noqa: F401  (đăng ký catalog i18n)
from namios_essentials._types import EssentialsUpdateResult, UpdateChannel
from namios_essentials.update_center import recovery_guidance
from namios_i18n import Lang, t

__all__ = ["run_essentials_update_transaction"]


def run_essentials_update_transaction(
    channel: UpdateChannel,
    *,
    sign_ok: bool,
    space_ok: bool,
    pin_ok: bool,
    snapshot_ok: bool,
    apply_ok: bool,
    health_ok: bool,
) -> EssentialsUpdateResult:
    """Chạy giao dịch cập nhật một kênh cài-được (APP11-016). ``sign_ok``/
    ``space_ok``/``pin_ok`` gộp AND thành ``source_ok`` của
    ``run_install_transaction`` — hỏng bất kỳ cái nào → dừng ở
    ``check_source``, CHƯA đụng hệ (chưa snapshot/apply)."""

    if channel is UpdateChannel.WEB_SHORTCUT:
        install = InstallResult(
            committed=False,
            rolled_back=False,
            final_stage=InstallStage.FAILED,
            reason_vi=t("essentials.update_txn.web_shortcut_not_installable", lang=Lang.VI),
        )
        return EssentialsUpdateResult(
            channel=channel,
            install=install,
            user_data_touched=False,
            recovery_message_vi=recovery_guidance(channel, None),
        )

    source_ok = sign_ok and space_ok and pin_ok
    install = run_install_transaction(
        source_ok=source_ok,
        snapshot_ok=snapshot_ok,
        apply_ok=apply_ok,
        function_ok=health_ok,
    )
    return EssentialsUpdateResult(
        channel=channel,
        install=install,
        user_data_touched=False,
        recovery_message_vi=recovery_guidance(channel, install),
    )
