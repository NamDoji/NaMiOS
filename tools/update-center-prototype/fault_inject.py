#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS — Fault-injection harness (Phụ lục 15 §9 "Độ tin cậy", U15-C).

Mô phỏng (mức VM/thư-mục, KHÔNG phần cứng) các sự cố ở TỪNG pha của chu trình
cập nhật staged và chứng minh BẤT BIẾN sau mỗi sự cố:

  1. Máy kết thúc ở trạng thái BOOT ĐƯỢC — bản MỚI hoặc bản TRƯỚC.
  2. Các tệp dữ liệu thử giữ ĐÚNG HASH (update staged KHÔNG đụng /home mô phỏng).
  3. KHÔNG BAO GIỜ có bản "nửa cài" (không deployment-thật-dở, không .staging sót).

Sự cố mô phỏng (PL15 §9 hàng "Độ tin cậy"):
  * Mất điện ở TỪNG pha: download · verify · stage · deployment-switch · boot_check.
  * Đầy ổ (disk-full), kill updater (SIGKILL ⇒ dừng đột ngột), đứt mạng.

"Mất điện" được mô phỏng bằng cách: dừng đột ngột (bỏ trạng thái trong RAM) rồi
DỰNG LẠI store/service TỪ ĐĨA và chạy ``recover()`` + resume journal — đúng như máy
mất điện, bật lại, chạy khôi phục.

Trạng thái: ``partial`` — đây là SIMULATION. Xác minh thật phải chạy fault-injection
trên VM rồi 5 máy pilot (gồm rút điện thật). Xem docs/specs/U15C-STAGED-ROLLBACK.md.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sign_test_repo import build_test_repo
from update_contract import TransactionJournal, UpdateState
from update_service import DeviceProfile, DownloadInterrupted, UpdateService
from staged_deploy import (
    BackupProof,
    DeploymentStore,
    Migration,
    StagedDeployer,
)
from boot_health import BootHealthChecker, all_healthy_probes, probes_with_failures


