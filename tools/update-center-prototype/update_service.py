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
# MỞ RỘNG (U19-05, PL15 §3) — tín hiệu preflight đĩa/khởi-động mở rộng.
#
# Preflight §7 hợp đồng chỉ có storage/power/network/backup (giữ schema ổn định,
# KHÔNG đổi §7/update_contract.schema.json). dual-boot + mã hóa ổ CHƯA có field
# riêng; hàm THUẦN dưới đây đánh giá các tín hiệu đó rồi ánh xạ về 'storage'
# (UPD-002) sẵn có — vì bản chất giống nhau: "đĩa/khởi-động chưa an toàn để
# staged". Độ chi tiết mã lỗi riêng cho dual-boot/mã hóa là việc làm sau, cần
# phần cứng thật để xác nhận hành vi đúng (xem báo cáo U19-05 — nhóm cần HW).
# --------------------------------------------------------------------------- #
def assess_disk_safety(
    *,
    dual_boot_other_os_detected: bool = False,
    disk_encrypted_and_locked: bool = False,
    disk_errors_detected: bool = False,
) -> Tuple[str, str]:
    """Trả (``storage`` result 'pass'|'fail', lý do tiếng Việt) để truyền vào
    :meth:`UpdateService.preflight`. KHÔNG tự sửa/xóa gì — THUẦN đánh giá."""
    reasons: List[str] = []
    if disk_errors_detected:
        reasons.append("Ổ đĩa báo lỗi (SMART/hệ thống tệp)")
    if disk_encrypted_and_locked:
        reasons.append("Ổ đã mã hoá nhưng chưa mở khoá — không ghi vùng staged an toàn")
    if dual_boot_other_os_detected:
        reasons.append("Phát hiện hệ điều hành khác (dual boot) — chưa xác nhận an toàn boot-entry")
    if reasons:
        return "fail", "; ".join(reasons)
    return "pass", "Không phát hiện rủi ro đĩa/khởi động (dual boot/mã hoá/lỗi ổ)"


