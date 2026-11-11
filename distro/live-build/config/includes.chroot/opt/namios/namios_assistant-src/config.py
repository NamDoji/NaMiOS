"""Cấu hình backend AI trực tuyến (TUỲ CHỌN) cho NaMiOS Assistant.

Nguồn cấu hình, theo thứ tự ưu tiên (biến môi trường PHỦ giá trị file config
— tiện cho test/chạy thử một lần mà không sửa file):

1. Biến môi trường ``NAMIOS_ASSISTANT_API_KEY`` / ``NAMIOS_ASSISTANT_MODEL`` /
   ``NAMIOS_ASSISTANT_BASE_URL`` / ``NAMIOS_ASSISTANT_TIMEOUT_SECONDS``.
2. File ``$XDG_CONFIG_HOME/namios/assistant.json`` (``namios_core.paths.
   config_dir()``), dạng ``{"api_key": "...", "model": "...", "base_url":
   "...", "request_timeout_seconds": 20}``.
3. KHÔNG có giá trị mặc định cho ``api_key``/``model``/``base_url`` — thiếu
   BẤT KỲ cái nào, ``AssistantConfig`` coi là "chưa cấu hình" (xem
   ``OnlineLlmBackend.is_configured``) và ``AssistantEngine`` tự rơi về KB
   ngoại tuyến, KHÔNG đoán một nhà cung cấp/giá trị mặc định thay người dùng.

File config CHỨA api_key ở dạng thuần văn bản (giống nhiều app desktop khác
đọc key qua file JSON cục bộ) — ``docs/SMARTAI-ASSISTANT.md`` khuyến nghị đặt
quyền file ``600`` thủ công; module này CHỈ ĐỌC, không tự ghi/tạo file đó."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from namios_core.paths import config_dir

__all__ = ["AssistantConfig", "load_config"]

_CONFIG_FILENAME = "assistant.json"

_ENV_API_KEY = "NAMIOS_ASSISTANT_API_KEY"
_ENV_MODEL = "NAMIOS_ASSISTANT_MODEL"
_ENV_BASE_URL = "NAMIOS_ASSISTANT_BASE_URL"
_ENV_TIMEOUT_SECONDS = "NAMIOS_ASSISTANT_TIMEOUT_SECONDS"

_DEFAULT_TIMEOUT_SECONDS = 20.0


@dataclass(frozen=True)
class AssistantConfig:
    """Cấu hình hiệu lực của backend AI trực tuyến. ``api_key``/``model``/
    ``base_url`` là ``None`` khi KHÔNG được cấu hình ở đâu cả (env lẫn file)
    — caller (``OnlineLlmBackend.is_configured``) coi thiếu BẤT KỲ field nào
    trong ba field này là "chưa cấu hình", không dùng giá trị rỗng ngầm."""

    api_key: str | None
    model: str | None
    base_url: str | None
    request_timeout_seconds: float

    @property
    def is_online_configured(self) -> bool:
        return bool(self.api_key) and bool(self.model) and bool(self.base_url)


def _read_config_file(path: Path) -> dict[str, Any]:
    """Đọc file config JSON. File vắng/hỏng -> ``{}`` (coi như chưa cấu hình
    gì qua file), KHÔNG raise — một file config lỗi không được làm app không
    mở lên được."""

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _non_empty_str(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _parse_timeout(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def load_config(*, config_directory: Path | None = None) -> AssistantConfig:
    """Nạp cấu hình hiệu lực. ``config_directory`` tiêm từ ngoài cho test
    (mặc định ``namios_core.paths.config_dir()`` — KHÔNG hardcode ``~/.config``
    lần thứ hai, cùng quy ước ``namios_welcome.ConfigApplier``)."""

    cfg_dir = config_directory if config_directory is not None else config_dir()
    file_payload = _read_config_file(cfg_dir / _CONFIG_FILENAME)

    api_key = os.environ.get(_ENV_API_KEY) or _non_empty_str(file_payload.get("api_key"))
    model = os.environ.get(_ENV_MODEL) or _non_empty_str(file_payload.get("model"))
    base_url = os.environ.get(_ENV_BASE_URL) or _non_empty_str(file_payload.get("base_url"))

    timeout = (
        _parse_timeout(os.environ.get(_ENV_TIMEOUT_SECONDS))
        or _parse_timeout(file_payload.get("request_timeout_seconds"))
        or _DEFAULT_TIMEOUT_SECONDS
    )

    return AssistantConfig(
        api_key=api_key,
        model=model,
        base_url=base_url,
        request_timeout_seconds=timeout,
    )
