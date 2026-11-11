#!/usr/bin/env python3
"""NaMiOS — sinh lai 3 anh cho Plymouth theme "namios" (two-step) theo bo
nhan dien v3 "Dong Son" (THAY v2 "Sen Viet" nga am). Day la buoc ke tiep
truc tiep branding/plymouth/make-plymouth-assets.py (v2) — cung ky thuat
(Pillow, khong co SVG rasterizer trong sandbox), khac mau/hinh nguon.

QD THUONG HIEU 11/11/2026 (nhiem vu "Wave Dong Son" giao rieng cho system-
screens dev): nen BOOT/LOGIN/SPLASH chuyen sang navy #092D4F — GHI DE quyet
dinh 09/11/2026 "sen quy khong dat nen den" (quyet dinh do VAN DUNG cho cac
mat khac — vi du wallpaper desktop mac dinh, man hinh About) NHUNG duoc nguoi
giao nhiem vu xac nhan RO RANG la sieu-xi (supersede) rieng cho 3 diem cham-
tram nay. Ghi lai o day de nguoi doc sau nay khong tuong day la mau thuan/
quen cap nhat.

Sinh 3 file (giu NGUYEN co che namios.plymouth hien co — two-step, ImageDir
khong doi):
  - background.png : nen navy + 2 dai song teal/gold (dongson_shapes.draw_navy_
    wave_background) — KHONG co bieu tuong/chu (watermark.png dam nhiem phan
    do, tranh 2 lop logo de len nhau).
  - watermark.png  : bieu tuong trong dong (ban nen-toi, mau day du) + chu
    "NaMiOS" mau ngoc trai #FFF9EF, xep ngang, resize ve dung WATERMARK_W=480
    (= ProgressBarWidth trong namios.plymouth, xep thang cot nhu ban v2).
  - lock.png       : bieu tuong trong dong don (khong chu) 128px — hai hoa
    gioi han bat buoc cua two-step (hien khi co hop thoai mat khau/LUKS).

Tai lap: python3 branding/dongson-v3-render/make_plymouth_assets_v3.py
Dau ra:  distro/live-build/config/includes.chroot/usr/share/plymouth/themes/namios/*.png
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dongson_shapes import (  # noqa: E402
    GOLD,
    IVORY,
    TEAL,
    VERMILION,
    draw_navy_wave_background,
    draw_trongdong_symbol,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
OUT_DIR = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/plymouth/themes/namios",
)

BG_W, BG_H = 1920, 1080
WATERMARK_W = 480  # = ProgressBarWidth trong namios.plymouth
LOCK_PX = 128


def _make_watermark() -> Image.Image:
    sym_h = 300
    sym = draw_trongdong_symbol(sym_h, ring_color=IVORY, star_color=GOLD, tick_color=VERMILION,
                                 flourish_color=TEAL, flourish_alt_color=VERMILION)

    f = ImageFont.truetype(FONT_BOLD, 150)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), "NaMiOS", font=f)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad = 20
    canvas_h = max(sym_h, text_h) + pad * 2
    canvas_w = sym_h + 30 + text_w + pad * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(sym, (pad, (canvas_h - sym_h) // 2))

    draw = ImageDraw.Draw(canvas)
    text_x = pad + sym_h + 30
    text_y = (canvas_h - text_h) // 2 - bbox[1]
    draw.text((text_x, text_y), "NaMiOS", font=f, fill=IVORY)

    out_h = round(canvas_h * WATERMARK_W / canvas_w)
    return canvas.resize((WATERMARK_W, out_h), Image.LANCZOS)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    bg = draw_navy_wave_background(BG_W, BG_H).convert("RGB")
    bg_path = os.path.join(OUT_DIR, "background.png")
    bg.save(bg_path, "PNG")
    print(f"wrote {bg_path} ({BG_W}x{BG_H}, {os.path.getsize(bg_path) // 1024} KB)")

    wk = _make_watermark()
    wk_path = os.path.join(OUT_DIR, "watermark.png")
    wk.save(wk_path, "PNG")
    print(f"wrote {wk_path} ({wk.width}x{wk.height}, {os.path.getsize(wk_path) // 1024} KB)")

    lock = draw_trongdong_symbol(LOCK_PX, ring_color=IVORY, star_color=GOLD, tick_color=VERMILION,
                                  flourish_color=TEAL, flourish_alt_color=VERMILION)
    lock_path = os.path.join(OUT_DIR, "lock.png")
    lock.save(lock_path, "PNG")
    print(f"wrote {lock_path} ({LOCK_PX}x{LOCK_PX}, {os.path.getsize(lock_path) // 1024} KB)")


if __name__ == "__main__":
    main()
