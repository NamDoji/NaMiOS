#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS — Boot health check + auto-rollback (Phụ lục 15 §5, U15-C).

Mô hình "kiểm tra sức khỏe sau khởi động" (PL15 §5): sau khi boot vào deployment
mới, chạy một bộ probe; nếu trong ngưỡng mà KHÔNG đạt ⇒ **tự chọn bản trước
(rollback)** và **KHÔNG xóa deployment cũ** cho tới khi bản mới qua cửa kiểm.

Bộ probe tối thiểu (PL15 §5):
    kernel up · login ok · data mount · basic network · UI không crash-lặp ·
    update-service phản hồi.

Ngưỡng:
  * Probe TỚI HẠN (critical) phải đạt: kernel, login, data_mount, update_service.
  * Số probe đạt phải ≥ ``pass_threshold`` (mặc định 5/6); UI crash-lặp luôn fail.
  * Cho boot lại tối đa ``max_boot_attempts`` lần (kiểu boot-counter/greenboot);
    hết lần mà chưa "healthy" ⇒ health FAIL ⇒ rollback.

Kết quả ánh xạ:
  * health đạt  → contract ``completed`` (bản mới được confirm, bản cũ GIỮ lại).
  * health fail → contract ``rolled_back`` + mã báo cáo **UPD-008** (ở lớp report,
    KHÔNG gắn vào contract vì error_code chỉ đi với ``blocked`` — PL15 §7).

Trạng thái: ``partial`` — probe ở đây là MÔ PHỎNG (hàm tiêm vào). Trên NaMiOS thật,
probe phải đọc dpkg --audit / systemctl is-system-running / mountpoint /home /
ping gateway / đếm restart của plasmashell / D-Bus ping update-service
(xem namios-health-check.sh, ADR 0014). Chưa chạy trên phần cứng.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from update_contract import TransactionJournal, UpdateContract, UpdateState


# Tên probe (giữ khớp PL15 §5).
PROBE_KERNEL = "kernel_up"
PROBE_LOGIN = "login_ok"
PROBE_DATA_MOUNT = "data_mount"
PROBE_NETWORK = "basic_network"
PROBE_UI = "ui_not_crash_loop"
PROBE_UPDATE_SERVICE = "update_service_responds"

ALL_PROBES = (
    PROBE_KERNEL, PROBE_LOGIN, PROBE_DATA_MOUNT,
    PROBE_NETWORK, PROBE_UI, PROBE_UPDATE_SERVICE,
)

#: Probe tới hạn — hỏng bất kỳ cái nào ⇒ health fail ngay, bất kể điểm số.
CRITICAL_PROBES = frozenset({PROBE_KERNEL, PROBE_LOGIN, PROBE_DATA_MOUNT, PROBE_UPDATE_SERVICE})

#: Nhãn tiếng Việt cho report.
PROBE_LABELS_VI = {
    PROBE_KERNEL: "Nhân (kernel) đã lên",
    PROBE_LOGIN: "Đăng nhập được",
    PROBE_DATA_MOUNT: "Ổ dữ liệu (/home) đã mount",
    PROBE_NETWORK: "Mạng cơ bản",
    PROBE_UI: "Giao diện không crash lặp",
    PROBE_UPDATE_SERVICE: "Dịch vụ cập nhật phản hồi",
}


@dataclass(frozen=True)
class ProbeResult:
    name: str
    ok: bool
    critical: bool
    detail_vi: str


@dataclass(frozen=True)
class HealthReport:
    passed: bool
    attempts_used: int
    results: Tuple[ProbeResult, ...]
    score: str                       # "n/6"
    error_code: Optional[str]        # None khi đạt; "UPD-008" khi fail
    summary_vi: str

    def failed_probes(self) -> List[str]:
        return [r.name for r in self.results if not r.ok]


@dataclass(frozen=True)
class BootOutcome:
    """Kết quả cuối sau boot_check: contract + report + có rollback hay không."""
    contract: UpdateContract
    report: HealthReport
    rolled_back: bool
    boot_deployment_id: Optional[str]


# Kiểu probe: () -> bool. Tiêm vào để mô phỏng/fault-inject.
ProbeFn = Callable[[], bool]


def all_healthy_probes() -> Dict[str, ProbeFn]:
    """Bộ probe 'máy khỏe' — mọi probe đạt (dùng cho luồng hợp lệ / test)."""
    return {name: (lambda: True) for name in ALL_PROBES}


def probes_with_failures(failing: Tuple[str, ...]) -> Dict[str, ProbeFn]:
    """Bộ probe trong đó các probe ``failing`` trả False, còn lại True."""
    fset = set(failing)
    return {name: (lambda n=name: n not in fset) for name in ALL_PROBES}


