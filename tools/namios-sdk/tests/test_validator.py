# -*- coding: utf-8 -*-
"""Test lớp 3 tầng của validator.py (ADR-0022): schema / policy / signature.

Ba ca bắt buộc theo đề bài M4:
  * manifest hợp lệ (đã ký đúng khoá, quyền trong tầm cho phép) -> accepted.
  * manifest quá quyền (schema đúng, ký đúng, nhưng vượt quyền cho
    certification_level) -> REJECTED bởi lớp chính sách.
  * manifest chưa ký -> REJECTED bởi lớp chữ ký.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

import manifest_signing
import validator


# --------------------------------------------------------------------------- #
# Lớp 1 — schema
# --------------------------------------------------------------------------- #
def test_schema_itself_is_a_valid_draft_2020_12_schema():
    schema = validator.load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)  # raise nếu schema sai


@pytest.mark.parametrize(
    "example_file",
    ["word-count-vi.manifest.json", "pdf-export.manifest.json"],
)
def test_example_manifests_validate_against_schema(example_file):
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    with (examples_dir / example_file).open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    errors = validator.check_schema(manifest)
    assert errors == [], f"{example_file} phải hợp lệ về schema, lỗi: {errors}"


def test_schema_rejects_filesystem_home_scope(base_manifest):
    manifest = dict(base_manifest)
    manifest["permission_scopes"] = ["filesystem:home"]
    errors = validator.check_schema(manifest)
    assert errors, "filesystem:home không nằm trong allow-list — schema PHẢI từ chối"


def test_schema_rejects_office_js_entrypoint(base_manifest):
    manifest = json.loads(json.dumps(base_manifest))  # deep copy an toàn
    manifest["automation"]["entrypoint_type"] = "office_js"
    errors = validator.check_schema(manifest)
    assert errors, "entrypoint_type ngoài {python_uno,nami_script_api,none} phải bị schema chặn"


# --------------------------------------------------------------------------- #
# Ba ca chính: happy path / quá quyền / chưa ký
# --------------------------------------------------------------------------- #
def test_valid_signed_manifest_is_accepted(valid_signed_manifest, trust_store):
    result = validator.validate_extension(valid_signed_manifest, trust_store=trust_store)
    assert result.schema_errors == []
    assert result.policy_errors == []
    assert result.signature_errors == []
    assert result.accepted is True


def test_over_permissioned_manifest_is_rejected_by_policy_layer(
    over_permissioned_manifest, trust_store
):
    result = validator.validate_extension(over_permissioned_manifest, trust_store=trust_store)
    # Phải pass schema (giá trị quyền nằm trong allow-list) và chữ ký (ký đúng) —
    # lý do từ chối CHỈ nằm ở lớp chính sách.
    assert result.schema_errors == [], "manifest này hợp lệ về schema, không phải lý do từ chối"
    assert result.signature_errors == [], "manifest này đã ký đúng, không phải lý do từ chối"
    assert result.policy_errors != [], "print:document ở mức 'declared' phải bị chính sách từ chối"
    assert result.accepted is False


def test_unsigned_manifest_is_rejected_by_signature_layer(unsigned_manifest, trust_store):
    result = validator.validate_extension(unsigned_manifest, trust_store=trust_store)
    assert result.schema_errors == [], "manifest này hợp lệ về schema, không phải lý do từ chối"
    assert result.policy_errors == [], "quyền nằm trong tầm cho phép, không phải lý do từ chối"
    assert result.signature_errors != [], "chưa ký phải bị lớp chữ ký từ chối (fail-closed)"
    assert result.accepted is False


# --------------------------------------------------------------------------- #
# Lớp chữ ký — các ca đối kháng khác
# --------------------------------------------------------------------------- #
def test_signature_rejected_when_key_not_in_trust_store(valid_signed_manifest):
    result = validator.validate_extension(valid_signed_manifest, trust_store={})
    assert result.accepted is False
    assert result.signature_errors != []


def test_signature_rejected_when_manifest_tampered_after_signing(
    valid_signed_manifest, trust_store
):
    tampered = dict(valid_signed_manifest)
    tampered["version"] = "9.9.9-evil"  # đổi nội dung sau khi đã ký
    result = validator.validate_extension(tampered, trust_store=trust_store)
    assert result.accepted is False
    assert result.signature_errors != []


def test_signature_half_signed_inconsistent_rejected_by_schema(base_manifest):
    """signed=true nhưng để trống key_id/signature_hex — 'ký nửa vời' phải bị
    SCHEMA chặn trước khi tới lớp chữ ký (if/then trong extension-manifest.schema.json).
    """
    manifest = json.loads(json.dumps(base_manifest))
    manifest["signature"] = {
        "signed": True,
        "algorithm": "ed25519",
        "key_id": None,
        "signature_hex": None,
        "signer": None,
    }
    errors = validator.check_schema(manifest)
    assert errors, "signed=true với key_id/signature_hex null phải bị schema từ chối"


# --------------------------------------------------------------------------- #
# Lớp chính sách — thang certification_level + revoke
# --------------------------------------------------------------------------- #
def test_revoked_certification_level_always_rejected(base_manifest):
    manifest = json.loads(json.dumps(base_manifest))
    manifest["certification_level"] = "revoked"
    manifest["revoked"] = True
    manifest["permission_scopes"] = ["office:document-only"]  # ngay cả quyền tối thiểu
    errors = validator.check_policy(manifest)
    assert errors != [], "certification_level=revoked PHẢI luôn bị chính sách từ chối"


def test_network_allowlist_scope_without_domains_rejected_by_policy(base_manifest):
    manifest = json.loads(json.dumps(base_manifest))
    manifest["certification_level"] = "published"
    manifest["permission_scopes"] = ["office:document-only", "network:allowlist-declared"]
    manifest["network_allowlist"] = []
    errors = validator.check_policy(manifest)
    assert any("network_allowlist" in e for e in errors)


def test_downloaded_with_document_source_restricted_by_policy(base_manifest):
    manifest = json.loads(json.dumps(base_manifest))
    manifest["certification_level"] = "published"
    manifest["source_trust"] = "downloaded_with_document"
    manifest["permission_scopes"] = ["office:document-only", "print:document"]
    errors = validator.check_policy(manifest)
    assert any("downloaded_with_document" in e for e in errors)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_cli_main_exit_code_accept_and_reject(tmp_path, valid_signed_manifest, unsigned_manifest, trust_store):
    from cryptography.hazmat.primitives import serialization

    trust_store_path = tmp_path / "trust_store.json"
    pem_map = {
        kid: pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        for kid, pub in trust_store.items()
    }
    trust_store_path.write_text(json.dumps(pem_map), encoding="utf-8")

    good_path = tmp_path / "good.manifest.json"
    good_path.write_text(json.dumps(valid_signed_manifest), encoding="utf-8")

    bad_path = tmp_path / "bad.manifest.json"
    bad_path.write_text(json.dumps(unsigned_manifest), encoding="utf-8")

    rc_good = validator.main([str(good_path), "--trust-store", str(trust_store_path)])
    rc_bad = validator.main([str(bad_path), "--trust-store", str(trust_store_path)])

    assert rc_good == 0
    assert rc_bad == 1
