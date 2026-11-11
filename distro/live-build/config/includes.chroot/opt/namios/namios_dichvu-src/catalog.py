"""Nạp + lọc danh bạ dịch vụ Việt (``services_vn.json``) cho Cổng Dịch vụ
Việt + Trung tâm Ký số (VN-2/VN-3, ``docs/roadmap/NEW-FUNCTIONS-DIRECTION.md``).

Module này KHÔNG import PySide6 (test được không cần GUI, cùng quy ước
``namios_assistant.engine``/``namios_lich.lunar``) và KHÔNG import
``namios_essentials``/``namios_eco`` (hai gói đó CHƯA được đóng gói vào
``/opt/namios`` của ảnh ở thời điểm viết module này — xem
``includes.chroot/opt/namios/`` chỉ có ``namios_core``/``namios_i18n``/
``namios_security`` là thư viện COMMON thật sự có mặt trong ảnh; import một
gói không có trong ảnh sẽ làm app crash ngay khi mở, phá vỡ yêu cầu
fail-safe). Vì vậy lớp "phân loại trạng thái"/"tìm không dấu" ở đây được viết
LẠI một cách tối giản, cùng NGUYÊN TẮC với ``namios_eco.status``/
``namios_eco.search``/``namios_essentials.labels`` (đọc 7 nấc thật, không bịa
"usable", bỏ dấu kiểu NFD+casefold) nhưng KHÔNG import chéo module đó — ứng
dụng này tự chứa (self-contained) theo đúng yêu cầu phạm vi của wave này.

``ServiceEntry.realistic_status`` (``works-web``/``works-native``/
``wine-candidate``/``blocked``) là một nhãn PHÂN LOẠI RIÊNG của NaMiOS, tác
giả thủ công dựa trên dữ liệu ``catalog/services/*.json`` +
``docs/wine/WINE-COMPAT-MATRIX.md`` + ``docs/wine/KY-SO-PKCS11-RESEARCH.md``
đã có trong repo (xem ``services_vn.json["disclaimer_vi"]``) — KHÔNG phải xác
nhận của nhà cung cấp, KHÔNG đồng nghĩa ``published_status`` (ECO-003, 7 nấc)
lấy trực tiếp từ catalog gốc khi có. Hai trường này hiển thị RIÊNG, không gộp
lẫn (ECO-004: ``tested_by_namios``/``officially_supported_by_vendor`` cũng độc
lập, giữ nguyên từ catalog)."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

__all__ = [
    "RealisticStatus",
    "REALISTIC_STATUSES",
    "Category",
    "AppOption",
    "ServiceEntry",
    "ServiceCatalog",
    "fold_vi",
    "load_catalog",
    "filter_services",
    "services_in_category",
]

#: 4 giá trị DUY NHẤT hợp lệ cho ``realistic_status`` (theo chỉ đạo phạm vi
#: VN-2/VN-3: "Per-service status must be one of: works-web / works-native /
#: wine-candidate / blocked"). Hợp đồng dữ liệu ổn định — ``services_vn.json``
#: PHẢI chỉ dùng 4 giá trị này, ``_coerce_entry`` ép về ``"blocked"`` (an toàn
#: nhất) nếu gặp giá trị lạ, KHÔNG đoán một trạng thái "tốt" cho giá trị
#: không nhận diện được.
RealisticStatus = Literal["works-web", "works-native", "wine-candidate", "blocked"]
REALISTIC_STATUSES: tuple[str, ...] = (
    "works-web",
    "works-native",
    "wine-candidate",
    "blocked",
)

_DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent / "services_vn.json"

_DJ_MAP = {"đ": "d", "Đ": "D"}
_WS_RE = re.compile(r"\s+")


def fold_vi(text: str) -> str:
    """Chuẩn hoá KHÔNG DẤU, không phân biệt hoa/thường — CHỈ dùng để tìm
    kiếm (ECO-007: "khai thue" phải khớp "khai thuế"). Thuật toán: thay "đ"
    tường minh (NFD không tách "đ" thành "d" + dấu gạch), NFD bỏ dấu tổ hợp,
    NFC ghép lại, casefold. Cùng thuật toán với ``namios_eco.search.fold_vn``/
    ``namios_essentials.labels._fold`` — viết lại độc lập ở đây vì module này
    không import hai gói đó (xem docstring module)."""

    translated = "".join(_DJ_MAP.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFD", translated)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    recomposed = unicodedata.normalize("NFC", stripped)
    return recomposed.casefold()


def _collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


@dataclass(frozen=True)
class Category:
    id: str
    label_vi: str
    label_en: str

    def label(self, *, lang: str = "vi") -> str:
        return self.label_vi if lang == "vi" else self.label_en


@dataclass(frozen=True)
class AppOption:
    """Một lựa chọn "Mở ứng dụng" (``action == "open_app"``) — ví dụ Okular
    HOẶC nOffice/LibreOffice cho tuyến ký .p12 (VN-3 tuyến 2)."""

    app_command: str
    label_vi: str
    label_en: str

    def label(self, *, lang: str = "vi") -> str:
        return self.label_vi if lang == "vi" else self.label_en


@dataclass(frozen=True)
class ServiceEntry:
    id: str
    category: str
    name_vi: str
    name_en: str
    provider: str
    purpose_vi: str
    official_url: str | None
    action: str  # "open_web" | "open_app" | "probe_pkcs11" | "info"
    app_options: tuple[AppOption, ...]
    windows_mode: str | None
    published_status: str | None
    realistic_status: str
    status_reason_vi: str
    status_reason_en: str
    tested_by_namios: bool
    officially_supported_by_vendor: bool
    account_condition_vi: str | None
    guide_vi: str | None
    guide_en: str | None
    last_updated: str | None
    source: str
    search_terms: tuple[str, ...]
    priority: int | None = None
    recommended: bool = False

    def name(self, *, lang: str = "vi") -> str:
        return self.name_vi if lang == "vi" else self.name_en

    def status_reason(self, *, lang: str = "vi") -> str:
        return self.status_reason_vi if lang == "vi" else self.status_reason_en

    def guide(self, *, lang: str = "vi") -> str | None:
        return self.guide_vi if lang == "vi" else self.guide_en

    def haystack(self) -> str:
        """Chuỗi gộp dùng để tìm kiếm (ECO-007) — tên, nhà cung cấp, mô tả,
        nhãn danh mục gốc, từ khoá phụ. KHÔNG fold ở đây — caller
        (``filter_services``) tự fold một lần cho cả haystack + query."""

        parts = [self.id, self.name_vi, self.name_en, self.provider, self.purpose_vi]
        parts.extend(self.search_terms)
        return " ".join(parts)


@dataclass(frozen=True)
class ServiceCatalog:
    schema_version: str
    generated_at: str | None
    verified_on_host: bool
    disclaimer_vi: str
    disclaimer_en: str
    status_legend: dict[str, dict[str, str]]
    categories: tuple[Category, ...]
    services: tuple[ServiceEntry, ...]
    empty_category_notes: dict[str, dict[str, str]] = field(default_factory=dict)
    load_error_vi: str | None = None

    def category_by_id(self, category_id: str) -> Category | None:
        for c in self.categories:
            if c.id == category_id:
                return c
        return None


def _empty_catalog(error_vi: str) -> ServiceCatalog:
    """Catalog rỗng fail-safe — dùng khi file dữ liệu vắng/hỏng. App vẫn mở
    được (cửa sổ trống + thông báo lỗi rõ), KHÔNG crash toàn bộ GUI vì một
    file JSON lỗi (cùng nguyên tắc fail-safe của ``namios_assistant.config``)."""

    return ServiceCatalog(
        schema_version="unknown",
        generated_at=None,
        verified_on_host=False,
        disclaimer_vi=error_vi,
        disclaimer_en=(
            "Could not load the service catalog data file — see the Vietnamese "
            "message for detail. The window is still usable but empty."
        ),
        status_legend={},
        categories=(),
        services=(),
        empty_category_notes={},
        load_error_vi=error_vi,
    )


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _bool_or_false(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _tuple_of_str(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(v for v in value if isinstance(v, str))


def _coerce_app_options(value: Any) -> tuple[AppOption, ...]:
    if not isinstance(value, list):
        return ()
    options: list[AppOption] = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        cmd = _str_or_none(raw.get("app_command"))
        if cmd is None:
            continue
        options.append(
            AppOption(
                app_command=cmd,
                label_vi=_str_or_none(raw.get("label_vi")) or cmd,
                label_en=_str_or_none(raw.get("label_en")) or cmd,
            )
        )
    return tuple(options)


def _coerce_entry(raw: dict[str, Any]) -> ServiceEntry | None:
    entry_id = _str_or_none(raw.get("id"))
    category = _str_or_none(raw.get("category"))
    name_vi = _str_or_none(raw.get("name_vi"))
    purpose_vi = _str_or_none(raw.get("purpose_vi"))
    if entry_id is None or category is None or name_vi is None or purpose_vi is None:
        return None  # thiếu trường bắt buộc -> bỏ qua entry hỏng, không crash cả catalog

    realistic_status = raw.get("realistic_status")
    if realistic_status not in REALISTIC_STATUSES:
        # Giá trị lạ/thiếu -> ép về "blocked" (an toàn nhất, KHÔNG đoán "tốt"
        # cho một entry có dữ liệu không nhận diện được).
        realistic_status = "blocked"

    return ServiceEntry(
        id=entry_id,
        category=category,
        name_vi=name_vi,
        name_en=_str_or_none(raw.get("name_en")) or name_vi,
        provider=_str_or_none(raw.get("provider")) or "",
        purpose_vi=purpose_vi,
        official_url=_str_or_none(raw.get("official_url")),
        action=_str_or_none(raw.get("action")) or "info",
        app_options=_coerce_app_options(raw.get("app_options")),
        windows_mode=_str_or_none(raw.get("windows_mode")),
        published_status=_str_or_none(raw.get("published_status")),
        realistic_status=realistic_status,
        status_reason_vi=_str_or_none(raw.get("status_reason_vi")) or "",
        status_reason_en=_str_or_none(raw.get("status_reason_en")) or "",
        tested_by_namios=_bool_or_false(raw.get("tested_by_namios")),
        officially_supported_by_vendor=_bool_or_false(raw.get("officially_supported_by_vendor")),
        account_condition_vi=_str_or_none(raw.get("account_condition_vi")),
        guide_vi=_str_or_none(raw.get("guide_vi")),
        guide_en=_str_or_none(raw.get("guide_en")),
        last_updated=_str_or_none(raw.get("last_updated")),
        source=_str_or_none(raw.get("source")) or "",
        search_terms=_tuple_of_str(raw.get("search_terms")),
        priority=raw.get("priority") if isinstance(raw.get("priority"), int) else None,
        recommended=_bool_or_false(raw.get("recommended")),
    )


def load_catalog(path: Path | None = None) -> ServiceCatalog:
    """Nạp ``services_vn.json``. Fail-safe tuyệt đối: file vắng/hỏng/JSON sai
    cấu trúc -> trả catalog RỖNG kèm ``load_error_vi`` rõ ràng, KHÔNG raise
    (app vẫn mở được cửa sổ, hiển thị thông báo, không crash — cùng nguyên
    tắc ``namios_assistant.branding.load_brand_colors``)."""

    catalog_path = path if path is not None else _DEFAULT_CATALOG_PATH
    try:
        raw_text = catalog_path.read_text(encoding="utf-8")
    except OSError:
        return _empty_catalog(
            "Không đọc được dữ liệu dịch vụ — Cổng Dịch vụ Việt hiện chưa có dữ liệu để "
            "hiển thị. Hãy thử khởi động lại ứng dụng; nếu vẫn lỗi, báo thông báo này cho "
            "người quản trị máy."
        )

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return _empty_catalog(
            "Dữ liệu dịch vụ cài sẵn trên máy bị lỗi định dạng nên không đọc được. Đây là "
            "lỗi dữ liệu cài sẵn, không phải do thao tác của bạn — hãy thử khởi động lại ứng "
            "dụng; nếu vẫn lỗi, báo thông báo này cho người quản trị máy hoặc đội NaMiOS."
        )

    if not isinstance(data, dict):
        return _empty_catalog(
            "Dữ liệu dịch vụ cài sẵn trên máy sai cấu trúc nên không đọc được. Đây là lỗi "
            "dữ liệu cài sẵn trên máy, không phải do thao tác của bạn — hãy thử khởi động "
            "lại ứng dụng; nếu vẫn lỗi, báo thông báo này cho người quản trị máy hoặc đội "
            "NaMiOS."
        )

    categories: list[Category] = []
    for raw_cat in data.get("categories", []):
        if not isinstance(raw_cat, dict):
            continue
        cat_id = _str_or_none(raw_cat.get("id"))
        if cat_id is None:
            continue
        categories.append(
            Category(
                id=cat_id,
                label_vi=_str_or_none(raw_cat.get("label_vi")) or cat_id,
                label_en=_str_or_none(raw_cat.get("label_en")) or cat_id,
            )
        )

    services: list[ServiceEntry] = []
    for raw_entry in data.get("services", []):
        if not isinstance(raw_entry, dict):
            continue
        entry = _coerce_entry(raw_entry)
        if entry is not None:
            services.append(entry)

    status_legend_raw = data.get("status_legend")
    status_legend: dict[str, dict[str, str]] = {}
    if isinstance(status_legend_raw, dict):
        for key, value in status_legend_raw.items():
            if isinstance(key, str) and isinstance(value, dict):
                status_legend[key] = {
                    k: v for k, v in value.items() if isinstance(k, str) and isinstance(v, str)
                }

    empty_notes_raw = data.get("empty_category_notes")
    empty_notes: dict[str, dict[str, str]] = {}
    if isinstance(empty_notes_raw, dict):
        for key, value in empty_notes_raw.items():
            if isinstance(key, str) and isinstance(value, dict):
                empty_notes[key] = {
                    k: v for k, v in value.items() if isinstance(k, str) and isinstance(v, str)
                }

    return ServiceCatalog(
        schema_version=_str_or_none(data.get("schema_version")) or "unknown",
        generated_at=_str_or_none(data.get("generated_at")),
        verified_on_host=_bool_or_false(data.get("verified_on_host")),
        disclaimer_vi=_str_or_none(data.get("disclaimer_vi")) or "",
        disclaimer_en=_str_or_none(data.get("disclaimer_en")) or "",
        status_legend=status_legend,
        categories=tuple(categories),
        services=tuple(services),
        empty_category_notes=empty_notes,
    )


def services_in_category(services: tuple[ServiceEntry, ...], category_id: str | None) -> tuple[ServiceEntry, ...]:
    """``category_id is None`` -> "Tất cả" (không lọc theo danh mục)."""

    if category_id is None:
        return services
    return tuple(s for s in services if s.category == category_id)


def filter_services(
    services: tuple[ServiceEntry, ...],
    *,
    category_id: str | None,
    query: str,
) -> tuple[ServiceEntry, ...]:
    """Lọc theo danh mục + tìm không dấu (ECO-007). Khớp SUBSTRING trên
    haystack đã fold; query rỗng/chỉ khoảng trắng -> không lọc theo chữ (chỉ
    còn lọc theo danh mục). Thứ tự giữ nguyên thứ tự khai báo trong
    ``services_vn.json`` (ưu tiên: recommended/priority thấp trước — xem
    ``priority`` của các entry ký số)."""

    scoped = services_in_category(services, category_id)
    folded_query = _collapse_ws(fold_vi(query))
    if not folded_query:
        return tuple(sorted(scoped, key=_sort_key))

    hits = [s for s in scoped if folded_query in fold_vi(s.haystack())]
    return tuple(sorted(hits, key=_sort_key))


def _sort_key(entry: ServiceEntry) -> tuple[int, int, str]:
    priority = entry.priority if entry.priority is not None else 99
    recommended_rank = 0 if entry.recommended else 1
    return (priority, recommended_rank, entry.id)
