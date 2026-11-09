#!/usr/bin/env python3
"""Cập nhật "bản runtime" nhận diện đóng gói trong ISO
(usr/share/namios-branding/logo/) từ bộ v2 "Sen Việt" — đây là thư mục
"active/shipped assets" (phân biệt với kho thiết kế gốc branding/logo/,
KHÔNG đụng tới, xem README ở đó + PROVENANCE.md). Giữ nguyên TÊN FILE cũ để
không hỏng tham chiếu từ brand.json/README trong cùng thư mục; chỉ thay NỘI
DUNG bằng bản v2.

SVG: copy thẳng nội dung text từ branding/logo-sen-viet-v2/ (không cần
rasterize — SVG→SVG chỉ là sao chép văn bản).
PNG/ICO: resize/compose từ PNG v2 có sẵn bằng Pillow (không có SVG
rasterizer trong sandbox).

Tái lập: python3 branding/namios-branding-runtime/make-runtime-assets.py
"""
from __future__ import annotations

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V2 = os.path.join(ROOT, "branding/logo-sen-viet-v2")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
OUT_DIR = os.path.join(
    ROOT, "distro/live-build/config/includes.chroot/usr/share/namios-branding/logo"
)

INK = (0x18, 0x2E, 0x3B)      # chữ mực — "NaMi" trên nền sáng (variant Light)
CREAM = (0xF8, 0xF5, 0xEE)    # chữ sáng — "NaMi" trên nền tối (variant Dark)
SON = (0xC9, 0x36, 0x43)      # đỏ son — "OS" (cả 2 bản)
INK_NAVY = (0x12, 0x2A, 0x3A)  # nền thẻ của bản Dark (khớp SVG v2: rect #122A3A)

LOCKUP_W, LOCKUP_H = 2400, 652


def _svg_copy(src_name: str, dst_name: str) -> None:
    src = os.path.join(V2, src_name)
    dst = os.path.join(OUT_DIR, dst_name)
    shutil.copyfile(src, dst)
    print(f"wrote {dst} (SVG text copy of {src_name})")


def _lockup(nami_color, bg=None) -> Image.Image:
    sym = Image.open(os.path.join(V2, "NaMiOS_Sen_Viet_Symbol_1024.png")).convert("RGBA")
    sym_h = 520
    sym_w = round(sym.width * sym_h / sym.height)
    sym_r = sym.resize((sym_w, sym_h), Image.LANCZOS)

    f = ImageFont.truetype(FONT_BOLD, 230)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox_full = d.textbbox((0, 0), "NaMiOS", font=f)
    bbox_nami = d.textbbox((0, 0), "NaMi", font=f)
    text_h = bbox_full[3] - bbox_full[1]
    nami_w = bbox_nami[2] - bbox_nami[0]

    base_color = bg if bg is not None else (0, 0, 0, 0)
    canvas = Image.new("RGBA", (LOCKUP_W, LOCKUP_H), base_color)
    sym_x = 40
    sym_y = (LOCKUP_H - sym_h) // 2
    canvas.alpha_composite(sym_r, (sym_x, sym_y))

    draw = ImageDraw.Draw(canvas)
    text_x = sym_x + sym_w + 60
    text_y = (LOCKUP_H - text_h) // 2 - bbox_full[1]
    draw.text((text_x, text_y), "NaMi", font=f, fill=nami_color)
    draw.text((text_x + nami_w, text_y), "OS", font=f, fill=SON)
    return canvas


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # --- SVG: copy thẳng từ v2 (giữ tên file cũ) ---
    _svg_copy("NaMiOS_App_Icon.svg", "NaMiOS_App_Icon_Master.svg")
    _svg_copy("NaMiOS_Sen_Viet_Symbol.svg", "NaMiOS_Symbol_Color.svg")
    _svg_copy("NaMiOS_Logo_Horizontal_Light.svg", "NaMiOS_Logo_Master_Outlined.svg")
    _svg_copy("NaMiOS_Logo_Horizontal_Dark.svg", "NaMiOS_Logo_Master_Outlined_Dark.svg")

    # --- PNG: resize/compose từ v2 bằng Pillow ---
    app_icon_src = os.path.join(V2, "NaMiOS_App_Icon_1024.png")
    app_icon_dst = os.path.join(OUT_DIR, "NaMiOS_App_Icon_1024.png")
    shutil.copyfile(app_icon_src, app_icon_dst)
    print(f"wrote {app_icon_dst} (copy of NaMiOS_App_Icon_1024.png)")

    sym_src = os.path.join(V2, "NaMiOS_Sen_Viet_Symbol_1024.png")
    sym_dst = os.path.join(OUT_DIR, "NaMiOS_Symbol_Transparent_1024.png")
    shutil.copyfile(sym_src, sym_dst)
    print(f"wrote {sym_dst} (copy of NaMiOS_Sen_Viet_Symbol_1024.png)")

    light = _lockup(INK)  # transparent bg, chữ mực — dùng trên nền sáng
    light_path = os.path.join(OUT_DIR, "NaMiOS_Logo_Light_2400.png")
    light.save(light_path, "PNG")
    print(f"wrote {light_path} ({light.size[0]}x{light.size[1]})")

    dark = _lockup(CREAM, bg=INK_NAVY + (255,))  # thẻ nền mực đêm đặc, chữ sáng
    dark_path = os.path.join(OUT_DIR, "NaMiOS_Logo_Dark_2400.png")
    dark.convert("RGBA").save(dark_path, "PNG")
    print(f"wrote {dark_path} ({dark.size[0]}x{dark.size[1]})")

    # Favicon đa cỡ (16/32/48) từ App Icon v2, multi-res .ico qua Pillow.
    app_icon = Image.open(app_icon_src).convert("RGBA")
    fav_path = os.path.join(OUT_DIR, "NaMiOS_Favicon.ico")
    app_icon.save(fav_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"wrote {fav_path} (multi-res ICO 16/32/48 from App_Icon_1024)")


if __name__ == "__main__":
    main()
