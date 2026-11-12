#!/usr/bin/env python3
"""NaMi — BỘ ICON app "cách điệu TRỐNG ĐỒNG ĐÔNG SƠN" (teaser để duyệt hướng).

Cuong #18393: "Chuyển hết về trống đồng đông sơn (bạn đưa design cách điệu cho
các phần)." → icon app KHÔNG dùng glyph generic nữa; mỗi app = ô squircle chất
macOS + MOTIF Đông Sơn (vành chấm đồng + tia mặt trời mờ làm nền) + glyph chức
năng ở tâm, cùng họ nhận diện với logo mới (mặt trời 12 tia). App "Trợ lý" dùng
thẳng mặt trời 12 tia (biểu tượng thương hiệu).

Tái dùng tile squircle + glyph từ make_app_icons_macos_v3.py, THÊM lớp motif
Đông Sơn phía sau glyph. Đây là TEASER (4 icon) để anh Cuong chấm hướng trước
khi nhân cả bộ. verified_on_host: NO.
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_app_icons_macos_v3 import (  # noqa: E402
    C, E, WORK, FINAL, base_tile, g_doc, g_gear, g_globe, hx,
)

OUT = os.path.join(HERE, "app-icons-dongson-preview")
os.makedirs(OUT, exist_ok=True)
FONT = "/tmp/vnfonts/Roboto-Medium.ttf"
IVORY = (255, 249, 239)
GOLD = (232, 182, 74)


def dongson_backdrop(size):
    """Lớp motif Đông Sơn mờ: vành chấm đồng + tia mặt trời, phía sau glyph."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = cy = size / 2.0
    # 12 tia mặt trời mờ (nan quạt mảnh toả ra)
    rays = 12
    r_in, r_out = E * 0.5, E * 1.9
    for i in range(rays):
        ang = 2 * math.pi * i / rays - math.pi / 2
        w = 0.085
        p1 = (cx + r_in * math.cos(ang - w), cy + r_in * math.sin(ang - w))
        p2 = (cx + r_in * math.cos(ang + w), cy + r_in * math.sin(ang + w))
        p3 = (cx + r_out * math.cos(ang), cy + r_out * math.sin(ang))
        d.polygon([p1, p2, p3], fill=(IVORY[0], IVORY[1], IVORY[2], 26))
    # vành chấm đồng (nhịp trống)
    dots, r_ring = 28, E * 1.62
    for i in range(dots):
        ang = 2 * math.pi * i / dots
        x = cx + r_ring * math.cos(ang)
        y = cy + r_ring * math.sin(ang)
        rr = E * 0.032
        d.ellipse([x - rr, y - rr, x + rr, y + rr],
                  fill=(IVORY[0], IVORY[1], IVORY[2], 60))
    # 2 vòng tròn mảnh
    for rr in (E * 1.72, E * 1.42):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  outline=(IVORY[0], IVORY[1], IVORY[2], 34),
                  width=max(1, int(E * 0.02)))
    return layer.filter(ImageFilter.GaussianBlur(WORK * 0.001))


def g_sun(d):
    """Mặt trời 12 tia (biểu tượng thương hiệu) — cho app Trợ lý."""
    pts = 12
    rO, rI = E * 1.35, E * 0.56
    poly = []
    for i in range(pts * 2):
        ang = math.pi * i / pts - math.pi / 2
        r = rO if i % 2 == 0 else rI
        poly.append((C + r * math.cos(ang), C + r * math.sin(ang)))
    d.polygon(poly, fill=GOLD + (255,))
    d.ellipse([C - E * 0.3, C - E * 0.3, C + E * 0.3, C + E * 0.3],
              fill=(255, 255, 255, 255))


ICONS = [
    ("nAssistant", "Trợ lý", "#124A7A", "#082742", g_sun, True),
    ("nDoc", "Văn bản", "#2F6FC9", "#1A3F86", lambda d: g_doc(d, hx("#1A3F86")), False),
    ("nBrowser", "Trình duyệt", "#2A9D9A", "#17726F", lambda d: g_globe(d, hx("#17726F")), False),
    ("nSettings", "Cài đặt", "#5B6473", "#2F3742", lambda d: g_gear(d, hx("#2F3742")), False),
]


def render(name, top, bottom, glyphfn, hero):
    tile = base_tile(hx(top), hx(bottom))
    tile = Image.alpha_composite(tile, dongson_backdrop(WORK))
    glyph = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glyph)
    glyphfn(gd)
    if not hero:
        sh = glyph.split()[3].filter(ImageFilter.GaussianBlur(WORK * 0.012))
        shimg = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
        shimg.putalpha(sh.point(lambda v: int(v * 0.26)))
        tile.alpha_composite(shimg, (0, int(WORK * 0.012)))
    tile = Image.alpha_composite(tile, glyph)
    icon = tile.resize((FINAL, FINAL), Image.LANCZOS)
    icon.save(os.path.join(OUT, f"{name}.png"))
    return icon


def contact_sheet(items):
    cols = 4
    cell, isz, pad, lblh, top = 300, 192, 60, 80, 150
    W = pad * 2 + cols * cell
    H = top + cell + lblh + 40
    import numpy as np
    bg = np.zeros((H, W, 3), np.float64)
    t = np.linspace(0, 1, H)[:, None, None]
    bg[:] = np.array(hx("#F4F6FA")) * (1 - t) + np.array(hx("#E4E8F0")) * t
    sheet = Image.fromarray(bg.astype(np.uint8), "RGB").convert("RGBA")
    dr = ImageDraw.Draw(sheet)
    try:
        ft = ImageFont.truetype(FONT, 50)
        fl = ImageFont.truetype(FONT, 32)
    except Exception:
        ft = fl = ImageFont.load_default()
    dr.text((pad, 46), "NaMi — icon cách điệu Trống Đồng Đông Sơn (mẫu)",
            font=ft, fill=hx("#092D4F") + (255,))
    for i, (name, viet) in enumerate(items):
        ic = Image.open(os.path.join(OUT, f"{name}.png")).resize((isz, isz), Image.LANCZOS)
        cx = pad + i * cell + (cell - isz) // 2
        cy = top + (cell - isz) // 2
        shm = ic.split()[3].filter(ImageFilter.GaussianBlur(16))
        shl = Image.new("RGBA", (isz, isz), (10, 25, 45, 0))
        shl.putalpha(shm.point(lambda v: int(v * 0.32)))
        s = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
        s.alpha_composite(shl, (cx, cy + 14))
        sheet = Image.alpha_composite(sheet, s.filter(ImageFilter.GaussianBlur(6)))
        sheet.alpha_composite(ic, (cx, cy))
        dr = ImageDraw.Draw(sheet)
        bb = dr.textbbox((0, 0), viet, font=fl)
        dr.text((pad + i * cell + (cell - (bb[2] - bb[0])) // 2, cy + isz + 16),
                viet, font=fl, fill=hx("#0E2238") + (255,))
    out = os.path.join(OUT, "contact-sheet.png")
    sheet.convert("RGB").save(out, "PNG")
    return out


def main():
    items = []
    for name, viet, top, bottom, fn, hero in ICONS:
        render(name, top, bottom, fn, hero)
        items.append((name, viet))
        print(f"[OK] {name} ({viet})")
    print("[OK] sheet ->", contact_sheet(items))


if __name__ == "__main__":
    main()
