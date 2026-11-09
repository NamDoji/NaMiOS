#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NaMiOS — make-colorscheme.py
Sinh file bộ màu KDE Plasma (Breeze `.colors`) TỪ tokens.json (nguồn sự thật
"Sen Việt"). Mục tiêu: token là NGUỒN DUY NHẤT cho cả preview web lẫn theme KDE,
tránh lệch hai nguồn (xem docs/adr/ADR-0016-design-system-integration.md).

Ánh xạ cốt lõi (yêu cầu A1):
  - Accent/nhấn   = brand.red đỏ son  #C93643 (= kdeglobals AccentColor 201,54,67).
  - ForegroundActive = brand.red-deep đỏ đài #92212E — chữ đỏ đạt WCAG trên nền sáng.
  - Window/View  = nền NGÀ ấm (surface.base/card/subtle) + chữ MỰC (text.primary).
  - Complementary = bộ màu TỐI (color.dark) để widget nền tối lấy đúng màu.

KHÔNG sửa kdeglobals: AccentColor=201,54,67 (đỏ son) vẫn khớp Selection/Decoration
ở đây, nên không phá cấu hình nhấn hiện có.

verified_on_boot: NO — cấu trúc `.colors` theo chuẩn Breeze đã biết; màu hiển thị
đúng chỉ xác nhận được khi boot KDE Plasma thật (boot-screenshot).

Dùng:  python3 branding/design-system/make-colorscheme.py
       (chạy từ gốc repo; tự dò đường nếu chạy nơi khác)
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
TOKENS = os.path.join(HERE, "tokens.json")
OUT = os.path.join(
    REPO,
    "distro", "live-build", "config", "includes.chroot",
    "usr", "share", "color-schemes", "NaMiOS.colors",
)
KDEGLOBALS = os.path.join(
    REPO,
    "distro", "live-build", "config", "includes.chroot",
    "etc", "skel", ".config", "kdeglobals",
)


def hx(h):
    """'#RRGGBB' -> 'R,G,B' (chuỗi KDE)."""
    h = h.lstrip("#")
    return "%d,%d,%d" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def load_palette(tokens, mode):
    """Rút các màu cần dùng từ color.<mode> trong tokens.json thành chuỗi 'R,G,B'."""
    c = tokens["color"][mode]
    p = {
        "base":    hx(c["surface"]["base"]["hex"]),
        "card":    hx(c["surface"]["card"]["hex"]),
        "subtle":  hx(c["surface"]["subtle"]["hex"]),
        "ink":     hx(c["text"]["primary"]["hex"]),
        "ink2":    hx(c["text"]["secondary"]["hex"]),
        "onBrand": hx(c["text"]["on-brand"]["hex"]),
        "red":     hx(c["brand"]["red"]["hex"]),
        "redDeep": hx(c["brand"]["red-deep"]["hex"]),
        "goldSoft": hx(c["brand"].get("gold-soft", c["brand"]["gold"])["hex"]),
        "teal":    hx(c["action"]["primary"]["hex"]),
        "tealHover": hx(c["action"]["primary-hover"]["hex"]),
        "success": hx(c["status"]["success"]["hex"]),
        "warning": hx(c["status"]["warning"]["hex"]),
        "error":   hx(c["status"]["error"]["hex"]),
        "info":    hx(c["status"]["info"]["hex"]),
        "focus":   hx(c["focus"]["ring"]["hex"]),
        "bSubtle": hx(c["border"]["subtle"]["hex"]),
        "bStrong": hx(c["border"]["strong"]["hex"]),
    }
    # ivory-top chỉ có ở light; dark dùng card làm nền tooltip
    if "ivory-top" in c["surface"]:
        p["ivoryTop"] = hx(c["surface"]["ivory-top"]["hex"])
    else:
        p["ivoryTop"] = p["card"]
    return p


def light_fore(L):
    """Khối Foreground/Decoration chung cho các section nền SÁNG."""
    return {
        "ForegroundNormal":   L["ink"],
        "ForegroundInactive": L["ink2"],
        "ForegroundActive":   L["redDeep"],   # đỏ đài — chữ đỏ WCAG an toàn
        "ForegroundLink":     L["teal"],
        "ForegroundVisited":  L["tealHover"],
        "ForegroundNegative": L["error"],
        "ForegroundNeutral":  L["warning"],
        "ForegroundPositive": L["success"],
        "DecorationFocus":    L["red"],        # đỏ son = accent (khớp AccentColor)
        "DecorationHover":    L["red"],
    }


