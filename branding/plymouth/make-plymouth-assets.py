#!/usr/bin/env python3
"""Sinh ảnh cho theme Plymouth "namios" (two-step, đơn giản) từ bộ nhận diện
v2 "Sen Việt" (branding/logo-sen-viet-v2/) — THAY bộ "Sen bừng sáng"
navy/jade cũ. Nền mực đêm (#122A3A) + watermark sen đỏ son + chữ "NaMiOS"
("NaMi" sáng / "OS" đỏ son #C93643).

Sinh 3 file:
  - background.png : gradient mực đêm đặc 1920x1080 (two-step tự stretch/tile
    màn hình thật nên kích thước tuyệt đối không quan trọng; đây chỉ là lớp
    "đẹp hơn" — theme.conf đã đặt BackgroundStartColor/EndColor làm lưới an
    toàn, Plymouth tự vẽ gradient y hệt bằng mã nếu thiếu/hỏng file này).
  - watermark.png  : logo ngang (lotus + "NaMiOS") bản sáng-trên-tối, resize
    về đúng bề rộng 480px = bằng bề rộng progress bar trong theme.conf (xếp
    thẳng cột cho gọn, không phụ thuộc độ phân giải màn hình thật).
  - lock.png       : icon lotus-only thu nhỏ — two-step YÊU CẦU BẮT BUỘC file
    này tồn tại và đọc được (chỉ hiển thị khi có hộp thoại nhập mật khẩu/LUKS,
    hiếm khi xảy ra ở NaMiOS mặc định, nhưng thiếu file sẽ làm TOÀN BỘ splash
    không khởi tạo được — xem plymouth plugin.c display_normal()).

Chữ "NaMiOS" tự vẽ bằng Pillow (không có SVG rasterizer trong sandbox) dùng
font DejaVu Sans Bold (branding/fonts/ — cùng font v2 README ghi là font mẫu
dùng trong SVG, trùng gói fonts-dejavu-core đã có trong package-lists).

Tái lập: python3 branding/plymouth/make-plymouth-assets.py
Đầu ra:  distro/live-build/config/includes.chroot/usr/share/plymouth/themes/namios/*.png
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYMBOL = os.path.join(ROOT, "branding/logo-sen-viet-v2/NaMiOS_Sen_Viet_Symbol_1024.png")
FONT_BOLD = os.path.join(ROOT, "branding/fonts/DejaVuSans-Bold.ttf")
OUT_DIR = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/plymouth/themes/namios",
)

# Mực đêm — khớp theme.conf BackgroundStartColor/EndColor (xem namios.plymouth).
TOP = (0x1D, 0x3C, 0x4F)
BOT = (0x12, 0x2A, 0x3A)
SON = (0xC9, 0x36, 0x43)   # đỏ son — chữ "OS"
LIGHT = (0xF4, 0xEF, 0xE8)  # chữ sáng — "NaMi"

BG_W, BG_H = 1920, 1080
WATERMARK_W = 480  # = ProgressBarWidth trong theme.conf -> xếp thẳng cột
LOCK_PX = 128


def _gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        row = (
            int(TOP[0] + (BOT[0] - TOP[0]) * t),
            int(TOP[1] + (BOT[1] - TOP[1]) * t),
            int(TOP[2] + (BOT[2] - TOP[2]) * t),
        )
        for x in range(w):
            px[x, y] = row
    return img


def _make_watermark() -> Image.Image:
    """Biểu tượng sen (trái) + chữ "NaMiOS" (phải), nền trong suốt, cao cố
    định rồi resize cả khối về đúng WATERMARK_W."""
    sym = Image.open(SYMBOL).convert("RGBA")
    sym_h = 420
    sym_w = round(sym.width * sym_h / sym.height)
    sym_r = sym.resize((sym_w, sym_h), Image.LANCZOS)

    f = ImageFont.truetype(FONT_BOLD, 180)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox_full = d.textbbox((0, 0), "NaMiOS", font=f)
    bbox_nami = d.textbbox((0, 0), "NaMi", font=f)
    text_w = bbox_full[2] - bbox_full[0]
    text_h = bbox_full[3] - bbox_full[1]
    nami_w = bbox_nami[2] - bbox_nami[0]

    pad = 24
    canvas_h = max(sym_h, text_h) + pad * 2
    canvas_w = sym_w + 36 + text_w + pad * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(sym_r, (pad, (canvas_h - sym_h) // 2))

    draw = ImageDraw.Draw(canvas)
    text_x = pad + sym_w + 36
    text_y = (canvas_h - text_h) // 2 - bbox_full[1]
    draw.text((text_x, text_y), "NaMi", font=f, fill=LIGHT)
    draw.text((text_x + nami_w, text_y), "OS", font=f, fill=SON)

    out_h = round(canvas_h * WATERMARK_W / canvas_w)
    return canvas.resize((WATERMARK_W, out_h), Image.LANCZOS)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) background.png — gradient đặc, two-step sẽ stretch vừa màn hình thật
    #    (ScaleBackgroundImage=true trong theme.conf) -> không quan trọng tỉ lệ.
    bg = _gradient(BG_W, BG_H)
    bg_path = os.path.join(OUT_DIR, "background.png")
    bg.save(bg_path, "PNG")
    print(f"wrote {bg_path} ({BG_W}x{BG_H}, {os.path.getsize(bg_path) // 1024} KB)")

    # 2) watermark.png — logo ngang sáng-trên-tối, resize về đúng 480px rộng
    wk = _make_watermark()
    wk_path = os.path.join(OUT_DIR, "watermark.png")
    wk.save(wk_path, "PNG")
    print(f"wrote {wk_path} ({wk.width}x{wk.height}, {os.path.getsize(wk_path) // 1024} KB)")

    # 3) lock.png — bắt buộc phải tồn tại + đọc được (two-step), icon lotus nhỏ
    sym = Image.open(SYMBOL).convert("RGBA")
    lock = sym.resize((LOCK_PX, LOCK_PX), Image.LANCZOS)
    lock_path = os.path.join(OUT_DIR, "lock.png")
    lock.save(lock_path, "PNG")
    print(f"wrote {lock_path} ({LOCK_PX}x{LOCK_PX}, {os.path.getsize(lock_path) // 1024} KB)")


if __name__ == "__main__":
    main()
