"""App & Driver Concierge — tra "tôi muốn cài X"/"máy in Y không nhận driver"
vào HAI catalog TĨNH đã kiểm duyệt bởi con người (``data/software_catalog.json``/
``data/driver_catalog.json``), trả về một ``InstallPlan`` cho UI vẽ nút hành
động, HOẶC ``None`` nếu không khớp gì.

HARD RULE (lý do module này tồn tại, xem yêu cầu "App & Driver Concierge"):
Trợ lý KHÔNG BAO GIỜ được tự bịa một đường link tải/tên gói. MỌI
``action_payload`` trả ra từ đây đều COPY NGUYÊN VĂN từ field ``source`` của
đúng MỘT entry có thật trong hai file catalog nói trên — không có đường nào
trong module này tự ghép chuỗi URL/tên gói từ input người dùng. Không khớp
entry nào -> trả ``None`` (``resolve_app``/``resolve_driver``) hoặc
``CatalogLookup(plan=None)`` (``resolve_catalog_lookup``) — caller
(``backend.AssistantEngine``) PHẢI hiển thị thông báo trung thực "chưa có
trong kho đã kiểm duyệt", KHÔNG được tự suy ra một phương án khác thay.

Khớp bí danh: ``fold_accents`` (tái dùng từ ``knowledge_base``, không viết
lại chuẩn fold-dấu lần thứ hai) rồi so khớp CHUỖI CON cho bí danh đủ dài
(>= 3 ký tự sau khi fold) — bắt được cả mã model dính liền chữ+số (vd
"g2010" nằm trong "canon g2010"). Bí danh NGẮN (<= 2 ký tự, vd "ai"/"ps"/
"hp") dễ trùng tình cờ vào một chuỗi con của từ khác (vd "ai" nằm sẵn trong
"tồn tại" -> fold "ton tai") nên bắt buộc khớp THEO TỪ (ranh giới không phải
chữ/số ở cả hai đầu) — xem ``_alias_matches``. Trong các entry cùng khớp,
bí danh DÀI NHẤT thắng (``>`` chặt — entry khai báo trước thắng khi hoà,
cùng quy ước ``classify.classify_subsystem``), để một model/brand cụ thể
(vd "Canon G-series") thắng brand chung chung (vd "Canon")."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from namios_assistant.engine.classify import CatalogIntent, classify_catalog_intent
from namios_assistant.engine.knowledge_base import fold_accents

__all__ = [
    "ActionKind",
    "InstallPlan",
    "CatalogLookup",
    "resolve_app",
    "resolve_driver",
    "build_install_plan_for_app",
    "build_install_plan_for_driver",
    "resolve_catalog_lookup",
    "all_apps",
    "all_drivers",
]

#: Thư mục chứa hai file catalog — package-relative (cùng cách
#: ``knowledge_base._BUNDLED_KB_PATH`` trỏ ``kb/starter_kb.json``), KHÔNG
#: hardcode đường dẫn cài đặt tuyệt đối (``/opt/namios/...``) để module này
#: import/test được cả trong môi trường dev chưa build ảnh.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SOFTWARE_CATALOG_PATH = _DATA_DIR / "software_catalog.json"
_DRIVER_CATALOG_PATH = _DATA_DIR / "driver_catalog.json"

#: Ngưỡng độ dài bí danh (sau khi fold dấu) bắt buộc khớp THEO TỪ thay vì
#: chuỗi con tự do — xem docstring module.
_SHORT_ALIAS_MAX_LEN = 2

ActionKind = Literal["pkg_install", "deb_install", "pack_install", "open_url", "wine", "none"]

#: ``method`` của một entry catalog -> hành động UI thực sự sẽ chạy. Entry
#: khai báo ``method`` lạ (lỗi gõ/chưa định nghĩa) rơi về ``"none"`` (an toàn
#: nhất — không hành động nào được đoán thêm).
#:
#: ``"deb_official"`` -> ``"deb_install"`` (thêm 12/11/2026, "Vendor .deb
#: auto-install" — xem ``engine/installer.install_deb_from_url``): trước
#: đây chỉ mở trang tải (``"open_url"``); giờ UI (``ui.py``) thử tải +
#: xác minh + cài THẬT qua nút "Cài 1 chạm" chính, kèm nút "Mở trang chính
#: thức" phụ (vẫn dùng cùng ``action_payload``/``verify_domain`` — xem
#: ``_build_plan``) làm phương án dự phòng khi domain chính chủ không trả
#: về một liên kết ``.deb`` tải trực tiếp (vd trang hướng dẫn cài qua kho
#: riêng/apt-key thủ công) — tải thất bại ở bước xác minh magic bytes vẫn
#: là một kết quả TRUNG THỰC (``InstallResult.success=False`` + lý do rõ),
#: KHÔNG BAO GIỜ coi là crash.
#:
#: ``"pack"`` -> ``"pack_install"`` (cùng đợt, "Dev Pack"): một entry gộp
#: nhiều app con (``members``) — xem ``_build_pack_plan``/``InstallPlan.members``.
_ACTION_KIND_BY_METHOD: dict[str, ActionKind] = {
    "apt": "pkg_install",
    "flatpak": "pkg_install",
    "deb_official": "deb_install",
    "web": "open_url",
    "vendor": "open_url",
    "wine": "wine",
    "pack": "pack_install",
    "none": "none",
}


@dataclass(frozen=True)
class InstallPlan:
    """Phương án cài đặt/driver đã phân giải — CHỈ chứa dữ liệu lấy TRỰC TIẾP
    từ một entry catalog đã kiểm duyệt (KHÔNG tự tổng hợp/suy luận thêm
    trường nào ở runtime). UI (``ui.py``) dùng dataclass này để vẽ thẻ hành
    động, KHÔNG tự quyết định nguồn/đường link nào khác ở tầng UI.

    ``action_payload`` là: tên gói Debian khi ``method in ("apt","flatpak")``
    nói riêng app id Flathub cho ``"flatpak"``; URL đầy đủ khi ``action_kind
    in ("open_url", "deb_install")`` (cùng một URL phục vụ cả nút "Cài 1
    chạm" lẫn nút dự phòng "Mở trang chính thức" — xem ``_ACTION_KIND_BY_METHOD``);
    chuỗi RỖNG khi ``action_kind in ("wine", "pack_install", "none")`` (
    không có MỘT hành động đơn lẻ nào để chạy — ``pack_install`` thay vào đó
    có ``members``, UI tự lặp qua từng phần tử; ``wine``/``none`` chỉ hiển
    thị ``note_vi``/``alt_vi``).

    ``members`` (thêm 12/11/2026, "Dev Pack"): CHỈ khác rỗng khi
    ``action_kind == "pack_install"`` — mỗi phần tử là một ``InstallPlan``
    ĐẦY ĐỦ đã dựng sẵn cho MỘT app con của bộ (xem ``_build_pack_plan``), để
    UI cài TUẦN TỰ từng món theo ĐÚNG phương thức riêng của món đó (apt/
    flatpak/deb_install) — module này KHÔNG tự chế một phương thức cài
    "gộp" nào khác."""

    kind: Literal["app", "driver"]
    title: str
    method: str
    action_kind: ActionKind
    action_payload: str
    verify_domain: str
    note_vi: str
    alt_vi: str
    members: tuple["InstallPlan", ...] = ()


@dataclass(frozen=True)
class CatalogLookup:
    """Kết quả MỘT lần thử tra catalog cho một câu hỏi người dùng.

    ``plan is None`` nghĩa là: đã phát hiện Ý ĐỊNH cài đặt/driver (``intent``)
    NHƯNG không có entry nào khớp trong catalog đã kiểm duyệt — caller
    (``backend.AssistantEngine.ask``) PHẢI hiển thị thông báo trung thực
    (KHÔNG bịa phương án khác), xem docstring module."""

    intent: CatalogIntent
    plan: InstallPlan | None


# ---------------------------------------------------------------------------
# Nạp catalog — fail-safe tuyệt đối (cùng nguyên tắc
# ``knowledge_base._load_entries_from_file``): file vắng/hỏng/sai định dạng
# -> catalog RỖNG, KHÔNG raise. Một catalog rỗng chỉ khiến resolver luôn trả
# ``None`` (trung thực: "chưa có gì trong kho"), KHÔNG làm sập Trợ lý.
# ---------------------------------------------------------------------------
def _load_json_list(path: Path, list_key: str) -> tuple[dict[str, Any], ...]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return ()
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, dict):
        return ()
    raw_list = payload.get(list_key)
    if not isinstance(raw_list, list):
        return ()
    return tuple(item for item in raw_list if isinstance(item, dict))


@lru_cache(maxsize=1)
def _software_catalog() -> tuple[dict[str, Any], ...]:
    return _load_json_list(_SOFTWARE_CATALOG_PATH, "apps")


@lru_cache(maxsize=1)
def _driver_catalog() -> tuple[dict[str, Any], ...]:
    return _load_json_list(_DRIVER_CATALOG_PATH, "printers")


def all_apps() -> tuple[dict[str, Any], ...]:
    """Toàn bộ catalog phần mềm NGUYÊN VĂN — dùng cho script kiểm chứng/
    thống kê (vd honesty check), KHÔNG dùng trong luồng hỏi-đáp bình thường
    (luồng đó luôn đi qua ``resolve_app`` để chỉ lấy ĐÚNG MỘT kết quả khớp
    nhất, không tự duyệt cả danh sách)."""

    return _software_catalog()


def all_drivers() -> tuple[dict[str, Any], ...]:
    """Tương tự ``all_apps`` cho catalog driver máy in."""

    return _driver_catalog()


# ---------------------------------------------------------------------------
# Khớp bí danh — xem docstring module cho lý do ngưỡng độ dài.
# ---------------------------------------------------------------------------
def _alias_matches(alias_folded: str, text_folded: str) -> bool:
    if not alias_folded:
        return False
    if len(alias_folded) > _SHORT_ALIAS_MAX_LEN:
        return alias_folded in text_folded
    # Bí danh ngắn: bắt buộc ranh giới không phải chữ/số ở cả hai đầu, tránh
    # khớp nhầm vào một chuỗi con tình cờ (vd "ai" trong "tồn tại").
    pattern = r"(?<![a-z0-9])" + re.escape(alias_folded) + r"(?![a-z0-9])"
    return re.search(pattern, text_folded) is not None


def _candidate_aliases(item: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    name = item.get("name") or item.get("brand")
    if isinstance(name, str):
        candidates.append(name)
    aliases = item.get("aliases")
    if isinstance(aliases, list):
        candidates.extend(alias for alias in aliases if isinstance(alias, str))
    return candidates


def _best_match(query: str, catalog: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not query:
        return None
    folded_query = fold_accents(query)

    best: dict[str, Any] | None = None
    best_len = 0
    for item in catalog:
        for alias in _candidate_aliases(item):
            folded_alias = fold_accents(alias)
            # ``>`` chặt: khi hoà độ dài, entry khai báo TRƯỚC trong catalog
            # giữ nguyên kết quả (cùng quy ước ``classify_subsystem``).
            if _alias_matches(folded_alias, folded_query) and len(folded_alias) > best_len:
                best_len = len(folded_alias)
                best = item
    return best


def resolve_app(query: str) -> dict[str, Any] | None:
    """Tìm app khớp nhất trong ``data/software_catalog.json`` theo bí danh
    (accent-insensitive). Trả ``dict`` NGUYÊN VĂN từ catalog (không bọc thêm
    dataclass ở tầng này — giữ tầng dữ liệu thô tách khỏi tầng trình bày, xem
    ``build_install_plan_for_app``) hoặc ``None`` nếu không khớp gì. ``None``
    là một câu trả lời TRUNG THỰC ("chưa có trong kho đã kiểm duyệt"), KHÔNG
    phải lỗi."""

    return _best_match(query, _software_catalog())


def resolve_driver(query: str) -> dict[str, Any] | None:
    """Tương tự ``resolve_app`` nhưng cho hãng/dòng máy in (``data/
    driver_catalog.json``). Bí danh DÀI NHẤT thắng — một dòng máy cụ thể (vd
    alias "canon g" của entry "Canon G-series") PHẢI thắng brand chung chung
    (vd alias "canon" của entry "Canon") khi câu hỏi khớp cả hai."""

    return _best_match(query, _driver_catalog())


# ---------------------------------------------------------------------------
# Dựng InstallPlan từ một entry catalog đã resolve.
# ---------------------------------------------------------------------------
def _str_field(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    return value if isinstance(value, str) else ""


def _build_plan(item: dict[str, Any], *, kind: Literal["app", "driver"]) -> InstallPlan:
    method = _str_field(item, "method") or "none"
    action_kind = _ACTION_KIND_BY_METHOD.get(method, "none")
    source = _str_field(item, "source")
    # Payload CHỈ khác rỗng cho các hành động thực sự "chạy được gì đó" —
    # "wine"/"pack_install"/"none" không có action_payload đơn lẻ (UI chỉ
    # hiển thị note/alt, hoặc với pack_install thì tự lặp qua ``members``).
    payload = source if action_kind in ("pkg_install", "open_url", "deb_install") else ""
    title = _str_field(item, "name") or _str_field(item, "brand")
    members = _build_pack_members(item) if kind == "app" and method == "pack" else ()
    return InstallPlan(
        kind=kind,
        title=title,
        method=method,
        action_kind=action_kind,
        action_payload=payload,
        verify_domain=_str_field(item, "verify_domain"),
        note_vi=_str_field(item, "note_vi"),
        alt_vi=_str_field(item, "alt_vi"),
        members=members,
    )


def _build_pack_members(item: dict[str, Any]) -> tuple[InstallPlan, ...]:
    """Dựng một ``InstallPlan`` ĐẦY ĐỦ cho MỖI id khai báo trong field
    ``members`` của một entry ``method == "pack"`` ("Dev Pack", thêm
    12/11/2026) — mỗi id PHẢI khớp ĐÚNG MỘT entry có thật trong
    ``data/software_catalog.json``, so khớp theo field ``id`` CHÍNH XÁC
    (KHÔNG qua bí danh/fuzzy — cùng nguyên tắc chống bịa của toàn module:
    không có đường nào tự suy luận thêm app con ở đây).

    id không khớp entry nào trong catalog, HOẶC entry khớp lại tự nó cũng
    ``method == "pack"`` (chặn pack lồng pack — tránh đệ quy/một bộ kéo
    theo bộ khác gây rối UI) -> BỎ QUA phần tử đó một cách ÊM (không raise,
    không tự chế một plan giả thay vào) — honesty check
    (``tests/test_app_catalog.py``) xác nhận catalog KHÔNG khai báo id ma
    trong ``members`` nên trong thực tế luôn resolve đủ."""

    raw_members = item.get("members")
    if not isinstance(raw_members, list):
        return ()
    by_id = {
        entry.get("id"): entry
        for entry in _software_catalog()
        if isinstance(entry.get("id"), str)
    }
    resolved: list[InstallPlan] = []
    for member_id in raw_members:
        if not isinstance(member_id, str):
            continue
        member_entry = by_id.get(member_id)
        if member_entry is None or _str_field(member_entry, "method") == "pack":
            continue
        resolved.append(_build_plan(member_entry, kind="app"))
    return tuple(resolved)


def build_install_plan_for_app(app: dict[str, Any]) -> InstallPlan:
    return _build_plan(app, kind="app")


def build_install_plan_for_driver(driver: dict[str, Any]) -> InstallPlan:
    return _build_plan(driver, kind="driver")


# ---------------------------------------------------------------------------
# Điểm vào DUY NHẤT dành cho ``backend.AssistantEngine`` — gộp phân loại Ý
# ĐỊNH (``classify.classify_catalog_intent``) + tra catalog thành MỘT lời
# gọi, để backend không phải tự biết chi tiết "driver thì gọi resolve_driver,
# app thì gọi resolve_app".
# ---------------------------------------------------------------------------
def resolve_catalog_lookup(text: str) -> CatalogLookup | None:
    """Trả ``None`` nếu văn bản KHÔNG mang tín hiệu ý định cài đặt/driver nào
    (``classify_catalog_intent`` trả ``None``) — caller giữ nguyên luồng KB/
    online bình thường, hoàn toàn không đụng tới catalog. Trả
    ``CatalogLookup`` (có thể ``plan=None``) khi có tín hiệu nhưng catalog
    không khớp entry nào — xem docstring ``CatalogLookup``."""

    intent = classify_catalog_intent(text)
    if intent is None:
        return None

    if intent == "driver_request":
        driver = resolve_driver(text)
        plan = build_install_plan_for_driver(driver) if driver is not None else None
    else:
        app = resolve_app(text)
        plan = build_install_plan_for_app(app) if app is not None else None

    return CatalogLookup(intent=intent, plan=plan)
