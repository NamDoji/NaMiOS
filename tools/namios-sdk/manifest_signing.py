#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS Extension SDK — ký/kiểm chữ ký manifest (ADR-0022).

Mô hình giống `tools/update-center-prototype/sign_test_repo.py` (ed25519,
canonical JSON bytes): mỗi NHÀ XUẤT BẢN có một cặp khoá ed25519; public key
được NaMiOS ghim vào một "trust store" (ở đây chỉ là file JSON cục bộ —
sản phẩm thật dùng kho khoá/HSM có quy trình review, ngoài phạm vi prototype
này). `validator.py` chỉ chấp nhận chữ ký hợp lệ VÀ key_id có trong trust
store đó; ký đúng nhưng khoá lạ vẫn bị từ chối (fail-closed).

==============================  TEST-ONLY  ==================================
`generate_keypair()` sinh khoá MỚI mỗi lần gọi, chỉ dùng để viết fixture/test
cho validator. TUYỆT ĐỐI không dùng khoá sinh ở đây làm khoá ký sản phẩm.
============================================================================
"""
from __future__ import annotations

import hashlib
import json
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

TEST_ONLY_BANNER = "TEST-ONLY — khoá sinh ngẫu nhiên cho test/fixture, KHÔNG phải khoá sản phẩm NaMiOS."

#: Trường PHẢI loại khỏi manifest trước khi tính canonical bytes để ký/kiểm —
#: tránh vòng lặp "ký cả chữ ký của chính nó".
_SIGNATURE_FIELD = "signature"


def generate_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """TEST-ONLY: sinh cặp khoá ed25519 mới. Không dùng cho sản phẩm."""
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def key_id(pub: Ed25519PublicKey) -> str:
    """Định danh khoá = sha256(public key raw bytes), rút gọn 32 hex đầu.

    Khớp quy ước `sign_test_repo.py::key_id` để hai hệ (Update Center, Extension
    SDK) dùng cùng cách sinh id khoá nếu sau này hợp nhất trust store.
    """
    raw = pub.public_bytes_raw()
    return hashlib.sha256(raw).hexdigest()[:32]


def canonical_manifest_bytes(manifest: dict) -> bytes:
    """Chuỗi hoá chính tắc để ký/kiểm: loại trường `signature`, JSON sort_keys,
    không khoảng trắng thừa, UTF-8 — khớp `sign_test_repo.py::canonical_bytes`.
    """
    stripped = {k: v for k, v in manifest.items() if k != _SIGNATURE_FIELD}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_manifest(priv: Ed25519PrivateKey, manifest: dict, signer: str) -> dict:
    """Trả về MỘT BẢN SAO của manifest với trường `signature` đã điền.

    Không chỉnh sửa `manifest` gốc (tránh side-effect bất ngờ trong test).
    """
    pub = priv.public_key()
    data = canonical_manifest_bytes(manifest)
    sig_hex = priv.sign(data).hex()
    out = dict(manifest)
    out[_SIGNATURE_FIELD] = {
        "signed": True,
        "algorithm": "ed25519",
        "key_id": key_id(pub),
        "signature_hex": sig_hex,
        "signer": signer,
    }
    return out


def verify_manifest_signature(manifest: dict, trusted_keys: dict) -> Tuple[bool, str]:
    """Kiểm chữ ký `manifest["signature"]` với `trusted_keys` = {key_id: Ed25519PublicKey}.

    Trả `(True, "")` khi hợp lệ; `(False, lý_do_tiếng_việt)` khi không — KHÔNG
    `raise` để lớp gọi (validator.py) luôn có thông báo rõ ràng, nhất quán với
    quy tắc "không raise, trả kết quả có lý do" của SmartAI Tool Broker.
    """
    sig = manifest.get(_SIGNATURE_FIELD) or {}
    if not sig.get("signed"):
        return False, "manifest chưa ký (signature.signed=false) — fail-closed, không cài/chạy"

    kid = sig.get("key_id")
    sig_hex = sig.get("signature_hex")
    algorithm = sig.get("algorithm")

    if algorithm != "ed25519":
        return False, f"thuật toán ký không được hỗ trợ: {algorithm!r}"
    if not kid or kid not in trusted_keys:
        return False, f"key_id {kid!r} không có trong trust store (khoá lạ/chưa ghim)"
    if not sig_hex:
        return False, "thiếu signature_hex"

    pub = trusted_keys[kid]
    data = canonical_manifest_bytes(manifest)
    try:
        sig_bytes = bytes.fromhex(sig_hex)
    except ValueError:
        return False, "signature_hex không phải hex hợp lệ"

    try:
        pub.verify(sig_bytes, data)
    except Exception:
        return False, "chữ ký KHÔNG khớp nội dung manifest (bị sửa sau khi ký hoặc chữ ký sai)"

    return True, ""
