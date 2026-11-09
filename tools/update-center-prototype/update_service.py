#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS Update Service — prototype quyền-giới-hạn (Phụ lục 15, U15-B).

Update Center là GIAO DIỆN; Update Service (file này) là thành phần có quyền
giới hạn thực hiện: check / download (chunk + resume) / verify (hash + chữ ký)
/ preflight (storage/power/network) / stage — đối chiếu một REPO TEST cục bộ.

NGUYÊN TẮC CỨNG (PL15 §4, §6, §9):
  * Client PIN trust root cài-từ-ISO; KHÔNG tin chỉ vì server trả 200.
  * Chữ ký / hash / hạn metadata / thu hồi / arch-model đều kiểm; BẤT KỲ cái nào
    hỏng ⇒ state='blocked' + UPD-00x đúng + TỪ CHỐI cài. KHÔNG có nút bypass.
  * KHÔNG bao giờ trả 'verified'/'completed' khi xác thực chưa thật sự đạt.
  * SmartAI KHÔNG gọi được lớp này để đổi trust/tắt chữ ký — đây là dịch vụ riêng.
  * Log che bí mật trước khi ghi.

Trạng thái: `partial` — chạy + test được trên repo giả; CHƯA nối apt/bootloader thật.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from update_contract import (
    Preflight,
    TransactionJournal,
    UpdateContract,
    UpdateState,
    new_correlation_id,
)

# sign_test_repo chứa canonical_bytes/key_id dùng chung cho verify.
from sign_test_repo import canonical_bytes, key_id as _pub_key_id


# --------------------------------------------------------------------------- #
# Che bí mật trong log (PL15 §4 "log không chứa dữ liệu riêng")
# --------------------------------------------------------------------------- #
_REDACTIONS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                re.DOTALL), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(password|passwd|token|secret|api[_-]?key|otp)\s*[=:]\s*\S+"),
     r"\1=[REDACTED]"),
    (re.compile(r"/home/[^/\s]+"), "/home/[USER]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
    (re.compile(r"\b[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}\b"), "[REDACTED_MAC]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[REDACTED_EMAIL]"),
]


def redact(text: str) -> str:
    """Che PEM key / Bearer / password|token|secret|otp / home path / IP / MAC / email."""
    out = text
    for pat, repl in _REDACTIONS:
        out = pat.sub(repl, out)
    return out


# --------------------------------------------------------------------------- #
# Hồ sơ thiết bị + lỗi dịch vụ
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DeviceProfile:
    architecture: str = "x86_64"
    model: str = "namios-ref-pc"
    current_deployment: str = "namios-1.0-x86_64-stable-0000"
    channel: str = "stable"


class VerificationError(Exception):
    """Lỗi xác thực mang theo mã UPD-00x để chặn + ghi nhật ký."""

    def __init__(self, code: str, reason_vi: str):
        super().__init__(f"{code}: {reason_vi}")
        self.code = code
        self.reason_vi = reason_vi


class DownloadInterrupted(Exception):
    """Mô phỏng đứt mạng/kill giữa chừng — phần đã tải vẫn giữ để resume."""


