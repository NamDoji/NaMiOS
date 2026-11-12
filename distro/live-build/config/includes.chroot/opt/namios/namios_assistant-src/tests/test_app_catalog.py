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

Bốn việc script này xác nhận:

1. **Hành vi resolver** đúng như yêu cầu "App & Driver Concierge" (6 ca cụ
   thể trong yêu cầu gốc, xem ``_test_resolver_cases``) + các ca "Dev
   Pack"/dev tools thêm 12/11/2026 (xem ``_test_dev_pack_resolver_cases``).
2. **Honesty check**: KHÔNG entry nào trong hai catalog vi phạm quy tắc
   chống bịa URL — mọi ``method`` cần URL (``deb_official``/``web``/
   ``vendor``) PHẢI có ``source`` bắt đầu ``https://`` VÀ domain của
   ``source`` kết thúc đúng bằng ``verify_domain``; mọi ``method`` cài gói
   (``apt``/``flatpak``) PHẢI có ``source`` khác rỗng; mọi app
   ``method=="none"`` PHẢI có ``source`` rỗng VÀ ``alt_vi`` khác rỗng (không
   được vừa "không có" vừa không gợi ý thay thế gì); mọi entry
   ``method=="wine"`` PHẢI có ``source`` rỗng (không có link nào để chạy
   trực tiếp, chỉ gợi ý nRun); mọi entry ``method=="pack"`` PHẢI có
   ``source`` rỗng VÀ ``members`` là danh sách KHÔNG rỗng, MỌI id trong đó
   PHẢI khớp đúng một entry khác có thật trong ``apps`` (thêm 12/11/2026,
   "Dev Pack").
3. **Vendor .deb auto-install — rào domain-pin** (thêm 12/11/2026): xác nhận
   ``installer.is_official_https_url`` (hàm THUẦN, không mạng) CHẤP NHẬN
   đúng domain/subdomain https://, và TỪ CHỐI scheme ``http://``, domain
   không khớp, VÀ domain "giả nhái" kiểu đuôi trùng ký tự (vd
   ``notzoom.us`` kết thúc đúng bằng chuỗi ``zoom.us`` dù không liên quan).
4. **build_install_plan_for_app** map đúng ``method`` -> ``action_kind``
   mới (``deb_official`` -> ``deb_install``, ``pack`` -> ``pack_install`` +
   ``members`` đã resolve đủ) — xem ``_test_install_plan_action_kinds``.

