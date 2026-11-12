#!/usr/bin/env python3
"""NaMi — sinh AVATAR mac dinh (.face.icon) bo nhan dien v3 "Dong Son".

LY DO (pilot 12/11/2026 — anh Cuong boot may that): man hinh Roi phien (Leave/
logout) + danh sach nguoi dung hien avatar = logo XOAY DEBIAN (mau do) vi
nguoi dung moi KHONG co ~/.face.icon rieng -> KUser.faceIconUrl roi ve avatar
mac dinh cua he (Debian). Ta ship mot avatar NaMi vao /etc/skel/.face.icon;
Calamares copy /etc/skel sang HOME nguoi dung moi -> ~/.face.icon = avatar
NaMi, KHONG con xoay Debian. (Rui ro con lai: neu AccountsService da ghi
Icon= rieng cho mot user co san thi uu tien hon ~/.face.icon — truong hop
cai moi KHONG co; xu ly sau bang hook firstboot neu can. verified_on_host: NO.)

Thiet ke: dia navy #092D4F + vanh vang mong + bieu tuong trong dong (vong
ivory + sao vang) canh giua — dung draw_trongdong_symbol da co, khong ve lai.

Tai lap: python3 branding/dongson-v3-render/make_default_avatar_v3.py
Dau ra:
  distro/.../includes.chroot/etc/skel/.face.icon
  distro/.../includes.chroot/usr/share/namios/avatars/namios-default-avatar.png
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dongson_shapes import (  # noqa: E402
    GOLD,
    IVORY,
    NAVY,
    _hex_to_rgba,
    draw_trongdong_symbol,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROOT = os.path.join(
    ROOT, "distro", "live-build", "config", "includes.chroot"
)
OUT_FACE = os.path.join(CHROOT, "etc", "skel", ".face.icon")
OUT_REF = os.path.join(
    CHROOT, "usr", "share", "namios", "avatars", "namios-default-avatar.png"
)

SIZE = 256
SS = 4  # supersample


def build_avatar() -> Image.Image:
    S = SIZE * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dia navy (co vanh vang mong lam vien) — ve tron khong fill goc vuong.
    margin = round(S * 0.012)
    bbox = (margin, margin, S - margin, S - margin)
    draw.ellipse(bbox, fill=_hex_to_rgba(NAVY))

    # Diem sang nhe phia tren (tao chieu sau, khong dung gradient GPU).
    hi = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hb = (
        round(S * 0.16),
        round(S * 0.08),
        round(S * 0.84),
        round(S * 0.62),
    )
    hd.ellipse(hb, fill=_hex_to_rgba(IVORY, 0.06))
    img = Image.alpha_composite(img, hi)
    draw = ImageDraw.Draw(img)

    # Vanh vang mong.
    rim_w = max(1, round(S * 0.018))
    draw.ellipse(bbox, outline=_hex_to_rgba(GOLD, 0.9), width=rim_w)

    # Bieu tuong trong dong canh giua (~60% duong kinh dia). LUU Y:
    # draw_trongdong_symbol tra ve anh dung o kich thuoc `size` DA downsample
    # (khong phai size*supersample) — nen tinh sym_size theo canvas SUPERSAMPLE
    # (S) de khi thu nho ve SIZE cuoi, bieu tuong chiem ~60% dia (truoc day
    # tinh theo SIZE -> chi ~15%, qua nho).
    sym_size = round(S * 0.60)
    sym = draw_trongdong_symbol(
        sym_size,
        ring_color=IVORY,
        star_color=GOLD,
        tick_color=IVORY,
        flourish_color=GOLD,
        flourish_alt_color=IVORY,
        supersample=SS,
    )
    sym_full = sym.size[0]
    off = (S - sym_full) // 2
    img.alpha_composite(sym, (off, off))

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> int:
    av = build_avatar()
    for path in (OUT_FACE, OUT_REF):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        av.save(path, "PNG")
        print(f"[OK] wrote {path} ({os.path.getsize(path)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
