"""Helper dựng raw manifest dict dùng RIÊNG cho bộ test đối kháng (adversarial)
của tester T1. CỐ Ý viết độc lập với ``tests/unit/manifest/_fixtures.py`` của
dev (không import, không tái dùng) — tránh test của tester bị lệch cùng giả
định với code đang kiểm thử. Không phải test case (không được pytest thu
thập — không có hàm bắt đầu bằng ``test_``)."""

from __future__ import annotations

import copy
from typing import Any


def baseline_manifest() -> dict[str, Any]:
    """Manifest tối thiểu PASS cả 2 tầng (schema + semantic), mode=native,
    không cần runner/dependency — dùng làm gốc để tester tự mutate/tiêm lỗi."""

    return {
        "schema_version": "1.0",
        "id": "qa-t1-baseline",
        "name": "QA T1 Baseline App",
        "publisher": "QA Tester",
        "mode": "native",
        "application": {
            "version": "1.0.0",
            "build": "2026.11.02",
            "architecture": "x86_64",
            "installer_sha256": "b" * 64,
        },
        "license": {
            "kind": "open_source",
            "spdx_expression": "MIT",
            "user_entitlement_required": False,
            "redistribution": "allowed_with_conditions",
            "terms_url": "https://example.test/terms",
        },
        "source": {
            "acquisition": "distribution_repository",
            "official_url": "https://example.test/download",
            "allowed_hosts": ["example.test"],
            "automatic_download": False,
        },
        "runtime": {
            "runner_id": None,
            "runner_sha256": None,
            "prefix_architecture": "not_applicable",
            "wow64_strategy": "not_applicable",
            "dependency_profile_ids": [],
        },
        "permissions": {
            "filesystem": [{"scope": "app_data", "access": "read_write"}],
            "network": "deny",
            "audio": False,
            "microphone": False,
            "camera": False,
            "printing": False,
            "clipboard": "deny",
            "display": "wayland",
            "isolation": "not_applicable",
            "exceptions": [],
        },
        "recipe": [],
        "compatibility": {
            "status": "untested",
            "vendor_support": "unknown",
            "required_task_ids": [],
            "limitations": [],
            "last_tested": None,
            "evidence_id": None,
        },
    }


def mutate(raw: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(raw)