# --------------------------------------------------------------------------- #
# Dịch vụ cập nhật
# --------------------------------------------------------------------------- #
class UpdateService:
    def __init__(
        self,
        repo_dir: str,
        trust_root_path: str,
        device: DeviceProfile,
        *,
        cache_dir: Optional[str] = None,
        journal: Optional[TransactionJournal] = None,
        user_policy: str = "auto_download_ask_install",
        now_fn=None,
        log_fn=None,
    ):
        self.repo = repo_dir
        self.device = device
        self.user_policy = user_policy
        self.cache_dir = cache_dir or os.path.join(repo_dir, "_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.journal = journal or TransactionJournal(
            os.path.join(self.cache_dir, "update-journal.jsonl")
        )
        self._now = now_fn or (lambda: _dt.datetime.now(_dt.timezone.utc))
        self._log_fn = log_fn
        self.logs: List[str] = []
        self._trust_pub, self._trust_key_id = self._load_trust_root(trust_root_path)

    # ------------------------------------------------------------------ #
    # Log (đã che bí mật)
    # ------------------------------------------------------------------ #
    def log(self, msg: str) -> None:
        safe = redact(msg)
        self.logs.append(safe)
        if self._log_fn:
            self._log_fn(safe)

    # ------------------------------------------------------------------ #
    # Trust root cài-từ-ISO (client pin)
    # ------------------------------------------------------------------ #
    def _load_trust_root(self, path: str) -> Tuple[Ed25519PublicKey, str]:
        with open(path, "r", encoding="utf-8") as fh:
            root = json.load(fh)
        pub = serialization.load_pem_public_key(root["public_key_pem"].encode("ascii"))
        if not isinstance(pub, Ed25519PublicKey):
            raise VerificationError("UPD-003", "Trust root không phải khoá ed25519 hợp lệ")
        kid = _pub_key_id(pub)
        if kid != root.get("key_id"):
            raise VerificationError("UPD-003", "key_id trust root không khớp public key")
        return pub, kid

    def _verify_signature(self, obj: dict, sig_hex: str, what: str) -> None:
        """Ném VerificationError(UPD-003) nếu chữ ký không hợp lệ hoặc khoá không được tin."""
        if obj.get("key_id") != self._trust_key_id:
            raise VerificationError(
                "UPD-003", f"{what}: khoá ký không nằm trong trust root (key_id lạ)"
            )
        try:
            self._trust_pub.verify(bytes.fromhex(sig_hex), canonical_bytes(obj))
        except (InvalidSignature, ValueError):
            raise VerificationError("UPD-003", f"{what}: chữ ký không hợp lệ")

    # ------------------------------------------------------------------ #
    # Đọc repo (cục bộ, mô phỏng mạng)
    # ------------------------------------------------------------------ #
    def _read_manifest(self, update_id: str) -> Tuple[dict, str]:
        mpath = os.path.join(self.repo, "metadata", f"{update_id}.manifest.json")
        spath = os.path.join(self.repo, "metadata", f"{update_id}.manifest.sig")
        if not (os.path.exists(mpath) and os.path.exists(spath)):
            raise VerificationError("UPD-001", "Không đọc được metadata bản cập nhật")
        with open(mpath, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        with open(spath, "r", encoding="utf-8") as fh:
            sig = json.load(fh)["sig"]
        return manifest, sig

    # ------------------------------------------------------------------ #
    # 1) CHECK — có bản mới? (available) ; mạng hỏng ⇒ UPD-001
    # ------------------------------------------------------------------ #
    def check(
        self,
        update_id: str,
        *,
        network_reachable: bool = True,
        correlation_id: Optional[str] = None,
    ) -> UpdateContract:
        cid = correlation_id or new_correlation_id()
        if not network_reachable:
            return self._blocked_fresh(
                update_id, cid, "UPD-001",
                network="fail",
                reason="Không tới được server cập nhật (mạng/captive portal)",
            )
        try:
            manifest, _sig = self._read_manifest(update_id)
        except VerificationError as e:
            return self._blocked_fresh(update_id, cid, e.code, reason=e.reason_vi,
                                       network="fail" if e.code == "UPD-001" else "unknown")
        self.log(f"check: thấy bản {update_id} kênh={manifest.get('channel')} "
                 f"metadata_version={manifest.get('metadata_version')}")
        contract = UpdateContract(
            update_id=update_id,
            component=manifest.get("component", "os"),
            channel=manifest.get("channel", self.device.channel),
            target_build=manifest.get("target_build", "unresolved"),
            architecture=manifest.get("architecture", self.device.architecture),
            metadata_version=int(manifest.get("metadata_version", 1)),
            # Hash trong manifest CHƯA được tin cho tới verify(); mang theo để UI
            # hiển thị, nhưng signature_status='unknown' đến khi kiểm xong.
            payload_hash=manifest["payload"]["hash"],
            signature_status="unknown",
            preflight=Preflight(),
            state=UpdateState.AVAILABLE,
            rollback_target=self.device.current_deployment or "none",
            user_policy=self.user_policy,
            correlation_id=cid,
        ).validate()
        self._commit(contract, "check: available")
        return contract

    # ------------------------------------------------------------------ #
    # 2) DOWNLOAD — theo chunk, resume được
    # ------------------------------------------------------------------ #
    def download(
        self,
        contract: UpdateContract,
        *,
        chunk_size: int = 4096,
        interrupt_after_bytes: Optional[int] = None,
    ) -> UpdateContract:
        """Tải payload theo chunk vào cache (.part). ``interrupt_after_bytes`` mô
        phỏng đứt mạng: ném DownloadInterrupted, GIỮ phần đã tải để gọi lại resume."""
        if contract.state not in (UpdateState.AVAILABLE, UpdateState.DOWNLOADING):
            raise RuntimeError(f"download chỉ từ available/downloading, nhận {contract.state.value}")
        manifest, _ = self._read_manifest(contract.update_id)
        src = os.path.join(self.repo, manifest["payload"]["path"])
        total = manifest["payload"]["size"]
        part = os.path.join(self.cache_dir, f"{contract.update_id}.part")
        done = os.path.join(self.cache_dir, f"{contract.update_id}.payload")

        if os.path.exists(done):
            self.log(f"download: {contract.update_id} đã có trong cache, bỏ qua tải lại")
            return self._to_downloading(contract)

        offset = os.path.getsize(part) if os.path.exists(part) else 0
        if offset:
            self.log(f"download: resume {contract.update_id} từ {offset}/{total} byte")
        else:
            self.log(f"download: bắt đầu {contract.update_id} 0/{total} byte")

        written = offset
        with open(src, "rb") as fin, open(part, "ab") as fout:
            fin.seek(offset)
            while written < total:
                want = min(chunk_size, total - written)  # chỉ nhận đúng size đã ký
                chunk = fin.read(want)
                if not chunk:
                    break
                fout.write(chunk)
                written += len(chunk)
                fout.flush()
                os.fsync(fout.fileno())
                if interrupt_after_bytes is not None and written >= interrupt_after_bytes:
                    self.log(f"download: ĐỨT ở {written}/{total} byte — giữ phần hợp lệ để tiếp tục")
                    raise DownloadInterrupted(f"interrupted at {written}/{total}")

        if written != total:
            # Thiếu byte — chưa đủ, không coi là xong (resume/retry).
            raise DownloadInterrupted(f"incomplete {written}/{total}")
        os.replace(part, done)
        self.log(f"download: xong {contract.update_id} {written}/{total} byte")
        return self._to_downloading(contract)

    def _to_downloading(self, contract: UpdateContract) -> UpdateContract:
        if contract.state == UpdateState.DOWNLOADING:
            return contract
        nxt = contract.transition(UpdateState.DOWNLOADING)
        self._commit(nxt, "download: downloading")
        return nxt

    # ------------------------------------------------------------------ #
    # 3) VERIFY — hash + chữ ký + hạn + thu hồi + arch/model (fail-closed)
    # ------------------------------------------------------------------ #
    def verify(self, contract: UpdateContract) -> UpdateContract:
        """Kiểm theo thứ tự fail-closed. Bất kỳ bước nào hỏng ⇒ state='blocked' +
        UPD-00x, TỪ CHỐI đi tiếp. CHỈ khi TẤT CẢ đạt mới sang 'verified'."""
        if contract.state != UpdateState.DOWNLOADING:
            raise RuntimeError(f"verify chỉ từ downloading, nhận {contract.state.value}")
        try:
            manifest, sig = self._read_manifest(contract.update_id)

            # (a) Chữ ký metadata TRƯỚC — chưa tin nội dung manifest cho tới khi ký đạt.
            self._verify_signature(manifest, sig, "manifest")

            # (b) Hạn metadata / clock. Không parse được ⇒ coi như "không xác minh được" (UPD-004).
            self._check_expiry(manifest)

            # (c) Thu hồi (revocation) — danh sách đã ký.
            self._check_revocation(contract.update_id, manifest)

            # (d) Arch + model khớp máy.
            self._check_arch_model(manifest)

            # (e) Hash payload ĐÃ TẢI khớp hash ĐÃ KÝ.
            self._check_payload_hash(contract.update_id, manifest)

        except VerificationError as e:
            self.log(f"verify: CHẶN {contract.update_id} -> {e.code} ({e.reason_vi})")
            blocked = contract.transition(
                UpdateState.BLOCKED, error_code=e.code, signature_status="failed"
            )
            self._commit(blocked, f"verify: blocked {e.code}")
            return blocked

        self.log(f"verify: ĐẠT {contract.update_id} — chữ ký + hash + hạn + thu hồi + arch/model OK")
        verified = contract.transition(UpdateState.VERIFIED, signature_status="verified")
        self._commit(verified, "verify: verified")
        return verified

    def _check_expiry(self, manifest: dict) -> None:
        raw = manifest.get("expires")
        if not raw:
            raise VerificationError("UPD-004", "Metadata thiếu hạn sử dụng (không xác minh được thời hạn)")
        try:
            exp = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            raise VerificationError("UPD-004", "Hạn metadata sai định dạng (clock/nguồn không rõ)")
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=_dt.timezone.utc)
        if self._now() > exp:
            raise VerificationError("UPD-004", f"Metadata đã hết hạn ({raw})")

    def _check_revocation(self, update_id: str, manifest: dict) -> None:
        rpath = os.path.join(self.repo, "revocation.json")
        spath = os.path.join(self.repo, "revocation.sig")
        if not (os.path.exists(rpath) and os.path.exists(spath)):
            # Không có danh sách thu hồi đã ký ⇒ không khẳng định "sạch".
            # Fail-closed cho an toàn chuỗi cung ứng.
            raise VerificationError("UPD-009", "Thiếu danh sách thu hồi đã ký (không xác minh được)")
        with open(rpath, "r", encoding="utf-8") as fh:
            rev = json.load(fh)
        with open(spath, "r", encoding="utf-8") as fh:
            sig = json.load(fh)["sig"]
        self._verify_signature(rev, sig, "revocation")
        if update_id in rev.get("revoked_update_ids", []):
            raise VerificationError("UPD-009", f"Bản {update_id} đã bị thu hồi")
        if manifest.get("key_id") in rev.get("revoked_key_ids", []):
            raise VerificationError("UPD-009", "Khoá ký bản này đã bị thu hồi")

    def _check_arch_model(self, manifest: dict) -> None:
        if manifest.get("architecture") != self.device.architecture:
            raise VerificationError(
                "UPD-005",
                f"Kiến trúc bản ({manifest.get('architecture')}) ≠ máy ({self.device.architecture})",
            )
        whitelist = manifest.get("model_whitelist", ["*"])
        if whitelist != ["*"] and self.device.model not in whitelist:
            raise VerificationError(
                "UPD-005", f"Model máy ({self.device.model}) không thuộc danh sách bản này"
            )

    def _check_payload_hash(self, update_id: str, manifest: dict) -> None:
        done = os.path.join(self.cache_dir, f"{update_id}.payload")
        if not os.path.exists(done):
            raise VerificationError("UPD-003", "Thiếu payload đã tải để kiểm hash")
        h = hashlib.sha256()
        with open(done, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        got = "sha256:" + h.hexdigest()
        want = manifest["payload"]["hash"]
        if got != want:
            raise VerificationError("UPD-003", "Hash payload không khớp hash đã ký (payload bị sửa)")

    # ------------------------------------------------------------------ #
    # 4) PREFLIGHT — storage/power/network
    # ------------------------------------------------------------------ #
    def preflight(
        self,
        contract: UpdateContract,
        *,
        storage: str = "pass",
        power: str = "pass",
        network: str = "pass",
        backup: Optional[str] = None,
    ) -> UpdateContract:
        """Kiểm tiền-đề cài. storage fail⇒UPD-002, network fail⇒UPD-001,
        power fail (firmware)⇒UPD-006. Chặn giữ bản hiện tại."""
        pf = Preflight(storage=storage, power=power, network=network, backup=backup)
        pf.validate()
        code = None
        reason = ""
        if storage == "fail":
            code, reason = "UPD-002", "Không đủ dung lượng cho staged/rollback"
        elif network == "fail":
            code, reason = "UPD-001", "Mạng không đạt để tải/cài"
        elif power == "fail" and contract.component == "firmware":
            code, reason = "UPD-006", "Pin/nguồn không đạt để cập nhật firmware"
        if code:
            self.log(f"preflight: CHẶN {contract.update_id} -> {code} ({reason})")
            blocked = contract.transition(UpdateState.BLOCKED, error_code=code, preflight=pf)
            self._commit(blocked, f"preflight: blocked {code}")
            return blocked
        # Preflight đạt: cập nhật preflight, giữ nguyên state (không phải chuyển state).
        updated = self._with_preflight(contract, pf)
        self.log(f"preflight: đạt {contract.update_id} storage={storage} power={power} network={network}")
        return updated

    def _with_preflight(self, contract: UpdateContract, pf: Preflight) -> UpdateContract:
        from dataclasses import replace as _replace
        updated = _replace(contract, preflight=pf).validate()
        self._commit(updated, "preflight: pass")
        return updated

    # ------------------------------------------------------------------ #
    # 5) STAGE — verified -> staged (staged-install mô phỏng, chưa đụng hệ đang chạy)
    # ------------------------------------------------------------------ #
    def stage(self, contract: UpdateContract) -> UpdateContract:
        if contract.state != UpdateState.VERIFIED:
            # Không có đường stage từ 'blocked' — transition sẽ ném; chặn tường minh cho rõ.
            raise RuntimeError(
                f"stage chỉ từ 'verified'. Trạng thái {contract.state.value} "
                f"không được cài (không bypass)."
            )
        staged = contract.transition(UpdateState.STAGED)
        self.log(f"stage: {contract.update_id} đã chuẩn bị (staged) — chưa đổi hệ đang chạy")
        self._commit(staged, "stage: staged")
        return staged

    def arm_reboot(self, contract: UpdateContract) -> UpdateContract:
        nxt = contract.transition(UpdateState.REBOOT_PENDING)
        self._commit(nxt, "reboot_pending")
        return nxt

    # ------------------------------------------------------------------ #
    # 6) BOOT CHECK — sau reboot; completed CHỈ khi health đạt, else rolled_back
    # ------------------------------------------------------------------ #
    def boot_check(self, contract: UpdateContract, *, health_ok: bool) -> UpdateContract:
        """Giả lập boot health (U15-C làm thật). health_ok=False ⇒ rolled_back (UPD-008
        được dùng ở lớp báo cáo); KHÔNG tự nâng completed khi chưa qua cửa kiểm."""
        if contract.state == UpdateState.REBOOT_PENDING:
            contract = contract.transition(UpdateState.BOOT_CHECK)
            self._commit(contract, "boot_check: checking")
        if contract.state != UpdateState.BOOT_CHECK:
            raise RuntimeError(f"boot_check cần reboot_pending/boot_check, nhận {contract.state.value}")
        if health_ok:
            done = contract.transition(UpdateState.COMPLETED)
            self.log(f"boot_check: ĐẠT {contract.update_id} -> completed (boot health OK)")
            self._commit(done, "boot_check: completed")
            return done
        rolled = contract.transition(UpdateState.ROLLED_BACK)
        self.log(f"boot_check: HỎNG {contract.update_id} -> rolled_back về {contract.rollback_target}")
        self._commit(rolled, "boot_check: rolled_back")
        return rolled

    # ------------------------------------------------------------------ #
    # Tiện ích nội bộ
    # ------------------------------------------------------------------ #
    def _commit(self, contract: UpdateContract, note: str) -> None:
        key = f"{contract.correlation_id}:{contract.update_id}:{contract.state.value}:{contract.error_code}"
        self.journal.append(contract, idempotency_key=key, note=note)

    def _blocked_fresh(
        self, update_id: str, cid: str, code: str, *, reason: str,
        network: str = "unknown",
    ) -> UpdateContract:
        self.log(f"CHẶN {update_id} ngay từ đầu -> {code} ({reason})")
        contract = UpdateContract(
            update_id=update_id,
            component="os",
            channel=self.device.channel,
            target_build="unresolved",
            architecture=self.device.architecture,
            metadata_version=1,
            payload_hash="sha256:" + "0" * 64,
            signature_status="unknown",
            preflight=Preflight(network=network),
            state=UpdateState.BLOCKED,
            error_code=code,
            rollback_target=self.device.current_deployment or "none",
            user_policy=self.user_policy,
            correlation_id=cid,
        ).validate()
        self._commit(contract, f"blocked {code}")
        return contract


# --------------------------------------------------------------------------- #
# Demo chạy tay (không phải test). `python3 update_service.py`
# --------------------------------------------------------------------------- #
def _demo() -> int:
    import tempfile
    from sign_test_repo import build_test_repo

    tmp = tempfile.mkdtemp(prefix="namios-upd-demo-")
    repo = os.path.join(tmp, "repo")
    info = build_test_repo(repo)
    svc = UpdateService(repo, info["root_path"], DeviceProfile(), cache_dir=os.path.join(tmp, "cache"))

    print("== LUỒNG HỢP LỆ ==")
    c = svc.check(info["update_id"])
    c = svc.download(c)
    c = svc.verify(c)
    c = svc.preflight(c, storage="pass", power="pass", network="pass")
    c = svc.stage(c)
    c = svc.arm_reboot(c)
    c = svc.boot_check(c, health_ok=True)
    print("  state cuối:", c.state.value, "| error:", c.error_code)

    print("\n== PAYLOAD BỊ SỬA (mong đợi UPD-003 + blocked) ==")
    tampered = os.path.join(repo, "targets", f"{info['update_id']}.payload")
    data = bytearray(open(tampered, "rb").read())
    data[0:4] = b"EVIL"  # sửa tại chỗ, giữ nguyên size đã ký -> hash lệch
    with open(tampered, "wb") as fh:
        fh.write(data)
    # Xoá cache để tải lại bản đã sửa.
    cache_payload = os.path.join(tmp, "cache", f"{info['update_id']}.payload")
    if os.path.exists(cache_payload):
        os.remove(cache_payload)
    c2 = svc.check(info["update_id"])
    c2 = svc.download(c2)
    c2 = svc.verify(c2)
    print("  state:", c2.state.value, "| error:", c2.error_code)

    print("\n== LOG (đã che bí mật) ==")
    for line in svc.logs[-6:]:
        print("  ", line)
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(_demo())
