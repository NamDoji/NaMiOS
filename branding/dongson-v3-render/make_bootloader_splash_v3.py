#!/usr/bin/env python3
"""NaMiOS — sinh lai splash.png cho GRUB (800x600, config/bootloaders/grub-pc/)
va isolinux/vesamenu (640x480, config/bootloaders/isolinux/) theo bo nhan dien
v3 "Dong Son" (navy + bieu tuong trong dong + song bien) — THAY ban nga-am
("boot-identity" polish 10/11/2026, da tu ghi chu trong theme.txt/stdmenu.cfg
la lech voi huong 09/11 roi lai chinh no bi sieu-xi boi QD rieng 11/11/2026
cho 3 diem cham-tram boot/login/splash, xem dongson_shapes.py dau file).

Giu NGUYEN vung bo cuc da thiet lap tu wave "boot-identity" truoc (logo+ten
san pham dat trong 8%-32% chieu cao, khoang trong 32%-52% lam vung dem an
toan truoc khi cham boot_menu bat dau o 52% — xem config/bootloaders/grub-pc/
live-theme/theme.txt) — CHI doi mau nen/logo, KHONG doi vi tri cac thanh
phan text that (title/boot_menu/progress_bar) ma GRUB/vesamenu tu ve de.

Dai song teal/gold dat gan day man hinh nhu nen SDDM/Plymouth — AN TOAN nam
DUOI ca vung boot_menu vi day chi la lop nen mo (opacity 10-14%), boot_menu
la TEXT GRUB tu ve DE LEN TREN bat ky nen nao, khong phai anh tinh chan
tuong tac (tuong tu Background.qml cua SDDM va background.png cua Plymouth).

Tai lap: python3 branding/dongson-v3-render/make_bootloader_splash_v3.py
Dau ra:
  - config/bootloaders/grub-pc/splash.png      (800x600)
  - config/bootloaders/isolinux/splash.png     (640x480)
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dongson_shapes import GOLD, IVORY, TEAL, VERMILION, draw_navy_wave_background, draw_trongdong_symbol  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")


def _logo_lockup(symbol_px: int, font_px: int) -> Image.Image:
    sym = draw_trongdong_symbol(symbol_px, ring_color=IVORY, star_color=GOLD, tick_color=VERMILION,
                                 flourish_color=TEAL, flourish_alt_color=VERMILION)
    f = ImageFont.truetype(FONT_BOLD, font_px)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), "NaMiOS", font=f)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    gap = max(8, symbol_px // 12)
    canvas_h = max(symbol_px, text_h)
    canvas_w = symbol_px + gap + text_w
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(sym, (0, (canvas_h - symbol_px) // 2))
    draw = ImageDraw.Draw(canvas)
    text_x = symbol_px + gap
    text_y = (canvas_h - text_h) // 2 - bbox[1]
    draw.text((text_x, text_y), "NaMiOS", font=f, fill=IVORY)
    return canvas


def _make_splash(w: int, h: int, out_path: str) -> None:
    bg = draw_navy_wave_background(w, h)

    band_top = round(h * 0.08)
    band_bottom = round(h * 0.32)
    band_h = band_bottom - band_top
    symbol_px = round(band_h * 0.92)
    font_px = round(symbol_px * 0.46)

    logo = _logo_lockup(symbol_px, font_px)
    # thu nho neu lockup rong hon khong gian an toan (~86% chieu rong canvas)
    max_w = round(w * 0.86)
    if logo.width > max_w:
        scale = max_w / logo.width
        logo = logo.resize((max_w, round(logo.height * scale)), Image.LANCZOS)

    x = (w - logo.width) // 2
    y = band_top + (band_h - logo.height) // 2
    bg.alpha_composite(logo, (x, y))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bg.convert("RGB").save(out_path, "PNG")
    print(f"wrote {out_path} ({w}x{h}, {os.path.getsize(out_path) // 1024} KB)")


def main() -> None:
    _make_splash(800, 600, os.path.join(ROOT, "distro/live-build/config/bootloaders/grub-pc/splash.png"))
    _make_splash(640, 480, os.path.join(ROOT, "distro/live-build/config/bootloaders/isolinux/splash.png"))


if __name__ == "__main__":
    main()
