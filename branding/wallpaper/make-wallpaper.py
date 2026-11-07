#!/usr/bin/env python3
"""Sinh hình nền mặc định NaMiOS từ bộ nhận diện (branding/logo).

Nền gradient navy đúng bộ màu icon ("Sen bừng sáng": #254A60 → #0B2034) +
quầng sáng nhẹ + logo ngang bản nền-tối (lotus + chữ NaMiOS) canh giữa.

Tái lập: python3 branding/wallpaper/make-wallpaper.py
Đầu ra:  distro/.../usr/share/backgrounds/namios/namios-default.png (2560x1440)

Không phụ thuộc font hệ thống (logo đã là ảnh có sẵn chữ). Nếu muốn thêm dòng
tag "Hệ điều hành cho người Việt" thì render ở bước build với Noto Sans.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCKUP = os.path.join(ROOT, "branding/logo/01_Master/NaMiOS_Logo_Dark_2400.png")
OUT = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/backgrounds/namios/namios-default.png",
)

W, H = 2560, 1440
TOP = (0x25, 0x4A, 0x60)  # navy_light
BOT = (0x0B, 0x20, 0x34)  # navy_dark
GLOW = (0x31, 0x5F, 0x78)  # quầng sáng nhẹ hơn nền


def _gradient() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(TOP[0] + (BOT[0] - TOP[0]) * t)
        g = int(TOP[1] + (BOT[1] - TOP[1]) * t)
        b = int(TOP[2] + (BOT[2] - TOP[2]) * t)
        row = (r, g, b)
        for x in range(W):
            px[x, y] = row
    return img


def main() -> None:
    bg = _gradient()
    # quầng sáng ellipse mềm phía sau logo
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    cx, cy, maxr = W // 2, int(H * 0.44), 900
    for rr in range(maxr, 0, -8):
        a = int(60 * (1 - rr / maxr))
        md.ellipse(
            [cx - rr, cy - int(rr * 0.72), cx + rr, cy + int(rr * 0.72)], fill=a
        )
    bg = Image.composite(Image.new("RGB", (W, H), GLOW), bg, mask)

    lk = Image.open(LOCKUP).convert("RGBA")
    tw = 1200
    lk = lk.resize((tw, int(lk.height * tw / lk.width)), Image.LANCZOS)
    base = bg.convert("RGBA")
    base.alpha_composite(lk, ((W - lk.width) // 2, int(H * 0.44) - lk.height // 2))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    base.convert("RGB").save(OUT, "PNG")
    print(f"wrote {OUT} ({W}x{H}, {os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
