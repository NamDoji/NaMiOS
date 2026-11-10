#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NaMiOS Extension & Automation SDK — reference validator (ADR-0022, M4).

Validation 2 TẦNG (khớp quy tắc CLAUDE.md "Validation 2 tầng" + triết lý
`capability-registry.schema.json`: "Schema hợp lệ KHÔNG cấp quyền"):

  1. **Cấu trúc** — `extension-manifest.schema.json` (JSON Schema draft
     2020-12). `permission_scopes` là ALLOW-LIST đóng; giá trị ngoài allow-list
     (ví dụ 'filesystem:home', 'network:any') bị schema tự chặn.
  2. **Chính sách (semantic)** — hàm `check_policy()` dưới đây: đối chiếu tổ
     hợp quyền với `certification_level` (manifest hợp lệ-về-schema vẫn có
     thể BỊ TỪ CHỐI vì xin nhiều quyền hơn mức đã được review cho phép —
     "over-permissioned"), kiểm nhất quán revoke, và — lớp fail-closed cuối —
     `check_signature()` kiểm chữ ký ed25519 so với trust store ghim trước.

Một manifest chỉ được coi là AN TOÀN ĐỂ CÀI khi CẢ BA lớp pass. Không có lớp
nào tự đủ: xem ADR-0022 §"Vì sao 3 lớp".

CLI:
    python3 validator.py <manifest.json> [--trust-store trust_store.json]

Thoát 0 khi accepted=True, thoát 1 khi False — để script/CI dùng trực tiếp.
Trạng thái triển khai: `specified` + reference validator CHẠY ĐƯỢC, có pytest
(`tests/test_validator.py`). CHƯA nối vào trình cài extension NaMiOffice thật
(cần app LibreOffice/UNO thật — xem ADR-0022 §Phạm vi trung thực).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from jsonschema import Draft202012Validator

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:  # pragma: no cover — cryptography is a declared dependency
    Ed25519PublicKey = None  # type: ignore[assignment,misc]

import manifest_signing

_HERE = Path(__file__).resolve().parent
SCHEMA_PATH = _HERE / "extension-manifest.schema.json"

#: Scope coi là "tối thiểu, an toàn cho mọi mức review" — không cần review gì
#: thêm ngoài việc tự khai (certification_level == 'declared').
MINIMAL_SCOPES = frozenset(
    {
        "office:document-only",
        "office:selection-only",
        "filesystem:none",
        "network:none",
        "automation:dry-run-only",
    }
)

#: Quyền cho phép theo TỪNG mức certification_level — thang leo dần đúng vòng
#: đời `declared -> sandbox_tested -> pilot_verified -> published`
#: (khớp capability-registry.schema.json PL16 §7). Một mức BAO GỒM mọi quyền
#: của các mức thấp hơn (set union được tính trong `_allowed_scopes_for()`).
_SCOPE_LADDER: Dict[str, frozenset] = {
    "declared": MINIMAL_SCOPES,
    "sandbox_tested": MINIMAL_SCOPES
    | {"clipboard:read-document", "office:document-and-linked-resources"},
    "pilot_verified": MINIMAL_SCOPES
    | {
        "clipboard:read-document",
        "office:document-and-linked-resources",
        "clipboard:write-document",
        "filesystem:user-chosen-export-target",
    },
    "published": MINIMAL_SCOPES
    | {
        "clipboard:read-document",
        "office:document-and-linked-resources",
        "clipboard:write-document",
        "filesystem:user-chosen-export-target",
        "print:document",
        "network:allowlist-declared",
    },
}
#: Hai mức cuối không còn hiệu lực chạy (dù trước đó ở ladder nào).
_INERT_LEVELS = frozenset({"stale", "revoked"})


def _allowed_scopes_for(certification_level: str) -> frozenset:
    return _SCOPE_LADDER.get(certification_level, frozenset())


@dataclass
class ValidationResult:
    manifest_id: Optional[str]
    accepted: bool
    schema_errors: List[str] = field(default_factory=list)
    policy_errors: List[str] = field(default_factory=list)
    signature_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "manifest_id": self.manifest_id,
            "accepted": self.accepted,
            "schema_errors": self.schema_errors,
            "policy_errors": self.policy_errors,
            "signature_errors": self.signature_errors,
        }


