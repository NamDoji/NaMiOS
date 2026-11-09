#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS Update Center — hợp đồng dữ liệu + máy trạng thái (Phụ lục 15 §7).

Module THUẦN (không I/O mạng, không apt thật) định nghĩa:
  * UpdateState / UpdateContract — cấu trúc §7, validate MỌI field.
  * VALID_TRANSITIONS — chỉ cho phép chuyển trạng thái hợp lệ:
        available -> downloading -> verified -> staged
                  -> reboot_pending -> boot_check -> completed | rolled_back | blocked
    'blocked' tới được từ mọi bước chưa-kết-thúc (chặn khi xác thực/preflight hỏng).
  * TransactionJournal — append-only JSONL, idempotency + resume-sau-reboot.

BẤT BIẾN AN TOÀN (PL15):
  * state='completed' CHỈ tới được từ 'boot_check' (boot health đạt) — KHÔNG bao
    giờ tự nâng 'completed' chỉ vì một tool tải/cài trả về success.
  * state='verified' CHỈ hợp lệ khi signature_status=='verified'.
  * state='blocked' ⇒ error_code != None (và ngược lại error_code != None ⇒ blocked).
  * Không có đường chuyển "blocked -> staged/completed" (không bypass).

Trạng thái triển khai: `partial` — prototype chạy được + test được; CHƯA nối vào
apt/rpm-ostree/bootloader thật. Không tuyên bố đã có updater sản phẩm.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Enums & hằng số (giữ khớp update_contract.schema.json)
# --------------------------------------------------------------------------- #
SCHEMA_VERSION = 1


class UpdateState(str, Enum):
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    VERIFIED = "verified"
    STAGED = "staged"
    REBOOT_PENDING = "reboot_pending"
    BOOT_CHECK = "boot_check"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


#: Trạng thái kết thúc — không chuyển tiếp được nữa.
TERMINAL_STATES = frozenset(
    {UpdateState.COMPLETED, UpdateState.ROLLED_BACK, UpdateState.BLOCKED}
)

#: Bảng chuyển hợp lệ. Mọi chuyển ngoài bảng này bị từ chối.
VALID_TRANSITIONS: Dict[UpdateState, frozenset] = {
    UpdateState.AVAILABLE: frozenset({UpdateState.DOWNLOADING, UpdateState.BLOCKED}),
    UpdateState.DOWNLOADING: frozenset({UpdateState.VERIFIED, UpdateState.BLOCKED}),
    UpdateState.VERIFIED: frozenset({UpdateState.STAGED, UpdateState.BLOCKED}),
    UpdateState.STAGED: frozenset({UpdateState.REBOOT_PENDING, UpdateState.BLOCKED}),
    UpdateState.REBOOT_PENDING: frozenset({UpdateState.BOOT_CHECK, UpdateState.BLOCKED}),
    UpdateState.BOOT_CHECK: frozenset(
        {UpdateState.COMPLETED, UpdateState.ROLLED_BACK, UpdateState.BLOCKED}
    ),
    UpdateState.COMPLETED: frozenset(),
    UpdateState.ROLLED_BACK: frozenset(),
    UpdateState.BLOCKED: frozenset(),
}

COMPONENTS = frozenset({"os", "app", "ai", "firmware", "driver", "recipe"})
CHANNELS = frozenset({"testing", "pilot", "stable", "security"})
ARCHITECTURES = frozenset({"x86_64", "aarch64", "riscv64"})
SIGNATURE_STATUS = frozenset({"verified", "failed", "unknown"})
PREFLIGHT_RESULTS = frozenset({"pass", "fail", "unknown", "skip"})
USER_POLICIES = frozenset(
    {"notify", "auto_download_ask_install", "auto_install_safe", "auto_scheduled"}
)

#: UPD-001..010 (xem update-error-catalog.json).
ERROR_CODES = frozenset(f"UPD-{n:03d}" for n in range(1, 11))

_PAYLOAD_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ERROR_CODE_RE = re.compile(r"^UPD-0(0[1-9]|10)$")


