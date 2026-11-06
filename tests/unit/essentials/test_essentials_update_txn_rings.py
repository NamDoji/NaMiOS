"""APP11-016 (cập nhật giao dịch) + APP11-017 (update rings). Bám E11-05 (gói
Office lỗi sau nâng cấp → rollback, tài liệu người dùng không mất)."""

from __future__ import annotations

import inspect

from namios_e08 import InstallStage
from namios_essentials import UpdateChannel, run_essentials_update_transaction
from namios_essentials.rings import evaluate_ring_promotion, is_retention_expired
from namios_essentials.update_txn import run_essentials_update_transaction as run_txn
from namios_odc import LifecycleRing

UC = UpdateChannel


def _ok_kwargs(**overrides: bool) -> dict[str, bool]:
    base = dict(
        sign_ok=True,
        space_ok=True,
        pin_ok=True,
        snapshot_ok=True,
        apply_ok=True,
        health_ok=True,
    )
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# E11-05 / APP11-016 — cập nhật giao dịch                                      #
# --------------------------------------------------------------------------- #


def test_all_stages_pass_commits() -> None:
    result = run_essentials_update_transaction(UC.OFFICE, **_ok_kwargs())
    assert result.install.committed is True
    assert result.install.final_stage is InstallStage.COMMIT
    assert result.user_data_touched is False


def test_e11_05_health_check_fail_rolls_back_office() -> None:
    # Gói Office lỗi sau nâng cấp (health check fail) → rollback, KHÔNG nửa vời.
    result = run_essentials_update_transaction(UC.OFFICE, **_ok_kwargs(health_ok=False))
    assert result.install.rolled_back is True
    assert result.install.committed is False
    assert result.user_data_touched is False  # tài liệu người dùng không mất
    assert "trước" in result.recovery_message_vi or "rollback" in result.recovery_message_vi.lower()


def test_apply_fail_also_rolls_back() -> None:
    result = run_essentials_update_transaction(UC.BROWSER, **_ok_kwargs(apply_ok=False))
    assert result.install.rolled_back is True


def test_missing_signature_stops_before_touching_system() -> None:
    result = run_essentials_update_transaction(UC.OFFICE, **_ok_kwargs(sign_ok=False))
    assert result.install.committed is False
    assert result.install.rolled_back is False
    assert result.install.final_stage is InstallStage.FAILED


def test_missing_disk_space_stops_before_touching_system() -> None:
    result = run_essentials_update_transaction(UC.OS, **_ok_kwargs(space_ok=False))
    assert result.install.final_stage is InstallStage.FAILED
    assert result.install.rolled_back is False


def test_missing_pin_stops_before_touching_system() -> None:
    result = run_essentials_update_transaction(UC.WINE_RECIPE, **_ok_kwargs(pin_ok=False))
    assert result.install.final_stage is InstallStage.FAILED


def test_user_data_touched_is_structurally_always_false() -> None:
    # APP11-016: hàm không nhận bất kỳ tham số đường dẫn dữ liệu người dùng nào
    # — kiểm CẤU TRÚC chữ ký hàm, không chỉ giá trị trả về.
    params = set(inspect.signature(run_txn).parameters)
    assert params.isdisjoint({"user_data_path", "document_path", "home_dir", "user_files"})
    for result in (
        run_essentials_update_transaction(UC.OFFICE, **_ok_kwargs()),
        run_essentials_update_transaction(UC.OFFICE, **_ok_kwargs(health_ok=False)),
    ):
        assert result.user_data_touched is False


def test_web_shortcut_has_no_installable_package() -> None:
    # APP11-019/032: web service không có gói để cài/rollback phía NaMiOS.
    result = run_essentials_update_transaction(UC.WEB_SHORTCUT, **_ok_kwargs())
    assert result.install.committed is False
    assert result.install.rolled_back is False
    assert result.install.final_stage is InstallStage.FAILED


# --------------------------------------------------------------------------- #
# APP11-017 — update rings                                                     #
# --------------------------------------------------------------------------- #


def test_browser_breaking_zalo_web_in_lab_blocks_stable_promotion_with_deadline() -> None:
    result = evaluate_ring_promotion(
        candidate_version="121.0",
        previous_stable_version="120.0",
        lab_regression_failed_services=frozenset({"zalo_web"}),
        critical_services=frozenset({"zalo_web", "whatsapp_web"}),
        retention_deadline="2026-11-20",
    )
    assert result.blocked is True
    assert result.target_ring is LifecycleRing.STABLE
    assert result.retained_version == "120.0"
    assert result.retention_deadline == "2026-11-20"
    assert result.warning_vi  # cảnh báo rủi ro bảo mật không rỗng


def test_non_critical_breakage_does_not_block_promotion() -> None:
    result = evaluate_ring_promotion(
        candidate_version="121.0",
        previous_stable_version="120.0",
        lab_regression_failed_services=frozenset({"some_minor_extension"}),
        critical_services=frozenset({"zalo_web", "whatsapp_web"}),
        retention_deadline="",
    )
    assert result.blocked is False
    assert result.retained_version is None


def test_retention_never_held_indefinitely_without_deadline() -> None:
    # Fail-closed: hạn rỗng coi như ĐÃ hết hạn — không có đường "giữ mãi".
    assert is_retention_expired("", "2026-11-07") is True
    assert is_retention_expired("2026-11-20", "2026-11-07") is False
    assert is_retention_expired("2026-11-20", "2026-11-21") is True
    assert is_retention_expired("not-a-date", "2026-11-07") is True