def load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def check_schema(manifest: dict, schema: Optional[dict] = None) -> List[str]:
    """Lớp 1: cấu trúc. Trả danh sách lỗi (rỗng = hợp lệ về schema)."""
    schema = schema if schema is not None else load_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
    return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def check_policy(manifest: dict) -> List[str]:
    """Lớp 2: chính sách — cấu trúc đúng vẫn có thể bị từ chối vì quá quyền.

    KHÔNG giả định manifest đã qua check_schema(); các truy cập .get() có mặc
    định an toàn để không crash trên input thiếu trường (fail-closed: thiếu
    thông tin -> coi là vi phạm chính sách, không coi là "chưa rõ nên cho qua").
    """
    errors: List[str] = []

    cert = manifest.get("certification_level")
    if cert in _INERT_LEVELS:
        errors.append(
            f"certification_level={cert!r} không còn hiệu lực chạy (stale/revoked)"
        )

    allowed = _allowed_scopes_for(cert) if cert not in _INERT_LEVELS else frozenset()
    requested = set(manifest.get("permission_scopes") or [])
    over_broad = requested - allowed
    if over_broad:
        errors.append(
            "permission_scopes vượt mức được phép cho certification_level="
            f"{cert!r}: {sorted(over_broad)} (cần review lên mức cao hơn trước)"
        )

    # network:allowlist-declared PHẢI đi kèm danh sách domain cụ thể, không rỗng.
    if "network:allowlist-declared" in requested:
        allowlist = manifest.get("network_allowlist") or []
        if not allowlist:
            errors.append("network:allowlist-declared nhưng network_allowlist rỗng/thiếu")

    # revoked=true PHẢI chặn tuyệt đối, bất kể certification_level ghi gì khác.
    if manifest.get("revoked") is True and cert != "revoked":
        errors.append(
            f"revoked=true nhưng certification_level={cert!r} (phải là 'revoked') — "
            "dữ liệu không nhất quán, từ chối fail-closed"
        )

    # Nguồn 'downloaded_with_document' đã bị schema ép hẹp permission_scopes;
    # validator vẫn kiểm lại ở lớp chính sách (phòng schema bị bỏ qua/khác bản).
    if manifest.get("source_trust") == "downloaded_with_document":
        safe_subset = {
            "office:document-only",
            "office:selection-only",
            "filesystem:none",
            "network:none",
            "clipboard:read-document",
            "automation:dry-run-only",
        }
        extra = requested - safe_subset
        if extra:
            errors.append(
                "source_trust=downloaded_with_document nhưng permission_scopes "
                f"vượt tập tối thiểu cho file tải về: {sorted(extra)}"
            )

    # Automation hard rules (ADR-0022): entrypoint_type đóng, macro không tự chạy.
    automation = manifest.get("automation") or {}
    if automation.get("entrypoint_type") not in {"python_uno", "nami_script_api", "none"}:
        errors.append(
            "automation.entrypoint_type phải là python_uno/nami_script_api/none — "
            "Office.js/VBA/COM/ActiveX KHÔNG được hỗ trợ bởi SDK này"
        )
    if automation.get("macro_autorun") is not False:
        errors.append("automation.macro_autorun phải là false (macro không tự chạy)")

    compat = manifest.get("compat_disclaimer") or {}
    for field_name in ("vba_supported", "com_activex_supported", "office_js_supported"):
        if compat.get(field_name) is not False:
            errors.append(f"compat_disclaimer.{field_name} phải là false")

    return errors


def check_signature(manifest: dict, trust_store: Optional[Dict[str, "Ed25519PublicKey"]]) -> List[str]:
    """Lớp 3: chữ ký, fail-closed. `trust_store` rỗng/None ⇒ KHÔNG tin ai (từ chối mọi signed=true)."""
    trust_store = trust_store or {}
    ok, reason = manifest_signing.verify_manifest_signature(manifest, trust_store)
    if not ok:
        return [reason]
    return []


def load_trust_store(path: Path) -> Dict[str, "Ed25519PublicKey"]:
    """Đọc trust store JSON {key_id: public_key_pem} -> {key_id: Ed25519PublicKey}."""
    from cryptography.hazmat.primitives import serialization

    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    out: Dict[str, "Ed25519PublicKey"] = {}
    for kid, pem in raw.items():
        key = serialization.load_pem_public_key(pem.encode("ascii"))
        out[kid] = key  # type: ignore[assignment]
    return out


def validate_extension(
    manifest: dict,
    trust_store: Optional[Dict[str, "Ed25519PublicKey"]] = None,
    schema: Optional[dict] = None,
) -> ValidationResult:
    """Chạy đủ 3 lớp theo thứ tự fail-closed: schema -> policy -> signature.

    Không dừng sớm ở lớp 1/2 lỗi — vẫn chạy tiếp các lớp sau để báo cáo đầy đủ
    lý do từ chối trong một lần gọi (dễ debug hơn cho tác giả extension), NHƯNG
    `accepted` chỉ True khi CẢ BA danh sách lỗi đều rỗng.
    """
    schema_errors = check_schema(manifest, schema=schema)
    policy_errors = check_policy(manifest)
    signature_errors = check_signature(manifest, trust_store)

    accepted = not (schema_errors or policy_errors or signature_errors)
    return ValidationResult(
        manifest_id=manifest.get("id"),
        accepted=accepted,
        schema_errors=schema_errors,
        policy_errors=policy_errors,
        signature_errors=signature_errors,
    )


def validate_extension_file(
    manifest_path: Path, trust_store_path: Optional[Path] = None
) -> ValidationResult:
    with Path(manifest_path).open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    trust_store = load_trust_store(trust_store_path) if trust_store_path else None
    return validate_extension(manifest, trust_store=trust_store)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="NaMiOS Extension SDK — validate manifest (ADR-0022)")
    parser.add_argument("manifest", type=Path, help="Đường dẫn file manifest JSON")
    parser.add_argument(
        "--trust-store",
        type=Path,
        default=None,
        help="File JSON {key_id: public_key_pem} các khoá publisher được ghim",
    )
    args = parser.parse_args(argv)

    result = validate_extension_file(args.manifest, args.trust_store)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
