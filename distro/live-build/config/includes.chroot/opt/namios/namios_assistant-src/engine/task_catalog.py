"""Task Concierge — tra "làm sao để thay đổi giao diện?"/"tôi muốn kết nối
Wi-Fi" vào MỘT catalog TĨNH đã kiểm duyệt bởi con người
(``data/task_catalog.json``), trả về một ``TaskPlan`` cho UI vẽ: hướng dẫn
ngắn (``steps_vi``) + MỘT nút hành động bấm-là-chạy (mở đúng trang Cài đặt/
công cụ), HOẶC ``None`` nếu không khớp tác vụ nào.

HARD RULE (cùng nguyên tắc ``engine/app_catalog.py`` — lý do module này tồn
tại): Trợ lý KHÔNG BAO GIỜ được để mô hình AI tự CHẾ ra một lệnh để chạy.
MỌI ``action_exec`` trả ra từ đây đều COPY NGUYÊN VĂN mảng ``action.exec`` của
đúng MỘT entry có thật trong ``data/task_catalog.json`` — không có đường nào
trong module này tự ghép chuỗi lệnh từ input người dùng. Không khớp entry nào
-> ``resolve`` trả ``None``; khi câu hỏi rõ là "làm sao để…" (``classify.
classify_task_intent``) mà vẫn không khớp, ``resolve_task_lookup`` trả
``TaskLookup(plan=None)`` để caller (``backend.AssistantEngine.ask``) hiển thị
TRUNG THỰC "chưa có trong hướng dẫn nhanh — mở Cài đặt" kèm nút mở
``systemsettings`` (``OPEN_SETTINGS_FALLBACK``), KHÔNG tự đoán một lệnh khác.

Khớp từ khoá: tái dùng ``fold_accents`` (bỏ dấu + hạ thường) rồi so khớp CHUỖI
CON — cùng khuôn ``app_catalog._best_match`` (từ khoá DÀI NHẤT thắng, ``>``
chặt nên entry khai báo trước thắng khi hoà). Từ khoá catalog đều là cụm >= 3
ký tự sau khi fold nên không gặp bẫy "bí danh quá ngắn" như ``app_catalog``;
vẫn áp cùng ngưỡng ``_SHORT_KEYWORD_MAX_LEN`` để an toàn nếu sau này ai đó
thêm một từ khoá ngắn."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from namios_assistant.engine.classify import TaskIntent, classify_task_intent
from namios_assistant.engine.knowledge_base import fold_accents

__all__ = [
    "TaskActionKind",
    "VALID_TASK_KINDS",
    "TaskPlan",
    "TaskLookup",
    "resolve",
    "resolve_task_lookup",
    "all_tasks",
    "OPEN_SETTINGS_FALLBACK",
]

#: Thư mục chứa catalog — package-relative (cùng cách ``app_catalog._DATA_DIR``),
#: KHÔNG hardcode ``/opt/namios/...`` để module import/test được trong môi
#: trường dev chưa build ảnh.
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_TASK_CATALOG_PATH = _DATA_DIR / "task_catalog.json"

#: Ngưỡng độ dài từ khoá (sau fold) bắt buộc khớp THEO TỪ thay vì chuỗi con tự
#: do — cùng lý do ``app_catalog._SHORT_ALIAS_MAX_LEN``.
_SHORT_KEYWORD_MAX_LEN = 2

TaskActionKind = Literal["settings", "app", "script"]

#: Giá trị ``action.kind`` hợp lệ. Entry khai báo kind lạ bị honesty-check
#: (``tests/test_task_catalog.py``) bắt; ở runtime ``_build_task_plan`` vẫn
#: nạp nguyên văn (không "sửa" dữ liệu thầm lặng) — nhưng catalog đã kiểm
#: duyệt nên trong thực tế luôn hợp lệ.
VALID_TASK_KINDS: frozenset[str] = frozenset({"settings", "app", "script"})


@dataclass(frozen=True)
class TaskPlan:
    """Một tác vụ desktop đã phân giải — CHỈ chứa dữ liệu lấy TRỰC TIẾP từ một
    entry catalog đã kiểm duyệt (KHÔNG tự tổng hợp/suy luận thêm ở runtime).
    UI (``ui.py``) dùng dataclass này để vẽ: tiêu đề + danh sách bước +
    MỘT nút chạy ``action_exec``.

    ``action_exec`` là argv TĨNH (mảng, KHÔNG phải chuỗi shell) — UI chạy bằng
    ``QProcess.startDetached(action_exec[0], list(action_exec[1:]))``, cùng quy
    ước ``RelatedTool.exec_argv`` (không nội suy input người dùng vào đây)."""

    id: str
    title_vi: str
    steps_vi: tuple[str, ...]
    action_label_vi: str
    action_exec: tuple[str, ...]
    action_kind: str


@dataclass(frozen=True)
class TaskLookup:
    """Kết quả MỘT lần thử tra task-catalog cho một câu hỏi người dùng.

    ``plan is None`` nghĩa là: đã phát hiện Ý ĐỊNH "làm sao để…" (``intent``)
    NHƯNG không có tác vụ nào khớp trong catalog đã kiểm duyệt — caller
    (``backend.AssistantEngine.ask``) PHẢI hiển thị thông báo trung thực
    (KHÔNG bịa lệnh khác) + nút mở ``systemsettings`` (``OPEN_SETTINGS_FALLBACK``)."""

    intent: TaskIntent
    plan: TaskPlan | None


# ---------------------------------------------------------------------------
# Nạp catalog — fail-safe tuyệt đối (cùng nguyên tắc
# ``app_catalog._load_json_list``): file vắng/hỏng/sai định dạng -> catalog
# RỖNG, KHÔNG raise. Catalog rỗng chỉ khiến resolver luôn trả ``None`` (trung
# thực: "chưa có tác vụ nào"), KHÔNG làm sập Trợ lý.
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
def _task_catalog() -> tuple[dict[str, Any], ...]:
    return _load_json_list(_TASK_CATALOG_PATH, "tasks")


def all_tasks() -> tuple[dict[str, Any], ...]:
    """Toàn bộ catalog tác vụ NGUYÊN VĂN — dùng cho script kiểm chứng/thống kê
    (vd honesty check ``tests/test_task_catalog.py``), KHÔNG dùng trong luồng
    hỏi-đáp bình thường (luồng đó luôn đi qua ``resolve`` để chỉ lấy ĐÚNG MỘT
    kết quả khớp nhất)."""

    return _task_catalog()


# ---------------------------------------------------------------------------
# Khớp từ khoá — cùng khuôn ``app_catalog._alias_matches``/``_best_match``.
# ---------------------------------------------------------------------------
def _keyword_matches(keyword_folded: str, text_folded: str) -> bool:
    if not keyword_folded:
        return False
    if len(keyword_folded) > _SHORT_KEYWORD_MAX_LEN:
        return keyword_folded in text_folded
    pattern = r"(?<![a-z0-9])" + re.escape(keyword_folded) + r"(?![a-z0-9])"
    return re.search(pattern, text_folded) is not None


def _candidate_keywords(item: dict[str, Any]) -> list[str]:
    keywords = item.get("keywords")
    if not isinstance(keywords, list):
        return []
    return [kw for kw in keywords if isinstance(kw, str)]


def _best_match(query: str, catalog: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    if not query:
        return None
    folded_query = fold_accents(query)

    best: dict[str, Any] | None = None
    best_len = 0
    for item in catalog:
        for keyword in _candidate_keywords(item):
            folded_keyword = fold_accents(keyword)
            # ``>`` chặt: khi hoà độ dài, entry khai báo TRƯỚC giữ nguyên kết
            # quả (cùng quy ước ``app_catalog._best_match``).
            if _keyword_matches(folded_keyword, folded_query) and len(folded_keyword) > best_len:
                best_len = len(folded_keyword)
                best = item
    return best


# ---------------------------------------------------------------------------
# Dựng TaskPlan từ một entry catalog đã resolve.
# ---------------------------------------------------------------------------
def _str_field(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    return value if isinstance(value, str) else ""


def _str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _build_task_plan(item: dict[str, Any]) -> TaskPlan:
    action = item.get("action")
    if not isinstance(action, dict):
        action = {}
    return TaskPlan(
        id=_str_field(item, "id"),
        title_vi=_str_field(item, "title_vi"),
        steps_vi=_str_tuple(item.get("steps_vi")),
        action_label_vi=_str_field(action, "label_vi"),
        action_exec=_str_tuple(action.get("exec")),
        action_kind=_str_field(action, "kind"),
    )


def resolve(query: str) -> TaskPlan | None:
    """Tìm tác vụ khớp nhất trong ``data/task_catalog.json`` theo từ khoá
    (accent-insensitive). Trả ``TaskPlan`` hoặc ``None`` nếu không khớp gì.
    ``None`` là một câu trả lời TRUNG THỰC ("chưa có tác vụ khớp"), KHÔNG phải
    lỗi — xem docstring module cho luồng hiển thị khi đó."""

    item = _best_match(query, _task_catalog())
    if item is None:
        return None
    return _build_task_plan(item)


#: TaskPlan DỰ PHÒNG khi câu hỏi rõ là "làm sao để…" nhưng không khớp tác vụ
#: nào trong catalog — mở Cài đặt hệ thống (``systemsettings``, có thật trên
#: Plasma 6) để người dùng tự tìm. ``exec`` ở đây vẫn TĨNH/đã kiểm duyệt
#: (không sinh từ input người dùng), đúng tinh thần chống bịa.
OPEN_SETTINGS_FALLBACK = TaskPlan(
    id="_open_settings",
    title_vi="Cài đặt hệ thống",
    steps_vi=(
        "Mở Cài đặt hệ thống bằng nút bên dưới.",
        "Dùng ô Tìm kiếm trong Cài đặt để gõ việc bạn muốn làm.",
    ),
    action_label_vi="Mở Cài đặt hệ thống",
    action_exec=("systemsettings",),
    action_kind="settings",
)


# ---------------------------------------------------------------------------
# Điểm vào DUY NHẤT dành cho ``backend.AssistantEngine`` — gộp phân loại Ý
# ĐỊNH (``classify.classify_task_intent``) + tra catalog thành MỘT lời gọi.
# ---------------------------------------------------------------------------
def resolve_task_lookup(text: str) -> TaskLookup | None:
    """Trả ``None`` khi KHÔNG có tín hiệu tác vụ nào — không khớp từ khoá tác
    vụ NÀO và cũng không phải câu "làm sao để…" (``classify_task_intent``):
    caller giữ nguyên luồng KB/online, không đụng tới task-catalog.

    Khớp một tác vụ theo từ khoá -> ``TaskLookup(plan=<TaskPlan>)`` (luôn hiện,
    kể cả khi câu không có cụm how-to — một từ khoá chủ đề khớp đã đủ rõ ràng).
    Rõ là câu "làm sao để…" nhưng không khớp tác vụ nào -> ``TaskLookup(
    plan=None)`` (caller hiện thông báo trung thực + nút mở Cài đặt, xem
    docstring ``TaskLookup``)."""

    plan = resolve(text)
    intent = classify_task_intent(text)
    if plan is None and intent is None:
        return None
    # ``intent`` có thể là ``None`` khi khớp theo từ khoá chủ đề mà không có
    # cụm how-to — vẫn là một tác vụ hợp lệ để hiện; gắn nhãn ``"howto_request"``
    # cho nhất quán (đây đúng là một yêu cầu how-to theo chủ đề).
    return TaskLookup(intent=intent or "howto_request", plan=plan)