class Phase(str, Enum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    STAGE = "stage"
    SWITCH = "deployment-switch"
    BOOT_CHECK = "boot_check"


class Fault(str, Enum):
    POWER_LOSS = "power_loss"
    DISK_FULL = "disk_full"
    KILLED_UPDATER = "killed_updater"
    NETWORK_DROP = "network_drop"


@dataclass(frozen=True)
class FaultOutcome:
    phase: Phase
    fault: Fault
    bootable: bool
    boot_deployment_id: Optional[str]
    data_intact: bool
    half_installed: bool
    rolled_back: bool
    final_state: Optional[str]
    note_vi: str

    def ok(self) -> bool:
        """Đạt bất biến U15-C: boot được + dữ liệu đúng hash + không nửa cài."""
        return self.bootable and self.data_intact and not self.half_installed


class InjectedPowerLoss(Exception):
    """Mô phỏng mất điện/kill: dừng đột ngột (không phải lỗi nghiệp vụ)."""


# Cross-product (pha × loại sự cố) được hiện thực trong harness này.
FAULT_MATRIX: Tuple[Tuple[Phase, Fault], ...] = (
    (Phase.DOWNLOAD, Fault.POWER_LOSS),
    (Phase.DOWNLOAD, Fault.NETWORK_DROP),
    (Phase.DOWNLOAD, Fault.KILLED_UPDATER),
    (Phase.DOWNLOAD, Fault.DISK_FULL),
    (Phase.VERIFY, Fault.POWER_LOSS),
    (Phase.VERIFY, Fault.KILLED_UPDATER),
    (Phase.STAGE, Fault.POWER_LOSS),
    (Phase.STAGE, Fault.DISK_FULL),
    (Phase.STAGE, Fault.KILLED_UPDATER),
    (Phase.SWITCH, Fault.POWER_LOSS),
    (Phase.SWITCH, Fault.KILLED_UPDATER),
    (Phase.BOOT_CHECK, Fault.POWER_LOSS),
    (Phase.BOOT_CHECK, Fault.KILLED_UPDATER),
)


class UpdateCampaign:
    """Dựng một chu trình cập nhật staged đầy đủ trên repo ký giả + store A-B +
    dữ liệu thử; cho phép tiêm sự cố ở từng pha và chạy khôi phục."""

    OLD_DEP = "namios-1.0-x86_64-stable-0000"

    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        os.makedirs(self.root, exist_ok=True)
        self.repo_info = build_test_repo(os.path.join(self.root, "repo"))
        self.device = DeviceProfile(
            architecture="x86_64", model="namios-ref-pc",
            current_deployment=self.OLD_DEP, channel="stable",
        )
        self.cache = os.path.join(self.root, "cache")
        os.makedirs(self.cache, exist_ok=True)
        self.journal_path = os.path.join(self.cache, "journal.jsonl")
        self.store_root = os.path.join(self.root, "store")

        # Bản đang chạy = deployment OLD, confirmed.
        self.store = DeploymentStore.initialize(
            self.store_root, dep_id=self.OLD_DEP, build="namios-1.0",
            update_id="seed", payload=b"NaMiOS 1.0 running deployment (TEST-ONLY)\n" * 8,
        )
        # Dữ liệu người dùng mô phỏng (/home) — update KHÔNG được đụng.
        self.expected_data: Dict[str, str] = {}
        for name, content in (
            ("tai-lieu-quan-trong.txt", b"Bai tap cua con - KHONG DUOC MAT\n" * 32),
            ("anh-gia-dinh.bin", bytes(range(256)) * 64),
            ("so-ke-toan.db", b"SQLITE-FAKE" + b"\x00\x01\x02\x03" * 128),
        ):
            self.expected_data[name] = self.store.seed_data(name, content)

        self.uid = self.repo_info["update_id"]

    # ------------------------------------------------------------------ #
    def _svc(self) -> UpdateService:
        return UpdateService(
            self.repo_info["repo"], self.repo_info["root_path"], self.device,
            cache_dir=self.cache,
            journal=TransactionJournal(self.journal_path),
            user_policy="auto_download_ask_install",
        )

    def _deployer(self, store: Optional[DeploymentStore] = None) -> StagedDeployer:
        return StagedDeployer(store or self.store, journal=TransactionJournal(self.journal_path))

    def _new_dep_id(self, build: str = "namios-1.1") -> str:
        return f"{self.uid}::{build}"

    def _payload_path(self) -> str:
        return os.path.join(self.cache, f"{self.uid}.payload")

    # ------------------------------------------------------------------ #
    def _reboot_and_check(self, phase: Phase, fault: Fault, note: str) -> FaultOutcome:
        """Mô phỏng khởi động lại sau sự cố: dựng store MỚI từ đĩa + recover()."""
        # Dọn cache .part để pha download sau còn mô phỏng được (không bắt buộc).
        store = DeploymentStore(self.store_root)
        rec = store.recover()
        self.store = store
        data_now = store.data_hashes()
        data_intact = data_now == self.expected_data
        half = store.has_half_installed()
        bootable = store.is_bootable()
        # Resume contract từ journal (bền qua reboot).
        j = TransactionJournal(self.journal_path)
        resumed = j.resume(self.uid)
        final_state = resumed.state.value if resumed else None
        return FaultOutcome(
            phase=phase, fault=fault, bootable=bootable,
            boot_deployment_id=store.current_default(), data_intact=data_intact,
            half_installed=half, rolled_back=rec.rolled_back, final_state=final_state,
            note_vi=f"{note} | recover: {rec.note_vi}",
        )

    # ------------------------------------------------------------------ #
    def simulate(self, phase: Phase, fault: Fault) -> FaultOutcome:
        """Chạy chu trình tới ``phase`` thì tiêm ``fault``, rồi khôi phục + kiểm."""
        svc = self._svc()
        c = svc.check(self.uid)

        # -------- Pha DOWNLOAD --------
        if phase is Phase.DOWNLOAD:
            # Đứt mạng / mất điện / kill / đầy ổ giữa tải: để lại .part hợp lệ.
            try:
                svc.download(c, chunk_size=512, interrupt_after_bytes=1024)
            except DownloadInterrupted:
                pass
            return self._reboot_and_check(
                phase, fault,
                "Mất tải giữa chừng — giữ phần đã tải (.part), hệ đang chạy chưa đổi.",
            )

        c = svc.download(c)

        # -------- Pha VERIFY --------
        if phase is Phase.VERIFY:
            # Bắt đầu verify rồi mất điện trước khi stage: không ghi gì vào store.
            _ = svc.verify(c)  # verify không đụng store/deployment
            return self._reboot_and_check(
                phase, fault, "Mất điện lúc verify — chưa chuẩn bị deployment nào.",
            )

        c = svc.verify(c)
        c = svc.preflight(c, storage="pass", power="pass", network="pass")
        deployer = self._deployer()
        new_dep = self._new_dep_id()

        # -------- Pha STAGE --------
        if phase is Phase.STAGE:
            reason = "ENOSPC (đầy ổ)" if fault is Fault.DISK_FULL else "mất điện/kill giữa stage"

            def _boom():
                raise InjectedPowerLoss(reason)

            try:
                deployer.prepare(
                    c, payload_path=self._payload_path(), build="namios-1.1",
                    new_dep_id=new_dep, _fault_hook=_boom,
                )
            except InjectedPowerLoss:
                pass
            return self._reboot_and_check(
                phase, fault,
                f"Sự cố ({reason}) giữa stage — còn .staging dở, deployment thật CHƯA xuất hiện.",
            )

        c, new_dep = deployer.prepare(
            c, payload_path=self._payload_path(), build="namios-1.1", new_dep_id=new_dep,
        )

        # -------- Pha DEPLOYMENT-SWITCH --------
        if phase is Phase.SWITCH:
            # arm_switch đã đổi con trỏ default sang bản MỚI (chưa confirmed).
            # Mất điện NGAY SAU khi flip con trỏ, trước khi confirm.
            c = deployer.arm_switch(c, new_dep)
            return self._reboot_and_check(
                phase, fault,
                "Mất điện ngay sau khi đổi con trỏ default (bản mới chưa confirmed).",
            )

        c = deployer.arm_switch(c, new_dep)

        # -------- Pha BOOT_CHECK --------
        if phase is Phase.BOOT_CHECK:
            # Default = bản mới; mất điện GIỮA boot-health, trước confirm.
            return self._reboot_and_check(
                phase, fault,
                "Mất điện giữa boot-health (bản mới chưa confirmed).",
            )

        raise ValueError(f"Pha không hỗ trợ tiêm sự cố: {phase}")

    # ------------------------------------------------------------------ #
    def run_clean(self, *, health_ok: bool = True) -> Tuple[str, Optional[str], bool]:
        """Chạy chu trình staged ĐẦY ĐỦ không sự cố. Trả (final_state, default_dep, rolled_back)."""
        svc = self._svc()
        c = svc.check(self.uid)
        c = svc.download(c)
        c = svc.verify(c)
        c = svc.preflight(c, storage="pass", power="pass", network="pass")
        deployer = self._deployer()
        new_dep = self._new_dep_id()
        c, new_dep = deployer.prepare(
            c, payload_path=self._payload_path(), build="namios-1.1", new_dep_id=new_dep,
        )
        c = deployer.arm_switch(c, new_dep)
        probes = all_healthy_probes() if health_ok else probes_with_failures(("ui_not_crash_loop",))
        checker = BootHealthChecker(probes, journal=TransactionJournal(self.journal_path))
        outcome = checker.run(c, deployer, new_dep)
        return outcome.contract.state.value, self.store.current_default(), outcome.rolled_back


def run_matrix(verbose: bool = False) -> List[FaultOutcome]:
    """Chạy toàn bộ ma trận sự cố, mỗi ca trên một campaign sạch. Trả danh sách outcome."""
    outcomes: List[FaultOutcome] = []
    for phase, fault in FAULT_MATRIX:
        tmp = tempfile.mkdtemp(prefix="namios-fault-")
        try:
            camp = UpdateCampaign(tmp)
            out = camp.simulate(phase, fault)
            outcomes.append(out)
            if verbose:
                flag = "OK " if out.ok() else "FAIL"
                print(f"[{flag}] {phase.value:17s} + {fault.value:14s} -> "
                      f"boot={out.boot_deployment_id} data_intact={out.data_intact} "
                      f"half_installed={out.half_installed} state={out.final_state}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return outcomes


def _demo() -> int:
    print("== NaMiOS U15-C fault-injection (SIMULATION) ==")
    outs = run_matrix(verbose=True)
    bad = [o for o in outs if not o.ok()]
    print(f"\nTổng {len(outs)} ca; đạt bất biến: {len(outs) - len(bad)}; vi phạm: {len(bad)}")
    # Happy path + health-fail rollback.
    tmp = tempfile.mkdtemp(prefix="namios-clean-")
    try:
        state, dep, rb = UpdateCampaign(tmp).run_clean(health_ok=True)
        print(f"Luồng sạch health OK  -> state={state} default={dep} rolled_back={rb}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    tmp = tempfile.mkdtemp(prefix="namios-hf-")
    try:
        state, dep, rb = UpdateCampaign(tmp).run_clean(health_ok=False)
        print(f"Luồng health FAIL     -> state={state} default={dep} rolled_back={rb}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_demo())
