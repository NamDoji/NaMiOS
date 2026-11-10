# -*- coding: utf-8 -*-
"""Cho pytest thấy module tools/namios-sdk (thư mục cha) khi chạy từ bất kỳ đâu
— cùng khuôn với tools/update-center-prototype/tests/conftest.py.

Cũng khai các fixture dùng chung cho test_validator.py: cặp khoá ed25519
TEST-ONLY, trust store tương ứng, và 3 biến thể manifest (hợp lệ-đã-ký /
quá-quyền / chưa-ký) dựng từ manifest mẫu `examples/word-count-vi.manifest.json`.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

_SDK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SDK_DIR not in sys.path:
    sys.path.insert(0, _SDK_DIR)

import manifest_signing  # noqa: E402  (sys.path chỉnh ở trên, trước import)

_EXAMPLES_DIR = Path(_SDK_DIR) / "examples"


def _load_base_manifest() -> dict:
    with (_EXAMPLES_DIR / "word-count-vi.manifest.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture()
def base_manifest() -> dict:
    """Bản sao sạch của manifest mẫu word-count-vi (chưa ký, certification=declared)."""
    return _load_base_manifest()


@pytest.fixture()
def test_keypair():
    """TEST-ONLY: một cặp khoá ed25519 sinh mới cho phiên test này."""
    priv, pub = manifest_signing.generate_keypair()
    return priv, pub


@pytest.fixture()
def trust_store(test_keypair):
    """Trust store chỉ chứa khoá publisher hợp lệ của test này."""
    _priv, pub = test_keypair
    return {manifest_signing.key_id(pub): pub}


@pytest.fixture()
def valid_signed_manifest(base_manifest, test_keypair) -> dict:
    """Happy path: quyền tối thiểu + certification_level khớp + ký hợp lệ bằng
    khoá có trong `trust_store`. Phải được `validate_extension()` CHẤP NHẬN.
    """
    priv, _pub = test_keypair
    manifest = copy.deepcopy(base_manifest)
    manifest["certification_level"] = "declared"
    manifest["permission_scopes"] = ["office:document-only"]
    signed = manifest_signing.sign_manifest(priv, manifest, signer="NaMiOS SDK Test Publisher")
    return signed


@pytest.fixture()
def over_permissioned_manifest(base_manifest, test_keypair) -> dict:
    """Hợp lệ về SCHEMA + KÝ ĐÚNG, nhưng xin quyền 'print:document' trong khi
    certification_level vẫn là 'declared' (chỉ được tập quyền tối thiểu) —
    phải bị lớp CHÍNH SÁCH từ chối, không phải vì schema hay chữ ký.
    """
    priv, _pub = test_keypair
    manifest = copy.deepcopy(base_manifest)
    manifest["certification_level"] = "declared"
    manifest["permission_scopes"] = ["office:document-only", "print:document"]
    manifest["rollback"] = {
        "supported": False,
        "mechanism": "In tài liệu không đảo ngược được; không có cơ chế hoàn tác.",
    }
    signed = manifest_signing.sign_manifest(priv, manifest, signer="NaMiOS SDK Test Publisher")
    return signed


@pytest.fixture()
def unsigned_manifest(base_manifest) -> dict:
    """Hợp lệ về SCHEMA + quyền trong tầm cho phép, nhưng `signature.signed`
    vẫn là false (như manifest mẫu gốc) — phải bị lớp CHỮ KÝ từ chối.
    """
    manifest = copy.deepcopy(base_manifest)
    manifest["certification_level"] = "declared"
    manifest["permission_scopes"] = ["office:document-only"]
    # signature đã là {"signed": false, ...} trong manifest mẫu — giữ nguyên.
    return manifest
