#!/usr/bin/env python3
"""Script kiểm chứng ĐỘC LẬP cho Task Concierge (``engine/task_catalog.py``)
— KHÔNG phụ thuộc pytest (chạy bằng ``python3`` thuần), cùng quy ước
``tests/test_app_catalog.py`` (script xác nhận thủ công cho dev/lead đọc
trước khi build ảnh).

Chạy (cùng quy ước PYTHONPATH của wrapper ``/usr/bin/namios-assistant``):

    PYTHONPATH=/opt/namios python3 /opt/namios/namios_assistant/tests/test_task_catalog.py

Bốn việc script này xác nhận:

1. **Hành vi resolver** đúng như yêu cầu "nAssistant actionable" (các ca cụ
   thể: "thay đổi giao diện màn hình" -> giao diện; "đổi độ phân giải" ->
   màn hình; "kết nối wifi" -> mạng; "doi mat khau" không dấu -> người dùng;
   câu vô nghĩa -> ``None``).
2. **Chống bịa (honesty check)**: MỌI entry trong ``task_catalog.json`` có
   ``action.exec`` là argv array KHÔNG rỗng, ``action.kind`` hợp lệ
   (``settings``/``app``/``script``), và các field bắt buộc (id/title_vi/
   keywords/steps_vi) không rỗng — KHÔNG có đường nào để một lệnh chạy được
   lọt ra ngoài catalog đã kiểm duyệt. ``resolve`` CHỈ trả lại đúng
   ``action.exec`` nguyên văn của entry khớp (không ghép/suy luận thêm).
3. **Ý định how-to + dự phòng**: ``resolve_task_lookup`` trả ``None`` cho câu
   không-phải-tác-vụ; ``TaskLookup(plan=None)`` cho câu rõ "làm sao để…" mà
   không khớp tác vụ nào; ``OPEN_SETTINGS_FALLBACK`` dùng khi đó hợp lệ
   (exec ``systemsettings`` không rỗng, kind hợp lệ).
4. **``classify_task_intent``** bắt cụm how-to ("làm sao"/"tôi muốn") và KHÔNG
   bắt câu báo lỗi thuần.

Thoát mã 0 nếu mọi kiểm tra PASS, mã 1 nếu có bất kỳ FAIL nào."""

from __future__ import annotations

import sys

from namios_assistant.engine.classify import classify_task_intent
from namios_assistant.engine.task_catalog import (
    OPEN_SETTINGS_FALLBACK,
    VALID_TASK_KINDS,
    TaskPlan,
    all_tasks,
    resolve,
    resolve_task_lookup,
)

_FAILURES: list[str] = []


def _check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail and not condition else ""
    print(f"[{status}] {label}{suffix}")
    if not condition:
        _FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) Hành vi resolver — đúng các ca nêu trong yêu cầu.
# ---------------------------------------------------------------------------
def _test_resolver_cases() -> None:
    print("\n== Resolver behavior ==")

    plan = resolve("tôi muốn thay đổi giao diện màn hình")
    _check(
        'resolve("...thay đổi giao diện màn hình") -> appearance (kcm_lookandfeel)',
        plan is not None
        and plan.id == "appearance"
        and plan.action_exec == ("/usr/local/bin/namios-open-setting", "kcm_lookandfeel"),
        detail=repr(plan),
    )

    plan = resolve("đổi độ phân giải")
    _check(
        'resolve("đổi độ phân giải") -> resolution (kcm_kscreen)',
        plan is not None
        and plan.id == "resolution"
        and plan.action_exec == ("/usr/local/bin/namios-open-setting", "kcm_kscreen"),
        detail=repr(plan),
    )

    plan = resolve("kết nối wifi")
    _check(
        'resolve("kết nối wifi") -> network (nConnect helper)',
        plan is not None
        and plan.id == "network"
        and plan.action_exec == ("/usr/local/bin/namios-ket-noi-thiet-bi",),
        detail=repr(plan),
    )

    plan = resolve("doi mat khau")
    _check(
        'resolve("doi mat khau") [no diacritics] -> users (kcm_users)',
        plan is not None
        and plan.id == "users"
        and plan.action_exec == ("/usr/local/bin/namios-open-setting", "kcm_users"),
        detail=repr(plan),
    )

    plan = resolve("them may in")
    _check(
        'resolve("them may in") [no diacritics] -> printer (nConnect may-in)',
        plan is not None
        and plan.id == "printer"
        and plan.action_exec == ("/usr/local/bin/namios-ket-noi-thiet-bi", "may-in"),
        detail=repr(plan),
    )

    plan = resolve("đổi hình nền")
    _check(
        'resolve("đổi hình nền") -> wallpaper',
        plan is not None and plan.id == "wallpaper",
        detail=repr(plan),
    )

    plan = resolve("xyzzy qwerty không liên quan gì cả")
    _check(
        'resolve("xyzzy qwerty …") -> None (honest, no fabricated action)',
        plan is None,
        detail=repr(plan),
    )

    plan = resolve("")
    _check('resolve("") -> None', plan is None, detail=repr(plan))