class ContractError(ValueError):
    """Field không hợp lệ theo §7 / schema."""


class IllegalTransition(RuntimeError):
    """Chuyển trạng thái không nằm trong VALID_TRANSITIONS (hoặc vi phạm bất biến)."""


# --------------------------------------------------------------------------- #
# Hợp đồng dữ liệu
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Preflight:
    storage: str = "unknown"
    power: str = "unknown"
    network: str = "unknown"
    backup: Optional[str] = None  # tuỳ chọn (U15-C)

    def validate(self) -> None:
        for name in ("storage", "power", "network"):
            val = getattr(self, name)
            if val not in PREFLIGHT_RESULTS:
                raise ContractError(f"preflight.{name} không hợp lệ: {val!r}")
        if self.backup is not None and self.backup not in PREFLIGHT_RESULTS:
            raise ContractError(f"preflight.backup không hợp lệ: {self.backup!r}")

    def to_dict(self) -> dict:
        d = {"storage": self.storage, "power": self.power, "network": self.network}
        if self.backup is not None:
            d["backup"] = self.backup
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Preflight":
        if not isinstance(d, dict):
            raise ContractError("preflight phải là object")
        extra = set(d) - {"storage", "power", "network", "backup"}
        if extra:
            raise ContractError(f"preflight có field lạ: {sorted(extra)}")
        return cls(
            storage=d.get("storage", "unknown"),
            power=d.get("power", "unknown"),
            network=d.get("network", "unknown"),
            backup=d.get("backup"),
        )


