#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS — Staged deployment + migration guard (Phụ lục 15 §5, U15-C).

Mô hình "triển khai theo bậc" (staged / A-B) DỰNG TRÊN hợp đồng §7 có sẵn
(``update_contract.py``) và dịch vụ U15-B (``update_service.py``). Ý tưởng cốt lõi
(PL15 §5 "Cập nhật nguyên tử, rollback và dữ liệu"):

  * CHUẨN BỊ bản mới thành MỘT DEPLOYMENT RIÊNG — KHÔNG ghi nửa vời lên hệ đang
    chạy. Payload đã-xác-thực được chép vào thư mục deployment mới qua một thư mục
    ``.staging-*`` tạm, rồi **đổi tên nguyên tử** sang deployment thật. Mất điện
    giữa prepare ⇒ chỉ còn thư mục ``.staging`` dở, KHÔNG có deployment-thật-nửa-vời.
  * GIỮ deployment trước **boot được** cho tới khi bản mới qua cửa kiểm (health).
  * ĐỔI con trỏ "deployment mặc định" bằng ``os.replace`` (rename nguyên tử POSIX)
    — luôn trỏ tới một deployment HOÀN CHỈNH; không có trạng thái con-trỏ-nửa.
  * ``MigrationGuard``: chặn/stage migration dữ liệu — đòi dry-run + bằng chứng
    backup đã-kiểm-khôi-phục; không an toàn ⇒ chặn **UPD-010** (giữ bản hiện tại).

ÁNH XẠ THỰC TẾ (honest — xem ADR 0014 / 0017 và docs/specs/U15C-STAGED-ROLLBACK.md):
  Đây là MÔ PHỎNG mức VM/thư-mục. "Deployment riêng" trên NaMiOS alpha KHÔNG phải
  A-B nguyên tử thật mà là **Timeshift snapshot (rsync, ext4) + apt staged-apply +
  GRUB default/recovery** (ADR 0014). "Đổi con trỏ mặc định" tương ứng đặt
  default GRUB entry + boot-counter kiểu greenboot. Chưa nối bootloader/apt thật,
  chưa test trên phần cứng. Trạng thái: ``partial``.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from update_contract import (
    Preflight,
    TransactionJournal,
    UpdateContract,
    UpdateState,
)