# ---------------------------------------------------------------------------
# 2) Honesty / anti-fabrication — MỌI action.exec là argv array KHÔNG rỗng,
#    kind hợp lệ, field bắt buộc không rỗng. Và ``resolve`` trả lại ĐÚNG
#    exec nguyên văn của entry (không chế thêm).
# ---------------------------------------------------------------------------
def _test_catalog_honesty() -> None:
    print("\n== Honesty check (every action is a non-empty argv from the catalog) ==")
    tasks = all_tasks()
    _check("task_catalog.json loaded with entries", len(tasks) > 0, detail=str(len(tasks)))

    seen_ids: set[str] = set()
    for entry in tasks:
        task_id = entry.get("id")
        label = f"task[{task_id}]"

        _check(f"{label}: has non-empty id", bool(task_id), detail=repr(task_id))
        _check(
            f"{label}: id is unique",
            task_id not in seen_ids,
            detail=f"duplicate {task_id!r}",
        )
        if isinstance(task_id, str):
            seen_ids.add(task_id)

        _check(
            f"{label}: has non-empty title_vi",
            isinstance(entry.get("title_vi"), str) and bool(entry.get("title_vi")),
            detail=repr(entry.get("title_vi")),
        )

        keywords = entry.get("keywords")
        _check(
            f"{label}: has non-empty keywords list (all str)",
            isinstance(keywords, list)
            and len(keywords) > 0
            and all(isinstance(kw, str) and kw.strip() for kw in keywords),
            detail=repr(keywords),
        )

        steps = entry.get("steps_vi")
        _check(
            f"{label}: has non-empty steps_vi list (all str)",
            isinstance(steps, list)
            and len(steps) > 0
            and all(isinstance(s, str) and s.strip() for s in steps),
            detail=repr(steps),
        )

        action = entry.get("action")
        _check(f"{label}: has an 'action' object", isinstance(action, dict), detail=repr(action))
        if not isinstance(action, dict):
            continue

        exec_argv = action.get("exec")
        _check(
            f"{label}: action.exec is a NON-EMPTY argv list (all non-empty str)",
            isinstance(exec_argv, list)
            and len(exec_argv) > 0
            and all(isinstance(arg, str) and arg.strip() for arg in exec_argv),
            detail=repr(exec_argv),
        )

        _check(
            f"{label}: action.kind is valid ({sorted(VALID_TASK_KINDS)})",
            action.get("kind") in VALID_TASK_KINDS,
            detail=repr(action.get("kind")),
        )

        _check(
            f"{label}: action.label_vi is non-empty",
            isinstance(action.get("label_vi"), str) and bool(action.get("label_vi")),
            detail=repr(action.get("label_vi")),
        )

        # ``resolve`` trên chính từ khoá đầu của entry PHẢI khớp lại entry này
        # (hoặc một entry có từ khoá DÀI HƠN chứa nó) và trả ĐÚNG exec của
        # entry được chọn — xác nhận không có đường "chế" exic khác entry.
        if isinstance(keywords, list) and keywords:
            resolved = resolve(str(keywords[0]))
            _check(
                f"{label}: resolve(first keyword) returns a TaskPlan whose exec is from the catalog",
                isinstance(resolved, TaskPlan)
                and list(resolved.action_exec)
                == (
                    exec_argv
                    if resolved.id == task_id
                    else _exec_of(resolved.id)
                ),
                detail=f"kw={keywords[0]!r} -> {resolved!r}",
            )