@dataclass(frozen=True)
class UpdateContract:
    """Một bản ghi hợp đồng cập nhật (PL15 §7). Bất biến (frozen) — mọi chuyển
    trạng thái tạo bản sao mới qua :meth:`transition`."""

    update_id: str
    component: str
    channel: str
    target_build: str
    architecture: str
    metadata_version: int
    payload_hash: str
    signature_status: str
    preflight: Preflight
    state: UpdateState
    rollback_target: str
    user_policy: str
    correlation_id: str
    error_code: Optional[str] = None
    schema_version: int = SCHEMA_VERSION

    # ------------------------------------------------------------------ #
    # Validate mọi field
    # ------------------------------------------------------------------ #
    def validate(self) -> "UpdateContract":
        if self.schema_version != SCHEMA_VERSION:
            raise ContractError(
                f"schema_version chỉ chấp nhận {SCHEMA_VERSION}, nhận {self.schema_version!r}"
            )
        if not isinstance(self.update_id, str) or not (1 <= len(self.update_id) <= 200):
            raise ContractError("update_id phải là chuỗi 1..200 ký tự")
        if self.component not in COMPONENTS:
            raise ContractError(f"component không hợp lệ: {self.component!r}")
        if self.channel not in CHANNELS:
            raise ContractError(f"channel không hợp lệ: {self.channel!r}")
        if not isinstance(self.target_build, str) or not self.target_build:
            raise ContractError("target_build không được rỗng ('unresolved' hợp lệ)")
        if self.architecture not in ARCHITECTURES:
            raise ContractError(f"architecture không hợp lệ: {self.architecture!r}")
        if not isinstance(self.metadata_version, int) or isinstance(
            self.metadata_version, bool
        ) or self.metadata_version < 1:
            raise ContractError("metadata_version phải là số nguyên >= 1")
        if not _PAYLOAD_HASH_RE.match(self.payload_hash):
            raise ContractError("payload_hash phải dạng 'sha256:<64 hex>'")
        if self.signature_status not in SIGNATURE_STATUS:
            raise ContractError(f"signature_status không hợp lệ: {self.signature_status!r}")
        if not isinstance(self.preflight, Preflight):
            raise ContractError("preflight phải là Preflight")
        self.preflight.validate()
        if not isinstance(self.state, UpdateState):
            raise ContractError(f"state không hợp lệ: {self.state!r}")
        if self.error_code is not None and not _ERROR_CODE_RE.match(self.error_code):
            raise ContractError(f"error_code không hợp lệ: {self.error_code!r}")
        if not isinstance(self.rollback_target, str) or not self.rollback_target:
            raise ContractError("rollback_target không được rỗng ('none' hợp lệ)")
        if self.user_policy not in USER_POLICIES:
            raise ContractError(f"user_policy không hợp lệ: {self.user_policy!r}")
        if not isinstance(self.correlation_id, str) or not self.correlation_id:
            raise ContractError("correlation_id không được rỗng")

        # --- bất biến liên-field ---
        if self.state == UpdateState.BLOCKED and self.error_code is None:
            raise ContractError("state='blocked' ⇒ error_code bắt buộc != null")
        if self.state != UpdateState.BLOCKED and self.error_code is not None:
            raise ContractError(
                "error_code chỉ được đặt cùng state='blocked' (lỗi đã chặn)"
            )
        # 'verified' và các state sau nó bắt buộc chữ ký đã xác minh.
        requires_verified_sig = {
            UpdateState.VERIFIED,
            UpdateState.STAGED,
            UpdateState.REBOOT_PENDING,
            UpdateState.BOOT_CHECK,
            UpdateState.COMPLETED,
        }
        if self.state in requires_verified_sig and self.signature_status != "verified":
            raise ContractError(
                f"state='{self.state.value}' đòi signature_status='verified', "
                f"nhận {self.signature_status!r}"
            )
        return self

    # ------------------------------------------------------------------ #
    # Chuyển trạng thái an toàn
    # ------------------------------------------------------------------ #
    def transition(
        self,
        new_state: UpdateState,
        *,
        error_code: Optional[str] = None,
        signature_status: Optional[str] = None,
        preflight: Optional[Preflight] = None,
    ) -> "UpdateContract":
        """Trả về bản sao ở ``new_state`` nếu hợp lệ; nếu không, ném
        :class:`IllegalTransition`. KHÔNG bao giờ cho phép 'blocked'->* hay nhảy cóc."""
        if not isinstance(new_state, UpdateState):
            raise IllegalTransition(f"new_state không hợp lệ: {new_state!r}")
        allowed = VALID_TRANSITIONS[self.state]
        if new_state not in allowed:
            raise IllegalTransition(
                f"Chuyển {self.state.value} -> {new_state.value} KHÔNG hợp lệ "
                f"(cho phép: {sorted(s.value for s in allowed) or 'không có — trạng thái kết thúc'})"
            )
        # 'completed' chỉ từ boot_check.
        if new_state == UpdateState.COMPLETED and self.state != UpdateState.BOOT_CHECK:
            raise IllegalTransition("'completed' chỉ tới được sau 'boot_check' (boot health đạt)")

        new_sig = signature_status if signature_status is not None else self.signature_status
        new_pre = preflight if preflight is not None else self.preflight
        if new_state == UpdateState.BLOCKED:
            if error_code is None:
                raise IllegalTransition("chuyển sang 'blocked' bắt buộc error_code")
            new_err = error_code
        else:
            # Rời khỏi lỗi không mang error_code (chỉ blocked mới có).
            new_err = None
        candidate = replace(
            self,
            state=new_state,
            error_code=new_err,
            signature_status=new_sig,
            preflight=new_pre,
        )
        return candidate.validate()

    # ------------------------------------------------------------------ #
    # (De)serialize
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "update_id": self.update_id,
            "component": self.component,
            "channel": self.channel,
            "target_build": self.target_build,
            "architecture": self.architecture,
            "metadata_version": self.metadata_version,
            "payload_hash": self.payload_hash,
            "signature_status": self.signature_status,
            "preflight": self.preflight.to_dict(),
            "state": self.state.value,
            "error_code": self.error_code,
            "rollback_target": self.rollback_target,
            "user_policy": self.user_policy,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UpdateContract":
        if not isinstance(d, dict):
            raise ContractError("hợp đồng phải là object")
        required = {
            "schema_version", "update_id", "component", "channel", "target_build",
            "architecture", "metadata_version", "payload_hash", "signature_status",
            "preflight", "state", "error_code", "rollback_target", "user_policy",
            "correlation_id",
        }
        missing = required - set(d)
        if missing:
            raise ContractError(f"thiếu field bắt buộc: {sorted(missing)}")
        extra = set(d) - required
        if extra:
            raise ContractError(f"field lạ (additionalProperties=false): {sorted(extra)}")
        state_raw = d["state"]
        try:
            state = UpdateState(state_raw)
        except ValueError:
            raise ContractError(f"state không hợp lệ: {state_raw!r}")
        obj = cls(
            schema_version=d["schema_version"],
            update_id=d["update_id"],
            component=d["component"],
            channel=d["channel"],
            target_build=d["target_build"],
            architecture=d["architecture"],
            metadata_version=d["metadata_version"],
            payload_hash=d["payload_hash"],
            signature_status=d["signature_status"],
            preflight=Preflight.from_dict(d["preflight"]),
            state=state,
            error_code=d["error_code"],
            rollback_target=d["rollback_target"],
            user_policy=d["user_policy"],
            correlation_id=d["correlation_id"],
        )
        return obj.validate()