class BootHealthChecker:
    """Chạy probe + ngưỡng; quyết định completed/rolled_back và tự rollback.

    ``probes`` là dict ``{tên_probe: () -> bool}``. Mỗi "lần boot" gọi lại toàn bộ
    probe; probe có thể phụ thuộc trạng thái ngoài (vd biến đếm) để mô phỏng
    crash-lặp vs. tự khỏi sau vài lần.
    """

    def __init__(
        self,
        probes: Optional[Dict[str, ProbeFn]] = None,
        *,
        pass_threshold: int = 5,
        max_boot_attempts: int = 3,
        journal: Optional[TransactionJournal] = None,
        log_fn=None,
    ):
        self.probes = probes or all_healthy_probes()
        missing = set(ALL_PROBES) - set(self.probes)
        if missing:
            raise ValueError(f"Thiếu probe bắt buộc: {sorted(missing)}")
        self.pass_threshold = pass_threshold
        self.max_boot_attempts = max(1, max_boot_attempts)
        self.journal = journal
        self._log_fn = log_fn
        self.logs: List[str] = []

    def log(self, msg: str) -> None:
        self.logs.append(msg)
        if self._log_fn:
            self._log_fn(msg)

    # ------------------------------------------------------------------ #
    def _run_once(self) -> Tuple[bool, List[ProbeResult]]:
        results: List[ProbeResult] = []
        for name in ALL_PROBES:
            try:
                ok = bool(self.probes[name]())
            except Exception:
                ok = False  # probe ném ⇒ coi như fail (fail-closed)
            crit = name in CRITICAL_PROBES
            detail = ("đạt" if ok else "KHÔNG đạt") + (" (tới hạn)" if crit else "")
            results.append(ProbeResult(name, ok, crit, f"{PROBE_LABELS_VI[name]}: {detail}"))
        critical_ok = all(r.ok for r in results if r.critical)
        n_ok = sum(1 for r in results if r.ok)
        ui_ok = next(r.ok for r in results if r.name == PROBE_UI)
        attempt_pass = critical_ok and ui_ok and n_ok >= self.pass_threshold
        return attempt_pass, results

    def evaluate(self) -> HealthReport:
        """Chạy tối đa ``max_boot_attempts`` lần boot; đạt ở lần nào ⇒ healthy."""
        last_results: List[ProbeResult] = []
        for attempt in range(1, self.max_boot_attempts + 1):
            ok, results = self._run_once()
            last_results = results
            n_ok = sum(1 for r in results if r.ok)
            self.log(f"boot-health lần {attempt}/{self.max_boot_attempts}: "
                     f"{'ĐẠT' if ok else 'chưa đạt'} ({n_ok}/{len(ALL_PROBES)} probe)")
            if ok:
                return HealthReport(
                    passed=True, attempts_used=attempt, results=tuple(results),
                    score=f"{n_ok}/{len(ALL_PROBES)}", error_code=None,
                    summary_vi=f"Boot health đạt ở lần {attempt}: {n_ok}/{len(ALL_PROBES)} probe.",
                )
        n_ok = sum(1 for r in last_results if r.ok)
        failed = [PROBE_LABELS_VI[r.name] for r in last_results if not r.ok]
        return HealthReport(
            passed=False, attempts_used=self.max_boot_attempts, results=tuple(last_results),
            score=f"{n_ok}/{len(ALL_PROBES)}", error_code="UPD-008",
            summary_vi=(f"Boot health FAIL sau {self.max_boot_attempts} lần "
                        f"({n_ok}/{len(ALL_PROBES)} probe). Chưa đạt: {', '.join(failed)}."),
        )

    # ------------------------------------------------------------------ #
    def _commit(self, contract: UpdateContract, note: str) -> None:
        if self.journal is None:
            return
        key = f"{contract.correlation_id}:{contract.update_id}:{contract.state.value}:{contract.error_code}:{note}"
        self.journal.append(contract, idempotency_key=key, note=note)

    def run(
        self,
        contract: UpdateContract,
        deployer,  # staged_deploy.StagedDeployer
        new_dep_id: str,
    ) -> BootOutcome:
        """Chạy boot-health cho deployment mới, rồi:
          * đạt ⇒ confirm bản mới + contract ``completed`` (bản cũ GIỮ lại).
          * fail ⇒ **tự rollback** về bản trước + contract ``rolled_back`` (UPD-008).
        KHÔNG bao giờ tự nâng ``completed`` khi health chưa đạt (PL15 §5/§7)."""
        if contract.state == UpdateState.REBOOT_PENDING:
            contract = contract.transition(UpdateState.BOOT_CHECK)
            self._commit(contract, "boot_check: đang kiểm tra sau khởi động")
        if contract.state != UpdateState.BOOT_CHECK:
            raise RuntimeError(
                f"boot_check cần reboot_pending/boot_check, nhận {contract.state.value}"
            )

        report = self.evaluate()

        if report.passed:
            deployer.confirm(new_dep_id)
            done = contract.transition(UpdateState.COMPLETED)
            self.log(f"boot_check: ĐẠT {contract.update_id} -> completed; "
                     f"bản cũ KHÔNG bị xóa (vẫn là rollback target).")
            self._commit(done, "boot_check: completed")
            return BootOutcome(done, report, rolled_back=False,
                               boot_deployment_id=deployer.store.current_default())

        # Health FAIL → tự rollback về bản trước (không xóa bản mới).
        prev = deployer.rollback_to_previous(new_dep_id)
        rolled = contract.transition(UpdateState.ROLLED_BACK)
        self.log(f"boot_check: HỎNG {contract.update_id} ({report.error_code}) -> "
                 f"rolled_back về '{prev}'. {report.summary_vi}")
        self._commit(rolled, f"boot_check: rolled_back ({report.error_code})")
        return BootOutcome(rolled, report, rolled_back=True, boot_deployment_id=prev)


__all__ = [
    "ALL_PROBES", "CRITICAL_PROBES", "PROBE_LABELS_VI",
    "PROBE_KERNEL", "PROBE_LOGIN", "PROBE_DATA_MOUNT", "PROBE_NETWORK",
    "PROBE_UI", "PROBE_UPDATE_SERVICE",
    "ProbeResult", "HealthReport", "BootOutcome",
    "all_healthy_probes", "probes_with_failures", "BootHealthChecker",
]