Thoát mã 0 nếu mọi kiểm tra PASS, mã 1 nếu có bất kỳ FAIL nào (để CI/script
gọi ngoài phát hiện được qua exit code, không chỉ qua đọc text in ra)."""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from namios_assistant.engine.app_catalog import (
    all_apps,
    all_drivers,
    build_install_plan_for_app,
    resolve_app,
    resolve_driver,
)
from namios_assistant.engine.installer import is_official_https_url

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
# 1b) Dev tools + "Bộ công cụ Lập trình" (Dev Pack) — thêm 12/11/2026.
# ---------------------------------------------------------------------------
def _test_dev_pack_resolver_cases() -> None:
    print("\n== Dev tools + Dev Pack resolver behavior ==")

    app = resolve_app("cài docker")
    _check(
        'resolve_app("cài docker") -> docker (apt, docker.io)',
        app is not None
        and app.get("id") == "docker"
        and app.get("method") == "apt"
        and app.get("source") == "docker.io",
        detail=repr(app),
    )

    app = resolve_app("cài giúp tôi nodejs")
    _check(
        'resolve_app("cài giúp tôi nodejs") -> nodejs (apt, nodejs)',
        app is not None
        and app.get("id") == "nodejs"
        and app.get("method") == "apt"
        and app.get("source") == "nodejs",
        detail=repr(app),
    )

    app = resolve_app("cài dbeaver")
    _check(
        'resolve_app("cài dbeaver") -> dbeaver (flatpak, io.dbeaver.DBeaverCommunity)',
        app is not None
        and app.get("id") == "dbeaver"
        and app.get("method") == "flatpak"
        and app.get("source") == "io.dbeaver.DBeaverCommunity",
        detail=repr(app),
    )

    for query in (
        "bộ công cụ lập trình",
        "dev pack",
        "cài đồ nghề lập trình",
        "công cụ cho dev",
    ):
        app = resolve_app(query)
        _check(
            f'resolve_app({query!r}) -> devpack (pack)',
            app is not None and app.get("id") == "devpack" and app.get("method") == "pack",
            detail=repr(app),
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
    elif method == "pack":
        # "Dev Pack" (thêm 12/11/2026): KHÔNG source đơn lẻ (KHÔNG có một
        # link/gói để tự bịa) — chỉ 'members' = danh sách id, MỖI id PHẢI
        # khớp đúng một entry khác có thật trong CHÍNH mảng 'apps' (so khớp
        # theo id nguyên văn, không qua bí danh/fuzzy — xem
        # ``engine/app_catalog.py::_build_pack_members``).
        _check(f"{label}: method=pack has EMPTY source (no fabricated link)", source == "", detail=source)
        members = entry.get("members")
        _check(
            f"{label}: method=pack has non-empty 'members' list",
            isinstance(members, list) and len(members) > 0,
            detail=str(members),
        )
        if isinstance(members, list):
            all_ids = {app.get("id") for app in all_apps()}
            for member_id in members:
                _check(
                    f"{label}: pack member id '{member_id}' exists in software_catalog.json",
                    member_id in all_ids,
                    detail=str(member_id),
                )
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


# ---------------------------------------------------------------------------
# 3) Vendor .deb auto-install — rào domain-pin (``is_official_https_url``,
#    HÀM THUẦN, không mạng/không IO) PHẢI từ chối scheme sai, domain sai, VÀ
#    domain "giả nhái" kiểu đuôi trùng ký tự — xem docstring hàm đó trong
#    ``engine/installer.py`` cho lý do dùng ``hostname == domain or
#    hostname.endswith("." + domain)`` thay vì so khớp chuỗi con ngây thơ.
# ---------------------------------------------------------------------------
def _test_deb_install_guard() -> None:
    print("\n== Vendor .deb auto-install — domain-pin guard (no network) ==")

    _check(
        "is_official_https_url: accepts exact https domain match",
        is_official_https_url("https://zoom.us/client/latest/zoom_amd64.deb", "zoom.us") is True,
    )
    _check(
        "is_official_https_url: accepts a real subdomain of verify_domain",
        is_official_https_url(
            "https://code.visualstudio.com/docs/setup/linux", "visualstudio.com"
        )
        is True,
    )
    _check(
        "is_official_https_url: REJECTS http:// (not https)",
        is_official_https_url("http://zoom.us/client/latest/zoom_amd64.deb", "zoom.us") is False,
    )
    _check(
        "is_official_https_url: REJECTS a completely different domain",
        is_official_https_url("https://evil-mirror.example/zoom_amd64.deb", "zoom.us") is False,
    )
    _check(
        "is_official_https_url: REJECTS domain-confusion suffix (notzoom.us != zoom.us)",
        is_official_https_url("https://notzoom.us/zoom_amd64.deb", "zoom.us") is False,
    )
    _check(
        "is_official_https_url: REJECTS lookalike domain (zoom.us.evil.com)",
        is_official_https_url("https://zoom.us.evil.com/zoom_amd64.deb", "zoom.us") is False,
    )
    _check(
        "is_official_https_url: REJECTS empty verify_domain (no pin = no trust)",
        is_official_https_url("https://zoom.us/client/latest/zoom_amd64.deb", "") is False,
    )
    _check(
        "is_official_https_url: REJECTS empty url",
        is_official_https_url("", "zoom.us") is False,
    )


# ---------------------------------------------------------------------------
# 4) ``build_install_plan_for_app`` — ``method`` -> ``action_kind`` mới
#    (deb_official -> deb_install, pack -> pack_install + members resolved).
# ---------------------------------------------------------------------------
def _test_install_plan_action_kinds() -> None:
    print("\n== InstallPlan action_kind mapping (deb_install / pack_install) ==")

    zoom = resolve_app("zoom")
    _check("resolve_app('zoom') found (precondition)", zoom is not None, detail=repr(zoom))
    if zoom is not None:
        plan = build_install_plan_for_app(zoom)
        _check(
            "build_install_plan_for_app(zoom): action_kind == 'deb_install'",
            plan.action_kind == "deb_install",
            detail=repr(plan),
        )
        _check(
            "build_install_plan_for_app(zoom): action_payload keeps the vendor URL",
            plan.action_payload == zoom.get("source"),
            detail=repr(plan),
        )

    devpack = resolve_app("dev pack")
    _check("resolve_app('dev pack') found (precondition)", devpack is not None, detail=repr(devpack))
    if devpack is not None:
        plan = build_install_plan_for_app(devpack)
        _check(
            "build_install_plan_for_app(devpack): action_kind == 'pack_install'",
            plan.action_kind == "pack_install",
            detail=repr(plan),
        )
        expected_members = devpack.get("members") or []
        _check(
            "build_install_plan_for_app(devpack): members resolved for every declared id",
            len(plan.members) == len(expected_members),
            detail=f"expected={expected_members!r} got={[m.title for m in plan.members]!r}",
        )
        _check(
            "build_install_plan_for_app(devpack): every member has its OWN real action_kind",
            all(member.action_kind != "none" for member in plan.members),
            detail=repr([(m.title, m.action_kind) for m in plan.members]),
        )


def main() -> int:
    _test_resolver_cases()
    _test_dev_pack_resolver_cases()
    _test_honesty_check()
    _test_deb_install_guard()
    _test_install_plan_action_kinds()

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
