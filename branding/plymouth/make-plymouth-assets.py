#!/usr/bin/env python3
"""Sinh ảnh cho theme Plymouth "namios" (two-step, đơn giản) từ bộ nhận diện
(branding/logo) — cùng bộ màu "Sen bừng sáng" dùng cho wallpaper/SDDM
(#254A60 -> #0B2034, chữ "NaMiOS" chữ sáng trên nền tối).

Sinh 3 file:
  - background.png : gradient navy đặc 1920x1080 (two-step tự stretch/tile
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

Tái lập: python3 branding/plymouth/make-plymouth-assets.py
Đầu ra:  distro/live-build/config/includes.chroot/usr/share/plymouth/themes/namios/*.png
"""
from __future__ import annotations

import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCKUP_LIGHT = os.path.join(ROOT, "branding/logo/01_Master/NaMiOS_Logo_Light_2400.png")
SYMBOL = os.path.join(ROOT, "branding/logo/01_Master/NaMiOS_Symbol_Transparent_1024.png")
OUT_DIR = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/plymouth/themes/namios",
)

TOP = (0x25, 0x4A, 0x60)  # navy_light — khớp theme.conf BackgroundStartColor
BOT = (0x0B, 0x20, 0x34)  # navy_dark  — khớp theme.conf BackgroundEndColor

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


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) background.png — gradient đặc, two-step sẽ stretch vừa màn hình thật
    #    (ScaleBackgroundImage=true trong theme.conf) -> không quan trọng tỉ lệ.
    bg = _gradient(BG_W, BG_H)
    bg_path = os.path.join(OUT_DIR, "background.png")
    bg.save(bg_path, "PNG")
    print(f"wrote {bg_path} ({BG_W}x{BG_H}, {os.path.getsize(bg_path) // 1024} KB)")

    # 2) watermark.png — logo ngang sáng-trên-tối, resize về đúng 480px rộng
    lk = Image.open(LOCKUP_LIGHT).convert("RGBA")
    wk_h = round(lk.height * WATERMARK_W / lk.width)
    wk = lk.resize((WATERMARK_W, wk_h), Image.LANCZOS)
    wk_path = os.path.join(OUT_DIR, "watermark.png")
    wk.save(wk_path, "PNG")
    print(f"wrote {wk_path} ({WATERMARK_W}x{wk_h}, {os.path.getsize(wk_path) // 1024} KB)")

    # 3) lock.png — bắt buộc phải tồn tại + đọc được (two-step), icon lotus nhỏ
    sym = Image.open(SYMBOL).convert("RGBA")
    lock = sym.resize((LOCK_PX, LOCK_PX), Image.LANCZOS)
    lock_path = os.path.join(OUT_DIR, "lock.png")
    lock.save(lock_path, "PNG")
    print(f"wrote {lock_path} ({LOCK_PX}x{LOCK_PX}, {os.path.getsize(lock_path) // 1024} KB)")


if __name__ == "__main__":
    main()
