#!/usr/bin/env python3
"""Sinh hình nền mặc định NaMiOS từ bộ nhận diện v2 "Sen Việt"
(branding/logo-sen-viet-v2/), THAY cho bộ "Sen bừng sáng" navy/jade cũ.

Nền gradient mực đêm (#122A3A, hơi sáng hơn ở nửa trên để có chiều sâu) +
quầng sáng đỏ-son rất nhạt phía sau biểu tượng + biểu tượng sen Sen Việt
(NaMiOS_Sen_Viet_Symbol_1024.png, raster PNG có sẵn — KHÔNG rasterize SVG,
môi trường build không có cairosvg/rsvg/inkscape) đặt lệch trái + chữ
"NaMiOS" tự vẽ bằng Pillow ("NaMi" màu sáng, "OS" màu đỏ son #C93643) +
khẩu hiệu nhỏ "Nét sen Việt, mở tương lai." phía dưới.

Font: DejaVu Sans / DejaVu Sans Bold (branding/fonts/, copy từ gói
matplotlib mpl-data đã cài sẵn trong sandbox — ĐÚNG font mà
branding/logo-sen-viet-v2/README.md ghi là font mẫu dùng trong các SVG v2,
và trùng gói fonts-dejavu-core đã có trong
distro/live-build/config/package-lists/0300-fonts.list.chroot — không thêm
font lạ/không rõ quyền phân phối). Phủ đủ dấu tiếng Việt (đã kiểm bằng
fontTools cmap trước khi chọn).

Tái lập: python3 branding/wallpaper/make-wallpaper.py
Đầu ra:  distro/.../usr/share/backgrounds/namios/namios-default.png (2560x1440)
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYMBOL = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
FONT_REG = os.path.join(ROOT, "branding/fonts/DejaVuSans.ttf")
OUT = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/backgrounds/namios/namios-default.png",
)

W, H = 2560, 1440

# Bộ màu "Sen Việt" (branding/logo-sen-viet-v2/README.md) — jade cũ ĐÃ GỠ BỎ.
INK_NAVY = (0x12, 0x2A, 0x3A)       # mực đêm — nền
INK_NAVY_TOP = (0x1D, 0x3C, 0x4F)  # mực đêm sáng hơn một chút cho chiều sâu
SON = (0xC9, 0x36, 0x43)           # đỏ son — chữ "OS", quầng sáng
LIGHT = (0xF4, 0xEF, 0xE8)         # chữ sáng cho "NaMi" + khẩu hiệu
TAGLINE_DIM = (0xC9, 0xC2, 0xB7)   # khẩu hiệu nhạt hơn chữ chính


def _gradient() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(INK_NAVY_TOP[0] + (INK_NAVY[0] - INK_NAVY_TOP[0]) * t)
        g = int(INK_NAVY_TOP[1] + (INK_NAVY[1] - INK_NAVY_TOP[1]) * t)
        b = int(INK_NAVY_TOP[2] + (INK_NAVY[2] - INK_NAVY_TOP[2]) * t)
        row = (r, g, b)
        for x in range(W):
            px[x, y] = row
    return img


def _glow(base: Image.Image, cx: int, cy: int) -> Image.Image:
    """Quầng sáng đỏ-son rất nhạt phía sau biểu tượng (giữ tinh thần bản cũ,
    đổi màu quầng sáng từ navy-light sang đỏ son mờ)."""
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    maxr = 760
    for rr in range(maxr, 0, -8):
        a = int(42 * (1 - rr / maxr))
        md.ellipse([cx - rr, cy - int(rr * 0.78), cx + rr, cy + int(rr * 0.78)], fill=a)
    glow_layer = Image.new("RGB", (W, H), SON)
    return Image.composite(glow_layer, base, mask)


def main() -> None:
    bg = _gradient()

    sym = Image.open(SYMBOL).convert("RGBA")
    sym_h = 560
    sym_w = round(sym.width * sym_h / sym.height)
    sym = sym.resize((sym_w, sym_h), Image.LANCZOS)

    cx_sym = int(W * 0.30)
    cy = int(H * 0.46)
    bg = _glow(bg, cx_sym, cy)
    base = bg.convert("RGBA")
    sym_x = cx_sym - sym_w // 2
    sym_y = cy - sym_h // 2
    base.alpha_composite(sym, (sym_x, sym_y))

    draw = ImageDraw.Draw(base)

    # "NaMiOS" — "NaMi" sáng + "OS" đỏ son, canh theo chiều cao biểu tượng.
    word_size = 190
    f_word = ImageFont.truetype(FONT_BOLD, word_size)
    text_x = sym_x + sym_w + 90
    bbox_nami = draw.textbbox((0, 0), "NaMi", font=f_word)
    nami_w = bbox_nami[2] - bbox_nami[0]
    bbox_full = draw.textbbox((0, 0), "NaMiOS", font=f_word)
    full_h = bbox_full[3] - bbox_full[1]
    text_y = cy - full_h // 2 - bbox_full[1]

    draw.text((text_x, text_y), "NaMi", font=f_word, fill=LIGHT)
    draw.text((text_x + nami_w, text_y), "OS", font=f_word, fill=SON)

    # Khẩu hiệu nhỏ bên dưới wordmark.
    tag_size = 46
    f_tag = ImageFont.truetype(FONT_REG, tag_size)
    tagline = "Nét sen Việt, mở tương lai."
    tag_y = text_y + full_h + 46
    draw.text((text_x, tag_y), tagline, font=f_tag, fill=TAGLINE_DIM)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    base.convert("RGB").save(OUT, "PNG")
    print(f"wrote {OUT} ({W}x{H}, {os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
