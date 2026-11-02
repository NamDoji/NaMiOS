"""Loader cho danh bạ dịch vụ ECO-006 (``catalog/services/*.json``) dùng bởi
subcommand ``namios service`` — WP3, phần ECO DATA + CLI (vai trò ``namios_eco``).

Thiết kế:
  - Danh bạ là dữ liệu TĨNH đóng gói sẵn trong repo (không phải input do người
    dùng cung cấp tại runtime), nên KHÔNG cần đi qua ``namios_security.
    resolve_within`` (dành cho path người dùng chọn — §8/SEC-002); đường dẫn
    thư mục catalog là hằng số nội bộ, không nhận giá trị từ argv/env.
  - Mỗi file phải qua ĐỦ HAI tầng thẩm định của ``namios_eco`` trước khi được
    coi là một ``ServiceEntry`` hợp lệ: tầng 1 cấu trúc
    (``catalog_schema.validate_raw``) + tầng 2 ngữ nghĩa tối thiểu (URL chính
    thức + không có khóa thực thi lạ — ``validator.validate_official_url``/
    ``validate_no_executable_keys``). Catalog hỏng là LỖI NỘI BỘ (dữ liệu đóng
    gói cùng repo phải luôn hợp lệ), không phải lỗi input người dùng — caller
    (``namios_cli.main``) chuẩn hoá về ``E_INTERNAL``.
  - KHÔNG tự "sửa" hay bỏ qua entry hỏng để trả về danh sách rút gọn — một
    file hỏng làm toàn bộ lệnh thất bại rõ ràng, tránh im lặng thiếu dữ liệu.
"""

from __future__ import annotations

import json
from pathlib import Path

from namios_eco import validator as eco_validator
from namios_eco.catalog_schema import build_entry, validate_raw
from namios_eco.models import ServiceEntry

__all__ = [
    "CATALOG_SERVICES_DIR",
    "ServiceCatalogLoadError",
    "load_service_catalog",
]

#: ``<repo_root>/catalog/services`` — file này ở ``src/namios_cli/…``, nên
#: ``parents[2]`` là gốc repo (``src/namios_cli/x.py`` → ``namios_cli`` →
#: ``src`` → gốc repo).
CATALOG_SERVICES_DIR = Path(__file__).resolve().parents[2] / "catalog" / "services"


class ServiceCatalogLoadError(Exception):
    """Danh bạ đóng gói cùng repo không đọc/thẩm định được — LỖI NỘI BỘ (dữ
    liệu đã được validate khi build, không phải input runtime của người
    dùng)."""


def _validate_entry_raw(raw: object, *, source_label: str) -> None:
    schema_errors = validate_raw(raw)
    if schema_errors:
        first = schema_errors[0]
        raise ServiceCatalogLoadError(
            f"{source_label}: lỗi cấu trúc tầng 1 tại '{first.path}': {first.message_vi}"
        )
    assert isinstance(raw, dict)  # validate_raw đã xác nhận ở trên
    semantic_errors = [
        *eco_validator.validate_official_url(raw["official_url"]),
        *eco_validator.validate_no_executable_keys(raw),
    ]
    if semantic_errors:
        first = semantic_errors[0]
        raise ServiceCatalogLoadError(
            f"{source_label}: lỗi ngữ nghĩa tầng 2 tại '{first.path}': {first.message_vi}"
        )


def load_service_catalog(directory: Path | None = None) -> tuple[ServiceEntry, ...]:
    """Đọc + thẩm định (2 tầng) mọi file ``*.json`` dưới ``directory``
    (mặc định ``CATALOG_SERVICES_DIR``), trả tuple ``ServiceEntry`` đã ổn định
    thứ tự theo tên file (để kết quả CLI xác định, không phụ thuộc thứ tự
    liệt kê filesystem).

    Raise :class:`ServiceCatalogLoadError` ngay khi file đầu tiên hỏng — KHÔNG
    trả danh sách rút gọn/lặng lẽ bỏ entry lỗi.
    """

    base = directory if directory is not None else CATALOG_SERVICES_DIR
    if not base.is_dir():
        return ()

    entries: list[ServiceEntry] = []
    for path in sorted(base.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ServiceCatalogLoadError(
                f"Không đọc được file catalog '{path.name}': {type(exc).__name__}."
            ) from exc
        _validate_entry_raw(raw, source_label=path.name)
        entries.append(build_entry(raw))

    return tuple(entries)
