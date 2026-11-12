#!/usr/bin/env python3
"""NaMi — BỘ ICON app "Đông Sơn" ĐẦY ĐỦ (rollout cả hệ điều hành).

Nối tiếp teaser make_app_icons_dongson_v4.py (Cuong #18397 "Ok" — duyệt hướng):
mỗi app lõi/hiện diện = ô squircle macOS + motif Đông Sơn mờ (vành chấm đồng +
tia mặt trời) + glyph chức năng TRẮNG sạch; app "Trợ lý" = mặt trời 12 tia vàng
(biểu tượng thương hiệu). Bảng màu navy/gold/teal/ngà, mỗi app một sắc riêng.

Tái dùng helper + glyph từ v4 (dongson_backdrop, g_sun) và v3 (base_tile, glyphs
doc/sheet/slide/globe/gear/folder/calendar, squircle_alpha, hx, C, E, WORK,
FINAL). THÊM glyph hình học đơn giản cho phần còn lại (shield/portico/book/
play-window/chip/plug/projector/monitor/people/app-grid/network/brush/clock/
refresh/bag/download/pencil/cylinder/formula/office/terminal/pdf/photo/music/
media/box/printer).

Cài vào CẢ 2 theme:
  usr/share/icons/NaMiOS-Lotus/<SIZE>x<SIZE>/apps/<icon-name>.png  (32..512)
  usr/share/icons/hicolor/<SIZE>x<SIZE>/apps/<icon-name>.png       (chỉ GHI ĐÈ
  entry đã tồn tại — không tạo thư mục/tên lạc)

Đầu ra phụ: app-icons-dongson-preview/<key>.png + full-set.png (contact sheet).
verified_on_host: NO (sandbox không có theme/Dolphin thật để xác nhận hiển thị).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_app_icons_macos_v3 import (  # noqa: E402
    C, E, WORK, FINAL, base_tile, hx, squircle_alpha,
    g_doc, g_sheet, g_slide, g_globe, g_gear, g_folder, g_calendar,
)
from make_app_icons_dongson_v4 import dongson_backdrop, g_sun  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CHROOT = os.path.join(
    REPO, "distro", "live-build", "config", "includes.chroot", "usr", "share")
LOTUS = os.path.join(CHROOT, "icons", "NaMiOS-Lotus")
HICOLOR = os.path.join(CHROOT, "icons", "hicolor")

OUT = os.path.join(HERE, "app-icons-dongson-preview")
os.makedirs(OUT, exist_ok=True)
FONT = "/tmp/vnfonts/Roboto-Medium.ttf"

WH = (255, 255, 255, 255)
IV = (255, 249, 239, 255)
LOTUS_SIZES = [32, 48, 64, 128, 256, 512]
HICOLOR_SIZES = [16, 32, 48, 64, 128, 256, 512]
SMALL_SIZES = {16, 32}

# ---- bảng màu tile (top, bottom) ----
PAL = {
    "navy":      ("#124A7A", "#082742"),
    "blue":      ("#3E8BFF", "#1D4FB0"),
    "green":     ("#2BC06F", "#148049"),
    "vermilion": ("#F0663E", "#B23A2E"),
    "gold":      ("#F0BC57", "#CB8F2E"),
    "teal":      ("#2FB3AF", "#17726F"),
    "slate":     ("#5E6B7E", "#39414F"),
    "graphite":  ("#5B6473", "#2F3742"),
    "red":       ("#F15A5A", "#C22E2E"),
}


def _lw(f=0.1):
    return max(2, int(E * f))


# ============================ GLYPH MỚI (trắng) =============================
def g_shield(d, accent):
    w, h = E * 1.46, E * 1.92
    y0 = C - h / 2
    pts = [(C, y0), (C + w / 2, y0 + h * 0.17), (C + w / 2, y0 + h * 0.52),
           (C, y0 + h), (C - w / 2, y0 + h * 0.52), (C - w / 2, y0 + h * 0.17)]
    d.polygon(pts, fill=WH)
    # dấu tích (check) màu app
    d.line([(C - E * 0.34, C + E * 0.02), (C - E * 0.06, C + E * 0.34),
            (C + E * 0.42, C - E * 0.36)], fill=accent + (255,),
           width=_lw(0.14), joint="curve")


def g_portal(d, accent):
    # Cổng dịch vụ: nóc tam giác + hàng cột (công sở)
    w = E * 1.78
    x0, x1 = C - w / 2, C + w / 2
    ytop, ybar, ybase = C - E * 0.98, C - E * 0.5, C + E * 1.0
    d.polygon([(C, ytop), (x1, ybar), (x0, ybar)], fill=WH)
    d.rectangle([x0, ybar, x1, ybar + E * 0.16], fill=WH)
    d.rectangle([x0 - E * 0.06, ybase, x1 + E * 0.06, ybase + E * 0.2], fill=WH)
    cols = 4
    cw = E * 0.17
    for i in range(cols):
        cx = x0 + E * 0.18 + i * (w - E * 0.36) / (cols - 1)
        d.rectangle([cx - cw / 2, ybar + E * 0.2, cx + cw / 2, ybase], fill=WH)


def g_book(d, accent):
    w, h = E * 1.84, E * 1.5
    x0, y0 = C - w / 2, C - h / 2
    d.rounded_rectangle([x0, y0, C - E * 0.04, y0 + h], radius=E * 0.08, fill=WH)
    d.rounded_rectangle([C + E * 0.04, y0, x0 + w, y0 + h], radius=E * 0.08, fill=WH)
    d.rectangle([C - E * 0.05, y0 + E * 0.02, C + E * 0.05, y0 + h - E * 0.02],
                fill=accent + (255,))
    for i in range(3):
        yy = y0 + h * (0.3 + i * 0.22)
        d.line([(x0 + E * 0.18, yy), (C - E * 0.2, yy)], fill=accent + (180,),
               width=_lw(0.05))
        d.line([(C + E * 0.2, yy), (x0 + w - E * 0.18, yy)], fill=accent + (180,),
               width=_lw(0.05))


def g_playwin(d, accent):
    w, h = E * 1.86, E * 1.5
    x0, y0 = C - w / 2, C - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=E * 0.1, fill=WH)
    d.rectangle([x0, y0, x0 + w, y0 + h * 0.2], fill=accent + (255,))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h * 0.2 + E * 0.02],
                        radius=E * 0.1, fill=accent + (255,))
    d.rectangle([x0, y0 + h * 0.14, x0 + w, y0 + h * 0.2], fill=accent + (255,))
    for i, cx in enumerate((x0 + E * 0.2, x0 + E * 0.42, x0 + E * 0.64)):
        d.ellipse([cx - E * 0.05, y0 + h * 0.1 - E * 0.05,
                   cx + E * 0.05, y0 + h * 0.1 + E * 0.05], fill=WH)
    t = E * 0.5
    d.polygon([(C - t * 0.42, C + h * 0.08 - t * 0.5),
               (C - t * 0.42, C + h * 0.08 + t * 0.5),
               (C + t * 0.6, C + h * 0.08)], fill=accent + (255,))


def g_chip(d, accent):
    s = E * 1.42
    x0, y0 = C - s / 2, C - s / 2
    pin, pl = E * 0.1, E * 0.26
    for i in range(3):
        off = -s * 0.28 + i * s * 0.28
        d.rectangle([C + off - pin / 2, y0 - pl, C + off + pin / 2, y0], fill=WH)
        d.rectangle([C + off - pin / 2, y0 + s, C + off + pin / 2, y0 + s + pl], fill=WH)
        d.rectangle([x0 - pl, C + off - pin / 2, x0, C + off + pin / 2], fill=WH)
        d.rectangle([x0 + s, C + off - pin / 2, x0 + s + pl, C + off + pin / 2], fill=WH)
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=E * 0.12, fill=WH)
    d.rounded_rectangle([x0 + s * 0.26, y0 + s * 0.26, x0 + s * 0.74, y0 + s * 0.74],
                        radius=E * 0.06, outline=accent + (255,), width=_lw(0.08))
    d.ellipse([C - E * 0.1, C - E * 0.1, C + E * 0.1, C + E * 0.1], fill=accent + (255,))


def g_plug(d, accent):
    # phích cắm nghiêng 45°
    for dx in (-E * 0.26, E * 0.26):
        d.line([(C + dx - E * 0.5, C - E * 0.5 - dx * 0), (C + dx, C)],
               fill=WH, width=_lw(0.14))
    d.line([(C - E * 0.72, C - E * 0.42), (C - E * 0.42, C - E * 0.72)],
           fill=WH, width=_lw(0.14))
    d.line([(C - E * 0.44, C - E * 0.14), (C - E * 0.14, C - E * 0.44)],
           fill=WH, width=_lw(0.14))
    d.polygon([(C - E * 0.1, C - E * 0.5), (C + E * 0.5, C + E * 0.1),
               (C + E * 0.28, C + E * 0.34), (C + E * 0.02, C + E * 0.42),
               (C - E * 0.42, C - E * 0.02)], fill=WH)
    d.line([(C + E * 0.24, C + E * 0.24), (C + E * 0.72, C + E * 0.72)],
           fill=WH, width=_lw(0.13))


def g_projector(d, accent):
    w, h = E * 1.5, E * 1.02
    x0, y0 = C - w / 2 - E * 0.22, C - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=E * 0.14, fill=WH)
    lx, ly = x0 + w * 0.64, C
    lr = E * 0.3
    d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], outline=accent + (255,),
              width=_lw(0.1))
    d.ellipse([lx - E * 0.08, ly - E * 0.08, lx + E * 0.08, ly + E * 0.08],
              fill=accent + (255,))
    d.ellipse([x0 + E * 0.22, y0 + E * 0.18, x0 + E * 0.36, y0 + E * 0.32], fill=accent + (255,))
    # chùm sáng
    bx = x0 + w
    for p in (0.26, 0.5, 0.74):
        d.line([(bx, ly), (bx + E * 0.6, y0 - h * 0.15 + h * 1.3 * p)],
               fill=(255, 255, 255, 150), width=_lw(0.05))


def g_monitor(d, accent):
    w, h = E * 1.86, E * 1.34
    x0, y0 = C - w / 2, C - h / 2 - E * 0.12
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=E * 0.1, fill=WH)
    d.rounded_rectangle([x0 + E * 0.14, y0 + E * 0.14, x0 + w - E * 0.14,
                         y0 + h - E * 0.14], radius=E * 0.05, fill=accent + (255,))
    d.rectangle([C - E * 0.12, y0 + h, C + E * 0.12, y0 + h + E * 0.3], fill=WH)
    d.rounded_rectangle([C - E * 0.44, y0 + h + E * 0.3, C + E * 0.44,
                         y0 + h + E * 0.44], radius=E * 0.06, fill=WH)


def g_people(d, accent):
    for dx, rr in ((E * 0.42, 0.9), (-E * 0.42, 0.9)):
        hr = E * 0.36 * rr
        hy = C - E * 0.42
        d.ellipse([C + dx - hr, hy - hr, C + dx + hr, hy + hr], fill=WH)
        bw, bh = E * 0.88 * rr, E * 0.78
        d.pieslice([C + dx - bw / 2, C - E * 0.02, C + dx + bw / 2,
                    C - E * 0.02 + bh * 2], 180, 360, fill=WH)


def g_appgrid(d, accent):
    s = E * 0.66
    gap = E * 0.2
    for r in range(2):
        for cc in range(2):
            x = C - s - gap / 2 + cc * (s + gap)
            y = C - s - gap / 2 + r * (s + gap)
            fill = WH if (r + cc) % 2 == 0 else (IV[0], IV[1], IV[2], 235)
            d.rounded_rectangle([x, y, x + s, y + s], radius=E * 0.12, fill=fill)


def g_network(d, accent):
    nodes = [(C, C - E * 0.9), (C - E * 0.9, C + E * 0.5),
             (C + E * 0.9, C + E * 0.5)]
    for nx, ny in nodes:
        d.line([(C, C), (nx, ny)], fill=WH, width=_lw(0.09))
    rr = E * 0.3
    d.ellipse([C - rr, C - rr, C + rr, C + rr], fill=WH)
    for nx, ny in nodes:
        r2 = E * 0.24
        d.ellipse([nx - r2, ny - r2, nx + r2, ny + r2], fill=WH)
        d.ellipse([nx - r2 * 0.4, ny - r2 * 0.4, nx + r2 * 0.4, ny + r2 * 0.4],
                  fill=accent + (255,))


def g_brush(d, accent):
    # cọ vẽ chéo
    d.polygon([(C - E * 0.78, C + E * 0.86), (C - E * 0.5, C + E * 0.58),
               (C - E * 0.34, C + E * 0.74), (C - E * 0.62, C + E * 1.02)],
              fill=WH)
    d.line([(C - E * 0.44, C + E * 0.64), (C + E * 0.62, C - E * 0.42)],
           fill=WH, width=_lw(0.22))
    d.ellipse([C + E * 0.4, C - E * 0.66, C + E * 0.86, C - E * 0.2],
              fill=accent + (255,))
    d.ellipse([C + E * 0.52, C - E * 0.54, C + E * 0.74, C - E * 0.32], fill=WH)


def g_clock(d, accent):
    r = E * 1.1
    d.ellipse([C - r, C - r, C + r, C + r], fill=WH)
    d.ellipse([C - r, C - r, C + r, C + r], outline=accent + (255,), width=_lw(0.07))
    d.line([(C, C), (C, C - r * 0.6)], fill=accent + (255,), width=_lw(0.11))
    d.line([(C, C), (C + r * 0.46, C + r * 0.18)], fill=accent + (255,), width=_lw(0.11))
    d.ellipse([C - E * 0.08, C - E * 0.08, C + E * 0.08, C + E * 0.08], fill=accent + (255,))


def g_refresh(d, accent):
    r = E * 0.92
    bb = [C - r, C - r, C + r, C + r]
    d.arc(bb, 60, 330, fill=WH, width=_lw(0.16))
    d.arc(bb, 240, 150, fill=WH, width=_lw(0.16))
    a1 = math.radians(60)
    tip1 = (C + r * math.cos(a1), C + r * math.sin(a1))
    d.polygon([(tip1[0] + E * 0.22, tip1[1] - E * 0.02),
               (tip1[0] - E * 0.16, tip1[1] - E * 0.2),
               (tip1[0] - E * 0.02, tip1[1] + E * 0.24)], fill=WH)
    a2 = math.radians(240)
    tip2 = (C + r * math.cos(a2), C + r * math.sin(a2))
    d.polygon([(tip2[0] - E * 0.22, tip2[1] + E * 0.02),
               (tip2[0] + E * 0.16, tip2[1] + E * 0.2),
               (tip2[0] + E * 0.02, tip2[1] - E * 0.24)], fill=WH)


def g_bag(d, accent):
    w, h = E * 1.5, E * 1.44
    x0, y0 = C - w / 2, C - h / 2 + E * 0.2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=E * 0.14, fill=WH)
    hr = E * 0.44
    d.arc([C - hr, y0 - hr * 0.9, C + hr, y0 + hr * 1.1], 180, 360,
          fill=WH, width=_lw(0.13))
    d.ellipse([C - E * 0.5, y0 + E * 0.34, C - E * 0.32, y0 + E * 0.52],
              fill=accent + (255,))
    d.ellipse([C + E * 0.32, y0 + E * 0.34, C + E * 0.5, y0 + E * 0.52],
              fill=accent + (255,))


def g_download(d, accent):
    d.line([(C, C - E * 0.96), (C, C + E * 0.26)], fill=WH, width=_lw(0.15))
    d.polygon([(C - E * 0.34, C - E * 0.06), (C + E * 0.34, C - E * 0.06),
               (C, C + E * 0.42)], fill=WH)
    d.line([(C - E * 0.74, C + E * 0.62), (C - E * 0.74, C + E * 0.92),
            (C + E * 0.74, C + E * 0.92), (C + E * 0.74, C + E * 0.62)],
           fill=WH, width=_lw(0.14), joint="curve")


def g_pencil(d, accent):
    # bút chì chéo (app Vẽ)
    x1, y1 = C - E * 0.82, C + E * 0.82
    x2, y2 = C + E * 0.7, C - E * 0.7
    nx, ny = (y2 - y1), -(x2 - x1)
    ln = math.hypot(nx, ny)
    hw = E * 0.26
    ux, uy = nx / ln * hw, ny / ln * hw
    # thân
    d.polygon([(x1 + ux, y1 + uy), (x2 + ux, y2 + uy),
               (x2 - ux, y2 - uy), (x1 - ux, y1 - uy)], fill=WH)
    # ngòi màu app
    tx, ty = C + E * 0.92, C - E * 0.92
    d.polygon([(x2 + ux, y2 + uy), (tx, ty), (x2 - ux, y2 - uy)], fill=accent + (255,))
    # tẩy
    d.line([(x1, y1), (x1 - ux * 0.0 - (x2 - x1) / ln * E * 0.0, y1)],
           fill=WH, width=1)
    d.ellipse([x1 - E * 0.2, y1 - E * 0.2, x1 + E * 0.2, y1 + E * 0.2], fill=accent + (255,))


def g_cylinder(d, accent):
    w, h = E * 1.4, E * 1.6
    x0, y0 = C - w / 2, C - h / 2
    eh = E * 0.4
    d.rectangle([x0, y0 + eh / 2, x0 + w, y0 + h - eh / 2], fill=WH)
    d.ellipse([x0, y0 + h - eh, x0 + w, y0 + h], fill=WH)
    d.ellipse([x0, y0, x0 + w, y0 + eh], fill=WH)
    d.ellipse([x0, y0, x0 + w, y0 + eh], outline=accent + (255,), width=_lw(0.07))
    for fy in (0.42, 0.72):
        yy = y0 + h * fy
        d.arc([x0, yy - eh / 2, x0 + w, yy + eh / 2], 0, 180,
              fill=accent + (220,), width=_lw(0.06))


def g_formula(d, accent):
    # dấu tổng Σ
    x0, x1 = C - E * 0.72, C + E * 0.72
    ytop, ybot = C - E * 0.9, C + E * 0.9
    w = _lw(0.16)
    d.line([(x1, ytop), (x0, ytop), (C + E * 0.05, C), (x0, ybot), (x1, ybot)],
           fill=WH, width=w, joint="curve")
    d.ellipse([C + E * 0.36, ytop - E * 0.12, C + E * 0.62, ytop + E * 0.14],
              fill=accent + (255,))


def g_office(d, accent):
    s = E * 1.56
    x0, y0 = C - s / 2, C - s / 2
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=E * 0.16, fill=WH)
    g = s * 0.1
    cs = (s - 3 * g) / 2
    cols = [hx("#2F6FC9"), hx("#2BC06F"), hx("#F0663E"), hx("#DEA93E")]
    k = 0
    for r in range(2):
        for cc in range(2):
            x = x0 + g + cc * (cs + g)
            y = y0 + g + r * (cs + g)
            d.rounded_rectangle([x, y, x + cs, y + cs], radius=E * 0.07,
                                fill=cols[k] + (255,))
            k += 1


def g_terminal(d, accent):
    w, h = E * 1.9, E * 1.5
    x0, y0 = C - w / 2, C - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=E * 0.12, fill=WH)
    bar = h * 0.22
    d.rounded_rectangle([x0, y0, x0 + w, y0 + bar + E * 0.1], radius=E * 0.12,
                        fill=accent + (255,))
    d.rectangle([x0, y0 + bar * 0.6, x0 + w, y0 + bar], fill=accent + (255,))
    for i, cx in enumerate((x0 + E * 0.22, x0 + E * 0.42, x0 + E * 0.62)):
        d.ellipse([cx - E * 0.05, y0 + bar * 0.5 - E * 0.05,
                   cx + E * 0.05, y0 + bar * 0.5 + E * 0.05], fill=WH)
    px, py = x0 + E * 0.28, y0 + bar + E * 0.34
    d.line([(px, py), (px + E * 0.34, py + E * 0.3), (px, py + E * 0.6)],
           fill=accent + (255,), width=_lw(0.11), joint="curve")
    d.line([(px + E * 0.5, py + E * 0.62), (px + E * 1.05, py + E * 0.62)],
           fill=accent + (255,), width=_lw(0.11))


def g_pdf(d, accent):
    w, h = E * 1.46, E * 1.84
    x0, y0 = C - w / 2, C - h / 2
    fold = w * 0.34
    d.polygon([(x0, y0), (x0 + w - fold, y0), (x0 + w, y0 + fold),
               (x0 + w, y0 + h), (x0, y0 + h)], fill=WH)
    d.polygon([(x0 + w - fold, y0), (x0 + w - fold, y0 + fold),
               (x0 + w, y0 + fold)], fill=(226, 232, 240, 255))
    band_y = y0 + h * 0.56
    d.rounded_rectangle([x0 + w * 0.08, band_y, x0 + w * 0.92, band_y + h * 0.26],
                        radius=E * 0.06, fill=accent + (255,))
    try:
        fnt = ImageFont.truetype(FONT, int(h * 0.19))
    except Exception:
        fnt = ImageFont.load_default()
    txt = "PDF"
    bb = d.textbbox((0, 0), txt, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((C - tw / 2 - bb[0], band_y + h * 0.13 - th / 2 - bb[1]), txt,
           font=fnt, fill=WH)


def g_photo(d, accent):
    s = E * 1.72
    x0, y0 = C - s / 2, C - s / 2
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=E * 0.12, fill=WH)
    m = E * 0.16
    ix0, iy0, ix1, iy1 = x0 + m, y0 + m, x0 + s - m, y0 + s - m
    d.rectangle([ix0, iy0, ix1, iy1], fill=accent + (255,))
    sr = E * 0.24
    d.ellipse([ix0 + s * 0.14, iy0 + s * 0.12, ix0 + s * 0.14 + sr,
               iy0 + s * 0.12 + sr], fill=WH)
    d.polygon([(ix0, iy1), (ix0 + s * 0.3, iy0 + s * 0.42),
               (ix0 + s * 0.52, iy1)], fill=WH)
    d.polygon([(ix0 + s * 0.36, iy1), (ix0 + s * 0.64, iy0 + s * 0.52),
               (ix1, iy1)], fill=(IV[0], IV[1], IV[2], 255))


def g_music(d, accent):
    x1, x2 = C - E * 0.3, C + E * 0.62
    ytop = C - E * 0.92
    d.line([(x1, ytop + E * 0.1), (x1, C + E * 0.5)], fill=WH, width=_lw(0.12))
    d.line([(x2, ytop - E * 0.06), (x2, C + E * 0.22)], fill=WH, width=_lw(0.12))
    d.polygon([(x1, ytop + E * 0.1), (x2, ytop - E * 0.06),
               (x2, ytop + E * 0.22), (x1, ytop + E * 0.38)], fill=WH)
    for cx, cy in ((x1 - E * 0.26, C + E * 0.5), (x2 - E * 0.26, C + E * 0.22)):
        d.ellipse([cx - E * 0.06, cy - E * 0.2, cx + E * 0.3, cy + E * 0.14], fill=WH)


def g_media(d, accent):
    s = E * 1.7
    x0, y0 = C - s / 2, C - s / 2
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=E * 0.26, fill=WH)
    t = E * 0.64
    d.polygon([(C - t * 0.4, C - t * 0.62), (C - t * 0.4, C + t * 0.62),
               (C + t * 0.66, C)], fill=accent + (255,))


def g_box(d, accent):
    w, h = E * 1.7, E * 1.44
    x0, y0 = C - w / 2, C - h / 2 + E * 0.08
    lid = h * 0.3
    d.rounded_rectangle([x0, y0, x0 + w, y0 + lid], radius=E * 0.06, fill=WH)
    d.rounded_rectangle([x0 + E * 0.06, y0 + lid, x0 + w - E * 0.06, y0 + h],
                        radius=E * 0.06, fill=WH)
    d.rounded_rectangle([C - E * 0.22, y0 + lid, C + E * 0.22, y0 + lid + E * 0.34],
                        radius=E * 0.05, fill=accent + (255,))
    d.rectangle([C - E * 0.1, y0 + lid * 0.3, C + E * 0.1, y0 + lid], fill=accent + (255,))


def g_printer(d, accent):
    w, h = E * 1.78, E * 0.96
    x0, y0 = C - w / 2, C - h / 2 + E * 0.16
    # giấy trên
    d.rectangle([x0 + E * 0.26, y0 - E * 0.5, x0 + w - E * 0.26, y0 + E * 0.12],
                fill=WH)
    for i in range(3):
        yy = y0 - E * 0.36 + i * E * 0.16
        d.line([(x0 + E * 0.42, yy), (x0 + w - E * 0.42, yy)],
               fill=accent + (220,), width=_lw(0.05))
    # thân máy
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=E * 0.12, fill=WH)
    d.ellipse([x0 + w - E * 0.38, y0 + E * 0.18, x0 + w - E * 0.18, y0 + E * 0.38],
              fill=accent + (255,))
    # giấy ra
    d.rectangle([x0 + E * 0.3, y0 + h - E * 0.1, x0 + w - E * 0.3, y0 + h + E * 0.5],
                fill=WH)
    d.rounded_rectangle([x0 + E * 0.3, y0 + h - E * 0.1, x0 + w - E * 0.3,
                         y0 + h + E * 0.5], radius=E * 0.04, outline=accent + (200,),
                        width=_lw(0.04))


# ======================= BẢNG ICON: key, nhãn, màu, glyph, hero, names ======
def L(fn):
    """bọc glyph nhận accent = màu bottom của tile."""
    return fn


def entry(key, viet, color, glyphfn, names, hero=False, calendar=False):
    top, bottom = PAL[color]
    return dict(key=key, viet=viet, top=top, bottom=bottom, color=color,
                glyphfn=glyphfn, names=names, hero=hero, calendar=calendar)


ICONS = [
    entry("nAssistant", "Trợ lý", "navy", lambda d, a: g_sun(d),
          ["namios", "namios-assistant"], hero=True),
    # nOffice (rebrand LibreOffice)
    entry("nWriter", "Văn bản", "blue", g_doc,
          ["libreoffice-writer", "libreoffice-oasis-text", "ooo-writer",
           "namioffice-writer"]),
    entry("nCalc", "Bảng tính", "green", g_sheet,
          ["libreoffice-calc", "libreoffice-oasis-spreadsheet", "ooo-calc",
           "namioffice-calc"]),
    entry("nImpress", "Trình chiếu", "vermilion", g_slide,
          ["libreoffice-impress", "libreoffice-oasis-presentation", "ooo-impress",
           "namioffice-impress"]),
    entry("nDraw", "Vẽ", "gold", g_pencil,
          ["libreoffice-draw", "libreoffice-oasis-drawing", "namioffice-draw"]),
    entry("nBase", "Cơ sở dữ liệu", "teal", g_cylinder,
          ["libreoffice-base", "namioffice-base"]),
    entry("nMath", "Công thức", "slate", g_formula,
          ["libreoffice-math", "namioffice-math"]),
    entry("nOffice", "Văn phòng", "navy", g_office,
          ["libreoffice-startcenter", "libreoffice-main", "namioffice-startcenter"]),
    # Trình duyệt + web app
    entry("nBrowser", "Trình duyệt", "teal", g_globe,
          ["internet-web-browser"]),
    # Tệp
    entry("nFiles", "Tệp", "gold", g_folder,
          ["system-file-manager", "org.kde.dolphin"]),
    # Cài đặt
    entry("nSettings", "Cài đặt", "graphite", g_gear,
          ["preferences-system", "systemsettings"]),
    # Cửa hàng
    entry("nStore", "Cửa hàng", "blue", g_bag,
          ["plasmadiscover", "plasma-discover", "org.kde.discover"]),
    # Cập nhật
    entry("nUpdate", "Cập nhật", "teal", g_refresh,
          ["system-software-update"]),
    # An toàn
    entry("nSecurity", "An toàn", "vermilion", g_shield,
          ["security-high"]),
    # Cổng dịch vụ
    entry("nServices", "Cổng Dịch vụ", "gold", g_portal,
          ["namios-services"]),
    # Máy chiếu
    entry("nProjector", "Máy chiếu", "navy", g_projector,
          ["video-display"]),
    # Màn hình (cài đặt hiển thị)
    entry("nDisplay", "Màn hình", "graphite", g_monitor,
          ["preferences-desktop-display"]),
    # Chẩn đoán
    entry("nDiag", "Chẩn đoán", "teal", g_chip,
          ["namios-diagnostics"]),
    # Hướng dẫn
    entry("nGuide", "Hướng dẫn", "blue", g_book,
          ["namios-guide", "help-contents"]),
    # Chạy phần mềm Windows
    entry("nRun", "Chạy Windows", "slate", g_playwin,
          ["namios-run"]),
    # Hỏi AI
    entry("nAI", "Hỏi AI", "navy", g_chip,
          ["namios-ai"]),
    # Lịch
    entry("nCalendar", "Lịch", "red", None,
          ["namios-calendar"], calendar=True),
    # Kết nối thiết bị / thiết bị ngoại vi
    entry("nConnect", "Thiết bị", "teal", g_plug,
          ["preferences-desktop-peripherals", "namios-connect"]),
    # Tài khoản
    entry("nAccounts", "Tài khoản", "teal", g_people,
          ["system-users"]),
    # Ứng dụng
    entry("nApps", "Ứng dụng", "slate", g_appgrid,
          ["preferences-desktop-default-applications"]),
    # Mạng
    entry("nNetwork", "Mạng", "blue", g_network,
          ["preferences-system-network"]),
    # Cá nhân hoá
    entry("nTheme", "Cá nhân hoá", "vermilion", g_brush,
          ["preferences-desktop-theme"]),
    # Thời gian & Ngôn ngữ
    entry("nTime", "Thời gian", "blue", g_clock,
          ["preferences-system-time"]),
    # Cài đặt phần mềm (calamares)
    entry("nInstall", "Cài hệ điều hành", "teal", g_download,
          ["system-software-install"]),
    # Terminal
    entry("nTerminal", "Dòng lệnh", "graphite", g_terminal,
          ["utilities-terminal", "konsole", "org.kde.konsole"]),
    # PDF
    entry("nPdf", "PDF", "vermilion", g_pdf,
          ["okular"]),
    # Ảnh
    entry("nPhoto", "Ảnh", "teal", g_photo,
          ["image-viewer", "gwenview", "org.kde.gwenview"]),
    # Media (VLC) + trình phát
    entry("nMedia", "Media", "gold", g_media,
          ["vlc", "haruna"]),
    entry("nMusic", "Nhạc", "gold", g_music,
          ["elisa"]),
    # Lưu trữ (Ark)
    entry("nArk", "Lưu trữ", "slate", g_box,
          ["ark"]),
    # Máy in
    entry("nPrinter", "Máy in", "blue", g_printer,
          ["printer"]),
]


# ============================ RENDER + INSTALL ==============================
def _zoom(layer, f):
    w = layer.size[0]
    nw = max(1, int(round(w * f)))
    big = layer.resize((nw, nw), Image.LANCZOS)
    if nw >= w:
        l = (nw - w) // 2
        return big.crop((l, l, l + w, l + w))
    out = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    out.alpha_composite(big, ((w - nw) // 2, (w - nw) // 2))
    return out


def _fade(layer, m):
    r, g, b, a = layer.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * m))))


_BD = None


def backdrop(small):
    global _BD
    if _BD is None:
        _BD = dongson_backdrop(WORK)
    return _fade(_BD, 0.5) if small else _BD


def build_master(it, small=False):
    tile = base_tile(hx(it["top"]), hx(it["bottom"]))
    tile = Image.alpha_composite(tile, backdrop(small))
    glyph = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glyph)
    overlay = None
    accent = hx(it["bottom"])
    if it["calendar"]:
        overlay = g_calendar(gd, accent)
    elif it["hero"]:
        it["glyphfn"](gd, accent)
    else:
        try:
            it["glyphfn"](gd, accent)
        except TypeError:
            it["glyphfn"](gd)
    if small:
        glyph = _zoom(glyph, 1.16)
        if overlay is not None:
            overlay = _zoom(overlay, 1.16)
    if not it["hero"]:
        sh = glyph.split()[3].filter(ImageFilter.GaussianBlur(WORK * 0.012))
        shimg = Image.new("RGBA", (WORK, WORK), (0, 0, 0, 0))
        shimg.putalpha(sh.point(lambda v: int(v * 0.26)))
        tile.alpha_composite(shimg, (0, int(WORK * 0.012)))
    if overlay is not None:
        tile = Image.alpha_composite(tile, overlay)
    tile = Image.alpha_composite(tile, glyph)
    a = (squircle_alpha(WORK) * 255).astype(np.uint8)
    ba = np.array(tile.split()[3], np.uint8)
    tile.putalpha(Image.fromarray(np.minimum(ba, a), "L"))
    return tile


def save_png(master, size, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = master.resize((size, size), Image.LANCZOS)
    img.save(path, "PNG")
    # kiểm tra non-empty + đúng cỡ
    assert os.path.getsize(path) > 0, f"empty {path}"
    with Image.open(path) as chk:
        assert chk.size == (size, size), f"bad size {path}: {chk.size}"


def update_lotus_index():
    idx = os.path.join(LOTUS, "index.theme")
    with open(idx, "r", encoding="utf-8") as f:
        txt = f.read()
    if "32x32/apps" in txt:
        return False
    txt = txt.replace(
        "Directories=512x512/apps,256x256/apps,128x128/apps,64x64/apps,48x48/apps",
        "Directories=512x512/apps,256x256/apps,128x128/apps,64x64/apps,"
        "48x48/apps,32x32/apps")
    txt = txt.rstrip("\n") + (
        "\n\n[32x32/apps]\nSize=32\nContext=Applications\nType=Fixed\n")
    with open(idx, "w", encoding="utf-8") as f:
        f.write(txt)
    return True


def main():
    changed_idx = update_lotus_index()
    files_written = 0
    hicolor_written = 0
    per_icon = {}
    sheet_items = []
    for it in ICONS:
        mnorm = build_master(it, small=False)
        msmall = build_master(it, small=True)
        prev = os.path.join(OUT, f"{it['key']}.png")
        mnorm.resize((FINAL, FINAL), Image.LANCZOS).save(prev, "PNG")
        sheet_items.append((it["key"], it["viet"]))
        written_names = []
        for name in it["names"]:
            n_sizes = []
            # Lotus
            for s in LOTUS_SIZES:
                m = msmall if s in SMALL_SIZES else mnorm
                p = os.path.join(LOTUS, f"{s}x{s}", "apps", f"{name}.png")
                save_png(m, s, p)
                files_written += 1
                n_sizes.append(s)
            # hicolor: chỉ GHI ĐÈ entry đã tồn tại
            for s in HICOLOR_SIZES:
                p = os.path.join(HICOLOR, f"{s}x{s}", "apps", f"{name}.png")
                if os.path.exists(p):
                    m = msmall if s in SMALL_SIZES else mnorm
                    save_png(m, s, p)
                    files_written += 1
                    hicolor_written += 1
            written_names.append((name, sorted(set(n_sizes))))
        per_icon[it["key"]] = dict(viet=it["viet"], color=it["color"],
                                   names=written_names)
        print(f"[OK] {it['key']:12s} {it['viet']:14s} -> {len(it['names'])} name(s)")

    sheet = contact_sheet(sheet_items)
    print(f"[OK] icons={len(ICONS)} files_written={files_written} "
          f"hicolor_overwrites={hicolor_written} index32={changed_idx}")
    print(f"[OK] full-set -> {sheet}")
    return per_icon, files_written, hicolor_written


def contact_sheet(items):
    cols = 6
    rows = math.ceil(len(items) / cols)
    cell, isz, pad, lblh, topband = 230, 150, 54, 62, 150
    W = pad * 2 + cols * cell
    H = topband + rows * (cell + lblh) + 44
    bg = np.zeros((H, W, 3), np.float64)
    t = np.linspace(0, 1, H)[:, None, None]
    bg[:] = np.array(hx("#F4F6FA")) * (1 - t) + np.array(hx("#E4E8F0")) * t
    sheet = Image.fromarray(bg.astype(np.uint8), "RGB").convert("RGBA")
    dr = ImageDraw.Draw(sheet)
    try:
        ft = ImageFont.truetype(FONT, 52)
        fl = ImageFont.truetype(FONT, 26)
    except Exception:
        ft = fl = ImageFont.load_default()
    dr.text((pad, 52), "NaMi — Bộ icon ứng dụng cách điệu Trống Đồng Đông Sơn",
            font=ft, fill=hx("#092D4F") + (255,))
    for i, (key, viet) in enumerate(items):
        ic = Image.open(os.path.join(OUT, f"{key}.png")).resize((isz, isz),
                                                               Image.LANCZOS)
        r, c = divmod(i, cols)
        cx = pad + c * cell + (cell - isz) // 2
        cy = topband + r * (cell + lblh) + (cell - isz) // 2
        shm = ic.split()[3].filter(ImageFilter.GaussianBlur(14))
        shl = Image.new("RGBA", (isz, isz), (10, 25, 45, 0))
        shl.putalpha(shm.point(lambda v: int(v * 0.3)))
        s = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
        s.alpha_composite(shl, (cx, cy + 12))
        sheet = Image.alpha_composite(sheet, s.filter(ImageFilter.GaussianBlur(5)))
        sheet.alpha_composite(ic, (cx, cy))
        dr = ImageDraw.Draw(sheet)
        bb = dr.textbbox((0, 0), viet, font=fl)
        dr.text((pad + c * cell + (cell - (bb[2] - bb[0])) // 2, cy + isz + 12),
                viet, font=fl, fill=hx("#0E2238") + (255,))
    out = os.path.join(OUT, "full-set.png")
    sheet.convert("RGB").save(out, "PNG")
    return out


if __name__ == "__main__":
    main()