# --------------------------------------------------------------------------- #
# MỞ RỘNG (U19-02, PL15 §3 + UPDATE-CENTER-UI.md §1) — lịch khởi động lại bền
# qua reboot: 4 chế độ người dùng + giờ yên tĩnh + chỉ-khi-cắm-sạc. API §6 liệt
# ``schedule_reboot``/``cancel_schedule`` nhưng CHƯA hiện thực trước bản vá này.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RebootWindow:
    quiet_start_hour: int = 22   # 0..23, giờ bắt đầu "yên tĩnh"
    quiet_end_hour: int = 6      # 0..23, giờ kết thúc (cho phép qua nửa đêm)
    require_charging: bool = False
    metered_network_limit_mb: Optional[int] = None  # None = không giới hạn

    def to_dict(self) -> dict:
        return {
            "quiet_start_hour": self.quiet_start_hour,
            "quiet_end_hour": self.quiet_end_hour,
            "require_charging": self.require_charging,
            "metered_network_limit_mb": self.metered_network_limit_mb,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RebootWindow":
        return cls(
            quiet_start_hour=int(d["quiet_start_hour"]),
            quiet_end_hour=int(d["quiet_end_hour"]),
            require_charging=bool(d["require_charging"]),
            metered_network_limit_mb=d.get("metered_network_limit_mb"),
        )


def hour_in_quiet_window(hour: int, window: RebootWindow) -> bool:
    """True nếu ``hour`` (0..23) nằm trong cửa sổ yên tĩnh của ``window``. Cho phép
    cửa sổ vắt qua nửa đêm (vd 22 -> 6)."""
    s, e = window.quiet_start_hour, window.quiet_end_hour
    if s == e:
        return True  # cửa sổ 24h
    if s < e:
        return s <= hour < e
    return hour >= s or hour < e  # vắt qua nửa đêm


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

            # (a2) MỞ RỘNG (U19-04 "cũ" — chống rollback/freeze): từ chối metadata
            # CŨ HƠN bản đã từng xác minh cho CÙNG update_id, dù chữ ký + hash riêng
            # lẻ vẫn hợp lệ (kẻ tấn công replay một bundle ký hợp lệ nhưng đã lỗi
            # thời — khác "hết hạn" theo đồng hồ ở bước (b)). UPD-004 catalog đã ghi
            # "chống tấn công đóng băng/rollback metadata" — hiện thực ở đây.
            self._check_anti_rollback(contract.update_id, manifest)

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
        # Chỉ GHI "phiên bản đã tin" sau khi MỌI kiểm đã đạt (không ghi sớm).
        self._record_trusted_version(contract.update_id, int(manifest.get("metadata_version", 1)))
        verified = contract.transition(UpdateState.VERIFIED, signature_status="verified")
        self._commit(verified, "verify: verified")
        return verified

    # ------------------------------------------------------------------ #
    # MỞ RỘNG (U19-04) — chống rollback/freeze: nhớ metadata_version cao nhất
    # đã từng XÁC MINH ĐẠT cho mỗi update_id, bền trên đĩa (sống qua restart
    # service/khởi động lại máy — giống journal). Phạm vi: theo update_id (đơn
    # giản hoá cho prototype; theo channel/component rộng hơn là việc làm sau).
    # ------------------------------------------------------------------ #
    def _trusted_versions_path(self) -> str:
        return os.path.join(self.cache_dir, "trusted-metadata-versions.json")

    def _load_trusted_versions(self) -> dict:
        p = self._trusted_versions_path()
        if not os.path.exists(p):
            return {}
        try:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return {}

    def _record_trusted_version(self, update_id: str, version: int) -> None:
        data = self._load_trusted_versions()
        if version > data.get(update_id, 0):
            data[update_id] = version
            tmp = self._trusted_versions_path() + f".tmp-{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._trusted_versions_path())

    def _check_anti_rollback(self, update_id: str, manifest: dict) -> None:
        trusted = self._load_trusted_versions().get(update_id)
        mv = int(manifest.get("metadata_version", 1))
        if trusted is not None and mv < trusted:
            raise VerificationError(
                "UPD-004",
                f"Metadata phiên bản {mv} CŨ HƠN bản đã tin trước đó ({trusted}) — "
                f"chặn tấn công hạ cấp/replay (rollback/freeze)",
            )

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
    # MỞ RỘNG (U19-01) — API §6 'get_release_notes'. Đọc + XÁC MINH CHỮ KÝ
    # metadata TRƯỚC KHI trả nội dung hiển thị (version/changelog/size) — nếu
    # không, một mirror độc hại có thể hiển thị mô tả giả để dụ cài tay dù bản
    # cài thật sẽ bị verify() chặn sau. Nội dung trả về LUÔN từ manifest đã ký,
    # KHÔNG phải do UI/SmartAI tự bịa.
    # ------------------------------------------------------------------ #
    def get_release_notes(self, update_id: str) -> dict:
        manifest, sig = self._read_manifest(update_id)
        self._verify_signature(manifest, sig, "manifest(get_release_notes)")
        payload = manifest.get("payload", {})
        return {
            "update_id": update_id,
            "component": manifest.get("component", "os"),
            "channel": manifest.get("channel"),
            "version": manifest.get("target_build"),
            "metadata_version": manifest.get("metadata_version"),
            "architecture": manifest.get("architecture"),
            "size_bytes": payload.get("size"),
            "release_notes_vi": manifest.get(
                "release_notes_vi", "(Bản TEST không kèm changelog thật.)"
            ),
        }

    # ------------------------------------------------------------------ #
    # 5) STAGE — verified -> staged (staged-install mô phỏng, chưa đụng hệ đang chạy)
    # ------------------------------------------------------------------ #
    def stage(self, contract: UpdateContract, *, firmware_user_confirmed: bool = False) -> UpdateContract:
        if contract.state != UpdateState.VERIFIED:
            # Không có đường stage từ 'blocked' — transition sẽ ném; chặn tường minh cho rõ.
            raise RuntimeError(
                f"stage chỉ từ 'verified'. Trạng thái {contract.state.value} "
                f"không được cài (không bypass)."
            )
        # MỞ RỘNG (U19-12, PL15 §3/§4/UPDATE-CENTER-UI.md §1): firmware KHÔNG BAO
        # GIỜ tự cài — KHÔNG chế độ người dùng nào (notify/auto_download_ask_install/
        # auto_install_safe/auto_scheduled) được phép bỏ qua xác nhận rõ. Thiếu cờ
        # xác nhận ⇒ từ chối tại API, bất kể caller là UI/daemon lập lịch/SmartAI.
        if contract.component == "firmware" and not firmware_user_confirmed:
            raise RuntimeError(
                f"stage(firmware) bị TỪ CHỐI cho {contract.update_id}: firmware luôn cần "
                f"xác nhận rõ (firmware_user_confirmed=True) + preflight pin/nguồn/model đạt "
                f"— không chế độ cập nhật nào được tự cài firmware."
            )
        staged = contract.transition(UpdateState.STAGED)
        self.log(f"stage: {contract.update_id} đã chuẩn bị (staged) — chưa đổi hệ đang chạy")
        self._commit(staged, "stage: staged")
        return staged

    def arm_reboot(
        self, contract: UpdateContract, *, unsaved_documents: Optional[List[str]] = None
    ) -> UpdateContract:
        """MỞ RỘNG (U19-06, UPD-007 — không blocking nhưng HOÃN reboot): nếu còn
        tài liệu NaMiOffice/NaMiPDF chưa lưu, KHÔNG chuyển 'reboot_pending' (không
        tạo bất ngờ khởi động lại) — giữ nguyên state hiện tại ('staged') để UI mời
        chọn giờ khác. Gọi lại KHÔNG có ``unsaved_documents`` khi đã lưu xong để
        tiếp tục."""
        if unsaved_documents:
            self.log(
                f"arm_reboot: HOÃN {contract.update_id} — tài liệu chưa lưu: "
                f"{', '.join(unsaved_documents)} (UPD-007, không reboot bất ngờ)"
            )
            return contract
        nxt = contract.transition(UpdateState.REBOOT_PENDING)
        self._commit(nxt, "reboot_pending")
        return nxt

    # ------------------------------------------------------------------ #
    # MỞ RỘNG (U19-02) — API §6 'schedule_reboot'/'cancel_schedule'. Lưu Ý ĐỊNH
    # lịch (giờ yên tĩnh/chỉ-khi-cắm-sạc/giới hạn mạng tính phí) BỀN trên đĩa
    # (file JSON ghi nguyên tử trong cache_dir) — sống qua restart service/khởi
    # động lại máy (mô phỏng bằng dựng UpdateService MỚI cùng cache_dir). KHÔNG
    # tự thực thi reboot; chỉ lưu lịch cho bộ điều phối (hoặc test) đọc lại qua
    # :meth:`reboot_allowed_now`.
    # ------------------------------------------------------------------ #
    def _schedule_path(self, update_id: str) -> str:
        return os.path.join(self.cache_dir, f"{update_id}.reboot-schedule.json")

    def schedule_reboot(self, contract: UpdateContract, window: RebootWindow) -> dict:
        if contract.state not in (UpdateState.STAGED, UpdateState.REBOOT_PENDING):
            raise RuntimeError(
                f"schedule_reboot chỉ hợp lệ khi đã staged/reboot_pending, "
                f"nhận {contract.state.value}"
            )
        data = {
            "update_id": contract.update_id,
            "correlation_id": contract.correlation_id,
            "window": window.to_dict(),
        }
        path = self._schedule_path(contract.update_id)
        tmp = path + f".tmp-{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        self.log(f"schedule_reboot: {contract.update_id} -> giờ yên tĩnh "
                 f"{window.quiet_start_hour}h-{window.quiet_end_hour}h "
                 f"(cắm sạc bắt buộc={window.require_charging})")
        return data

    def get_schedule(self, update_id: str) -> Optional[dict]:
        path = self._schedule_path(update_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def cancel_schedule(self, update_id: str) -> bool:
        path = self._schedule_path(update_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        self.log(f"cancel_schedule: {update_id} — đã bỏ lịch khởi động lại")
        return True

    def reboot_allowed_now(
        self, update_id: str, *, now_hour: int, on_charger: bool = True
    ) -> Tuple[bool, str]:
        """Có được khởi động lại NGAY theo lịch đã lưu không? KHÔNG tự reboot —
        chỉ trả quyết định cho bộ điều phối. Không có lịch ⇒ (False, lý do)."""
        sched = self.get_schedule(update_id)
        if sched is None:
            return False, "Chưa có lịch khởi động lại cho bản này."
        window = RebootWindow.from_dict(sched["window"])
        if window.require_charging and not on_charger:
            return False, "Cần cắm sạc trước khi khởi động lại theo lịch."
        if not hour_in_quiet_window(now_hour, window):
            return False, (
                f"Ngoài giờ yên tĩnh đã chọn ({window.quiet_start_hour}h-"
                f"{window.quiet_end_hour}h) — hoãn tới cửa sổ kế tiếp."
            )
        return True, "Trong cửa sổ đã chọn và đủ điều kiện — được khởi động lại."

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
