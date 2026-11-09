#!/usr/bin/env python3
"""NaMiOS — sinh icon ứng dụng "sen đỏ trên Ô NỀN NGÀ sáng" (squircle bo góc),
thay cho icon v2 gốc đặt sen trên nền MỰC ĐÊM.

QUYẾT ĐỊNH (Cuong 09/11/2026): "Hoa sen KHÔNG BAO GIỜ đặt trên nền ĐEN — đó là
điều kiêng kỵ." Áp cho MỌI nơi có hoa sen, gồm cả ô icon launcher. Vì vậy ô
nền icon đổi từ mực đêm -> ngà ấm (đồng bộ wallpaper/SDDM/Plymouth).

Dựng master 1024 (ô squircle ngà + sen đỏ v2 ở giữa) từ biểu tượng trong suốt
branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png (KHÔNG rasterize SVG;
build không có cairosvg/rsvg), rồi resize xuống mọi cỡ icon đang có + ghi logo
trình cài Calamares.

Tái lập: python3 branding/icons/make-app-icon-light.py
"""
from __future__ import annotations

import os
import re
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYMBOL = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png")
MASTER = os.path.join(ROOT, "branding/icons/NaMiOS_App_Icon_Light_1024.png")
ICONS_ROOT = os.path.join(ROOT, "distro/live-build/config/includes.chroot/usr/share/icons")
CALAMARES_LOGO = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/etc/calamares/branding/namios/logo.png",
)
THEMES = ["NaMiOS-Lotus", "hicolor"]
FILENAMES = ["namios.png", "start-here-namios.png"]
SIZE_RE = re.compile(r"^(\d+)x\1$")

S = 1024
RADIUS = round(0.2235 * S)        # squircle ~ kiểu iOS
IVORY_TOP = (0xFD, 0xFB, 0xF6)
IVORY_BOT = (0xF1, 0xE6, 0xD4)
BORDER = (0xE4, 0xD7, 0xC2)       # viền ngà ấm nhạt để tách icon khỏi nền sáng


def _build_master() -> Image.Image:
    # Nền gradient ngà dọc.
    grad = Image.new("RGB", (S, S))
    px = grad.load()
    for y in range(S):
        t = y / (S - 1)
        px_row = (
            int(IVORY_TOP[0] + (IVORY_BOT[0] - IVORY_TOP[0]) * t),
            int(IVORY_TOP[1] + (IVORY_BOT[1] - IVORY_TOP[1]) * t),
            int(IVORY_TOP[2] + (IVORY_BOT[2] - IVORY_TOP[2]) * t),
        )
        for x in range(S):
            px[x, y] = px_row
    tile = grad.convert("RGBA")

    # Mặt nạ bo góc squircle.
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=RADIUS, fill=255)
    tile.putalpha(mask)

    # Viền mảnh cho rõ trên nền sáng.
    bd = ImageDraw.Draw(tile)
    bd.rounded_rectangle([2, 2, S - 3, S - 3], radius=RADIUS - 2, outline=BORDER + (255,), width=4)

    # Sen đỏ (trong suốt) canh giữa, chiếm ~76% theo cạnh lớn.
    sym = Image.open(SYMBOL).convert("RGBA")
    target = int(S * 0.76)
    scale = target / max(sym.width, sym.height)
    sym_r = sym.resize((round(sym.width * scale), round(sym.height * scale)), Image.LANCZOS)
    ox = (S - sym_r.width) // 2
    oy = (S - sym_r.height) // 2
    tile.alpha_composite(sym_r, (ox, oy))
    return tile


def _size_dirs(theme_root: str):
    out = []
    if not os.path.isdir(theme_root):
        return out
    for name in sorted(os.listdir(theme_root)):
        m = SIZE_RE.match(name)
        if m and os.path.isdir(os.path.join(theme_root, name, "apps")):
            out.append((int(m.group(1)), os.path.join(theme_root, name, "apps")))
    return out


def main() -> None:
    master = _build_master()
    os.makedirs(os.path.dirname(MASTER), exist_ok=True)
    master.save(MASTER, "PNG")
    print(f"wrote master {MASTER} ({master.size})")

    n = 0
    for theme in THEMES:
        for size, apps_dir in _size_dirs(os.path.join(ICONS_ROOT, theme)):
            icon = master.resize((size, size), Image.LANCZOS)
            for fname in FILENAMES:
                target = os.path.join(apps_dir, fname)
                if os.path.exists(target):
                    icon.save(target, "PNG")
                    n += 1
    print(f"regenerated {n} theme icon files (light tile)")

    if os.path.isdir(os.path.dirname(CALAMARES_LOGO)):
        master.save(CALAMARES_LOGO, "PNG")
        print(f"wrote calamares logo {CALAMARES_LOGO}")


if __name__ == "__main__":
    main()
