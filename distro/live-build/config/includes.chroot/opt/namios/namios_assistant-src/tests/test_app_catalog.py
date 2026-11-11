#!/usr/bin/env python3
"""Script kiểm chứng ĐỘC LẬP cho App & Driver Concierge (``engine/app_catalog.py``)
— KHÔNG phụ thuộc pytest (chạy được bằng ``python3`` thuần), vì đây là một
script xác nhận thủ công cho dev/lead đọc trước khi build ảnh, không phải một
phần của bộ test tự động của repo (CI chỉ lint ``src/``, xem docstring
module/README của wave này).

Chạy (từ thư mục chứa gói ``namios_assistant`` thật hoặc symlink tới
``namios_assistant-src``, cùng quy ước PYTHONPATH="/opt/namios" của wrapper
``/usr/bin/namios-assistant``):

    PYTHONPATH=/opt/namios python3 /opt/namios/namios_assistant/tests/test_app_catalog.py

Hai việc script này xác nhận:

1. **Hành vi resolver** đúng như yêu cầu "App & Driver Concierge" (6 ca cụ
   thể trong yêu cầu, xem ``_RESOLVER_CASES``).
2. **Honesty check**: KHÔNG entry nào trong hai catalog vi phạm quy tắc
   chống bịa URL — mọi ``method`` cần URL (``deb_official``/``web``/
   ``vendor``) PHẢI có ``source`` bắt đầu ``https://`` VÀ domain của
   ``source`` kết thúc đúng bằng ``verify_domain``; mọi ``method`` cài gói
   (``apt``/``flatpak``) PHẢI có ``source`` khác rỗng; mọi app
   ``method=="none"`` PHẢI có ``source`` rỗng VÀ ``alt_vi`` khác rỗng (không
   được vừa "không có" vừa không gợi ý thay thế gì); mọi entry
   ``method=="wine"`` PHẢI có ``source`` rỗng (không có link nào để chạy
   trực tiếp, chỉ gợi ý nRun).

Thoát mã 0 nếu mọi kiểm tra PASS, mã 1 nếu có bất kỳ FAIL nào (để CI/script
gọi ngoài phát hiện được qua exit code, không chỉ qua đọc text in ra)."""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from namios_assistant.engine.app_catalog import (
    all_apps,
    all_drivers,
    resolve_app,
    resolve_driver,
)

_FAILURES: list[str] = []


def _check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail and not condition else ""
    print(f"[{status}] {label}{suffix}")
    if not condition:
        _FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) Hành vi resolver — đúng 6 ca nêu trong yêu cầu "App & Driver Concierge".
# ---------------------------------------------------------------------------
def _test_resolver_cases() -> None:
    print("\n== Resolver behavior ==")

    app = resolve_app("cài giúp tôi zoom")
    _check(
        'resolve_app("cài giúp tôi zoom") -> zoom (deb_official, zoom.us)',
        app is not None
        and app.get("id") == "zoom"
        and app.get("method") == "deb_official"
        and app.get("verify_domain") == "zoom.us",
        detail=repr(app),
    )

    app = resolve_app("zalo")
    _check(
        'resolve_app("zalo") -> web',
        app is not None and app.get("id") == "zalo" and app.get("method") == "web",
        detail=repr(app),
    )

    app = resolve_app("photoshop")
    _check(
        'resolve_app("photoshop") -> none + alt GIMP',
        app is not None
        and app.get("id") == "adobe-photoshop"
        and app.get("method") == "none"
        and "GIMP" in (app.get("alt_vi") or ""),
        detail=repr(app),
    )

    app = resolve_app("cài telegram")
    _check(
        'resolve_app("cài telegram") -> apt telegram-desktop',
        app is not None
        and app.get("id") == "telegram"
        and app.get("method") == "apt"
        and app.get("source") == "telegram-desktop",
        detail=repr(app),
    )

    driver = resolve_driver("canon g2010")
    _check(
        'resolve_driver("canon g2010") -> Canon G-series (vendor)',
        driver is not None
        and driver.get("brand") == "Canon G-series"
        and driver.get("method") == "vendor",
        detail=repr(driver),
    )

    driver = resolve_driver("máy in hp")
    _check(
        'resolve_driver("máy in hp") -> hplip',
        driver is not None and driver.get("brand") == "HP" and driver.get("source") == "hplip",
        detail=repr(driver),
    )

    app = resolve_app("phần mềm không tồn tại xyz")
    _check(
        'resolve_app("phần mềm không tồn tại xyz") -> None (honest)',
        app is None,
        detail=repr(app),
    )

    # Ca bổ sung từ câu chuyện người dùng trong yêu cầu gốc ("máy in Canon
    # G2010 không nhận driver") — xác nhận cả cụm đầy đủ vẫn resolve đúng,
    # không chỉ cụm rút gọn "canon g2010".
    driver = resolve_driver("máy in Canon G2010 không nhận driver")
    _check(
        'resolve_driver("máy in Canon G2010 không nhận driver") -> Canon G-series',
        driver is not None and driver.get("brand") == "Canon G-series",
        detail=repr(driver),
    )


# ---------------------------------------------------------------------------
# 2) Honesty check — KHÔNG entry nào trong catalog được phép bịa URL/thiếu
#    gói/thiếu alternative.
# ---------------------------------------------------------------------------
def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


def _check_entry_honesty(label: str, entry: dict) -> None:
    method = entry.get("method")
    source = entry.get("source") or ""
    verify_domain = (entry.get("verify_domain") or "").lower()

    if method in ("deb_official", "web", "vendor"):
        _check(
            f"{label}: method={method} source starts with https://",
            source.startswith("https://"),
            detail=source,
        )
        domain = _domain_of(source)
        _check(
            f"{label}: method={method} domain '{domain}' ends with verify_domain '{verify_domain}'",
            bool(verify_domain) and domain.endswith(verify_domain),
            detail=f"domain={domain!r} verify_domain={verify_domain!r}",
        )
    elif method in ("apt", "flatpak"):
        _check(f"{label}: method={method} has non-empty source", bool(source.strip()), detail=source)
    elif method == "none":
        _check(f"{label}: method=none has EMPTY source (no fabricated link)", source == "", detail=source)
        alt_vi = entry.get("alt_vi") or ""
        _check(f"{label}: method=none has non-empty alt_vi", bool(alt_vi.strip()), detail=alt_vi)
    elif method == "wine":
        _check(f"{label}: method=wine has EMPTY source (no runnable link)", source == "", detail=source)
    else:
        _check(f"{label}: method '{method}' is a KNOWN value", False, detail=str(method))


def _test_honesty_check() -> None:
    print("\n== Honesty check (zero fabricated-URL entries) ==")
    apps = all_apps()
    drivers = all_drivers()
    _check("software_catalog.json loaded with entries", len(apps) > 0, detail=str(len(apps)))
    _check("driver_catalog.json loaded with entries", len(drivers) > 0, detail=str(len(drivers)))

    for app in apps:
        _check_entry_honesty(f"app[{app.get('id')}]", app)
    for driver in drivers:
        _check_entry_honesty(f"driver[{driver.get('brand')}]", driver)


def main() -> int:
    _test_resolver_cases()
    _test_honesty_check()

    print("\n== Summary ==")
    if _FAILURES:
        print(f"FAIL — {len(_FAILURES)} check(s) failed:")
        for failure in _FAILURES:
            print(f"  - {failure}")
        return 1

    print("PASS — all checks passed, zero fabricated-URL entries found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
