#!/usr/bin/env python3
"""NaMiOS — sinh anh nen man hinh dang nhap SDDM theme "namios", bo nhan dien
v3 "Dong Son" (navy + bieu tuong trong dong + song bien teal/gold).

QUYET DINH THIET KE (khac voi dung thang file PNG 1920x1080 co san trong
branding/kit/NaMi_Brand_DongSon_v1/04_system_screens/login-background.png):
anh goc cua kit VE SAN chu tinh "NaMi"/"Xin chao"/"Dang nhap de tiep tuc"
(xem noi dung <text> trong .../login-background.svg, y~560-790px tren canvas
1920x1080) NAM DE NGAY VUNG GIUA MAN HINH — dung vi tri Main.qml dat khoi
dang nhap THAT (dong ho + danh sach nguoi dung + o mat khau + nut) khi dung
anchors.centerIn mac dinh truoc day. Neu ghep thang PNG do lam nen, chu tinh
"Xin chao"/"Dang nhap de tiep tuc" se dung ngay DUOI lop the/o mat khau that,
tao cam giac 2 lop chu trung/xung dot — trai voi nguyen tac "khong chen hinh
splash tinh nhu UI tuong tac" (xem 06_implementation/CLAUDE_CODE_PROMPT.md
dong 7: "Khong chen hinh splash tinh nhu UI tuong tac; tao nut, text va
progress that").

=> Chon nhanh "REPRODUCE" ma chinh nhiem vu cho phep ro rang ("use the kit
login-background image OR reproduce it: navy + teal wave"): ve lai BANG
dongson_shapes (cung toa do goc SVG, cung mau, cung vi tri song+bieu tuong)
NHUNG BO 3 dong chu tinh — vi Main.qml da tu ve dong ho SONG + badge "NaMiOS"
那 that roi, khong can anh tinh lap lai. Main.qml (cung sua trong nhiem vu nay)
doi cho khoi dang nhap xuong 1/3 duoi man hinh (tren dai song) de KHONG de
len vung bieu tuong trung tam phia tren.

Tai lap: python3 branding/dongson-v3-render/make_sddm_login_bg_v3.py
Dau ra:  distro/live-build/config/includes.chroot/usr/share/sddm/themes/namios/namios-login-background.png
"""
from __future__ import annotations

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dongson_shapes import GOLD, IVORY, TEAL, VERMILION, draw_navy_wave_background, draw_trongdong_symbol  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(
    ROOT,
    "distro/live-build/config/includes.chroot/usr/share/sddm/themes/namios",
)

W, H = 1920, 1080
# Bieu tuong can giua ngang, than cao ~358px dat tai y~130..488 — DUNG dung vi
# tri/ty le cua kit (translate(780 130) scale(.70) tren canvas 512 => box
# 358x358 bat dau (780,130)) de giu "coherent" voi huong thiet ke kit, trong
# luc Main.qml dat khoi dang nhap that o 1/3 duoi (xem ghi chu dau file).
SYMBOL_SIZE = 358
SYMBOL_X = 780
SYMBOL_Y = 130


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    bg = draw_navy_wave_background(W, H)
    sym = draw_trongdong_symbol(
        SYMBOL_SIZE, ring_color=IVORY, star_color=GOLD, tick_color=VERMILION,
        flourish_color=TEAL, flourish_alt_color=VERMILION,
    )
    bg.alpha_composite(sym, (SYMBOL_X, SYMBOL_Y))
    out_path = os.path.join(OUT_DIR, "namios-login-background.png")
    bg.convert("RGB").save(out_path, "PNG")
    print(f"wrote {out_path} ({W}x{H}, {os.path.getsize(out_path) // 1024} KB)")


if __name__ == "__main__":
    main()
