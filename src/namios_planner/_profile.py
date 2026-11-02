"""Digest ổn định của phần "hồ sơ" (profile) một ``Manifest`` dùng cho
``InstallPlan.profile_digest``.

Chỉ lấy các trường ảnh hưởng đến NỘI DUNG cài đặt thật (id, build/kiến
trúc ứng dụng, runner đã pin, recipe) — KHÔNG lấy trường mô tả/metadata
không ảnh hưởng hành vi cài (vd. ``name`` hiển thị) để digest ổn định khi
chỉ đổi metadata không liên quan. Đây là digest NỘI BỘ của planner, không
phải hợp đồng dùng chung — WP khác không cần đọc nó.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from namios_core.manifest_types import Manifest
from namios_planner._digest import sha256_text

__all__ = ["profile_digest"]


def _as_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {k: _as_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, tuple | list):
        return [_as_jsonable(v) for v in value]
    return value


def _profile_payload(m: Manifest) -> dict[str, Any]:
    return {
        "schema_version": m.schema_version,
        "id": m.id,
        "mode": m.mode,
        "application": _as_jsonable(m.application),
        "runtime": _as_jsonable(m.runtime),
        "recipe": [_as_jsonable(step) for step in m.recipe],
    }


def profile_digest(m: Manifest) -> str:
    payload = _profile_payload(m)
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256_text(canonical)
