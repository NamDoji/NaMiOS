#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS Update Center — bộ dựng REPO TEST đã ký (Phụ lục 15 §9, U15-B).

==============================  TEST-ONLY  ==================================
Script này SINH MỘT CẶP KHOÁ ed25519 MỚI mỗi lần chạy và dùng nó để ký
metadata + payload giả, dựng một repo cục bộ để kiểm thử offline.

TUYỆT ĐỐI KHÔNG dùng khoá sản phẩm ở đây. Khoá sinh ra là khoá dùng một lần
cho test, lưu trong thư mục repo test với nhãn TEST-ONLY. Trong sản phẩm,
khoá root/targets phải offline/HSM với quorum (PL15 §4) — ngoài phạm vi prototype.
============================================================================

Dựng gì:
  <repo>/root.json            -> trust root (public key + key_id)   [client pin khoá này]
  <repo>/TEST-ONLY-private.pem-> khoá riêng TEST (chỉ để tái ký biến thể trong test)
  <repo>/revocation.json(.sig)-> danh sách thu hồi đã ký
  <repo>/metadata/<id>.manifest.json + <id>.manifest.sig
  <repo>/targets/<id>.payload

Hàm tái dùng cho test (dựng ca phản công hợp-lệ/sai-chữ-ký/hết-hạn/sai-arch/thu-hồi):
  generate_keypair(), sign_bytes(), canonical_bytes(), build_update(),
  write_revocation(), build_test_repo().
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

MANIFEST_SCHEMA = "namios.update-manifest/v1"
ROOT_SCHEMA = "namios.trust-root/v1"
REVOCATION_SCHEMA = "namios.revocation/v1"
TEST_ONLY_BANNER = "TEST-ONLY — khoá sinh ngẫu nhiên, KHÔNG phải khoá sản phẩm NaMiOS."


# --------------------------------------------------------------------------- #
# Khoá + ký
# --------------------------------------------------------------------------- #
def generate_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def public_key_pem(pub: Ed25519PublicKey) -> str:
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def private_key_pem(priv: Ed25519PrivateKey) -> str:
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),  # TEST-ONLY
    ).decode("ascii")


def key_id(pub: Ed25519PublicKey) -> str:
    """Định danh khoá = sha256 của public key dạng raw (16 byte đầu, hex)."""
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()[:32]


