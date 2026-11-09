# -*- coding: utf-8 -*-
"""Bộ kiểm thử U15-C — staged deployment, boot-health, auto-rollback, migration
guard, fault-injection (PL15 §5, §9). Chạy & pass bằng pytest; KHÔNG đụng U15-B.

Chứng minh:
  * Khôi phục sau mất-điện ở TỪNG pha (download/verify/stage/switch/boot_check):
    máy boot được (bản mới HOẶC bản trước) + tệp dữ liệu còn đúng hash + không nửa cài.
  * boot-health fail → tự rollback về bản trước, KHÔNG completed, báo UPD-008,
    KHÔNG xóa deployment cũ.
  * migration không an toàn → chặn UPD-010 + đòi backup; migration an toàn → cho stage.
  * resume sau đứt tải → đi tiếp tới completed.
  * Đổi con trỏ default nguyên tử + giữ bản cũ boot được.
"""
import os

import pytest

from update_contract import TransactionJournal, UpdateState
from update_service import DeviceProfile, DownloadInterrupted, UpdateService
from staged_deploy import (
    BackupProof,
    DeploymentStore,
    DeploymentError,
    Migration,
    MigrationGuard,
    StagedDeployer,
)
from boot_health import (
    ALL_PROBES,
    BootHealthChecker,
    all_healthy_probes,
    probes_with_failures,
    PROBE_UI,
    PROBE_KERNEL,
)
from fault_inject import FAULT_MATRIX, Fault, Phase, UpdateCampaign, run_matrix


# --------------------------------------------------------------------------- #
# 1. Fault-injection: mọi pha × mọi sự cố → boot được + data hash đúng + không nửa cài
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("phase,fault", FAULT_MATRIX,
                         ids=[f"{p.value}-{f.value}" for p, f in FAULT_MATRIX])
def test_fault_recovers_bootable_data_intact_no_half_install(phase, fault, tmp_path):
    camp = UpdateCampaign(str(tmp_path / f"{phase.value}-{fault.value}"))
    out = camp.simulate(phase, fault)
    assert out.bootable, f"{phase}/{fault}: máy KHÔNG boot được sau sự cố"
    assert out.data_intact, f"{phase}/{fault}: tệp dữ liệu LỆCH hash"
    assert not out.half_installed, f"{phase}/{fault}: còn bản NỬA CÀI"
    assert out.ok()


def test_matrix_covers_every_phase():
    phases = {p for p, _ in FAULT_MATRIX}
    assert phases == set(Phase), "Ma trận phải phủ mọi pha của chu trình"
    # Mất điện (power_loss) phải có ở TỪNG pha (PL15 §9).
    power_phases = {p for p, f in FAULT_MATRIX if f is Fault.POWER_LOSS}
    assert power_phases == set(Phase)


def test_run_matrix_all_invariants_hold():
    outs = run_matrix()
    assert len(outs) == len(FAULT_MATRIX)
    assert all(o.ok() for o in outs)


