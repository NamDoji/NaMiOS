#!/usr/bin/env python3
"""[ĐÃ NGHỈ HƯU — v2] Sinh hình nền mặc định từ bộ nhận diện v2 "Sen Việt"
(branding/logo-sen-viet-v2/). Hình nền đang ship (namios-default.png) đã là
v3 "Đông Sơn" (nền navy + trống đồng, không sen/không chữ "NaMiOS"); script này
bị chặn fail-closed trong main() để khỏi ghi đè art v3 (xem NAMI_ALLOW_V2_WALLPAPER).

QUYẾT ĐỊNH THIẾT KẾ (Cuong 09/11/2026): "hoa sen là loài hoa quý, KHÔNG đặt
trên nền đen/mực đêm". => Nền hình nền đổi sang NGÀ ẤM (ivory) sang trọng,
sáng nhẹ, hợp văn hoá Việt (sen hồng/đỏ trên nền sáng) thay cho nền mực đêm.

Thành phần: nền gradient ngà ấm (sáng ở trên, ấm sâu hơn ở dưới) + một quầng
ấm VÀNG rất nhạt "nâng" biểu tượng (không phải vệt tối) + biểu tượng sen Sen
Việt (NaMiOS_Sen_Viet_Symbol_1024.png, raster PNG trong suốt — KHÔNG rasterize
SVG vì build không có cairosvg/rsvg/inkscape) đặt lệch trái + chữ "NaMiOS" tự
vẽ ("NaMi" màu chữ-mực #182E3B đậm đọc rõ trên nền sáng, "OS" đỏ son #C93643) +
khẩu hiệu nhỏ "Nét sen Việt, mở tương lai." màu ấm dịu phía dưới.

Font: DejaVu Sans / Bold (branding/fonts/, trùng fonts-dejavu-core trong
package-lists/0300-fonts.list.chroot; phủ đủ dấu tiếng Việt).

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

# Bộ màu "Sen Việt" (branding/logo-sen-viet-v2/README.md).
IVORY_TOP = (0xFB, 0xF8, 0xF2)     # ngà sáng — nửa trên
IVORY_BOT = (0xEF, 0xE3, 0xD1)     # ngà ấm sâu hơn — nửa dưới (chiều sâu)
WARM_GLOW = (0xF2, 0xC6, 0x6D)     # vàng tâm — quầng ấm rất nhạt nâng biểu tượng
SON = (0xC9, 0x36, 0x43)           # đỏ son — chữ "OS"
INK_TEXT = (0x18, 0x2E, 0x3B)      # chữ mực — "NaMi" đọc rõ trên nền sáng
TAGLINE_DIM = (0x8A, 0x7E, 0x6A)   # khẩu hiệu ấm dịu


def _gradient() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(IVORY_TOP[0] + (IVORY_BOT[0] - IVORY_TOP[0]) * t)
        g = int(IVORY_TOP[1] + (IVORY_BOT[1] - IVORY_TOP[1]) * t)
        b = int(IVORY_TOP[2] + (IVORY_BOT[2] - IVORY_TOP[2]) * t)
        row = (r, g, b)
        for x in range(W):
            px[x, y] = row
    return img


def _glow(base: Image.Image, cx: int, cy: int) -> Image.Image:
    """Quầng ấm VÀNG rất nhạt phía sau biểu tượng để "nâng" hoa sen trên nền
    sáng (không dùng vệt tối). Alpha thấp để tinh tế, không loang."""
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    maxr = 820
    for rr in range(maxr, 0, -8):
        a = int(30 * (1 - rr / maxr))  # tối đa ~30/255 — rất nhạt
        md.ellipse([cx - rr, cy - int(rr * 0.80), cx + rr, cy + int(rr * 0.80)], fill=a)
    glow_layer = Image.new("RGB", (W, H), WARM_GLOW)
    return Image.composite(glow_layer, base, mask)


def main() -> None:
    # [KHOÁ v2] Generator này vẽ hình nền v2 "Sen Việt" (sen + chữ "NaMiOS").
    # Hình nền ĐANG SHIP (namios-default.png) đã là v3 "Đông Sơn" (nền navy +
    # hoạ tiết trống đồng, không sen, không chữ "NaMiOS"). Chạy lại script này
    # sẽ GHI ĐÈ art v3 bằng v2 cũ. Chặn fail-closed; chỉ chạy khi CỐ Ý đặt
    # NAMI_ALLOW_V2_WALLPAPER=1.
    if os.environ.get("NAMI_ALLOW_V2_WALLPAPER") != "1":
        raise SystemExit(
            "[CHẶN] Generator hình nền v2 'Sen Việt' đã nghỉ hưu. Hình nền đang "
            "ship là v3 'Đông Sơn'; chạy script này sẽ ghi đè art v3 bằng v2 cũ. "
            "Nếu CỐ Ý khôi phục v2, đặt NAMI_ALLOW_V2_WALLPAPER=1 rồi chạy lại."
        )
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

    # "NaMiOS" — "NaMi" chữ mực đậm (đọc rõ trên nền sáng) + "OS" đỏ son.
    word_size = 190
    f_word = ImageFont.truetype(FONT_BOLD, word_size)
    text_x = sym_x + sym_w + 90
    bbox_nami = draw.textbbox((0, 0), "NaMi", font=f_word)
    nami_w = bbox_nami[2] - bbox_nami[0]
    bbox_full = draw.textbbox((0, 0), "NaMiOS", font=f_word)
    full_h = bbox_full[3] - bbox_full[1]
    text_y = cy - full_h // 2 - bbox_full[1]

    draw.text((text_x, text_y), "NaMi", font=f_word, fill=INK_TEXT)
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