def render(tokens):
    L = load_palette(tokens, "light")
    D = load_palette(tokens, "dark")

    def section(name, pairs):
        out = ["[%s]" % name]
        for k, v in pairs:
            out.append("%s=%s" % (k, v))
        return "\n".join(out)

    lf = light_fore(L)

    header = (
        "# NaMiOS — bộ màu KDE Plasma \"Sen Việt\" v1.0 (nhấn ĐỎ SON #C93643).\n"
        "# FILE NÀY ĐƯỢC SINH TỰ ĐỘNG từ branding/design-system/tokens.json bằng\n"
        "# branding/design-system/make-colorscheme.py — ĐỪNG sửa tay; sửa token rồi chạy lại.\n"
        "# Nền NGÀ ấm (surface.base/card/subtle) + chữ MỰC (#182E3B). Nhấn đỏ son\n"
        "# #C93643 (= kdeglobals AccentColor 201,54,67 — KHÔNG đổi). ForegroundActive\n"
        "# dùng đỏ đài #92212E (146,33,46) vì đỏ son chỉ ~4.3:1 trên nền trắng — đỏ\n"
        "# đài đậm hơn, đọc được chữ trên nền sáng (WCAG AA). Complementary = bộ TỐI.\n"
        "#\n"
        "# verified_on_boot: NO — cấu trúc .colors theo chuẩn Breeze đã biết; màu sắc\n"
        "# hiển thị đúng chỉ xác nhận được khi boot KDE Plasma thật (boot-screenshot).\n"
    )

    blocks = [header]

    # Giữ nguyên hiệu ứng như bản Breeze trước (không phá hành vi disabled/inactive)
    blocks.append(section("ColorEffects:Disabled", [
        ("Color", "56,56,56"), ("ColorAmount", "0"), ("ColorEffect", "0"),
        ("ContrastAmount", "0.65"), ("ContrastEffect", "1"),
        ("IntensityAmount", "0.1"), ("IntensityEffect", "2"),
    ]))
    blocks.append(section("ColorEffects:Inactive", [
        ("ChangeSelectionColor", "true"), ("Color", "112,111,110"),
        ("ColorAmount", "0.025"), ("ColorEffect", "2"), ("ContrastAmount", "0.1"),
        ("ContrastEffect", "2"), ("Enable", "false"), ("IntensityAmount", "0"),
        ("IntensityEffect", "0"),
    ]))

    # Nhóm nền SÁNG: Button / Tooltip / View / Window / Header
    def light_block(bg_normal, bg_alt):
        return ([("BackgroundAlternate", bg_alt), ("BackgroundNormal", bg_normal)]
                + sorted(lf.items()))

    blocks.append(section("Colors:Button", light_block(L["card"], L["subtle"])))

    # Selection: nền đỏ son, chữ trắng
    blocks.append(section("Colors:Selection", [
        ("BackgroundAlternate", L["redDeep"]),
        ("BackgroundNormal", L["red"]),
        ("DecorationFocus", L["red"]),
        ("DecorationHover", L["red"]),
        ("ForegroundActive", L["onBrand"]),
        ("ForegroundInactive", "235,218,224"),
        ("ForegroundLink", L["goldSoft"]),
        ("ForegroundNegative", "255,221,221"),
        ("ForegroundNeutral", "255,236,207"),
        ("ForegroundNormal", L["onBrand"]),
        ("ForegroundPositive", "213,242,224"),
        ("ForegroundVisited", "235,218,224"),
    ]))

    blocks.append(section("Colors:Tooltip", light_block(L["ivoryTop"], L["subtle"])))
    blocks.append(section("Colors:View", light_block(L["card"], L["subtle"])))
    blocks.append(section("Colors:Window", light_block(L["base"], L["subtle"])))

    # Complementary = bộ TỐI (color.dark): nền mực đêm, chữ ngà
    blocks.append(section("Colors:Complementary", [
        ("BackgroundAlternate", D["subtle"]),
        ("BackgroundNormal", D["base"]),
        ("DecorationFocus", D["red"]),   # đỏ nền tối (≥3:1), không dùng đỏ son
        ("DecorationHover", D["red"]),
        ("ForegroundActive", D["red"]),
        ("ForegroundInactive", D["ink2"]),
        ("ForegroundLink", D["teal"]),
        ("ForegroundNegative", D["error"]),
        ("ForegroundNeutral", D["warning"]),
        ("ForegroundNormal", D["ink"]),
        ("ForegroundPositive", D["success"]),
        ("ForegroundVisited", D["goldSoft"]),
    ]))

    blocks.append(section("Colors:Header", light_block(L["base"], L["subtle"])))

    blocks.append(section("General", [
        ("ColorScheme", "NaMiOS"), ("Name", "NaMiOS"),
        ("accentActiveTitlebar", "false"), ("shadeSortColumn", "true"),
    ]))
    blocks.append(section("KDE", [("contrast", "4")]))

    # WM: thanh tiêu đề mực đêm + chữ ngà (on-brand nhưng accentActiveTitlebar=false)
    blocks.append(section("WM", [
        ("activeBackground", L["ink"]),
        ("activeBlend", "255,255,255"),
        ("activeForeground", D["ink"]),   # ngà (#F8F5EE)
        ("inactiveBackground", L["base"]),
        ("inactiveBlend", L["ink2"]),
        ("inactiveForeground", L["ink2"]),
    ]))

    return "\n\n".join(blocks) + "\n", L, D


def check_accent_unchanged(L):
    """Trung thực: khẳng định accent đỏ son khớp kdeglobals AccentColor (không phá)."""
    expected = "201,54,67"
    ok = (L["red"] == expected)
    note = []
    if os.path.exists(KDEGLOBALS):
        with open(KDEGLOBALS, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("AccentColor="):
                    val = line.strip().split("=", 1)[1]
                    note.append("kdeglobals AccentColor=%s" % val)
                    ok = ok and (val == expected)
    return ok, note


def main():
    if not os.path.exists(TOKENS):
        print("LỖI: không thấy tokens.json tại %s" % TOKENS, file=sys.stderr)
        return 2
    with open(TOKENS, encoding="utf-8") as f:
        tokens = json.load(f)

    content, L, D = render(tokens)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)

    ok, note = check_accent_unchanged(L)
    print("Đã ghi: %s" % OUT)
    print("  accent (brand.red light)   = %s  (đỏ son #C93643)" % L["red"])
    print("  ForegroundActive (red-deep)= %s  (đỏ đài #92212E)" % L["redDeep"])
    print("  Window nền ngà base        = %s" % L["base"])
    print("  View nền card              = %s" % L["card"])
    print("  Complementary nền tối base = %s" % D["base"])
    for n in note:
        print("  " + n)
    print("  accent khớp AccentColor, KHÔNG sửa kdeglobals: %s" % ("OK" if ok else "LỆCH — KIỂM LẠI"))
    print("  verified_on_boot: NO — cần boot KDE Plasma thật để xác nhận hiển thị.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