# --------------------------------------------------------------------------- #
# Tiện ích I/O bền (atomic write + fsync) — best-effort cho mô phỏng mất điện
# --------------------------------------------------------------------------- #
def _fsync_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_DIRECTORY)
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _atomic_write_bytes(path: str, data: bytes) -> None:
    """Ghi file nguyên tử: temp + fsync + os.replace (POSIX rename nguyên tử)."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-write-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)  # nguyên tử
        _fsync_dir(d)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _atomic_write_json(path: str, obj: dict) -> None:
    _atomic_write_bytes(path, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


# --------------------------------------------------------------------------- #
# Deployment (một "bậc" hệ điều hành có thể boot)
# --------------------------------------------------------------------------- #
@dataclass
class Deployment:
    dep_id: str
    build: str
    update_id: str
    payload_hash: str
    created_ns: int
    confirmed: bool = False  # đã qua boot-health → giữ làm bản tin cậy
    failed: bool = False     # đã bị rollback khỏi (không chọn làm mặc định nữa)

    def to_dict(self) -> dict:
        return {
            "dep_id": self.dep_id,
            "build": self.build,
            "update_id": self.update_id,
            "payload_hash": self.payload_hash,
            "created_ns": self.created_ns,
            "confirmed": self.confirmed,
            "failed": self.failed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Deployment":
        return cls(
            dep_id=d["dep_id"],
            build=d["build"],
            update_id=d["update_id"],
            payload_hash=d["payload_hash"],
            created_ns=int(d["created_ns"]),
            confirmed=bool(d.get("confirmed", False)),
            failed=bool(d.get("failed", False)),
        )


@dataclass(frozen=True)
class RecoveryResult:
    boot_deployment_id: Optional[str]
    rolled_back: bool
    cleaned_staging: List[str]
    bootable: bool
    note_vi: str


class DeploymentError(RuntimeError):
    pass


class DeploymentStore:
    """Tập deployment A-B trên thư mục, với con trỏ ``default`` đổi nguyên tử.

    Bố cục::

        root/
          deployments/<dep_id>/payload
          deployments/<dep_id>/deployment.json
          default                      # con trỏ (1 dòng dep_id) — đổi nguyên tử
          data/                        # mô phỏng /home — staging KHÔNG đụng

    BẤT BIẾN:
      * Thư mục deployment thật CHỈ xuất hiện khi payload đã chép đủ + hash khớp
        (prepare dùng ``.staging-*`` rồi rename nguyên tử). Không bao giờ nửa-vời.
      * ``default`` chỉ đổi qua :meth:`set_default` (os.replace) → luôn trỏ tới
        deployment hoàn chỉnh.
      * KHÔNG xóa deployment cũ khi bản mới chưa ``confirmed`` (giữ đường quay lui).
    """

    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.deployments_dir = os.path.join(self.root, "deployments")
        self.default_path = os.path.join(self.root, "default")
        self.data_dir = os.path.join(self.root, "data")
        os.makedirs(self.deployments_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    # -- khởi tạo bản đang chạy -------------------------------------------- #
    @classmethod
    def initialize(
        cls, root: str, *, dep_id: str, build: str, update_id: str = "seed",
        payload: bytes = b"NaMiOS running OS deployment (TEST-ONLY)\n",
    ) -> "DeploymentStore":
        store = cls(root)
        if store.current_default() is None:
            store._write_deployment(dep_id, build, update_id, payload, confirmed=True)
            store.set_default(dep_id)
        return store

    # -- dữ liệu người dùng (mô phỏng /home) ------------------------------- #
    def seed_data(self, name: str, content: bytes) -> str:
        path = os.path.join(self.data_dir, name)
        _atomic_write_bytes(path, content)
        return _sha256_file(path)

    def data_hashes(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for name in sorted(os.listdir(self.data_dir)):
            p = os.path.join(self.data_dir, name)
            if os.path.isfile(p):
                out[name] = _sha256_file(p)
        return out

    # -- đọc trạng thái ---------------------------------------------------- #
    def _dep_dir(self, dep_id: str) -> str:
        return os.path.join(self.deployments_dir, dep_id)

    def _meta_path(self, dep_id: str) -> str:
        return os.path.join(self._dep_dir(dep_id), "deployment.json")

    def _payload_path(self, dep_id: str) -> str:
        return os.path.join(self._dep_dir(dep_id), "payload")

    def load(self, dep_id: str) -> Optional[Deployment]:
        mpath = self._meta_path(dep_id)
        if not os.path.exists(mpath):
            return None
        try:
            with open(mpath, "r", encoding="utf-8") as fh:
                return Deployment.from_dict(json.load(fh))
        except (json.JSONDecodeError, KeyError):
            return None

    def deployments(self) -> List[Deployment]:
        out: List[Deployment] = []
        for name in os.listdir(self.deployments_dir):
            if name.startswith(".staging"):
                continue
            dep = self.load(name)
            if dep is not None:
                out.append(dep)
        return sorted(out, key=lambda d: d.created_ns)

    def is_complete(self, dep_id: str) -> bool:
        """Deployment hoàn chỉnh: có meta + payload + hash khớp hash đã ghi."""
        dep = self.load(dep_id)
        if dep is None:
            return False
        ppath = self._payload_path(dep_id)
        if not os.path.exists(ppath):
            return False
        return _sha256_file(ppath) == dep.payload_hash

    def current_default(self) -> Optional[str]:
        if not os.path.exists(self.default_path):
            return None
        with open(self.default_path, "r", encoding="utf-8") as fh:
            val = fh.read().strip()
        return val or None

    # -- ghi nguyên tử ----------------------------------------------------- #
    def set_default(self, dep_id: str) -> None:
        if not self.is_complete(dep_id):
            raise DeploymentError(
                f"Từ chối trỏ default sang '{dep_id}' chưa hoàn chỉnh (chống con-trỏ-nửa)."
            )
        _atomic_write_bytes(self.default_path, (dep_id + "\n").encode("utf-8"))

    def _write_deployment(
        self, dep_id: str, build: str, update_id: str, payload: bytes, *, confirmed: bool,
        _fault_hook=None,
    ) -> Deployment:
        """Chép payload qua thư mục .staging rồi rename nguyên tử sang deployment thật.

        ``_fault_hook`` (chỉ để fault-injection): nếu đặt, gọi NGAY TRƯỚC rename
        nguyên tử — ném để mô phỏng mất điện/đầy đĩa giữa prepare. Khi đó chỉ còn
        thư mục ``.staging`` dở; deployment THẬT chưa bao giờ xuất hiện nửa-vời."""
        final = self._dep_dir(dep_id)
        if os.path.exists(final):
            shutil.rmtree(final)
        staging = os.path.join(self.deployments_dir, f".staging-{dep_id}-{os.getpid()}")
        if os.path.exists(staging):
            shutil.rmtree(staging)
        os.makedirs(staging)
        # 1) payload
        ppath = os.path.join(staging, "payload")
        with open(ppath, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        payload_hash = _sha256_file(ppath)
        dep = Deployment(
            dep_id=dep_id, build=build, update_id=update_id,
            payload_hash=payload_hash, created_ns=time.time_ns(), confirmed=confirmed,
        )
        # 2) meta (trong staging)
        with open(os.path.join(staging, "deployment.json"), "w", encoding="utf-8") as fh:
            json.dump(dep.to_dict(), fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        _fsync_dir(staging)
        # Fault-injection seam: mô phỏng mất điện NGAY TRƯỚC khi "công bố" deployment.
        if _fault_hook is not None:
            _fault_hook()
        # 3) rename NGUYÊN TỬ cả thư mục -> deployment thật chỉ hiện khi đã đủ
        os.replace(staging, final)
        _fsync_dir(self.deployments_dir)
        return dep

    def _rewrite_meta(self, dep: Deployment) -> None:
        _atomic_write_json(self._meta_path(dep.dep_id), dep.to_dict())

    def mark_confirmed(self, dep_id: str) -> None:
        dep = self.load(dep_id)
        if dep is None:
            raise DeploymentError(f"Không có deployment '{dep_id}' để xác nhận")
        dep.confirmed = True
        dep.failed = False
        self._rewrite_meta(dep)

    def mark_failed(self, dep_id: str) -> None:
        dep = self.load(dep_id)
        if dep is None:
            return
        dep.failed = True
        dep.confirmed = False
        self._rewrite_meta(dep)

    # -- chọn bản quay lui ------------------------------------------------- #
    def latest_confirmed(self, *, exclude: Optional[str] = None) -> Optional[Deployment]:
        cands = [
            d for d in self.deployments()
            if d.confirmed and not d.failed and d.dep_id != exclude and self.is_complete(d.dep_id)
        ]
        if not cands:
            return None
        return max(cands, key=lambda d: d.created_ns)

    # -- dọn rác staging + khôi phục sau mất điện -------------------------- #
    def clean_staging(self) -> List[str]:
        cleaned: List[str] = []
        for name in os.listdir(self.deployments_dir):
            if name.startswith(".staging") or name.startswith(".tmp-"):
                p = os.path.join(self.deployments_dir, name)
                shutil.rmtree(p, ignore_errors=True)
                cleaned.append(name)
        return cleaned

    def recover(self) -> RecoveryResult:
        """Chạy sau "mất điện/kill": dọn staging dở; nếu default trỏ tới bản chưa
        ``confirmed`` / không hoàn chỉnh ⇒ tự quay về bản confirmed gần nhất."""
        cleaned = self.clean_staging()
        cur = self.current_default()
        cur_dep = self.load(cur) if cur else None
        default_ok = (
            cur is not None and cur_dep is not None
            and self.is_complete(cur) and cur_dep.confirmed and not cur_dep.failed
        )
        if default_ok:
            return RecoveryResult(cur, False, cleaned, True,
                                  f"Default '{cur}' hoàn chỉnh + confirmed; boot bình thường.")
        # default hỏng / chưa xác nhận → quay về bản confirmed gần nhất
        fallback = self.latest_confirmed(exclude=cur)
        if fallback is None:
            # Không có bản tin cậy nào — hiếm; giữ nguyên, báo không boot được.
            return RecoveryResult(cur, False, cleaned, False,
                                  "Không tìm được deployment confirmed để quay lui.")
        if cur is not None and cur_dep is not None:
            self.mark_failed(cur)
        self.set_default(fallback.dep_id)
        return RecoveryResult(
            fallback.dep_id, True, cleaned, True,
            f"Default '{cur}' chưa qua kiểm → tự quay về '{fallback.dep_id}' (confirmed).",
        )

    def is_bootable(self) -> bool:
        """Có một default hoàn chỉnh để boot không (sau recover)?"""
        cur = self.current_default()
        return cur is not None and self.is_complete(cur)

    def has_half_installed(self) -> bool:
        """TRUE nếu còn bất kỳ deployment thật nào không hoàn chỉnh, hoặc còn
        thư mục .staging sót lại → vi phạm 'không có bản nửa cài'."""
        for name in os.listdir(self.deployments_dir):
            if name.startswith(".staging") or name.startswith(".tmp-"):
                return True
            if not self.is_complete(name):
                return True
        return False

    def prune_old(self, *, keep_last_confirmed: int = 2) -> List[str]:
        """Xóa deployment cũ — CHỈ giữ ``keep_last_confirmed`` bản confirmed gần nhất
        + default. KHÔNG bao giờ xóa default hay bản confirmed mới nhất (đường quay lui)."""
        cur = self.current_default()
        confirmed = [d for d in self.deployments() if d.confirmed and not d.failed]
        confirmed.sort(key=lambda d: d.created_ns, reverse=True)
        keep = {d.dep_id for d in confirmed[:max(keep_last_confirmed, 1)]}
        if cur:
            keep.add(cur)
        removed: List[str] = []
        for d in self.deployments():
            if d.dep_id not in keep:
                shutil.rmtree(self._dep_dir(d.dep_id), ignore_errors=True)
                removed.append(d.dep_id)
        return removed


# --------------------------------------------------------------------------- #
# Migration guard (PL15 §5 — dữ liệu, dry-run, backup proof, UPD-010)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Migration:
    """Mô tả một migration schema/dữ liệu đi kèm bản cập nhật."""
    migration_id: str
    version_from: int
    version_to: int
    data_paths: Tuple[str, ...] = ()
    forward_backward_compatible: bool = False  # bản cũ còn mở được dữ liệu sau migrate?
    reversible: bool = False                    # có script hạ cấp (down) đã kiểm?
    dry_run_ok: bool = False                    # đã chạy dry-run và ĐẠT?


@dataclass(frozen=True)
class BackupProof:
    """Bằng chứng backup/snapshot đã kiểm KHÔI PHỤC (không chỉ 'đã tạo')."""
    backup_id: str
    created: bool
    restore_verified: bool              # dry-run restore ra đúng hash
    covered_paths: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MigrationDecision:
    allowed: bool
    error_code: Optional[str]           # None | "UPD-010"
    reasons_vi: Tuple[str, ...]
    backup_result: str                  # preflight.backup: pass|fail|skip


class MigrationGuard:
    """Quyết định CHẶN/CHO migration dữ liệu — fail-closed theo PL15 §5.

    CHO đi tiếp CHỈ KHI tất cả đạt:
      1. Có backup đã tạo **và** restore_verified (dry-run restore đúng hash).
      2. Migration có dry-run **đạt**.
      3. Nếu migration một-chiều (không forward/backward-compat và không reversible)
         thì backup phải **phủ** đúng các data_paths (đường phục hồi duy nhất).
    Thiếu bất kỳ cái nào ⇒ ``UPD-010`` (chặn update, đòi backup + kế hoạch chuyển đổi).
    Không có migration (None) ⇒ an toàn, không cần backup.
    """

    def assess(self, migration: Optional[Migration], backup: Optional[BackupProof]) -> MigrationDecision:
        if migration is None:
            return MigrationDecision(True, None, ("Không có migration dữ liệu — an toàn.",), "skip")

        reasons: List[str] = []
        backup_ok = backup is not None and backup.created and backup.restore_verified
        if backup is None or not backup.created:
            reasons.append("Thiếu backup/snapshot dữ liệu trước migration.")
        elif not backup.restore_verified:
            reasons.append("Backup chưa được kiểm khôi phục (dry-run restore chưa đạt).")

        if not migration.dry_run_ok:
            reasons.append("Migration chưa qua dry-run đạt.")

        one_way = not (migration.forward_backward_compatible or migration.reversible)
        if one_way:
            covered = backup_ok and all(p in backup.covered_paths for p in migration.data_paths)
            if not covered:
                reasons.append(
                    "Migration một chiều (không tương thích tiến/lùi, không đảo được) "
                    "và backup không phủ dữ liệu → không có đường quay lại."
                )

        if migration.version_to <= migration.version_from:
            reasons.append("version_to phải lớn hơn version_from (migration không hợp lệ).")

        allowed = not reasons
        return MigrationDecision(
            allowed=allowed,
            error_code=None if allowed else "UPD-010",
            reasons_vi=tuple(reasons) if reasons else ("Migration an toàn: có backup kiểm khôi phục + dry-run đạt.",),
            backup_result="pass" if backup_ok else "fail",
        )


# --------------------------------------------------------------------------- #
# StagedDeployer — điều phối staged prepare / arm-switch dựa trên hợp đồng §7
# --------------------------------------------------------------------------- #
class StagedDeployer:
    """Điều phối triển khai theo bậc trên một :class:`DeploymentStore`.

    * :meth:`prepare` — contract ``verified`` → chuẩn bị deployment MỚI riêng
      (default vẫn trỏ bản cũ), chạy :class:`MigrationGuard`; không an toàn ⇒
      ``blocked`` UPD-010 và KHÔNG prepare. Đạt ⇒ contract ``staged``.
    * :meth:`arm_switch` — ``staged`` → ``reboot_pending`` + **đổi con trỏ default
      nguyên tử** sang deployment mới; GIỮ bản cũ boot được.
    Sau đó ``boot_health.BootHealthChecker`` quyết định ``completed`` / ``rolled_back``.
    """

    def __init__(
        self,
        store: DeploymentStore,
        *,
        journal: Optional[TransactionJournal] = None,
        guard: Optional[MigrationGuard] = None,
        log_fn=None,
    ):
        self.store = store
        self.journal = journal
        self.guard = guard or MigrationGuard()
        self._log_fn = log_fn
        self.logs: List[str] = []

    def log(self, msg: str) -> None:
        self.logs.append(msg)
        if self._log_fn:
            self._log_fn(msg)

    def _commit(self, contract: UpdateContract, note: str) -> None:
        if self.journal is None:
            return
        key = f"{contract.correlation_id}:{contract.update_id}:{contract.state.value}:{contract.error_code}:{note}"
        self.journal.append(contract, idempotency_key=key, note=note)

    # ------------------------------------------------------------------ #
    def prepare(
        self,
        contract: UpdateContract,
        *,
        payload_path: str,
        build: str,
        new_dep_id: Optional[str] = None,
        migration: Optional[Migration] = None,
        backup: Optional[BackupProof] = None,
        _fault_hook=None,
    ) -> Tuple[UpdateContract, Optional[str]]:
        """Chuẩn bị deployment mới (RIÊNG) sau khi đã ``verified``.

        Trả ``(contract, new_dep_id)``. Nếu migration không an toàn ⇒
        ``(blocked UPD-010, None)`` và KHÔNG tạo deployment nào."""
        if contract.state != UpdateState.VERIFIED:
            raise DeploymentError(
                f"prepare chỉ từ 'verified' (đã xác thực). Trạng thái {contract.state.value} "
                f"không được staged (không bypass)."
            )

        # 1) Migration guard TRƯỚC — chặn trước khi đụng đĩa nếu không an toàn.
        decision = self.guard.assess(migration, backup)
        if not decision.allowed:
            self.log(f"migration_guard: CHẶN {contract.update_id} -> {decision.error_code} "
                     f"({'; '.join(decision.reasons_vi)})")
            pf = Preflight(
                storage=contract.preflight.storage,
                power=contract.preflight.power,
                network=contract.preflight.network,
                backup=decision.backup_result,
            )
            blocked = contract.transition(
                UpdateState.BLOCKED, error_code=decision.error_code, preflight=pf
            )
            self._commit(blocked, f"migration_guard blocked {decision.error_code}")
            return blocked, None

        # 2) Chuẩn bị deployment MỚI thành thư mục riêng (atomic, không đụng bản chạy).
        dep_id = new_dep_id or f"{contract.update_id}::{contract.target_build}"
        with open(payload_path, "rb") as fh:
            payload = fh.read()
        self.store._write_deployment(
            dep_id, build=build, update_id=contract.update_id, payload=payload,
            confirmed=False, _fault_hook=_fault_hook,
        )
        self.log(f"stage: chuẩn bị deployment MỚI '{dep_id}' (riêng) — default vẫn "
                 f"'{self.store.current_default()}', hệ đang chạy chưa đổi.")

        # 3) Cập nhật preflight.backup (nếu migration cần) + chuyển sang staged.
        pf = Preflight(
            storage=contract.preflight.storage,
            power=contract.preflight.power,
            network=contract.preflight.network,
            backup=decision.backup_result if migration is not None else contract.preflight.backup,
        )
        from dataclasses import replace as _replace
        staged = _replace(contract, preflight=pf).validate().transition(UpdateState.STAGED)
        self._commit(staged, "staged: deployment mới sẵn sàng")
        return staged, dep_id

    def arm_switch(self, contract: UpdateContract, new_dep_id: str) -> UpdateContract:
        """``staged`` → ``reboot_pending`` + đổi con trỏ default NGUYÊN TỬ sang
        deployment mới. GIỮ bản cũ (confirmed) để còn đường quay lui."""
        if contract.state != UpdateState.STAGED:
            raise DeploymentError(f"arm_switch cần 'staged', nhận {contract.state.value}")
        if not self.store.is_complete(new_dep_id):
            raise DeploymentError(f"Từ chối chuyển sang '{new_dep_id}' chưa hoàn chỉnh.")
        prev = self.store.current_default()
        nxt = contract.transition(UpdateState.REBOOT_PENDING)
        # ĐỔI NGUYÊN TỬ: từ đây default = new (chưa confirmed). Bản prev vẫn còn,
        # confirmed → recover()/rollback luôn có đường về.
        self.store.set_default(new_dep_id)
        self.log(f"arm_switch: đổi default '{prev}' -> '{new_dep_id}' (nguyên tử); "
                 f"GIỮ '{prev}' boot được tới khi bản mới qua health.")
        self._commit(nxt, f"reboot_pending: default -> {new_dep_id}")
        return nxt

    def rollback_to_previous(self, new_dep_id: str) -> Optional[str]:
        """Đổi default về bản confirmed gần nhất (≠ new); đánh dấu new failed.
        KHÔNG xóa deployment nào (giữ chứng cứ + đường cứu hộ)."""
        prev = self.store.latest_confirmed(exclude=new_dep_id)
        if prev is None:
            return None
        self.store.mark_failed(new_dep_id)
        self.store.set_default(prev.dep_id)
        self.log(f"rollback: default -> '{prev.dep_id}' (confirmed); giữ '{new_dep_id}' "
                 f"(failed) không xóa.")
        return prev.dep_id

    def confirm(self, new_dep_id: str) -> None:
        """Bản mới qua health → đánh dấu confirmed (giữ default = new). KHÔNG tự
        xóa bản cũ (PL15 §5: không xóa deployment cũ cho tới khi bản mới qua cửa kiểm —
        và vẫn giữ ít nhất 1 bản quay lui)."""
        self.store.mark_confirmed(new_dep_id)
        self.log(f"confirm: '{new_dep_id}' qua boot-health → confirmed; giữ bản cũ làm rollback target.")


__all__ = [
    "Deployment", "DeploymentStore", "DeploymentError", "RecoveryResult",
    "Migration", "BackupProof", "MigrationGuard", "MigrationDecision",
    "StagedDeployer",
]