def canonical_bytes(obj: dict) -> bytes:
    """Chuỗi hoá chính tắc để ký: JSON sort_keys, không khoảng trắng thừa, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_bytes(priv: Ed25519PrivateKey, data: bytes) -> str:
    return priv.sign(data).hex()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


# --------------------------------------------------------------------------- #
# Dựng repo
# --------------------------------------------------------------------------- #
def _iso(dt: _dt.datetime) -> str:
    return dt.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def write_trust_root(repo: str, pub: Ed25519PublicKey) -> dict:
    root = {
        "schema": ROOT_SCHEMA,
        "role": "targets",
        "key_id": key_id(pub),
        "public_key_pem": public_key_pem(pub),
        "note": TEST_ONLY_BANNER,
    }
    with open(os.path.join(repo, "root.json"), "w", encoding="utf-8") as fh:
        json.dump(root, fh, ensure_ascii=False, indent=2)
    return root


def build_update(
    repo: str,
    priv: Ed25519PrivateKey,
    pub: Ed25519PublicKey,
    *,
    update_id: str,
    payload: bytes,
    component: str = "os",
    channel: str = "stable",
    architecture: str = "x86_64",
    target_build: str = "namios-1.1-x86_64-stable",
    metadata_version: int = 2,
    model_whitelist: Optional[List[str]] = None,
    expires: Optional[_dt.datetime] = None,
    sign_with: Optional[Ed25519PrivateKey] = None,
    override_payload_hash: Optional[str] = None,
    tamper_payload_after_sign: Optional[bytes] = None,
) -> dict:
    """Ký + ghi một bản cập nhật vào repo. Các tham số tấn công cho test:

    * ``sign_with``   : ký bằng khoá KHÁC (giả chữ ký) → chữ ký không khớp trust root.
    * ``override_payload_hash`` : ghi hash sai vào manifest (ít dùng; thường dùng tamper).
    * ``tamper_payload_after_sign`` : ghi đè payload SAU khi ký (payload ≠ hash đã ký).
    * ``expires`` quá khứ : metadata hết hạn.
    * ``architecture`` lệch máy / ``model_whitelist`` loại máy : sai arch/model.
    """
    os.makedirs(os.path.join(repo, "metadata"), exist_ok=True)
    os.makedirs(os.path.join(repo, "targets"), exist_ok=True)

    payload_rel = f"targets/{update_id}.payload"
    payload_abs = os.path.join(repo, payload_rel)
    with open(payload_abs, "wb") as fh:
        fh.write(payload)

    payload_hash = override_payload_hash or sha256_file(payload_abs)
    if expires is None:
        expires = _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(days=30)

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "update_id": update_id,
        "component": component,
        "channel": channel,
        "architecture": architecture,
        "target_build": target_build,
        "metadata_version": metadata_version,
        "model_whitelist": model_whitelist if model_whitelist is not None else ["*"],
        "payload": {
            "path": payload_rel,
            "size": len(payload),
            "hash": payload_hash,
        },
        "expires": _iso(expires),
        "key_id": key_id(pub),
        "note": TEST_ONLY_BANNER,
    }
    signer = sign_with or priv
    sig_hex = sign_bytes(signer, canonical_bytes(manifest))

    with open(os.path.join(repo, "metadata", f"{update_id}.manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(repo, "metadata", f"{update_id}.manifest.sig"), "w",
              encoding="utf-8") as fh:
        json.dump({"alg": "ed25519", "sig": sig_hex}, fh, ensure_ascii=False, indent=2)

    # Giả lập payload bị sửa sau khi ký (mirror độc hại / man-in-the-middle).
    if tamper_payload_after_sign is not None:
        with open(payload_abs, "wb") as fh:
            fh.write(tamper_payload_after_sign)

    return manifest


def write_revocation(
    repo: str,
    priv: Ed25519PrivateKey,
    pub: Ed25519PublicKey,
    *,
    revoked_update_ids: Optional[List[str]] = None,
    revoked_key_ids: Optional[List[str]] = None,
    metadata_version: int = 1,
    expires: Optional[_dt.datetime] = None,
) -> dict:
    if expires is None:
        expires = _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(days=30)
    rev = {
        "schema": REVOCATION_SCHEMA,
        "metadata_version": metadata_version,
        "revoked_update_ids": sorted(revoked_update_ids or []),
        "revoked_key_ids": sorted(revoked_key_ids or []),
        "expires": _iso(expires),
        "key_id": key_id(pub),
    }
    sig_hex = sign_bytes(priv, canonical_bytes(rev))
    with open(os.path.join(repo, "revocation.json"), "w", encoding="utf-8") as fh:
        json.dump(rev, fh, ensure_ascii=False, indent=2)
    with open(os.path.join(repo, "revocation.sig"), "w", encoding="utf-8") as fh:
        json.dump({"alg": "ed25519", "sig": sig_hex}, fh, ensure_ascii=False, indent=2)
    return rev


def build_test_repo(
    repo: str,
    *,
    payload: bytes = b"NaMiOS 1.1 fake OS deployment payload (TEST-ONLY)\n" * 64,
) -> Dict[str, object]:
    """Dựng repo TEST tối thiểu: 1 trust root + 1 bản cập nhật HỢP LỆ + revocation rỗng.
    Trả về dict tiện cho test (đường dẫn, khoá, update_id...)."""
    os.makedirs(repo, exist_ok=True)
    priv, pub = generate_keypair()

    # Lưu khoá riêng TEST (để các ca test tái ký biến thể hợp-lệ-nhưng-nội-dung-xấu).
    with open(os.path.join(repo, "TEST-ONLY-private.pem"), "w", encoding="utf-8") as fh:
        fh.write("# " + TEST_ONLY_BANNER + "\n")
        fh.write(private_key_pem(priv))
    os.chmod(os.path.join(repo, "TEST-ONLY-private.pem"), 0o600)

    root = write_trust_root(repo, pub)
    update_id = "namios-os-1.1-stable-0001"
    manifest = build_update(
        repo, priv, pub,
        update_id=update_id,
        payload=payload,
        component="os",
        channel="stable",
        architecture="x86_64",
        target_build="namios-1.1-x86_64-stable",
        metadata_version=2,
    )
    write_revocation(repo, priv, pub, revoked_update_ids=[], metadata_version=1)

    return {
        "repo": repo,
        "root_path": os.path.join(repo, "root.json"),
        "private_pem": os.path.join(repo, "TEST-ONLY-private.pem"),
        "update_id": update_id,
        "key_id": root["key_id"],
        "manifest": manifest,
        "priv": priv,
        "pub": pub,
    }


def load_private_key(pem_path: str) -> Ed25519PrivateKey:
    with open(pem_path, "rb") as fh:
        data = fh.read()
    # Bỏ dòng comment đầu nếu có.
    if data.lstrip().startswith(b"#"):
        data = b"\n".join(line for line in data.splitlines() if not line.lstrip().startswith(b"#"))
    return serialization.load_pem_private_key(data, password=None)


def _main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Dựng repo cập nhật TEST đã ký (TEST-ONLY).")
    ap.add_argument("out_dir", help="thư mục repo test sẽ dựng")
    args = ap.parse_args()

    info = build_test_repo(args.out_dir)
    print("==================================================================")
    print("  " + TEST_ONLY_BANNER)
    print("==================================================================")
    print(f"repo        : {info['repo']}")
    print(f"trust root  : {info['root_path']}")
    print(f"key_id      : {info['key_id']}")
    print(f"update_id   : {info['update_id']}")
    print(f"payload     : targets/{info['update_id']}.payload")
    print("Khoá riêng TEST lưu ở TEST-ONLY-private.pem (0600) — chỉ để test tái ký.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