def _exec_of(task_id: str | None) -> list[str]:
    for entry in all_tasks():
        if entry.get("id") == task_id:
            action = entry.get("action") or {}
            return list(action.get("exec") or [])
    return []


# ---------------------------------------------------------------------------
# 3) Ý định how-to + dự phòng OPEN_SETTINGS_FALLBACK.
# ---------------------------------------------------------------------------
def _test_task_lookup_and_fallback() -> None:
    print("\n== resolve_task_lookup intent gating + fallback ==")

    lookup = resolve_task_lookup("làm sao để thay đổi giao diện")
    _check(
        'resolve_task_lookup("làm sao… giao diện") -> matched TaskPlan',
        lookup is not None and lookup.plan is not None and lookup.plan.id == "appearance",
        detail=repr(lookup),
    )

    lookup = resolve_task_lookup("làm sao để máy tính bay lên mặt trăng")
    _check(
        'resolve_task_lookup(how-to with NO matching task) -> TaskLookup(plan=None)',
        lookup is not None and lookup.plan is None,
        detail=repr(lookup),
    )

    lookup = resolve_task_lookup("máy tôi bị màn hình đen khi khởi động")
    _check(
        'resolve_task_lookup(pure error, no how-to) -> None (normal KB/AI flow)',
        lookup is None,
        detail=repr(lookup),
    )

    # Khớp theo từ khoá chủ đề dù KHÔNG có cụm how-to -> vẫn hiện tác vụ.
    lookup = resolve_task_lookup("kết nối wifi")
    _check(
        'resolve_task_lookup("kết nối wifi") [no how-to phrase] -> matched network task',
        lookup is not None and lookup.plan is not None and lookup.plan.id == "network",
        detail=repr(lookup),
    )

    _check(
        "OPEN_SETTINGS_FALLBACK: exec is a non-empty argv (systemsettings)",
        bool(OPEN_SETTINGS_FALLBACK.action_exec)
        and OPEN_SETTINGS_FALLBACK.action_exec[0] == "systemsettings",
        detail=repr(OPEN_SETTINGS_FALLBACK.action_exec),
    )
    _check(
        "OPEN_SETTINGS_FALLBACK: kind is valid",
        OPEN_SETTINGS_FALLBACK.action_kind in VALID_TASK_KINDS,
        detail=repr(OPEN_SETTINGS_FALLBACK.action_kind),
    )


# ---------------------------------------------------------------------------
# 4) ``classify_task_intent`` — bắt how-to, KHÔNG bắt báo lỗi thuần.
# ---------------------------------------------------------------------------
def _test_task_intent() -> None:
    print("\n== classify_task_intent ==")

    for text in ("làm sao để đổi hình nền", "tôi muốn thay đổi giao diện", "hướng dẫn kết nối bluetooth"):
        _check(
            f"classify_task_intent({text!r}) == 'howto_request'",
            classify_task_intent(text) == "howto_request",
            detail=repr(classify_task_intent(text)),
        )

    for text in ("wifi bị lỗi không vào được mạng", "máy in kẹt giấy", ""):
        _check(
            f"classify_task_intent({text!r}) is None (not a how-to)",
            classify_task_intent(text) is None,
            detail=repr(classify_task_intent(text)),
        )


def main() -> int:
    _test_resolver_cases()
    _test_catalog_honesty()
    _test_task_lookup_and_fallback()
    _test_task_intent()

    print("\n== Summary ==")
    if _FAILURES:
        print(f"FAIL — {len(_FAILURES)} check(s) failed:")
        for failure in _FAILURES:
            print(f"  - {failure}")
        return 1

    print(f"PASS — all checks passed ({len(all_tasks())} tasks in the curated catalog).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
