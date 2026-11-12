#!/usr/bin/env python3
"""NaMi — sinh AVATAR mac dinh (.face.icon) bo nhan dien v2 "Dong Son duong dai".

LY DO (pilot 12/11/2026 — anh Cuong boot may that): man hinh Roi phien (Leave/
logout) + danh sach nguoi dung hien avatar = logo XOAY DEBIAN (mau do) vi
nguoi dung moi KHONG co ~/.face.icon rieng -> KUser.faceIconUrl roi ve avatar
mac dinh cua he (Debian). Ta ship mot avatar NaMi vao /etc/skel/.face.icon;
Calamares copy /etc/skel sang HOME nguoi dung moi -> ~/.face.icon = avatar
NaMi, KHONG con xoay Debian.

THIET KE v2: dia navy #092D4F + vanh vang mong + BIEU TUONG MOI v2 ban nen toi
(namios-symbol-dark-256.png trong bo kit NaMi_Brand_DongSon_v2) composite canh
giua ~62% duong kinh dia. KHONG ve lai trong dong cu — dung thang asset kit la
nguon chuan (khong co SVG rasterizer trong sandbox nay).

Tai lap: python3 branding/dongson-v3-render/make_default_avatar_v3.py
Dau ra:
  distro/.../includes.chroot/etc/skel/.face.icon
  distro/.../includes.chroot/usr/share/namios/avatars/namios-default-avatar.png
verified_on_host: NO.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KIT = os.path.join(ROOT, "branding", "kit", "NaMi_Brand_DongSon_v2", "assets")
KIT_SYMBOL_DARK = os.path.join(KIT, "namios-symbol-dark-256.png")
CHROOT = os.path.join(ROOT, "distro", "live-build", "config", "includes.chroot")
OUT_FACE = os.path.join(CHROOT, "etc", "skel", ".face.icon")
OUT_REF = os.path.join(
    CHROOT, "usr", "share", "namios", "avatars", "namios-default-avatar.png"
)

NAVY = (9, 45, 79, 255)      # #092D4F
GOLD = (222, 169, 62, 255)   # #DEA93E
IVORY = (255, 249, 239)      # #FFF9EF

SIZE = 256
SS = 4            # supersample for smooth disc/rim
SYMBOL_FRAC = 0.62  # symbol duong kinh ~62% dia


def build_avatar() -> Image.Image:
    S = SIZE * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dia navy tron (khong fill goc vuong).
    margin = round(S * 0.012)
    bbox = (margin, margin, S - margin, S - margin)
    draw.ellipse(bbox, fill=NAVY)

    # Diem sang nhe phia tren tao chieu sau.
    hi = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hb = (round(S * 0.16), round(S * 0.08), round(S * 0.84), round(S * 0.62))
    hd.ellipse(hb, fill=(IVORY[0], IVORY[1], IVORY[2], 15))
    img = Image.alpha_composite(img, hi)
    draw = ImageDraw.Draw(img)

    # Vanh vang mong.
    rim_w = max(1, round(S * 0.018))
    draw.ellipse(bbox, outline=(GOLD[0], GOLD[1], GOLD[2], 230), width=rim_w)

    # Bieu tuong v2 ban nen toi, composite canh giua.
    sym = Image.open(KIT_SYMBOL_DARK).convert("RGBA")
    sym_px = round(S * SYMBOL_FRAC)
    sym = sym.resize((sym_px, sym_px), Image.LANCZOS)
    off = (S - sym_px) // 2
    img.alpha_composite(sym, (off, off))

    # Thu nho ve kich thuoc cuoi.
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    avatar = build_avatar()
    for out in (OUT_FACE, OUT_REF):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        avatar.save(out, "PNG")
        print(f"wrote {out} ({avatar.size[0]}x{avatar.size[1]}, "
              f"{os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
