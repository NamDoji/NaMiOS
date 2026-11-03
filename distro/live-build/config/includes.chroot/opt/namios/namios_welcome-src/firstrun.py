"""Áp lựa chọn lần đầu (UI-005) bằng cách ghi file config trong ``$HOME`` —
KHÔNG cần root, KHÔNG đổi file hệ thống.

``ConfigApplier`` ghi/đọc một file JSON duy nhất (``welcome.json``) trong
thư mục config do caller truyền vào (mặc định caller dùng
``namios_core.paths.config_dir()``; module này KHÔNG tự hardcode
``~/.config``). Mọi lần ``apply()`` đều giữ lại giá trị TRƯỚC đó trong một
file backup (``welcome.json.bak``) để ``revert()`` khôi phục được — "hoàn
tác" ở đây nghĩa là lấy lại đúng nội dung lần áp dụng trước, không phải một
Undo tổng quát cho toàn hệ thống (bộ gõ/cỡ chữ/app mặc định thật sự có hiệu
lực chỉ khi desktop session đọc file này — nằm ngoài phạm vi module, xem
ADR 0011)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from namios_i18n import Lang, t

# NOTE (i18n, 03/11/2026): ``reason_vi``/``FirstRunValidationError.reason_vi``
# đi qua ``namios_i18n.t`` (nhóm key ``welcome.firstrun.error.*``, VI/EN đã
# seed) nhưng LUÔN ép ``lang=Lang.VI`` — field đặt tên theo quy ước ``_vi``
# (giống ``ValidationError.message_vi`` ở namios_eco/namios_core), một
# nguồn sự thật chung, KHÔNG đổi theo ngôn ngữ hiển thị wizard (``ui.py``
# dịch phần LABEL hiển thị riêng, độc lập với exception này).

__all__ = [
    "ImeMethod",
    "UiScalePercent",
    "FirstRunChoices",
    "AppliedConfigReport",
    "FirstRunValidationError",
    "ConfigApplier",
]

ImeMethod = Literal["telex", "vni"]
UiScalePercent = Literal[100, 125, 150]

_VALID_IME_METHODS: frozenset[str] = frozenset({"telex", "vni"})
_VALID_UI_SCALES: frozenset[int] = frozenset({100, 125, 150})

_CONFIG_FILENAME = "welcome.json"
_BACKUP_SUFFIX = ".bak"
_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FirstRunChoices:
    """Các lựa chọn luồng đầu tiên (UI-005). ``default_printer=None`` nghĩa
    là người dùng chưa chọn máy in mặc định (bỏ qua bước này)."""

    ime_method: ImeMethod
    ui_scale_percent: UiScalePercent
    default_app_docx: str
    default_app_xlsx: str
    default_app_pdf: str
    default_printer: str | None = None

    def validate(self) -> None:
        if self.ime_method not in _VALID_IME_METHODS:
            raise FirstRunValidationError(
                field="ime_method",
                reason_vi=t(
                    "welcome.firstrun.error.ime_method_invalid",
                    lang=Lang.VI,
                    value=self.ime_method,
                ),
            )
        if self.ui_scale_percent not in _VALID_UI_SCALES:
            raise FirstRunValidationError(
                field="ui_scale_percent",
                reason_vi=t(
                    "welcome.firstrun.error.ui_scale_invalid",
                    lang=Lang.VI,
                    value=self.ui_scale_percent,
                ),
            )
        for field_name, value in (
            ("default_app_docx", self.default_app_docx),
            ("default_app_xlsx", self.default_app_xlsx),
            ("default_app_pdf", self.default_app_pdf),
        ):
            if not value or not value.strip():
                raise FirstRunValidationError(
                    field=field_name,
                    reason_vi=t("welcome.firstrun.error.field_blank", lang=Lang.VI),
                )


@dataclass(frozen=True)
class AppliedConfigReport:
    """Kết quả một lần ``apply()`` — ``previous`` là giá trị trước đó
    (``None`` nếu đây là lần áp dụng đầu tiên)."""

    config_path: str
    backup_path: str | None
    previous: FirstRunChoices | None
    current: FirstRunChoices


@dataclass
class FirstRunValidationError(Exception):
    """Lựa chọn lần đầu không hợp lệ (field cụ thể)."""

    field: str
    reason_vi: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return t(
            "welcome.firstrun.error.validation_prefix",
            lang=Lang.VI,
            field=self.field,
            reason=self.reason_vi,
        )


def _choices_to_payload(choices: FirstRunChoices, applied_at: str) -> dict[str, Any]:
    payload = asdict(choices)
    payload["schema_version"] = _SCHEMA_VERSION
    payload["applied_at"] = applied_at
    return payload


def _payload_to_choices(payload: dict[str, Any]) -> FirstRunChoices:
    return FirstRunChoices(
        ime_method=payload["ime_method"],
        ui_scale_percent=payload["ui_scale_percent"],
        default_app_docx=payload["default_app_docx"],
        default_app_xlsx=payload["default_app_xlsx"],
        default_app_pdf=payload["default_app_pdf"],
        default_printer=payload.get("default_printer"),
    )


def _default_clock() -> datetime:
    return datetime.now(tz=UTC)


class ConfigApplier:
    """Ghi/đọc/hoàn tác lựa chọn luồng đầu tiên trong một file config JSON
    dưới ``config_dir`` (do caller truyền vào — KHÔNG hardcode ``$HOME``)."""

    def __init__(
        self,
        config_dir: Path | str,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._clock = clock if clock is not None else _default_clock

    @property
    def config_path(self) -> Path:
        return self._config_dir / _CONFIG_FILENAME

    @property
    def backup_path(self) -> Path:
        return self._config_dir / f"{_CONFIG_FILENAME}{_BACKUP_SUFFIX}"

    def read_current(self) -> FirstRunChoices | None:
        """Đọc lựa chọn hiện tại. Trả ``None`` nếu chưa có file hoặc file
        hỏng (KHÔNG ném lỗi — coi như "chưa áp dụng lần nào")."""

        return self._read_payload_as_choices(self.config_path)

    def _read_payload_as_choices(self, path: Path) -> FirstRunChoices | None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            payload = json.loads(text)
            return _payload_to_choices(payload)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def _write_atomic(self, path: Path, payload: dict[str, Any]) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_path, path)

    def apply(self, choices: FirstRunChoices) -> AppliedConfigReport:
        """Ghi ``choices`` vào file config (không cần root). Giá trị trước
        đó (nếu có) được sao lưu vào file ``.bak`` để ``revert()`` dùng."""

        choices.validate()
        previous = self.read_current()

        if self.config_path.exists():
            self._config_dir.mkdir(parents=True, exist_ok=True)
            previous_text = self.config_path.read_text(encoding="utf-8")
            tmp_backup = self.backup_path.with_name(f"{self.backup_path.name}.tmp-{os.getpid()}")
            tmp_backup.write_text(previous_text, encoding="utf-8")
            os.replace(tmp_backup, self.backup_path)

        applied_at = self._clock().isoformat()
        payload = _choices_to_payload(choices, applied_at)
        self._write_atomic(self.config_path, payload)

        return AppliedConfigReport(
            config_path=str(self.config_path),
            backup_path=str(self.backup_path) if self.backup_path.exists() else None,
            previous=previous,
            current=choices,
        )

    def revert(self) -> FirstRunChoices | None:
        """Khôi phục config về giá trị TRƯỚC lần ``apply()`` gần nhất (từ
        file ``.bak``). Trả giá trị đã khôi phục, hoặc ``None`` nếu không có
        backup để hoàn tác (chưa từng ``apply()`` quá 1 lần)."""

        if not self.backup_path.exists():
            return None
        restored = self._read_payload_as_choices(self.backup_path)
        backup_text = self.backup_path.read_text(encoding="utf-8")
        self._config_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.config_path.with_name(f"{self.config_path.name}.tmp-{os.getpid()}")
        tmp_path.write_text(backup_text, encoding="utf-8")
        os.replace(tmp_path, self.config_path)
        os.remove(self.backup_path)
        return restored