# --------------------------------------------------------------------------- #
# 2. Power-loss ở deployment-switch và boot_check phải quay về bản TRƯỚC (confirmed)
# --------------------------------------------------------------------------- #
def test_power_loss_at_switch_falls_back_to_previous(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    out = camp.simulate(Phase.SWITCH, Fault.POWER_LOSS)
    assert out.boot_deployment_id == UpdateCampaign.OLD_DEP
    assert out.rolled_back is True
    assert out.bootable and out.data_intact and not out.half_installed


def test_power_loss_at_boot_check_falls_back_to_previous(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    out = camp.simulate(Phase.BOOT_CHECK, Fault.POWER_LOSS)
    assert out.boot_deployment_id == UpdateCampaign.OLD_DEP
    assert out.rolled_back is True
    assert out.bootable and out.data_intact and not out.half_installed


# --------------------------------------------------------------------------- #
# 3. Boot-health fail → auto rollback, KHÔNG completed, UPD-008, giữ bản cũ
# --------------------------------------------------------------------------- #
def test_boot_health_fail_auto_rollback_never_completed(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    state, default_dep, rolled_back = camp.run_clean(health_ok=False)
    assert state == UpdateState.ROLLED_BACK.value
    assert state != UpdateState.COMPLETED.value
    assert default_dep == UpdateCampaign.OLD_DEP   # quay về bản trước
    assert rolled_back is True


def test_boot_health_fail_keeps_old_and_failed_new_deployment(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    camp.run_clean(health_ok=False)
    store = DeploymentStore(camp.store_root)
    ids = {d.dep_id for d in store.deployments()}
    # Bản cũ còn + bản mới KHÔNG bị xóa (giữ chứng cứ); default = cũ.
    assert UpdateCampaign.OLD_DEP in ids
    new_dep = f"{camp.uid}::namios-1.1"
    assert new_dep in ids
    assert store.current_default() == UpdateCampaign.OLD_DEP
    assert store.load(new_dep).failed is True
    assert store.load(UpdateCampaign.OLD_DEP).confirmed is True


def test_health_report_maps_to_upd008_on_critical_fail():
    # Probe tới hạn (kernel) hỏng → fail bất kể điểm số, mã báo cáo UPD-008.
    checker = BootHealthChecker(probes_with_failures((PROBE_KERNEL,)), max_boot_attempts=2)
    report = checker.evaluate()
    assert report.passed is False
    assert report.error_code == "UPD-008"
    assert PROBE_KERNEL in report.failed_probes()


def test_health_report_pass_has_no_error_code():
    checker = BootHealthChecker(all_healthy_probes())
    report = checker.evaluate()
    assert report.passed is True
    assert report.error_code is None


def test_ui_crash_loop_fails_even_if_score_high():
    # UI crash-lặp luôn fail dù các probe khác đạt (>= threshold).
    checker = BootHealthChecker(probes_with_failures((PROBE_UI,)),
                                pass_threshold=5, max_boot_attempts=3)
    report = checker.evaluate()
    assert report.passed is False
    assert report.error_code == "UPD-008"


def test_happy_path_completes_and_keeps_old(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    state, default_dep, rolled_back = camp.run_clean(health_ok=True)
    assert state == UpdateState.COMPLETED.value
    assert rolled_back is False
    store = DeploymentStore(camp.store_root)
    new_dep = f"{camp.uid}::namios-1.1"
    assert default_dep == new_dep
    assert store.load(new_dep).confirmed is True
    # PL15 §5: KHÔNG xóa deployment cũ sau khi bản mới qua cửa kiểm (rollback target).
    assert UpdateCampaign.OLD_DEP in {d.dep_id for d in store.deployments()}


# --------------------------------------------------------------------------- #
# 4. Migration guard — UPD-010 khi không an toàn, cho stage khi an toàn
# --------------------------------------------------------------------------- #
def _drive_to_verified(camp):
    svc = camp._svc()
    c = svc.check(camp.uid)
    c = svc.download(c)
    c = svc.verify(c)
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    return svc, c


def test_unsafe_migration_blocks_upd010_requires_backup(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    _, c = _drive_to_verified(camp)
    deployer = camp._deployer()
    mig = Migration("m-no-backup", version_from=1, version_to=2,
                    data_paths=("app.db",), forward_backward_compatible=False,
                    reversible=False, dry_run_ok=True)
    blocked, dep = deployer.prepare(
        c, payload_path=camp._payload_path(), build="namios-1.1",
        migration=mig, backup=None,   # KHÔNG có backup
    )
    assert blocked.state == UpdateState.BLOCKED
    assert blocked.error_code == "UPD-010"
    assert blocked.preflight.backup == "fail"
    assert dep is None
    # Không tạo deployment mới (giữ bản hiện tại).
    store = DeploymentStore(camp.store_root)
    assert {d.dep_id for d in store.deployments()} == {UpdateCampaign.OLD_DEP}


def test_unsafe_migration_unverified_backup_blocks_upd010(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    _, c = _drive_to_verified(camp)
    deployer = camp._deployer()
    mig = Migration("m2", 1, 2, data_paths=("app.db",),
                    forward_backward_compatible=True, dry_run_ok=True)
    backup = BackupProof("b-chua-kiem", created=True, restore_verified=False,
                         covered_paths=("app.db",))
    blocked, dep = deployer.prepare(
        c, payload_path=camp._payload_path(), build="namios-1.1",
        migration=mig, backup=backup,
    )
    assert blocked.state == UpdateState.BLOCKED
    assert blocked.error_code == "UPD-010"
    assert dep is None


def test_safe_migration_with_verified_backup_stages(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    _, c = _drive_to_verified(camp)
    deployer = camp._deployer()
    mig = Migration("m-ok", 1, 2, data_paths=("app.db",),
                    forward_backward_compatible=True, reversible=False, dry_run_ok=True)
    backup = BackupProof("b-ok", created=True, restore_verified=True,
                         covered_paths=("app.db",))
    staged, dep = deployer.prepare(
        c, payload_path=camp._payload_path(), build="namios-1.1",
        migration=mig, backup=backup,
    )
    assert staged.state == UpdateState.STAGED
    assert staged.error_code is None
    assert staged.preflight.backup == "pass"
    assert dep is not None


def test_migration_guard_unit_fail_closed():
    g = MigrationGuard()
    # Không migration → an toàn, không cần backup.
    assert g.assess(None, None).allowed is True
    # Một chiều + backup phủ + dry-run đạt → cho (backup là đường phục hồi).
    mig_one_way = Migration("o", 1, 2, data_paths=("d",), dry_run_ok=True)
    bk = BackupProof("b", True, True, covered_paths=("d",))
    assert g.assess(mig_one_way, bk).allowed is True
    # Một chiều + backup KHÔNG phủ dữ liệu → chặn UPD-010.
    bk_miss = BackupProof("b", True, True, covered_paths=("khac",))
    d = g.assess(mig_one_way, bk_miss)
    assert d.allowed is False and d.error_code == "UPD-010"
    # dry-run chưa đạt → chặn.
    mig_no_dry = Migration("n", 1, 2, forward_backward_compatible=True, dry_run_ok=False)
    assert g.assess(mig_no_dry, bk).allowed is False


# --------------------------------------------------------------------------- #
# 5. Resume sau đứt tải → đi tiếp tới completed qua đường staged
# --------------------------------------------------------------------------- #
def test_resume_after_download_interrupt_then_completes(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    svc = camp._svc()
    c = svc.check(camp.uid)
    with pytest.raises(DownloadInterrupted):
        svc.download(c, chunk_size=512, interrupt_after_bytes=1024)
    part = os.path.join(camp.cache, f"{camp.uid}.part")
    assert os.path.exists(part)

    # Giả lập tiến trình khởi động lại: resume contract từ journal rồi đi tiếp.
    j = TransactionJournal(camp.journal_path)
    resumed = j.resume(camp.uid)
    assert resumed.state == UpdateState.AVAILABLE
    svc2 = camp._svc()
    c = svc2.download(resumed, chunk_size=512)   # resume từ .part
    c = svc2.verify(c)
    assert c.state == UpdateState.VERIFIED

    deployer = camp._deployer()
    new_dep = f"{camp.uid}::namios-1.1"
    c, new_dep = deployer.prepare(
        c, payload_path=camp._payload_path(), build="namios-1.1", new_dep_id=new_dep,
    )
    c = deployer.arm_switch(c, new_dep)
    checker = BootHealthChecker(all_healthy_probes(),
                                journal=TransactionJournal(camp.journal_path))
    res = checker.run(c, deployer, new_dep)
    assert res.contract.state == UpdateState.COMPLETED
    assert res.rolled_back is False


# --------------------------------------------------------------------------- #
# 6. DeploymentStore — đổi con trỏ nguyên tử, giữ bản cũ, recover fallback
# --------------------------------------------------------------------------- #
def test_atomic_switch_keeps_previous_bootable(tmp_path):
    store = DeploymentStore.initialize(str(tmp_path / "store"),
                                       dep_id="A", build="1.0", payload=b"A" * 64)
    assert store.current_default() == "A"
    store._write_deployment("B", "1.1", "u", b"B" * 64, confirmed=False)
    store.set_default("B")  # nguyên tử
    assert store.current_default() == "B"
    # Bản cũ A vẫn còn và boot được (complete).
    assert store.is_complete("A") is True
    assert store.load("A").confirmed is True


def test_set_default_refuses_incomplete_deployment(tmp_path):
    store = DeploymentStore.initialize(str(tmp_path / "store"),
                                       dep_id="A", build="1.0", payload=b"A" * 64)
    with pytest.raises(DeploymentError):
        store.set_default("khong-ton-tai")


def test_recover_cleans_staging_and_detects_no_half_install(tmp_path):
    store = DeploymentStore.initialize(str(tmp_path / "store"),
                                       dep_id="A", build="1.0", payload=b"A" * 64)
    # Mô phỏng .staging dở còn sót sau mất điện giữa prepare.
    staging = os.path.join(store.deployments_dir, ".staging-B-999")
    os.makedirs(staging)
    with open(os.path.join(staging, "payload"), "wb") as fh:
        fh.write(b"B-cha")  # payload dở
    assert store.has_half_installed() is True   # còn .staging
    rec = store.recover()
    assert rec.bootable is True
    assert rec.boot_deployment_id == "A"
    assert store.has_half_installed() is False   # đã dọn .staging


def test_recover_rolls_back_when_default_unconfirmed(tmp_path):
    store = DeploymentStore.initialize(str(tmp_path / "store"),
                                       dep_id="A", build="1.0", payload=b"A" * 64)
    store._write_deployment("B", "1.1", "u", b"B" * 64, confirmed=False)
    store.set_default("B")   # trỏ sang bản CHƯA confirmed (như vừa đổi xong thì mất điện)
    rec = store.recover()
    assert rec.rolled_back is True
    assert rec.boot_deployment_id == "A"       # quay về bản confirmed
    assert store.load("B").failed is True


def test_data_files_never_touched_by_staging(tmp_path):
    camp = UpdateCampaign(str(tmp_path))
    before = camp.store.data_hashes()
    camp.run_clean(health_ok=True)   # cập nhật thành công
    after = DeploymentStore(camp.store_root).data_hashes()
    assert after == before == camp.expected_data
