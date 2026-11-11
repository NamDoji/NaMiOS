#!/usr/bin/env python3
"""[ĐÃ NGHỈ HƯU — v2] Sinh 2 ảnh branding Calamares từ bộ nhận diện v2
"Sen Việt" (branding/logo-sen-viet-v2/).

⚠️  CẢNH BÁO: Đây là generator CŨ thuộc bộ nhận diện v2 "Sen Việt". Hệ đã
rebrand sang v3 "Đông Sơn" (commit 0798827). Các ảnh calamares ĐANG SHIP
(logo.png/welcome.png + bg-welcome/bg-progress) là bản v3 và KHÔNG do script
này tạo. Nếu chạy lại script này nó sẽ GHI ĐÈ art v3 bằng art v2 cũ — làm hỏng
nhận diện. Vì vậy script tự chặn (fail-closed) trừ khi đặt biến môi trường
NAMI_ALLOW_V2_CALAMARES=1 (chỉ dùng khi cố ý khôi phục art v2).

  - logo.png    : icon vuông 1024x1024 — chính là NaMiOS_App_Icon_1024.png
                  (sen đỏ son trên nền vuông bo góc mực đêm), dùng nguyên,
                  không chỉnh sửa (branding.desc dùng cho cả productLogo và
                  productIcon).
  - welcome.png : logo ngang 2400x652, nền TRONG SUỐT (khớp bản cũ — kiểm
                  tra bằng Pillow thấy góc ảnh cũ alpha=0), chữ "NaMiOS" màu
                  mực ("NaMi") + đỏ son ("OS") — dùng trên nền sáng của màn
                  hình welcome Calamares (xem etc/calamares/branding/namios/
                  branding.desc, images: productWelcome).

Không rasterize SVG (môi trường build không có cairosvg/rsvg/inkscape) — chỉ
resize/compose từ PNG có sẵn + tự vẽ chữ bằng Pillow (DejaVu Sans Bold,
branding/fonts/ — cùng font v2 README ghi làm mẫu, trùng gói
fonts-dejavu-core đã có trong package-lists).

Tái lập: python3 branding/calamares/make-calamares-assets.py
Đầu ra:  distro/live-build/config/includes.chroot/etc/calamares/branding/namios/{logo,welcome}.png
"""

from __future__ import annotations

import os
import shutil

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_ICON = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_App_Icon_1024.png")
SYMBOL = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
OUT_DIR = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/etc/calamares/branding/namios",
)

INK = (0x18, 0x2E, 0x3B)  # chữ mực — "NaMi" trên nền sáng
SON = (0xC9, 0x36, 0x43)  # đỏ son — "OS"

WELCOME_W, WELCOME_H = 2400, 652


def make_logo() -> None:
    src = Image.open(APP_ICON).convert("RGBA")
    assert src.size == (1024, 1024), f"expected 1024x1024, got {src.size}"
    out_path = os.path.join(OUT_DIR, "logo.png")
    shutil.copyfile(APP_ICON, out_path)
    print(f"wrote {out_path} ({src.size[0]}x{src.size[1]}, copy of {os.path.basename(APP_ICON)})")


def make_welcome() -> None:
    sym = Image.open(SYMBOL).convert("RGBA")
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

    canvas = Image.new("RGBA", (WELCOME_W, WELCOME_H), (0, 0, 0, 0))
    sym_x = 40
    sym_y = (WELCOME_H - sym_h) // 2
    canvas.alpha_composite(sym_r, (sym_x, sym_y))

    draw = ImageDraw.Draw(canvas)
    text_x = sym_x + sym_w + 60
    text_y = (WELCOME_H - text_h) // 2 - bbox_full[1]
    draw.text((text_x, text_y), "NaMi", font=f, fill=INK)
    draw.text((text_x + nami_w, text_y), "OS", font=f, fill=SON)

    out_path = os.path.join(OUT_DIR, "welcome.png")
    canvas.save(out_path, "PNG")
    print(f"wrote {out_path} ({WELCOME_W}x{WELCOME_H}, {os.path.getsize(out_path) // 1024} KB)")


def main() -> None:
    if os.environ.get("NAMI_ALLOW_V2_CALAMARES") != "1":
        raise SystemExit(
            "[CHẶN] Generator calamares v2 'Sen Việt' đã nghỉ hưu. Art calamares "
            "đang ship là v3 'Đông Sơn' (commit 0798827); chạy script này sẽ ghi "
            "đè art v3 bằng v2 cũ. Nếu CỐ Ý khôi phục v2, đặt "
            "NAMI_ALLOW_V2_CALAMARES=1 rồi chạy lại."
        )
    os.makedirs(OUT_DIR, exist_ok=True)
    make_logo()
    make_welcome()


if __name__ == "__main__":
    main()