# --------------------------------------------------------------------------- #
# Journal: append-only, idempotency + resume sau reboot
# --------------------------------------------------------------------------- #
def new_correlation_id(rand: Optional[str] = None) -> str:
    """Dạng 'YYYYmmdd-HHMMSS-<pid>-<rand>' (PL15 §7)."""
    ts = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    r = rand if rand is not None else os.urandom(3).hex()
    return f"{ts}-{os.getpid()}-{r}"


class TransactionJournal:
    """Nhật ký giao dịch cập nhật, bền qua reboot.

    Mỗi dòng là một JSON record: snapshot đầy đủ hợp đồng + idempotency_key.
    * ``append`` bỏ qua (no-op) nếu idempotency_key đã tồn tại → an toàn khi
      chạy lại sau khi crash giữa chừng.
    * ``resume`` dựng lại hợp đồng mới nhất của một update_id sau reboot.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8"):
                pass

    # -- đọc --
    def _records(self) -> List[dict]:
        out: List[dict] = []
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def seen_key(self, idempotency_key: str) -> bool:
        return any(r.get("idempotency_key") == idempotency_key for r in self._records())

    def records_for(self, update_id: str) -> List[dict]:
        return [r for r in self._records() if r.get("update_id") == update_id]

    def resume(self, update_id: str) -> Optional[UpdateContract]:
        """Hợp đồng mới nhất của ``update_id`` dựng lại từ journal (sau reboot)."""
        recs = self.records_for(update_id)
        if not recs:
            return None
        return UpdateContract.from_dict(recs[-1]["snapshot"])

    # -- ghi --
    def append(
        self,
        contract: UpdateContract,
        *,
        idempotency_key: str,
        note: str = "",
    ) -> Tuple[bool, UpdateContract]:
        """Ghi snapshot. Trả (đã_ghi, hợp_đồng). idempotency_key trùng ⇒ (False, snapshot_cũ)."""
        contract.validate()
        if self.seen_key(idempotency_key):
            # Idempotent: giao dịch này đã commit rồi.
            for r in reversed(self._records()):
                if r.get("idempotency_key") == idempotency_key:
                    return False, UpdateContract.from_dict(r["snapshot"])
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
            "idempotency_key": idempotency_key,
            "update_id": contract.update_id,
            "correlation_id": contract.correlation_id,
            "state": contract.state.value,
            "error_code": contract.error_code,
            "note": note,
            "snapshot": contract.to_dict(),
        }
        # Ghi + flush + fsync để bền qua mất điện (best-effort).
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return True, contract


__all__ = [
    "SCHEMA_VERSION", "UpdateState", "TERMINAL_STATES", "VALID_TRANSITIONS",
    "COMPONENTS", "CHANNELS", "ARCHITECTURES", "SIGNATURE_STATUS",
    "PREFLIGHT_RESULTS", "USER_POLICIES", "ERROR_CODES",
    "ContractError", "IllegalTransition", "Preflight", "UpdateContract",
    "TransactionJournal", "new_correlation_id",
]
